"""PG3-03: SM2.riesgo_ram y SM2.virtualizacion (+ controles de test_offline_SM2 que siguen valiendo)."""
import unittest

from asistente.contrato import Aclaracion
from asistente.submodulos import sm2
from asistente.submodulos.sm2.repositorio import CONSULTAS
from tests.comun import GrafoFalso, fixture, grafo_real, requiere_neo4j


class TestSM2Offline(unittest.TestCase):
    def test_g_riesgo_como_rango_ram_desconocida_y_alertas(self):
        f = fixture("SM2.riesgo_ram")
        nb = sm2.ejecutar("SM2.riesgo_ram", f["parametros"], GrafoFalso(f))["evidencia"]["notebooks"][0]
        self.assertEqual(nb["notebook"], "Notebook_G")
        self.assertEqual(nb["riesgo"], {"min": 49.58, "max": 81.46})
        self.assertEqual(nb["indice_ampliabilidad"], "desconocida")
        self.assertEqual(nb["tipo_ram"], "desconocida")
        self.assertEqual({a["codigo"] for a in nb["alertas"]}, {"REN-R10", "FZ-R7"})
        self.assertTrue(all(a["notebook"] == "Notebook_G" for a in nb["alertas"]))
        self.assertTrue(all(r["id"].startswith("FZ-R") for r in nb["reglas"]))

    def test_k_riesgo_puntual_medio(self):
        f = fixture("SM2.riesgo_ram.todas")
        nbs = {n["notebook"]: n for n in sm2.ejecutar("SM2.riesgo_ram", f["parametros"], GrafoFalso(f))
               ["evidencia"]["notebooks"]}
        self.assertEqual((nbs["Notebook_K"]["riesgo"], nbs["Notebook_K"]["etiqueta"]), (49.55, "medio"))

    def test_virtualizacion_e_incumple(self):
        f = fixture("SM2.virtualizacion")
        nbs = {n["notebook"]: n for n in sm2.ejecutar("SM2.virtualizacion", f["parametros"], GrafoFalso(f))
               ["evidencia"]["notebooks"]}
        self.assertEqual(nbs["Notebook_E"]["resultado"], "no cumple")
        self.assertEqual(nbs["Notebook_E"]["estado"], "Descartada (excluyente incumplido)")
        self.assertEqual(nbs["Notebook_G"]["resultado"], "falta informacion")

    def test_sin_evaluaciones_es_aclaracion(self):
        with self.assertRaises(Aclaracion):
            sm2.ejecutar("SM2.riesgo_ram", {"requerimiento_id": "req_02"}, GrafoFalso())

    def test_sin_pedido_no_usa_req_01(self):
        g = GrafoFalso(fixture("SM2.riesgo_ram"))
        with self.assertRaises(Aclaracion):
            sm2.ejecutar("SM2.riesgo_ram", {}, g)
        self.assertEqual(g.llamadas, [])
        for c in CONSULTAS.values():
            self.assertNotIn("req_01", c)

    def test_etiqueta_invalida(self):
        with self.assertRaises(Aclaracion):
            sm2.ejecutar("SM2.riesgo_ram", {"requerimiento_id": "req_01", "etiqueta": "altisimo"}, GrafoFalso())


@requiere_neo4j
class ConGrafo(unittest.TestCase):
    def test_g(self):
        nb = sm2.ejecutar("SM2.riesgo_ram", {"requerimiento_id": "req_01", "modelos": ["Notebook_G"]},
                          grafo_real())["evidencia"]["notebooks"][0]
        self.assertEqual(nb["riesgo"], {"min": 49.58, "max": 81.46})

    def test_virtualizacion_coincide_con_c1(self):
        g = grafo_real()
        ev = {n["notebook"]: n["resultado"] for n in sm2.ejecutar(
            "SM2.virtualizacion", {"requerimiento_id": "req_01"}, g)["evidencia"]["notebooks"]}
        c1 = {f["n"]: f["e"] for f in g.leer(
            "MATCH (n:Notebook)-[:POSEE]->(cpu:CPU) RETURN n.modelo AS n, CASE cpu.virtualizacion "
            "WHEN 'soportada' THEN 'cumple' WHEN 'no soportada' THEN 'no cumple' ELSE 'falta informacion' END AS e")}
        self.assertEqual(ev, c1)

    def test_req_02_sin_evaluaciones(self):
        with self.assertRaises(Aclaracion):
            sm2.ejecutar("SM2.riesgo_ram", {"requerimiento_id": "req_02"}, grafo_real())


if __name__ == "__main__":
    unittest.main()
