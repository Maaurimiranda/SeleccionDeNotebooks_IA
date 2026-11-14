"""Consultas libres (D-08, issues #12 a #24): extracción, validación, alta, inferencia por $req y aclaración.

- Offline: la validación del JSON extraído (INT-R1, INT-R7, INT-R10, INT-R11), el router y el orquestador
  con un LLM y un SM1 de prueba, y que los archivos de inferencia tengan el filtro por $req.
- Con Neo4j (se saltean sin él): alta de un pedido nuevo, ranking de SM4, aclaración del mismo pedido,
  que req_01..req_03 no cambien y que la limpieza no deje restos.
"""
import re
import tempfile
import unittest
from unittest import mock

from asistente import inferencia, router
from asistente.contrato import Aclaracion
from asistente.extractor import ESQUEMA_PEDIDO
from asistente.orquestador import Orquestador
from asistente.submodulos.sm1 import servicio
from tests.comun import GrafoFalso, fixture, grafo_real

VOCAB = {"expresiones": ["a veces", "la necesito para", "todos los dias", "principalmente"],
         "horas_expresion": {"a veces": 4.0, "la necesito para": 28.0, "todos los dias": 14.0, "principalmente": 28.0},
         "juegos": ["Cyberpunk 2077", "Fortnite", "Stardew Valley"],
         "catalogo": [f"Notebook_{x}" for x in "ABCEGHKMX"]}


def act(descripcion, tipo, evidencia, expresion=None, horas=None, periodo=None, juegos=()):
    return {"descripcion": descripcion, "tipo": tipo, "evidencia": evidencia, "expresion_frecuencia": expresion,
            "cantidad_horas": horas, "periodo_horas": periodo, "juegos": list(juegos)}


def ext(monto=None, moneda=None, actividades=(), prioridad="ninguna", es_pedido=True):
    return {"es_pedido_notebook": es_pedido, "presupuesto": {"monto": monto, "moneda": moneda, "evidencia": None},
            "prioridad": prioridad, "usa_monitor_externo": False, "notebook_consultada": None,
            "actividades": list(actividades)}


TEXTO_VIRT = "Quiero una notebook para programar y usar Docker, y a veces jugar al Fortnite. Tengo 900 dólares."
EXT_VIRT = ext(900, "USD", [act("programar", "programar", "para programar", "la necesito para"),
                            act("usar Docker", "virtualizar", "usar Docker", "la necesito para"),
                            act("jugar", "jugar", "a veces jugar al Fortnite", "a veces", juegos=["Fortnite"])])


