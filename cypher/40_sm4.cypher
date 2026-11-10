// =====================================================================
// cypher/40_sm4.cypher
// Bloques del canonico: 10.f
// Duenio: Luconi
// Origen: docs/cypher/Grupo_2_PG2_U1_corregido.cypher, cortado sin cambiar el contenido (PG3-02).
// =====================================================================

// 10.f SM4 - filtro de excluyentes (REC-R3) y evaluacion por notebook
// (la (:Evaluacion) y su excluyente se crearon en 10.c.0)

// Pesos del perfil con el incremento por prioridad (REC-R4, REC-R5)
MATCH (ip:Parametro {nombre:'P_INCREMENTO_PRIORIDAD'})
MATCH (c:Requerimiento)-[:TIENE_PERFIL_DOMINANTE]->(pf:Perfil)
MATCH (c)-[:EVALUA]->(ev:Evaluacion)
WITH ev,
     pf.peso_rendimiento + (CASE WHEN c.prioridad = 'rendimiento' THEN ip.valor ELSE 0.0 END) AS br,
     pf.peso_grafica     + (CASE WHEN c.prioridad = 'grafica' THEN ip.valor ELSE 0.0 END) AS bg,
     pf.peso_movilidad   + (CASE WHEN c.prioridad IN ['portabilidad','autonomia'] THEN ip.valor ELSE 0.0 END) AS bm
WITH ev, br, bg, bm, br + bg + bm AS tot
SET ev.peso_rendimiento = round(br / tot, 3),
    ev.peso_grafica     = round(bg / tot, 3),
    ev.peso_movilidad   = round(bm / tot, 3)
WITH ev
MATCH (q4:Regla {id:'REC-R4'}), (q5:Regla {id:'REC-R5'})
MERGE (ev)-[:ACTIVA]->(q4)
MERGE (ev)-[:ACTIVA]->(q5);

// Adecuacion global y excedente de presupuesto
MATCH (c:Requerimiento)-[:EVALUA]->(ev:Evaluacion)-[:SOBRE]->(n:Notebook)
WHERE ev.adecuacion_grafica IS NOT NULL AND n.adecuacion_movilidad IS NOT NULL
SET ev.adecuacion_global = round(ev.peso_rendimiento * ev.adecuacion_rendimiento
                               + ev.peso_grafica     * ev.adecuacion_grafica
                               + ev.peso_movilidad   * n.adecuacion_movilidad, 3),
    ev.excedente_presupuesto = round(CASE
      WHEN n.precio_usd <= c.presupuesto_usd THEN 0.0
      ELSE (n.precio_usd - c.presupuesto_usd) / c.presupuesto_usd * 100.0 END, 2);

// REC-R15 - Politica general de dato faltante (devolucion de PG1 y de PI3 de SM4):
// si falta un grado que solo ORDENA (aca, la movilidad porque la ficha no
// informa la autonomia), no se inventa un valor intermedio: se calcula la
// adecuacion global minima (grado faltante = 0) y maxima (= 1) y se infiere
// el grado de recomendacion en los dos escenarios, como dos lecturas.
MATCH (c:Requerimiento)-[:EVALUA]->(ev:Evaluacion)-[:SOBRE]->(n:Notebook)
WHERE ev.adecuacion_grafica IS NOT NULL AND n.adecuacion_movilidad IS NULL
WITH c, ev, n,
     ev.peso_rendimiento * ev.adecuacion_rendimiento + ev.peso_grafica * ev.adecuacion_grafica AS base,
     round(CASE WHEN n.precio_usd <= c.presupuesto_usd THEN 0.0
                ELSE (n.precio_usd - c.presupuesto_usd) / c.presupuesto_usd * 100.0 END, 2) AS exc
SET ev.adecuacion_global = null,
    ev.adecuacion_global_min = round(base, 3),
    ev.adecuacion_global_max = round(base + ev.peso_movilidad, 3),
    ev.excedente_presupuesto = exc,
    ev.dato_faltante = 'adecuacion_movilidad (autonomia no informada)'
MERGE (ev)-[:TIENE_LECTURA]->(lp:Lectura {escenario:'peor', dato:'adecuacion_movilidad',
                                          evaluacion:ev.requerimiento + '/' + ev.notebook})
SET lp.adecuacion_global = round(base, 3), lp.excedente_presupuesto = exc
MERGE (ev)-[:TIENE_LECTURA]->(lm:Lectura {escenario:'mejor', dato:'adecuacion_movilidad',
                                          evaluacion:ev.requerimiento + '/' + ev.notebook})
