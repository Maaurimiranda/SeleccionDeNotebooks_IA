"""Asistente SM3 — Evaluación Gráfica y de Movilidad (PI4, patrón sándwich).

Usuario → [1] LLM extracción (JSON) → [2] router + guardrails → [3] Neo4j (Cypher) → [4] LLM explicación.

Especificación completa: SPEC.md. Este archivo se organiza en las secciones del §4 de la spec.
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import sys
import time
from operator import itemgetter
from pathlib import Path
from typing import Any, Literal

import httpx
from dotenv import load_dotenv
from langchain_core.language_models import BaseChatModel
from langchain_core.exceptions import OutputParserException
from langchain_core.messages import SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable, RunnableBranch, RunnableLambda, RunnableParallel
from neo4j import Driver, GraphDatabase
from neo4j.exceptions import AuthError, ServiceUnavailable, SessionExpired
from ollama import ResponseError as OllamaResponseError
from pydantic import BaseModel, Field, ValidationError
from rich.console import Console, Group
from rich.json import JSON
from rich.markdown import Markdown
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text

# =============================================================================
# 1. CONFIGURACIÓN
# =============================================================================
load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "")
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")
LLM_MODEL = os.getenv("LLM_MODEL", "qwen2.5:3b")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

LIMITE_RESULTADOS = 5   # filas máximas que recibe el explicador (SPEC §8)
SRGB_DISENO = 95        # perfil DIS del grafo: "sRGB >= 95 %" (SPEC §5)
DIR_PROMPTS = Path(__file__).resolve().parent / "prompts"


# =============================================================================
# 2. ESQUEMAS (contrato del extractor, SPEC §5)
# =============================================================================
# El mismo modelo genera el JSON Schema que Ollama usa para restringir la salida
# (constrained decoding) y valida la respuesta. Una sola fuente de verdad.

class Extraccion(BaseModel):
    """Parámetros técnicos extraídos de la consulta del usuario."""

    intencion: Literal["grafica", "movilidad", "mixta", "modelo", "fuera_de_alcance"]
    modelo_especifico: str | None = None
    tipo_gpu: Literal["dedicada", "integrada"] | None = None
    gama_min: int | None = Field(None, ge=1, le=5)
    peso_max_kg: float | None = None
    bateria_min_horas: float | None = None
    pantalla_exigente: bool = False
    consulta_incompleta_o_absurda: bool = False
    motivo_absurdo: str | None = None


# =============================================================================
# 3. FÁBRICA DE LLM (D11: Factory + Adapter)
# =============================================================================
# Cada Chat* de LangChain adapta un proveedor a la interfaz común BaseChatModel.
# Este es el único punto que cambia para sumar otro proveedor (SPEC §14).

TEMPERATURAS = {"extraccion": 0.0, "explicacion": 0.3}


def crear_llm(rol: Literal["extraccion", "explicacion"]) -> BaseChatModel:
    temperatura = TEMPERATURAS[rol]
    match LLM_PROVIDER:
        case "ollama":
            from langchain_ollama import ChatOllama
            # keep_alive: mantiene el modelo en RAM entre consultas (por defecto Ollama lo
            # descarga a los 5 min y la siguiente consulta paga ~40 s de carga en frío).
            return ChatOllama(model=LLM_MODEL, base_url=OLLAMA_HOST, temperature=temperatura,
                              keep_alive="30m")
        case _:
            raise ValueError(f"Proveedor de LLM no soportado: {LLM_PROVIDER!r} (disponibles: 'ollama')")


def leer_prompt(nombre: str) -> str:
    return (DIR_PROMPTS / f"{nombre}.txt").read_text(encoding="utf-8")


# =============================================================================
# 4. CHAIN DE EXTRACCIÓN (paso 1 del sándwich)
# =============================================================================
# El system prompt va como SystemMessage (no como plantilla) porque sus ejemplos
# tienen llaves JSON que ChatPromptTemplate tomaría como variables.

def crear_chain_extraccion() -> Runnable:
    """LLM (con JSON restringido por esquema) seguido de la normalización determinista.

    Entrada: {"pregunta": str, "catalogo": str}. Salida: Extraccion normalizada.
    """
    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content=leer_prompt("extraccion")),
        ("human", "Modelos del catálogo: {catalogo}\n\nConsulta del usuario: {pregunta}"),
    ])
    llm = crear_llm("extraccion").with_structured_output(Extraccion, method="json_schema")
    llm_con_reintento = (prompt | llm).with_retry(stop_after_attempt=2)
    return RunnableParallel(extraccion=llm_con_reintento, pregunta=itemgetter("pregunta")) | \
        RunnableLambda(lambda d: normalizar_extraccion(d["extraccion"], d["pregunta"]))


# Un modelo nombrado en el texto: "Notebook_X", "notebook x", "la notebook-x".
_RE_MODELO = re.compile(r"\bnotebook[\s_-]*([a-z])\b", re.IGNORECASE)


def modelo_mencionado(pregunta: str) -> str | None:
    """Detecta de forma determinista un modelo escrito en la pregunta."""
    m = _RE_MODELO.search(pregunta)
    return f"Notebook_{m.group(1).upper()}" if m else None


def normalizar_extraccion(ext: Extraccion, pregunta: str) -> Extraccion:
    """Corrige con reglas fijas los errores estructurales del LLM (SPEC §5).

    - El modelo lo decide el texto, no el LLM: si hay "notebook <letra>" en la pregunta,
      ese es el modelo y la intención es "modelo" (el LLM tiende a clasificar por el tema,
      p. ej. "batería" → movilidad). Si el LLM devolvió un modelo que no aparece en el texto,
      se descarta (evita que "elija" uno del catálogo que recibió como contexto).
    """
    mencionado = modelo_mencionado(pregunta)
    cambios: dict[str, Any] = {"modelo_especifico": mencionado}
    if mencionado:
        cambios["intencion"] = "modelo"
    elif ext.intencion == "modelo":
        # Pidió "modelo" sin nombrar ninguno: no hay a quién consultar.
        cambios |= {"consulta_incompleta_o_absurda": True,
                    "motivo_absurdo": ext.motivo_absurdo or "No indicaste ningún criterio de gráfica o movilidad, ni un modelo del catálogo."}
    return ext.model_copy(update=cambios)


# =============================================================================
# 5. ROUTER Y GUARDRAILS (paso 2 del sándwich — Python puro, sin LLM)
# =============================================================================
# Decide si se consulta Neo4j y con qué parámetros, o qué aclaración devolver.
# Es determinista: un absurdo se detecta aunque el LLM no lo haya marcado (D9).

# Rangos físicamente posibles (SPEC §6). Fuera de ellos la consulta es absurda.
RANGO_PESO_KG = (0.5, 5.0)
RANGO_BATERIA_H = (0.0, 30.0)   # (mín excluido, máx incluido]

MENSAJE_FUERA_DE_ALCANCE = (
    "Esa consulta está fuera de mi alcance: yo evalúo la parte gráfica (GPU y pantalla) "
    "y la movilidad (peso y batería) de las notebooks. Las preguntas sobre CPU, RAM o "
    "almacenamiento las responde el submódulo SM2 (rendimiento)."
)

EJEMPLOS_REFORMULACION = (
    "Por ejemplo, podés preguntarme:\n"
    "  • \"Quiero una notebook gamer que pese menos de 2 kg\"\n"
    "  • \"Necesito una liviana con al menos 8 horas de batería\"\n"
    "  • \"¿Qué tal es la Notebook_X?\""
)


class Decision(BaseModel):
    """Resultado del router: qué hacer con la consulta."""

    tipo: Literal["consulta_unificada", "consulta_modelo", "aclaracion", "fuera_de_alcance"]
    orden: Literal["grafica", "movilidad", "mixta"] | None = None
    filtros: dict[str, Any] = Field(default_factory=dict)
    modelo: str | None = None
    mensaje: str | None = None              # respuesta final cuando no se consulta Neo4j
    criterios: list[str] = Field(default_factory=list)  # "criterios aplicados", para SP2 y la CLI

    @property
    def requiere_neo4j(self) -> bool:
        return self.tipo in ("consulta_unificada", "consulta_modelo")


def validar_rangos(ext: Extraccion) -> list[str]:
    """Guardrails deterministas: devuelve los valores imposibles encontrados."""
    problemas = []
    if ext.peso_max_kg is not None and not RANGO_PESO_KG[0] <= ext.peso_max_kg <= RANGO_PESO_KG[1]:
        problemas.append(
            f"un peso máximo de {ext.peso_max_kg:g} kg (las notebooks pesan entre "
            f"{RANGO_PESO_KG[0]:g} y {RANGO_PESO_KG[1]:g} kg)")
    if ext.bateria_min_horas is not None and not RANGO_BATERIA_H[0] < ext.bateria_min_horas <= RANGO_BATERIA_H[1]:
        problemas.append(
            f"una batería de al menos {ext.bateria_min_horas:g} h (el máximo realista es "
            f"{RANGO_BATERIA_H[1]:g} h)")
    return problemas


def filtros_de(ext: Extraccion) -> tuple[dict[str, Any], list[str]]:
    """Traduce la extracción a parámetros Cypher y a criterios legibles."""
    filtros: dict[str, Any] = {}
    criterios: list[str] = []
    if ext.tipo_gpu is not None:
        filtros["dedicada"] = ext.tipo_gpu == "dedicada"
        criterios.append(f"GPU {ext.tipo_gpu}")
    if ext.gama_min is not None:
        filtros["gama_min"] = ext.gama_min
        criterios.append(f"gama de GPU ≥ {ext.gama_min} (de 5)")
    if ext.peso_max_kg is not None:
        filtros["peso_max"] = ext.peso_max_kg
        criterios.append(f"peso ≤ {ext.peso_max_kg:g} kg")
    if ext.bateria_min_horas is not None:
        filtros["bateria_min"] = ext.bateria_min_horas
        criterios.append(f"batería ≥ {ext.bateria_min_horas:g} h")
    if ext.pantalla_exigente:
        filtros["srgb_min"] = SRGB_DISENO
        criterios.append(f"pantalla con sRGB ≥ {SRGB_DISENO} % (perfil DIS)")
    return filtros, criterios


def resolver_modelo(nombre: str, catalogo: list[str]) -> str | None:
    """Convierte el nombre a su forma canónica del catálogo, sin distinguir mayúsculas."""
    por_clave = {m.lower(): m for m in catalogo}
    return por_clave.get(nombre.strip().lower().replace(" ", "_"))


def rutear(ext: Extraccion, catalogo: list[str]) -> Decision:
    """Router del SPEC §6. El orden de las reglas importa."""
    # 1. Fuera de alcance → derivación fija a SM2.
    if ext.intencion == "fuera_de_alcance":
        return Decision(tipo="fuera_de_alcance", mensaje=MENSAJE_FUERA_DE_ALCANCE)

    # 2. Guardrails de rangos: no dependen de que el LLM lo haya marcado.
    problemas = validar_rangos(ext)
    if problemas:
        return Decision(tipo="aclaracion", mensaje=(
            "No puedo buscar con " + " ni con ".join(problemas) + ". "
            "¿Podés indicarme valores realistas?\n" + EJEMPLOS_REFORMULACION))

    # 3. Consulta por modelo (antes que "incompleta": nombrar un modelo ya es un criterio).
    if ext.intencion == "modelo" and ext.modelo_especifico:
        canonico = resolver_modelo(ext.modelo_especifico, catalogo)
        if canonico is None:
            return Decision(tipo="aclaracion", mensaje=(
                f"No encuentro \"{ext.modelo_especifico}\" en el catálogo. "
                f"Los modelos disponibles son: {', '.join(catalogo)}."))
        return Decision(tipo="consulta_modelo", modelo=canonico, criterios=[f"modelo {canonico}"])

    # 4. Incompleta o absurda según el LLM, o sin ningún filtro utilizable.
    filtros, criterios = filtros_de(ext)
    if ext.consulta_incompleta_o_absurda or not filtros:
        motivo = ext.motivo_absurdo or "No encontré ningún criterio de gráfica ni de movilidad en la consulta."
        return Decision(tipo="aclaracion", mensaje=f"{motivo}\n{EJEMPLOS_REFORMULACION}")

    # 5. Búsqueda en el catálogo con la consulta unificada.
    orden = ext.intencion if ext.intencion in ("grafica", "movilidad", "mixta") else "mixta"
    return Decision(tipo="consulta_unificada", orden=orden, filtros=filtros, criterios=criterios)


def responder_aclaracion(decision: Decision) -> str:
    """Respuesta final cuando no se consulta Neo4j (ni se llama al explicador)."""
    return decision.mensaje or EJEMPLOS_REFORMULACION


# =============================================================================
# 6. CONSULTAS CYPHER Y ACCESO A NEO4J (paso 3 del sándwich)
# =============================================================================
# Los textos del usuario NUNCA se interpolan en el Cypher: todo va por parámetros ($x).
# La única parte variable es el ORDER BY, que sale de la lista blanca ORDENES.

_MATCH_UNIFICADA = """
MATCH (n:Notebook)-[:POSEE]->(g:GPU)-[:ES_DE_GAMA]->(gg:GamaGPU)
MATCH (n)-[:POSEE]->(p:Pantalla)
MATCH (n)-[:POSEE]->(b:Bateria)
WHERE ($dedicada    IS NULL OR g.dedicada = $dedicada)
  AND ($gama_min    IS NULL OR gg.indice >= $gama_min)
  AND ($peso_max    IS NULL OR n.peso_kg <= $peso_max)
  AND ($bateria_min IS NULL OR b.autonomia_usada_h >= $bateria_min)
  AND ($srgb_min    IS NULL OR p.srgb >= $srgb_min)
