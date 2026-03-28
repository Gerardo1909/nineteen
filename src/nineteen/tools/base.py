"""
Sistema de herramientas pluggable para el agente nineteen.

Provee las abstracciones base (``ToolSpec``, ``ToolRegistry``) para registrar
y ejecutar herramientas. La conversión al esquema de wire de cada proveedor
es responsabilidad del adaptador correspondiente (ver ``providers/ollama.py``).

Dependencias: ninguna (solo stdlib).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class ToolSpec:
    """Especificación de una herramienta registrable en el agente.

    Attributes:
        name: Identificador único de la herramienta (p. ej. ``"list_dir"``).
        description: Descripción en inglés que el modelo usará para elegir la herramienta.
        signature: Firma de parámetros como cadena (p. ej. ``"path: str"``).
            Debe seguir el formato ``"param: type, param2: type2"``.
        func: Función Python que implementa la herramienta.
            Debe aceptar los parámetros definidos en ``signature`` y retornar ``str``.
    """

    name: str
    description: str
    signature: str
    func: Callable[..., str]


class ToolRegistry:
    """Registro central de herramientas disponibles para el agente.

    Permite registrar, consultar y ejecutar herramientas de forma segura.
    El agente instancia un único ``ToolRegistry`` y lo pasa al bucle agentico.

    Example:
        >>> reg = ToolRegistry()
        >>> reg.register(ToolSpec(name="echo", description="Echo", signature="msg: str", func=lambda msg: msg))
        >>> reg.call("echo", {"msg": "hola"})
        'hola'
    """

    def __init__(self) -> None:
        self._tools: dict[str, ToolSpec] = {}

    def register(self, spec: ToolSpec) -> None:
        """Registra una herramienta en el registro.

        Args:
            spec: Especificación de la herramienta a registrar.
                Si ya existe una herramienta con el mismo nombre, se sobreescribe.
        """
        self._tools[spec.name] = spec

    def get(self, name: str) -> ToolSpec | None:
        """Obtiene la especificación de una herramienta por nombre.

        Args:
            name: Nombre de la herramienta a buscar.

        Returns:
            El ``ToolSpec`` correspondiente, o ``None`` si no existe.
        """
        return self._tools.get(name)

    def __len__(self) -> int:
        """Retorna la cantidad de herramientas registradas."""
        return len(self._tools)

    def descriptions(self) -> str:
        """Retorna una lista legible de todas las herramientas registradas.

        Returns:
            Cadena multilínea con el formato ``- nombre(firma): descripción``
            para cada herramienta registrada.
        """
        lines = []
        for spec in self._tools.values():
            lines.append(f"- {spec.name}({spec.signature}): {spec.description}")
        return "\n".join(lines)

    def call(self, name: str, args: dict[str, Any]) -> str:
        """Ejecuta una herramienta por nombre con los argumentos dados.

        Args:
            name: Nombre de la herramienta a ejecutar.
            args: Diccionario de argumentos a pasar a la función de la herramienta.

        Returns:
            Resultado de la herramienta como cadena. Si la herramienta no existe
            o falla, retorna un mensaje de error con prefijo ``"ERROR: "``.
        """
        spec = self.get(name)
        if spec is None:
            return f"ERROR: Unknown tool '{name}'. Available: {', '.join(self._tools)}"
        try:
            return spec.func(**args)
        except TypeError as e:
            return f"ERROR: Wrong arguments for '{name}': {e}"
        except Exception as e:
            return f"ERROR: Tool '{name}' failed: {e}"