SET lm.adecuacion_global = round(base + ev.peso_movilidad, 3), lm.excedente_presupuesto = exc
MERGE (n)-[:GENERA]->(:Alerta {tipo:'Informacion incompleta', submodulo_origen:'SM4',
  regla_origen:'REC-R15', notebook:n.modelo,
  mensaje:'La ficha no informa la autonomia: la adecuacion global se informa como rango'});

// Fuzificacion de las dos entradas de SM4 (sobre evaluaciones y sobre lecturas)
MATCH (ev) WHERE (ev:Evaluacion OR ev:Lectura) AND ev.adecuacion_global IS NOT NULL
MATCH (v:VariableDifusa)-[:TIENE_ETIQUETA]->(e:EtiquetaDifusa)
WHERE v.nombre IN ['adecuacion_global','excedente_presupuesto']
WITH ev, e, CASE e.variable WHEN 'adecuacion_global' THEN ev.adecuacion_global
                            ELSE (CASE WHEN ev.excedente_presupuesto > 30.0 THEN 30.0
                                       ELSE ev.excedente_presupuesto END) END AS x
MERGE (ev)-[f:PERTENECE_A]->(e)
SET f.grado = CASE
      WHEN e.tipo = 'hombro_izq' AND x <= e.centro THEN 1.0
      WHEN e.tipo = 'hombro_der' AND x >= e.centro THEN 1.0
      ELSE exp(-((x - e.centro)^2) / (2.0 * e.sigma^2)) END,
    f.valor_crisp = x, f.ts = datetime();

// REC-RD1 a REC-RD5: grado de recomendacion
MATCH (ev)-[fg:PERTENECE_A]->(eg:EtiquetaDifusa {variable:'adecuacion_global'})
WHERE ev:Evaluacion OR ev:Lectura
WITH ev, collect({et:eg.nombre, mu:fg.grado}) AS G
MATCH (ev)-[fx:PERTENECE_A]->(ex:EtiquetaDifusa {variable:'excedente_presupuesto'})
WITH ev, G, collect({et:ex.nombre, mu:fx.grado}) AS X
WITH ev,
     [x IN G WHERE x.et = 'baja' ][0].mu AS gB,
     [x IN G WHERE x.et = 'media'][0].mu AS gM,
     [x IN G WHERE x.et = 'alta' ][0].mu AS gA,
     [x IN X WHERE x.et = 'dentro'   ][0].mu AS xD,
     [x IN X WHERE x.et = 'levemente'][0].mu AS xL,
     [x IN X WHERE x.et = 'muy'      ][0].mu AS xM
WITH ev,
     (CASE WHEN gA < xD THEN gA ELSE xD END) AS r1,
     (CASE WHEN gM < xD THEN gM ELSE xD END) AS r2,
     (CASE WHEN gA < xL THEN gA ELSE xL END) AS r3,
     (CASE WHEN gM < xL THEN gM ELSE xL END) AS r4,
     (CASE WHEN gB > xM THEN gB ELSE xM END) AS r5
MATCH (k1:Regla {id:'REC-RD1'}), (k2:Regla {id:'REC-RD2'}), (k3:Regla {id:'REC-RD3'}),
      (k4:Regla {id:'REC-RD4'}), (k5:Regla {id:'REC-RD5'})
FOREACH (_ IN CASE WHEN r1 > 0.01 THEN [1] ELSE [] END | MERGE (ev)-[x:ACTIVA]->(k1) SET x.fuerza = round(r1, 3))
FOREACH (_ IN CASE WHEN r2 > 0.01 THEN [1] ELSE [] END | MERGE (ev)-[x:ACTIVA]->(k2) SET x.fuerza = round(r2, 3))
FOREACH (_ IN CASE WHEN r3 > 0.01 THEN [1] ELSE [] END | MERGE (ev)-[x:ACTIVA]->(k3) SET x.fuerza = round(r3, 3))
FOREACH (_ IN CASE WHEN r4 > 0.01 THEN [1] ELSE [] END | MERGE (ev)-[x:ACTIVA]->(k4) SET x.fuerza = round(r4, 3))
FOREACH (_ IN CASE WHEN r5 > 0.01 THEN [1] ELSE [] END | MERGE (ev)-[x:ACTIVA]->(k5) SET x.fuerza = round(r5, 3))
WITH ev, r1, r2, r3, r4, r5
WITH ev, r1,
     (CASE WHEN r2 > r3 THEN r2 ELSE r3 END) AS rConsiderar,
     (CASE WHEN r4 > r5 THEN r4 ELSE r5 END) AS rDescartar