"""

_MATCH_MODELO = """
MATCH (n:Notebook {modelo: $modelo})-[:POSEE]->(g:GPU)-[:ES_DE_GAMA]->(gg:GamaGPU)
MATCH (n)-[:POSEE]->(p:Pantalla)
MATCH (n)-[:POSEE]->(b:Bateria)
"""

# Bloque común (SPEC §7.1): se agrega por etapas para evitar productos cartesianos.
# collect(CASE WHEN x IS NULL THEN null ...) devuelve [] en lugar de [{...: null}].
_BLOQUE_COMUN = """
// (1) Movilidad: reglas GM-RD1..RD3 activadas desde la notebook (absolutas)
OPTIONAL MATCH (n)-[am:ACTIVA]->(rm:Regla {submodulo: 'SM3'})
WITH n, g, gg, p, b,
     collect(CASE WHEN rm IS NULL THEN null ELSE
       {regla: rm.id, antecedente: rm.antecedente, consecuente: rm.consecuente,
        fuerza: am.fuerza, validacion: rm.estado_validacion} END) AS reglas_movilidad
// (2) Gráfica: una entrada por evaluación (requerimiento x notebook)
OPTIONAL MATCH (c:Requerimiento)-[:EVALUA]->(ev:Evaluacion)-[:SOBRE]->(n)
OPTIONAL MATCH (c)-[:TIENE_PERFIL_DOMINANTE]->(pf:Perfil)
OPTIONAL MATCH (ev)-[ag:ACTIVA]->(rg:Regla {submodulo: 'SM3'})
WITH n, g, gg, p, b, reglas_movilidad, c, ev, pf,
     collect(CASE WHEN rg IS NULL THEN null ELSE
       {regla: rg.id, fuerza: ag.fuerza,
        texto: coalesce(rg.enunciado, rg.antecedente + ' -> ' + rg.consecuente),
        validacion: rg.estado_validacion} END) AS reglas_ev
