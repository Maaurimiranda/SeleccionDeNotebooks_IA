// =====================================================================
// cypher/90_verificacion.cypher
// Bloques del canonico: 11 (C1-C3) · 12 (CP1-CP11, V1)
// Duenio: Miranda
// Origen: docs/cypher/Grupo_2_PG2_U1_corregido.cypher, cortado sin cambiar el contenido (PG3-02).
// =====================================================================

// ---------------------------------------------------------------------
// 11. CONSULTAS DE INFERENCIA DE LA DEMOSTRACION
// ---------------------------------------------------------------------
// C1 (inferencia crisp) - Antes de comparar nada: que notebooks hay que
// descartar porque el perfil del comprador exige virtualizacion por
// hardware, y de cuales no lo sabemos?
MATCH (c:Requerimiento {id:'req_01'})-[:TIENE_PERFIL_DOMINANTE]->(p:Perfil)-[:EXIGE]->(req:Requisito {criterio:'virtualizacion'})
WHERE req.es_excluyente
MATCH (n:Notebook)-[:POSEE]->(cpu:CPU)
WITH c, p, req, n, cpu,
     CASE cpu.virtualizacion WHEN 'soportada' THEN 'cumple'
                             WHEN 'no soportada' THEN 'no cumple'
                             ELSE 'falta informacion' END AS estado
FOREACH (_ IN CASE WHEN estado = 'no cumple' THEN [1] ELSE [] END |
  MERGE (n)-[:INCUMPLE {excluyente:true, regla:'REN-R1'}]->(req))
FOREACH (_ IN CASE WHEN estado = 'falta informacion' THEN [1] ELSE [] END |
  MERGE (n)-[:NO_VERIFICADO {regla:'REN-R1'}]->(req))
RETURN n.modelo AS notebook, cpu.gama AS gama_cpu, cpu.virtualizacion AS virtualizacion,
       estado AS resultado_requisito,
       CASE estado WHEN 'no cumple' THEN 'Descartada (REN-R1 + REC-R3)'
                   WHEN 'falta informacion' THEN 'Indeterminada: completar informacion (REC-R3)'
                   ELSE 'Sigue en evaluacion' END AS conclusion
ORDER BY resultado_requisito, notebook;

// C2 (fuzificacion) - Que riesgo corre cada notebook de quedarse corta de
// RAM para este perfil? Devuelve el valor crisp, las pertenencias, las
// activaciones de FZ-R1 a FZ-R5 y el riesgo desborrosificado (o el rango,
// si la ampliabilidad es desconocida). Todo se lee de la evaluacion del
// pedido, porque rho y a se normalizan contra su perfil.
MATCH (c:Requerimiento {id:'req_01'})-[:TIENE_PERFIL_DOMINANTE]->(pf:Perfil)
MATCH (c)-[:EVALUA]->(ev:Evaluacion)-[:SOBRE]->(n:Notebook)-[:POSEE]->(r:RAM)
OPTIONAL MATCH (ev)-[fs:PERTENECE_A]->(es:EtiquetaDifusa {variable:'suficiencia_ram'})
WITH n, r, ev, pf, collect(es.nombre + '=' + toString(round(fs.grado, 3))) AS pert_suficiencia
OPTIONAL MATCH (ev)-[fa:PERTENECE_A]->(ea:EtiquetaDifusa {variable:'indice_ampliabilidad'})
WITH n, r, ev, pf, pert_suficiencia, collect(ea.nombre + '=' + toString(round(fa.grado, 3))) AS pert_ampliabilidad
OPTIONAL MATCH (ev)-[:TIENE_LECTURA*0..1]->(x)-[act:ACTIVA]->(q:Regla)
WHERE q.id STARTS WITH 'FZ-R' AND act.fuerza IS NOT NULL
WITH n, r, ev, pf, pert_suficiencia, pert_ampliabilidad,
     collect(DISTINCT coalesce(x.escenario + ': ', '') + q.id + '=' + toString(act.fuerza)) AS reglas_activadas
RETURN n.modelo AS notebook,
       r.ram_gb AS ram_gb, pf.ram_min AS ram_min_perfil,
       round(ev.suficiencia_rho, 3) AS rho,
       r.ampliabilidad AS ampliabilidad,
       CASE WHEN ev.indice_ampliabilidad IS NULL THEN 'desconocido'
            ELSE toString(round(ev.indice_ampliabilidad, 3)) END AS indice_a,
       pert_suficiencia AS pertenencias_suficiencia,
       pert_ampliabilidad AS pertenencias_ampliabilidad,
       reglas_activadas,
       coalesce(toString(ev.riesgo_valor),
                '[' + toString(ev.riesgo_min) + ' ; ' + toString(ev.riesgo_max) + ']') AS riesgo_0_100,
       ev.riesgo_etiqueta AS etiqueta
