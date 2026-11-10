"""GRUPO · Repositorio: L3 y L4 del bloque 13 (traza y parámetros).

L3 suma la validación y la fuente de cada regla (si la propiedad existe).
L4 suma los (:Parametro) crisp a las etiquetas difusas.
"""
from asistente.submodulos.comun import leer_consulta

SM = "GRUPO"

CONSULTAS: dict[str, str] = {
    "existe_evaluacion": """
MATCH (c:Requerimiento {id:$requerimiento_id})-[:EVALUA]->(ev:Evaluacion)-[:SOBRE]->(n:Notebook {modelo:$modelo})
RETURN count(ev) AS evaluaciones
""",
    "L3": """
MATCH (c:Requerimiento {id:$requerimiento_id})-[:EVALUA]->(ev:Evaluacion)-[:SOBRE]->(n:Notebook {modelo:$modelo})
OPTIONAL MATCH (c)-[:INCLUYE]->(a:Actividad)
WITH c, ev, n, collect(a) AS acts
UNWIND [c, ev, n] + acts AS origen
OPTIONAL MATCH (origen)-[:TIENE_LECTURA*0..1]->(x)-[act:ACTIVA]->(q:Regla)
WITH origen, x, act, q WHERE q IS NOT NULL
RETURN q.submodulo AS submodulo, q.id AS regla, q.tipo AS tipo,
       coalesce(q.antecedente, q.enunciado) AS antecedente, q.consecuente AS consecuente,
       labels(origen)[0] AS sobre, x.escenario AS escenario, act.fuerza AS fuerza,
       q.estado_validacion AS validacion, q.fuente AS fuente
ORDER BY submodulo, regla, escenario
""",
    "L4": """
MATCH (e:EtiquetaDifusa)<-[:TIENE_ETIQUETA]-(v:VariableDifusa)
RETURN v.submodulo AS submodulo, v.nombre + '.' + e.nombre AS nombre,
       {centro:e.centro, sigma:e.sigma} AS valor, e.estado_validacion AS estado_validacion,
       'etiqueta_difusa' AS tipo
UNION ALL
MATCH (p:Parametro)
RETURN p.submodulo AS submodulo, p.nombre AS nombre, p.valor AS valor,
       p.estado_validacion AS estado_validacion, 'parametro' AS tipo
""",
}


def existe_evaluacion(grafo, requerimiento_id: str, modelo: str):
    return leer_consulta(grafo, SM, "existe_evaluacion", CONSULTAS["existe_evaluacion"],
                         {"requerimiento_id": requerimiento_id, "modelo": modelo})


def traza(grafo, requerimiento_id: str, modelo: str):
    return leer_consulta(grafo, SM, "L3", CONSULTAS["L3"], {"requerimiento_id": requerimiento_id, "modelo": modelo})


def parametros(grafo):
    return leer_consulta(grafo, SM, "L4", CONSULTAS["L4"], {})
