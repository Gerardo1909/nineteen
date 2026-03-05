"""nineteen — agente de IA local pensado para hardware sin GPU.

Usa Ollama para ejecutar modelos de lenguaje localmente y expone un conjunto
de herramientas de filesystem que el modelo puede invocar mediante tool calling
nativo. Compatible con modelos pequeños (≥731 MB) en CPU pura.

Versión: 0.1.0
Dependencias principales: ollama, click
"""

__version__ = "0.1.0"
