"""Herramientas de filesystem para el agente nineteen.

Implementa operaciones de archivos y sistema que el agente puede ejecutar:
listar directorios, leer, escribir, eliminar, renombrar, copiar archivos,
crear directorios, cambiar de directorio, buscar en archivos, vista de arbol,
informacion de archivos y ejecucion de comandos.

Todas las funciones retornan cadenas: resultado legible en exito,
o mensaje con prefijo ``"ERROR: "`` en caso de fallo.

Dependencias: solo stdlib (``pathlib``, ``os``, ``shutil``, ``subprocess``).
"""

from __future__ import annotations

import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from nineteen.tools.base import ToolRegistry, ToolSpec

_BLOCKED_COMMANDS = frozenset(
    {
        "rm -rf /",
        "rm -rf /*",
        "mkfs",
        "dd",
        ":(){ :|:& };:",
        "format",
        "shutdown",
        "reboot",
        "halt",
        "poweroff",
        "del /f /s /q",
        "rd /s /q",
    }
)
"""Comandos peligrosos que run_command rechaza sin ejecutar."""

_RUN_TIMEOUT = 30
"""Timeout en segundos para run_command."""


def _list_dir(path: str) -> str:
    """Lista el contenido de un directorio.

    Args:
        path: Ruta al directorio a listar. Acepta ``~`` y rutas relativas.

    Returns:
        Lista de entradas con prefijo ``DIR `` o ``FILE``, ordenadas
        (directorios primero, luego archivos en orden alfabetico).
        Si el directorio esta vacio, retorna ``"(empty directory)"``.
        En caso de error, retorna un mensaje con prefijo ``"ERROR: "``.
    """
    p = Path(path).expanduser().resolve()
    if not p.exists():
        return f"ERROR: Path does not exist: {path}"
    if not p.is_dir():
        return f"ERROR: Not a directory: {path}"
    entries = sorted(p.iterdir(), key=lambda x: (x.is_file(), x.name.lower()))
    if not entries:
        return "(empty directory)"
    lines = []
    for entry in entries:
        kind = "FILE" if entry.is_file() else "DIR "
        lines.append(f"{kind}  {entry.name}")
    return "\n".join(lines)


def _read_file(path: str) -> str:
    """Lee el contenido completo de un archivo de texto.

    Args:
        path: Ruta al archivo a leer. Acepta ``~`` y rutas relativas.

    Returns:
        Contenido del archivo como cadena UTF-8.
        En caso de error (archivo inexistente, directorio, o binario), retorna
        un mensaje con prefijo ``"ERROR: "``.
    """
    p = Path(path).expanduser().resolve()
    if not p.exists():
        return f"ERROR: File does not exist: {path}"
    if not p.is_file():
        return f"ERROR: Not a file: {path}"
    try:
        return p.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return "ERROR: File is not valid UTF-8 text."


def _write_file(path: str, content: str) -> str:
    """Escribe contenido de texto en un archivo.

    Crea el archivo si no existe. Crea los directorios intermedios si son necesarios.
    Si el archivo ya existe, su contenido es reemplazado completamente.

    Args:
        path: Ruta destino del archivo. Acepta ``~`` y rutas relativas.
        content: Contenido de texto a escribir (UTF-8).

    Returns:
        Mensaje de confirmacion con la cantidad de caracteres escritos y la ruta absoluta.
    """
    p = Path(path).expanduser().resolve()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return f"OK: Written {len(content)} characters to {p}"


def _delete_file(path: str) -> str:
    """Elimina un archivo del sistema de archivos.

    No elimina directorios. Para eso usar herramientas del sistema operativo.

    Args:
        path: Ruta al archivo a eliminar. Acepta ``~`` y rutas relativas.

    Returns:
        Mensaje de confirmacion con la ruta absoluta eliminada.
        En caso de error (archivo inexistente o es un directorio), retorna
        un mensaje con prefijo ``"ERROR: "``.
    """
    p = Path(path).expanduser().resolve()
    if not p.exists():
        return f"ERROR: File does not exist: {path}"
    if p.is_dir():
        return f"ERROR: '{path}' is a directory. This tool only deletes files."
    p.unlink()
    return f"OK: Deleted {p}"


