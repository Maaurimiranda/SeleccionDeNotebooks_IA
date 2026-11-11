"""PG3-13: el explicador común. Offline: el verificador (controles a-h), la plantilla fija y la regeneración.
Con LLM (PG3_TEST_LLM=1 y Ollama): las evidencias de los fixtures de los E2E.

    PG3_TEST_LLM=1 python -m unittest tests.test_explicador
"""
import os
import re
import unittest

from asistente import explicador
from asistente.contrato import ADVERTENCIA
from asistente.explicador import MAX_PALABRAS, MAX_PALABRAS_PLANTILLA, explicar, plantilla_fija, verificar
from tests.comun import fixture


def evidencia_de(*nombres: str) -> dict:
    """Evidencia común armada con los fixtures: SM1 va en `pedido`, el resto en su submódulo."""
    ev = {"advertencia": ADVERTENCIA}
    for n in nombres:
        datos = fixture(n)["evidencia"]
        if n.startswith("SM1."):
            ev["pedido"] = datos
        else:
            sm, intencion = n.split(".")[:2]
            previa = ev.setdefault(sm, {}).get(intencion)
            if previa and "notebooks" in previa:  # la misma intención para dos modelos (E2E-2): una sola evidencia
                datos = {**previa, "notebooks": previa["notebooks"] + datos["notebooks"]}
            ev[sm][intencion] = datos
    return ev


# Evidencia con estados, a mano: los fixtures de SM4 son de forma hasta que esté PG3-12.
EV_ESTADOS = {"advertencia": ADVERTENCIA, "SM4": {"recomendar": {"notebooks": [
    {"notebook": "Notebook_A", "estado": "Recomendada (Alta)", "grado": 0.785},
    {"notebook": "Notebook_M", "estado": "Recomendada condicionada por falta de informacion",
     "grado": {"min": 0.504, "max": 0.826}},
    {"notebook": "Notebook_E", "estado": "Descartada (excluyente incumplido)", "grado": 0.81}]}}}

CASOS_E2E = {
    "E2E-1": ("SM1.interpretacion_pedido", "SM2.riesgo_ram", "SM3.buscar", "SM4.recomendar"),
    "E2E-2": ("SM1.interpretacion_pedido", "SM2.riesgo_ram.todas", "SM4.explicar_notebook",
              "SM4.explicar_notebook.G"),
    "E2E-3": ("SM1.interpretacion_pedido.req_02",),
    "E2E-5": ("SM1.interpretacion_pedido", "SM4.comparar"),
    "E2E-9": ("SM1.interpretacion_pedido", "GRUPO.traza_reglas", "SM2.riesgo_ram"),
    "E2E-10": ("SM1.interpretacion_pedido", "SM3.buscar", "SM4.costo_beneficio"),
    "parametros": ("GRUPO.parametros",),
}


class LLMFalso:
    """Devuelve las respuestas armadas, una por llamada, y guarda lo que recibió."""
    modelo = "falso"

    def __init__(self, *respuestas: str):
        self.respuestas, self.llamadas = list(respuestas), []

    def texto(self, sistema, usuario, variables=None):
        self.llamadas.append({"sistema": sistema, "usuario": usuario, "variables": variables})
        return self.respuestas[min(len(self.llamadas), len(self.respuestas)) - 1]


def con(texto: str, advertencia: bool = True) -> str:
    return f"{texto} {ADVERTENCIA}" if advertencia else texto


