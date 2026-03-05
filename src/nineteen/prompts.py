"""Gestión del system prompt del agente nineteen.

Define las instrucciones base que se envían al modelo al inicio de cada
sesión, guiando su comportamiento para usar herramientas de forma efectiva
y responder de manera concisa.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nineteen.tools.base import ToolRegistry

_SYSTEM_TEMPLATE = """\
You are a helpful AI assistant running on the user's local machine.
You have access to {tool_count} tools to interact with the filesystem and system.

Available tools:
{tool_list}

Guidelines:
- Use tools when the task requires interacting with the filesystem or running commands.
- When using list_dir, use "." for the current directory.
- Use get_cwd to check where you are before operating on relative paths.
- Keep your final answer concise and relevant to the user's request.
- If a tool returns an error, report it clearly to the user.
- For dangerous operations (deleting files, running commands), confirm intent when unclear.
"""
"""System prompt template del agente.

Placeholders:
- ``{tool_count}``: numero de herramientas disponibles.
- ``{tool_list}``: lista formateada de herramientas desde el registry.
"""


def build_system_prompt(registry: ToolRegistry | None = None) -> str:
    """Construye y retorna el system prompt completo para el agente.

    Si se provee un registry, el prompt incluye la lista de herramientas
    disponibles de forma dinamica. Si no, usa un fallback generico.

    Args:
        registry: Registro de herramientas del agente. Si es ``None``,
            se genera un prompt generico sin lista de herramientas.

    Returns:
        Cadena con el system prompt listo para usar como mensaje de sistema.
    """
    if registry is None:
        return _SYSTEM_TEMPLATE.format(
            tool_count="several",
            tool_list="(tool list not available)",
        )
    return _SYSTEM_TEMPLATE.format(
        tool_count=len(registry),
        tool_list=registry.descriptions(),
    )
