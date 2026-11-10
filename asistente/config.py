"""Configuración leída de variables de entorno (ARQUITECTURA §4.6).

Sin python-dotenv (D-05): las variables se exportan antes de lanzar la CLI o la API.
"""
import os

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")

MAX_CARACTERES = int(os.getenv("MAX_CARACTERES", "1500"))
MAX_REGENERACIONES = int(os.getenv("MAX_REGENERACIONES", "2"))
DIR_TRAZAS = os.getenv("DIR_TRAZAS", "trazas")
