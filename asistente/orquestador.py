"""Orquestador (ARQUITECTURA §3): prevalida, planifica, despacha, arma la evidencia,
explica y escribe la traza. Es la capa de servicio principal del sistema.

Consulta libre (D-08): si el plan empieza con SM1.registrar_pedido o SM1.aclarar_pedido, primero Ollama
extrae del texto un JSON con usos, juegos y presupuesto (asistente/extractor.py); SM1 lo valida, lo guarda en
Neo4j y corre la inferencia para ese pedido; recién después se despachan las consultas de lectura sobre el
pedido nuevo. Si falta un dato imprescindible, se repregunta y la sesión guarda lo dicho («borrador»).

Despacho con LangChain: un mapa intención -> RunnableLambda(submódulo.ejecutar).
El LLM solo eligió la intención (ya validada por el router); qué Cypher se ejecuta lo
decide el submódulo. Sin agentes ni tool calling (RESTRICCIONES §5).
"""
import re
import time

from langchain_core.runnables import RunnableLambda

from asistente import config, explicador, extractor, router, traza
from asistente.contrato import (ADVERTENCIA, Aclaracion, ErrorGrafo, ErrorLLM, FueraDeAlcance, MENSAJE_ALCANCE,
                                MENSAJE_ERROR, MENSAJE_ERROR_GRAFO, MENSAJE_ERROR_LLM, submodulo_de)
from asistente.submodulos import grupo, sm1, sm2, sm3, sm4

MODULOS = {"SM1": sm1, "SM2": sm2, "SM3": sm3, "SM4": sm4, "GRUPO": grupo}
INTENCION_PEDIDO = "SM1.interpretacion_pedido"
# Una respuesta a «¿cuántas horas…?» o «¿para qué la vas a usar?» (sin signo de pregunta)
_RESPUESTA = re.compile(r"\d|\bhoras?\b|\bhs\b|todos los dias|a diario|a veces|siempre|principalmente|fines de semana"
                        r"|seguido|bastante|cada tanto|de vez en cuando|casi nunca|para (?:programar|jugar|trabajar|estudiar)")


def prevalidar(texto) -> str:
    """Rechaza entradas vacías, sin letras o de más de MAX_CARACTERES, sin recortar (D-07 §8)."""
    t = (texto or "").strip()
    if not t:
        raise Aclaracion("No recibí ninguna consulta. Escribí, por ejemplo: «¿Qué me recomendás para req_01?».")
    if len(t) > config.MAX_CARACTERES:
        raise Aclaracion(f"La consulta es muy larga ({len(t)} caracteres; el máximo es {config.MAX_CARACTERES}). "
                         "¿Podés resumirla en una sola pregunta?")
    if not re.search(r"[A-Za-zÁÉÍÓÚÜáéíóúüÑñ]", t):
        raise Aclaracion("No pude entender la consulta: no tiene palabras. ¿Podés reformularla?")
    return t


def _ms(desde: float) -> int:
    return int((time.perf_counter() - desde) * 1000)


