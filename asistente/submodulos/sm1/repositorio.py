"""SM1 · Repositorio: L1 del bloque 13 (requerimiento formal interpretado) y escritura del pedido nuevo.

Se agregan grado_min/grado_max por si un perfil queda como rango (D-09).

La escritura (D-08) es la única del sistema: alta de un pedido (`registrar`) y aclaración del mismo pedido
(`aclarar`). Las dos van en UNA transacción junto con la inferencia de cypher/10 a 40 para ese `$req`
(asistente/inferencia.py): si algo falla, no queda un pedido a medias.
"""
import threading

from asistente import inferencia
from asistente.submodulos.comun import leer_consulta

SM = "SM1"
PRIMER_ID_NUEVO = 101          # req_101 en adelante: req_04 y req_05 quedan para PG3-25 (D-03, D-11)
ORIGEN_CONSULTA = "consulta"   # marca de los pedidos creados desde una consulta (los borra scripts/limpiar_pedidos)
_candado = threading.Lock()    # dos altas a la vez no pueden tomar el mismo id

CONSULTAS: dict[str, str] = {
    "L1": """
MATCH (c:Requerimiento {id:$requerimiento_id})
OPTIONAL MATCH (c)-[r:PERTENECE]->(p:Perfil)
OPTIONAL MATCH (c)-[:REQUIERE_ACLARACION]->(q:Pregunta) WHERE coalesce(q.estado, 'pendiente') = 'pendiente'
RETURN c.id AS requerimiento, c.presupuesto_usd AS presupuesto, c.prioridad AS prioridad,
       c.perfil_dominante AS perfil_dominante,
       [x IN collect(DISTINCT {perfil:p.codigo, grado:r.grado, grado_min:r.grado_min, grado_max:r.grado_max,
                impone_requisitos:r.impone_requisitos, en_frontera:r.en_frontera}) WHERE x.perfil IS NOT NULL] AS perfiles,
       c.intensidad_grafica AS intensidad, c.intensidad_valor AS intensidad_valor,
       collect(DISTINCT q.texto) AS preguntas_pendientes
""",
    "VOCABULARIO": """
MATCH (e:ExpresionFrecuencia) WITH collect({texto:e.texto, horas:e.horas_ref}) AS expresiones
MATCH (j:Juego) WITH expresiones, collect(j.nombre) AS juegos
MATCH (n:Notebook) RETURN expresiones, juegos, collect(n.modelo) AS catalogo
""",
    "ULTIMO_ID": """
MATCH (c:Requerimiento) WHERE c.id =~ 'req_[0-9]+'
RETURN max(toInteger(substring(c.id, 4))) AS ultimo
""",
    "PEDIDO": """
MATCH (c:Requerimiento {id:$requerimiento_id})
OPTIONAL MATCH (c)-[:INCLUYE]->(a:Actividad)
OPTIONAL MATCH (a)-[:USA]->(j:Juego)
OPTIONAL MATCH (c)-[:REQUIERE_ACLARACION]->(q:Pregunta) WHERE coalesce(q.estado, 'pendiente') = 'pendiente'
WITH c, a, collect(DISTINCT j.nombre) AS juegos, collect(DISTINCT q.texto) AS preguntas
RETURN c.id AS requerimiento, c.presupuesto_usd AS presupuesto_usd, c.prioridad AS prioridad,
       c.texto_pedido AS texto_pedido, c.origen AS origen,
       collect(CASE WHEN a IS NULL THEN null ELSE {id:a.id, descripcion:a.descripcion, perfil:a.perfil_asociado,
               dedicacion_h:a.dedicacion_h, dedicacion_origen:a.dedicacion_origen, expresion:a.expresion,
               juegos:juegos} END) AS actividades,
       head(collect(preguntas)) AS preguntas
""",
}

# --- Escritura -------------------------------------------------------------------------------
ALTA_REQUERIMIENTO = """
MERGE (p:Comprador {id:$comprador})
ON CREATE SET p.carrera_origen = 'desconocida', p.origen = $origen
MERGE (c:Requerimiento {id:$req})
SET c.presupuesto_usd = $presupuesto, c.prioridad = $prioridad, c.usa_monitor_externo = $monitor,
    c.moneda_original = $moneda, c.texto_pedido = $texto, c.origen = $origen, c.creado = datetime()
FOREACH (_ IN CASE WHEN $notebook IS NULL THEN [] ELSE [1] END | SET c.notebook_consultada = $notebook)
MERGE (p)-[:FORMULA {fecha:date()}]->(c)
"""

