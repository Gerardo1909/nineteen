"""
Sub-paquete de herramientas para el agente nineteen.

Re-exporta las abstracciones públicas del sistema de herramientas:

- ``ToolSpec``: dataclass que describe una herramienta registrable.
- ``ToolRegistry``: registro central de herramientas.
- ``build_default_registry``: fábrica del registry con todas las herramientas del agente.
"""

from nineteen.tools.base import ToolRegistry, ToolSpec
from nineteen.tools.filesystem import build_default_registry

__all__ = [
    "ToolSpec",
    "ToolRegistry",
    "build_default_registry",
]
