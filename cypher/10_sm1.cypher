// =====================================================================
// cypher/10_sm1.cypher
// Bloques del canonico: 9 (encabezado) · 9.a · 9.b · 10 (encabezado) · 10.a · 10.b
// Duenio: Olea
// Origen: docs/cypher/Grupo_2_PG2_U1_corregido.cypher, cortado sin cambiar el contenido (PG3-02).
// =====================================================================

// ---------------------------------------------------------------------
// 9. FUZIFICACION
//    Una sola consulta generica por variable de entrada. El grado se
//    guarda en la relacion (:PERTENECE_A {grado}), como definio PI3.
//    Las etiquetas con hombro valen 1 del lado del borde del universo.
//    Aca se fuzifican las cinco entradas que no dependen del perfil. La
//    suficiencia de RAM y el indice de ampliabilidad se normalizan contra
//    la RAM minima y la recomendada del perfil, asi que se calculan y se
//    fuzifican por evaluacion en el bloque 10.c.
// ---------------------------------------------------------------------
// 9.a SM1 - dedicacion_h de cada actividad
MATCH (a:Actividad) WHERE a.dedicacion_h IS NOT NULL
MATCH (v:VariableDifusa {nombre:'dedicacion_h'})-[:TIENE_ETIQUETA]->(e:EtiquetaDifusa)
WITH a, e, CASE WHEN a.dedicacion_h > 40.0 THEN 40.0 ELSE a.dedicacion_h END AS x
MERGE (a)-[f:PERTENECE_A]->(e)
SET f.grado = CASE
      WHEN e.tipo = 'hombro_izq' AND x <= e.centro THEN 1.0
      WHEN e.tipo = 'hombro_der' AND x >= e.centro THEN 1.0
      ELSE exp(-((x - e.centro)^2) / (2.0 * e.sigma^2)) END,
    f.valor_crisp = x, f.ts = datetime();

// 9.b SM1 - exigencia_grafica de cada juego
MATCH (j:Juego) WHERE j.exigencia IS NOT NULL
MATCH (v:VariableDifusa {nombre:'exigencia_grafica'})-[:TIENE_ETIQUETA]->(e:EtiquetaDifusa)
WITH j, e, j.exigencia AS x
MERGE (j)-[f:PERTENECE_A]->(e)
SET f.grado = CASE
      WHEN e.tipo = 'hombro_izq' AND x <= e.centro THEN 1.0
      WHEN e.tipo = 'hombro_der' AND x >= e.centro THEN 1.0
      ELSE exp(-((x - e.centro)^2) / (2.0 * e.sigma^2)) END,
    f.valor_crisp = x, f.ts = datetime();

// ---------------------------------------------------------------------
// 10. INFERENCIA DIFUSA (Mamdani: recorte, agregacion MAX, centroide)
// ---------------------------------------------------------------------
// 10.a SM1 - INT-RD1 a INT-RD3: peso de cada actividad en su perfil
MATCH (a:Actividad)-[f:PERTENECE_A]->(e:EtiquetaDifusa {variable:'dedicacion_h'})
WITH a, collect({et:e.nombre, mu:f.grado}) AS D
WITH a,
     [x IN D WHERE x.et = 'rara_vez' ][0].mu AS dRV,
     [x IN D WHERE x.et = 'ocasional'][0].mu AS dOC,
     [x IN D WHERE x.et = 'frecuente'][0].mu AS dFR,
     [x IN D WHERE x.et = 'principal'][0].mu AS dPR
WITH a, (CASE WHEN dRV > dOC THEN dRV ELSE dOC END) AS w1, dFR AS w2, dPR AS w3
MATCH (q1:Regla {id:'INT-RD1'}), (q2:Regla {id:'INT-RD2'}), (q3:Regla {id:'INT-RD3'})
FOREACH (_ IN CASE WHEN w1 > 0.01 THEN [1] ELSE [] END | MERGE (a)-[x:ACTIVA]->(q1) SET x.fuerza = round(w1, 3))
FOREACH (_ IN CASE WHEN w2 > 0.01 THEN [1] ELSE [] END | MERGE (a)-[x:ACTIVA]->(q2) SET x.fuerza = round(w2, 3))
FOREACH (_ IN CASE WHEN w3 > 0.01 THEN [1] ELSE [] END | MERGE (a)-[x:ACTIVA]->(q3) SET x.fuerza = round(w3, 3))
WITH a, w1, w2, w3
MATCH (sM:EtiquetaDifusa {variable:'peso_perfil', nombre:'marginal'}),
      (sR:EtiquetaDifusa {variable:'peso_perfil', nombre:'relevante'}),
      (sD:EtiquetaDifusa {variable:'peso_perfil', nombre:'determinante'})
