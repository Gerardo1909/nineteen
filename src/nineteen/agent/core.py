"""Núcleo del agente nineteen: bucle agentico con tool calling nativo de Ollama.

El agente mantiene un historial de mensajes y ejecuta herramientas en un bucle
hasta que el modelo produce una respuesta final (sin tool calls) o se alcanza
el límite de pasos.

Flujo general:
    1. Se construye el historial con el system prompt.
    2. Se llama a Ollama con el historial y el esquema de herramientas.
    3. Si la respuesta contiene tool calls → se ejecutan y se agregan los
       resultados al historial, luego se repite desde 2.
    4. Si no hay tool calls → se imprime la respuesta final y se detiene.

Dependencias externas: ``ollama`` (cliente oficial de Ollama).
"""

from __future__ import annotations

import sys

import ollama

from nineteen.display import (
    print_tool_call,
    print_tool_result,
    print_warning,
)
from nineteen.prompts import build_system_prompt
from nineteen.tools import ToolRegistry, _build_tools_schema, build_default_registry

MAX_RESULT_LEN = 2000
"""Longitud máxima del resultado de una herramienta antes de truncarlo."""


class Agent:
    """Agente conversacional con capacidad de ejecutar herramientas de filesystem.

    Encapsula el bucle agentico completo: llamadas a Ollama, ejecución de
    herramientas y mantenimiento del historial de mensajes.

    Attributes:
        model: Nombre del modelo Ollama a usar.
        show_thinking: Si es ``True``, imprime el bloque ``<think>`` por stderr.
        max_steps: Máximo de pasos del bucle agentico por tarea.
        registry: Registro de herramientas disponibles para el agente.
    """

    def __init__(
        self,
        model: str = "lfm2.5-thinking:1.2b",
        show_thinking: bool = False,
        max_steps: int = 10,
        registry: ToolRegistry | None = None,
    ) -> None:
        """Inicializa el agente con modelo y configuración opcionales.

        Args:
            model: Nombre del modelo Ollama (debe estar disponible localmente).
                Por defecto usa ``"lfm2.5-thinking:1.2b"``.
            show_thinking: Si es ``True``, imprime el bloque de razonamiento
                interno del modelo por ``stderr``. Útil para depuración.
            max_steps: Número máximo de iteraciones del bucle agentico.
                Evita bucles infinitos en caso de que el modelo no converja.
            registry: Registro de herramientas a usar. Si es ``None``, se
                construye el registry por defecto con las 5 herramientas de filesystem.
        """
        self.model = model
        self.show_thinking = show_thinking
        self.max_steps = max_steps
        self.registry = registry or build_default_registry()
        self._tools_schema = _build_tools_schema(self.registry)

    def run(self, task: str) -> None:
        """Ejecuta una tarea en modo one-shot hasta completarla o alcanzar max_steps.

        Crea un historial nuevo con el system prompt y la tarea del usuario,
        ejecuta el bucle agentico y retorna al terminar.

        Args:
            task: Descripción de la tarea a ejecutar en lenguaje natural.
        """
        messages: list[dict] = [
            {"role": "system", "content": build_system_prompt(self.registry)},
            {"role": "user", "content": task},
        ]
        self._loop(messages)

    def chat_loop(self) -> None:
        """Inicia el REPL interactivo. Mantiene el historial entre turnos.

        Lee entrada del usuario en un bucle, ejecuta el agente y muestra
        la respuesta. Se detiene cuando el usuario escribe ``exit``, ``quit``
        o presiona Ctrl-C / Ctrl-D.
        """
        messages: list[dict] = [
            {"role": "system", "content": build_system_prompt(self.registry)},
        ]
        try:
            while True:
                try:
                    user_input = input(f"\n\033[36m\033[1m❯\033[0m ").strip()
                except EOFError:
                    break
                if not user_input:
                    continue
                if user_input.lower() in ("exit", "quit", "/exit", "/quit"):
                    print()
                    break
                messages.append({"role": "user", "content": user_input})
                messages = self._loop(messages)
        except KeyboardInterrupt:
            print("\n")

    def _loop(self, messages: list[dict]) -> list[dict]:
        """Ejecuta el bucle agentico hasta una respuesta final o max_steps.

        En cada iteración:
        1. Llama a Ollama con el historial actual.
        2. Si hay tool calls → los ejecuta y agrega resultados al historial.
        3. Si no hay tool calls → imprime la respuesta final y sale del bucle.

        Args:
            messages: Historial de mensajes acumulado (system + user + assistant + tool).

        Returns:
            Historial actualizado con todos los mensajes de esta sesión de bucle.
        """
        for step in range(self.max_steps):
            content, thinking, tool_calls = self._call(messages)

            if self.show_thinking and thinking:
                sys.stderr.write(f"\033[2m[thinking] {thinking[:500]}...\033[0m\n")
                sys.stderr.flush()

            if not tool_calls:
                # Respuesta final
                if content:
                    sys.stdout.write(content)
                    sys.stdout.write("\n")
                    sys.stdout.flush()
                messages.append({"role": "assistant", "content": content or ""})
                break

            # Hay tool calls — ejecutar cada uno
            messages.append(
                {
                    "role": "assistant",
                    "content": content or "",
                    "tool_calls": [
                        {
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments,
                            }
                        }
                        for tc in tool_calls
                    ],
                }
            )

            for tc in tool_calls:
                name = tc.function.name
                args = tc.function.arguments  # ya es un dict desde el SDK

                print_tool_call(name, args)
                result = self.registry.call(name, args)
                result = result[:MAX_RESULT_LEN]
                print_tool_result(result)

                messages.append(
                    {
                        "role": "tool",
                        "content": result,
                    }
                )
        else:
            print_warning(f"Reached max steps ({self.max_steps}). Stopping.")

        return messages

    def _call(self, messages: list[dict]) -> tuple[str, str, list]:
        """Realiza una llamada no-streaming a Ollama con tool calling nativo.

        Envía el historial completo al modelo con el esquema de herramientas.
        La respuesta puede contener contenido de texto, bloque de razonamiento
        (``thinking``) y/o tool calls.

        Args:
            messages: Historial de mensajes a enviar al modelo.

        Returns:
            Tupla ``(content, thinking, tool_calls)`` donde:
            - ``content``: Texto de la respuesta del asistente (puede ser vacío).
            - ``thinking``: Bloque de razonamiento interno (puede ser vacío).
            - ``tool_calls``: Lista de tool calls del SDK de Ollama (puede ser vacía).
        """
        resp = ollama.chat(
            model=self.model,
            messages=messages,
            tools=self._tools_schema,
            options={"temperature": 0},
        )
        content = resp.message.content or ""
        thinking = resp.message.thinking or ""
        tool_calls = resp.message.tool_calls or []
        return content, thinking, tool_calls