ORDER BY coalesce(ev.riesgo_max, ev.riesgo_valor) DESC;

// C3 (inferencia cruzada) - Cual conviene recomendarle a este comprador y
// por que? Atraviesa SM1 (perfil interpretado), SM2 (rendimiento y riesgo),
// SM3 (grafica y movilidad) y SM4 (grado de recomendacion).
MATCH (p:Comprador)-[:FORMULA]->(c:Requerimiento {id:'req_01'})-[:TIENE_PERFIL_DOMINANTE]->(pf:Perfil)
MATCH (c)-[:EVALUA]->(ev:Evaluacion)-[:SOBRE]->(n:Notebook)
MATCH (n)-[:POSEE]->(r:RAM)
OPTIONAL MATCH (al:Alerta)
WHERE EXISTS { MATCH (ev)-[:GENERA]->(al) } OR EXISTS { MATCH (n)-[:GENERA]->(al) }
OPTIONAL MATCH (c)-[:RECIBE]->(:Recomendacion)-[pr:PROPONE|PROPONE_FUERA_DE_PRESUPUESTO]->(n)
WITH p, c, pf, ev, n, r, pr, collect(DISTINCT al.tipo) AS alertas
RETURN p.id AS comprador, pf.codigo AS perfil_SM1, round(c.grado_perfil_dominante, 3) AS grado_perfil,
       c.intensidad_grafica AS intensidad_SM1,
       n.modelo AS notebook, n.precio_usd AS precio,
       ev.adecuacion_rendimiento AS adec_rend_SM2,
       coalesce(toString(ev.riesgo_valor),
                '[' + toString(ev.riesgo_min) + ' ; ' + toString(ev.riesgo_max) + ']') AS riesgo_SM2,
       ev.riesgo_etiqueta AS riesgo_etq_SM2,
       ev.adecuacion_grafica AS adec_graf_SM3, n.adecuacion_movilidad AS adec_mov_SM3,
       coalesce(toString(ev.adecuacion_global),
                '[' + toString(ev.adecuacion_global_min) + ' ; ' + toString(ev.adecuacion_global_max) + ']') AS adec_global_SM4,
       ev.excedente_presupuesto AS excedente_pct,
       coalesce(toString(ev.grado_recomendacion),
                '[' + toString(ev.grado_recomendacion_min) + ' ; ' + toString(ev.grado_recomendacion_max) + ']') AS grado_SM4,
       ev.estado AS estado,
       r.nivel_ampliabilidad AS ampliabilidad,
       ev.indice_costo_beneficio AS costo_beneficio,
       CASE type(pr) WHEN 'PROPONE' THEN 'puesto ' + toString(pr.orden)
                     WHEN 'PROPONE_FUERA_DE_PRESUPUESTO' THEN 'alternativa fuera de presupuesto'
                     ELSE '-' END AS en_la_recomendacion,
       alertas
ORDER BY coalesce(ev.grado_recomendacion, ev.grado_recomendacion_min) DESC;


// ---------------------------------------------------------------------
// 12. CONSULTAS DE VERIFICACION DE LOS CASOS DE PRUEBA
// ---------------------------------------------------------------------
// CP1 positivo / CP2 negativo / CP3 difuso / CP4 indeterminado / CP9 dato que solo ordena
MATCH (:Requerimiento {id:'req_01'})-[:EVALUA]->(ev:Evaluacion)-[:SOBRE]->(n:Notebook)
WHERE n.modelo IN ['Notebook_A','Notebook_E','Notebook_X','Notebook_G','Notebook_M']
RETURN n.modelo AS notebook, ev.excluyente_virtualizacion AS excluyente,
       ev.adecuacion_global AS global, ev.excedente_presupuesto AS excedente,
       ev.grado_recomendacion AS grado, ev.etiqueta_recomendacion AS etiqueta,
       ev.grado_recomendacion_min AS grado_min, ev.grado_recomendacion_max AS grado_max,
       ev.estado AS estado
ORDER BY notebook;

