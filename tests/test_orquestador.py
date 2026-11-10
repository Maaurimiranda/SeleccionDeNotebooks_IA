"""PG3-01: el orquestador corre de punta a punta con un plan fijo y un Grafo falso."""
import json
import tempfile
import unittest
from pathlib import Path

from asistente.contrato import ADVERTENCIA, ErrorLLM
from asistente.grafo import Grafo
from asistente.orquestador import Orquestador
from tests.comun import GrafoFalso, LLMFalso, fixture


def plan_fijo(plan):
    return lambda texto, sesion, llm, **kw: plan


class TestOrquestador(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.grafo = GrafoFalso(fixture("SM1.interpretacion_pedido"), fixture("SM2.riesgo_ram"),
                                fixture("SM4.explicar_notebook.G"))
        self.orq = Orquestador(self.grafo, LLMFalso(), planificar=plan_fijo(fixture("plan_ejemplo")),
                               dir_trazas=self.dir)

    def test_punta_a_punta_con_stubs(self):
        r = self.orq.consultar("¿Por qué la G quedó indeterminada y qué riesgo de RAM tiene en req_01?")
        self.assertEqual(r["origen_respuesta"], "plantilla_fija")
        self.assertEqual(r["requerimiento_id"], "req_01")
        self.assertEqual(r["submodulos_consultados"], ["SM1", "SM4", "SM2"])
        ev = r["traza"]["evidencia"]
        self.assertEqual(ev["pedido"]["perfil_dominante"], "VIRT")          # L1 agregada siempre
        self.assertEqual(ev["SM2"]["riesgo_ram"]["notebooks"][0]["riesgo"], {"min": 49.58, "max": 81.46})
        self.assertEqual(ev["SM4"]["explicar_notebook"]["notebooks"][0]["estado"],
                         "Indeterminada: completar informacion")           # SM4 real, con filas del grafo
        self.assertEqual(ev["advertencia"], ADVERTENCIA)
        # la traza quedó escrita, con submódulo y duración por consulta
        lineas = list(Path(self.dir).glob("*.jsonl"))[0].read_text(encoding="utf-8").splitlines()
        t = json.loads(lineas[-1])
        self.assertEqual([c["sm"] for c in t["consultas"]], ["SM1", "SM4", "SM2"])
        self.assertTrue(all("ms" in c for c in t["consultas"]))
        self.assertTrue({"plan", "consultas", "explicacion"} <= set(t["duracion_ms"]))

    def test_despacho_por_mapa_de_runnables(self):
        from langchain_core.runnables import RunnableLambda
        self.assertEqual(set(self.orq.despachos), {"SM1", "SM2", "SM3", "SM4", "GRUPO"})
        self.assertTrue(all(isinstance(r, RunnableLambda) for r in self.orq.despachos.values()))

    def test_1501_caracteres_no_se_recorta(self):
        texto = "a" * 1501
        r = self.orq.consultar(texto)
        self.assertEqual(r["origen_respuesta"], "validacion")
        self.assertIn("1501", r["respuesta"])
        self.assertEqual(r["traza"]["consulta_usuario"], texto)

    def test_vacia_y_sin_letras(self):
        self.assertEqual(self.orq.consultar("   ")["origen_respuesta"], "validacion")
        self.assertEqual(self.orq.consultar("123 ???")["origen_respuesta"], "validacion")

    def test_fuera_de_alcance_no_toca_el_grafo(self):
        orq = Orquestador(self.grafo, LLMFalso(), dir_trazas=self.dir, planificar=plan_fijo(
            {"requerimiento_id": None, "consultas": [], "evidencia": [], "fuera_de_alcance": True,
             "aclaracion": None}))
        r = orq.consultar("¿Cuál es la capital de Francia?")
        self.assertEqual(r["origen_respuesta"], "fuera_de_alcance")
        self.assertEqual(self.grafo.llamadas, [])

    def test_error_del_llm_sin_traceback(self):
        def falla(*a, **k):
            raise ErrorLLM("caído")
        orq = Orquestador(self.grafo, LLMFalso(), planificar=falla, dir_trazas=self.dir)
        r = orq.consultar("¿Qué me recomendás para req_01?")
        self.assertEqual(r["origen_respuesta"], "error")
        self.assertNotIn("Traceback", r["respuesta"])

    def test_neo4j_apagado_da_error_con_mensaje_fijo(self):
        apagado = Grafo(uri="bolt://localhost:1", clave="x")
        orq = Orquestador(apagado, LLMFalso(), planificar=plan_fijo(fixture("plan_ejemplo")), dir_trazas=self.dir)
        r = orq.consultar("¿Qué riesgo de RAM tiene la G en req_01?")
        self.assertEqual(r["origen_respuesta"], "error")
        self.assertIn("Neo4j", r["respuesta"])
        self.assertNotIn("Traceback", r["respuesta"])

    def test_pedido_de_sesion(self):
        sesion = {}
        plan = dict(fixture("plan_ejemplo"), requerimiento_id=None)
        orq = Orquestador(self.grafo, LLMFalso(), planificar=plan_fijo(plan), dir_trazas=self.dir)
        r = orq.consultar("¿Y qué riesgo de RAM tiene la G?", sesion=sesion)
        self.assertEqual(r["origen_respuesta"], "validacion")          # sin pedido: pregunta, no asume req_01
        r = orq.consultar("¿Y qué riesgo de RAM tiene la G?", requerimiento_id="req_01", sesion=sesion)
        self.assertEqual(r["requerimiento_id"], "req_01")


if __name__ == "__main__":
    unittest.main()