MATCH (sD:EtiquetaDifusa {variable:'grado_recomendacion', nombre:'descartar'}),
      (sC:EtiquetaDifusa {variable:'grado_recomendacion', nombre:'considerar'}),
      (sR:EtiquetaDifusa {variable:'grado_recomendacion', nombre:'recomendar'})
UNWIND range(0, 100) AS i
WITH ev, r1, rConsiderar, rDescartar, sD, sC, sR, i / 100.0 AS y
WITH ev, y, sD, sC, sR,
     (CASE WHEN rDescartar  < exp(-((y - sD.centro)^2)/(2.0*sD.sigma^2)) THEN rDescartar
           ELSE exp(-((y - sD.centro)^2)/(2.0*sD.sigma^2)) END) AS cD,
     (CASE WHEN rConsiderar < exp(-((y - sC.centro)^2)/(2.0*sC.sigma^2)) THEN rConsiderar
           ELSE exp(-((y - sC.centro)^2)/(2.0*sC.sigma^2)) END) AS cC,
     (CASE WHEN r1          < exp(-((y - sR.centro)^2)/(2.0*sR.sigma^2)) THEN r1
           ELSE exp(-((y - sR.centro)^2)/(2.0*sR.sigma^2)) END) AS cR
WITH ev, y, sD, sC, sR, (CASE WHEN cD >= cC AND cD >= cR THEN cD
                              WHEN cC >= cR THEN cC ELSE cR END) AS agg
WITH ev, sD, sC, sR, sum(y * agg) / sum(agg) AS y0
WITH ev, y0,
     exp(-((y0 - sD.centro)^2)/(2.0*sD.sigma^2)) AS mD,
     exp(-((y0 - sC.centro)^2)/(2.0*sC.sigma^2)) AS mC,
     exp(-((y0 - sR.centro)^2)/(2.0*sR.sigma^2)) AS mR
SET ev.grado_recomendacion = round(y0, 3),
    ev.etiqueta_recomendacion = CASE WHEN mR >= mC AND mR >= mD THEN 'recomendar'
                                      WHEN mC >= mD THEN 'considerar' ELSE 'descartar' END;

// REC-R15 (cierre): el rango de grados vuelve a la evaluacion
MATCH (ev:Evaluacion)-[:TIENE_LECTURA]->(lp:Lectura {escenario:'peor', dato:'adecuacion_movilidad'}),
      (ev)-[:TIENE_LECTURA]->(lm:Lectura {escenario:'mejor', dato:'adecuacion_movilidad'})
SET ev.grado_recomendacion = null,
    ev.grado_recomendacion_min = lp.grado_recomendacion,
    ev.grado_recomendacion_max = lm.grado_recomendacion,
    ev.etiqueta_peor = lp.etiqueta_recomendacion,
    ev.etiqueta_mejor = lm.etiqueta_recomendacion;

// Estado de evaluacion. Politica general de dato faltante:
//   falta un dato de un EXCLUYENTE      -> Indeterminada (no se compara)
//   falta un dato que solo ORDENA       -> rango; peor caso no descartable
//                                          -> Recomendada condicionada;
//                                          mejor caso descartable -> Descartada;
//                                          si depende del dato -> Indeterminada
MATCH (ev:Evaluacion)-[:SOBRE]->(n:Notebook)
SET ev.estado = CASE
  WHEN ev.excluyente_virtualizacion = 'no cumple'        THEN 'Descartada (excluyente incumplido)'
  WHEN ev.excluyente_virtualizacion = 'falta informacion' THEN 'Indeterminada: completar informacion'
  WHEN ev.etiqueta_peor IS NOT NULL AND ev.etiqueta_peor <> 'descartar'
       THEN 'Recomendada condicionada por falta de informacion'
  WHEN ev.etiqueta_mejor = 'descartar' THEN 'Descartada'
  WHEN ev.etiqueta_peor IS NOT NULL THEN 'Indeterminada: completar informacion'
  WHEN ev.etiqueta_recomendacion = 'recomendar' THEN 'Recomendada (Alta)'
  WHEN ev.etiqueta_recomendacion = 'considerar' THEN 'Recomendada (Media)'
  ELSE 'Descartada' END;