class TestVerificador(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ram = evidencia_de("SM1.interpretacion_pedido", "SM2.riesgo_ram")
        cls.todas = evidencia_de("SM1.interpretacion_pedido", "SM2.riesgo_ram.todas")
        cls.indeterminado = evidencia_de("SM1.interpretacion_pedido.req_02")

    def assertDispara(self, control: str, respuesta: str, evidencia: dict):
        problemas = verificar(respuesta, evidencia)
        self.assertTrue(any(p.startswith(f"({control})") for p in problemas), f"({control}) no se disparó: {problemas}")

    # --- respuestas buenas
    def test_buena_con_rango_y_alerta(self):
        r = con("Para req_01, con presupuesto de 1000, el riesgo de RAM de Notebook_G va de 49.58 a 81.46: es alto. "
                "Alerta REN-R10: la ficha no informa si la RAM es ampliable.")
        self.assertEqual(verificar(r, self.ram), [])

    def test_buena_con_coma_decimal_y_redondeo(self):
        r = con("El perfil VIRT tiene grado 0,899 (casi 0.9) y presupuesto de 1000 USD.")
        self.assertEqual(verificar(r, self.ram), [])

    def test_punto_de_miles_no_es_decimal(self):
        self.assertEqual(verificar(con("El presupuesto es de 1.000 USD."), self.ram), [])
        self.assertTrue(any(p.startswith("(a)") for p in verificar(con("El presupuesto es de 2.000 USD."), self.ram)))

    def test_millones_con_puntos_no_se_leen_como_decimal(self):
        self.assertTrue(any(p.startswith("(a)") for p in verificar(con("El presupuesto es de 1.000.000 USD."), self.ram)))

    def test_buena_con_estados_con_tilde(self):
        r = con("Notebook_M queda Recomendada condicionada por falta de información, entre 0.504 y 0.826. "
                "Notebook_A queda Recomendada (Alta) con 0.785 y Notebook_E, Descartada (excluyente incumplido).")
        self.assertEqual(verificar(r, EV_ESTADOS), [])

    def test_buena_con_estado_dicho_en_corto(self):
        r = con("Notebook_E quedó descartada, aunque su puntaje es parecido: 0.81.")
        self.assertEqual(verificar(r, EV_ESTADOS), [])

    def test_buena_con_pedido_indeterminado(self):
        r = con("El pedido req_02 está indeterminado: falta saber para qué lo va a usar. Presupuesto de 600.")
        self.assertEqual(verificar(r, self.indeterminado), [])

    # --- una mala por cada control
    def test_a_cifra_inventada(self):
        self.assertDispara("a", con("El presupuesto de req_01 es de 1500 USD."), self.ram)

    def test_a_cifra_de_otra_notebook(self):
        ev = evidencia_de("SM1.interpretacion_pedido", "SM4.comparar")
        h, b = ev["SM4"]["comparar"]["notebooks"][:2]
        self.assertNotEqual(h["precio_usd"], b["precio_usd"])
        self.assertDispara("a", con(f"{h['notebook']} cuesta {b['precio_usd']:.0f}."), ev)

    def test_a_la_cifra_de_su_notebook_pasa(self):
        ev = evidencia_de("SM1.interpretacion_pedido", "SM4.comparar")
        h = ev["SM4"]["comparar"]["notebooks"][0]
        self.assertEqual(verificar(con(f"{h['notebook']} cuesta {h['precio_usd']:.0f}."), ev), [])

    def test_d_respuesta_vacia(self):
        self.assertDispara("d", "", self.ram)

    def test_f_otro_dato_de_la_notebook_dentro_del_rango_no_es_un_promedio(self):
        grado = EV_ESTADOS["SM4"]["recomendar"]["notebooks"][1]
        ev = {"SM4": {"recomendar": {"notebooks": [{**grado, "excedente": 0.7}]}}}
        self.assertEqual(verificar("Notebook_M: grado entre 0.504 y 0.826, excedente 0.7.", ev), [])

    def test_b_modelo_inexistente(self):
        self.assertDispara("b", con("Notebook_Z tiene riesgo alto."), self.ram)

    def test_b_regla_inexistente(self):
        self.assertDispara("b", con("Se activó la regla FZ-R99."), self.ram)

    def test_c_alerta_de_otra_notebook(self):
        alertas = explicador._alertas(self.todas)
        codigo, duenos = next((c, d) for c, d in alertas.items() if len(d) == 1)
        ajeno = next(m for m in explicador._MODELO.findall(str(self.todas)) if m not in duenos)
        self.assertDispara("c", con(f"{ajeno} tiene la alerta {codigo}."), self.todas)
        self.assertDispara("c", con(f"La alerta {codigo} aparece en {ajeno}."), self.todas)   # alerta nombrada antes del modelo

    def test_d_largo(self):
        self.assertDispara("d", con(" ".join(["palabra"] * (MAX_PALABRAS + 1))), self.ram)

    def test_e_sin_advertencia(self):
        self.assertDispara("e", con("El perfil VIRT tiene grado 0.899.", advertencia=False), self.ram)

    def test_f_valor_intermedio_de_un_rango(self):
        self.assertDispara("f", con("El riesgo de RAM de Notebook_G ronda 65.52."), self.ram)

    def test_f_un_solo_extremo(self):
        self.assertDispara("f", con("El riesgo de RAM de Notebook_G llega a 81.46."), self.ram)

    def test_g_perfil_asumido_con_pedido_indeterminado(self):
        self.assertDispara("g", con("Como es para GAM, te conviene una con buena gráfica."), self.indeterminado)

    def test_g_perfil_en_palabras(self):
        self.assertDispara("g", con("El perfil es de oficina, así que alcanza con cualquiera."), self.indeterminado)

    def test_h_estado_de_otra_notebook(self):
        self.assertDispara("h", con("Notebook_E queda Recomendada (Alta) con 0.81."), EV_ESTADOS)

    def test_h_estado_que_no_existe(self):
        self.assertDispara("h", con("Notebook_A queda Recomendada (Media)."), EV_ESTADOS)


class TestVerificadorRevision(unittest.TestCase):
    """Hallazgos de la revisión de código de PG3-13."""

    def assertDispara(self, control, respuesta, evidencia):
        problemas = verificar(respuesta, evidencia)
        self.assertTrue(any(p.startswith(f"({control})") for p in problemas), f"({control}): {problemas}")

    def test_una_cifra_degenerada_no_tumba_el_verificador(self):
        ev = evidencia_de("SM1.interpretacion_pedido", "SM2.riesgo_ram")
        self.assertDispara("a", con("El riesgo de Notebook_G es 0." + "9" * 40), ev)

    def test_oracion_con_dos_modelos_atribuye_cada_cifra_a_su_notebook(self):
        ev = evidencia_de("SM1.interpretacion_pedido", "SM4.comparar")
        h, b = ev["SM4"]["comparar"]["notebooks"][:2]
        bien = f"{h['notebook']} cuesta {h['precio_usd']:.0f} USD y {b['notebook']} cuesta {b['precio_usd']:.0f} USD."
        cruzada = f"{h['notebook']} cuesta {b['precio_usd']:.0f} USD y {b['notebook']} cuesta {h['precio_usd']:.0f} USD."
        self.assertEqual(verificar(con(bien), ev), [])
        self.assertDispara("a", con(cruzada), ev)

    def test_oracion_con_dos_modelos_atribuye_cada_estado(self):
        self.assertDispara("h", con("Notebook_A queda Descartada (excluyente incumplido) y Notebook_E, Recomendada (Alta)."),
                           EV_ESTADOS)

    def test_una_alerta_de_una_notebook_y_la_otra_sin_alertas_es_correcta(self):
        ev = {"advertencia": ADVERTENCIA, "SM4": {"recomendar": {"ranking": [
            {"notebook": "Notebook_X", "alertas": [{"codigo": "GM-R8", "texto": "t", "notebook": "Notebook_X"}]},
            {"notebook": "Notebook_C", "alertas": []}]}}}
        self.assertEqual(verificar(con("Notebook_X tiene la alerta GM-R8, y Notebook_C no tiene ninguna."), ev), [])

    def test_otro_dato_dentro_del_rango_en_otra_notebook_no_es_un_promedio(self):
        r = con("Notebook_M queda entre 0.504 y 0.826, por debajo de Notebook_A con 0.785.")
        self.assertEqual(verificar(r, EV_ESTADOS), [])

    def test_b_ids_de_reglas_difusas_y_no_subcadenas(self):
        ev = evidencia_de("SM1.interpretacion_pedido", "GRUPO.traza_reglas", "SM2.riesgo_ram")
        self.assertDispara("b", con("Aplica INT-RD42."), ev)
        self.assertDispara("b", con("Alerta REN-R1 en Notebook_G."), ev)   # REN-R1 no es REN-R10

    def test_c_una_alerta_no_es_una_regla_activada(self):
        ev = evidencia_de("SM1.interpretacion_pedido", "SM2.riesgo_ram")
        self.assertDispara("c", con("Notebook_G activó la regla FZ-R7 y por eso tiene riesgo entre 49.58 y 81.46."), ev)

    def test_h_no_se_recomienda_lo_que_la_evidencia_descarta(self):
        self.assertDispara("h", con("Te recomiendo Notebook_E, tiene grado 0.81."), EV_ESTADOS)
        self.assertEqual(verificar(con("No te recomiendo Notebook_E: está descartada."), EV_ESTADOS), [])
        self.assertEqual(verificar(con("Te recomiendo Notebook_A, con grado 0.785."), EV_ESTADOS), [])

    def test_h_no_se_recomienda_lo_que_esta_fuera_del_ranking(self):
        ev = evidencia_de("SM1.interpretacion_pedido", "SM4.recomendar")
        self.assertDispara("h", con("Te conviene Notebook_X, con grado 0.534."), ev)

    def test_g_perfil_sin_la_palabra_perfil_y_con_la_oracion_de_indeterminado(self):
        ev = evidencia_de("SM1.interpretacion_pedido.req_02")
        self.assertDispara("g", con("Como es para gaming, te conviene una con buena gráfica."), ev)
        self.assertDispara("g", con("El perfil es indeterminado, pero seguro es de oficina."), ev)

    def test_g_repetir_la_pregunta_pendiente_esta_permitido(self):
        ev = evidencia_de("SM1.interpretacion_pedido.req_02")
        pregunta = ev["pedido"]["preguntas_pendientes"][0]
        self.assertEqual(verificar(con(f"Falta definir qué va a hacer con la notebook: {pregunta}"), ev), [])

    def test_plantilla_avisa_si_recorta_reglas_y_marca_el_perfil_provisional(self):
        ev = evidencia_de("SM1.interpretacion_pedido", "GRUPO.traza_reglas")
        self.assertIn("y otras (ver la traza)", plantilla_fija(ev))
        ev["pedido"] = {**ev["pedido"], "perfil_dominante_provisional": True}
        self.assertIn("(provisional)", plantilla_fija(ev))


class TestPlantillaFija(unittest.TestCase):
    def test_la_recomendacion_va_primero_y_cada_fila_es_de_su_notebook(self):
        ev = evidencia_de("SM1.interpretacion_pedido", "SM2.riesgo_ram", "SM3.buscar", "SM4.recomendar")
        r = plantilla_fija(ev)
        self.assertIn("SM4.recomendar", r)
        self.assertIn("puesto 1, estado Recomendada (Alta)", r)

    def test_pasa_su_propio_verificador_en_los_fixtures(self):
        for caso, nombres in CASOS_E2E.items():
            with self.subTest(caso):
                ev = evidencia_de(*nombres)
                respuesta = plantilla_fija(ev)
                self.assertEqual(verificar(respuesta, ev, MAX_PALABRAS_PLANTILLA), [])
                self.assertLessEqual(len(respuesta.split()), MAX_PALABRAS_PLANTILLA)
                self.assertIn(ADVERTENCIA, respuesta)

    def test_pedido_indeterminado_no_asume_perfil(self):
        r = plantilla_fija(evidencia_de("SM1.interpretacion_pedido.req_02"))
        self.assertIn("indeterminado", r)
        self.assertFalse(re.search(r"\b(?:OFI|DEV|VIRT|DIS|VID3D|GAM|DATOS)\b", r))

    def test_conserva_los_rangos(self):
        r = plantilla_fija(evidencia_de("SM1.interpretacion_pedido", "SM2.riesgo_ram"))
        self.assertIn("[49.58 ; 81.46]", r)


class TestExplicar(unittest.TestCase):
    def setUp(self):
        self.ev = evidencia_de("SM1.interpretacion_pedido", "SM2.riesgo_ram")
        self.buena = "El riesgo de RAM de Notebook_G va de 49.58 a 81.46: es alto."
        self.mala = "El riesgo de RAM de Notebook_G es 65.52."

    def test_a_la_primera(self):
        llm = LLMFalso(self.buena)
        r = explicar("¿Cómo anda de RAM la G?", self.ev, llm)
        self.assertEqual((r["origen_respuesta"], len(r["intentos"])), ("llm", 1))
        self.assertEqual(verificar(r["respuesta"], self.ev), [])

    def test_agrega_la_advertencia_si_falta_y_no_inventa_otra_cosa(self):
        r = explicar("x", self.ev, LLMFalso(self.buena))
        self.assertTrue(r["respuesta"].startswith(self.buena))
        self.assertTrue(r["respuesta"].endswith(ADVERTENCIA))

    def test_regenera_con_los_problemas_y_despues_pasa(self):
        llm = LLMFalso(self.mala, self.buena)
        r = explicar("x", self.ev, llm)
        self.assertEqual((r["origen_respuesta"], len(r["intentos"])), ("llm", 2))
        self.assertTrue(r["intentos"][0]["problemas"])
        self.assertEqual(llm.llamadas[0]["variables"]["correcciones"], "")
        self.assertIn("(f)", llm.llamadas[1]["variables"]["correcciones"])
        self.assertIn(self.mala, llm.llamadas[1]["variables"]["correcciones"])

    def test_si_falla_dos_veces_sale_la_plantilla_fija(self):
        llm = LLMFalso(self.mala)
        r = explicar("x", self.ev, llm)
        self.assertEqual(r["origen_respuesta"], "plantilla_fija")
        self.assertEqual(len(r["intentos"]), 1 + explicador.MAX_REGENERACIONES)
        self.assertEqual(r["respuesta"], plantilla_fija(self.ev))

    def test_el_prompt_lleva_la_evidencia_y_el_texto(self):
        llm = LLMFalso(self.buena)
        explicar("¿Cómo anda de RAM la G?", self.ev, llm)
        llamada = llm.llamadas[0]
        self.assertEqual(llamada["usuario"], "¿Cómo anda de RAM la G?")
        self.assertIn("Notebook_G", llamada["variables"]["evidencia"])


class TestPrompt(unittest.TestCase):
    def setUp(self):
        self.prompt = explicador.RUTA_PROMPT.read_text(encoding="utf-8")

    def test_variables_y_sin_llaves_sueltas(self):
        self.assertEqual(sorted(re.findall(r"\{(\w*)\}", self.prompt)), ["correcciones", "evidencia"])
        self.assertEqual(self.prompt.count("{"), 2)

    def test_voseo_sin_tuteo(self):
        self.assertIn("voseo", self.prompt)
        self.assertFalse(re.search(r"\b(?:tienes|puedes|eres|quieres|debes|usa|di|escribe)\b", self.prompt.lower()))


class TestCompactar(unittest.TestCase):
    def test_junta_las_reglas_repetidas_y_acorta_las_listas(self):
        ev = {"reglas": [{"id": "FZ-R1", "fuerza": 1.0, "escenario": "peor"},
                         {"id": "FZ-R1", "fuerza": 0.5, "escenario": "mejor"}],
              "parametros": [{"nombre": f"p{i}"} for i in range(40)]}
        c = explicador._compactar(ev)
        self.assertEqual(c["reglas"], [{"id": "FZ-R1", "fuerza": [1.0, 0.5]}])
        self.assertEqual(len(c["parametros"]), explicador.MAX_FILAS_PROMPT + 1)
        self.assertEqual(c["parametros"][-1], {"_omitidas": 28})

    def test_la_traza_de_a_entra_en_el_contexto_del_modelo(self):
        ev = evidencia_de("SM1.interpretacion_pedido", "GRUPO.traza_reglas", "SM2.riesgo_ram")
        self.assertLess(len(str(explicador._compactar(ev))), 6500)


@unittest.skipUnless(os.getenv("PG3_TEST_LLM") == "1", "prueba con LLM: exportar PG3_TEST_LLM=1 (lenta)")
class ConLLM(unittest.TestCase):
    def test_respuestas_con_respaldo_en_la_evidencia(self):
        from asistente.llm import LLM
        llm = LLM()
        if not llm.salud().get("ok"):
            self.skipTest("Ollama no está disponible")
        for caso, nombres in CASOS_E2E.items():
            with self.subTest(caso):
                ev = evidencia_de(*nombres)
                r = explicar("Explicame el resultado.", ev, llm)
                print(f"\n[{caso}] origen={r['origen_respuesta']} intentos={len(r['intentos'])}")
                for i, intento in enumerate(r["intentos"], 1):
                    print(f"   intento {i}: {intento['problemas']}")
                self.assertIn(r["origen_respuesta"], ("llm", "plantilla_fija"))
                self.assertEqual(verificar(r["respuesta"], ev, MAX_PALABRAS_PLANTILLA), [])


if __name__ == "__main__":
    unittest.main()
