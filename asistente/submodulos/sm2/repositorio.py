"""SM2 · Repositorio: Cypher fijo sobre las (:Evaluacion) del canónico.

C2 y C1 vienen del bloque 11, portadas a `ev.*` (contexto SM2 §14-K) y sin MERGE.
Acá no se arma evidencia: solo se ejecutan las consultas.
"""
from asistente.submodulos.comun import leer_consulta

SM = "SM2"

CONSULTAS: dict[str, str] = {
    # C2 · riesgo de obsolescencia por RAM (FZ-R1..R5), con filtros opcionales
    "C2": """
MATCH (c:Requerimiento {id:$requerimiento_id})-[:EVALUA]->(ev:Evaluacion)-[:SOBRE]->(n:Notebook)-[:POSEE]->(r:RAM)
WHERE ($modelos IS NULL OR n.modelo IN $modelos)
  AND ($tipo_ram IS NULL OR r.tipo = $tipo_ram)
  AND ($etiqueta IS NULL OR ev.riesgo_etiqueta = $etiqueta)
CALL {
  WITH ev
  OPTIONAL MATCH (ev)-[:TIENE_LECTURA*0..1]->(x)-[act:ACTIVA]->(q:Regla)
  WHERE q.id STARTS WITH 'FZ-R' AND act.fuerza IS NOT NULL
  RETURN collect(DISTINCT CASE WHEN q IS NULL THEN null ELSE
         {id:q.id, fuerza:act.fuerza, escenario:x.escenario, validacion:q.estado_validacion} END) AS reglas
}
CALL {
  WITH ev, n
  OPTIONAL MATCH (al:Alerta {submodulo_origen:'SM2'})
  WHERE EXISTS { MATCH (ev)-[:GENERA]->(al) } OR EXISTS { MATCH (n)-[:GENERA]->(al) }
  RETURN collect(DISTINCT CASE WHEN al IS NULL THEN null ELSE
         {codigo:al.regla_origen, tipo:al.tipo, texto:al.mensaje} END) AS alertas
}
RETURN n.modelo AS notebook, ev.perfil AS perfil, r.ram_gb AS ram_gb, r.tipo AS tipo_ram,
       r.ampliabilidad AS ampliabilidad, ev.suficiencia_rho AS suficiencia_rho,
       ev.indice_ampliabilidad AS indice_ampliabilidad,
       ev.riesgo_valor AS riesgo_valor, ev.riesgo_min AS riesgo_min, ev.riesgo_max AS riesgo_max,
       ev.riesgo_etiqueta AS riesgo_etiqueta, reglas, alertas
ORDER BY coalesce(ev.riesgo_max, ev.riesgo_valor) DESC, notebook
""",
    # C1 · excluyente de virtualización (REN-R1 + REC-R3), leído de la evaluación
    "C1": """
MATCH (c:Requerimiento {id:$requerimiento_id})-[:EVALUA]->(ev:Evaluacion)-[:SOBRE]->(n:Notebook)-[:POSEE]->(cpu:CPU)
WHERE ($modelos IS NULL OR n.modelo IN $modelos)
OPTIONAL MATCH (c)-[:TIENE_PERFIL_DOMINANTE]->(p:Perfil)-[:EXIGE]->(req:Requisito {criterio:'virtualizacion'})
RETURN n.modelo AS notebook, ev.perfil AS perfil, coalesce(req.es_excluyente, false) AS excluyente,
       cpu.virtualizacion AS virtualizacion_cpu, ev.excluyente_virtualizacion AS resultado,
       ev.estado AS estado
ORDER BY resultado, notebook
""",
}


def riesgo_ram(grafo, requerimiento_id: str, modelos=None, etiqueta=None, tipo_ram=None):
    return leer_consulta(grafo, SM, "C2", CONSULTAS["C2"], {
        "requerimiento_id": requerimiento_id, "modelos": modelos, "etiqueta": etiqueta, "tipo_ram": tipo_ram})


def virtualizacion(grafo, requerimiento_id: str, modelos=None):
    return leer_consulta(grafo, SM, "C1", CONSULTAS["C1"], {
        "requerimiento_id": requerimiento_id, "modelos": modelos})
