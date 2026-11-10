"""PG3-07: SM1.interpretacion_pedido."""
import unittest

from asistente.contrato import Aclaracion
from asistente.submodulos import sm1
from tests.comun import GrafoFalso, fixture, grafo_real, requiere_neo4j


class TestSM1Offline(unittest.TestCase):
    def ev(self, nombre, req):
        return sm1.ejecutar("SM1.interpretacion_pedido", {"requerimiento_id": req}, GrafoFalso(fixture(nombre)))

    def test_req_01_virt_dominante(self):
        e = self.ev("SM1.interpretacion_pedido", "req_01")["evidencia"]
        self.assertEqual(e["perfil_dominante"], "VIRT")
        self.assertEqual(e["estado_pedido"], "interpretado")
        virt = e["perfiles"][0]
        self.assertEqual((virt["perfil"], virt["grado"], virt["impone_requisitos"]), ("VIRT", 0.899, True))
        self.assertEqual(e["presupuesto"], 1000.0)

    def test_req_02_indeterminado_sin_perfil_asumido(self):
        e = self.ev("SM1.interpretacion_pedido.req_02", "req_02")["evidencia"]
        self.assertEqual(e["estado_pedido"], "indeterminado")
        self.assertEqual(e["perfiles"], [])
        self.assertTrue(e["preguntas_pendientes"])
        self.assertNotIn("OFI", str(e))

    def test_pedido_inexistente(self):
        with self.assertRaises(Aclaracion):
            sm1.ejecutar("SM1.interpretacion_pedido", {"requerimiento_id": "req_99"}, GrafoFalso())

    def test_rango_que_cruza_04_se_informa_como_rango(self):
        """D-09: un perfil con rango no se promedia; si es el dominante queda provisional."""
        filas = [{"requerimiento": "req_x", "presupuesto": 900.0, "prioridad": "ninguna", "perfil_dominante": "DIS",
                  "perfiles": [{"perfil": "DIS", "grado": None, "grado_min": 0.3, "grado_max": 0.6,
                                "impone_requisitos": None, "en_frontera": True}],
                  "intensidad": None, "intensidad_valor": None, "preguntas_pendientes": []}]
        g = GrafoFalso()
        g.leer = lambda c, p=None: filas
        e = sm1.ejecutar("SM1.interpretacion_pedido", {"requerimiento_id": "req_x"}, g)["evidencia"]
        self.assertEqual(e["perfiles"][0]["grado"], {"min": 0.3, "max": 0.6})
        self.assertTrue(e["perfil_dominante_provisional"])

    def test_nivel_2_no_disponible(self):
        with self.assertRaises(Aclaracion):
            sm1.ejecutar("SM1.registrar_pedido", {"texto": "x"}, GrafoFalso())


@requiere_neo4j
class ConGrafo(unittest.TestCase):
    def test_req_01_y_req_02(self):
        g = grafo_real()
        e1 = sm1.ejecutar("SM1.interpretacion_pedido", {"requerimiento_id": "req_01"}, g)["evidencia"]
        self.assertEqual(e1["perfil_dominante"], "VIRT")
        e2 = sm1.ejecutar("SM1.interpretacion_pedido", {"requerimiento_id": "req_02"}, g)["evidencia"]
        self.assertEqual((e2["estado_pedido"], e2["perfiles"]), ("indeterminado", []))

    def test_inexistente(self):
        with self.assertRaises(Aclaracion):
            sm1.ejecutar("SM1.interpretacion_pedido", {"requerimiento_id": "req_99"}, grafo_real())


if __name__ == "__main__":
    unittest.main()
