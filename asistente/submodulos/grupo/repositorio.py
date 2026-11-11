"""GRUPO · Repositorio: L3 y L4 del bloque 13 (traza y parámetros).

L3 suma la validación de cada regla. L4 suma los (:Parametro) crisp a las etiquetas difusas.

Origen del conocimiento (PG3-05): las (:Regla) no guardan `fuente` en el grafo, así que el origen
se busca en otros nodos: `origen_reglas` (los parámetros que respaldan cada regla y la consulta al
técnico que los valida), `origen_notebook` (precio y autonomía) y `origen_parametros`.
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
    # Un parámetro respalda una regla si (a) es el `centros_y_sigmas_<variable>` de la variable de su
    # consecuente (solo esa variable, no las del antecedente) o (b) su `origen` nombra el id de la regla.
    # El borde de palabra (\b) evita atribuir REC-R1 a un origen que dice REC-R15.
    # Además, una `ConsultaExperto` que valida la regla directamente (p. ej., CE-FZ-R2-R3) es parte de su origen:
    # sale con `parametro` nulo.
    "origen_reglas": r"""
CALL {
  UNWIND $reglas AS rid
  MATCH (q:Regla {id: rid})
  OPTIONAL MATCH (p:Parametro)
  WHERE p.nombre = 'centros_y_sigmas_' + split(coalesce(q.consecuente, ''), ' = ')[0]
     OR p.origen =~ ('.*\\b' + rid + '\\b.*')
  OPTIONAL MATCH (ce:ConsultaExperto)-[:VALIDA]->(p)
  RETURN rid AS regla, p.nombre AS parametro, p.origen AS origen, p.estado_validacion AS validacion,
         ce.id AS consulta_experto, ce.estado AS estado_consulta
  UNION ALL
  UNWIND $reglas AS rid
  MATCH (ce:ConsultaExperto)-[:VALIDA]->(:Regla {id: rid})
  RETURN rid AS regla, null AS parametro, null AS origen, null AS validacion,
         ce.id AS consulta_experto, ce.estado AS estado_consulta
}
RETURN regla, parametro, origen, validacion, consulta_experto, estado_consulta
ORDER BY regla, parametro, consulta_experto
""",
    # La fuente de la autonomía solo cuenta si la autonomía existe: `Bateria.fuente` está aunque el dato sea desconocido.
    "origen_notebook": """
MATCH (n:Notebook {modelo:$modelo})
OPTIONAL MATCH (n)-[:POSEE]->(b:Bateria)
RETURN n.fuente_precio AS fuente_precio,
       CASE WHEN b.tipo_dato = 'desconocida' THEN null ELSE b.fuente END AS fuente_autonomia
""",
    "origen_parametros": """
MATCH (e:EtiquetaDifusa)<-[:TIENE_ETIQUETA]-(v:VariableDifusa)
RETURN v.nombre + '.' + e.nombre AS nombre, e.fuente AS origen
UNION ALL
MATCH (p:Parametro)
RETURN p.nombre AS nombre, p.origen AS origen
""",
}


def existe_evaluacion(grafo, requerimiento_id: str, modelo: str):
    return leer_consulta(grafo, SM, "existe_evaluacion", CONSULTAS["existe_evaluacion"],
                         {"requerimiento_id": requerimiento_id, "modelo": modelo})


def traza(grafo, requerimiento_id: str, modelo: str):
    return leer_consulta(grafo, SM, "L3", CONSULTAS["L3"], {"requerimiento_id": requerimiento_id, "modelo": modelo})


def parametros(grafo):
    return leer_consulta(grafo, SM, "L4", CONSULTAS["L4"], {})


def origen_reglas(grafo, reglas: list[str]):
    return leer_consulta(grafo, SM, "origen_reglas", CONSULTAS["origen_reglas"], {"reglas": reglas})


def origen_notebook(grafo, modelo: str):
    return leer_consulta(grafo, SM, "origen_notebook", CONSULTAS["origen_notebook"], {"modelo": modelo})


def origen_parametros(grafo):
    return leer_consulta(grafo, SM, "origen_parametros", CONSULTAS["origen_parametros"], {})
