"""PG3-01: los cinco paquetes tienen la misma forma y solo exportan ejecutar();
LangChain solo en llm.py y orquestador.py; el servicio no tiene Cypher (ARQUITECTURA §2.1)."""
import importlib
import re
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent / "asistente"
ARCHIVOS = {"__init__.py", "entrada.py", "servicio.py", "repositorio.py", "esquemas.py"}
PAQUETES = ["sm1", "sm2", "sm3", "sm4", "grupo"]


class TestEstructura(unittest.TestCase):
    def test_paquetes_iguales(self):
        for p in PAQUETES:
            with self.subTest(paquete=p):
                presentes = {f.name for f in (RAIZ / "submodulos" / p).glob("*.py")}
                self.assertEqual(presentes, ARCHIVOS)
                modulo = importlib.import_module(f"asistente.submodulos.{p}")
                self.assertEqual(modulo.__all__, ["ejecutar"])
                self.assertTrue(callable(modulo.ejecutar))

    def test_servicio_sin_cypher_y_repositorio_sin_evidencia(self):
        cypher = re.compile(r"\b(MATCH|MERGE|CREATE|RETURN)\b")
        for p in PAQUETES:
            with self.subTest(paquete=p):
                servicio = (RAIZ / "submodulos" / p / "servicio.py").read_text(encoding="utf-8")
                self.assertIsNone(cypher.search(servicio), f"{p}/servicio.py tiene Cypher")
                repo = (RAIZ / "submodulos" / p / "repositorio.py").read_text(encoding="utf-8")
                self.assertNotIn("evidencia", repo.replace("no se arma evidencia", "").replace(
                    "no arma evidencia", ""), f"{p}/repositorio.py arma evidencia")

    def test_submodulos_no_se_importan_entre_si(self):
        for p in PAQUETES:
            for f in (RAIZ / "submodulos" / p).glob("*.py"):
                texto = f.read_text(encoding="utf-8")
                for otro in PAQUETES:
                    if otro != p:
                        self.assertNotIn(f"submodulos.{otro}", texto, f"{f} importa {otro}")

    def test_langchain_solo_en_llm_y_orquestador(self):
        for f in RAIZ.rglob("*.py"):
            if "langchain" in f.read_text(encoding="utf-8").replace("LangChain", ""):
                self.assertIn(f.name, {"llm.py", "orquestador.py"}, f"{f} importa LangChain")

    def test_sin_agentes_ni_tool_calling(self):
        prohibido = re.compile(r"AgentExecutor|create_react_agent|bind_tools|langgraph", re.IGNORECASE)
        for f in RAIZ.rglob("*.py"):
            self.assertIsNone(prohibido.search(f.read_text(encoding="utf-8")), str(f))


if __name__ == "__main__":
    unittest.main()
