"""SM4 · Repositorio: Q1, Q2, Q3, Q4 (L2), Q6, Q6B y Q7 del PI4 de Luconi, solo lectura.

Base: docs/fuentes/SM4/Luconi_Martina_PI4_U4.py, sin los filtros de precio y alertas (el contrato no
los tiene) y con todo `ORDER BY` desempatado por modelo, para que dos corridas den el mismo orden.
Las consultas leen lo que el bloque 10.f de cypher/40_sm4.cypher ya infirió: estado, grado, ranking
(`PROPONE`) y alternativa fuera de presupuesto. Acá no se arma evidencia: solo se ejecutan consultas.
"""
from asistente.submodulos.comun import leer_consulta

SM = "SM4"

# Alertas de la evaluación (SM2, SM3 y SM4) o de la notebook, siempre con la regla que las produjo.
_ALERTAS = """
CALL {
  WITH ev, n
  OPTIONAL MATCH (al:Alerta)
  WHERE EXISTS { MATCH (ev)-[:GENERA]->(al) } OR EXISTS { MATCH (n)-[:GENERA]->(al) }
  RETURN collect(DISTINCT CASE WHEN al IS NULL THEN null ELSE
         {codigo:al.regla_origen, texto:al.mensaje} END) AS alertas
}
"""

# Evaluaciones del pedido con su lugar en la recomendación (puesto, alternativa fuera de presupuesto
# o consulta puntual). `filtro` es un WHERE sobre la notebook y va antes de los demás MATCH.
def _evaluadas(filtro: str = "") -> str:
    return """
MATCH (c:Requerimiento {id:$requerimiento_id})-[:EVALUA]->(ev:Evaluacion)-[:SOBRE]->(n:Notebook)
""" + filtro + """MATCH (n)-[:POSEE]->(r:RAM)
MATCH (mx:Parametro {nombre:'P_MAX_RECOMENDADAS'}), (me:Parametro {nombre:'P_MARGEN_EMPATE'})
OPTIONAL MATCH (c)-[:RECIBE]->(:Recomendacion)-[p:PROPONE|PROPONE_FUERA_DE_PRESUPUESTO]->(n)
OPTIONAL MATCH (c)-[cp:CONSULTA_POR]->(n)
""" + _ALERTAS


# Por qué una notebook no figura en el ranking y qué regla lo decidió (D-06: estados sin tildes).
# Para las que sí figuran, `m` es null.
_MOTIVO = """
CALL {
  WITH ev
  OPTIONAL MATCH (ev)-[a:ACTIVA]->(q:Regla)
  WHERE q.id IN ['REC-RD4', 'REC-RD5']
  RETURN q.id AS regla_descarte ORDER BY a.fuerza DESC, q.id LIMIT 1
}
WITH *, CASE
  WHEN ev.excluyente_virtualizacion = 'no cumple' THEN
       {regla:'REC-R3', motivo:'La CPU no soporta virtualizacion por hardware: requisito excluyente del perfil'}
  WHEN ev.excluyente_virtualizacion = 'falta informacion' THEN
       {regla:'REC-R3', motivo:'La ficha no informa si la CPU soporta virtualizacion: no se puede comparar'}
  WHEN ev.estado = 'Descartada' THEN
       {regla:regla_descarte, motivo:'El grado de recomendacion queda en descartar'}
  WHEN NOT ev.estado STARTS WITH 'Recomendada' THEN
       {regla:'REC-R15', motivo:'El resultado depende de un dato que falta: ' + coalesce(ev.dato_faltante, 'no informado')}
  WHEN p IS NOT NULL THEN null
  WHEN cp IS NOT NULL THEN
       {regla:null, motivo:'Es una consulta puntual por esta notebook: se responde con su evaluacion, sin ranking'}
  WHEN ev.excedente_presupuesto > 0 THEN
       {regla:null, motivo:'Supera el presupuesto: solo se ofrece una alternativa fuera de presupuesto'}
  ELSE {regla:'REC-R8', motivo:'Quedo fuera de los primeros ' + toString(toInteger(mx.valor)) + ' puestos del ranking'}
END AS m
"""