# ---------------------------------------------------------------------------
# Validación (offline)
# ---------------------------------------------------------------------------
class TestValidacion(unittest.TestCase):
    def test_pedido_completo(self):
        datos, faltan, motivo = servicio.validar_pedido(TEXTO_VIRT, EXT_VIRT, VOCAB)
        self.assertEqual((faltan, motivo), ([], None))
        self.assertEqual(datos["presupuesto_usd"], 900.0)
        self.assertEqual([a["perfil"] for a in datos["actividades"]], ["VIRT", "VIRT", "GAM"])   # INT-R11
        self.assertEqual(datos["actividades"][2]["juegos"], ["Fortnite"])
        self.assertEqual(datos["actividades"][2]["expresion"], "a veces")

    def test_programar_sin_virtualizar_es_dev(self):
        datos, _, _ = servicio.validar_pedido("Necesito una notebook para programar, tengo 1000 USD",
                                              ext(1000, "USD", [act("programar", "programar", "para programar")]),
                                              VOCAB)
        self.assertEqual(datos["actividades"][0]["perfil"], "DEV")
        self.assertEqual(datos["actividades"][0]["expresion"], "la necesito para")

    def test_sin_presupuesto_repregunta(self):
        datos, faltan, motivo = servicio.validar_pedido(
            "Necesito usar máquinas virtuales todos los días",
            ext(actividades=[act("virtualizar", "virtualizar", "usar máquinas virtuales todos los días",
                                 "todos los dias")]), VOCAB)
        self.assertIsNone(datos["presupuesto_usd"])
        self.assertIn("presupuesto", motivo)          # INT-R1: no se escribe nada

    def test_sin_usos_repregunta(self):
        _, faltan, _ = servicio.validar_pedido("Tengo 800 USD", ext(800, "USD"), VOCAB)
        self.assertTrue(any("Para qué vas a usar" in f for f in faltan))

    def test_sin_frecuencia_repregunta_horas(self):
        _, faltan, _ = servicio.validar_pedido("Edito video, 800 USD",
                                               ext(800, "USD", [act("editar video", "editar_video", "Edito video")]),
                                               VOCAB)
        self.assertTrue(any("horas por semana" in f for f in faltan))

    def test_actividad_inventada_se_descarta(self):
        e = ext(900, "USD", [*EXT_VIRT["actividades"], act("renderizar", "modelar_3d", "renderizo en Blender")])
        datos, _, _ = servicio.validar_pedido(TEXTO_VIRT, e, VOCAB)
        self.assertNotIn("VID3D", [a["perfil"] for a in datos["actividades"]])                 # INT-R7
        self.assertTrue(any("INT-R7" in o for o in datos["observaciones"]))

    def test_presupuesto_inventado_se_descarta(self):
        _, _, motivo = servicio.validar_pedido("Quiero programar todos los días",
                                               ext(1500, "USD", [act("programar", "programar",
                                                                     "programar todos los días", "todos los dias")]),
                                               VOCAB)
        self.assertIn("presupuesto", motivo)

    def test_manda_el_monto_escrito(self):
        datos, _, _ = servicio.validar_pedido(TEXTO_VIRT, {**EXT_VIRT, "presupuesto": {"monto": 1000, "moneda": "USD"}},
                                              VOCAB)
        self.assertEqual(datos["presupuesto_usd"], 900.0)

    def test_pesos_sin_cotizacion_pide_dolares(self):
        with mock.patch("asistente.config.COTIZACION_ARS_USD", None):
            _, _, motivo = servicio.validar_pedido("Quiero programar todos los días, tengo 800 mil pesos",
                                                   ext(800000, "ARS", [act("programar", "programar",
                                                                           "programar todos los días",
                                                                           "todos los dias")]), VOCAB)
        self.assertIn("INT-R10", motivo)

    def test_pesos_con_cotizacion(self):
        with mock.patch("asistente.config.COTIZACION_ARS_USD", 1000.0):
            datos, _, motivo = servicio.validar_pedido("Quiero programar todos los días, tengo 800 mil pesos",
                                                       ext(None, None, [act("programar", "programar",
                                                                            "programar todos los días",
                                                                            "todos los dias")]), VOCAB)
        self.assertIsNone(motivo)
        self.assertEqual((datos["presupuesto_usd"], datos["moneda_original"]), (800.0, "ARS"))

    def test_presupuesto_fuera_de_rango(self):
        _, _, motivo = servicio.validar_pedido("Tengo 50000 USD y quiero programar todos los días",
                                               ext(50000, "USD", [act("programar", "programar",
                                                                      "programar todos los días", "todos los dias")]),
                                               VOCAB)
        self.assertIn("INT-R1", motivo)

    def test_prioridad_sin_respaldo_se_descarta(self):
        datos, _, _ = servicio.validar_pedido(TEXTO_VIRT, {**EXT_VIRT, "prioridad": "rendimiento"}, VOCAB)
        self.assertEqual(datos["prioridad"], "ninguna")
        datos, _, _ = servicio.validar_pedido(TEXTO_VIRT + " Que sea liviana.",
                                              {**EXT_VIRT, "prioridad": "portabilidad"}, VOCAB)
        self.assertEqual(datos["prioridad"], "portabilidad")

    def test_juego_desconocido_se_informa(self):
        e = ext(900, "USD", [act("jugar", "jugar", "jugar al Valorant todos los días", "todos los dias",
                                 juegos=["Valorant"])])
        datos, _, _ = servicio.validar_pedido("Quiero jugar al Valorant todos los días, tengo 900 USD", e, VOCAB)
        self.assertEqual(datos["actividades"][0]["juegos"], [])
        self.assertTrue(any("Valorant" in o for o in datos["observaciones"]))

    def test_horas_declaradas_las_calcula_python(self):
        e = ext(700, "USD", [act("ofimatica", "ofimatica", "3 horas por día para Word", None, 21, "semana")])
        datos, _, _ = servicio.validar_pedido("La uso 3 horas por día para Word, tengo 700 USD", e, VOCAB)
        self.assertEqual(datos["actividades"][0]["horas"], 21.0)    # 3 × 7, no el 21 del LLM

    def test_utilidades(self):
        self.assertEqual(servicio.presupuesto_en_texto("tengo 1.200 dólares")[:2], (1200.0, "USD"))
        self.assertEqual(servicio.presupuesto_en_texto("USD 850")[:2], (850.0, "USD"))
        self.assertEqual(servicio.presupuesto_en_texto("800 mil pesos")[:2], (800000.0, "ARS"))
        self.assertIsNone(servicio.presupuesto_en_texto("tengo 1000"))
        self.assertEqual(servicio.horas_en_texto("unas 10 hs semanales"), 10.0)
        self.assertEqual(servicio.horas_en_texto("2,5 horas al día"), 17.5)
        self.assertTrue(servicio.contiene_expresion("Necesito una notebook para programar", "la necesito para"))