// ("considerar" se informa como "Recomendada (Media)": la etiqueta lingüistica
//  queda en ev.etiqueta_recomendacion y el estado es lo que ve el asesor)

// Traza de las reglas crisp que decidieron el estado
MATCH (ev:Evaluacion), (q3:Regla {id:'REC-R3'}), (q1:Regla {id:'REN-R1'})
WHERE ev.excluyente_virtualizacion IN ['no cumple','falta informacion']
MERGE (ev)-[:ACTIVA]->(q3)
MERGE (ev)-[:ACTIVA]->(q1);
MATCH (ev:Evaluacion)-[:TIENE_LECTURA]->(:Lectura {dato:'adecuacion_movilidad'}), (q:Regla {id:'REC-R15'})
MERGE (ev)-[:ACTIVA]->(q);

// Indice costo-beneficio (REC-R9)
MATCH (ev:Evaluacion)-[:SOBRE]->(n:Notebook)
WHERE coalesce(ev.adecuacion_global, ev.adecuacion_global_min) IS NOT NULL
SET ev.indice_costo_beneficio = round(coalesce(ev.adecuacion_global, ev.adecuacion_global_min)
                                      / (n.precio_usd / 1000.0), 3)
WITH ev
MATCH (q:Regla {id:'REC-R9'})
MERGE (ev)-[:ACTIVA]->(q);

// Alertas de infra y sobredimensionamiento (REC-R7, REC-R13), por evaluacion
MATCH (c:Requerimiento)-[:TIENE_PERFIL_DOMINANTE]->(pf:Perfil)
MATCH (c)-[:EVALUA]->(ev:Evaluacion)-[:SOBRE]->(n:Notebook)-[:POSEE]->(r:RAM)
WHERE r.ram_gb < pf.ram_min
MERGE (ev)-[:GENERA]->(:Alerta {tipo:'Infradimensionamiento', submodulo_origen:'SM4',
  regla_origen:'REC-R13', requerimiento:c.id, notebook:n.modelo,
  mensaje:'La RAM (' + toString(r.ram_gb) + ' GB) no llega al minimo del perfil (' + toString(pf.ram_min) + ' GB)'});

MATCH (c:Requerimiento)-[:TIENE_PERFIL_DOMINANTE]->(pf:Perfil)
MATCH (c)-[:EVALUA]->(ev:Evaluacion)-[:SOBRE]->(n:Notebook)-[:POSEE]->(r:RAM)
WHERE pf.ram_sobra IS NOT NULL AND r.ram_gb >= pf.ram_sobra
MERGE (ev)-[:GENERA]->(:Alerta {tipo:'Sobredimensionamiento', submodulo_origen:'SM4',
  regla_origen:'REC-R7', requerimiento:c.id, notebook:n.modelo,
  mensaje:'La RAM alcanza el valor a partir del cual el equipo sobra para el perfil'});

// GM-R11: alerta de autonomia insuficiente
MATCH (al:Parametro {nombre:'P_ALFA_ALERTA_AUTONOMIA'})
MATCH (c:Requerimiento) WHERE c.prioridad = 'autonomia'
MATCH (c)-[:EVALUA]->(ev:Evaluacion)-[:SOBRE]->(n:Notebook)-[:POSEE]->(b:Bateria)
MATCH (b)-[f:PERTENECE_A]->(e:EtiquetaDifusa {variable:'autonomia_h', nombre:'baja'})
WHERE f.grado >= al.valor
MERGE (ev)-[:GENERA]->(:Alerta {tipo:'Autonomia insuficiente', submodulo_origen:'SM3',
  regla_origen:'GM-R11', requerimiento:c.id, notebook:n.modelo,
  mensaje:'La autonomia pertenece a "baja" con grado ' + toString(round(f.grado, 2))});

// Recomendacion final: hasta P_MAX_RECOMENDADAS, desempate por ampliabilidad (REC-R8).
// Una consulta puntual (req_03) no arma ranking: su respuesta es la evaluacion.
MATCH (mx:Parametro {nombre:'P_MAX_RECOMENDADAS'}), (me:Parametro {nombre:'P_MARGEN_EMPATE'})
MATCH (c:Requerimiento)-[:EVALUA]->(ev:Evaluacion)-[:SOBRE]->(n:Notebook)-[:POSEE]->(r:RAM)
WHERE ev.estado STARTS WITH 'Recomendada' AND ev.excedente_presupuesto = 0.0
  AND NOT EXISTS { MATCH (c)-[:CONSULTA_POR]->(:Notebook) }
