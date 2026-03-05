"""Sub-paquete del agente nineteen.

Re-exporta la clase ``Agent`` desde ``agent.core`` para que los importadores
externos puedan usar ``from nineteen.agent import Agent`` sin conocer la
estructura interna del sub-paquete.
"""
from nineteen.agent.core import Agent

__all__ = ["Agent"]