OPTIONAL MATCH (ev)-[:GENERA]->(al:Alerta {submodulo_origen: 'SM3'})
WITH n, g, gg, p, b, reglas_movilidad, c, ev, pf, reglas_ev,
     collect(CASE WHEN al IS NULL THEN null ELSE
       {tipo: al.tipo, regla: al.regla_origen, mensaje: al.mensaje} END) AS alertas_ev
WITH n, g, gg, p, b, reglas_movilidad,
     collect(CASE WHEN ev IS NULL THEN null ELSE
       {requerimiento: c.id, perfil: ev.perfil, perfil_gama_gpu_min: pf.gama_gpu_min,
        grado_gpu: ev.grado_gpu, margen_gama: ev.margen_gama,
        grado_pantalla: ev.grado_pantalla, adecuacion_grafica: ev.adecuacion_grafica,
        reglas: reglas_ev, alertas: alertas_ev} END) AS evaluaciones
"""

_RETURN_COMUN = """
RETURN n.modelo AS modelo, n.precio_usd AS precio, n.peso_kg AS peso,
       g.dedicada AS gpu_dedicada, gg.nombre AS gpu_gama, gg.indice AS gpu_gama_indice,
       g.vram_gb AS vram_gb, g.tgp_w AS tgp_watts, g.tgp_max_w AS tgp_max_watts,
       g.potencia_relativa AS potencia_relativa,
       p.resolucion AS resolucion, p.refresco_hz AS refresco_hz, p.srgb AS srgb,
       b.autonomia_usada_h AS bateria_horas, b.tipo_dato AS fiabilidad_bateria,
       b.fuente AS fuente_bateria,
       n.adecuacion_movilidad AS adecuacion_movilidad,
       n.movilidad_etiqueta AS movilidad_etiqueta,
       reglas_movilidad, evaluaciones"""

CYPHER_UNIFICADA = (
    _MATCH_UNIFICADA + _BLOQUE_COMUN + _RETURN_COMUN
    + "\nORDER BY __ORDEN__\nLIMIT $limite"
)

CYPHER_MODELO = (
    _MATCH_MODELO + _BLOQUE_COMUN + _RETURN_COMUN
    + ",\n       b.autonomia_medida_h AS bateria_medida,"
    + " b.autonomia_declarada_h AS bateria_declarada"
)

# Lista blanca de ordenamientos (SPEC §6). Solo datos absolutos de la ficha (D14).
# coalesce(...) manda los null al final: en Neo4j los null van primero en un DESC.
ORDENES: dict[str, str] = {
    "grafica": "gpu_gama_indice DESC, coalesce(potencia_relativa, 0) DESC, srgb DESC, precio ASC",
    "movilidad": "coalesce(adecuacion_movilidad, -1) DESC, peso ASC",
    "mixta": "gpu_gama_indice DESC, coalesce(adecuacion_movilidad, -1) DESC",
}

CYPHER_CATALOGO = "MATCH (n:Notebook) RETURN n.modelo AS modelo ORDER BY modelo"
CYPHER_PERFILES = """
MATCH (pf:Perfil)
RETURN pf.codigo AS perfil, pf.gama_gpu_min AS gama_gpu_min, pf.fundamento AS fundamento
ORDER BY perfil"""

FILTROS_UNIFICADA = ("dedicada", "gama_min", "peso_max", "bateria_min", "srgb_min")


def cypher_unificada(orden: str) -> str:
    """Devuelve la consulta unificada con el ORDER BY de la lista blanca.

    Usa str.replace y no str.format: el Cypher tiene llaves de mapas ({regla: ...}).
    """
    if orden not in ORDENES:
        raise ValueError(f"Orden no permitido: {orden!r}. Opciones: {sorted(ORDENES)}")
    return CYPHER_UNIFICADA.replace("__ORDEN__", ORDENES[orden])


class BaseConocimiento:
    """Acceso a la base de conocimiento PG2 en Neo4j (un driver reutilizable)."""

    def __init__(self, uri: str = NEO4J_URI, usuario: str = NEO4J_USERNAME,
                 clave: str = NEO4J_PASSWORD) -> None:
        if not uri:
            raise RuntimeError("Falta NEO4J_URI en el .env (ver .env.example).")
        self._driver: Driver = GraphDatabase.driver(uri, auth=(usuario, clave))
        self._driver.verify_connectivity()
        self.catalogo: list[str] = []
        self.perfiles: dict[str, dict[str, Any]] = {}

    def cerrar(self) -> None:
        self._driver.close()

    def __enter__(self) -> BaseConocimiento:
        return self

    def __exit__(self, *_: object) -> None:
        self.cerrar()

    # -- contexto inicial (SPEC §9) ------------------------------------------
    def cargar_contexto(self) -> None:
        """Carga una sola vez el catálogo (para SP1) y el glosario de perfiles (para SP2)."""
        self.catalogo = [f["modelo"] for f in self.ejecutar(CYPHER_CATALOGO)]
        self.perfiles = {f["perfil"]: f for f in self.ejecutar(CYPHER_PERFILES)}

    # -- ejecución --------------------------------------------------------------
    def ejecutar(self, cypher: str, parametros: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """Ejecuta Cypher parametrizado y devuelve las filas como diccionarios."""
        records, _, _ = self._driver.execute_query(cypher, parametros or {})
        return [r.data() for r in records]

    def buscar(self, orden: str, limite: int = LIMITE_RESULTADOS,
               **filtros: Any) -> tuple[str, dict[str, Any], list[dict[str, Any]]]:
        """Consulta unificada (SPEC §7.1). Devuelve (cypher, parámetros, filas) para la traza."""
        desconocidos = set(filtros) - set(FILTROS_UNIFICADA)
        if desconocidos:
            raise ValueError(f"Filtros desconocidos: {sorted(desconocidos)}")
        parametros = {k: filtros.get(k) for k in FILTROS_UNIFICADA} | {"limite": limite}
        cypher = cypher_unificada(orden)
        return cypher, parametros, _ordenar_reglas(self.ejecutar(cypher, parametros))

    def ficha(self, modelo: str) -> tuple[str, dict[str, Any], list[dict[str, Any]]]:
        """Consulta por modelo (SPEC §7.2). `modelo` debe venir ya normalizado al catálogo."""
        parametros = {"modelo": modelo}
        return CYPHER_MODELO, parametros, _ordenar_reglas(self.ejecutar(CYPHER_MODELO, parametros))


def _ordenar_reglas(filas: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """collect() no garantiza orden: deja las reglas de mayor fuerza primero."""
    def clave(r: dict[str, Any]) -> float:
        return -(r.get("fuerza") or 0.0)

    for f in filas:
        f["reglas_movilidad"].sort(key=clave)
        for ev in f["evaluaciones"]:
            ev["reglas"].sort(key=clave)
    return filas


# =============================================================================
# 7. CHAIN DE EXPLICACIÓN (paso 4 del sándwich)
# =============================================================================
# Python compacta las filas en texto legible ANTES del LLM: solo formatea y redondea
# datos del grafo, no interpreta. Las filas crudas quedan en la traza y en la tabla
# de evidencias. Con un modelo de 3B, menos contexto = menos errores y menos latencia.

def _num(x: float | None, nd: int = 2) -> str:
    return "no disponible" if x is None else f"{round(x, nd):g}"


def _regla(r: dict[str, Any]) -> str:
    consecuente = r.get("consecuente") or (r.get("texto") or "").split("->")[-1].strip()
    fuerza = f" (fuerza {_num(r['fuerza'], 3)})" if r.get("fuerza") is not None else ""
    return f"{r['regla']} → {consecuente}{fuerza}"


def compactar_fila(f: dict[str, Any], perfiles: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Versión legible de una fila de Neo4j para el explicador (sin agregar información)."""
    if f["gpu_dedicada"]:
        tgp = (f"TGP {f['tgp_watts']} W de {f['tgp_max_watts']} W máx "
               f"({round(100 * f['potencia_relativa'])} % de potencia)"
               if f["potencia_relativa"] is not None else "TGP no informado")
        gpu = f"dedicada, gama '{f['gpu_gama']}' ({f['gpu_gama_indice']} de 5), {f['vram_gb']} GB VRAM, {tgp}"
    else:
        gpu = f"integrada, gama '{f['gpu_gama']}' ({f['gpu_gama_indice']} de 5)"

    match f["fiabilidad_bateria"]:
        case "medida":
            bateria = (f"{_num(f['bateria_horas'])} h, dato MEDIDO en pruebas independientes "
                       f"({f['fuente_bateria']}), no declarado por el fabricante")
        case "estimada":
            bateria = (f"{_num(f['bateria_horas'])} h, dato ESTIMADO por la regla GM-R12 "
                       f"(70 % de las horas declaradas por el fabricante)")
        case _:
            bateria = "NO DISPONIBLE: no hay autonomía medida ni declarada"

    movilidad = (f"{f['movilidad_etiqueta']} (grado {_num(f['adecuacion_movilidad'], 3)} de 1)"
                 if f["adecuacion_movilidad"] is not None
                 else "NO EVALUABLE: falta el dato de autonomía")

    # Frases ya armadas: el modelo tiende a copiarlas tal cual y así no pierde el perfil.
    evaluaciones = []
    for ev in f["evaluaciones"]:
        frase = (f"Para el perfil {ev['perfil']} del requerimiento {ev['requerimiento']} "
                 f"(que exige gama de GPU ≥ {ev['perfil_gama_gpu_min']}): grado de GPU {ev['grado_gpu']}, "
                 f"margen de gama '{ev['margen_gama']}', adecuación gráfica {ev['adecuacion_grafica']}")
        if ev["reglas"]:
            frase += ". Reglas activadas: " + "; ".join(_regla(r) for r in ev["reglas"])
        evaluaciones.append(frase)
    alertas = [f"{a['tipo']} ({a['regla']}): {a['mensaje']}" for ev in f["evaluaciones"] for a in ev["alertas"]]

    return {
        "modelo": f["modelo"],
        "precio_usd": f["precio"],
        "peso_kg": f["peso"],
        "gpu": gpu,
        "pantalla": f"{f['resolucion']}, {f['refresco_hz']} Hz, sRGB {f['srgb']} %",
        "bateria": bateria,
        "movilidad": movilidad,
        "reglas_de_movilidad": [_regla(r) for r in f["reglas_movilidad"][:2]],
        "evaluaciones_por_perfil": evaluaciones,
        "alertas": alertas or "ninguna",
    }