UNWIND range(0, 100) AS i
WITH a, w1, w2, w3, sM, sR, sD, i / 100.0 AS y
WITH a, w1, w2, w3, y,
     exp(-((y - sM.centro)^2) / (2.0 * sM.sigma^2)) AS muM,
     exp(-((y - sR.centro)^2) / (2.0 * sR.sigma^2)) AS muR,
     exp(-((y - sD.centro)^2) / (2.0 * sD.sigma^2)) AS muD
WITH a, y,
     (CASE WHEN w1 < muM THEN w1 ELSE muM END) AS cM,
     (CASE WHEN w2 < muR THEN w2 ELSE muR END) AS cR,
     (CASE WHEN w3 < muD THEN w3 ELSE muD END) AS cD
WITH a, y, (CASE WHEN cM >= cR AND cM >= cD THEN cM
                 WHEN cR >= cD THEN cR ELSE cD END) AS agg
WITH a, sum(y * agg) AS num, sum(agg) AS den
SET a.grado = CASE WHEN den = 0 THEN null ELSE round(num / den, 3) END;

// Grado del perfil = MAX entre sus actividades; alfa-corte INT-R5
MATCH (u:Parametro {nombre:'umbral_exigencia'}), (bf:Parametro {nombre:'banda_frontera'})
MATCH (c:Requerimiento)-[:INCLUYE]->(a:Actividad)-[:APUNTA_A]->(p:Perfil)
WHERE a.grado IS NOT NULL
WITH u, bf, c, p, max(a.grado) AS grado
MERGE (c)-[r:PERTENECE]->(p)
SET r.grado = grado, r.origen = 'actividad declarada',
    r.impone_requisitos = (grado >= u.valor),
    r.en_frontera = (abs(grado - u.valor) <= bf.valor);

// Perfil dominante (INT-R11 a R13: el de mayor grado; empate -> mas exigente)
MATCH (c:Requerimiento)-[r:PERTENECE]->(p:Perfil)
WITH c, p, r ORDER BY r.grado DESC, p.ram_min DESC
WITH c, collect(p)[0] AS dom, collect(r)[0] AS rdom
SET c.perfil_dominante = dom.codigo, c.grado_perfil_dominante = rdom.grado
MERGE (c)-[:TIENE_PERFIL_DOMINANTE]->(dom)
WITH c, rdom.grado AS gmax
MATCH (c)-[r:PERTENECE]->(:Perfil)
WITH c, gmax, count(CASE WHEN r.grado = gmax THEN 1 END) AS empatados
MATCH (q11:Regla {id:'INT-R11'}), (q12:Regla {id:'INT-R12'})
MERGE (c)-[:ACTIVA]->(q11)
FOREACH (_ IN CASE WHEN empatados > 1 THEN [1] ELSE [] END | MERGE (c)-[:ACTIVA]->(q12));

// INT-R13 (reformulada en PG2, devolucion de PG1): si no se pudo determinar
// ningun perfil y la aclaracion quedo sin respuesta, el perfil dominante es
// 'indeterminado'. NO se asume OFI: OFI trae requisitos y pesos concretos y
// cambiaria que notebook se recomienda. El requerimiento no se evalua contra
// el catalogo hasta que se complete; se registra la alerta y la pregunta.
MATCH (c:Requerimiento)
WHERE NOT EXISTS { MATCH (c)-[:PERTENECE]->(:Perfil) }
  AND c.aclaracion = 'sin respuesta'
SET c.perfil_dominante = 'indeterminado', c.grado_perfil_dominante = null
MERGE (c)-[:GENERA]->(:Alerta {tipo:'Perfil indeterminado', submodulo_origen:'SM1',
  regla_origen:'INT-R13', requerimiento:c.id,
  mensaje:'El pedido no permite determinar el perfil de uso y la aclaracion no tuvo respuesta; no se asume ningun perfil'})
MERGE (c)-[:REQUIERE_ACLARACION]->(:Pregunta {requerimiento:c.id,
  texto:'Que programas o actividades va a usar con la notebook (por ejemplo: Office, programacion, diseno, juegos)?'})
WITH c
MATCH (q:Regla {id:'INT-R13'})
MERGE (c)-[:ACTIVA]->(q);

// 10.b SM1 - INT-RD4 a INT-RD7: intensidad grafica requerida
MATCH (c:Requerimiento)-[:INCLUYE]->(a:Actividad)-[:USA]->(j:Juego)
MATCH (a)-[fd:PERTENECE_A]->(ed:EtiquetaDifusa {variable:'dedicacion_h'})
WITH c, a, j, collect({et:ed.nombre, mu:fd.grado}) AS D
MATCH (j)-[fe:PERTENECE_A]->(ee:EtiquetaDifusa {variable:'exigencia_grafica'})
WITH c, D, collect({et:ee.nombre, mu:fe.grado}) AS E
WITH c,
     [x IN D WHERE x.et = 'rara_vez' ][0].mu AS dRV,
     [x IN D WHERE x.et = 'ocasional'][0].mu AS dOC,
     [x IN D WHERE x.et = 'frecuente'][0].mu AS dFR,
     [x IN D WHERE x.et = 'principal'][0].mu AS dPR,
     [x IN E WHERE x.et = 'baja' ][0].mu AS eB,
     [x IN E WHERE x.et = 'media'][0].mu AS eM,
     [x IN E WHERE x.et = 'alta' ][0].mu AS eA