_MOTIVO_COLUMNAS = "m.motivo AS motivo, m.regla AS regla,"

_LUGAR_COLUMNAS = """CASE type(p) WHEN 'PROPONE' THEN 'puesto ' + toString(p.orden)
                    WHEN 'PROPONE_FUERA_DE_PRESUPUESTO' THEN 'alternativa fuera de presupuesto'
                    ELSE CASE WHEN cp IS NOT NULL THEN 'consulta puntual: se responde con su evaluacion, sin ranking'
                              ELSE 'no figura en la recomendacion' END END AS en_la_recomendacion,"""

# Franja de ancho P_MARGEN_EMPATE (REC-R8): las que caen en la misma franja empatan y desempata la ampliabilidad.
_FRANJA_COLUMNA = """CASE type(p) WHEN 'PROPONE' THEN toInteger(floor(
            coalesce(ev.grado_recomendacion, ev.grado_recomendacion_min) / me.valor)) END AS franja_empate,"""

# Columnas que comparten todas las consultas. El rango (REC-R15) viaja en las columnas _min y _max.
_COLUMNAS = """n.modelo AS notebook, n.precio_usd AS precio_usd, ev.estado AS estado,
       ev.grado_recomendacion AS grado_recomendacion, ev.grado_recomendacion_min AS grado_recomendacion_min,
       ev.grado_recomendacion_max AS grado_recomendacion_max,
       ev.adecuacion_global AS adecuacion_global, ev.adecuacion_global_min AS adecuacion_global_min,
       ev.adecuacion_global_max AS adecuacion_global_max,
       ev.excedente_presupuesto AS excedente_presupuesto_pct,
       ev.indice_costo_beneficio AS indice_costo_beneficio, r.nivel_ampliabilidad AS ampliabilidad_ram,
       alertas"""

CONSULTAS: dict[str, str] = {
    # Q1 · ranking de la recomendación (REC-R8) y alternativa fuera de presupuesto. `franja_empate` es la
    # franja de ancho P_MARGEN_EMPATE: dos notebooks de la misma franja empatan y desempata la ampliabilidad.
    "Q1_RECOMENDACION": """
MATCH (c:Requerimiento {id:$requerimiento_id})-[:RECIBE]->(:Recomendacion)
      -[p:PROPONE|PROPONE_FUERA_DE_PRESUPUESTO]->(n:Notebook)
MATCH (c)-[:EVALUA]->(ev:Evaluacion)-[:SOBRE]->(n)
MATCH (n)-[:POSEE]->(r:RAM)
MATCH (me:Parametro {nombre:'P_MARGEN_EMPATE'})
""" + _ALERTAS + """
RETURN CASE type(p) WHEN 'PROPONE' THEN p.orden END AS puesto,
       type(p) = 'PROPONE_FUERA_DE_PRESUPUESTO' AS fuera_de_presupuesto,
       """ + _FRANJA_COLUMNA + """
       """ + _COLUMNAS + """
ORDER BY fuera_de_presupuesto, puesto, notebook
""",

    # Q2 · lo evaluado que no figura en la recomendación, con el motivo y la regla
    "Q2_NO_PROPUESTAS": _evaluadas() + "WITH * WHERE p IS NULL" + _MOTIVO + """
RETURN """ + _MOTIVO_COLUMNAS + """ ev.dato_faltante AS dato_faltante,
       """ + _COLUMNAS + """
ORDER BY coalesce(ev.grado_recomendacion, ev.grado_recomendacion_min) DESC, notebook
""",

    # Q3 · sin alternativa adecuada (REC-R10)
    "Q3_SIN_ALTERNATIVA": """
MATCH (c:Requerimiento {id:$requerimiento_id})-[:RECIBE]->(s:SinAlternativaAdecuada)
RETURN s.motivo AS motivo
ORDER BY motivo
""",

    # Q4 · L2 del bloque 13: una notebook en un pedido, en los tres bloques de REC-R11
    "Q4_EXPLICAR_NOTEBOOK": _evaluadas("WHERE n.modelo = $modelo\n") + """
MATCH (c)-[:TIENE_PERFIL_DOMINANTE]->(pf:Perfil)
MATCH (n)-[:POSEE]->(b:Bateria)
""" + _MOTIVO + """
RETURN pf.codigo AS perfil, c.presupuesto_usd AS presupuesto_usd,
       {rendimiento:ev.peso_rendimiento, grafica:ev.peso_grafica, movilidad:ev.peso_movilidad} AS pesos,
       ev.dato_faltante AS dato_faltante,
       """ + _LUGAR_COLUMNAS + " " + _MOTIVO_COLUMNAS + """
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
       """ + _COLUMNAS + """
ORDER BY notebook
""",

    # Q6 · comparación de dos o tres notebooks en un pedido (primero las que figuran en la recomendación)
    "Q6_COMPARAR": _evaluadas("WHERE n.modelo IN $modelos\n") + _MOTIVO + """
RETURN """ + _LUGAR_COLUMNAS + """
       """ + _FRANJA_COLUMNA + " " + _MOTIVO_COLUMNAS + """
       """ + _COLUMNAS + """
ORDER BY coalesce(p.orden, 99), coalesce(ev.grado_recomendacion, ev.grado_recomendacion_min) DESC, notebook
""",

    # Q6B · el criterio de desempate (REC-R8) y su margen, leídos del grafo
    "Q6B_CRITERIO_DESEMPATE": """
MATCH (q:Regla {id:'REC-R8'}), (me:Parametro {nombre:'P_MARGEN_EMPATE'})
RETURN q.id AS regla, q.enunciado AS enunciado, me.valor AS margen_empate,
       q.estado_validacion AS validacion, me.estado_validacion AS validacion_margen
""",

    # Q7 · orden por índice costo-beneficio (REC-R9) entre las notebooks recomendadas
    "Q7_COSTO_BENEFICIO": """
MATCH (c:Requerimiento {id:$requerimiento_id})-[:EVALUA]->(ev:Evaluacion)-[:SOBRE]->(n:Notebook)
WHERE ev.estado STARTS WITH 'Recomendada'
MATCH (n)-[:POSEE]->(r:RAM)
MATCH (q:Regla {id:'REC-R9'})
""" + _ALERTAS + """
RETURN q.id AS regla, q.enunciado AS enunciado, q.estado_validacion AS validacion,
       """ + _COLUMNAS + """
ORDER BY indice_costo_beneficio DESC, notebook
""",
}