def reglas_sin_validar(filas: list[dict[str, Any]]) -> bool:
    reglas = [r for f in filas for r in f["reglas_movilidad"]]
    reglas += [r for f in filas for ev in f["evaluaciones"] for r in ev["reglas"]]
    return any(r.get("validacion") == "sin validar" for r in reglas)


PLANTILLA_EXPLICACION = """PREGUNTA DEL USUARIO: {pregunta}

CRITERIOS APLICADOS EN LA BÚSQUEDA: {criterios}

RESULTADOS DE NEO4J ({cantidad} notebook(s), ordenados de mejor a peor según los criterios):
{datos}

REGLAS SIN VALIDAR POR EL TÉCNICO: {sin_validar}"""


def entrada_explicacion(pregunta: str, criterios: list[str], filas: list[dict[str, Any]],
                        perfiles: dict[str, dict[str, Any]]) -> dict[str, str]:
    """Variables del mensaje humano de SP2."""
    filas = filas[:LIMITE_RESULTADOS]
    return {
        "pregunta": pregunta,
        "criterios": "; ".join(criterios) or "ninguno",
        "cantidad": str(len(filas)),
        "datos": json.dumps([compactar_fila(f, perfiles) for f in filas], ensure_ascii=False, indent=1),
        "sin_validar": "sí" if reglas_sin_validar(filas) else "no",
    }