# Mismas propiedades y relaciones que las actividades de cypher/02_instancias.cypher, pero con un id
# propio del pedido (para no pisar act_programar y compañía) y la dedicación calculada igual.
ALTA_ACTIVIDADES = """
MATCH (c:Requerimiento {id:$req})
UNWIND $actividades AS x
MERGE (a:Actividad {id: $req + '_' + x.id})
SET a.descripcion = x.descripcion, a.tipo = x.tipo, a.perfil_asociado = x.perfil,
    a.expresion = x.expresion, a.horas_explicitas_semana = x.horas, a.fragmento_literal = x.fragmento,
    a.requerimiento = $req
MERGE (c)-[:INCLUYE]->(a)
WITH a, x
OPTIONAL MATCH (p:Perfil {codigo:x.perfil})
FOREACH (_ IN CASE WHEN p IS NULL THEN [] ELSE [1] END | MERGE (a)-[:APUNTA_A]->(p))
WITH a, x
OPTIONAL MATCH (e:ExpresionFrecuencia {texto:x.expresion})
FOREACH (_ IN CASE WHEN e IS NULL THEN [] ELSE [1] END | MERGE (a)-[:EXPRESADA_COMO]->(e))
SET a.dedicacion_h = coalesce(a.horas_explicitas_semana, e.horas_ref),
    a.dedicacion_origen = CASE
      WHEN a.horas_explicitas_semana IS NOT NULL THEN 'declarada'
      WHEN e IS NOT NULL THEN 'lexico'
      ELSE 'desconocida' END
WITH a, x
UNWIND x.juegos AS nombre
MATCH (j:Juego {nombre:nombre})
MERGE (a)-[:USA]->(j)
"""

CONSULTA_POR = """
MATCH (c:Requerimiento {id:$req}), (n:Notebook {modelo:$notebook})
MERGE (c)-[:CONSULTA_POR]->(n)
"""

PREGUNTAS = """
MATCH (c:Requerimiento {id:$req})
UNWIND $preguntas AS t
MERGE (c)-[:REQUIERE_ACLARACION]->(q:Pregunta {requerimiento:$req, texto:t})
SET q.estado = 'pendiente', q.origen = 'SM1 alta'
"""

# Aclaración (D-08): se completa el MISMO pedido y se vuelve a inferir.
ACTUALIZAR = """
MATCH (c:Requerimiento {id:$req})
SET c.presupuesto_usd = coalesce($presupuesto, c.presupuesto_usd),
    c.moneda_original = coalesce($moneda, c.moneda_original),
    c.prioridad = CASE WHEN $prioridad IS NULL OR $prioridad = 'ninguna' THEN c.prioridad ELSE $prioridad END,
    c.aclaracion = 'respondida',
    c.texto_aclaracion = trim(coalesce(c.texto_aclaracion, '') + ' ' + $texto)
"""

HORAS_ACTIVIDADES = """
MATCH (c:Requerimiento {id:$req})-[:INCLUYE]->(a:Actividad)
WHERE a.id IN $ids
SET a.horas_explicitas_semana = $horas, a.dedicacion_h = $horas, a.dedicacion_origen = 'declarada'
"""

RESPONDER_PREGUNTAS = """
MATCH (c:Requerimiento {id:$req})-[:REQUIERE_ACLARACION]->(q:Pregunta)
WHERE coalesce(q.estado, 'pendiente') = 'pendiente'
SET q.estado = 'respondida', q.respuesta = $texto
"""

# Borra lo que la inferencia deriva del pedido, para recalcularlo sin restos de la versión anterior.
# Las actividades, las preguntas y el pedido quedan.
BORRAR_DERIVADOS = [
    """
MATCH (c:Requerimiento {id:$req})-[:EVALUA]->(ev:Evaluacion)
OPTIONAL MATCH (ev)-[:TIENE_LECTURA]->(l:Lectura)
OPTIONAL MATCH (ev)-[:GENERA]->(al:Alerta)
DETACH DELETE l, al, ev
""",
    """
MATCH (c:Requerimiento {id:$req})
OPTIONAL MATCH (c)-[:RECIBE]->(rec:Recomendacion)
OPTIONAL MATCH (c)-[:GENERA]->(al:Alerta)
DETACH DELETE rec, al
""",
    """
MATCH (c:Requerimiento {id:$req})-[r:PERTENECE|TIENE_PERFIL_DOMINANTE|ACTIVA]->()
DELETE r
""",
    """
MATCH (c:Requerimiento {id:$req})
REMOVE c.perfil_dominante, c.grado_perfil_dominante, c.intensidad_valor, c.intensidad_grafica,
       c.mu_int_baja, c.mu_int_media, c.mu_int_alta
""",
]

BORRAR_PEDIDOS_CONSULTA = """
MATCH (c:Requerimiento {origen:$origen})
WHERE $req IS NULL OR c.id = $req
OPTIONAL MATCH (c)-[:EVALUA]->(ev:Evaluacion)
OPTIONAL MATCH (ev)-[:TIENE_LECTURA]->(l:Lectura)
OPTIONAL MATCH (ev)-[:GENERA]->(alev:Alerta)
OPTIONAL MATCH (c)-[:RECIBE]->(rec:Recomendacion)
OPTIONAL MATCH (c)-[:GENERA]->(al:Alerta)
OPTIONAL MATCH (c)-[:INCLUYE]->(a:Actividad)
OPTIONAL MATCH (c)-[:REQUIERE_ACLARACION]->(q:Pregunta)
OPTIONAL MATCH (p:Comprador {origen:$origen})-[:FORMULA]->(c)
WITH c,
     [x IN collect(DISTINCT l) + collect(DISTINCT alev) + collect(DISTINCT ev) + collect(DISTINCT rec)
           + collect(DISTINCT al) + collect(DISTINCT a) + collect(DISTINCT q) + collect(DISTINCT p) WHERE x IS NOT NULL] AS nodos
FOREACH (n IN nodos | DETACH DELETE n)
DETACH DELETE c
RETURN count(*) AS borrados
"""