# ---------------------------------------------------------------------------
# Router (offline)
# ---------------------------------------------------------------------------
CATALOGO = VOCAB["catalogo"]
PEDIDOS = ["req_01", "req_02", "req_03"]


def plan(consultas, req=None):
    return {"requerimiento_id": req, "consultas": consultas, "evidencia": [], "fuera_de_alcance": False,
            "aclaracion": None}


class TestRouterPedidoNuevo(unittest.TestCase):
    def test_consulta_libre_registra_y_recomienda(self):
        v = router.validar(plan([]), TEXTO_VIRT, {}, CATALOGO, PEDIDOS)
        self.assertEqual([c["intencion"] for c in v["consultas"]], ["SM1.registrar_pedido", "SM4.recomendar"])
        self.assertEqual(v["consultas"][0]["parametros"], {"texto": TEXTO_VIRT})   # el texto del usuario, no el del LLM
        self.assertIsNone(v["requerimiento_id"])

    def test_consulta_libre_con_otra_intencion(self):
        v = router.validar(plan([{"intencion": "SM4.costo_beneficio", "parametros": {}}]),
                           "Uso Word todos los días, tengo 600 USD. ¿Cuál rinde más por su precio?", {}, CATALOGO,
                           PEDIDOS)
        self.assertEqual([c["intencion"] for c in v["consultas"]], ["SM1.registrar_pedido", "SM4.costo_beneficio"])

    def test_pedido_escrito_no_registra(self):
        v = router.validar(plan([{"intencion": "SM1.registrar_pedido", "parametros": {}},
                                 {"intencion": "SM4.recomendar", "parametros": {}}], "req_01"),
                           "¿Qué me recomendás para req_01? Tengo 900 USD", {}, CATALOGO, PEDIDOS)
        self.assertEqual([c["intencion"] for c in v["consultas"]], ["SM4.recomendar"])
        self.assertEqual(v["requerimiento_id"], "req_01")

    def test_pregunta_sin_pedido_sigue_pidiendo_el_pedido(self):
        with self.assertRaises(Aclaracion):
            router.validar(plan([{"intencion": "SM2.riesgo_ram", "parametros": {}}]),
                           "¿Qué riesgo de RAM tiene la Notebook_G?", {}, CATALOGO, PEDIDOS)

    def test_aclarar_usa_el_pedido_de_la_sesion(self):
        v = router.validar(plan([{"intencion": "SM1.aclarar_pedido", "parametros": {}}]),
                           "programo todos los días", {"requerimiento_id": "req_02"}, CATALOGO, PEDIDOS)
        self.assertEqual(v["requerimiento_id"], "req_02")
        self.assertEqual(v["consultas"][0], {"intencion": "SM1.aclarar_pedido",
                                             "parametros": {"respuesta": "programo todos los días"}})

    def test_parece_pedido(self):
        self.assertTrue(router.parece_pedido("Tengo 900 dólares"))
        self.assertTrue(router.parece_pedido("quiero programar y jugar"))
        self.assertFalse(router.parece_pedido("¿Qué riesgo de RAM tiene la Notebook_G?"))
        self.assertFalse(router.parece_pedido("¿Qué me recomendás para req_01? Tengo 900 USD"))