def respuesta_sin_resultados(criterios: list[str]) -> str:
    """0 filas: no hay nada que explicar, así que no se llama al LLM (no puede inventar)."""
    lista = "\n".join(f"  • {c}" for c in criterios)
    return ("No encontré ninguna notebook del catálogo que cumpla todos estos criterios a la vez:\n"
            f"{lista}\n"
            "Probá relajar alguno de ellos (por ejemplo, aceptar un poco más de peso o una gama de GPU "
            "menor) y vuelvo a buscar.")


def crear_chain_explicacion() -> Runnable:
    """Entrada: las variables de entrada_explicacion(). Salida: texto de la respuesta."""
    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content=leer_prompt("explicacion")),
        ("human", PLANTILLA_EXPLICACION),
    ])
    return prompt | crear_llm("explicacion") | StrOutputParser() | RunnableLambda(limpiar_respuesta)


# "RESPUESTA:", "**Respuesta:**" o cualquier rótulo en MAYÚSCULAS con ":" al inicio.
_RE_PREFIJO_RESPUESTA = re.compile(r"^\s*\**\s*respuesta\s*\**\s*:\s*\**\s*", re.IGNORECASE)
_RE_PREFIJO_MAYUSCULAS = re.compile(r"^\s*\**\s*[A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ ]{3,60}\s*\**\s*[:.]\s*\**\s*")


def limpiar_respuesta(texto: str) -> str:
    """Quita encabezados que el modelo agrega aunque el prompt los prohíba ("RESPUESTA:")."""
    texto = _RE_PREFIJO_RESPUESTA.sub("", texto)
    return _RE_PREFIJO_MAYUSCULAS.sub("", texto).strip()


# --- Control de alucinación de números (evidencia para la sección h del informe) ---
_RE_NUMERO = re.compile(r"(?<![\w.])\d+(?:[.,]\d+)?(?![\w])")
_RE_CODIGOS = re.compile(r"\b(?:GM|REC|REN|INT|FZ)-R[D]?\d+\b|\breq_\d+\b|Notebook_\w", re.IGNORECASE)


def numeros_sin_respaldo(respuesta: str, contexto: str) -> list[str]:
    """Números de la respuesta que no aparecen en el contexto que recibió el LLM.

    Es una verificación heurística (no prueba la ausencia de errores, pero detecta
    valores inventados): normaliza coma decimal y elimina los códigos de reglas.
    """
    def numeros(texto: str) -> set[float]:
        texto = _RE_CODIGOS.sub(" ", texto)
        return {float(n.replace(",", ".")) for n in _RE_NUMERO.findall(texto)}

    permitidos = numeros(contexto)
    return sorted(f"{n:g}" for n in numeros(respuesta) - permitidos)


# --- Tabla de evidencias: la imprime Python, no el LLM (D10) ------------------
def tabla_evidencias(filas: list[dict[str, Any]]) -> Table:
    t = Table(title="Evidencias recuperadas de Neo4j", show_lines=True, title_style="bold")
    for col in ("Modelo", "Peso", "Batería", "GPU", "Pantalla", "Movilidad", "Por perfil (gráfica)"):
        t.add_column(col, overflow="fold")
    for f in filas[:LIMITE_RESULTADOS]:
        gpu = f"{f['gpu_gama']} ({f['gpu_gama_indice']}/5)"
        if f["potencia_relativa"] is not None:
            gpu += f"\n{f['tgp_watts']}/{f['tgp_max_watts']} W"
        bateria = ("—" if f["bateria_horas"] is None else f"{_num(f['bateria_horas'])} h") + f"\n{f['fiabilidad_bateria']}"
        movilidad = "—" if f["adecuacion_movilidad"] is None else f"{f['movilidad_etiqueta']} {f['adecuacion_movilidad']:.3f}"
        movilidad += "".join(f"\n{r['regla']}={r['fuerza']}" for r in f["reglas_movilidad"][:2])
        por_perfil = "\n".join(
            f"{ev['perfil']}/{ev['requerimiento']}: GPU {ev['grado_gpu']}, gráf. {ev['adecuacion_grafica']}"
            + "".join(f"\n  ⚠ {a['regla']}" for a in ev["alertas"])
            for ev in f["evaluaciones"]) or "—"
        t.add_row(f["modelo"], f"{f['peso']} kg", bateria, gpu,
                  f"sRGB {f['srgb']}\n{f['refresco_hz']} Hz", movilidad, por_perfil)
    return t