WITH c, mx, me, ev, n, r,
     CASE r.nivel_ampliabilidad WHEN 'alta' THEN 3 WHEN 'media' THEN 2
                                WHEN 'baja' THEN 1 ELSE 0 END AS amp
// con rango, se ordena por el peor caso: no se premia un dato que no se tiene
// REC-R9 (correccion PG3): si la prioridad declarada es 'precio', el primer
// criterio es el indice costo-beneficio; si no, ese termino vale 0 para todas
// y el orden queda como antes (franja de grado REC-R8, ampliabilidad, indice).
ORDER BY CASE WHEN c.prioridad = 'precio' THEN ev.indice_costo_beneficio ELSE 0.0 END DESC,
         floor(coalesce(ev.grado_recomendacion, ev.grado_recomendacion_min) / me.valor) DESC,
         amp DESC, ev.indice_costo_beneficio DESC
WITH c, mx, collect({ev:ev, n:n}) AS candidatas
WITH c, candidatas[0..toInteger(mx.valor)] AS top
MERGE (c)-[:RECIBE]->(rec:Recomendacion {requerimiento:c.id})
SET rec.cantidad = size(top), rec.generada = datetime()
WITH rec, top
UNWIND range(0, size(top) - 1) AS pos
WITH rec, top[pos].n AS nb, top[pos].ev AS ev, pos + 1 AS orden
MERGE (rec)-[p:PROPONE {orden:orden}]->(nb)
SET p.grado_recomendacion = coalesce(ev.grado_recomendacion, ev.grado_recomendacion_min),
    p.estado = ev.estado
WITH rec
MATCH (q:Regla {id:'REC-R8'})
MERGE (rec)-[:ACTIVA]->(q);

// REC-R9 en la traza: la recomendacion de un pedido con prioridad 'precio'
// queda ligada a la regla que cambio su criterio de orden (correccion PG3).
MATCH (c:Requerimiento {prioridad:'precio'})-[:RECIBE]->(rec:Recomendacion), (q:Regla {id:'REC-R9'})
MERGE (rec)-[:ACTIVA]->(q);

// Alternativa fuera de presupuesto (frame Recomendacion de PG1: maximo 1).
// Con REC-RD3 una notebook muy adecuada que se pasa un poco no desaparece:
// baja a "considerar" y se ofrece aparte, nunca entre las tres primeras.
MATCH (c:Requerimiento)-[:RECIBE]->(rec:Recomendacion)
MATCH (c)-[:EVALUA]->(ev:Evaluacion)-[:SOBRE]->(n:Notebook)
WHERE ev.estado STARTS WITH 'Recomendada' AND ev.excedente_presupuesto > 0.0
WITH rec, ev, n ORDER BY ev.grado_recomendacion DESC
WITH rec, collect(n)[0] AS nb, collect(ev)[0] AS ev
MERGE (rec)-[p:PROPONE_FUERA_DE_PRESUPUESTO]->(nb)
SET p.grado_recomendacion = ev.grado_recomendacion,
    p.excedente_presupuesto = ev.excedente_presupuesto,
    p.estado = ev.estado;

// REC-R10: si no quedo ninguna recomendada
// (un requerimiento con perfil indeterminado no recibe "sin alternativa":
//  no es que no haya notebook adecuada, es que todavia no se sabe para que)
MATCH (c:Requerimiento)
WHERE c.perfil_dominante <> 'indeterminado'
  AND NOT EXISTS { MATCH (c)-[:CONSULTA_POR]->(:Notebook) }
  AND NOT EXISTS { MATCH (c)-[:RECIBE]->(:Recomendacion) }
MERGE (c)-[:RECIBE]->(s:SinAlternativaAdecuada {requerimiento:c.id,
  motivo:'Ninguna notebook del catalogo alcanzo el grado de recomendacion con las restricciones del pedido'})
WITH s
MATCH (q:Regla {id:'REC-R10'})
MERGE (s)-[:ACTIVA]->(q);

// Cada alerta queda ligada a la regla que la produjo
MATCH (al:Alerta), (q:Regla)
WHERE q.id = al.regla_origen
MERGE (al)-[:PRODUCIDA_POR]->(q);