# ---------------------------------------------------------------------------
# Orquestador (offline, con un SM1 de prueba)
# ---------------------------------------------------------------------------
class LLMGuion:
    """LLM de prueba: devuelve el JSON de extracción o el plan, según el esquema que le piden."""
    modelo = "guion"

    def __init__(self):
        self.extraido, self.plan, self.textos_extraidos = None, plan([]), []

    def json(self, sistema, usuario, esquema, variables=None):
        if esquema is ESQUEMA_PEDIDO:
            self.textos_extraidos.append(usuario)
            return self.extraido
        return self.plan

    def texto(self, *a, **k):
        return ""

    def salud(self):
        return {"ok": True}


class SM1Falso:
    """Registra el pedido como req_101 si trae presupuesto; si no, repregunta (como SM1)."""

    def __init__(self):
        self.llamadas = []

    def ejecutar(self, intencion, parametros, grafo):
        self.llamadas.append((intencion, parametros))
        if intencion == "SM1.interpretacion_pedido":
            return {"consultas": [], "evidencia": fixture("SM1.interpretacion_pedido")["evidencia"]}
        if not (parametros.get("pedido") or {}).get("presupuesto", {}).get("monto"):
            raise Aclaracion("Para armar tu pedido me falta un dato. ¿Cuál es tu presupuesto?")
        req = parametros.get("requerimiento_id") or "req_101"
        return {"consultas": [{"nombre": "SM1.ALTA", "cypher": "", "parametros": {}, "filas": []}],
                "evidencia": {"requerimiento_id": req, "pedido_nuevo": intencion == "SM1.registrar_pedido",
                              "entendido": {"presupuesto_usd": 900.0}, "observaciones": []}}


class SM4Falso:
    def ejecutar(self, intencion, parametros, grafo):
        if parametros["requerimiento_id"] == "req_102":
            raise Aclaracion("El pedido req_102 no tiene notebooks evaluadas que recomendar.")
        return {"consultas": [], "evidencia": {"requerimiento_id": parametros["requerimiento_id"], "ranking": []}}


class TestOrquestadorPedidoNuevo(unittest.TestCase):
    def setUp(self):
        self.llm, self.sm1 = LLMGuion(), SM1Falso()
        grafo = GrafoFalso(pedidos=["req_01", "req_02", "req_03", "req_101", "req_102"])
        self.orq = Orquestador(grafo, self.llm, modulos={"SM1": self.sm1, "SM4": SM4Falso()},
                               dir_trazas=tempfile.mkdtemp())

    def test_registra_y_responde_sobre_el_pedido_nuevo(self):
        self.llm.extraido = EXT_VIRT
        sesion = {}
        r = self.orq.consultar(TEXTO_VIRT, sesion=sesion)
        self.assertEqual((r["requerimiento_id"], r["pedido_nuevo"]), ("req_101", True))
        self.assertEqual(sesion["requerimiento_id"], "req_101")
        self.assertEqual(r["submodulos_consultados"], ["SM1", "SM4"])
        self.assertEqual(r["traza"]["extraccion"]["json"], EXT_VIRT)          # el JSON de Ollama queda en la traza
        self.assertIn("Registré tu pedido como req_101.", r["respuesta"])
        intenciones = [i for i, _ in self.sm1.llamadas]
        self.assertEqual(intenciones, ["SM1.registrar_pedido", "SM1.interpretacion_pedido"])   # L1 después del alta

    def test_repregunta_y_completa_el_mismo_pedido(self):
        sesion = {}
        self.llm.extraido = ext(actividades=EXT_VIRT["actividades"])
        r = self.orq.consultar("Quiero programar y usar Docker todos los días", sesion=sesion)
        self.assertEqual(r["origen_respuesta"], "validacion")
        self.assertIn("presupuesto", r["repregunta"])
        self.assertEqual(sesion["borrador"], "Quiero programar y usar Docker todos los días")
        self.llm.extraido = EXT_VIRT
        r = self.orq.consultar("tengo 900 dólares", sesion=sesion)
        self.assertTrue(r["pedido_nuevo"])
        self.assertEqual(self.llm.textos_extraidos[-1],
                         'Pedido: "Quiero programar y usar Docker todos los días tengo 900 dólares"')
        self.assertNotIn("borrador", sesion)

    def test_si_sm4_no_puede_responder_el_pedido_igual_queda(self):
        self.llm.extraido = EXT_VIRT
        sm1 = self.sm1
        original = sm1.ejecutar
        sm1.ejecutar = lambda i, p, g: (original(i, {**p, "requerimiento_id": "req_102"}, g))
        r = self.orq.consultar(TEXTO_VIRT, sesion={})
        self.assertEqual(r["requerimiento_id"], "req_102")
        self.assertIn("no tiene notebooks evaluadas", r["respuesta"])
        self.assertNotEqual(r["origen_respuesta"], "validacion")

    def test_respuesta_a_la_pregunta_pendiente_aclara(self):
        self.llm.extraido = ext(900, "USD")
        sesion = {"requerimiento_id": "req_101", "preguntas_pendientes": ["¿Cuántas horas por semana…?"]}
        r = self.orq.consultar("unas 10 horas por semana", sesion=sesion)
        self.assertEqual(self.sm1.llamadas[0][0], "SM1.aclarar_pedido")
        self.assertEqual(self.sm1.llamadas[0][1]["requerimiento_id"], "req_101")
        self.assertFalse(r["pedido_nuevo"])
        self.assertIn("Actualicé el pedido req_101.", r["respuesta"])

    def test_una_pregunta_no_se_toma_como_aclaracion(self):
        sesion = {"requerimiento_id": "req_101", "preguntas_pendientes": ["¿Cuántas horas por semana…?"]}
        self.assertIsNone(self.orq._plan_de_sesion("¿Qué riesgo de RAM tiene la Notebook_G?", sesion))
        self.assertIsNone(self.orq._plan_de_sesion("Mostrame la ficha de la Notebook_A", sesion))


