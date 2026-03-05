"""Punto de entrada para ``python -m nineteen``.

Permite ejecutar el paquete directamente sin necesidad de instalar el
script de consola. Equivale a llamar al comando ``nineteen`` desde la CLI.

Uso::

    python -m nineteen            # modo interactivo
    python -m nineteen run "..."  # modo one-shot
"""
from nineteen.cli import main

if __name__ == "__main__":
    main()
