"""Sub-paquete de herramientas para el agente nineteen.

Re-exporta las abstracciones publicas del sistema de herramientas:

- `ToolSpec`: dataclass que describe una herramienta registrable.
- `ToolRegistry`: registro central de herramientas.
- `build_default_registry`: fabrica del registry con todas las herramientas del agente.
- `_build_tools_schema`: conversion del registry al esquema nativo de Ollama.
"""

from nineteen.tools.base import ToolRegistry, ToolSpec, _build_tools_schema
from nineteen.tools.filesystem import build_default_registry

__all__ = [
    "ToolSpec",
    "ToolRegistry",
    "build_default_registry",
    "_build_tools_schema",
]
