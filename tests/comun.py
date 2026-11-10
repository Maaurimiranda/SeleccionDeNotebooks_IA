"""Ayudas para los tests: fixtures, Grafo falso y detección de Neo4j / Ollama."""
import json
import os
import unittest
from pathlib import Path

DIR_FIXTURES = Path(__file__).resolve().parent / "fixtures"


def fixture(nombre: str) -> dict:
    return json.loads((DIR_FIXTURES / f"{nombre}.json").read_text(encoding="utf-8"))


class GrafoFalso:
    """Devuelve las filas del fixture para el mismo Cypher. Registra cada llamada."""

    def __init__(self, *fixtures: dict, catalogo=None, pedidos=None):
        self.respuestas = {}
        for f in fixtures:
            for c in f.get("consultas", []):
                self.respuestas[c["cypher"].strip()] = c["filas"]
        self.llamadas: list[tuple[str, dict]] = []
        self._catalogo = catalogo or [f"Notebook_{x}" for x in "ABCEGHKMX"]
        self._pedidos = pedidos or ["req_01", "req_02", "req_03"]

    def leer(self, cypher, parametros=None):
        self.llamadas.append((cypher.strip(), dict(parametros or {})))
        return self.respuestas.get(cypher.strip(), [])

    def catalogo(self):
        return self._catalogo

    def pedidos(self):
        return self._pedidos

    def salud(self):
        return {"ok": True, "uri": "falso"}


class LLMFalso:
    modelo = "falso"

    def salud(self):
        return {"ok": True, "modelo": "falso"}


_GRAFO = None


def grafo_real():
    """Grafo conectado, o None si no hay Neo4j (los tests ConGrafo se saltean)."""
    global _GRAFO
    if _GRAFO is None:
        if not os.getenv("NEO4J_PASSWORD"):
            return None
        from asistente.grafo import Grafo
        g = Grafo()
        if not g.salud().get("ok"):
            return None
        _GRAFO = g
    return _GRAFO


def requiere_neo4j(cls):
    return unittest.skipIf(grafo_real() is None, "sin Neo4j (exportar NEO4J_PASSWORD y levantar la base)")(cls)
