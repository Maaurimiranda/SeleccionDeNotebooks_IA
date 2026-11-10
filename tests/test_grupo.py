"""PG3-04: GRUPO.traza_reglas (L3) y GRUPO.parametros (L4)."""
import unittest

from asistente.contrato import Aclaracion, SIN_VALIDAR
from asistente.submodulos import grupo
from tests.comun import GrafoFalso, fixture, grafo_real, requiere_neo4j


class TestGrupoOffline(unittest.TestCase):
    def test_traza_de_a_cubre_los_cuatro_submodulos(self):
        f = fixture("GRUPO.traza_reglas")
        e = grupo.ejecutar("GRUPO.traza_reglas", f["parametros"], GrafoFalso(f))["evidencia"]
        self.assertEqual(e["submodulos"], ["SM1", "SM2", "SM3", "SM4"])
        con_fuerza = [r for r in e["reglas"] if r["fuerza"] is not None]
        self.assertTrue(con_fuerza)
        self.assertTrue(all({"id", "submodulo", "validacion"} <= set(r) for r in e["reglas"]))

    def test_parametros_todos_sin_validar(self):
        f = fixture("GRUPO.parametros")
        e = grupo.ejecutar("GRUPO.parametros", {}, GrafoFalso(f))["evidencia"]
        self.assertGreater(e["total"], 0)
        self.assertEqual(e["sin_validar"], e["total"])
        self.assertTrue(all(p["estado_validacion"] == SIN_VALIDAR for p in e["parametros"]))

    def test_modelo_sin_evaluacion(self):
        with self.assertRaises(Aclaracion):
            grupo.ejecutar("GRUPO.traza_reglas", {"requerimiento_id": "req_03", "modelo": "Notebook_A"},
                           GrafoFalso())

    def test_falta_modelo(self):
        with self.assertRaises(Aclaracion):
            grupo.ejecutar("GRUPO.traza_reglas", {"requerimiento_id": "req_01"}, GrafoFalso())


@requiere_neo4j
class ConGrafo(unittest.TestCase):
    def test_traza_a(self):
        e = grupo.ejecutar("GRUPO.traza_reglas", {"requerimiento_id": "req_01", "modelo": "Notebook_A"},
                           grafo_real())["evidencia"]
        self.assertEqual(e["submodulos"], ["SM1", "SM2", "SM3", "SM4"])

    def test_parametros(self):
        e = grupo.ejecutar("GRUPO.parametros", {}, grafo_real())["evidencia"]
        self.assertEqual(e["sin_validar"], e["total"])

    def test_sin_evaluacion(self):
        with self.assertRaises(Aclaracion):
            grupo.ejecutar("GRUPO.traza_reglas", {"requerimiento_id": "req_03", "modelo": "Notebook_A"},
                           grafo_real())


if __name__ == "__main__":
    unittest.main()
