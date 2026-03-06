"""
Capa de presentación del agente nineteen: salida ANSI, logo y feedback de herramientas.

Centraliza toda la salida al terminal para mantener el resto del código limpio
de lógica de presentación. Usa códigos ANSI directos (sin dependencias externas).
"""

from __future__ import annotations

import re
import sys
from typing import Any

RESET = "\033[0m"
"""Resetea todos los atributos de texto al valor por defecto del terminal."""
BOLD = "\033[1m"
"""Texto en negrita."""
DIM = "\033[2m"
"""Texto atenuado (gris)."""
CYAN = "\033[36m"
"""Color cyan — usado para el logo, el banner y el prompt interactivo."""
YELLOW = "\033[33m"
"""Color amarillo — usado para llamadas a herramientas y advertencias."""
GREEN = "\033[32m"
"""Color verde — usado para resultados exitosos de herramientas."""
RED = "\033[31m"
"""Color rojo — usado para errores de herramientas y mensajes de error."""
WHITE = "\033[37m"
"""Color blanco — usado para destacar valores en el banner."""

_ANSI_RE = re.compile(r"\033\[[0-9;]*m")
"""Expresión regular para eliminar códigos ANSI al calcular longitud visible."""

_LOGO_LINES = [
    "  ██   ████  ",
    " ███   ██  ██",
    "  ██   ██  ██",
    "  ██   █████ ",
    "  ██       ██",
    "  ██   ██  ██",
    " ████   ████ ",
]
"""Logo ASCII de 7 filas con los dígitos '1' y '9' en bloques de píxeles."""


def print_banner(model: str, tool_count: int) -> None:
    """Imprime el banner de bienvenida con el logo pixelado "19".

    Muestra el logo en cyan seguido de la versión del agente, el modelo
    activo, la cantidad de herramientas cargadas y las instrucciones de salida.

    Args:
        model: Nombre del modelo Ollama activo (p. ej. ``"lfm2.5-thinking:1.2b"``).
        tool_count: Número de herramientas cargadas en el registry.
    """
    print()
    for line in _LOGO_LINES:
        print(f"  {CYAN}{line}{RESET}")
    print()

    width = 54
    border = "─" * width
    print(f"{CYAN}┌{border}┐{RESET}")
    _banner_line(f"  {BOLD}nineteen{RESET}{CYAN}  v0.1.0", width)
    _banner_line(
        f"  model: {WHITE}{model}{RESET}{CYAN}  •  tools: {tool_count} cargadas", width
    )
    _banner_line(
        f"  Escribe {WHITE}'exit'{RESET}{CYAN} o {WHITE}Ctrl-C{RESET}{CYAN} para salir",
        width,
    )
    print(f"{CYAN}└{border}┘{RESET}\n")


def _banner_line(content: str, width: int) -> None:
    """Imprime una línea del banner con bordes laterales y padding automático.

    Calcula el ancho visible (sin códigos ANSI) para aplicar el padding correcto
    y mantener los bordes alineados.

    Args:
        content: Contenido de la línea, puede incluir códigos ANSI.
        width: Ancho total de la caja del banner (en caracteres visibles).
    """
    plain = _ANSI_RE.sub("", content)
    padding = width - len(plain)
    print(f"{CYAN}│{RESET}{content}{' ' * max(0, padding)}{CYAN}│{RESET}")


def print_tool_call(name: str, args: dict[str, Any]) -> None:
    """Imprime una notificación de llamada a herramienta.

    Muestra el nombre de la herramienta y sus argumentos en amarillo atenuado,
    antes de que la herramienta sea ejecutada.

    Args:
        name: Nombre de la herramienta que se está llamando.
        args: Diccionario de argumentos de la llamada.
    """
    args_repr = ", ".join(f"{k}={repr(v)[:60]}" for k, v in args.items())
    print(f"\n{DIM}{YELLOW}⚙  {name}({args_repr}){RESET}", flush=True)


def print_tool_result(result: str) -> None:
    """Imprime un preview del resultado de una herramienta.

    Muestra los primeros 120 caracteres del resultado. El color indica el estado:
    rojo para errores (resultado comienza con ``"ERROR"``), verde para éxito.

    Args:
        result: Resultado de la ejecución de la herramienta.
    """
    preview = result[:120] + ("…" if len(result) > 120 else "")
    color = RED if result.startswith("ERROR") else GREEN
    print(f"{DIM}{color}→  {preview}{RESET}\n", flush=True)


def print_error(msg: str) -> None:
    """Imprime un mensaje de error en rojo por ``stderr``.

    Args:
        msg: Mensaje de error a mostrar.
    """
    print(f"\n{RED}✗  {msg}{RESET}\n", file=sys.stderr)


def print_warning(msg: str) -> None:
    """Imprime un mensaje de advertencia en amarillo por ``stdout``.

    Args:
        msg: Mensaje de advertencia a mostrar.
    """
    print(f"\n{YELLOW}⚠  {msg}{RESET}\n", flush=True)


def prompt_approval(name: str, args: dict[str, Any]) -> str:
    """Pide confirmacion al usuario antes de ejecutar una herramienta destructiva.

    Muestra las 3 opciones y espera input. Enter sin texto equivale a "y".
    EOF o Ctrl-C equivalen a "n" (denegar).

    Args:
        name: Nombre de la herramienta que requiere aprobacion.
        args: Argumentos de la llamada a la herramienta.

    Returns:
        ``"y"`` (si), ``"n"`` (no), o ``"a"`` (si, siempre para esta herramienta).
    """
    args_repr = ", ".join(f"{k}={repr(v)[:60]}" for k, v in args.items())
    print(f"{YELLOW}⚠  ¿Ejecutar {WHITE}{name}({args_repr}){YELLOW}?{RESET}")
    print(
        f"   {GREEN}[y]{RESET} Sí   {RED}[n]{RESET} No   "
        f"{CYAN}[a]{RESET} Sí, siempre para {name}"
    )

    while True:
        try:
            choice = input(f"   {DIM}>{RESET} ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            return "n"
        if choice in ("y", "n", "a", ""):
            return choice or "y"
