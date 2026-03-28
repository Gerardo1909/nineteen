"""
Adaptador Ollama para el protocolo LLMProvider.

Implementa ``LLMProvider`` usando el cliente oficial de Ollama. Es el único
módulo en el proyecto que importa el SDK de ``ollama``.

También contiene la lógica de conversión del ``ToolRegistry`` al esquema de
herramientas nativo de Ollama (formato OpenAI-compatible).
"""

from __future__ import annotations

from typing import Iterator, Optional

import ollama

from nineteen.providers.base import ChatChunk, ToolCallData, ToolCallFunction
from nineteen.tools.base import ToolRegistry

_TYPE_MAP: dict[str, str] = {
    "str": "string",
    "int": "integer",
    "float": "number",
    "bool": "boolean",
}
"""Conversión de nombres de tipo Python a tipos JSON Schema."""


def _parse_signature(sig: str) -> dict[str, tuple[str, bool]]:
    """
    Parsea una firma de parámetros a un diccionario nombre -> (tipo, opcional).

    Args:
        sig: Cadena con formato ``"param: tipo, param2: tipo2?"``

    Returns:
        Diccionario ``{nombre_param: (tipo_json_schema, es_opcional)}``.
    """
    result = {}
    for part in sig.split(","):
        part = part.strip()
        if ":" in part:
            name, type_hint = part.split(":", 1)
            py_type = type_hint.strip()
            optional = py_type.endswith("?")
            if optional:
                py_type = py_type[:-1]
            result[name.strip()] = (_TYPE_MAP.get(py_type, "string"), optional)
    return result


def _build_tools_schema(registry: ToolRegistry) -> list[dict]:
    """
    Convierte un ``ToolRegistry`` al formato de herramientas nativo de Ollama.

    Args:
        registry: Registro de herramientas a convertir.

    Returns:
        Lista de diccionarios en formato ``tools`` compatible con ``ollama.chat()``.
    """
    tools = []
    for spec in registry._tools.values():
        params = _parse_signature(spec.signature)
        required = [name for name, (_type, optional) in params.items() if not optional]
        tools.append(
            {
                "type": "function",
                "function": {
                    "name": spec.name,
                    "description": spec.description,
                    "parameters": {
                        "type": "object",
                        "properties": {
                            p_name: {"type": p_type, "description": p_name}
                            for p_name, (p_type, _opt) in params.items()
                        },
                        "required": required,
                    },
                },
            }
        )
    return tools


class OllamaProvider:
    """
    Adaptador que implementa ``LLMProvider`` usando el servidor Ollama local.

    Convierte el ``ToolRegistry`` al esquema nativo de Ollama una vez en
    ``__init__`` para no reconstruirlo en cada llamada.

    Attributes:
        model: Nombre del modelo Ollama activo (p. ej. ``"qwen3:0.6b"``).
    """

    def __init__(
        self,
        model: str = "qwen3:0.6b",
        registry: Optional[ToolRegistry] = None,
    ) -> None:
        """
        Inicializa el proveedor con el modelo y herramientas disponibles.

        Args:
            model: Nombre del modelo instalado en Ollama.
            registry: Registro de herramientas. Si es ``None``, el provider
                no envía esquema de tools al modelo (útil para pruebas).
        """
        self.model = model
        self._tools_schema = _build_tools_schema(registry) if registry else []

    def chat_stream(self, messages: list[dict]) -> Iterator[ChatChunk]:
        """
        Envía mensajes a Ollama y normaliza la respuesta en ``ChatChunk``.

        Siempre usa ``stream=True`` internamente. Temperature fijada a 0 para
        tool calling estable y reproducible.

        Args:
            messages: Historial de mensajes en formato OpenAI.

        Yields:
            ``ChatChunk`` con content, thinking y/o tool_calls normalizados.
        """
        for chunk in ollama.chat(
            model=self.model,
            messages=messages,
            tools=self._tools_schema,
            options={"temperature": 0},
            stream=True,
        ):
            tool_calls = [
                ToolCallData(
                    function=ToolCallFunction(
                        name=tc.function.name,
                        arguments=dict(tc.function.arguments),
                    )
                )
                for tc in (chunk.message.tool_calls or [])
            ]
            yield ChatChunk(
                content=chunk.message.content or "",
                thinking=chunk.message.thinking,
                tool_calls=tool_calls,
            )