class Orquestador:
    def __init__(self, grafo=None, llm=None, modulos: dict | None = None, planificar=None, explicar=None,
                 dir_trazas: str | None = None):
        if grafo is None:
            from asistente.grafo import Grafo
            grafo = Grafo()
        if llm is None:
            from asistente.llm import LLM
            llm = LLM()
        self.grafo, self.llm = grafo, llm
        self.planificar = planificar or router.planificar
        self.explicar = explicar or explicador.explicar
        self.dir_trazas = dir_trazas
        modulos = modulos or MODULOS
        # Mapa de despacho: agregar un submódulo es agregar su entrada acá.
        self.despachos: dict[str, RunnableLambda] = {
            sm: RunnableLambda(lambda c, m=modulo: m.ejecutar(c["intencion"], c["parametros"], self.grafo),
                               name=f"despacho_{sm}")
            for sm, modulo in modulos.items()
        }
        self.despachador = RunnableLambda(self._despachar, name="despachador")

    def _despachar(self, consulta: dict) -> dict:
        sm = submodulo_de(consulta["intencion"])
        if sm not in self.despachos:
            raise Aclaracion(f"El submódulo {sm} no está disponible.")
        return self.despachos[sm].invoke(consulta)

    # ------------------------------------------------------------------
    def _plan_de_sesion(self, texto: str, sesion: dict) -> dict | None:
        """Continuaciones que no pasan por el router (D-08): completar un pedido a medio cargar o responder
        la pregunta pendiente del pedido de la sesión. Son deterministas: no dependen de que el LLM las adivine."""
        if router.pedidos_en_texto(texto):
            return None
        if sesion.get("borrador"):
            completo = f"{sesion['borrador']} {texto}".strip()
            return {"requerimiento_id": None, "observaciones": ["completa el pedido en curso (repregunta anterior)"],
                    "evidencia": [], "consultas": [
                        {"intencion": "SM1.registrar_pedido", "parametros": {"texto": completo}},
                        {"intencion": "SM4.recomendar", "parametros": {}}]}
        if (sesion.get("preguntas_pendientes") and sesion.get("requerimiento_id") and "?" not in texto
                and not router.modelos_en_texto(texto) and (router.parece_pedido(texto) or _RESPUESTA.search(
                    router._sin_tildes(texto)))):
            return {"requerimiento_id": sesion["requerimiento_id"], "evidencia": [],
                    "observaciones": ["responde la pregunta pendiente del pedido de la sesión"],
                    "consultas": [{"intencion": "SM1.aclarar_pedido", "parametros": {"respuesta": texto}},
                                  {"intencion": "SM4.recomendar", "parametros": {}}]}
        return None

    def _escribir(self, c: dict, t: dict, sesion: dict, formulario: dict | None = None) -> dict:
        """registrar_pedido o aclarar_pedido: primero Ollama extrae el JSON del texto (asistente/extractor.py),
        después SM1 lo valida, lo guarda y corre la inferencia para ese pedido.

        `formulario`: el pedido que la persona armó o corrigió en la web, con el mismo esquema que el extractor.
        En ese caso no se llama a Ollama, pero SM1 lo valida igual contra el texto."""
        texto = c["parametros"].get("texto") or c["parametros"].get("respuesta") or ""
        t0 = time.perf_counter()
        if formulario is not None:
            extraido = formulario
            t["extraccion"] = {"texto": texto, "json": extraido, "ms": 0, "origen": "formulario"}
        else:
            vocabulario = self.grafo.vocabulario() if hasattr(self.grafo, "vocabulario") else {}
            extraido = extractor.extraer(texto, self.llm, vocabulario)
            t["extraccion"] = {"texto": texto, "json": extraido, "ms": _ms(t0)}
        try:
            salida = self.despachador.invoke({**c, "parametros": {**c["parametros"], "pedido": extraido}})
        except Aclaracion as e:
            if c["intencion"] == "SM1.registrar_pedido":   # falta un dato: se guarda lo dicho y se repregunta
                sesion["borrador"] = texto
                t["repregunta"] = e.mensaje
            raise
        sesion.pop("borrador", None)
        t["escritura"] = {"intencion": c["intencion"], "requerimiento_id": salida["evidencia"]["requerimiento_id"],
                          "ms": _ms(t0)}
        return salida

    # ------------------------------------------------------------------
    def consultar(self, texto: str, requerimiento_id: str | None = None, sesion: dict | None = None,
                  pedido: dict | None = None) -> dict:
        """`pedido`: armado con el formulario de la web («Armar pedido»). Registra un pedido nuevo sin pasar
        por el router ni por el extractor; la validación de SM1 y la inferencia de Neo4j son las mismas."""
        inicio = time.perf_counter()
        sesion = sesion if sesion is not None else {}
        if pedido is not None:
            requerimiento_id = None
            sesion.pop("requerimiento_id", None)
            sesion.pop("preguntas_pendientes", None)
            sesion.pop("borrador", None)
        if requerimiento_id:
            sesion["requerimiento_id"] = router.normalizar_pedido(requerimiento_id) or requerimiento_id
            sesion.pop("borrador", None)
        t = traza.nueva(texto)
        respuesta, origen, intento, req, submodulos = None, None, 0, sesion.get("requerimiento_id"), []
        pedido_nuevo, repregunta, entendido = False, None, None
        try:
            texto = prevalidar(texto)
            catalogo, pedidos = self.grafo.catalogo(), self.grafo.pedidos()
            if sesion.get("requerimiento_id") and sesion["requerimiento_id"] not in pedidos:
                raise Aclaracion(f"No existe el pedido {sesion['requerimiento_id']}. "
                                 f"Pedidos cargados: {', '.join(pedidos)}.")

            # 1. Plan (o la continuación de la sesión: completar un pedido o responder su pregunta)
            t0 = time.perf_counter()
            if pedido is not None:      # «Armar pedido» de la web: registrar y recomendar, sin router
                valido = {"requerimiento_id": None, "evidencia": [], "observaciones": ["pedido armado con el formulario"],
                          "consultas": [{"intencion": "SM1.registrar_pedido", "parametros": {"texto": texto}},
                                        {"intencion": "SM4.recomendar", "parametros": {}}]}
                t["plan"] = {"origen": "formulario", "consultas": valido["consultas"]}
            else:
                valido = self._plan_de_sesion(texto, sesion)
                if valido is not None:
                    t["plan"] = {"origen": "sesion", "consultas": valido["consultas"]}
            if valido is None:
                plan = self.planificar(texto, sesion, self.llm, catalogo=catalogo, pedidos=pedidos)
                t["plan"] = plan
                try:
                    valido = router.validar(plan, texto, sesion, catalogo, pedidos)
                finally:
                    t["duracion_ms"]["plan"] = _ms(t0)
            t["validacion"]["observaciones"] = valido["observaciones"]
            req = valido["requerimiento_id"]
            consultas = list(valido["consultas"])
            escritura = consultas.pop(0) if consultas and consultas[0]["intencion"] in router.ESCRITURA else None

            # 2. Escritura (D-08): alta o aclaración del pedido, con su inferencia. Solo estas dos escriben.
            t0 = time.perf_counter()
            evidencia: dict = {}
            if escritura is not None:
                c = {"intencion": escritura["intencion"],
                     "parametros": {**escritura["parametros"], "requerimiento_id": req}}
                salida = self._escribir(c, t, sesion, formulario=pedido)
                req = salida["evidencia"]["requerimiento_id"]
                sesion["requerimiento_id"] = req      # el pedido ya está guardado, aunque falle algo después
                pedido_nuevo = bool(salida["evidencia"].get("pedido_nuevo"))
                entendido = salida["evidencia"].get("entendido")
                t["consultas"].extend({"sm": "SM1", "intencion": c["intencion"], **q} for q in salida["consultas"])
                aviso = (f"Registré tu pedido como {req}." if pedido_nuevo else f"Actualicé el pedido {req}.")
                obs = salida["evidencia"].get("observaciones") or []
                if obs:
                    aviso += " Nota: " + "; ".join(obs) + "."
                evidencia.setdefault("SM1", {})[c["intencion"].split(".", 1)[1]] = {
                    **salida["evidencia"], "aviso_validacion": aviso}
                submodulos.append("SM1")

            # 3. L1 siempre que haya pedido (la evidencia común lo lleva en "pedido")
            if req and not any(c["intencion"] == INTENCION_PEDIDO for c in consultas):
                consultas.insert(0, {"intencion": INTENCION_PEDIDO, "parametros": {}})

            # 4. Despacho y evidencia común
            for c in consultas:
                c = {"intencion": c["intencion"], "parametros": {**c["parametros"], "requerimiento_id": req}}
                tc = time.perf_counter()
                sm, corta = c["intencion"].split(".", 1)
                try:
                    salida = self.despachador.invoke(c)
                except Aclaracion as e:
                    if escritura is None:
                        raise
                    # El pedido ya quedó guardado: lo que no se pudo responder se cuenta, no corta la respuesta
                    salida = {"consultas": [], "evidencia": {"aviso_validacion": e.mensaje}}
                registros = [{"sm": sm, "intencion": c["intencion"], **q} for q in salida["consultas"]]
                if not registros:  # p. ej., un stub sin Cypher: igual queda el submódulo ejecutado
                    registros = [{"sm": sm, "intencion": c["intencion"], "nombre": "(sin Cypher)"}]
                registros[-1]["ms"] = _ms(tc)  # duración del submódulo, en la última consulta que hizo
                t["consultas"].extend(registros)
                if c["intencion"] == INTENCION_PEDIDO:
                    evidencia["pedido"] = salida["evidencia"]
                else:
                    previa = evidencia.setdefault(sm, {}).get(corta)
                    if previa and isinstance(previa.get("notebooks"), list) and isinstance(salida["evidencia"].get("notebooks"), list):
                        # la misma intención para otro modelo (p. ej., explicar la M y la G): una sola evidencia, sin pisar la anterior
                        salida["evidencia"] = {**previa, "notebooks": previa["notebooks"] + salida["evidencia"]["notebooks"]}
                    evidencia[sm][corta] = salida["evidencia"]
                if sm not in submodulos:
                    submodulos.append(sm)
            evidencia["advertencia"] = ADVERTENCIA       # siempre que se consulta el grafo (D-07 §7)
            t["duracion_ms"]["consultas"] = _ms(t0)
            t["evidencia"] = evidencia

            # 5. Explicación
            t0 = time.perf_counter()
            exp = self.explicar(texto, evidencia, self.llm)
            t["duracion_ms"]["explicacion"] = _ms(t0)
            respuesta, origen = exp["respuesta"], exp["origen_respuesta"]
            t["intentos"] = exp.get("intentos", [])
            intento = len(t["intentos"]) or 1
            if req:
                sesion["requerimiento_id"] = req
                sesion["preguntas_pendientes"] = (evidencia.get("pedido") or {}).get("preguntas_pendientes") or []
        except Aclaracion as e:
            respuesta, origen = e.mensaje, "validacion"
            t["validacion"]["aclaracion"] = e.mensaje
            repregunta = t.get("repregunta")
        except FueraDeAlcance:
            respuesta, origen = MENSAJE_ALCANCE, "fuera_de_alcance"
        except ErrorGrafo as e:
            respuesta, origen, t["error"] = MENSAJE_ERROR_GRAFO, "error", str(e)
        except ErrorLLM as e:
            respuesta, origen, t["error"] = MENSAJE_ERROR_LLM, "error", str(e)
        except Exception as e:  # nunca un traceback al usuario; queda en la traza
            respuesta, origen, t["error"] = MENSAJE_ERROR, "error", f"{type(e).__name__}: {e}"
        t["respuesta"], t["origen_respuesta"] = respuesta, origen
        t["segundos"] = round(time.perf_counter() - inicio, 3)
        try:
            traza.escribir(t, self.dir_trazas)
        except OSError as e:
            t["error"] = (t["error"] or "") + f" | no se pudo escribir la traza: {e}"
        return {"respuesta": respuesta, "requerimiento_id": req, "submodulos_consultados": submodulos,
                "origen_respuesta": origen, "intento": intento, "traza": t,
                "pedido_nuevo": pedido_nuevo, "repregunta": repregunta, "pedido": entendido}

    def salud(self) -> dict:
        neo, oll = self.grafo.salud(), self.llm.salud()
        return {"ok": bool(neo.get("ok") and oll.get("ok")), "neo4j": neo, "ollama": oll,
                "modelo": getattr(self.llm, "modelo", None)}
