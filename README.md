# nineteen

> El agente de IA local pensado para equipos sin GPU.

```
  ██   ████
 ███   ██  ██
  ██   ██  ██
  ██   █████
  ██       ██
  ██   ██  ██
 ████   ████
```

**nineteen** es un agente CLI minimalista que ejecuta modelos de lenguaje localmente mediante Ollama
y les da acceso a herramientas de filesystem y sistema usando tool calling nativo. Sin GPU. Sin la nube.
Sin dependencias pesadas.

---

## ¿Por qué nineteen?

Las alternativas populares (Aider, Open Interpreter, OpenClaw) asumen que tenés una GPU o acceso
a una API cloud. En hardware modesto — un Ryzen 5, 16 GB RAM, sin VRAM — simplemente no funcionan.

nineteen nació para ese escenario: modelos de 731 MB corriendo en CPU pura, con tool calling
nativo de Ollama, sin ReAct personalizado ni parseo frágil de texto.

---

## Características

- ✅ Funciona en CPU pura (sin GPU, sin VRAM)
- ✅ Modelos desde 731 MB (`lfm2.5-thinking:1.2b`)
- ✅ 13 herramientas integradas (filesystem, navegación, búsqueda, shell)
- ✅ Modo interactivo + one-shot
- ✅ Native Ollama tool calling (sin ReAct)
- ✅ Arquitectura pluggable — agregá herramientas fácilmente
- ✅ Sin dependencias pesadas (solo `ollama` + `click`)

---

## Instalación