def _rename_file(src: str, dst: str) -> str:
    """Renombra o mueve un archivo.

    Equivale a ``mv src dst``. Si ``dst`` es una ruta diferente, actua como mover.

    Args:
        src: Ruta de origen. Acepta ``~`` y rutas relativas.
        dst: Ruta de destino. Acepta ``~`` y rutas relativas.

    Returns:
        Mensaje de confirmacion con las rutas absolutas de origen y destino.
        En caso de error (origen inexistente), retorna un mensaje con prefijo ``"ERROR: "``.
    """
    s = Path(src).expanduser().resolve()
    d = Path(dst).expanduser().resolve()
    if not s.exists():
        return f"ERROR: Source does not exist: {src}"
    s.rename(d)
    return f"OK: Renamed {s} -> {d}"


# -- Herramientas nuevas: directorio --------------------------------------------


def _make_dir(path: str) -> str:
    """Crea un directorio, incluyendo directorios intermedios si es necesario.

    Args:
        path: Ruta del directorio a crear. Acepta ``~`` y rutas relativas.

    Returns:
        Mensaje de confirmacion con la ruta absoluta creada.
        Si el directorio ya existe, lo indica sin error.
    """
    p = Path(path).expanduser().resolve()
    if p.exists() and p.is_dir():
        return f"OK: Directory already exists: {p}"
    if p.exists() and not p.is_dir():
        return f"ERROR: Path exists but is not a directory: {p}"
    try:
        p.mkdir(parents=True, exist_ok=True)
        return f"OK: Created directory {p}"
    except OSError as e:
        return f"ERROR: Could not create directory: {e}"


def _change_dir(path: str) -> str:
    """Cambia el directorio de trabajo actual del proceso.

    Args:
        path: Ruta al directorio destino. Acepta ``~`` y rutas relativas.

    Returns:
        Mensaje de confirmacion con el nuevo directorio de trabajo.
        En caso de error, retorna un mensaje con prefijo ``"ERROR: "``.
    """
    p = Path(path).expanduser().resolve()
    if not p.exists():
        return f"ERROR: Path does not exist: {path}"
    if not p.is_dir():
        return f"ERROR: Not a directory: {path}"
    try:
        os.chdir(p)
        return f"OK: Changed working directory to {p}"
    except OSError as e:
        return f"ERROR: Could not change directory: {e}"


def _get_cwd() -> str:
    """Retorna el directorio de trabajo actual.

    Returns:
        Ruta absoluta del directorio de trabajo actual.
    """
    return str(Path.cwd())


def _copy_file(src: str, dst: str) -> str:
    """Copia un archivo preservando metadatos.

    Args:
        src: Ruta de origen. Acepta ``~`` y rutas relativas.
        dst: Ruta de destino. Acepta ``~`` y rutas relativas.

    Returns:
        Mensaje de confirmacion con las rutas absolutas.
        En caso de error, retorna un mensaje con prefijo ``"ERROR: "``.
    """
    s = Path(src).expanduser().resolve()
    d = Path(dst).expanduser().resolve()
    if not s.exists():
        return f"ERROR: Source does not exist: {src}"
    if not s.is_file():
        return f"ERROR: Source is not a file: {src}"
    try:
        d.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(s, d)
        return f"OK: Copied {s} -> {d}"
    except OSError as e:
        return f"ERROR: Copy failed: {e}"


def _file_info(path: str) -> str:
    """Retorna informacion sobre un archivo o directorio.

    Args:
        path: Ruta al archivo o directorio. Acepta ``~`` y rutas relativas.

    Returns:
        Cadena con tipo, tamanio, permisos y fechas de modificacion/creacion.
        En caso de error, retorna un mensaje con prefijo ``"ERROR: "``.
    """
    p = Path(path).expanduser().resolve()
    if not p.exists():
        return f"ERROR: Path does not exist: {path}"
    try:
        stat = p.stat()
        kind = "directory" if p.is_dir() else "file"
        size = stat.st_size
        # Human-readable size
        if size < 1024:
            size_str = f"{size} B"
        elif size < 1024 * 1024:
            size_str = f"{size / 1024:.1f} KB"
        else:
            size_str = f"{size / (1024 * 1024):.1f} MB"
        mtime = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).strftime(
            "%Y-%m-%d %H:%M:%S UTC"
        )
        perms = oct(stat.st_mode)[-3:]
        lines = [
            f"Path: {p}",
            f"Type: {kind}",
            f"Size: {size_str} ({size} bytes)",
            f"Permissions: {perms}",
            f"Modified: {mtime}",
        ]
        return "\n".join(lines)
    except OSError as e:
        return f"ERROR: Could not get file info: {e}"


