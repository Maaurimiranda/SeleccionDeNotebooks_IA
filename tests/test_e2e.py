"""PG3-11: los E2E de scripts/correr_e2e.py como pruebas. Piden Neo4j (con el grafo cargado) y Ollama con el modelo.

    PG3_TEST_LLM=1 python -m unittest tests.test_e2e

Se saltean si falta alguno. El aprobado de cada E2E lo decide la evidencia del grafo, no el texto del LLM.
"""
import os
import tempfile
import unittest

from scripts.correr_e2e import CASOS, _correr, _submodulos_pedidos
from tests.comun import grafo_real


@unittest.skipUnless(os.getenv("PG3_TEST_LLM") == "1", "prueba con LLM: exportar PG3_TEST_LLM=1 (lenta)")
class TestE2E(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from asistente.llm import LLM
        from asistente.orquestador import Orquestador
        grafo, llm = grafo_real(), LLM()
        if grafo is None or not grafo.salud().get("notebooks") or not llm.salud().get("ok"):
            raise unittest.SkipTest("hace falta Neo4j (con el grafo cargado) y Ollama con el modelo")
        orq = Orquestador(grafo, llm, dir_trazas=tempfile.mkdtemp())
        cls.corridas = {c["id"]: _correr(c, orq) for c in CASOS}   # una sola corrida por caso (el LLM es lento)

    def test_cada_e2e(self):
        for caso in CASOS:
            with self.subTest(caso["id"]):
                c = self.corridas[caso["id"]]
                fallos = [f"{x['esperado']} -> {x['obtenido']}" for x in c["resultados"] if not x["ok"]]
                self.assertEqual(fallos, [])

    def test_los_casos_integrales_cruzan_al_menos_dos_submodulos(self):
        integrales = [c for c in CASOS if c["tipo"] == "integral"]
        self.assertGreaterEqual(len(integrales), 5)
        for caso in integrales:
            with self.subTest(caso["id"]):
                self.assertGreaterEqual(len(_submodulos_pedidos(self.corridas[caso["id"]]["traza"])), 2)

    def test_el_control_fuera_de_alcance_no_consulta_el_grafo(self):
        caso = next(c for c in CASOS if c["id"] == "E2E-8")
        c = self.corridas[caso["id"]]
        self.assertEqual(c["traza"]["consultas"], [])
        self.assertEqual(c["respuesta"]["origen_respuesta"], "fuera_de_alcance")


if __name__ == "__main__":
    unittest.main()
