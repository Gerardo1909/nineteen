# nineteen

> El agente de IA local pensado para máquinas sin GPU.

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

Las alternativas populares (Aider, Open Interpreter) asumen que tenés una GPU o acceso a una API
cloud. En hardware modesto — un Ryzen 5, 16 GB RAM, sin VRAM — simplemente no funcionan bien.

nineteen nació para ese escenario: modelos desde 522 MB corriendo en CPU pura, con tool calling
nativo de Ollama, sin ReAct personalizado ni parseo frágil de texto.

---

## Características

- ✅ Funciona en CPU pura (sin GPU, sin VRAM)
- ✅ Modelos desde 522 MB (`qwen3:0.6b`)
- ✅ 13 herramientas integradas (filesystem, navegación, búsqueda, shell)
- ✅ Modo interactivo + one-shot
- ✅ Native Ollama tool calling (sin ReAct)
- ✅ Arquitectura hexagonal — proveedor LLM intercambiable sin tocar el agente
- ✅ Sistema de aprobación para herramientas destructivas
- ✅ Streaming con spinner braille durante razonamiento
- ✅ Sin dependencias pesadas (solo `ollama` + `click`)

---

## Instalación

**Requisitos previos:**
- [Ollama](https://ollama.com) instalado y corriendo
- Python 3.13+
- [uv](https://docs.astral.sh/uv/) (recomendado) o pip

### Instalación global (recomendado)

```bash
git clone <repo-url>
cd nineteen
uv tool install -e .

# Descargar el modelo por defecto
ollama pull qwen3:0.6b
```

Después de esto, el comando `nineteen` queda disponible globalmente sin necesidad
de activar ningún entorno virtual.

### Alternativa: desarrollo local

```bash
git clone <repo-url>
cd nineteen
uv sync
uv run nineteen
```

---

## Uso

### Modo interactivo

```bash
nineteen
```

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
│  model: qwen3:0.6b  •  tools: 13 cargadas           │
│  Escribe 'exit' o Ctrl-C para salir                  │
│  → best model for your CPU: canirun.ai               │
└──────────────────────────────────────────────────────┘

❯ find all Python files modified in the last 7 days
⠙ pensando...
⚙  run_command(command='find . -name "*.py" -mtime -7')
→  ./src/nineteen/providers/base.py
   ./src/nineteen/providers/ollama.py
   ...

Here are the Python files modified in the last 7 days: ...
```

### Modo one-shot

```bash
nineteen run "list files in the current directory"
nineteen run "read pyproject.toml and summarize it"
nineteen run "find all TODO comments in src/"
```

### Variables de entorno

| Variable         | Descripción          | Default      |
|------------------|----------------------|--------------|
| `NINETEEN_MODEL` | Modelo Ollama a usar | `qwen3:0.6b` |

### Opciones CLI

```
nineteen [OPTIONS] COMMAND [ARGS]...

Options:
  -m, --model TEXT       Modelo Ollama a usar
  --max-steps INTEGER    Máximo de pasos por tarea (default: 10)
  --no-approval          Omitir confirmación para herramientas destructivas
  --no-stream            Deshabilitar streaming (esperar respuesta completa)
  -V, --version          Muestra la versión y sale
  -h, --help             Muestra la ayuda

Commands:
  run    Ejecuta una tarea one-shot y sale
```

---

## Herramientas disponibles

### Navegación y lectura

| Herramienta       | Firma                        | Descripción                                       |
|-------------------|------------------------------|---------------------------------------------------|
| `get_cwd`         | *(sin parámetros)*           | Retorna el directorio de trabajo actual            |
| `change_dir`      | `path: str`                  | Cambia el directorio de trabajo                    |
| `list_dir`        | `path: str`                  | Lista el contenido de un directorio                |
| `tree`            | `path: str, max_depth?: int` | Vista de árbol del directorio (default depth: 3)   |
| `file_info`       | `path: str`                  | Metadata de un archivo (tamaño, permisos, fechas)  |
| `search_in_files` | `pattern: str, path: str`    | Busca texto en archivos recursivamente             |
| `read_file`       | `path: str`                  | Lee el contenido completo de un archivo (UTF-8)   |

### Escritura y mutación

| Herramienta   | Firma                     | Descripción                                     |
|---------------|---------------------------|-------------------------------------------------|
| `write_file`  | `path: str, content: str` | Escribe texto en un archivo (crea si no existe) |
| `copy_file`   | `src: str, dst: str`      | Copia un archivo preservando metadata           |
| `rename_file` | `src: str, dst: str`      | Renombra o mueve un archivo                     |
| `delete_file` | `path: str`               | Elimina un archivo (no directorios)             |
| `make_dir`    | `path: str`               | Crea un directorio (incluyendo intermedios)     |

### Sistema

| Herramienta   | Firma          | Descripción                             |
|---------------|----------------|-----------------------------------------|
| `run_command` | `command: str` | Ejecuta un comando shell (timeout: 30s) |

Las herramientas destructivas (`write_file`, `delete_file`, `rename_file`, `copy_file`,
`make_dir`, `run_command`) requieren aprobación interactiva antes de ejecutarse. Usá
`--no-approval` para saltear este paso en entornos automatizados.

---

## Modelos recomendados

nineteen funciona con cualquier modelo Ollama que soporte tool calling nativo. Para encontrar
el modelo óptimo para tu hardware específico, visitá **[canirun.ai](https://www.canirun.ai)**.

Algunos modelos probados:

| Modelo       | Tamaño | RAM mínima | Tool calling |
|--------------|--------|------------|--------------|
| `qwen3:0.6b` | 522 MB | 2 GB       | ✅ nativo    |
| `qwen3:1.7b` | 1.1 GB | 4 GB       | ✅ nativo    |
| `llama3.2:1b`| 1.3 GB | 4 GB       | ✅ nativo    |
| `qwen3:4b`   | 2.6 GB | 6 GB       | ✅ nativo    |
| `mistral:7b` | 4.1 GB | 8 GB       | ✅ nativo    |

```bash
# Cambiar modelo en runtime
nineteen --model qwen3:1.7b run "tarea"

# O de forma persistente
export NINETEEN_MODEL=qwen3:1.7b
```

---

## Comparativa con alternativas

| Herramienta      | CPU-only | Modelos <1B | Sin GPU | Sin cloud | Ligero |
|------------------|----------|-------------|---------|-----------|--------|
| Aider            | ~        | ✗           | ✗       | ✗         | ~      |
| Open Interpreter | ~        | ✗           | ✗       | ✗         | ✗      |
| **nineteen**     | **✅**   | **✅**      | **✅**  | **✅**    | **✅** |

---

## Arquitectura

```
src/nineteen/
├── cli.py               # Click CLI — punto de entrada
├── display.py           # Salida ANSI, spinner braille, banner
├── prompts.py           # System prompt dinámico
├── providers/           # Puerto LLMProvider (arquitectura hexagonal)
│   ├── base.py          # Protocolo LLMProvider + tipos normalizados
│   └── ollama.py        # OllamaProvider — único módulo que importa ollama
├── agent/
│   └── core.py          # Agent — bucle agéntico agnóstico del proveedor
└── tools/
    ├── base.py          # ToolSpec, ToolRegistry (stdlib only)
    └── filesystem.py    # 13 herramientas + build_default_registry()
```

**Decisiones de diseño:**

- **Arquitectura hexagonal para el LLM**: `Agent` depende del protocolo `LLMProvider`, nunca del SDK de Ollama directamente. Cambiar de backend requiere únicamente crear un nuevo adaptador e inyectarlo — sin tocar el agente ni las herramientas.
- **Native tool calling**: `ollama.chat(tools=[...])` en lugar de ReAct. Los modelos pequeños no siguen formatos de texto personalizados de forma confiable; el esquema JSON Schema produce tool calls estructurados sin parseo frágil.
- **Temperature=0**: produce tool calls deterministas y estables, especialmente necesario en modelos con reasoning interno.
- **Streaming por defecto**: los tokens se muestran progresivamente. Durante el reasoning interno aparece un spinner braille en stderr para no contaminar stdout.
- **System prompt dinámico**: el prompt incluye automáticamente la lista de herramientas del registry activo — agregar herramientas no requiere modificar el prompt manualmente.

---

## Roadmap

- [x] Sistema de aprobación para herramientas destructivas
- [x] Streaming con spinner braille
- [x] Abstracción de proveedor LLM (arquitectura hexagonal)
- [ ] Backend llama.cpp — ejecución directa de GGUF sin servidor Ollama
- [ ] Modo sandboxed (`--workdir`) — confina el agente a un directorio
- [ ] Memoria de sesión — persiste conversaciones en `~/.nineteen/sessions/`

---

## Contribución & Licencia

**Autor:** Gerardo Toboso
**Contacto:** gerardotoboso1909@gmail.com
**Licencia:** MIT License