# ---------------------------------------------------------------------------
# Archivos de inferencia (offline)
# ---------------------------------------------------------------------------
class TestFiltroReq(unittest.TestCase):
    def test_todo_match_de_requerimiento_tiene_el_filtro(self):
        for nombre, linea, texto in inferencia.sentencias_inferencia():
            for m in re.finditer(r"MATCH \(c:Requerimiento[^\n]*", texto):
                resto = texto[m.start():m.start() + 300]
                with self.subTest(archivo=nombre, linea=linea):
                    self.assertIn(inferencia.FILTRO_REQ, resto)

    def test_sin_filtro_vuelve_al_canonico(self):
        con = "MATCH (c:Requerimiento)\nWHERE ($req IS NULL OR c.id = $req)\n  AND c.x = 1\nSET c.y = 2"
        self.assertEqual(inferencia.sin_filtro_req(con), "MATCH (c:Requerimiento)\nWHERE c.x = 1\nSET c.y = 2")
        con = "MATCH (c:Requerimiento)-[:R]->(p)\nWHERE ($req IS NULL OR c.id = $req)\nSET c.y = 2"
        self.assertEqual(inferencia.sin_filtro_req(con), "MATCH (c:Requerimiento)-[:R]->(p)\nSET c.y = 2")

    def test_inferir_exige_pedido(self):
        with self.assertRaises(ValueError):
            inferencia.inferir(None, None)


# ---------------------------------------------------------------------------
# Con Neo4j: alta, inferencia, aclaración y limpieza sobre el grafo real
# ---------------------------------------------------------------------------
FOTO = """
MATCH (c:Requerimiento) WHERE c.id IN ['req_01', 'req_02', 'req_03']
OPTIONAL MATCH (c)-[:EVALUA]->(ev:Evaluacion)
OPTIONAL MATCH (c)-[:RECIBE]->(:Recomendacion)-[p]->(n:Notebook)
RETURN c.id AS req, c.perfil_dominante AS dom, c.intensidad_valor AS inten,
       collect(DISTINCT [ev.notebook, ev.estado, ev.grado_recomendacion, ev.riesgo_valor]) AS evs,
       collect(DISTINCT [type(p), n.modelo, p.orden]) AS propuestas
ORDER BY req
"""


