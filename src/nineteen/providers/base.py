"""
Puerto LLMProvider: abstracción del proveedor de lenguaje para el agente nineteen.

Define el protocolo que cualquier backend de LLM debe implementar, junto con
los tipos normalizados que fluyen entre el proveedor y el agente.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterator, Optional, Protocol, runtime_checkable


@dataclass
class ToolCallFunction:
    """
    Datos de la función invocada dentro de un tool call.

    Attributes:
        name: Nombre de la herramienta a ejecutar.
        arguments: Argumentos de la llamada como diccionario.
    """

    name: str
    arguments: dict[str, Any]


@dataclass
class ToolCallData:
    """
    Representación normalizada de un tool call emitido por el modelo.

    Attributes:
        function: Datos de la función a invocar.
    """

    function: ToolCallFunction


@dataclass
class ChatChunk:
    """
    Fragmento normalizado de una respuesta en streaming del modelo.

    Attributes:
        content: Texto de respuesta del asistente (puede ser vacío en un chunk).
        thinking: Bloque de razonamiento interno. ``None`` si el proveedor o
            modelo no soporta thinking; cadena vacía si lo soporta pero no
            produjo nada en este chunk.
        tool_calls: Lista de tool calls emitidos en este chunk (generalmente
            llega todo en un solo chunk al final del stream).
    """

    content: str = ""
    thinking: Optional[str] = None
    tool_calls: list[ToolCallData] = field(default_factory=list)


@runtime_checkable
class LLMProvider(Protocol):
    """
    Protocolo (puerto) que todo backend de LLM debe implementar.

    El agente depende únicamente de esta interfaz — nunca de un SDK concreto.
    Los adaptadores (``OllamaProvider``, etc.) implementan este protocolo
    sin necesidad de herencia explícita.
    """

    def chat_stream(self, messages: list[dict]) -> Iterator[ChatChunk]:
        """Envía el historial de mensajes al modelo y retorna chunks normalizados.

        Args:
            messages: Historial de mensajes en formato OpenAI
                (``[{"role": "...", "content": "..."}]``).

        Yields:
            ``ChatChunk`` con el contenido parcial, thinking y/o tool calls
            de cada fragmento del stream.
        """
        ...
