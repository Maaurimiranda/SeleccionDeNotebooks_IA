// =====================================================================
// cypher/15_evaluaciones.cypher
// Bloques del canonico: 10.c (encabezado) · 10.c.0
// Duenio: Miranda
// Origen: docs/cypher/Grupo_2_PG2_U1_corregido.cypher, cortado sin cambiar el contenido (PG3-02).
// =====================================================================

// 10.c SM2 - FZ-R1 a FZ-R5: riesgo de obsolescencia por RAM, por evaluacion
//
// 10.c.0 Evaluaciones (devolucion de PG2): una (:Evaluacion) por cada
// requerimiento con perfil dominante y cada notebook del catalogo, o solo
// por la notebook consultada si el pedido es una consulta puntual. Desde
// aca, todo lo que depende del perfil o del pedido se guarda en la
// evaluacion y no en la notebook: dos compradores con requerimientos
// distintos pueden evaluar la misma notebook sin pisarse (CP11). Las
// salidas crisp de PI2 se copian del par notebook-perfil; sin ellas la
// notebook no se evalua para ese perfil (limitacion 5 del informe).
MATCH (c:Requerimiento)-[:TIENE_PERFIL_DOMINANTE]->(pf:Perfil)
MATCH (n:Notebook)-[s:SALIDA_PI2]->(pf)
WHERE NOT EXISTS { MATCH (c)-[:CONSULTA_POR]->(:Notebook) }
   OR EXISTS { MATCH (c)-[:CONSULTA_POR]->(n) }
MATCH (n)-[:POSEE]->(cpu:CPU)
MERGE (c)-[:EVALUA]->(ev:Evaluacion {requerimiento:c.id, notebook:n.modelo})
MERGE (ev)-[:SOBRE]->(n)
SET ev.perfil = pf.codigo,
    ev.adecuacion_rendimiento = s.adecuacion_rendimiento,
    ev.grado_pantalla = s.grado_pantalla,
    ev.excluyente_virtualizacion = CASE
      WHEN NOT pf.requiere_virtualizacion THEN 'no aplica'
      WHEN cpu.virtualizacion = 'soportada'     THEN 'cumple'
      WHEN cpu.virtualizacion = 'no soportada'  THEN 'no cumple'
      ELSE 'falta informacion' END;
