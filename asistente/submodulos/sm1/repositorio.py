"""SM1 · Repositorio: L1 del bloque 13 (requerimiento formal interpretado).

Se agregan grado_min/grado_max por si un perfil queda como rango (D-09).
"""
from asistente.submodulos.comun import leer_consulta

SM = "SM1"

CONSULTAS: dict[str, str] = {
    "L1": """
MATCH (c:Requerimiento {id:$requerimiento_id})
OPTIONAL MATCH (c)-[r:PERTENECE]->(p:Perfil)
OPTIONAL MATCH (c)-[:REQUIERE_ACLARACION]->(q:Pregunta)
RETURN c.id AS requerimiento, c.presupuesto_usd AS presupuesto, c.prioridad AS prioridad,
       c.perfil_dominante AS perfil_dominante,
       [x IN collect(DISTINCT {perfil:p.codigo, grado:r.grado, grado_min:r.grado_min, grado_max:r.grado_max,
                impone_requisitos:r.impone_requisitos, en_frontera:r.en_frontera}) WHERE x.perfil IS NOT NULL] AS perfiles,
       c.intensidad_grafica AS intensidad, c.intensidad_valor AS intensidad_valor,
       collect(DISTINCT q.texto) AS preguntas_pendientes
""",
}


def interpretacion(grafo, requerimiento_id: str):
    return leer_consulta(grafo, SM, "L1", CONSULTAS["L1"], {"requerimiento_id": requerimiento_id})