@unittest.skipUnless(grafo_real(), "sin Neo4j")
class TestPedidoNuevoConGrafo(unittest.TestCase):
    def setUp(self):
        from asistente.submodulos import sm1, sm4
        from asistente.submodulos.sm1 import repositorio
        self.grafo, self.sm1, self.sm4, self.repo = grafo_real(), sm1, sm4, repositorio
        self.foto = self.grafo.leer(FOTO)

    def tearDown(self):
        self.repo.borrar_pedidos_consulta(self.grafo)
        self.assertEqual(self.grafo.leer(FOTO), self.foto, "cambió un pedido precargado")
        self.assertEqual(self.grafo.leer("MATCH (c:Requerimiento {origen:'consulta'}) RETURN count(c) AS n")[0]["n"], 0)

    def test_pedido_virt_queda_evaluado_y_recomendado(self):
        r = self.sm1.ejecutar("SM1.registrar_pedido", {"texto": TEXTO_VIRT, "pedido": EXT_VIRT}, self.grafo)
        req = r["evidencia"]["requerimiento_id"]
        self.assertRegex(req, r"^req_1\d\d$")
        self.assertIn(req, self.grafo.pedidos())
        l1 = self.sm1.ejecutar("SM1.interpretacion_pedido", {"requerimiento_id": req}, self.grafo)["evidencia"]
        self.assertEqual(l1["perfil_dominante"], "VIRT")
        self.assertEqual({p["perfil"] for p in l1["perfiles"]}, {"VIRT", "GAM"})
        rec = self.sm4.ejecutar("SM4.recomendar", {"requerimiento_id": req}, self.grafo)["evidencia"]
        self.assertTrue(rec["ranking"])
        self.assertTrue(all(x["precio_usd"] <= 900 for x in rec["ranking"]))
        n = self.grafo.leer("MATCH (:Requerimiento {id:$r})-[:EVALUA]->(e) RETURN count(e) AS n", {"r": req})[0]["n"]
        self.assertEqual(n, 9)                     # una Evaluacion por notebook con SALIDA_PI2 de VIRT

    def test_aclarar_actualiza_el_mismo_pedido(self):
        texto = "Quiero usar Docker todos los días y editar video, tengo 950 USD"
        e = ext(950, "USD", [act("usar Docker", "virtualizar", "usar Docker todos los días", "todos los dias"),
                             act("editar video", "editar_video", "editar video")])
        req = self.sm1.ejecutar("SM1.registrar_pedido", {"texto": texto, "pedido": e},
                                self.grafo)["evidencia"]["requerimiento_id"]
        l1 = self.sm1.ejecutar("SM1.interpretacion_pedido", {"requerimiento_id": req}, self.grafo)["evidencia"]
        self.assertEqual(len(l1["preguntas_pendientes"]), 1)
        antes = self.grafo.leer("MATCH (c:Requerimiento) RETURN count(c) AS n")[0]["n"]
        self.sm1.ejecutar("SM1.aclarar_pedido", {"requerimiento_id": req, "respuesta": "unas 20 horas por semana",
                                                 "pedido": ext()}, self.grafo)
        self.assertEqual(self.grafo.leer("MATCH (c:Requerimiento) RETURN count(c) AS n")[0]["n"], antes)
        l1 = self.sm1.ejecutar("SM1.interpretacion_pedido", {"requerimiento_id": req}, self.grafo)["evidencia"]
        self.assertEqual(l1["preguntas_pendientes"], [])
        self.assertIn("VID3D", {p["perfil"] for p in l1["perfiles"]})   # el video ya tiene dedicación y grado

    def test_sin_presupuesto_no_escribe(self):
        antes = self.grafo.leer("MATCH (n) RETURN count(n) AS n")[0]["n"]
        with self.assertRaises(Aclaracion):
            self.sm1.ejecutar("SM1.registrar_pedido", {"texto": "Quiero programar todos los días",
                                                       "pedido": ext(actividades=[act("programar", "programar",
                                                                                      "programar todos los días",
                                                                                      "todos los dias")])},
                              self.grafo)
        self.assertEqual(self.grafo.leer("MATCH (n) RETURN count(n) AS n")[0]["n"], antes)

    def test_inferir_un_pedido_cargado_es_idempotente(self):
        inferencia.inferir(self.grafo, "req_01")


if __name__ == "__main__":
    unittest.main()