def _search_in_files(pattern: str, path: str) -> str:
    """Busca un patron de texto en archivos dentro de un directorio (recursivo).

    Equivale a ``grep -rn pattern path``. Solo busca en archivos de texto UTF-8.
    Ignora directorios ocultos y archivos binarios.

    Args:
        pattern: Texto a buscar (case-sensitive, no regex).
        path: Directorio raiz donde buscar. Acepta ``~`` y rutas relativas.

    Returns:
        Coincidencias en formato ``archivo:linea: contenido``, limitadas a 50 resultados.
        Si no hay coincidencias, retorna ``"No matches found."``.
    """
    root = Path(path).expanduser().resolve()
    if not root.exists():
        return f"ERROR: Path does not exist: {path}"
    if not root.is_dir():
        return f"ERROR: Not a directory: {path}"

    matches: list[str] = []
    max_matches = 50

    # Skip hidden dirs and common non-text directories
    skip_dirs = {".git", ".venv", "__pycache__", "node_modules", ".mypy_cache"}

    for file_path in _walk_files(root, skip_dirs):
        try:
            text = file_path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for i, line in enumerate(text.splitlines(), 1):
            if pattern in line:
                rel = file_path.relative_to(root)
                matches.append(f"{rel}:{i}: {line.rstrip()[:120]}")
                if len(matches) >= max_matches:
                    matches.append(f"... (truncated at {max_matches} matches)")
                    return "\n".join(matches)

    if not matches:
        return "No matches found."
    return "\n".join(matches)


def _walk_files(root: Path, skip_dirs: set[str]) -> list[Path]:
    """Recorre recursivamente un directorio retornando archivos regulares.

    Omite directorios ocultos (que empiezan con '.') y los listados en skip_dirs.
    """
    files: list[Path] = []
    try:
        for entry in sorted(root.iterdir(), key=lambda x: x.name.lower()):
            if entry.is_dir():
                if entry.name.startswith(".") or entry.name in skip_dirs:
                    continue
                files.extend(_walk_files(entry, skip_dirs))
            elif entry.is_file():
                files.append(entry)
    except PermissionError:
        pass
    return files


def _tree(path: str, max_depth: int = 3) -> str:
    """Genera una vista de arbol del directorio, similar al comando ``tree``.

    Args:
        path: Directorio raiz. Acepta ``~`` y rutas relativas.
        max_depth: Profundidad maxima del arbol (default: 3).

    Returns:
        Representacion de arbol con indentacion.
        En caso de error, retorna un mensaje con prefijo ``"ERROR: "``.
    """
    root = Path(path).expanduser().resolve()
    if not root.exists():
        return f"ERROR: Path does not exist: {path}"
    if not root.is_dir():
        return f"ERROR: Not a directory: {path}"

    skip_dirs = {".git", ".venv", "__pycache__", "node_modules", ".mypy_cache"}
    lines = [f"{root.name}/"]
    _tree_recurse(root, "", lines, skip_dirs, 0, max_depth)

    if len(lines) > 200:
        lines = lines[:200]
        lines.append("... (truncated at 200 entries)")
    return "\n".join(lines)


def _tree_recurse(
    directory: Path,
    prefix: str,
    lines: list[str],
    skip_dirs: set[str],
    depth: int,
    max_depth: int,
) -> None:
    """Funcion recursiva interna para construir el arbol."""
    if depth >= max_depth:
        return
    try:
        entries = sorted(
            directory.iterdir(), key=lambda x: (x.is_file(), x.name.lower())
        )
    except PermissionError:
        return

    # Filter out hidden/skipped dirs
    entries = [
        e
        for e in entries
        if not (e.is_dir() and (e.name.startswith(".") or e.name in skip_dirs))
    ]

    for i, entry in enumerate(entries):
        is_last = i == len(entries) - 1
        connector = "└── " if is_last else "├── "
        suffix = "/" if entry.is_dir() else ""
        lines.append(f"{prefix}{connector}{entry.name}{suffix}")
        if entry.is_dir():
            extension = "    " if is_last else "│   "
            _tree_recurse(
                entry, prefix + extension, lines, skip_dirs, depth + 1, max_depth
            )