WITH c, eB, eM, eA,
     (CASE WHEN dFR > dPR THEN dFR ELSE dPR END) AS dMucha,
     (CASE WHEN dRV > dOC THEN dRV ELSE dOC END) AS dPoca
WITH c, eB,
     (CASE WHEN eA < dMucha THEN eA ELSE dMucha END) AS w4,
     (CASE WHEN eA < dPoca  THEN eA ELSE dPoca  END) AS w5,
     (CASE WHEN eM < dMucha THEN eM ELSE dMucha END) AS w6,
     (CASE WHEN eM < dPoca  THEN eM ELSE dPoca  END) AS t7
WITH c, w4, w5, w6, (CASE WHEN eB > t7 THEN eB ELSE t7 END) AS w7
WITH c, max(w4) AS w4, max(w5) AS w5, max(w6) AS w6, max(w7) AS w7
MATCH (q4:Regla {id:'INT-RD4'}), (q5:Regla {id:'INT-RD5'}), (q6:Regla {id:'INT-RD6'}), (q7:Regla {id:'INT-RD7'})
FOREACH (_ IN CASE WHEN w4 > 0.01 THEN [1] ELSE [] END | MERGE (c)-[x:ACTIVA]->(q4) SET x.fuerza = round(w4, 3))
FOREACH (_ IN CASE WHEN w5 > 0.01 THEN [1] ELSE [] END | MERGE (c)-[x:ACTIVA]->(q5) SET x.fuerza = round(w5, 3))
FOREACH (_ IN CASE WHEN w6 > 0.01 THEN [1] ELSE [] END | MERGE (c)-[x:ACTIVA]->(q6) SET x.fuerza = round(w6, 3))
FOREACH (_ IN CASE WHEN w7 > 0.01 THEN [1] ELSE [] END | MERGE (c)-[x:ACTIVA]->(q7) SET x.fuerza = round(w7, 3))
WITH c, w4, w7, (CASE WHEN w5 > w6 THEN w5 ELSE w6 END) AS wMedia
MATCH (sB:EtiquetaDifusa {variable:'intensidad_grafica', nombre:'baja'}),
      (sM:EtiquetaDifusa {variable:'intensidad_grafica', nombre:'media'}),
      (sA:EtiquetaDifusa {variable:'intensidad_grafica', nombre:'alta'})
UNWIND range(0, 100) AS i
WITH c, w4, wMedia, w7, sB, sM, sA, i / 100.0 AS y
WITH c, sB, sM, sA, y,
     (CASE WHEN w7 < exp(-((y - sB.centro)^2)/(2.0*sB.sigma^2)) THEN w7
           ELSE exp(-((y - sB.centro)^2)/(2.0*sB.sigma^2)) END) AS cB,
     (CASE WHEN wMedia < exp(-((y - sM.centro)^2)/(2.0*sM.sigma^2)) THEN wMedia
           ELSE exp(-((y - sM.centro)^2)/(2.0*sM.sigma^2)) END) AS cMe,
     (CASE WHEN w4 < exp(-((y - sA.centro)^2)/(2.0*sA.sigma^2)) THEN w4
           ELSE exp(-((y - sA.centro)^2)/(2.0*sA.sigma^2)) END) AS cA
WITH c, sB, sM, sA, y, (CASE WHEN cB >= cMe AND cB >= cA THEN cB
                             WHEN cMe >= cA THEN cMe ELSE cA END) AS agg
WITH c, sB, sM, sA, sum(y * agg) / sum(agg) AS y0
WITH c, y0,
     exp(-((y0 - sB.centro)^2)/(2.0*sB.sigma^2)) AS mB,
     exp(-((y0 - sM.centro)^2)/(2.0*sM.sigma^2)) AS mM,
     exp(-((y0 - sA.centro)^2)/(2.0*sA.sigma^2)) AS mA
SET c.intensidad_valor = round(y0, 3),
    c.mu_int_baja = round(mB, 2), c.mu_int_media = round(mM, 2), c.mu_int_alta = round(mA, 2),
    c.intensidad_grafica = CASE WHEN mA >= mM AND mA >= mB THEN 'alta'
                                WHEN mM >= mB THEN 'media' ELSE 'baja' END;