# =============================================================================
# 8. CHAIN MAESTRA "SANDWICH", TRAZA Y API PÚBLICA (SPEC §9)
# =============================================================================
# El estado es un diccionario que cada paso amplía:
#   {pregunta} → +extraccion → +decision → +cypher/parametros/filas → +respuesta
# Cada paso registra su duración en estado["tiempos_ms"].

class ErrorAsistente(Exception):
    """Error con un mensaje apto para el usuario (sin traceback)."""

    def __init__(self, mensaje: str, detalle: str = "") -> None:
        super().__init__(mensaje)
        self.mensaje, self.detalle = mensaje, detalle


class Traza(BaseModel):
    """Todo lo que la consigna pide documentar por caso (sección 6 de la consigna)."""

    pregunta: str
    extraccion: dict[str, Any] | None = None
    decision: dict[str, Any] | None = None
    cypher: str | None = None
    parametros: dict[str, Any] | None = None
    filas: list[dict[str, Any]] = Field(default_factory=list)
    respuesta: str = ""
    tiempos_ms: dict[str, int] = Field(default_factory=dict)


def _cronometrado(nombre: str, fn: Any) -> Runnable:
    """Paso del sándwich: ejecuta fn(estado) → dict, lo agrega al estado y mide su duración."""
    def paso(estado: dict[str, Any]) -> dict[str, Any]:
        t = time.perf_counter()
        nuevo = fn(estado)
        ms = round((time.perf_counter() - t) * 1000)
        return {**estado, **nuevo, "tiempos_ms": {**estado.get("tiempos_ms", {}), nombre: ms}}
    return RunnableLambda(paso, name=nombre)


class Asistente:
    """Orquestador del patrón sándwich (una instancia por sesión)."""

    def __init__(self) -> None:
        try:
            self.bc = BaseConocimiento()
            self.bc.cargar_contexto()
        except (ServiceUnavailable, AuthError) as e:
            raise ErrorAsistente("No pude conectarme a Neo4j. Revisá NEO4J_URI, NEO4J_USERNAME y "
                                 "NEO4J_PASSWORD en el .env y que la instancia de Aura esté activa.",
                                 str(e)) from e
        self._chain_extraccion = crear_chain_extraccion()
        self._chain_explicacion = crear_chain_explicacion()
        self.sandwich = self._crear_sandwich()

    def cerrar(self) -> None:
        self.bc.cerrar()

    # -- pasos ----------------------------------------------------------------
    def _extraer(self, s: dict[str, Any]) -> dict[str, Any]:
        ext = self._chain_extraccion.invoke({"pregunta": s["pregunta"], "catalogo": ", ".join(self.bc.catalogo)})
        return {"extraccion": ext}

    def _rutear(self, s: dict[str, Any]) -> dict[str, Any]:
        return {"decision": rutear(s["extraccion"], self.bc.catalogo)}

    def _consultar(self, s: dict[str, Any]) -> dict[str, Any]:
        d: Decision = s["decision"]
        if d.tipo == "consulta_modelo":
            cypher, parametros, filas = self.bc.ficha(d.modelo)
        else:
            cypher, parametros, filas = self.bc.buscar(d.orden, **d.filtros)
        return {"cypher": cypher, "parametros": parametros, "filas": filas}

    def _explicar(self, s: dict[str, Any]) -> dict[str, Any]:
        if not s["filas"]:
            return {"respuesta": respuesta_sin_resultados(s["decision"].criterios)}
        entrada = entrada_explicacion(s["pregunta"], s["decision"].criterios, s["filas"], self.bc.perfiles)
        return {"respuesta": self._chain_explicacion.invoke(entrada)}

    def _aclarar(self, s: dict[str, Any]) -> dict[str, Any]:
        return {"respuesta": responder_aclaracion(s["decision"])}

    def _crear_sandwich(self) -> Runnable:
        consultar_y_explicar = (
            _cronometrado("consulta_neo4j", self._consultar)          # [3] Neo4j
            | _cronometrado("explicacion", self._explicar)            # [4] LLM
        )
        return (
            _cronometrado("extraccion", self._extraer)                # [1] LLM
            | _cronometrado("router", self._rutear)                   # [2] Python
            | RunnableBranch(
                (lambda s: s["decision"].requiere_neo4j, consultar_y_explicar),
                _cronometrado("aclaracion", self._aclarar),           # sin Neo4j ni LLM
            )
        )

    # -- API pública ----------------------------------------------------------
    def responder(self, pregunta: str) -> Traza:
        """Ejecuta el flujo completo. No imprime nada: PG3 puede reutilizarlo."""
        try:
            s = self.sandwich.invoke({"pregunta": pregunta})
        except (httpx.ConnectError, httpx.ConnectTimeout) as e:
            raise ErrorAsistente(f"No pude conectarme a Ollama en {OLLAMA_HOST}. "
                                 "Iniciá el servicio con: sudo systemctl start ollama", str(e)) from e
        except OllamaResponseError as e:
            if e.status_code == 404:
                raise ErrorAsistente(f"Ollama no tiene el modelo {LLM_MODEL}. "
                                     f"Descargalo con: ollama pull {LLM_MODEL}", str(e)) from e
            raise ErrorAsistente("Ollama devolvió un error al generar la respuesta.", str(e)) from e
        except (OutputParserException, ValidationError) as e:
            raise ErrorAsistente("No pude interpretar la consulta (el modelo no devolvió un JSON "
                                 "válido tras el reintento). ¿Podés reformularla?", str(e)) from e
        except (ServiceUnavailable, SessionExpired) as e:
            raise ErrorAsistente("Se perdió la conexión con Neo4j. Probá de nuevo en unos segundos.",
                                 str(e)) from e
        return Traza(
            pregunta=pregunta,
            extraccion=s["extraccion"].model_dump(),
            decision=s["decision"].model_dump(),
            cypher=s.get("cypher"),
            parametros=s.get("parametros"),
            filas=s.get("filas", []),
            respuesta=s["respuesta"],
            tiempos_ms=s["tiempos_ms"],
        )


# =============================================================================
# 9. CLI
# =============================================================================

