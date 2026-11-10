"""Orquestador (ARQUITECTURA §3): prevalida, planifica, despacha, arma la evidencia,
explica y escribe la traza. Es la capa de servicio principal del sistema.

Despacho con LangChain: un mapa intención -> RunnableLambda(submódulo.ejecutar).
El LLM solo eligió la intención (ya validada por el router); qué Cypher se ejecuta lo
decide el submódulo. Sin agentes ni tool calling (RESTRICCIONES §5).
"""
import re
import time

from langchain_core.runnables import RunnableLambda

from asistente import config, explicador, router, traza
from asistente.contrato import (ADVERTENCIA, Aclaracion, ErrorGrafo, ErrorLLM, FueraDeAlcance, MENSAJE_ALCANCE,
                                MENSAJE_ERROR, MENSAJE_ERROR_GRAFO, MENSAJE_ERROR_LLM, submodulo_de)
from asistente.submodulos import grupo, sm1, sm2, sm3, sm4

MODULOS = {"SM1": sm1, "SM2": sm2, "SM3": sm3, "SM4": sm4, "GRUPO": grupo}
INTENCION_PEDIDO = "SM1.interpretacion_pedido"


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
    def consultar(self, texto: str, requerimiento_id: str | None = None, sesion: dict | None = None) -> dict:
        inicio = time.perf_counter()
        sesion = sesion if sesion is not None else {}
        if requerimiento_id:
            sesion["requerimiento_id"] = router.normalizar_pedido(requerimiento_id) or requerimiento_id
        t = traza.nueva(texto)
        respuesta, origen, intento, req, submodulos = None, None, 0, sesion.get("requerimiento_id"), []
        try:
            texto = prevalidar(texto)
            catalogo, pedidos = self.grafo.catalogo(), self.grafo.pedidos()
            if sesion.get("requerimiento_id") and sesion["requerimiento_id"] not in pedidos:
                raise Aclaracion(f"No existe el pedido {sesion['requerimiento_id']}. "
                                 f"Pedidos cargados: {', '.join(pedidos)}.")

            # 1. Plan
            t0 = time.perf_counter()
            plan = self.planificar(texto, sesion, self.llm, catalogo=catalogo, pedidos=pedidos)
            t["plan"] = plan
            try:
                valido = router.validar(plan, texto, sesion, catalogo, pedidos)
            finally:
                t["duracion_ms"]["plan"] = _ms(t0)
            t["validacion"]["observaciones"] = valido["observaciones"]
            req = valido["requerimiento_id"]

            # 2. L1 siempre que haya pedido (la evidencia común lo lleva en "pedido")
            consultas = list(valido["consultas"])
            if req and not any(c["intencion"] == INTENCION_PEDIDO for c in consultas):
                consultas.insert(0, {"intencion": INTENCION_PEDIDO, "parametros": {}})

            # 3. Despacho y evidencia común
            t0 = time.perf_counter()
            evidencia: dict = {}
            for c in consultas:
                c = {"intencion": c["intencion"], "parametros": {**c["parametros"], "requerimiento_id": req}}
                tc = time.perf_counter()
                salida = self.despachador.invoke(c)
                sm, corta = c["intencion"].split(".", 1)
                registros = [{"sm": sm, "intencion": c["intencion"], **q} for q in salida["consultas"]]
                if not registros:  # p. ej., un stub sin Cypher: igual queda el submódulo ejecutado
                    registros = [{"sm": sm, "intencion": c["intencion"], "nombre": "(sin Cypher)"}]
                registros[-1]["ms"] = _ms(tc)  # duración del submódulo, en la última consulta que hizo
                t["consultas"].extend(registros)
                if c["intencion"] == INTENCION_PEDIDO:
                    evidencia["pedido"] = salida["evidencia"]
                else:
                    evidencia.setdefault(sm, {})[corta] = salida["evidencia"]
                if sm not in submodulos:
                    submodulos.append(sm)
            evidencia["advertencia"] = ADVERTENCIA       # siempre que se consulta el grafo (D-07 §7)
            t["duracion_ms"]["consultas"] = _ms(t0)
            t["evidencia"] = evidencia

            # 4. Explicación
            t0 = time.perf_counter()
            exp = self.explicar(texto, evidencia, self.llm)
            t["duracion_ms"]["explicacion"] = _ms(t0)
            respuesta, origen = exp["respuesta"], exp["origen_respuesta"]
            t["intentos"] = exp.get("intentos", [])
            intento = len(t["intentos"]) or 1
            if req:
                sesion["requerimiento_id"] = req
        except Aclaracion as e:
            respuesta, origen = e.mensaje, "validacion"
            t["validacion"]["aclaracion"] = e.mensaje
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
                "origen_respuesta": origen, "intento": intento, "traza": t}

    def salud(self) -> dict:
        neo, oll = self.grafo.salud(), self.llm.salud()
        return {"ok": bool(neo.get("ok") and oll.get("ok")), "neo4j": neo, "ollama": oll,
                "modelo": getattr(self.llm, "modelo", None)}