// CP10: pedido ambiguo sin respuesta -> perfil indeterminado, no OFI
MATCH (p:Comprador)-[:FORMULA]->(c:Requerimiento {id:'req_02'})
OPTIONAL MATCH (c)-[:GENERA]->(al:Alerta)
OPTIONAL MATCH (c)-[:REQUIERE_ACLARACION]->(q:Pregunta)
OPTIONAL MATCH (c)-[:EVALUA]->(ev:Evaluacion)
RETURN p.id AS comprador, c.id AS requerimiento, c.perfil_dominante AS perfil_dominante,
       count(DISTINCT ev) AS notebooks_evaluadas, collect(DISTINCT al.tipo) AS alertas,
       collect(DISTINCT q.texto) AS pregunta;

// CP7: la recomendacion final, en orden (desempate por ampliabilidad),
// y la alternativa fuera de presupuesto
MATCH (:Recomendacion)-[p:PROPONE|PROPONE_FUERA_DE_PRESUPUESTO]->(n:Notebook)-[:POSEE]->(r:RAM)
RETURN coalesce(toString(p.orden), 'fuera de presupuesto') AS orden, n.modelo AS notebook,
       p.grado_recomendacion AS grado, r.nivel_ampliabilidad AS ampliabilidad, p.estado AS estado
ORDER BY coalesce(p.orden, 99);

// CP8: traza de parametros sin validar que sostienen la recomendacion
MATCH (e:EtiquetaDifusa) WHERE e.estado_validacion = 'sin validar'
RETURN e.variable AS variable, count(*) AS etiquetas_sin_validar
ORDER BY variable;

// CP11 (devolucion de PG2): dos compradores con requerimientos distintos
// evaluan la misma notebook. Cada fila es una evaluacion, con su perfil,
// sus entradas normalizadas, sus reglas activadas, sus grados y sus
// alertas. La ultima columna comprueba que en (:Notebook) no quedo ningun
// resultado que dependa del perfil: tiene que venir vacia.
MATCH (p:Comprador)-[:FORMULA]->(c:Requerimiento)-[:EVALUA]->(ev:Evaluacion)-[:SOBRE]->(n:Notebook {modelo:'Notebook_K'})
OPTIONAL MATCH (ev)-[:GENERA]->(al:Alerta)
WITH p, c, ev, n, collect(DISTINCT al.tipo + ' (' + al.regla_origen + ')') AS alertas_de_la_evaluacion
OPTIONAL MATCH (ev)-[act:ACTIVA]->(q:Regla)
WHERE act.fuerza IS NOT NULL
WITH p, c, ev, n, alertas_de_la_evaluacion,
     collect(q.id + '=' + toString(act.fuerza)) AS reglas_activadas
RETURN p.id AS comprador, c.id AS requerimiento, ev.perfil AS perfil,
       round(ev.suficiencia_rho, 3) AS rho, round(ev.indice_ampliabilidad, 3) AS indice_a,
       ev.riesgo_valor AS riesgo, ev.riesgo_etiqueta AS riesgo_etiqueta,
       ev.grado_gpu AS grado_gpu, ev.adecuacion_grafica AS adec_grafica,
       ev.adecuacion_rendimiento AS adec_rend,
       [ev.peso_rendimiento, ev.peso_grafica, ev.peso_movilidad] AS pesos,
       ev.adecuacion_global AS adec_global, ev.grado_recomendacion AS grado,
       ev.estado AS estado, reglas_activadas, alertas_de_la_evaluacion,
       [k IN keys(n) WHERE k IN ['riesgo_obsolescencia','riesgo_etiqueta','riesgo_rango',
         'grado_gpu','margen_gama','adecuacion_grafica','adecuacion_rendimiento',
         'grado_pantalla']] AS resultados_por_perfil_en_Notebook
ORDER BY requerimiento;

// V1 (devolucion de PG2): agenda para la sesion con el tecnico. Lo que hay
// que validar, la pregunta tal como se le hace y que nodos cambian si
// responde distinto.
MATCH (ce:ConsultaExperto)-[:VALIDA]->(x)
OPTIONAL MATCH (x)<-[:SE_PARAMETRIZA_CON]-(e:EtiquetaDifusa)
RETURN ce.id AS consulta, ce.submodulo AS submodulo, ce.que_se_valida AS que_se_valida,
       ce.pregunta AS pregunta, ce.situacion_actual AS hoy, ce.alternativa_a_evaluar AS alternativa,
       collect(DISTINCT coalesce(x.id, x.nombre)) AS nodos_que_cambian,
       count(DISTINCT e) AS etiquetas, ce.estado AS estado
ORDER BY submodulo, consulta;