def _cypher_resumido(cypher: str) -> str:
    """Muestra el MATCH/WHERE (lo que cambia por consulta) y resume el bloque común."""
    corte = cypher.find("// (1)")
    if corte < 0:
        return cypher.strip()
    cola = "\n".join(re.findall(r"^(?:ORDER BY|LIMIT) .*$", cypher, re.MULTILINE))
    return (cypher[:corte].strip()
            + "\n// … bloque común: reglas de movilidad, evaluaciones por perfil y alertas SM3 (SPEC §7.1)"
            + "\n// … RETURN modelo, peso, gpu_*, srgb, bateria_*, adecuacion_movilidad, reglas, evaluaciones"
            + (f"\n{cola}" if cola else ""))


def mostrar_traza(console: Console, t: Traza, simple: bool = False, cypher_completo: bool = False) -> None:
    if not simple:
        console.print(Panel(JSON.from_data(t.extraccion), title="① Extracción (LLM → JSON)",
                            subtitle=f"{t.tiempos_ms.get('extraccion', 0) / 1000:.1f} s", border_style="cyan"))
        d = t.decision or {}
        cuerpo: list[Any] = [Text.assemble(("Decisión: ", "bold"), d.get("tipo", ""))]
        if d.get("criterios"):
            cuerpo.append(Text.assemble(("Criterios aplicados: ", "bold"), "; ".join(d["criterios"])))
        if t.cypher:
            cuerpo.append(Syntax(t.cypher.strip() if cypher_completo else _cypher_resumido(t.cypher),
                                 "cypher", theme="ansi_dark", word_wrap=True))
            cuerpo.append(Text.assemble(("Parámetros: ", "bold"),
                                        json.dumps(t.parametros, ensure_ascii=False)))
        else:
            cuerpo.append(Text("No se consulta Neo4j.", style="italic"))
        console.print(Panel(Group(*cuerpo), title="② Router y consulta Cypher", border_style="magenta"))
        if t.cypher:
            contenido: Any = tabla_evidencias(t.filas) if t.filas else Text("0 filas", style="italic")
            console.print(Panel(contenido, title=f"③ Conocimiento recuperado de Neo4j ({len(t.filas)} filas)",
                                subtitle=f"{t.tiempos_ms.get('consulta_neo4j', 0)} ms", border_style="green"))
    pie = " · ".join(f"{k} {v / 1000:.1f} s" for k, v in t.tiempos_ms.items())
    console.print(Panel(Markdown(t.respuesta), title="④ Respuesta", subtitle=pie, border_style="yellow"))


# --- Batería de casos de prueba (SPEC §11) → evidencias/ -----------------------
DIR_EVIDENCIAS = Path(__file__).resolve().parent / "evidencias"

# (pregunta, decisión esperada, modelos esperados en el resultado o None, propósito en el informe)
CASOS_PRUEBA: list[tuple[str, str, list[str] | None, str]] = [
    ("Quiero una notebook gamer para jugar juegos pesados", "consulta_unificada",
     ["Notebook_C", "Notebook_X"], "f · interacción exitosa (gráfica)"),
    ("Necesito algo liviano, menos de 1.5 kg, con 10 horas de batería", "consulta_unificada",
     ["Notebook_B"], "f · interacción exitosa (movilidad)"),
    ("Gamer pero que pese menos de 2 kilos", "consulta_unificada",
     ["Notebook_X"], "f · interacción exitosa (mixta)"),
    ("Soy diseñador gráfico, necesito fidelidad de color", "consulta_unificada",
     ["Notebook_C", "Notebook_X"], "f · interacción exitosa (pantalla)"),
    ("¿Qué tal la Notebook_X?", "consulta_modelo", ["Notebook_X"], "f · interacción exitosa (modelo)"),
    ("Quiero una que pese 50 gramos y dure 200 horas", "aclaracion", None, "g · datos absurdos (guardrail)"),
    ("¿Cuánta RAM tiene la mejor?", "fuera_de_alcance", None, "g · fuera de alcance (deriva a SM2)"),
    ("Recomendame una", "aclaracion", None, "g · consulta incompleta"),
    ("¿Cuánto dura la batería de la notebook M?", "consulta_modelo", ["Notebook_M"],
     "h · dato faltante (no debe inventar la batería)"),
    ("¿Qué tal la Notebook_Z?", "aclaracion", None, "g · modelo inexistente"),
    ("¿Cuánto dura la batería de la Notebook_G?", "consulta_modelo", ["Notebook_G"],
     "h · dato estimado (GM-R12)"),
    ("¿La Notebook_K me sirve para llevarla a todos lados?", "consulta_modelo", ["Notebook_K"],
     "h · evaluaciones que dependen del perfil"),
]


def _md_fila(f: dict[str, Any]) -> str:
    bat = "—" if f["bateria_horas"] is None else f"{_num(f['bateria_horas'])} h"
    mov = "—" if f["adecuacion_movilidad"] is None else f"{f['movilidad_etiqueta']} ({f['adecuacion_movilidad']})"
    tgp = f" · {f['tgp_watts']}/{f['tgp_max_watts']} W" if f["potencia_relativa"] is not None else ""
    perfiles = "; ".join(f"{e['perfil']}/{e['requerimiento']}: GPU {e['grado_gpu']}, gráf. {e['adecuacion_grafica']}"
                         + "".join(f" ⚠{a['regla']}" for a in e["alertas"]) for e in f["evaluaciones"]) or "—"
    return (f"| {f['modelo']} | {f['peso']} kg | {bat} ({f['fiabilidad_bateria']}) | "
            f"{f['gpu_gama']} ({f['gpu_gama_indice']}/5){tgp} | sRGB {f['srgb']}, {f['refresco_hz']} Hz | "
            f"{mov} | {perfiles} |")


