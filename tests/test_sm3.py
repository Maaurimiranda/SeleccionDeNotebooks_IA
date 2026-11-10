"""PG3-09: SM3.buscar y SM3.ficha."""
import unittest

from asistente.contrato import Aclaracion
from asistente.submodulos import sm3
from asistente.submodulos.sm3.repositorio import CONSULTAS
from tests.comun import GrafoFalso, fixture, grafo_real, requiere_neo4j


class TestSM3Offline(unittest.TestCase):
    def test_buscar_grafica_x_con_grado_074_y_orden_descendente(self):
        f = fixture("SM3.buscar")
        nbs = sm3.ejecutar("SM3.buscar", f["parametros"], GrafoFalso(f))["evidencia"]["notebooks"]
        x = next(n for n in nbs if n["notebook"] == "Notebook_X")
        self.assertEqual(x["grado_gpu"], 0.74)
        adec = [n["adecuacion_grafica"] for n in nbs]
        self.assertEqual(adec, sorted(adec, reverse=True))

    def test_ficha_m_movilidad_null_como_dato_faltante(self):
        f = fixture("SM3.ficha")
        nb = sm3.ejecutar("SM3.ficha", f["parametros"], GrafoFalso(f))["evidencia"]["notebooks"][0]
        self.assertIsNone(nb["adecuacion_movilidad"])
        self.assertIsNone(nb["autonomia_h"])
        self.assertTrue(any("autonomia" in d for d in nb["datos_faltantes"]))

    def test_filtra_por_el_pedido(self):
        """Todas las consultas filtran por $requerimiento_id y lo reciben como parámetro."""
        for nombre, c in CONSULTAS.items():
            self.assertIn("{id:$requerimiento_id}", c, nombre)
        g = GrafoFalso(fixture("SM3.buscar"))
        try:
            sm3.ejecutar("SM3.buscar", {"requerimiento_id": "req_03", "orden": "grafica"}, g)
        except Aclaracion:
            pass
        self.assertEqual(g.llamadas[-1][1]["requerimiento_id"], "req_03")

    def test_peso_fuera_de_rango(self):
        g = GrafoFalso()
        with self.assertRaises(Aclaracion):
            sm3.ejecutar("SM3.buscar", {"requerimiento_id": "req_01", "orden": "movilidad",
                                        "filtros": {"peso_max": 50}}, g)
        self.assertEqual(g.llamadas, [])

    def test_orden_invalido(self):
        with self.assertRaises(Aclaracion):
            sm3.ejecutar("SM3.buscar", {"requerimiento_id": "req_01", "orden": "precio"}, GrafoFalso())

    def test_sin_dependencias_fuera_de_lo_permitido(self):
        from pathlib import Path
        import re
        for f in (Path(sm3.__file__).parent).glob("*.py"):
            self.assertIsNone(re.search(r"langchain|pydantic|rich|dotenv", f.read_text(encoding="utf-8")), f.name)


@requiere_neo4j
class ConGrafo(unittest.TestCase):
    def test_x_grado_gpu_074(self):
        nbs = sm3.ejecutar("SM3.buscar", {"requerimiento_id": "req_01", "orden": "grafica",
                                          "filtros": {"dedicada": True}}, grafo_real())["evidencia"]["notebooks"]
        self.assertEqual(next(n for n in nbs if n["notebook"] == "Notebook_X")["grado_gpu"], 0.74)

    def test_solo_las_evaluaciones_del_pedido(self):
        """K está evaluada en req_01 (VIRT) y en req_03 (OFI): cada pedido ve solo la suya."""
        g = grafo_real()
        r3 = sm3.ejecutar("SM3.buscar", {"requerimiento_id": "req_03", "orden": "grafica"}, g)["evidencia"]
        self.assertEqual([(n["notebook"]) for n in r3["notebooks"]], ["Notebook_K"])
        self.assertEqual(r3["perfil"], "OFI")
        r1 = sm3.ejecutar("SM3.ficha", {"requerimiento_id": "req_01", "modelo": "Notebook_K"}, g)["evidencia"]
        self.assertEqual(r1["perfil"], "VIRT")

    def test_ficha_m(self):
        nb = sm3.ejecutar("SM3.ficha", {"requerimiento_id": "req_01", "modelo": "Notebook_M"},
                          grafo_real())["evidencia"]["notebooks"][0]
        self.assertIsNone(nb["adecuacion_movilidad"])


if __name__ == "__main__":
    unittest.main()