**Requisitos previos:**
- [Ollama](https://ollama.com) instalado y corriendo
- Python 3.13+
- [uv](https://docs.astral.sh/uv/) (recomendado) o pip

### Instalación global (recomendado)

Instala `nineteen` como comando global disponible desde cualquier terminal:

```bash
git clone <repo-url>
cd nineteen
uv tool install -e .

# Descargar el modelo por defecto
ollama pull lfm2.5-thinking:1.2b
```

Después de esto, el comando `nineteen` queda disponible globalmente sin necesidad
de activar ningún entorno virtual.

### Alternativa: desarrollo local

Si estás trabajando en el código del agente:

```bash
git clone <repo-url>
cd nineteen
uv sync

# Ejecutar sin activar el venv
uv run nineteen

# O activar el venv y usar directamente
source .venv/bin/activate   # Linux/macOS
.venv\Scripts\activate      # Windows
nineteen
```

---

## Uso

### Modo interactivo

```bash
nineteen
```

El agente muestra el logo, el modelo activo y la cantidad de herramientas cargadas.
Escribí tu tarea en lenguaje natural y presioná Enter.

```

    ██   ████
   ███   ██  ██
    ██   ██  ██
    ██   █████
    ██       ██
    ██   ██  ██
   ████   ████

┌──────────────────────────────────────────────────────┐
│  nineteen  v0.1.0                                    │
│  model: lfm2.5-thinking:1.2b  •  tools: 13 cargadas  │
│  Escribe 'exit' o Ctrl-C para salir                  │
└──────────────────────────────────────────────────────┘


❯ Hola
Hola! ¿Cómo estás? ¿En qué puedo ayudarte?
```

### Modo one-shot

```bash
nineteen run "list files in the current directory"
nineteen run "read the file pyproject.toml and summarize it"
```

### Variables de entorno

| Variable          | Descripción                       | Default                   |
|-------------------|-----------------------------------|---------------------------|
| `NINETEEN_MODEL`  | Modelo Ollama a usar              | `lfm2.5-thinking:1.2b`    |

### Opciones CLI

```
nineteen [OPTIONS] COMMAND [ARGS]...

Options:
  -m, --model TEXT       Modelo Ollama a usar
  --max-steps INTEGER    Máximo de pasos por tarea (default: 10)
  -V, --version          Muestra la versión y sale
  -h, --help             Muestra la ayuda

Commands:
  run    Ejecuta una tarea one-shot y sale
```

---

## Herramientas disponibles

### Navegación y lectura

| Herramienta        | Firma                              | Descripción                                        |
|--------------------|------------------------------------|----------------------------------------------------|
| `get_cwd`          | *(sin parámetros)*                 | Retorna el directorio de trabajo actual             |
| `change_dir`       | `path: str`                        | Cambia el directorio de trabajo                     |
| `list_dir`         | `path: str`                        | Lista el contenido de un directorio                 |
| `tree`             | `path: str, max_depth?: int`       | Vista de árbol del directorio (default depth: 3)    |
| `file_info`        | `path: str`                        | Metadata de un archivo (tamaño, permisos, fechas)   |
| `search_in_files`  | `pattern: str, path: str`          | Busca texto en archivos recursivamente (como grep)  |

### Escritura y mutación

| Herramienta    | Firma                          | Descripción                                      |
|----------------|--------------------------------|--------------------------------------------------|
| `read_file`    | `path: str`                    | Lee el contenido completo de un archivo (UTF-8)  |
| `write_file`   | `path: str, content: str`      | Escribe texto en un archivo (crea si no existe)  |
| `copy_file`    | `src: str, dst: str`           | Copia un archivo preservando metadata            |
| `rename_file`  | `src: str, dst: str`           | Renombra o mueve un archivo                      |
| `delete_file`  | `path: str`                    | Elimina un archivo (no directorios)              |
| `make_dir`     | `path: str`                    | Crea un directorio (incluyendo intermedios)      |

### Sistema

| Herramienta    | Firma                          | Descripción                                      |
|----------------|--------------------------------|--------------------------------------------------|
| `run_command`  | `command: str`                 | Ejecuta un comando shell (timeout: 30s)          |

---

## Modelos recomendados

| Modelo                    | Tamaño  | Hardware mínimo       | Tool calling |
|---------------------------|---------|-----------------------|--------------|
| `lfm2.5-thinking:1.2b`    | 731 MB  | 4 GB RAM, CPU         | ✅ nativo    |
| `qwen2.5:3b`              | 1.9 GB  | 8 GB RAM, CPU         | ✅ nativo    |
| `llama3.2:3b`             | 2.0 GB  | 8 GB RAM, CPU         | ✅ nativo    |
| `mistral:7b`              | 4.1 GB  | 8 GB RAM, CPU/GPU     | ✅ nativo    |

Cambiá el modelo con:
```bash
NINETEEN_MODEL=qwen2.5:3b nineteen
```

---

## Comparativa con alternativas

| Herramienta       | CPU-only | Modelos <3B | Sin GPU | Ligero |
|-------------------|----------|-------------|---------|--------|
| Aider             | ~        | ✗           | ✗       | ~      |
| Open Interpreter  | ~        | ✗           | ✗       | ✗      |
| OpenClaw          | ✗        | ✗           | ✗       | ✗      |
| **nineteen**      | **✅**   | **✅**       | **✅**  | **✅** |

---

## Arquitectura

```
src/nineteen/
├── __init__.py          # versión del paquete
├── __main__.py          # python -m nineteen
├── cli.py               # Click CLI (interfaz delgada)
├── prompts.py           # system prompt dinámico del agente
├── display.py           # salida ANSI + logo pixelado
├── agent/
│   ├── __init__.py      # re-exporta Agent
│   └── core.py          # clase Agent + bucle agentico
└── tools/
    ├── __init__.py      # re-exporta ToolSpec, ToolRegistry, build_default_registry
    ├── base.py          # ToolSpec, ToolRegistry, schema builder
    └── filesystem.py    # 13 herramientas + build_default_registry()
```

**Decisiones de diseño:**
- **Non-streaming**: la respuesta completa se recolecta antes de mostrarla. Evita la máquina de estados necesaria para eliminar bloques `<think>` del stream.
- **Native tool calling**: `ollama.chat(tools=[...])` en lugar de ReAct. Los modelos de 1.2B no siguen formatos de texto personalizados de forma confiable.
- **Temperature=0**: necesario para que el modelo de razonamiento produzca tool calls estables.
- **System prompt dinámico**: el prompt incluye automáticamente la lista de herramientas del registry, eliminando la necesidad de actualizar manualmente cuando se agregan herramientas.
- **os.chdir() para change_dir**: un proceso CLI de un solo usuario no necesita un CWD virtual. La simplicidad gana.

---

## Futuras features

- [ ] **Soporte MCP** — integración con el Model Context Protocol para herramientas externas
- [ ] **Memoria de sesión** — caché entre conversaciones para mantener contexto
- [ ] **Fallback local → cloud** — degradación automática cuando el modelo no puede resolver la tarea
- [ ] **Modo sandboxed** — ejecución en directorio aislado para mayor seguridad
- [ ] **Sistema de aprobación** — dry-run mode para revisar acciones antes de ejecutarlas
- [ ] **Plugin system** — herramientas de terceros mediante entrypoints
- [ ] **Herramientas en paralelo** — ejecución concurrente de múltiples tool calls
- [ ] **Monitoring de recursos** — CPU/RAM usage durante la sesión

---

## Contribución & Licencia

**Autor:** Gerardo Toboso
**Contacto:** gerardotoboso1909@gmail.com
**Licencia:** MIT License