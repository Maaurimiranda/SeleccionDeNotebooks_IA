#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Actividad PI4 - Unidad 4 (Individual)
Integracion de Modelos de Lenguaje con la Base de Conocimiento

Proyecto : Asistente Experto para la Seleccion Personalizada de Notebooks (Grupo 2, 5K09)
Submodulo: SM4 - Integracion, costo-beneficio y recomendacion explicable
Autora   : Luconi Furque, Martina (legajo 48889)

Patron sandwich:
    texto del asesor -> [LLM: prompt de EXTRACCION, JSON estricto]
                     -> validacion en Python
                     -> [Neo4j: consultas Cypher parametrizadas del grafo PG2]
                     -> paquete de evidencia (JSON)
                     -> [LLM: prompt de EXPLICACION, solo con esa evidencia]
                     -> verificacion REC-R11 (hasta 2 regeneraciones, despues plantilla fija)

El LLM no escribe Cypher, no calcula y no decide: el estado, el grado, el orden y
las alertas de cada notebook los infiere el grafo (bloque 10.f del script de PG2).

Requisitos:
    pip install neo4j
    Ollama corriendo localmente (https://ollama.com) con un modelo descargado, p. ej.:
        ollama pull qwen2.5:7b
    Neo4j 5.x con el script Grupo_2_PG2_U1.cypher ya ejecutado (bloques 0 a 12).

Uso:
    python Luconi_Martina_PI4_U4.py                    # modo interactivo (pedido req_01 por defecto)
    python Luconi_Martina_PI4_U4.py --req req_03       # otro pedido como contexto de la sesion
    python Luconi_Martina_PI4_U4.py --casos            # corre los casos de prueba de la PI4
    python Luconi_Martina_PI4_U4.py --sin-llm --casos  # respaldo sin LLM (extractor por reglas + plantilla)
    python Luconi_Martina_PI4_U4.py --api              # expone POST /consultar con FastAPI (para PG3)

Variables de entorno (opcionales):
    NEO4J_URI (bolt://localhost:7687), NEO4J_USER (neo4j), NEO4J_PASSWORD (password)
    OLLAMA_URL (http://localhost:11434), OLLAMA_MODEL (qwen2.5:7b)
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

from neo4j import GraphDatabase, READ_ACCESS

# ---------------------------------------------------------------------------
# Configuracion
# ---------------------------------------------------------------------------
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")

MAX_REGENERACIONES = 2          # REC-R11: hasta 2 regeneraciones, despues plantilla fija
INTENCIONES = ["recomendar", "explicar_notebook", "comparar", "costo_beneficio", "desconocida"]
CONCEPTOS = ["presupuesto", "costo_beneficio", "ampliabilidad", "alertas",
             "sobredimensionamiento", "infradimensionamiento", "dato_faltante",
             "excluyente", "desempate"]


# ---------------------------------------------------------------------------
# 1. PROMPT DE EXTRACCION (texto exacto del System Prompt)
# ---------------------------------------------------------------------------
PROMPT_EXTRACCION = """Eres un extractor estricto de parametros para un sistema experto de recomendacion de notebooks.
Recibes la consulta de un asesor de ventas sobre la recomendacion que el sistema ya calculo para un pedido.
Tu unica tarea es convertir la consulta en un JSON que cumpla exactamente el esquema indicado.

REGLAS:
1. Devuelve SOLO el objeto JSON. Sin texto antes ni despues, sin comentarios, sin bloques de codigo.
2. No respondas la consulta, no recomiendes, no calcules y no opines: solo extraes.
3. Extrae unicamente lo que esta escrito en la consulta. Si un dato no aparece, usa null, [] o false.
   Nunca completes un dato con conocimiento propio.
4. "intencion" debe ser exactamente uno de estos valores:
   - "recomendar": pide la recomendacion, el ranking o "que le conviene" a un comprador o pedido.
   - "explicar_notebook": pregunta por que una notebook concreta quedo recomendada, descartada,
     indeterminada o en cierto puesto, o si le sirve al comprador.
   - "comparar": pide comparar dos o mas notebooks concretas o por que una quedo antes que otra.
   - "costo_beneficio": pide la opcion mas barata que sirva, la mejor relacion precio-calidad
     o un orden por precio.
   - "desconocida": la consulta no trata sobre notebooks o recomendaciones, es ambigua o no se entiende.
5. "notebooks": modelos mencionados, escritos como "Notebook_<letra>" (por ejemplo "la H" -> "Notebook_H").
   No agregues modelos que no esten mencionados.
6. "comprador_id" con el formato "comprador_NN" y "requerimiento_id" con el formato "req_NN",
   solo si aparecen en la consulta.
7. "filtros.precio_max_usd": tope de precio en USD SOLO si el asesor lo dice ("de menos de 900", "hasta 800 dolares").
   "filtros.incluir_fuera_de_presupuesto": false solo si pide explicitamente excluir lo que se pasa del presupuesto;
   en cualquier otro caso true. "filtros.solo_sin_alertas": true solo si pide opciones sin advertencias.
8. "conceptos": los conceptos del dominio que la consulta menciona, solo de esta lista:
   presupuesto, costo_beneficio, ampliabilidad, alertas, sobredimensionamiento, infradimensionamiento,
   dato_faltante, excluyente, desempate.
9. "evidencia": por cada dato extraido (intencion, notebook, comprador, requerimiento, filtro), el fragmento
   LITERAL de la consulta que lo respalda. Si no hay fragmento literal, no extraigas el dato.
10. Si la consulta no se puede interpretar, usa "intencion": "desconocida", "requiere_aclaracion": true
    y escribe en "pregunta_aclaracion" una pregunta breve para el asesor.

ESQUEMA:
{
  "intencion": "recomendar | explicar_notebook | comparar | costo_beneficio | desconocida",
  "comprador_id": "comprador_NN" o null,
  "requerimiento_id": "req_NN" o null,
  "notebooks": ["Notebook_X", ...],
  "filtros": {"precio_max_usd": numero o null, "incluir_fuera_de_presupuesto": true/false, "solo_sin_alertas": true/false},
  "conceptos": ["..."],
  "evidencia": [{"dato": "...", "fragmento": "..."}],
  "requiere_aclaracion": true/false,
  "pregunta_aclaracion": "..." o null
}

EJEMPLO
Consulta: "¿Por que la H quedo antes que la B para el comprador_01?"
Salida: {"intencion":"comparar","comprador_id":"comprador_01","requerimiento_id":null,"notebooks":["Notebook_H","Notebook_B"],"filtros":{"precio_max_usd":null,"incluir_fuera_de_presupuesto":true,"solo_sin_alertas":false},"conceptos":["desempate"],"evidencia":[{"dato":"intencion","fragmento":"quedo antes que"},{"dato":"Notebook_H","fragmento":"la H"},{"dato":"Notebook_B","fragmento":"la B"},{"dato":"comprador_id","fragmento":"comprador_01"}],"requiere_aclaracion":false,"pregunta_aclaracion":null}"""

# Esquema JSON que se le pasa a Ollama en "format" (salida estructurada)
ESQUEMA_EXTRACCION = {
    "type": "object",
    "properties": {
        "intencion": {"type": "string", "enum": INTENCIONES},
        "comprador_id": {"type": ["string", "null"]},
        "requerimiento_id": {"type": ["string", "null"]},
        "notebooks": {"type": "array", "items": {"type": "string"}},
        "filtros": {
            "type": "object",
            "properties": {
                "precio_max_usd": {"type": ["number", "null"]},
                "incluir_fuera_de_presupuesto": {"type": "boolean"},
                "solo_sin_alertas": {"type": "boolean"},
            },
            "required": ["precio_max_usd", "incluir_fuera_de_presupuesto", "solo_sin_alertas"],
        },
        "conceptos": {"type": "array", "items": {"type": "string", "enum": CONCEPTOS}},
        "evidencia": {
            "type": "array",
            "items": {"type": "object",
                      "properties": {"dato": {"type": "string"}, "fragmento": {"type": "string"}},
                      "required": ["dato", "fragmento"]},
        },
        "requiere_aclaracion": {"type": "boolean"},
        "pregunta_aclaracion": {"type": ["string", "null"]},
    },
    "required": ["intencion", "comprador_id", "requerimiento_id", "notebooks", "filtros",
                 "conceptos", "evidencia", "requiere_aclaracion", "pregunta_aclaracion"],
}


# ---------------------------------------------------------------------------
# 2. PROMPT DE EXPLICACION (texto exacto del System Prompt)
# ---------------------------------------------------------------------------
PROMPT_EXPLICACION = """Eres el asistente explicativo de un sistema experto que recomienda notebooks.
Le hablas a un asesor de ventas que esta atendiendo a un comprador. El sistema experto (una base de
conocimiento en Neo4j) ya tomo todas las decisiones. Tu tarea es contarle al asesor, en espanol claro y
con un tono cercano y empatico con la necesidad del comprador, que decidio el sistema y por que.

Recibes dos cosas:
- CONSULTA: lo que pregunto el asesor.
- EVIDENCIA: un JSON con los resultados devueltos por Neo4j. Es la UNICA fuente de verdad.

REGLAS OBLIGATORIAS:
1. Usa unicamente datos que esten en EVIDENCIA. No agregues modelos, precios, componentes, porcentajes,
   reglas ni criterios que no esten ahi. No uses conocimiento general sobre notebooks o marcas.
2. No calcules nada nuevo (ni diferencias, ni promedios, ni porcentajes). Si un numero no esta en
   EVIDENCIA, no lo escribas. Copia los numeros tal como aparecen.
3. No cambies el estado, el orden ni las alertas. Si el sistema descarto una notebook, no la sugieras.
4. Justifica cada conclusion con su evidencia: lo que la notebook cumple, lo que no cumple, lo que falta
   verificar y las alertas. Cuando ayude a auditar, cita entre parentesis el id de la regla (por ejemplo
   "(REC-R8)") tal como figura en EVIDENCIA.
5. Traduce los grados a palabras usando la etiqueta o el estado ("recomendada con adecuacion alta",
   "para considerar"). Si das el valor numerico, que sea el que figura en EVIDENCIA.
6. Si un valor viene como rango (minimo y maximo), dilo como rango y explica que depende de un dato que
   falta. Nunca elijas un valor intermedio.
7. Si EVIDENCIA trae "preguntas_pendientes", "sin_alternativa" o un "aviso", explicalo y sugiere al asesor
   la pregunta o el paso siguiente que figura en EVIDENCIA.
8. Si EVIDENCIA no alcanza para responder la consulta, dilo con honestidad en una oracion.
9. Cierra con una oracion que recuerde que los parametros del sistema son provisionales, si EVIDENCIA
   trae "advertencia".
10. Formato: entre 4 y 10 oraciones, en parrafos breves o una lista corta. Sin titulos, sin JSON, sin
    tablas."""


# ---------------------------------------------------------------------------
# 3. CONSULTAS CYPHER (todas de solo lectura; los parametros los arma Python)
# ---------------------------------------------------------------------------
CONSULTAS = {
    # Catalogo para validar las entidades extraidas
    "CATALOGO": """
MATCH (n:Notebook) RETURN collect(n.modelo) AS modelos""",

    # Comprador -> su requerimiento (si el asesor nombra al comprador y no al pedido)
    "REQ_DE_COMPRADOR": """
MATCH (:Comprador {id:$comprador_id})-[:FORMULA]->(c:Requerimiento)
RETURN c.id AS requerimiento ORDER BY c.id DESC LIMIT 1""",

    # L1 de PG2: requerimiento formal interpretado (y preguntas pendientes si el perfil es indeterminado)
    "L1_REQUERIMIENTO": """
MATCH (c:Requerimiento {id:$requerimiento_id})
OPTIONAL MATCH (p:Comprador)-[:FORMULA]->(c)
OPTIONAL MATCH (c)-[:REQUIERE_ACLARACION]->(q:Pregunta)
OPTIONAL MATCH (c)-[:CONSULTA_POR]->(nc:Notebook)
RETURN c.id AS requerimiento, p.id AS comprador, c.texto_pedido AS pedido,
       c.presupuesto_usd AS presupuesto_usd, c.prioridad AS prioridad,
       c.perfil_dominante AS perfil_dominante, c.grado_perfil_dominante AS grado_perfil,
       nc.modelo AS notebook_consultada,
       collect(DISTINCT q.texto) AS preguntas_pendientes""",

    # Q1 (SM4): recomendacion final (REC-R8) y alternativa fuera de presupuesto, con filtros
    "Q1_RECOMENDACION": """
MATCH (c:Requerimiento {id:$requerimiento_id})-[:RECIBE]->(rec:Recomendacion)
      -[p:PROPONE|PROPONE_FUERA_DE_PRESUPUESTO]->(n:Notebook)
MATCH (c)-[:EVALUA]->(ev:Evaluacion)-[:SOBRE]->(n)-[:POSEE]->(r:RAM)
WHERE ($precio_max_usd IS NULL OR n.precio_usd <= $precio_max_usd)
  AND ($incluir_fuera_de_presupuesto OR type(p) = 'PROPONE')
OPTIONAL MATCH (al:Alerta)
WHERE EXISTS { MATCH (ev)-[:GENERA]->(al) } OR EXISTS { MATCH (n)-[:GENERA]->(al) }
WITH p, n, ev, r, [a IN collect(DISTINCT {tipo:al.tipo, regla:al.regla_origen, mensaje:al.mensaje})
                   WHERE a.tipo IS NOT NULL] AS alertas
WHERE NOT $solo_sin_alertas OR size(alertas) = 0
RETURN CASE type(p) WHEN 'PROPONE' THEN p.orden END AS puesto,
       type(p) = 'PROPONE_FUERA_DE_PRESUPUESTO' AS fuera_de_presupuesto,
       n.modelo AS notebook, n.precio_usd AS precio_usd, ev.estado AS estado,
       ev.etiqueta_recomendacion AS etiqueta,
       coalesce(ev.grado_recomendacion, ev.grado_recomendacion_min) AS grado_recomendacion,
       ev.grado_recomendacion_max AS grado_recomendacion_max,
       ev.excedente_presupuesto AS excedente_presupuesto_pct,
       ev.indice_costo_beneficio AS indice_costo_beneficio,
       r.nivel_ampliabilidad AS ampliabilidad_ram, alertas
ORDER BY fuera_de_presupuesto, puesto""",

    # Q2 (SM4): resto de las notebooks evaluadas y su estado (para "por que no aparece X")
    "Q2_NO_PROPUESTAS": """
MATCH (c:Requerimiento {id:$requerimiento_id})-[:EVALUA]->(ev:Evaluacion)-[:SOBRE]->(n:Notebook)
WHERE NOT EXISTS { MATCH (c)-[:RECIBE]->(:Recomendacion)-[:PROPONE|PROPONE_FUERA_DE_PRESUPUESTO]->(n) }
RETURN n.modelo AS notebook, ev.estado AS estado
ORDER BY coalesce(ev.grado_recomendacion, ev.grado_recomendacion_min) DESC""",

    # Q3 (SM4): sin alternativa adecuada (REC-R10)
    "Q3_SIN_ALTERNATIVA": """
MATCH (c:Requerimiento {id:$requerimiento_id})-[:RECIBE]->(s:SinAlternativaAdecuada)
RETURN s.motivo AS motivo""",

    # Q4 (SM4, sobre L2 de PG2): explicacion de UNA notebook para UN pedido, en tres bloques (REC-R11)
    "Q4_EXPLICAR_NOTEBOOK": """
MATCH (c:Requerimiento {id:$requerimiento_id})-[:EVALUA]->(ev:Evaluacion)-[:SOBRE]->(n:Notebook {modelo:$modelo})
MATCH (c)-[:TIENE_PERFIL_DOMINANTE]->(pf:Perfil)
MATCH (n)-[:POSEE]->(r:RAM), (n)-[:POSEE]->(b:Bateria)
OPTIONAL MATCH (c)-[:RECIBE]->(:Recomendacion)-[p:PROPONE|PROPONE_FUERA_DE_PRESUPUESTO]->(n)
OPTIONAL MATCH (c)-[cp:CONSULTA_POR]->(n)
OPTIONAL MATCH (al:Alerta)
WHERE EXISTS { MATCH (ev)-[:GENERA]->(al) } OR EXISTS { MATCH (n)-[:GENERA]->(al) }
WITH c, ev, n, pf, r, b, p, cp, [a IN collect(DISTINCT {tipo:al.tipo, regla:al.regla_origen, mensaje:al.mensaje})
                            WHERE a.tipo IS NOT NULL] AS alertas
RETURN n.modelo AS notebook, n.precio_usd AS precio_usd, c.presupuesto_usd AS presupuesto_usd,
       pf.codigo AS perfil, ev.estado AS estado, ev.etiqueta_recomendacion AS etiqueta,
       coalesce(ev.grado_recomendacion, ev.grado_recomendacion_min) AS grado_recomendacion,
       ev.grado_recomendacion_max AS grado_recomendacion_max,
       coalesce(ev.adecuacion_global, ev.adecuacion_global_min) AS adecuacion_global,
       ev.adecuacion_global_max AS adecuacion_global_max,
       {rendimiento:ev.peso_rendimiento, grafica:ev.peso_grafica, movilidad:ev.peso_movilidad} AS pesos,
       ev.excedente_presupuesto AS excedente_presupuesto_pct,
       ev.indice_costo_beneficio AS indice_costo_beneficio,
       ev.dato_faltante AS dato_faltante,
       CASE type(p) WHEN 'PROPONE' THEN 'puesto ' + toString(p.orden)
                    WHEN 'PROPONE_FUERA_DE_PRESUPUESTO' THEN 'alternativa fuera de presupuesto'
                    ELSE CASE WHEN cp IS NOT NULL THEN 'consulta puntual: se responde con su evaluacion, sin ranking'
                              ELSE 'no figura en la recomendacion' END END AS en_la_recomendacion,
       [x IN [
         CASE WHEN ev.excluyente_virtualizacion = 'cumple' THEN 'La CPU soporta virtualizacion por hardware' END,
         CASE WHEN r.ram_gb >= pf.ram_min THEN 'La RAM alcanza el minimo del perfil (' + toString(r.ram_gb) + ' GB)' END,
         CASE WHEN r.nivel_ampliabilidad = 'alta' THEN 'La RAM se puede ampliar y queda un slot M.2 libre' END,
         CASE WHEN ev.excedente_presupuesto = 0.0 THEN 'El precio esta dentro del presupuesto' END
       ] WHERE x IS NOT NULL] AS cumple,
       [x IN [
         CASE WHEN ev.excluyente_virtualizacion = 'no cumple' THEN 'La CPU no soporta virtualizacion: requisito excluyente' END,
         CASE WHEN r.ram_gb < pf.ram_min THEN 'La RAM (' + toString(r.ram_gb) + ' GB) no llega al minimo del perfil (' + toString(pf.ram_min) + ' GB)' END,
         CASE WHEN ev.riesgo_etiqueta = 'alto' THEN 'Riesgo alto de quedarse corta de RAM' END,
         CASE WHEN ev.excedente_presupuesto > 0 THEN 'El precio supera el presupuesto en ' + toString(ev.excedente_presupuesto) + ' %' END
       ] WHERE x IS NOT NULL] AS no_cumple,
       [x IN [
         CASE WHEN ev.excluyente_virtualizacion = 'falta informacion' THEN 'La ficha no informa si la CPU soporta virtualizacion' END,
         CASE WHEN r.ampliabilidad = 'desconocida' THEN 'La ficha no informa si la RAM es ampliable' END,
         CASE WHEN b.tipo_dato = 'estimada' THEN 'La autonomia es estimada, no medida' END,
         CASE WHEN b.tipo_dato = 'desconocida' THEN 'La ficha no informa la autonomia: la adecuacion se informa como rango' END
       ] WHERE x IS NOT NULL] AS falta_verificar,
       alertas""",

    # Q5 (SM4, sobre L3 de PG2): traza de reglas activadas en la evaluacion (y sus lecturas)
    "Q5_TRAZA": """
MATCH (c:Requerimiento {id:$requerimiento_id})-[:EVALUA]->(ev:Evaluacion)-[:SOBRE]->(:Notebook {modelo:$modelo})
MATCH (ev)-[:TIENE_LECTURA*0..1]->(x)-[act:ACTIVA]->(q:Regla)
WHERE q.submodulo = 'SM4' OR act.fuerza IS NOT NULL
RETURN q.id AS regla, q.submodulo AS submodulo,
       coalesce(q.antecedente, q.enunciado) AS antecedente_o_enunciado,
       q.consecuente AS consecuente, x.escenario AS escenario, act.fuerza AS fuerza
ORDER BY submodulo DESC, regla, escenario""",

    # Q6 (SM4, sobre C3 de PG2): comparacion de dos o mas notebooks para un pedido + criterio de desempate
    "Q6_COMPARAR": """
MATCH (c:Requerimiento {id:$requerimiento_id})-[:EVALUA]->(ev:Evaluacion)-[:SOBRE]->(n:Notebook)
WHERE n.modelo IN $modelos
MATCH (n)-[:POSEE]->(r:RAM)
OPTIONAL MATCH (c)-[:RECIBE]->(:Recomendacion)-[p:PROPONE|PROPONE_FUERA_DE_PRESUPUESTO]->(n)
OPTIONAL MATCH (al:Alerta)
WHERE EXISTS { MATCH (ev)-[:GENERA]->(al) } OR EXISTS { MATCH (n)-[:GENERA]->(al) }
WITH ev, n, r, p, [a IN collect(DISTINCT {tipo:al.tipo, regla:al.regla_origen}) WHERE a.tipo IS NOT NULL] AS alertas
RETURN n.modelo AS notebook, n.precio_usd AS precio_usd, ev.estado AS estado,
       coalesce(ev.grado_recomendacion, ev.grado_recomendacion_min) AS grado_recomendacion,
       ev.grado_recomendacion_max AS grado_recomendacion_max,
       coalesce(ev.adecuacion_global, ev.adecuacion_global_min) AS adecuacion_global,
       ev.adecuacion_global_max AS adecuacion_global_max,
       ev.excedente_presupuesto AS excedente_presupuesto_pct,
       ev.indice_costo_beneficio AS indice_costo_beneficio,
       r.nivel_ampliabilidad AS ampliabilidad_ram,
       CASE ev.excluyente_virtualizacion
         WHEN 'no cumple' THEN 'La CPU no soporta virtualizacion por hardware: requisito excluyente del perfil (REC-R3)'
         WHEN 'falta informacion' THEN 'La ficha no informa si la CPU soporta virtualizacion (REC-R3)'
       END AS motivo_excluyente,
       CASE type(p) WHEN 'PROPONE' THEN 'puesto ' + toString(p.orden)
                    WHEN 'PROPONE_FUERA_DE_PRESUPUESTO' THEN 'alternativa fuera de presupuesto'
                    ELSE 'no figura en la recomendacion' END AS en_la_recomendacion,
       alertas
ORDER BY coalesce(p.orden, 99), grado_recomendacion DESC""",

    "Q6B_CRITERIO_DESEMPATE": """
MATCH (q:Regla {id:'REC-R8'}), (me:Parametro {nombre:'P_MARGEN_EMPATE'})
RETURN q.id AS regla, q.enunciado AS enunciado, me.valor AS margen_empate,
       me.estado_validacion AS estado_parametro""",

    # Q7 (SM4): orden por indice costo-beneficio (REC-R9) entre las notebooks no descartadas
    "Q7_COSTO_BENEFICIO": """
MATCH (c:Requerimiento {id:$requerimiento_id})-[:EVALUA]->(ev:Evaluacion)-[:SOBRE]->(n:Notebook)
WHERE ev.estado STARTS WITH 'Recomendada'
  AND ($precio_max_usd IS NULL OR n.precio_usd <= $precio_max_usd)
  AND ($incluir_fuera_de_presupuesto OR ev.excedente_presupuesto = 0.0)
OPTIONAL MATCH (al:Alerta)
WHERE EXISTS { MATCH (ev)-[:GENERA]->(al) } OR EXISTS { MATCH (n)-[:GENERA]->(al) }
WITH ev, n, [a IN collect(DISTINCT {tipo:al.tipo, regla:al.regla_origen}) WHERE a.tipo IS NOT NULL] AS alertas
WHERE NOT $solo_sin_alertas OR size(alertas) = 0
MATCH (q:Regla {id:'REC-R9'})
RETURN n.modelo AS notebook, n.precio_usd AS precio_usd, ev.estado AS estado,
       ev.indice_costo_beneficio AS indice_costo_beneficio,
       coalesce(ev.grado_recomendacion, ev.grado_recomendacion_min) AS grado_recomendacion,
       ev.excedente_presupuesto AS excedente_presupuesto_pct, alertas,
       q.id + ': ' + q.enunciado AS regla_aplicada
ORDER BY indice_costo_beneficio DESC""",

    # Q8 (sobre L4 de PG2): parametros de SM4 sin validar (advertencia que viaja en toda respuesta)
    "Q8_PARAMETROS_SM4": """
MATCH (v:VariableDifusa {submodulo:'SM4'})-[:TIENE_ETIQUETA]->(e:EtiquetaDifusa)
RETURN count(e) AS etiquetas_sm4,
       size([x IN collect(e.estado_validacion) WHERE x <> 'validado']) AS sin_validar""",
}


# ---------------------------------------------------------------------------
# Acceso a Neo4j (solo lectura)
# ---------------------------------------------------------------------------
class BaseConocimiento:
    def __init__(self, uri=NEO4J_URI, user=NEO4J_USER, password=NEO4J_PASSWORD):
        self.driver = GraphDatabase.driver(uri, auth=(user, password),
                                           notifications_min_severity="OFF")
        self.driver.verify_connectivity()
        self.catalogo = self.consultar("CATALOGO")[0]["modelos"]

    def consultar(self, nombre, **params):
        registros, _, _ = self.driver.execute_query(
            CONSULTAS[nombre], params, routing_="r", database_="neo4j")
        return [r.data() for r in registros]

    def cerrar(self):
        self.driver.close()


# ---------------------------------------------------------------------------
# Cliente del LLM (Ollama, API HTTP local)
# ---------------------------------------------------------------------------
class LLMOllama:
    def __init__(self, url=OLLAMA_URL, modelo=OLLAMA_MODEL):
        self.url = url.rstrip("/") + "/api/chat"
        self.modelo = modelo

    def chat(self, system, user, formato=None, temperatura=0.0):
        cuerpo = {
            "model": self.modelo,
            "stream": False,
            "options": {"temperature": temperatura, "seed": 42},
            "messages": [{"role": "system", "content": system},
                         {"role": "user", "content": user}],
        }
        if formato is not None:
            cuerpo["format"] = formato
        req = urllib.request.Request(self.url, data=json.dumps(cuerpo).encode("utf-8"),
                                     headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=300) as resp:
                return json.loads(resp.read().decode("utf-8"))["message"]["content"]
        except urllib.error.URLError as e:
            raise RuntimeError(f"No se pudo contactar a Ollama en {self.url}: {e}") from e


# ---------------------------------------------------------------------------
# Paso 1: EXTRACCION (LLM) + validacion en Python
# ---------------------------------------------------------------------------
def _json_estricto(texto):
    """El prompt exige JSON puro. Si viene texto alrededor, se rechaza (no se 'rescata')."""
    texto = texto.strip()
    if not (texto.startswith("{") and texto.endswith("}")):
        raise ValueError("La salida del extractor tiene texto fuera del JSON")
    return json.loads(texto)


def extraer_con_llm(llm, texto):
    ultimo_error = None
    for _ in range(2):                                   # un reintento si el JSON es invalido
        salida = llm.chat(PROMPT_EXTRACCION, f"Consulta: \"{texto}\"", formato=ESQUEMA_EXTRACCION)
        try:
            return _json_estricto(salida), salida
        except (ValueError, json.JSONDecodeError) as e:
            ultimo_error = e
    raise ValueError(f"El extractor no devolvio JSON valido: {ultimo_error}")


def extraer_sin_llm(texto):
    """Extractor de respaldo por reglas (se usa si Ollama no esta disponible: --sin-llm)."""
    t = texto.lower()
    notebooks = []
    for m in re.finditer(r"notebook[_ ]([a-z])\b|\b(?:la|el|a la|y la|que la|con la)\s+([a-z])\b", t):
        letra = (m.group(1) or m.group(2)).upper()
        nb = f"Notebook_{letra}"
        if nb not in notebooks:
            notebooks.append(nb)
    comprador = re.search(r"comprador[_ ]?(\d+)", t)
    req = re.search(r"req[_ ]?(\d+)", t)
    precio = re.search(r"(?:menos de|hasta|maximo|tope de)\s*(?:usd|u\$s|\$)?\s*(\d[\d\.]*)", t)
    if len(notebooks) >= 2 or "compar" in t or "antes que" in t:
        intencion = "comparar"
    elif any(k in t for k in ["barat", "costo-beneficio", "costo beneficio", "precio-calidad",
                              "relacion precio", "economic"]):
        intencion = "costo_beneficio"
    elif len(notebooks) == 1:
        intencion = "explicar_notebook"
    elif (any(k in t for k in ["recomend", "recomiend", "conviene", "ranking", "ofrezco", "opciones"])
          and any(k in t for k in ["comprador", "req", "pedido", "notebook", "equipo", "opciones"])):
        intencion = "recomendar"
    else:
        intencion = "desconocida"
    return {
        "intencion": intencion,
        "comprador_id": f"comprador_{comprador.group(1).zfill(2)}" if comprador else None,
        "requerimiento_id": f"req_{req.group(1).zfill(2)}" if req else None,
        "notebooks": notebooks,
        "filtros": {"precio_max_usd": float(precio.group(1).replace(".", "")) if precio else None,
                    "incluir_fuera_de_presupuesto": not ("dentro del presupuesto" in t or "sin pasarse" in t),
                    "solo_sin_alertas": "sin alertas" in t or "sin advertencias" in t},
        "conceptos": [],
        "evidencia": [],
        "requiere_aclaracion": intencion == "desconocida",
        "pregunta_aclaracion": None,
    }


def normalizar_notebook(nombre, catalogo):
    m = re.search(r"([A-Za-z])\s*$", (nombre or "").strip())
    if not m:
        return None
    candidato = f"Notebook_{m.group(1).upper()}"
    return candidato if candidato in catalogo else None


def validar_extraccion(datos, texto, bc, req_sesion):
    """Controles de Python sobre la salida del LLM. Devuelve (parametros, avisos, aclaracion)."""
    avisos = []
    t = texto.lower()

    intencion = datos.get("intencion")
    if intencion not in INTENCIONES:
        avisos.append(f"Intencion '{intencion}' fuera del esquema: se toma como 'desconocida'")
        intencion = "desconocida"

    # Notebooks: deben existir en el catalogo del grafo
    notebooks, desconocidas = [], []
    for nb in datos.get("notebooks") or []:
        norm = normalizar_notebook(nb, bc.catalogo)
        if norm and norm not in notebooks:
            notebooks.append(norm)
        elif not norm:
            desconocidas.append(nb)
    if desconocidas:
        return None, avisos, (f"No encuentro {', '.join(desconocidas)} en el catalogo cargado. "
                              f"Los modelos disponibles son: {', '.join(sorted(bc.catalogo))}.")

    # Requerimiento: el del texto, el del comprador nombrado o el de la sesion
    req = datos.get("requerimiento_id")
    if req and req.lower() not in t:
        avisos.append(f"requerimiento_id '{req}' no aparece en la consulta: se ignora")
        req = None
    comprador = datos.get("comprador_id")
    if not req and comprador:
        if re.sub(r"\D", "", comprador) and re.sub(r"\D", "", comprador).lstrip("0") in t:
            filas = bc.consultar("REQ_DE_COMPRADOR", comprador_id=comprador)
            if not filas:
                return None, avisos, f"No hay un pedido registrado para {comprador}."
            req = filas[0]["requerimiento"]
        else:
            avisos.append(f"comprador_id '{comprador}' no aparece en la consulta: se ignora")
    if not req:
        req = req_sesion
    if not req:
        return None, avisos, "¿Sobre que comprador o pedido es la consulta?"
    if not bc.consultar("L1_REQUERIMIENTO", requerimiento_id=req):
        return None, avisos, f"No existe el pedido {req} en la base de conocimiento."

    # Filtros: el tope de precio tiene que estar escrito en la consulta y ser razonable
    f = datos.get("filtros") or {}
    precio = f.get("precio_max_usd")
    if precio is not None:
        try:
            precio = float(precio)
        except (TypeError, ValueError):
            precio = None
        if precio is not None and str(int(precio)) not in re.sub(r"[\.\s]", "", t):
            avisos.append(f"Tope de precio {precio} sin respaldo literal en la consulta: se ignora")
            precio = None
        elif precio is not None and not (100 <= precio <= 10000):
            return None, avisos, (f"El tope de {precio:g} USD esta fuera del rango del catalogo "
                                  f"(precios en USD al 01/10/2026). ¿Podes confirmarlo?")
    filtros = {"precio_max_usd": precio,
               "incluir_fuera_de_presupuesto": bool(f.get("incluir_fuera_de_presupuesto", True)),
               "solo_sin_alertas": bool(f.get("solo_sin_alertas", False))}

    # Coherencia intencion / entidades
    if intencion == "comparar" and len(notebooks) == 1:
        avisos.append("Pidio comparar pero nombro una sola notebook: se explica esa notebook")
        intencion = "explicar_notebook"
    if intencion == "explicar_notebook" and len(notebooks) > 1:
        intencion = "comparar"
    if intencion in ("explicar_notebook", "comparar") and not notebooks:
        return None, avisos, "¿Sobre que notebook del catalogo es la consulta?"
    if intencion == "desconocida":
        pregunta = datos.get("pregunta_aclaracion") or (
            "No entendi la consulta. Puedo mostrar la recomendacion de un pedido, explicar por que "
            "una notebook quedo en su lugar, comparar dos notebooks o ordenarlas por costo-beneficio.")
        return None, avisos, pregunta

    return {"intencion": intencion, "requerimiento_id": req, "notebooks": notebooks,
            "filtros": filtros}, avisos, None


# ---------------------------------------------------------------------------
# Paso 2: CONSULTA a Neo4j segun la intencion
# ---------------------------------------------------------------------------
def consultar_grafo(bc, p):
    """Devuelve (evidencia, consultas_ejecutadas). La evidencia es lo unico que vera el LLM."""
    ejecutadas = []

    def q(nombre, **params):
        ejecutadas.append({"consulta": nombre, "parametros": params})
        return bc.consultar(nombre, **params)

    req = p["requerimiento_id"]
    f = p["filtros"]
    l1 = q("L1_REQUERIMIENTO", requerimiento_id=req)[0]
    evidencia = {"consulta_resuelta": p["intencion"], "pedido": l1}
    if not l1["preguntas_pendientes"]:
        del l1["preguntas_pendientes"]

    if l1["perfil_dominante"] == "indeterminado":
        evidencia["aviso"] = ("El perfil de uso del pedido es indeterminado: el sistema no evaluo "
                              "ninguna notebook hasta que el comprador responda la pregunta pendiente.")
    elif p["intencion"] == "recomendar":
        if l1.get("notebook_consultada"):
            evidencia["aviso"] = ("Es una consulta puntual por " + l1["notebook_consultada"] +
                                  ": el sistema no arma ranking, responde con la evaluacion de esa notebook.")
            evidencia["evaluacion"] = q("Q4_EXPLICAR_NOTEBOOK", requerimiento_id=req,
                                        modelo=l1["notebook_consultada"])
        else:
            evidencia["recomendacion"] = q("Q1_RECOMENDACION", requerimiento_id=req, **f)
            evidencia["otras_evaluadas"] = q("Q2_NO_PROPUESTAS", requerimiento_id=req)
            if evidencia["recomendacion"]:
                evidencia["criterio_desempate"] = q("Q6B_CRITERIO_DESEMPATE")[0]
            sin = q("Q3_SIN_ALTERNATIVA", requerimiento_id=req)
            if sin:
                evidencia["sin_alternativa"] = sin[0]["motivo"]
            if not evidencia["recomendacion"] and not sin:
                evidencia["aviso"] = "Ninguna notebook recomendada cumple los filtros pedidos."
            if any(f.values()) and f != {"precio_max_usd": None, "incluir_fuera_de_presupuesto": True,
                                         "solo_sin_alertas": False}:
                evidencia["filtros_aplicados"] = f
    elif p["intencion"] == "explicar_notebook":
        nb = p["notebooks"][0]
        ev = q("Q4_EXPLICAR_NOTEBOOK", requerimiento_id=req, modelo=nb)
        if not ev:
            evidencia["aviso"] = f"{nb} no fue evaluada para el pedido {req}."
        else:
            evidencia["evaluacion"] = ev[0]
            evidencia["traza_reglas"] = q("Q5_TRAZA", requerimiento_id=req, modelo=nb)
    elif p["intencion"] == "comparar":
        evidencia["comparacion"] = q("Q6_COMPARAR", requerimiento_id=req, modelos=p["notebooks"])
        evidencia["criterio_desempate"] = q("Q6B_CRITERIO_DESEMPATE")[0]
        faltan = set(p["notebooks"]) - {x["notebook"] for x in evidencia["comparacion"]}
        if faltan:
            evidencia["aviso"] = "No fueron evaluadas para este pedido: " + ", ".join(sorted(faltan))
    elif p["intencion"] == "costo_beneficio":
        evidencia["orden_costo_beneficio"] = q("Q7_COSTO_BENEFICIO", requerimiento_id=req, **f)
        if f["precio_max_usd"] is not None or not f["incluir_fuera_de_presupuesto"] or f["solo_sin_alertas"]:
            evidencia["filtros_aplicados"] = f
        if not evidencia["orden_costo_beneficio"]:
            evidencia["aviso"] = "Ninguna notebook recomendada cumple los filtros pedidos."

    par = q("Q8_PARAMETROS_SM4")[0]
    if par["sin_validar"]:
        evidencia["advertencia"] = (f"{par['sin_validar']} de las {par['etiquetas_sm4']} etiquetas difusas de SM4 "
                                    "son parametros provisionales, todavia no validados por el experto.")
    return evidencia, ejecutadas


# ---------------------------------------------------------------------------
# Paso 3: EXPLICACION (LLM) + verificacion REC-R11 + plantilla fija
# ---------------------------------------------------------------------------
def _numeros_de(obj, acc=None):
    acc = set() if acc is None else acc
    if isinstance(obj, bool) or obj is None:
        return acc
    if isinstance(obj, (int, float)):
        acc.add(round(float(obj), 3))
    elif isinstance(obj, str):
        for n in re.findall(r"\d+(?:[\.,]\d+)?", obj):
            acc.add(round(float(n.replace(",", ".")), 3))
    elif isinstance(obj, dict):
        for v in obj.values():
            _numeros_de(v, acc)
    elif isinstance(obj, list):
        for v in obj:
            _numeros_de(v, acc)
    return acc


def verificar_explicacion(texto, evidencia):
    """REC-R11: la explicacion no puede mencionar modelos, reglas ni numeros ausentes de la evidencia."""
    crudo = json.dumps(evidencia, ensure_ascii=False)
    problemas = []
    for nb in set(re.findall(r"Notebook[_ ][A-Z]\b", texto)):
        if nb.replace(" ", "_") not in crudo:
            problemas.append(f"menciona {nb}, que no esta en la evidencia")
    for regla in set(re.findall(r"\b(?:REC|REN|FZ|GM|INT)-R[D]?\d+\b", texto)):
        if regla not in crudo:
            problemas.append(f"cita la regla {regla}, que no esta en la evidencia")
    permitidos = _numeros_de(evidencia) | {1.0, 2.0, 3.0}       # 1, 2, 3: puestos del ranking
    texto_sin_ids = re.sub(r"\b(?:Notebook|comprador|req)[_ ]\w+|\b[A-Z]+-R[D]?\d+\b", "", texto)
    for n in re.findall(r"\d+(?:[\.,]\d+)?", texto_sin_ids):
        valor = round(float(n.replace(",", ".")), 3)
        if valor not in permitidos:
            problemas.append(f"usa el numero {n}, que no esta en la evidencia")
    return problemas


def plantilla_fija(evidencia):
    """Respuesta determinista (REC-R11, despues de 2 regeneraciones fallidas o en modo --sin-llm)."""
    lineas = []
    ped = evidencia["pedido"]
    if "recomendacion" in evidencia:
        lineas.append(f"Recomendacion para el pedido {ped['requerimiento']} "
                      f"(perfil {ped['perfil_dominante']}, presupuesto {ped['presupuesto_usd']:g} USD, "
                      f"prioridad {ped['prioridad']}):")
        for r in evidencia["recomendacion"]:
            lugar = "Fuera de presupuesto" if r["fuera_de_presupuesto"] else f"{r['puesto']}."
            grado = (f"[{r['grado_recomendacion']} ; {r['grado_recomendacion_max']}]"
                     if r["grado_recomendacion_max"] is not None else r["grado_recomendacion"])
            al = "; ".join(f"{a['tipo']} ({a['regla']})" for a in r["alertas"]) or "sin alertas"
            lineas.append(f"  {lugar} {r['notebook']} - {r['precio_usd']:g} USD - {r['estado']} "
                          f"(grado {grado}) - ampliabilidad {r['ampliabilidad_ram']} - {al}")
        if evidencia.get("otras_evaluadas"):
            lineas.append("  No figuran: " + "; ".join(f"{o['notebook']}: {o['estado']}"
                                                       for o in evidencia["otras_evaluadas"]))
    if "evaluacion" in evidencia:
        evs = evidencia["evaluacion"] if isinstance(evidencia["evaluacion"], list) else [evidencia["evaluacion"]]
        for e in evs:
            lineas.append(f"{e['notebook']} ({e['precio_usd']:g} USD) para el perfil {e['perfil']}: "
                          f"{e['estado']}, {e['en_la_recomendacion']}.")
            for titulo, clave in (("Cumple", "cumple"), ("No cumple", "no_cumple"),
                                  ("Falta verificar", "falta_verificar")):
                if e[clave]:
                    lineas.append(f"  {titulo}: " + "; ".join(e[clave]) + ".")
            if e["alertas"]:
                lineas.append("  Alertas: " + "; ".join(f"{a['tipo']} ({a['regla']})" for a in e["alertas"]) + ".")
    if "comparacion" in evidencia:
        for c in evidencia["comparacion"]:
            lineas.append(f"{c['notebook']}: {c['estado']}, grado {c['grado_recomendacion']}, "
                          f"ampliabilidad {c['ampliabilidad_ram']}, {c['en_la_recomendacion']}.")
        d = evidencia["criterio_desempate"]
        lineas.append(f"Criterio de desempate ({d['regla']}): {d['enunciado']} (margen {d['margen_empate']}).")
    if "orden_costo_beneficio" in evidencia:
        lineas.append("Orden por indice costo-beneficio (REC-R9):")
        for i, c in enumerate(evidencia["orden_costo_beneficio"], 1):
            lineas.append(f"  {i}. {c['notebook']} - {c['precio_usd']:g} USD - indice {c['indice_costo_beneficio']} "
                          f"- {c['estado']}")
    if evidencia.get("sin_alternativa"):
        lineas.append("Sin alternativa adecuada: " + evidencia["sin_alternativa"])
    if ped.get("preguntas_pendientes"):
        lineas.append("Pregunta pendiente para el comprador: " + " / ".join(ped["preguntas_pendientes"]))
    if evidencia.get("aviso"):
        lineas.append("Aviso: " + evidencia["aviso"])
    if evidencia.get("advertencia"):
        lineas.append("Advertencia: " + evidencia["advertencia"])
    return "\n".join(lineas)


def explicar(llm, consulta, evidencia):
    """Devuelve (texto, origen, intentos_rechazados)."""
    if llm is None:
        return plantilla_fija(evidencia), "plantilla fija (modo sin LLM)", []
    mensaje = ("CONSULTA:\n" + consulta + "\n\nEVIDENCIA:\n" +
               json.dumps(evidencia, ensure_ascii=False, indent=1, default=str))
    rechazados = []
    for intento in range(1 + MAX_REGENERACIONES):
        extra = ""
        if rechazados:
            extra = ("\n\nTu respuesta anterior fue rechazada por el verificador porque: "
                     + "; ".join(rechazados[-1]["problemas"]) + ". Reescribila sin esos datos.")
        texto = llm.chat(PROMPT_EXPLICACION, mensaje + extra, temperatura=0.2).strip()
        problemas = verificar_explicacion(texto, evidencia)
        if not problemas:
            return texto, f"LLM (intento {intento + 1})", rechazados
        rechazados.append({"texto": texto, "problemas": problemas})
    return plantilla_fija(evidencia), "plantilla fija (REC-R11: 2 regeneraciones rechazadas)", rechazados


# ---------------------------------------------------------------------------
# Orquestador (patron sandwich)
# ---------------------------------------------------------------------------
def orquestar(texto, bc, llm, req_sesion=None):
    traza = {"consulta_usuario": texto}
    t0 = time.time()
    if not texto or not texto.strip():
        traza["respuesta"] = "La consulta esta vacia. ¿Que queres saber sobre la recomendacion?"
        traza["origen_respuesta"] = "validacion"
        return traza
    if len(texto) > 1500:
        texto = texto[:1500]
        traza["aviso_longitud"] = "La consulta se recorto a 1500 caracteres"

    # 1. Extraccion
    try:
        if llm is None:
            datos = extraer_sin_llm(texto)
            traza["salida_extractor"] = json.dumps(datos, ensure_ascii=False)
        else:
            datos, crudo = extraer_con_llm(llm, texto)
            traza["salida_extractor"] = crudo
    except ValueError as e:
        traza["respuesta"] = ("No pude interpretar la consulta. ¿Podes reformularla nombrando el "
                              "comprador o la notebook?")
        traza["origen_respuesta"] = f"validacion ({e})"
        return traza
    traza["extraccion"] = datos

    # 2. Validacion
    params, avisos, aclaracion = validar_extraccion(datos, texto, bc, req_sesion)
    traza["avisos_validacion"] = avisos
    if aclaracion:
        traza["respuesta"] = aclaracion
        traza["origen_respuesta"] = "mensaje de aclaracion (no se consulta Neo4j)"
        return traza
    traza["parametros"] = params

    # 3. Consulta a Neo4j
    evidencia, ejecutadas = consultar_grafo(bc, params)
    traza["consultas_ejecutadas"] = ejecutadas
    traza["evidencia"] = evidencia

    # 4. Explicacion
    texto_resp, origen, rechazados = explicar(llm, texto, evidencia)
    traza["respuesta"] = texto_resp
    traza["origen_respuesta"] = origen
    traza["explicaciones_rechazadas"] = rechazados
    traza["segundos"] = round(time.time() - t0, 1)
    return traza


# ---------------------------------------------------------------------------
# Presentacion en terminal
# ---------------------------------------------------------------------------
def _titulo(t):
    print("\n" + "-" * 78 + f"\n{t}\n" + "-" * 78)


def mostrar(traza, verbose=True):
    _titulo("[1] CONSULTA DEL ASESOR")
    print(traza["consulta_usuario"])
    if "extraccion" in traza:
        _titulo("[2] EXTRACCION (salida del prompt de extraccion, JSON)")
        print(json.dumps(traza["extraccion"], ensure_ascii=False, indent=1))
        if traza.get("avisos_validacion"):
            print("Avisos de validacion: " + " | ".join(traza["avisos_validacion"]))
    if "parametros" in traza:
        _titulo("[3] CONSULTAS CYPHER EJECUTADAS EN NEO4J")
        for c in traza["consultas_ejecutadas"]:
            print(f"- {c['consulta']}  {json.dumps(c['parametros'], ensure_ascii=False)}")
            if verbose and c["consulta"] not in ("L1_REQUERIMIENTO", "Q8_PARAMETROS_SM4"):
                print("  " + CONSULTAS[c["consulta"]].strip().replace("\n", "\n  "))
        _titulo("[4] RESULTADO RECUPERADO (evidencia que recibe el LLM)")
        print(json.dumps(traza["evidencia"], ensure_ascii=False, indent=1, default=str))
    for r in traza.get("explicaciones_rechazadas", []):
        _titulo("[!] EXPLICACION RECHAZADA POR EL VERIFICADOR (REC-R11)")
        print(r["texto"])
        print("Motivos: " + "; ".join(r["problemas"]))
    _titulo(f"[5] RESPUESTA  <- {traza['origen_respuesta']}")
    print(traza["respuesta"])


# ---------------------------------------------------------------------------
# Casos de prueba de la PI4 (seccion 6 del informe)
# ---------------------------------------------------------------------------
CASOS = [
    ("CP1", "req_01", "¿Qué le recomendamos al comprador_01?"),
    ("CP2", "req_01", "¿Por qué la Notebook_E quedó afuera si tiene casi el mismo puntaje que la H?"),
    ("CP3", "req_01", "¿Por qué la H quedó antes que la B si la B es más barata?"),
    ("CP4", "req_01", "Contame qué pasa con la Notebook_M, ¿se la puedo ofrecer?"),
    ("CP5", "req_01", "Al comprador le importa mucho la plata: ¿cuál es la de mejor relación precio-calidad de menos de 900 dólares?"),
    ("CP6", "req_03", "¿Le sirve la Notebook_K al comprador_03?"),
    ("CP7", "req_02", "¿Qué le recomiendo al comprador_02?"),
    ("CP8", "req_01", "Recomendame una pizza de muzzarella para 3 personas"),
    ("CP9", "req_01", "¿Y la Notebook_Z le sirve?"),
    ("CP10", "req_01", "Quiero las opciones de menos de 5 dólares"),
]


def correr_casos(bc, llm, salida_json):
    resultados = []
    for cid, req, texto in CASOS:
        print("\n" + "=" * 78 + f"\n{cid}  (pedido de la sesion: {req})\n" + "=" * 78)
        traza = orquestar(texto, bc, llm, req_sesion=req)
        traza["caso"] = cid
        mostrar(traza, verbose=False)
        resultados.append(traza)
    with open(salida_json, "w", encoding="utf-8") as fh:
        json.dump(resultados, fh, ensure_ascii=False, indent=1, default=str)
    print(f"\nTrazas completas guardadas en {salida_json}")


# ---------------------------------------------------------------------------
# API opcional (para integrar en PG3)
# ---------------------------------------------------------------------------
def levantar_api(bc, llm):
    from fastapi import FastAPI
    from pydantic import BaseModel
    import uvicorn

    app = FastAPI(title="SM4 - Recomendacion explicable (PI4)")

    class Consulta(BaseModel):
        texto: str
        requerimiento_id: str | None = None

    @app.post("/consultar")
    def consultar(c: Consulta):
        return orquestar(c.texto, bc, llm, req_sesion=c.requerimiento_id)

    uvicorn.run(app, host="127.0.0.1", port=8000)


def main():
    ap = argparse.ArgumentParser(description="PI4 - SM4: LLM + Neo4j (patron sandwich)")
    ap.add_argument("--req", default="req_01", help="pedido de contexto de la sesion (default req_01)")
    ap.add_argument("--casos", action="store_true", help="corre los casos de prueba y guarda las trazas")
    ap.add_argument("--sin-llm", action="store_true", help="extractor por reglas + plantilla fija")
    ap.add_argument("--api", action="store_true", help="expone POST /consultar con FastAPI")
    ap.add_argument("--salida", default="ejecucion_casos_PI4.json")
    args = ap.parse_args()

    bc = BaseConocimiento()
    llm = None if args.sin_llm else LLMOllama()
    print(f"Neo4j: {NEO4J_URI} | catalogo: {len(bc.catalogo)} notebooks | "
          f"LLM: {'ninguno (respaldo)' if llm is None else 'Ollama ' + OLLAMA_MODEL}")
    try:
        if args.api:
            levantar_api(bc, llm)
        elif args.casos:
            correr_casos(bc, llm, args.salida)
        else:
            print(f"Pedido de la sesion: {args.req}. Escribi tu consulta ('salir' para terminar).")
            while True:
                try:
                    texto = input("\nAsesor> ").strip()
                except (EOFError, KeyboardInterrupt):
                    break
                if texto.lower() in ("salir", "exit", "quit"):
                    break
                m = re.match(r"^/pedido\s+(req_\d+)$", texto)
                if m:
                    args.req = m.group(1)
                    print(f"Pedido de la sesion: {args.req}")
                    continue
                mostrar(orquestar(texto, bc, llm, req_sesion=args.req))
    finally:
        bc.cerrar()


if __name__ == "__main__":
    sys.exit(main())
