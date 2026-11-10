"""PG3-01: la API con TestClient y los stubs."""
import tempfile
import unittest

from fastapi.testclient import TestClient

from asistente.api import crear_app
from asistente.orquestador import Orquestador
from tests.comun import GrafoFalso, LLMFalso, fixture

CLAVES = {"respuesta", "requerimiento_id", "submodulos_consultados", "origen_respuesta", "intento", "traza"}


class TestAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        grafo = GrafoFalso(fixture("SM1.interpretacion_pedido"), fixture("SM2.riesgo_ram"))
        orq = Orquestador(grafo, LLMFalso(), planificar=lambda *a, **k: fixture("plan_ejemplo"),
                          dir_trazas=tempfile.mkdtemp())
        cls.cliente = TestClient(crear_app(orq))

    def test_consultar(self):
        r = self.cliente.post("/consultar", json={"texto": "¿Qué riesgo de RAM tiene la G en req_01?"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(set(r.json()), CLAVES)
        self.assertEqual(r.json()["origen_respuesta"], "plantilla_fija")

    def test_1501_caracteres_es_validacion_no_422(self):
        r = self.cliente.post("/consultar", json={"texto": "x" * 1501})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["origen_respuesta"], "validacion")

    def test_salud(self):
        r = self.cliente.get("/salud")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(set(r.json()), {"ok", "neo4j", "ollama", "modelo"})

    def test_openapi_documenta_los_dos_endpoints_con_ejemplos(self):
        esquema = self.cliente.get("/openapi.json").json()
        self.assertEqual(set(esquema["paths"]), {"/consultar", "/salud"})
        entrada = esquema["components"]["schemas"]["ConsultaEntrada"]["properties"]["texto"]
        self.assertTrue(entrada.get("examples"))
        self.assertEqual(self.cliente.get("/docs").status_code, 200)


if __name__ == "__main__":
    unittest.main()
