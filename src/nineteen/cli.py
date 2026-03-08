"""
Interfaz de línea de comandos del agente nineteen.

Expone dos modos de uso mediante Click:

- **Modo interactivo** (``nineteen``): REPL con historial persistente entre turnos.
- **Modo one-shot** (``nineteen run "tarea"``): ejecuta una tarea y sale.

El modelo y los parámetros pueden configurarse por flags o variables de entorno.
"""

from __future__ import annotations

import sys

import click

from nineteen import __version__
from nineteen.agent import Agent
from nineteen.display import print_banner, print_error
from nineteen.tools import build_default_registry

DEFAULT_MODEL = "lfm2.5-thinking:1.2b"
"""Modelo Ollama usado por defecto si no se especifica uno."""


@click.group(
    invoke_without_command=True,
    context_settings={"help_option_names": ["-h", "--help"]},
)
@click.version_option(__version__, "-V", "--version")
@click.option(
    "--model",
    "-m",
    default=DEFAULT_MODEL,
    envvar="NINETEEN_MODEL",
    show_default=True,
    help="Ollama model to use.",
)
@click.option(
    "--max-steps", default=10, show_default=True, help="Maximum agentic steps per task."
)
@click.option(
    "--show-thinking",
    is_flag=True,
    default=False,
    hidden=True,
    help="Print <think> blocks to stderr (dev mode).",
)
@click.option(
    "--no-approval",
    is_flag=True,
    default=False,
    help="Skip interactive approval for destructive tools.",
)
@click.option(
    "--no-stream",
    is_flag=True,
    default=False,
    help="Disable streaming output (wait for full response).",
)
@click.pass_context
def main(
    ctx: click.Context,
    model: str,
    max_steps: int,
    show_thinking: bool,
    no_approval: bool,
    no_stream: bool,
) -> None:
    """nineteen — lightweight local AI agent powered by Ollama.

    Opciones disponibles:

    \b
    --model / -m          Modelo Ollama a usar (o NINETEEN_MODEL env var).
    --max-steps           Límite de pasos por tarea (default: 10).
    --no-approval         Omitir confirmación para herramientas destructivas.
    --no-stream           Deshabilitar streaming (esperar respuesta completa).
    -V / --version        Muestra la versión y sale.
    -h / --help           Muestra este mensaje y sale.

    Sin subcomando, inicia el modo interactivo.
    """
    ctx.ensure_object(dict)
    ctx.obj["model"] = model
    ctx.obj["max_steps"] = max_steps
    ctx.obj["show_thinking"] = show_thinking
    ctx.obj["no_approval"] = no_approval
    ctx.obj["no_stream"] = no_stream

    if ctx.invoked_subcommand is None:
        _interactive(model, max_steps, show_thinking, no_approval, no_stream)


@main.command()
@click.argument("task")
@click.option(
    "--model",
    "-m",
    default=None,
    envvar="NINETEEN_MODEL",
    help="Ollama model to use (overrides parent option).",
)
@click.option(
    "--max-steps",
    default=None,
    type=int,
    help="Maximum agentic steps (overrides parent option).",
)
@click.option("--show-thinking", is_flag=True, default=False, hidden=True)
@click.option(
    "--no-approval",
    is_flag=True,
    default=False,
    help="Skip interactive approval for destructive tools.",
)
@click.option(
    "--no-stream",
    is_flag=True,
    default=False,
    help="Disable streaming output (wait for full response).",
)
@click.pass_context
def run(
    ctx: click.Context,
    task: str,
    model: str | None,
    max_steps: int | None,
    show_thinking: bool,
    no_approval: bool,
    no_stream: bool,
) -> None:
    """Ejecuta una tarea en modo one-shot y sale.

    Args:
        task: Descripción de la tarea a ejecutar en lenguaje natural.
            Ejemplo: ``nineteen run "list files in the current directory"``
    """
    obj = ctx.obj or {}
    effective_model = model or obj.get("model", DEFAULT_MODEL)
    effective_steps = max_steps or obj.get("max_steps", 10)
    effective_thinking = show_thinking or obj.get("show_thinking", False)
    effective_no_approval = no_approval or obj.get("no_approval", False)
    effective_no_stream = no_stream or obj.get("no_stream", False)

    agent = _make_agent(
        effective_model,
        effective_thinking,
        effective_steps,
        no_approval=effective_no_approval,
        no_stream=effective_no_stream,
    )
    if agent is None:
        sys.exit(1)
    agent.run(task)


def _interactive(
    model: str,
    max_steps: int,
    show_thinking: bool,
    no_approval: bool = False,
    no_stream: bool = False,
) -> None:
    """Inicia el modo interactivo: muestra el banner y lanza el REPL del agente.

    Args:
        model: Nombre del modelo Ollama a usar.
        max_steps: Límite de pasos agenticos por tarea.
        show_thinking: Si es ``True``, imprime bloques ``<think>`` por stderr.
        no_approval: Si es ``True``, omite la confirmacion para herramientas destructivas.
        no_stream: Si es ``True``, deshabilita el streaming progresivo.
    """
    registry = build_default_registry()
    print_banner(model, len(registry))
    agent = _make_agent(
        model, show_thinking, max_steps, registry=registry,
        no_approval=no_approval, no_stream=no_stream,
    )
    if agent is None:
        sys.exit(1)
    agent.chat_loop()


def _make_agent(
    model: str,
    show_thinking: bool,
    max_steps: int,
    registry=None,
    no_approval: bool = False,
    no_stream: bool = False,
) -> Agent | None:
    """Construye y retorna una instancia del agente, o ``None`` en caso de error.

    Intenta verificar que el modelo esté disponible en Ollama antes de crear
    el agente. Si la verificación falla, igual intenta construir el agente
    (el error real surgirá en la primera llamada al modelo).

    Args:
        model: Nombre del modelo Ollama a usar.
        show_thinking: Si es ``True``, imprime bloques ``<think>`` por stderr.
        max_steps: Límite de pasos agenticos por tarea.
        registry: Registry de herramientas. Si es ``None``, se usa el por defecto.
        no_approval: Si es ``True``, omite la confirmacion para herramientas destructivas.
        no_stream: Si es ``True``, deshabilita el streaming progresivo.

    Returns:
        Instancia de ``Agent`` lista para usar, o ``None`` si hay un error de importación.
    """
    try:
        import ollama as _ollama

        _ollama.show(model)  # verificar que el modelo esté disponible
    except Exception:
        pass  # Si show() falla, igual intentamos; el error real surge en el primer chat

    try:
        from nineteen.agent import Agent

        return Agent(
            model=model,
            show_thinking=show_thinking,
            max_steps=max_steps,
            registry=registry,
            approval=not no_approval,
            stream=not no_stream,
        )
    except ImportError as e:
        print_error(f"Import error: {e}")
        return None