def ejecutar_casos(asistente: Asistente, console: Console) -> int:
    """Corre CASOS_PRUEBA y escribe evidencias/casos.md, casos.json y un SVG por caso."""
    DIR_EVIDENCIAS.mkdir(exist_ok=True)
    resultados, md = [], [
        "# Evidencias de ejecución — Asistente SM3 (PI4)", "",
        f"Generado con `python sm3_asistente.py --casos` · modelo `{LLM_MODEL}` · "
        f"{time.strftime('%d/%m/%Y %H:%M')}", "",
        "| # | Consulta | Propósito | Decisión | Resultado | Verificación |",
        "|---|---|---|---|---|---|",
    ]
    detalle: list[str] = []
    fallidos = 0
    for i, (pregunta, tipo_esp, modelos_esp, proposito) in enumerate(CASOS_PRUEBA, 1):
        console.print(f"[bold]{i:>2}/{len(CASOS_PRUEBA)}[/] {pregunta}", end=" ")
        try:
            t = asistente.responder(pregunta)
        except ErrorAsistente as e:
            console.print(f"[red]✗ {e.mensaje}[/]")
            return 1
        modelos = [f["modelo"] for f in t.filas] if t.cypher else None
        ok = t.decision["tipo"] == tipo_esp and modelos == modelos_esp
        fallidos += not ok
        console.print("[green]✓[/]" if ok else f"[red]✗ esperado {tipo_esp} {modelos_esp}[/]",
                      f"({sum(t.tiempos_ms.values()) / 1000:.0f} s)")

        # "Captura" fiel de la terminal: la misma salida de la CLI, exportada a SVG.
        grabadora = Console(record=True, width=118, file=io.StringIO(), force_terminal=True)
        grabadora.print(f"[bold blue]Vos:[/] {pregunta}")
        mostrar_traza(grabadora, t)
        svg = DIR_EVIDENCIAS / f"caso_{i:02d}.svg"
        grabadora.save_svg(str(svg), title=f"Asistente SM3 — caso {i}")

        resultados.append({"caso": i, "proposito": proposito, "esperado": {"decision": tipo_esp,
                           "modelos": modelos_esp}, "verificado": ok, **t.model_dump()})
        md.append(f"| {i} | {pregunta} | {proposito} | `{t.decision['tipo']}` | "
                  f"{', '.join(modelos) if modelos else 'sin consulta a Neo4j'} | {'✓' if ok else '✗'} |")
        detalle += [
            f"## Caso {i}: {pregunta}", "", f"*Propósito:* {proposito} · *captura:* [`{svg.name}`]({svg.name})", "",
            "**1. Consulta del usuario**", "", f"> {pregunta}", "",
            "**2. Información extraída (LLM → JSON)**", "", "```json",
            json.dumps(t.extraccion, ensure_ascii=False, indent=2), "```", "",
            f"Decisión del router: `{t.decision['tipo']}`"
            + (f" · criterios: {'; '.join(t.decision['criterios'])}" if t.decision["criterios"] else ""), "",
            "**3. Consulta ejecutada**", "",
        ]
        if t.cypher:
            detalle += ["```cypher", t.cypher.strip(), "```", "",
                        f"Parámetros: `{json.dumps(t.parametros, ensure_ascii=False)}`", "",
                        "**4. Resultado recuperado de Neo4j**", ""]
            if t.filas:
                detalle += ["| Modelo | Peso | Batería | GPU | Pantalla | Movilidad | Por perfil (gráfica) |",
                            "|---|---|---|---|---|---|---|", *[_md_fila(f) for f in t.filas], ""]
            else:
                detalle += ["0 filas.", ""]
        else:
            detalle += ["No se consultó Neo4j (el router respondió directamente).", "",
                        "**4. Resultado recuperado de Neo4j**", "", "—", ""]
        tiempos = " · ".join(f"{k} {v / 1000:.1f} s" for k, v in t.tiempos_ms.items())
        detalle += ["**5. Respuesta generada**", "", t.respuesta, "", f"*Tiempos:* {tiempos}", "", "---", ""]

    md += ["", f"**{len(CASOS_PRUEBA) - fallidos}/{len(CASOS_PRUEBA)} casos con el resultado esperado.** "
           "La verificación compara la decisión del router y los modelos recuperados; "
           "la calidad de la redacción se revisa a mano (ver SPEC §15).", "", "---", "", *detalle]
    (DIR_EVIDENCIAS / "casos.md").write_text("\n".join(md), encoding="utf-8")
    (DIR_EVIDENCIAS / "casos.json").write_text(
        json.dumps(resultados, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    console.print(f"\n[bold]{len(CASOS_PRUEBA) - fallidos}/{len(CASOS_PRUEBA)}[/] casos OK → "
                  f"{DIR_EVIDENCIAS}/casos.md, casos.json y caso_XX.svg")
    return 1 if fallidos else 0


def main() -> None:
    ap = argparse.ArgumentParser(description="Asistente SM3 — evaluación gráfica y de movilidad (PI4).")
    ap.add_argument("--pregunta", help="ejecuta una sola consulta y termina")
    ap.add_argument("--simple", action="store_true", help="muestra solo la respuesta final")
    ap.add_argument("--cypher-completo", action="store_true", help="muestra el Cypher entero en el panel ②")
    ap.add_argument("--diagrama", action="store_true", help="imprime el diagrama Mermaid de la chain y termina")
    ap.add_argument("--casos", action="store_true", help="corre los 12 casos de prueba y escribe evidencias/")
    args = ap.parse_args()
    console = Console()

    try:
        with console.status("Conectando con Neo4j…"):
            asistente = Asistente()
    except ErrorAsistente as e:
        console.print(f"[bold red]✗ {e.mensaje}[/]")
        sys.exit(1)

    try:
        if args.diagrama:
            print(asistente.sandwich.get_graph().draw_mermaid())
            return
        if args.casos:
            sys.exit(ejecutar_casos(asistente, console))

        def atender(pregunta: str) -> None:
            try:
                with console.status("Pensando… (extracción → router → Neo4j → explicación)"):
                    traza = asistente.responder(pregunta)
            except ErrorAsistente as e:
                console.print(f"[bold red]✗ {e.mensaje}[/]")
                return
            mostrar_traza(console, traza, simple=args.simple, cypher_completo=args.cypher_completo)

        if args.pregunta:
            atender(args.pregunta)
            return

        console.print(Panel(
            f"Evalúo GPU, pantalla, peso y batería de {len(asistente.bc.catalogo)} notebooks "
            f"({', '.join(asistente.bc.catalogo)}).\nEscribí tu consulta, o [bold]salir[/] para terminar.",
            title="Asistente SM3 · Gráfica y movilidad", border_style="blue"))
        while True:
            try:
                pregunta = console.input("[bold blue]Vos:[/] ").strip()
            except (EOFError, KeyboardInterrupt):
                break
            if pregunta.lower() in {"salir", "exit", "quit"}:
                break
            if pregunta:
                atender(pregunta)
    finally:
        asistente.cerrar()


if __name__ == "__main__":
    main()
