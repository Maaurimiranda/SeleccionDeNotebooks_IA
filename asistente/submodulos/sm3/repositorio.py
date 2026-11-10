"""SM3 · Repositorio: consulta unificada (gráfica, movilidad, mixta) y consulta por modelo.

Base: docs/fuentes/SM3/sm3_asistente.py, ahora filtrada por el pedido
(c.id = $requerimiento_id): antes traía las evaluaciones de todos los pedidos.
El ORDER BY sale de una lista blanca (nunca del usuario ni del LLM).
"""
from asistente.submodulos.comun import leer_consulta

SM = "SM3"
LIMITE_RESULTADOS = 5

_MATCH_PEDIDO = """
MATCH (c:Requerimiento {id:$requerimiento_id})-[:EVALUA]->(ev:Evaluacion)-[:SOBRE]->(n:Notebook)
MATCH (n)-[:POSEE]->(g:GPU)-[:ES_DE_GAMA]->(gg:GamaGPU)
MATCH (n)-[:POSEE]->(p:Pantalla)
MATCH (n)-[:POSEE]->(b:Bateria)
"""

_FILTROS = """
WHERE ($dedicada    IS NULL OR g.dedicada = $dedicada)
  AND ($gama_min    IS NULL OR gg.indice >= $gama_min)
  AND ($peso_max    IS NULL OR n.peso_kg <= $peso_max)
  AND ($bateria_min IS NULL OR b.autonomia_usada_h >= $bateria_min)
  AND ($srgb_min    IS NULL OR p.srgb >= $srgb_min)
"""

_POR_MODELO = "WHERE n.modelo = $modelo\n"

# Reglas de SM3: movilidad (desde la notebook) y gráfica (desde la evaluación del pedido)
_BLOQUE_COMUN = """
OPTIONAL MATCH (x)-[act:ACTIVA]->(q:Regla {submodulo:'SM3'})
WHERE x = n OR x = ev
WITH c, ev, n, g, gg, p, b,
     collect(DISTINCT CASE WHEN q IS NULL THEN null ELSE
       {id:q.id, fuerza:act.fuerza, validacion:q.estado_validacion} END) AS reglas
OPTIONAL MATCH (al:Alerta {submodulo_origen:'SM3'})
WHERE EXISTS { MATCH (ev)-[:GENERA]->(al) } OR EXISTS { MATCH (n)-[:GENERA]->(al) }
WITH c, ev, n, g, gg, p, b, reglas,
     collect(DISTINCT CASE WHEN al IS NULL THEN null ELSE
       {codigo:al.regla_origen, texto:al.mensaje} END) AS alertas
"""

_RETURN = """
RETURN n.modelo AS notebook, ev.perfil AS perfil, n.precio_usd AS precio_usd,
       gg.nombre AS gama_gpu, gg.indice AS gama_gpu_indice, g.dedicada AS gpu_dedicada,
       ev.grado_gpu AS grado_gpu, ev.margen_gama AS margen_gama, ev.adecuacion_grafica AS adecuacion_grafica,
       n.adecuacion_movilidad AS adecuacion_movilidad, n.movilidad_etiqueta AS movilidad_etiqueta,
       n.peso_kg AS peso_kg, b.autonomia_usada_h AS autonomia_h, b.tipo_dato AS autonomia_tipo_dato,
       p.srgb AS srgb, reglas, alertas"""

# Lista blanca de ordenamientos. coalesce manda los null al final (en un DESC irían primero).
ORDENES: dict[str, str] = {
    "grafica": "coalesce(adecuacion_grafica, -1) DESC, gama_gpu_indice DESC, precio_usd ASC",
    "movilidad": "coalesce(adecuacion_movilidad, -1) DESC, peso_kg ASC",
    "mixta": "(coalesce(adecuacion_grafica, 0) + coalesce(adecuacion_movilidad, 0)) DESC, precio_usd ASC",
}

CONSULTAS: dict[str, str] = {
    **{f"unificada_{o}": _MATCH_PEDIDO + _FILTROS + _BLOQUE_COMUN + _RETURN + f"\nORDER BY {orden}\nLIMIT $limite"
       for o, orden in ORDENES.items()},
    "modelo": _MATCH_PEDIDO + _POR_MODELO + _BLOQUE_COMUN + _RETURN
              + ",\n       b.autonomia_medida_h AS autonomia_medida_h, b.autonomia_declarada_h AS autonomia_declarada_h,"
              + "\n       b.fuente AS fuente_bateria, p.resolucion AS resolucion, p.refresco_hz AS refresco_hz,"
              + "\n       g.vram_gb AS vram_gb, n.fuente_precio AS fuente_precio",
}

FILTROS = ("dedicada", "gama_min", "peso_max", "bateria_min", "srgb_min")


def buscar(grafo, requerimiento_id: str, orden: str, filtros: dict, limite: int = LIMITE_RESULTADOS):
    nombre = f"unificada_{orden}"
    parametros = {"requerimiento_id": requerimiento_id, **{k: filtros.get(k) for k in FILTROS}, "limite": limite}
    return leer_consulta(grafo, SM, nombre, CONSULTAS[nombre], parametros)


def ficha(grafo, requerimiento_id: str, modelo: str):
    return leer_consulta(grafo, SM, "modelo", CONSULTAS["modelo"],
                         {"requerimiento_id": requerimiento_id, "modelo": modelo})
