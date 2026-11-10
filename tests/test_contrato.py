"""PG3-01: cada fixture respeta el contrato de ARQUITECTURA §4.1."""
import json
import unittest

from asistente.contrato import ESQUEMA_PLAN, ESTADOS, INTENCIONES, INTENCIONES_NIVEL_1, ORIGENES_RESPUESTA
from tests.comun import DIR_FIXTURES


class TestFixtures(unittest.TestCase):
    def test_hay_un_fixture_por_intencion_de_nivel_1(self):
        nombres = {p.stem.split(".")[0] + "." + p.stem.split(".")[1] for p in DIR_FIXTURES.glob("*.*.json")}
        for intencion in INTENCIONES_NIVEL_1:
            self.assertIn(intencion, nombres, f"falta tests/fixtures/{intencion}.json")

    def test_forma_de_cada_fixture(self):
        for ruta in DIR_FIXTURES.glob("*.*.json"):
            with self.subTest(fixture=ruta.name):
                f = json.loads(ruta.read_text(encoding="utf-8"))
                self.assertTrue({"parametros", "consultas", "evidencia"} <= set(f))
                self.assertIsInstance(f["evidencia"], dict)
                for c in f["consultas"]:
                    self.assertEqual(set(c), {"nombre", "cypher", "parametros", "filas"})
                    self.assertRegex(c["nombre"], r"^(SM[1-4]|GRUPO)\.")

    def test_alertas_con_notebook(self):
        """La atribución de cada alerta la controla el verificador: la notebook es obligatoria."""
        def alertas(x):
            if isinstance(x, dict):
                for k, v in x.items():
                    if k == "alertas":
                        yield from v
                    else:
                        yield from alertas(v)
            elif isinstance(x, list):
                for v in x:
                    yield from alertas(v)
        for ruta in DIR_FIXTURES.glob("*.*.json"):
            for a in alertas(json.loads(ruta.read_text(encoding="utf-8"))["evidencia"]):
                self.assertTrue({"codigo", "texto", "notebook"} <= set(a), f"{ruta.name}: {a}")

    def test_estados_de_la_evidencia_son_literales_d06(self):
        for ruta in DIR_FIXTURES.glob("*.*.json"):
            texto = ruta.read_text(encoding="utf-8")
            for f in json.loads(texto).get("consultas", []):
                for fila in f["filas"]:
                    if fila.get("estado"):
                        self.assertIn(fila["estado"], ESTADOS, ruta.name)


class TestContrato(unittest.TestCase):
    def test_esquema_plan_cerrado(self):
        items = ESQUEMA_PLAN["properties"]["consultas"]
        self.assertEqual(items["maxItems"], 3)
        self.assertEqual(set(items["items"]["properties"]["intencion"]["enum"]), set(INTENCIONES))
        self.assertEqual(len(INTENCIONES), 13)

    def test_origenes(self):
        self.assertEqual(ORIGENES_RESPUESTA, ["llm", "plantilla_fija", "validacion", "fuera_de_alcance", "error"])


if __name__ == "__main__":
    unittest.main()
