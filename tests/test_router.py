"""PG3-06: router. Offline: cada regla de validar(). Con LLM: acierto sobre el CSV.

La prueba con LLM es lenta (qwen2.5:3b, decenas de segundos por consulta), así que corre
solo con PG3_TEST_LLM=1 y Ollama levantado:  PG3_TEST_LLM=1 python -m unittest tests.test_router
"""
import csv
import os
import unittest
from pathlib import Path

from asistente.contrato import Aclaracion, FueraDeAlcance
from asistente.router import normalizar_modelo, normalizar_pedido, validar

CATALOGO = [f"Notebook_{x}" for x in "ABCEGHKMX"]
PEDIDOS = ["req_01", "req_02", "req_03"]
CSV = Path(__file__).resolve().parent / "datos" / "consultas_router.csv"


def plan(consultas, req=None, fuera=False, evidencia=None):
    return {"requerimiento_id": req, "consultas": consultas, "evidencia": evidencia or [],
            "fuera_de_alcance": fuera, "aclaracion": None}


def v(p, texto, sesion=None):
    return validar(p, texto, sesion or {}, CATALOGO, PEDIDOS)


class TestValidar(unittest.TestCase):
    def test_plan_valido(self):
        r = v(plan([{"intencion": "SM4.explicar_notebook", "parametros": {"modelo": "la G"}},
                    {"intencion": "SM2.riesgo_ram", "parametros": {"modelos": ["G"]}}], "req_01"),
              "¿Por qué la G quedó indeterminada y qué riesgo de RAM tiene en req_01?")
        self.assertEqual(r["requerimiento_id"], "req_01")
        self.assertEqual([c["intencion"] for c in r["consultas"]], ["SM4.explicar_notebook", "SM2.riesgo_ram"])
        self.assertEqual(r["consultas"][0]["parametros"]["modelo"], "Notebook_G")
        self.assertEqual(r["consultas"][1]["parametros"]["modelos"], ["Notebook_G"])

    def test_los_filtros_que_el_texto_no_pide_se_descartan(self):
        """El modelo chico copia los filtros del ejemplo del prompt: solo valen los que el usuario dijo."""
        p = plan([{"intencion": "SM3.buscar", "parametros": {"orden": "movilidad",
                  "filtros": {"peso_max": 2.5, "bateria_min": 8, "dedicada": True}}}], "req_01")
        r = v(p, "Para req_01, ¿cuáles son las mejores en movilidad?")
        self.assertNotIn("filtros", r["consultas"][0]["parametros"])
        self.assertTrue(any("filtros" in o for o in r["observaciones"]))
        r = v(p, "Para req_01, las de más de 8 horas de batería, con gráfica dedicada y menos de 2,5 kg")
        self.assertEqual(r["consultas"][0]["parametros"]["filtros"], {"peso_max": 2.5, "bateria_min": 8, "dedicada": True})

    def test_filtro_escrito_en_palabras_o_con_punto_de_miles(self):
        from asistente.router import _filtro_en_texto
        self.assertTrue(_filtro_en_texto(8, "las de ocho horas de batería"))
        self.assertTrue(_filtro_en_texto(2500, "menos de 2.500 gramos"))
        self.assertTrue(_filtro_en_texto(2.5, "menos de 2,5 kg"))
        self.assertFalse(_filtro_en_texto(8, "las de nueve horas"))
        self.assertFalse(_filtro_en_texto(8, "las de 18 horas"))   # el 8 de 18 no cuenta

    def test_intencion_invalida_se_descarta(self):
        r = v(plan([{"intencion": "SM9.volar", "parametros": {}},
                    {"intencion": "SM4.recomendar", "parametros": {}}], "req_01"), "recomendame algo para req_01")
        self.assertEqual([c["intencion"] for c in r["consultas"]], ["SM4.recomendar"])
        self.assertTrue(any("inválida" in o for o in r["observaciones"]))

    def test_sm_e_intencion_separados(self):
        r = v(plan([{"sm": "SM4", "intencion": "recomendar", "parametros": {}}], "req_01"), "recomendame para req_01")
        self.assertEqual(r["consultas"][0]["intencion"], "SM4.recomendar")

    def test_fragmento_no_literal_se_descarta(self):
        r = v(plan([{"intencion": "SM4.recomendar", "parametros": {}}], "req_01",
                   evidencia=[{"dato": "pedido", "fragmento": "req_01"}, {"dato": "x", "fragmento": "inventado"}]),
              "¿Qué me recomendás para req_01?")
        self.assertEqual([e["fragmento"] for e in r["evidencia"]], ["req_01"])

    def test_pedido_inventado_por_el_llm_no_se_asume(self):
        with self.assertRaises(Aclaracion):
            v(plan([{"intencion": "SM4.recomendar", "parametros": {}}], "req_01"), "¿Qué me recomendás?")

    def test_pedido_de_la_sesion(self):
        r = v(plan([{"intencion": "SM4.recomendar", "parametros": {}}], None), "¿Qué me recomendás?",
              {"requerimiento_id": "req_01"})
        self.assertEqual(r["requerimiento_id"], "req_01")

    def test_manda_el_pedido_escrito(self):
        r = v(plan([{"intencion": "SM4.recomendar", "parametros": {}}], "req_01"), "y para req_03?",
              {"requerimiento_id": "req_01"})
        self.assertEqual(r["requerimiento_id"], "req_03")

    def test_pedido_inexistente(self):
        with self.assertRaises(Aclaracion):
            v(plan([{"intencion": "SM4.recomendar", "parametros": {}}], "req_09"), "recomendame para req_09")

    def test_modelo_inexistente(self):
        with self.assertRaises(Aclaracion):
            v(plan([{"intencion": "SM3.ficha", "parametros": {"modelo": "Notebook_Z"}}], "req_01"),
              "ficha de la Notebook_Z en req_01")
        with self.assertRaises(Aclaracion):   # aunque el LLM no lo proponga, está en el texto
            v(plan([{"intencion": "SM4.recomendar", "parametros": {}}], "req_01"), "y la Notebook_Q en req_01?")

    def test_modelo_tomado_del_texto(self):
        r = v(plan([{"intencion": "SM3.ficha", "parametros": {}}], "req_01"), "ficha de la Notebook_M en req_01")
        self.assertEqual(r["consultas"][0]["parametros"]["modelo"], "Notebook_M")

    def test_comparar_necesita_dos_o_tres(self):
        with self.assertRaises(Aclaracion):
            v(plan([{"intencion": "SM4.comparar", "parametros": {"modelos": ["Notebook_A"]}}], "req_01"),
              "compará la Notebook_A en req_01")

    def test_fuera_de_alcance(self):
        with self.assertRaises(FueraDeAlcance):
            v(plan([], fuera=True), "¿Cuál es la capital de Francia?")

    def test_fuera_de_alcance_falso_se_ignora(self):
        r = v(plan([{"intencion": "SM4.recomendar", "parametros": {}}], "req_01", fuera=True),
              "¿Qué notebook me recomendás para req_01?")
        self.assertEqual(r["consultas"][0]["intencion"], "SM4.recomendar")

    def test_plan_vacio_del_dominio_pide_reformular(self):
        with self.assertRaises(Aclaracion):
            v(plan([]), "notebook algo req_01")

    def test_nivel_2_no_disponible(self):
        with self.assertRaises(Aclaracion):
            v(plan([{"intencion": "SM1.registrar_pedido", "parametros": {}}]), "quiero cargar un pedido nuevo")

    def test_maximo_tres_consultas(self):
        cs = [{"intencion": i, "parametros": {}} for i in
              ("SM4.recomendar", "SM4.costo_beneficio", "GRUPO.parametros", "SM2.virtualizacion")]
        self.assertEqual(len(v(plan(cs, "req_01"), "todo sobre req_01")["consultas"]), 3)

    def test_parametros_no_permitidos_se_ignoran(self):
        r = v(plan([{"intencion": "SM4.recomendar", "parametros": {"modelo": "Notebook_A", "tipo_ram": "x"}}],
                   "req_01"), "recomendame para req_01")
        self.assertEqual(r["consultas"][0]["parametros"], {})

    def test_plan_no_dict(self):
        with self.assertRaises(FueraDeAlcance):
            v(None, "hola")

    def test_normalizaciones(self):
        self.assertEqual(normalizar_pedido("REQ 1"), "req_01")
        self.assertEqual(normalizar_modelo("notebook g"), "Notebook_G")
        self.assertEqual(normalizar_modelo("la X"), "Notebook_X")


