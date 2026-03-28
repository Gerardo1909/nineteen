"""Sub-paquete de proveedores LLM para el agente nineteen.

Re-exporta el puerto (``LLMProvider``) y los tipos normalizados junto con
el adaptador Ollama por defecto.

Para agregar un nuevo backend, implementar el protocolo ``LLMProvider``
en un módulo nuevo (ej. ``providers/llamacpp.py``) sin modificar este paquete.
"""

from nineteen.providers.base import ChatChunk, LLMProvider, ToolCallData, ToolCallFunction
from nineteen.providers.ollama import OllamaProvider

__all__ = [
    "LLMProvider",
    "ChatChunk",
    "ToolCallData",
    "ToolCallFunction",
    "OllamaProvider",
]