def ranking(grafo, requerimiento_id: str):
    return leer_consulta(grafo, SM, "Q1_RECOMENDACION", CONSULTAS["Q1_RECOMENDACION"],
                         {"requerimiento_id": requerimiento_id})


def no_propuestas(grafo, requerimiento_id: str):
    return leer_consulta(grafo, SM, "Q2_NO_PROPUESTAS", CONSULTAS["Q2_NO_PROPUESTAS"],
                         {"requerimiento_id": requerimiento_id})


def sin_alternativa(grafo, requerimiento_id: str):
    return leer_consulta(grafo, SM, "Q3_SIN_ALTERNATIVA", CONSULTAS["Q3_SIN_ALTERNATIVA"],
                         {"requerimiento_id": requerimiento_id})


def explicar(grafo, requerimiento_id: str, modelo: str):
    return leer_consulta(grafo, SM, "Q4_EXPLICAR_NOTEBOOK", CONSULTAS["Q4_EXPLICAR_NOTEBOOK"],
                         {"requerimiento_id": requerimiento_id, "modelo": modelo})


def comparar(grafo, requerimiento_id: str, modelos: list[str]):
    return leer_consulta(grafo, SM, "Q6_COMPARAR", CONSULTAS["Q6_COMPARAR"],
                         {"requerimiento_id": requerimiento_id, "modelos": modelos})


def criterio_desempate(grafo):
    return leer_consulta(grafo, SM, "Q6B_CRITERIO_DESEMPATE", CONSULTAS["Q6B_CRITERIO_DESEMPATE"], {})


def costo_beneficio(grafo, requerimiento_id: str):
    return leer_consulta(grafo, SM, "Q7_COSTO_BENEFICIO", CONSULTAS["Q7_COSTO_BENEFICIO"],
                         {"requerimiento_id": requerimiento_id})
