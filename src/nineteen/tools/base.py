"""Sistema de herramientas pluggable para el agente nineteen.

Provee las abstracciones base (`ToolSpec`, `ToolRegistry`) y las utilidades
para convertir el registro al esquema de herramientas nativo de Ollama.

Dependencias: ninguna (solo stdlib).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

_TYPE_MAP: dict[str, str] = {
    "str": "string",
    "int": "integer",
    "float": "number",
    "bool": "boolean",
}
"""Conversión de nombres de tipo Python a tipos JSON Schema.

Solo cubre los tipos primitivos utilizados en las firmas de herramientas.
Cualquier tipo no listado aquí se mapea a ``"string"`` por defecto.
"""


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


def _build_tools_schema(registry: ToolRegistry) -> list[dict]:
    """Convierte un ``ToolRegistry`` al formato de herramientas nativo de Ollama.

    Ollama espera una lista de objetos con estructura ``{"type": "function", "function": {...}}``.
    Esta funcion genera esa lista a partir de los ``ToolSpec`` registrados.

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


def _parse_signature(sig: str) -> dict[str, tuple[str, bool]]:
    """Parsea una firma de parametros a un diccionario nombre -> (tipo, opcional).

    Usa el sufijo ``?`` en el tipo para marcar parametros opcionales.
    Por ejemplo: ``"path: str, max_depth: int?"`` marca ``max_depth`` como opcional.

    Args:
        sig: Cadena con formato ``"param: tipo, param2: tipo2?"``
            (p. ej. ``"path: str, count: int?"``).

    Returns:
        Diccionario ``{nombre_param: (tipo_json_schema, es_opcional)}``.
        Tipos no reconocidos se mapean a ``"string"``.

    Example:
        >>> _parse_signature("path: str, count: int?")
        {'path': ('string', False), 'count': ('integer', True)}
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