# --- Lectura ---------------------------------------------------------------------------------
def interpretacion(grafo, requerimiento_id: str):
    return leer_consulta(grafo, SM, "L1", CONSULTAS["L1"], {"requerimiento_id": requerimiento_id})


def vocabulario(grafo) -> dict:
    filas = grafo.leer(CONSULTAS["VOCABULARIO"])
    f = filas[0] if filas else {}
    horas = {e["texto"]: e["horas"] for e in f.get("expresiones") or []}
    return {"expresiones": sorted(horas), "horas_expresion": horas, "juegos": sorted(f.get("juegos") or []),
            "catalogo": sorted(f.get("catalogo") or [])}


def pedido(grafo, requerimiento_id: str):
    return leer_consulta(grafo, SM, "PEDIDO", CONSULTAS["PEDIDO"], {"requerimiento_id": requerimiento_id})


# --- Escritura -------------------------------------------------------------------------------
def _lote_inferencia() -> list[tuple[str, str]]:
    return [(f"{a}:{l}", t) for a, l, t in inferencia.sentencias_inferencia()]


def registrar(grafo, datos: dict, texto: str) -> dict:
    """Alta del pedido + inferencia para ese pedido, en una transacción. Devuelve el registro de la traza."""
    with _candado:
        ultimo = (grafo.leer(CONSULTAS["ULTIMO_ID"]) or [{}])[0].get("ultimo") or 0
        req = f"req_{max(ultimo + 1, PRIMER_ID_NUEVO)}"
        parametros = {
            "req": req, "comprador": f"comprador_{req}", "origen": ORIGEN_CONSULTA, "texto": texto,
            "presupuesto": datos["presupuesto_usd"], "prioridad": datos["prioridad"],
            "monitor": datos["usa_monitor_externo"], "moneda": datos["moneda_original"],
            "notebook": datos.get("notebook_consultada"), "actividades": datos["actividades"],
            "preguntas": datos.get("preguntas") or [],
        }
        lote = [("alta:requerimiento", ALTA_REQUERIMIENTO), ("alta:actividades", ALTA_ACTIVIDADES),
                ("alta:preguntas", PREGUNTAS)]
        if datos.get("notebook_consultada"):
            lote.append(("alta:consulta_por", CONSULTA_POR))
        lote += _lote_inferencia()
        grafo.escribir_lote(lote, parametros)
    return {"nombre": f"{SM}.ALTA", "cypher": "\n".join(t.strip() for _, t in lote[:4]) +
            f"\n// + inferencia de cypher/10 a 40 con $req ({len(lote) - 4} sentencias)",
            "parametros": parametros, "filas": [{"requerimiento_id": req}]}


def aclarar(grafo, req: str, datos: dict, texto: str, ids_sin_horas: list[str], horas: float | None) -> dict:
    """Completa el MISMO pedido, marca sus preguntas como respondidas y lo vuelve a inferir (una transacción)."""
    parametros = {
        "req": req, "texto": texto, "presupuesto": datos.get("presupuesto_usd"),
        "moneda": datos.get("moneda_original"), "prioridad": datos.get("prioridad"),
        "actividades": datos.get("actividades") or [], "preguntas": datos.get("preguntas") or [],
        "ids": ids_sin_horas, "horas": horas,
    }
    lote = [("aclarar:respuestas", RESPONDER_PREGUNTAS), ("aclarar:pedido", ACTUALIZAR)]
    if datos.get("actividades"):
        lote.append(("aclarar:actividades", ALTA_ACTIVIDADES))
    if horas is not None and ids_sin_horas:
        lote.append(("aclarar:horas", HORAS_ACTIVIDADES))
    lote.append(("aclarar:preguntas", PREGUNTAS))
    lote += [(f"aclarar:borrar_derivados_{i}", t) for i, t in enumerate(BORRAR_DERIVADOS, 1)]
    n = len(lote)
    lote += _lote_inferencia()
    grafo.escribir_lote(lote, parametros)
    return {"nombre": f"{SM}.ACLARAR", "cypher": "\n".join(t.strip() for _, t in lote[:n]) +
            f"\n// + inferencia de cypher/10 a 40 con $req ({len(lote) - n} sentencias)",
            "parametros": parametros, "filas": [{"requerimiento_id": req}]}


def borrar_pedidos_consulta(grafo, req: str | None = None) -> int:
    """Borra los pedidos creados desde consultas (origen 'consulta') y todo lo que cuelga de ellos.
    Nunca toca req_01..req_03, que no tienen esa marca."""
    filas = grafo.escribir(BORRAR_PEDIDOS_CONSULTA, {"origen": ORIGEN_CONSULTA, "req": req})
    return sum(f["borrados"] for f in filas)