def leer_csv():
    with CSV.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


class TestCSV(unittest.TestCase):
    def test_cobertura_del_csv(self):
        filas = leer_csv()
        self.assertGreaterEqual(len(filas), 20)
        from asistente.contrato import INTENCIONES
        cubiertas = {i for f in filas for i in f["intenciones_esperadas"].split("|") if i}
        self.assertEqual(cubiertas, set(INTENCIONES))
        cuenta = lambda c: sum(1 for f in filas if f["cubre"] == c)  # noqa: E731
        self.assertGreaterEqual(cuenta("multisubmodulo"), 4)
        self.assertGreaterEqual(cuenta("fuera_de_alcance"), 3)
        self.assertGreaterEqual(cuenta("sin_pedido"), 2)
        self.assertGreaterEqual(cuenta("modelo_inexistente"), 2)


@unittest.skipUnless(os.getenv("PG3_TEST_LLM") == "1", "prueba con LLM: exportar PG3_TEST_LLM=1 (lenta)")
class TestRouterConLLM(unittest.TestCase):
    def test_acierto_sobre_el_csv(self):
        from asistente.llm import LLM
        from asistente.router import planificar
        llm = LLM()
        if not llm.salud()["ok"]:
            self.skipTest("Ollama o el modelo no disponible")
        aciertos_int, aciertos_res, detalle = 0, 0, []
        for f in leer_csv():
            sesion = {"requerimiento_id": f["pedido_sesion"]} if f["pedido_sesion"] else {}
            p = planificar(f["consulta"], sesion, llm, CATALOGO, PEDIDOS)
            obtenidas = {c.get("intencion") for c in p.get("consultas") or []}
            esperadas = {i for i in f["intenciones_esperadas"].split("|") if i}
            ok_int = obtenidas == esperadas
            try:
                validar(p, f["consulta"], sesion, CATALOGO, PEDIDOS)
                resultado = "plan"
            except Aclaracion:
                resultado = "aclaracion"
            except FueraDeAlcance:
                resultado = "fuera_de_alcance"
            ok_res = resultado == f["resultado_esperado"]
            aciertos_int += ok_int
            aciertos_res += ok_res
            detalle.append(f"{f['id']}: intenciones {'OK' if ok_int else 'X'} {sorted(obtenidas)} · "
                           f"resultado {'OK' if ok_res else 'X'} {resultado}")
        n = len(detalle)
        print("\n" + "\n".join(detalle))
        print(f"\nAcierto de intenciones: {aciertos_int}/{n} = {aciertos_int / n:.0%} · "
              f"resultado final: {aciertos_res}/{n} = {aciertos_res / n:.0%}")
        self.assertGreaterEqual(aciertos_int / n, 0.85)


if __name__ == "__main__":
    unittest.main()
