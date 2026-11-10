"""PG3-12: SM4.recomendar, SM4.explicar_notebook, SM4.comparar y SM4.costo_beneficio."""
import re
import unittest
from pathlib import Path

from asistente.contrato import Aclaracion, ESTADOS, SIN_VALIDAR
from asistente.submodulos import sm4
from asistente.submodulos.sm4.repositorio import CONSULTAS
from tests.comun import GrafoFalso, fixture, grafo_real, requiere_neo4j

PREFIJOS_DE_ESTADO = ("Recomendada", "Descartada", "Indeterminada")
CLAVES_VALIDACION = ("validacion", "validacion_margen")


def literales_invalidos(obj, ruta="evidencia") -> list[str]:
    """Recorre toda la evidencia: los estados y la validación tienen que ser los literales de D-06."""
    malos = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == "estado" and v not in ESTADOS:
                malos.append(f"{ruta}.estado = {v!r}")
            if k in CLAVES_VALIDACION and v != SIN_VALIDAR:
                malos.append(f"{ruta}.{k} = {v!r}")
            malos += literales_invalidos(v, f"{ruta}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            malos += literales_invalidos(v, f"{ruta}[{i}]")
    elif isinstance(obj, str) and obj.startswith(PREFIJOS_DE_ESTADO) and obj not in ESTADOS:
        malos.append(f"{ruta} = {obj!r}")
    return malos


def estados_de(obj) -> set:
    if isinstance(obj, dict):
        return ({obj["estado"]} if "estado" in obj else set()).union(*(estados_de(v) for v in obj.values()))
    if isinstance(obj, list):
        return set().union(*(estados_de(v) for v in obj))
    return set()


def por_modelo(lista: list[dict], modelo: str) -> dict:
    return next(n for n in lista if n["notebook"] == modelo)


def ejecutar_fixture(nombre: str) -> dict:
    f = fixture(nombre)
    return sm4.ejecutar(f["intencion"], f["parametros"], GrafoFalso(f))


class TestSM4Offline(unittest.TestCase):
    def test_recomendar_req_01_ranking(self):
        r = ejecutar_fixture("SM4.recomendar")
        e = r["evidencia"]
        self.assertEqual([c["nombre"] for c in r["consultas"]],
                         ["SM4.Q1_RECOMENDACION", "SM4.Q2_NO_PROPUESTAS", "SM4.Q3_SIN_ALTERNATIVA",
                          "SM4.Q6B_CRITERIO_DESEMPATE"])
        self.assertEqual([(n["puesto"], n["notebook"]) for n in e["ranking"]],
                         [(1, "Notebook_A"), (2, "Notebook_H"), (3, "Notebook_B")])
        a, h, b = e["ranking"]
        self.assertEqual(a["grado"], 0.785)
        self.assertEqual(a["estado"], "Recomendada (Alta)")
        self.assertEqual(a["empata_con"], [])
        # H y B caen en la misma franja de REC-R8: desempata la ampliabilidad (alta frente a baja)
        self.assertEqual((h["empata_con"], b["empata_con"]), (["Notebook_B"], ["Notebook_H"]))
        self.assertEqual((h["ampliabilidad_ram"], b["ampliabilidad_ram"]), ("alta", "baja"))
        self.assertEqual(e["criterio_desempate"]["regla"], "REC-R8")
        self.assertEqual(e["criterio_desempate"]["margen_empate"], 0.05)
        self.assertIsNone(e["sin_alternativa"])

    def test_recomendar_x_fuera_de_presupuesto(self):
        x = ejecutar_fixture("SM4.recomendar")["evidencia"]["fuera_de_presupuesto"]
        self.assertEqual(x["notebook"], "Notebook_X")
        self.assertEqual(x["excedente_presupuesto_pct"], 5.0)
        self.assertEqual([(a["codigo"], a["notebook"]) for a in x["alertas"]], [("GM-R8", "Notebook_X")])

    def test_recomendar_no_propuestas_con_motivo_y_regla(self):
        nps = ejecutar_fixture("SM4.recomendar")["evidencia"]["no_propuestas"]
        estados = {n["notebook"]: n["estado"] for n in nps}
        self.assertEqual(estados, {
            "Notebook_M": "Recomendada condicionada por falta de informacion",
            "Notebook_E": "Descartada (excluyente incumplido)",
            "Notebook_C": "Descartada",
            "Notebook_K": "Descartada",
            "Notebook_G": "Indeterminada: completar informacion",
        })
        self.assertEqual(por_modelo(nps, "Notebook_E")["regla"], "REC-R3")
        self.assertEqual(por_modelo(nps, "Notebook_G")["regla"], "REC-R3")
        c = por_modelo(nps, "Notebook_C")
        self.assertEqual((c["regla"], c["excedente_presupuesto_pct"]), ("REC-RD5", 20.0))
        self.assertTrue(all(n["motivo"] for n in nps))
        m = por_modelo(nps, "Notebook_M")
        self.assertEqual(m["grado"], {"min": 0.504, "max": 0.826})      # el rango no se completa
        self.assertEqual(m["dato_faltante"], "adecuacion_movilidad (autonomia no informada)")

    def test_recomendar_consulta_puntual_no_arma_ranking(self):
        e = ejecutar_fixture("SM4.recomendar.req_03")["evidencia"]
        self.assertEqual((e["ranking"], e["fuera_de_presupuesto"]), ([], None))
        k = e["no_propuestas"][0]
        self.assertEqual((k["notebook"], k["estado"]), ("Notebook_K", "Recomendada (Media)"))
        self.assertIn("consulta puntual", k["motivo"])

    def test_explicar_m_con_rango_y_falta_verificar_autonomia(self):
        r = ejecutar_fixture("SM4.explicar_notebook")
        self.assertEqual([c["nombre"] for c in r["consultas"]], ["SM4.Q4_EXPLICAR_NOTEBOOK"])
        e = r["evidencia"]
        m = e["notebooks"][0]
        self.assertEqual(m["notebook"], "Notebook_M")
        self.assertEqual(m["estado"], "Recomendada condicionada por falta de informacion")
        self.assertEqual(m["grado"], {"min": 0.504, "max": 0.826})
        self.assertEqual(m["adecuacion_global"], {"min": 0.741, "max": 0.908})
        self.assertTrue(any("autonomia" in x for x in m["falta_verificar"]))
        self.assertEqual([(a["codigo"], a["notebook"]) for a in m["alertas"]], [("REC-R15", "Notebook_M")])
        self.assertTrue(m["indice_con_peor_caso"])
        self.assertEqual(m["no_cumple"], [])
        self.assertTrue(m["cumple"])
        self.assertEqual(e["perfil"], "VIRT")
        self.assertNotIn(0.665, _numeros(e))                             # ni el promedio de 0,504 y 0,826

    def test_explicar_g_indeterminada(self):
        g = ejecutar_fixture("SM4.explicar_notebook.G")["evidencia"]["notebooks"][0]
        self.assertEqual(g["estado"], "Indeterminada: completar informacion")
        self.assertEqual(g["ampliabilidad_ram"], "desconocida")
        self.assertEqual({a["codigo"] for a in g["alertas"]}, {"FZ-R7", "REN-R10", "REC-R13"})
        self.assertTrue(all(a["notebook"] == "Notebook_G" for a in g["alertas"]))

    def test_comparar_e_b_h_el_excluyente_gana_al_puntaje(self):
        r = ejecutar_fixture("SM4.comparar")
        self.assertEqual([c["nombre"] for c in r["consultas"]],
                         ["SM4.Q6_COMPARAR", "SM4.Q6B_CRITERIO_DESEMPATE"])
        e = r["evidencia"]
        nbs = e["notebooks"]
        self.assertEqual([n["notebook"] for n in nbs], ["Notebook_H", "Notebook_B", "Notebook_E"])
        h, b, x = nbs
        self.assertEqual((h["en_la_recomendacion"], b["en_la_recomendacion"]), ("puesto 2", "puesto 3"))
        self.assertEqual(x["estado"], "Descartada (excluyente incumplido)")
        self.assertEqual(x["regla"], "REC-R3")
        # E tiene el mismo puntaje que B y H (≈ 0,81) y aun así queda descartada
        for n in nbs:
            self.assertAlmostEqual(n["adecuacion_global"], 0.81, delta=0.005)
        self.assertNotIn("empata_con", x)
        self.assertEqual(e["criterio_desempate"]["regla"], "REC-R8")

    def test_costo_beneficio_ordenado_por_indice(self):
        r = ejecutar_fixture("SM4.costo_beneficio")
        self.assertEqual([c["nombre"] for c in r["consultas"]], ["SM4.Q7_COSTO_BENEFICIO"])
        e = r["evidencia"]
        nbs = e["notebooks"]
        indices = [n["indice_costo_beneficio"] for n in nbs]
        self.assertEqual(indices, sorted(indices, reverse=True))
        self.assertEqual([n["posicion"] for n in nbs], list(range(1, len(nbs) + 1)))
        self.assertEqual((nbs[0]["notebook"], nbs[0]["indice_costo_beneficio"]), ("Notebook_B", 1.161))
        modelos = {n["notebook"] for n in nbs}
        self.assertFalse({"Notebook_E", "Notebook_G", "Notebook_K", "Notebook_C"} & modelos)   # no recomendadas
        self.assertEqual(e["regla"]["id"], "REC-R9")
        m = por_modelo(nbs, "Notebook_M")
        self.assertEqual(m["adecuacion_global"], {"min": 0.741, "max": 0.908})
        self.assertTrue(m["indice_con_peor_caso"])

    def test_literales_de_d06_en_toda_la_evidencia(self):
        vistos = set()
        for nombre in ("SM4.recomendar", "SM4.recomendar.req_03", "SM4.explicar_notebook",
                       "SM4.explicar_notebook.G", "SM4.comparar", "SM4.costo_beneficio"):
            e = ejecutar_fixture(nombre)["evidencia"]
            self.assertEqual(literales_invalidos(e), [], nombre)
            vistos |= estados_de(e)
        self.assertEqual(vistos, set(ESTADOS))                  # los seis aparecen; el recorrido no es vacío

    def test_el_recorrido_detecta_un_literal_distinto(self):
        self.assertTrue(literales_invalidos({"ranking": [{"estado": "Recomendada (alta)"}]}))
        self.assertTrue(literales_invalidos({"x": ["Descartada por presupuesto"]}))
        self.assertTrue(literales_invalidos({"criterio": {"validacion": "provisional"}}))
        self.assertEqual(literales_invalidos({"estado": "Descartada", "validacion": SIN_VALIDAR}), [])

    def test_pedido_o_modelo_sin_evaluacion_lanza_aclaracion(self):
        vacio = GrafoFalso()
        for intencion, p in (("SM4.recomendar", {"requerimiento_id": "req_02"}),
                             ("SM4.costo_beneficio", {"requerimiento_id": "req_02"}),
                             ("SM4.explicar_notebook", {"requerimiento_id": "req_03", "modelo": "Notebook_A"}),
                             ("SM4.comparar", {"requerimiento_id": "req_03", "modelos": ["Notebook_A", "Notebook_H"]})):
            with self.subTest(intencion=intencion), self.assertRaises(Aclaracion):
                sm4.ejecutar(intencion, p, vacio)

    def test_comparar_un_modelo_no_evaluado_lanza_aclaracion(self):
        f = fixture("SM4.comparar")
        with self.assertRaises(Aclaracion) as cm:
            sm4.ejecutar("SM4.comparar", {"requerimiento_id": "req_01",
                                          "modelos": ["Notebook_E", "Notebook_B", "Notebook_Z"]}, GrafoFalso(f))
        self.assertIn("Notebook_Z", cm.exception.mensaje)

    def test_comparar_exige_dos_o_tres_modelos(self):
        for modelos in ([], ["Notebook_A"], ["Notebook_A", "Notebook_A"], list("ABCD"), None, "Notebook_A"):
            g = GrafoFalso()
            with self.subTest(modelos=modelos), self.assertRaises(Aclaracion):
                sm4.ejecutar("SM4.comparar", {"requerimiento_id": "req_01", "modelos": modelos}, g)
            self.assertEqual(g.llamadas, [])                    # se valida antes de consultar el grafo

    def test_sin_pedido_no_asume_req_01(self):
        for intencion in ("SM4.recomendar", "SM4.explicar_notebook", "SM4.comparar", "SM4.costo_beneficio"):
            g = GrafoFalso()
            with self.subTest(intencion=intencion), self.assertRaises(Aclaracion):
                sm4.ejecutar(intencion, {"modelo": "Notebook_A", "modelos": ["Notebook_A", "Notebook_H"]}, g)
            self.assertEqual(g.llamadas, [])

    def test_explicar_sin_modelo(self):
        with self.assertRaises(Aclaracion):
            sm4.ejecutar("SM4.explicar_notebook", {"requerimiento_id": "req_01"}, GrafoFalso())

    def test_intencion_de_otro_submodulo(self):
        with self.assertRaises(ValueError):
            sm4.ejecutar("SM2.riesgo_ram", {"requerimiento_id": "req_01"}, GrafoFalso())

    def test_filtra_por_el_pedido(self):
        """Todas las consultas, salvo el criterio de desempate, filtran por $requerimiento_id."""
        for nombre, c in CONSULTAS.items():
            if nombre != "Q6B_CRITERIO_DESEMPATE":
                self.assertIn("{id:$requerimiento_id}", c, nombre)
        f = fixture("SM4.recomendar")
        g = GrafoFalso(f)
        sm4.ejecutar("SM4.recomendar", {"requerimiento_id": "req_01"}, g)
        for cypher, parametros in g.llamadas:
            if "$requerimiento_id" in cypher:
                self.assertEqual(parametros["requerimiento_id"], "req_01")

    def test_solo_lectura(self):
        escritura = re.compile(r"\b(MERGE|CREATE|SET|DELETE|REMOVE|DROP|LOAD)\b")
        for nombre, c in CONSULTAS.items():
            self.assertIsNone(escritura.search(c), nombre)

    def test_todo_order_by_termina_en_un_desempate(self):
        """Dos corridas dan el mismo orden: la última clave de cada ORDER BY es única (modelo, motivo o regla)."""
        self.assertEqual({n for n, c in CONSULTAS.items() if "ORDER BY" not in c}, {"Q6B_CRITERIO_DESEMPATE"})
        for nombre, c in CONSULTAS.items():
            for o in re.findall(r"ORDER BY ([^\n]+)", c):
                ultima = re.sub(r"\s+(LIMIT \d+|DESC|ASC)\b", "", o.strip()).split(",")[-1].strip()
                self.assertIn(ultima, {"notebook", "motivo", "q.id"}, f"{nombre}: ORDER BY {o}")

    def test_sin_dependencias_fuera_de_lo_permitido(self):
        for f in Path(sm4.__file__).parent.glob("*.py"):
            self.assertIsNone(re.search(r"langchain|pydantic|rich|dotenv|urllib|requests", f.read_text(encoding="utf-8")),
                              f.name)


def _numeros(obj) -> set:
    if isinstance(obj, bool) or obj is None:
        return set()
    if isinstance(obj, (int, float)):
        return {obj}
    if isinstance(obj, dict):
        return set().union(*(_numeros(v) for v in obj.values())) if obj else set()
    if isinstance(obj, list):
        return set().union(*(_numeros(v) for v in obj)) if obj else set()
    return set()


@requiere_neo4j
class ConGrafo(unittest.TestCase):
    def ejecutar(self, intencion, **p):
        return sm4.ejecutar(intencion, p, grafo_real())["evidencia"]

    def test_e2e_1_recomendacion_completa(self):
        e = self.ejecutar("SM4.recomendar", requerimiento_id="req_01")
        self.assertEqual([(n["puesto"], n["notebook"]) for n in e["ranking"]],
                         [(1, "Notebook_A"), (2, "Notebook_H"), (3, "Notebook_B")])
        self.assertEqual(e["ranking"][0]["grado"], 0.785)
        self.assertEqual(e["fuera_de_presupuesto"]["notebook"], "Notebook_X")
        estados = {n["notebook"]: n["estado"] for n in e["no_propuestas"]}
        self.assertEqual(estados["Notebook_M"], "Recomendada condicionada por falta de informacion")
        self.assertEqual(estados["Notebook_E"], "Descartada (excluyente incumplido)")
        self.assertEqual(estados["Notebook_C"], "Descartada")
        self.assertEqual(estados["Notebook_G"], "Indeterminada: completar informacion")
        self.assertEqual(literales_invalidos(e), [])

    def test_e2e_2_m_rango_y_falta_la_autonomia(self):
        m = self.ejecutar("SM4.explicar_notebook", requerimiento_id="req_01", modelo="Notebook_M")["notebooks"][0]
        self.assertEqual(m["grado"], {"min": 0.504, "max": 0.826})
        self.assertTrue(any("autonomia" in x for x in m["falta_verificar"]))

    def test_e2e_5_el_excluyente_gana_al_puntaje(self):
        nbs = self.ejecutar("SM4.comparar", requerimiento_id="req_01",
                            modelos=["Notebook_E", "Notebook_B", "Notebook_H"])["notebooks"]
        e = por_modelo(nbs, "Notebook_E")
        self.assertEqual(e["estado"], "Descartada (excluyente incumplido)")
        self.assertAlmostEqual(e["adecuacion_global"], 0.81, delta=0.005)
        self.assertEqual([n["notebook"] for n in nbs][:2], ["Notebook_H", "Notebook_B"])

    def test_costo_beneficio(self):
        nbs = self.ejecutar("SM4.costo_beneficio", requerimiento_id="req_01")["notebooks"]
        indices = [n["indice_costo_beneficio"] for n in nbs]
        self.assertEqual(indices, sorted(indices, reverse=True))
        self.assertEqual(nbs[0]["notebook"], "Notebook_B")

    def test_los_pedidos_no_se_mezclan(self):
        """K es Descartada en req_01 (VIRT) y Recomendada (Media) en req_03 (OFI): cada pedido ve la suya."""
        k1 = self.ejecutar("SM4.explicar_notebook", requerimiento_id="req_01", modelo="Notebook_K")["notebooks"][0]
        k3 = self.ejecutar("SM4.explicar_notebook", requerimiento_id="req_03", modelo="Notebook_K")
        self.assertEqual(k1["estado"], "Descartada")
        self.assertEqual((k3["perfil"], k3["notebooks"][0]["estado"]), ("OFI", "Recomendada (Media)"))
        e3 = self.ejecutar("SM4.recomendar", requerimiento_id="req_03")
        self.assertEqual(e3["ranking"], [])

    def test_literales_d06_en_todo_lo_que_devuelve(self):
        g = grafo_real()
        salidas = [self.ejecutar("SM4.recomendar", requerimiento_id="req_01"),
                   self.ejecutar("SM4.costo_beneficio", requerimiento_id="req_01"),
                   self.ejecutar("SM4.comparar", requerimiento_id="req_01", modelos=["Notebook_A", "Notebook_G"])]
        salidas += [self.ejecutar("SM4.explicar_notebook", requerimiento_id="req_01", modelo=m)
                    for m in g.catalogo()]
        vistos = set()
        for e in salidas:
            self.assertEqual(literales_invalidos(e), [])
            vistos |= estados_de(e)
        self.assertEqual(vistos, set(ESTADOS))

    def test_pedido_o_modelo_sin_evaluacion(self):
        g = grafo_real()
        for intencion, p in (("SM4.recomendar", {"requerimiento_id": "req_02"}),
                             ("SM4.costo_beneficio", {"requerimiento_id": "req_02"}),
                             ("SM4.explicar_notebook", {"requerimiento_id": "req_03", "modelo": "Notebook_A"}),
                             ("SM4.comparar", {"requerimiento_id": "req_03",
                                               "modelos": ["Notebook_K", "Notebook_A"]})):
            with self.subTest(intencion=intencion), self.assertRaises(Aclaracion):
                sm4.ejecutar(intencion, p, g)

    def test_los_fixtures_siguen_al_grafo(self):
        """Los fixtures offline son la salida real: si el grafo o las consultas cambian, hay que regenerarlos."""
        g = grafo_real()
        for nombre in ("SM4.recomendar", "SM4.recomendar.req_03", "SM4.explicar_notebook",
                       "SM4.explicar_notebook.G", "SM4.comparar", "SM4.costo_beneficio"):
            f = fixture(nombre)
            self.assertEqual(sm4.ejecutar(f["intencion"], f["parametros"], g)["evidencia"], f["evidencia"], nombre)


if __name__ == "__main__":
    unittest.main()
