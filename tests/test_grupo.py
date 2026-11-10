"""PG3-04: GRUPO.traza_reglas (L3) y GRUPO.parametros (L4). PG3-05: origen del conocimiento."""
import re
import unittest

from asistente.contrato import Aclaracion, SIN_VALIDAR
from asistente.submodulos import grupo
from asistente.submodulos.grupo import repositorio
from asistente.submodulos.grupo.servicio import NO_REGISTRADA
from tests.comun import GrafoFalso, fixture, grafo_real, requiere_neo4j


def _filas(consulta: str, filas: list[dict]) -> dict:
    """Filas armadas a mano para una consulta de origen. Los fixtures reales de estas consultas
    se generan con `python -m scripts.generar_fixtures` cuando hay Neo4j."""
    return {"consultas": [{"cypher": repositorio.CONSULTAS[consulta], "filas": filas}]}


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

    def test_origen_de_reglas_y_notebook(self):
        f = fixture("GRUPO.traza_reglas")
        ids = sorted({r["id"] for r in f["evidencia"]["reglas"]})
        con = ids[0]
        reglas = _filas("origen_reglas", [
            {"regla": con, "parametro": "centros_y_sigmas_grado_gpu", "origen": "Decision de diseno del grupo (PI3)",
             "validacion": SIN_VALIDAR, "consulta_experto": "CE-grado_gpu", "estado_consulta": "pendiente"}])
        notebook = _filas("origen_notebook", [{"fuente_precio": "Mercado Libre", "fuente_autonomia": None}])
        grafo = GrafoFalso(f, reglas, notebook)
        o = grupo.ejecutar("GRUPO.traza_reglas", f["parametros"], grafo)["evidencia"]["origen"]
        llamadas = {cypher: parametros for cypher, parametros in grafo.llamadas}
        self.assertEqual(llamadas[repositorio.CONSULTAS["origen_reglas"].strip()], {"reglas": ids})
        self.assertEqual(llamadas[repositorio.CONSULTAS["origen_notebook"].strip()],
                         {"modelo": f["parametros"]["modelo"]})
        self.assertEqual(o["reglas"][con][0]["origen"], "Decision de diseno del grupo (PI3)")
        self.assertEqual(o["reglas"][con][0]["consulta_experto"], "CE-grado_gpu")
        self.assertNotIn(con, o["reglas_sin_origen"])
        self.assertEqual(len(o["reglas"]) + len(o["reglas_sin_origen"]), len(ids))
        self.assertEqual(o["notebook"], {"fuente_precio": "Mercado Libre", "fuente_autonomia": NO_REGISTRADA})

    def test_origen_con_filas_reales_del_grafo(self):
        """El fixture trae las filas reales de la traza de A: 14 de sus 18 reglas tienen origen."""
        f = fixture("GRUPO.traza_reglas")
        ids = {r["id"] for r in f["evidencia"]["reglas"]}
        o = grupo.ejecutar("GRUPO.traza_reglas", f["parametros"], GrafoFalso(f))["evidencia"]["origen"]
        self.assertTrue(o["reglas"])
        self.assertEqual(set(o["reglas"]) | set(o["reglas_sin_origen"]), ids)
        self.assertFalse(set(o["reglas"]) & set(o["reglas_sin_origen"]))
        self.assertNotIn(NO_REGISTRADA, o["notebook"].values())

    def test_sin_origen_en_el_grafo_dice_no_registrada(self):
        f = fixture("GRUPO.traza_reglas")
        vacio = GrafoFalso(f, _filas("origen_reglas", []), _filas("origen_notebook", []))
        o = grupo.ejecutar("GRUPO.traza_reglas", f["parametros"], vacio)["evidencia"]["origen"]
        self.assertEqual(o["reglas"], {})
        self.assertEqual(len(o["reglas_sin_origen"]), len({r["id"] for r in f["evidencia"]["reglas"]}))
        self.assertEqual(set(o["notebook"].values()), {NO_REGISTRADA})

    def test_parametros_con_origen_real(self):
        f = fixture("GRUPO.parametros")
        e = grupo.ejecutar("GRUPO.parametros", {}, GrafoFalso(f))["evidencia"]
        self.assertEqual(e["sin_origen"], 0)
        self.assertTrue(all(p["origen"] != NO_REGISTRADA for p in e["parametros"]))

    def test_parametros_con_y_sin_origen(self):
        f = fixture("GRUPO.parametros")
        p0 = f["evidencia"]["parametros"][0]["nombre"]
        origen = _filas("origen_parametros", [{"nombre": p0, "origen": "Decision del grupo (REC-R5)"}])
        e = grupo.ejecutar("GRUPO.parametros", {}, GrafoFalso(f, origen))["evidencia"]
        por_nombre = {p["nombre"]: p["origen"] for p in e["parametros"]}
        self.assertEqual(por_nombre[p0], "Decision del grupo (REC-R5)")
        self.assertEqual(e["sin_origen"], e["total"] - 1)

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
        self.assertEqual(e["sin_origen"], 0)

    def test_origen_de_la_traza_de_a(self):
        """PG3-05: la regla, su parámetro y la fuente del dato salen del grafo, y ninguno es inventado."""
        o = grupo.ejecutar("GRUPO.traza_reglas", {"requerimiento_id": "req_01", "modelo": "Notebook_A"},
                           grafo_real())["evidencia"]["origen"]
        self.assertTrue(o["reglas"], "al menos una regla con su origen")
        self.assertNotEqual(o["notebook"]["fuente_precio"], NO_REGISTRADA)
        for rid, parametros in o["reglas"].items():
            for p in parametros:
                if not p["parametro"].startswith("centros_y_sigmas_"):
                    # el parámetro solo respalda la regla si su origen la nombra completa (REC-R1 no es REC-R15)
                    self.assertRegex(p["origen"], rf"\b{re.escape(rid)}\b")

    def test_sin_evaluacion(self):
        with self.assertRaises(Aclaracion):
            grupo.ejecutar("GRUPO.traza_reglas", {"requerimiento_id": "req_03", "modelo": "Notebook_A"},
                           grafo_real())


if __name__ == "__main__":
    unittest.main()