def _run_command(command: str) -> str:
    """Ejecuta un comando del sistema y retorna su salida.

    El comando se ejecuta con un timeout de 30 segundos. Comandos peligrosos
    conocidos son bloqueados automaticamente.

    Args:
        command: Comando a ejecutar (se pasa a la shell del sistema).

    Returns:
        Salida combinada (stdout + stderr) del comando, o mensaje de error.
        La salida se trunca a 3000 caracteres.
    """
    cmd_lower = command.strip().lower()
    for blocked in _BLOCKED_COMMANDS:
        if blocked in cmd_lower:
            return f"ERROR: Command blocked for safety: {command}"

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=_RUN_TIMEOUT,
            cwd=os.getcwd(),
        )
        output = ""
        if result.stdout:
            output += result.stdout
        if result.stderr:
            if output:
                output += "\n"
            output += result.stderr

        if not output.strip():
            output = f"(command exited with code {result.returncode}, no output)"

        if result.returncode != 0:
            output = f"[exit code {result.returncode}]\n{output}"

        # Truncate long output
        if len(output) > 3000:
            output = output[:3000] + "\n... (truncated at 3000 characters)"

        return output
    except subprocess.TimeoutExpired:
        return f"ERROR: Command timed out after {_RUN_TIMEOUT} seconds."
    except OSError as e:
        return f"ERROR: Could not execute command: {e}"


def build_default_registry() -> ToolRegistry:
    """Construye y retorna el ``ToolRegistry`` con todas las herramientas del agente.

    Returns:
        Instancia de ``ToolRegistry`` lista para usar con el agente.
    """
    reg = ToolRegistry()

    # -- Filesystem: lectura y navegacion
    reg.register(
        ToolSpec(
            name="get_cwd",
            description="Get the current working directory.",
            signature="",
            func=_get_cwd,
        )
    )
    reg.register(
        ToolSpec(
            name="change_dir",
            description="Change the current working directory.",
            signature="path: str",
            func=_change_dir,
        )
    )
    reg.register(
        ToolSpec(
            name="list_dir",
            description="List the contents of a directory.",
            signature="path: str",
            func=_list_dir,
        )
    )
    reg.register(
        ToolSpec(
            name="tree",
            description="Show a tree view of a directory structure. max_depth defaults to 3.",
            signature="path: str, max_depth: int?",
            func=_tree,
        )
    )
    reg.register(
        ToolSpec(
            name="file_info",
            description="Get metadata about a file or directory (size, permissions, dates).",
            signature="path: str",
            func=_file_info,
        )
    )
    reg.register(
        ToolSpec(
            name="search_in_files",
            description="Search for a text pattern in files within a directory (recursive, like grep -rn).",
            signature="pattern: str, path: str",
            func=_search_in_files,
        )
    )

    # -- Filesystem: escritura y mutacion
    reg.register(
        ToolSpec(
            name="read_file",
            description="Read the full text content of a file (UTF-8).",
            signature="path: str",
            func=_read_file,
        )
    )
    reg.register(
        ToolSpec(
            name="write_file",
            description="Write text content to a file, creating it if it does not exist.",
            signature="path: str, content: str",
            func=_write_file,
        )
    )
    reg.register(
        ToolSpec(
            name="copy_file",
            description="Copy a file preserving metadata.",
            signature="src: str, dst: str",
            func=_copy_file,
        )
    )
    reg.register(
        ToolSpec(
            name="rename_file",
            description="Rename or move a file.",
            signature="src: str, dst: str",
            func=_rename_file,
        )
    )
    reg.register(
        ToolSpec(
            name="delete_file",
            description="Delete a file. Does not delete directories.",
            signature="path: str",
            func=_delete_file,
        )
    )
    reg.register(
        ToolSpec(
            name="make_dir",
            description="Create a directory, including intermediate directories if needed.",
            signature="path: str",
            func=_make_dir,
        )
    )

    # -- Sistema
    reg.register(
        ToolSpec(
            name="run_command",
            description="Execute a shell command and return its output. Times out after 30s.",
            signature="command: str",
            func=_run_command,
        )
    )

    return reg
