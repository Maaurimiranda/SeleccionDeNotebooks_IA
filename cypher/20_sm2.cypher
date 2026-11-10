// =====================================================================
// cypher/20_sm2.cypher
// Bloques del canonico: 10.c.1 · 10.c.2
// Duenio: Miranda
// Origen: docs/cypher/Grupo_2_PG2_U1_corregido.cypher, cortado sin cambiar el contenido (PG3-02).
// =====================================================================

// 10.c.1 Entradas de SM2 normalizadas contra el perfil de cada evaluacion:
// suficiencia rho = ram / RAM minima; indice a con las ranuras libres y el
// margen hasta el maximo sobre la RAM recomendada (vacio si se desconoce)
MATCH (wr:Parametro {nombre:'P_PESO_RANURAS_AMPLIABILIDAD'}), (rr:Parametro {nombre:'P_RANURAS_REFERENCIA'})
MATCH (c:Requerimiento)-[:TIENE_PERFIL_DOMINANTE]->(pf:Perfil)
MATCH (c)-[:EVALUA]->(ev:Evaluacion)-[:SOBRE]->(n:Notebook)-[:POSEE]->(r:RAM)
SET ev.suficiencia_rho = CASE WHEN r.ram_gb / toFloat(pf.ram_min) > 3.0 THEN 3.0
                              ELSE r.ram_gb / toFloat(pf.ram_min) END,
    ev.indice_ampliabilidad = CASE WHEN r.ranuras_libres IS NULL OR r.max_gb IS NULL THEN null ELSE
        wr.valor * (CASE WHEN r.ranuras_libres > rr.valor THEN rr.valor ELSE r.ranuras_libres END) / rr.valor
      + (1.0 - wr.valor) * (CASE WHEN (r.max_gb - r.ram_gb) / toFloat(pf.ram_rec) > 1.0 THEN 1.0
                                 ELSE (r.max_gb - r.ram_gb) / toFloat(pf.ram_rec) END) END;

MATCH (ev:Evaluacion) WHERE ev.suficiencia_rho IS NOT NULL
MATCH (v:VariableDifusa {nombre:'suficiencia_ram'})-[:TIENE_ETIQUETA]->(e:EtiquetaDifusa)
WITH ev, e, ev.suficiencia_rho AS x
MERGE (ev)-[f:PERTENECE_A]->(e)
SET f.grado = CASE
      WHEN e.tipo = 'hombro_izq' AND x <= e.centro THEN 1.0
      WHEN e.tipo = 'hombro_der' AND x >= e.centro THEN 1.0
      ELSE exp(-((x - e.centro)^2) / (2.0 * e.sigma^2)) END,
    f.valor_crisp = x, f.ts = datetime();

MATCH (ev:Evaluacion) WHERE ev.indice_ampliabilidad IS NOT NULL
MATCH (v:VariableDifusa {nombre:'indice_ampliabilidad'})-[:TIENE_ETIQUETA]->(e:EtiquetaDifusa)
WITH ev, e, ev.indice_ampliabilidad AS x
MERGE (ev)-[f:PERTENECE_A]->(e)
SET f.grado = CASE
      WHEN e.tipo = 'hombro_izq' AND x <= e.centro THEN 1.0
      WHEN e.tipo = 'hombro_der' AND x >= e.centro THEN 1.0
      ELSE exp(-((x - e.centro)^2) / (2.0 * e.sigma^2)) END,
    f.valor_crisp = x, f.ts = datetime();

// 10.c.2 FZ-R1 a FZ-R5 sobre cada evaluacion. La traza [:ACTIVA] sale de la
// evaluacion, asi que cada recomendacion conserva sus propias activaciones.
MATCH (ev:Evaluacion)-[fs:PERTENECE_A]->(es:EtiquetaDifusa {variable:'suficiencia_ram'})
WITH ev, collect({et:es.nombre, mu:fs.grado}) AS S
MATCH (ev)-[fa:PERTENECE_A]->(ea:EtiquetaDifusa {variable:'indice_ampliabilidad'})
WITH ev, S, collect({et:ea.nombre, mu:fa.grado}) AS A
WITH ev,
     [x IN S WHERE x.et = 'insuficiente'][0].mu AS sIN,
     [x IN S WHERE x.et = 'justa'       ][0].mu AS sJU,
     [x IN S WHERE x.et = 'suficiente'  ][0].mu AS sSU,
     [x IN S WHERE x.et = 'holgada'     ][0].mu AS sHO,
     [x IN A WHERE x.et = 'poca' ][0].mu AS aPO,
     [x IN A WHERE x.et = 'media'][0].mu AS aME,
     [x IN A WHERE x.et = 'mucha'][0].mu AS aMU
WITH ev, sIN, sJU, sSU, sHO, aPO, (CASE WHEN aME > aMU THEN aME ELSE aMU END) AS aSi
WITH ev,
     (CASE WHEN sIN < aPO THEN sIN ELSE aPO END) AS w1,
     (CASE WHEN sIN < aSi THEN sIN ELSE aSi END) AS w2,
     (CASE WHEN sJU < aPO THEN sJU ELSE aPO END) AS w3,
     (CASE WHEN sJU < aSi THEN sJU ELSE aSi END) AS w4,
     (CASE WHEN sSU > sHO THEN sSU ELSE sHO END) AS w5
MATCH (f1:Regla {id:'FZ-R1'}), (f2:Regla {id:'FZ-R2'}), (f3:Regla {id:'FZ-R3'}),
      (f4:Regla {id:'FZ-R4'}), (f5:Regla {id:'FZ-R5'})
FOREACH (_ IN CASE WHEN w1 > 0.01 THEN [1] ELSE [] END | MERGE (ev)-[x:ACTIVA]->(f1) SET x.fuerza = round(w1, 3))
FOREACH (_ IN CASE WHEN w2 > 0.01 THEN [1] ELSE [] END | MERGE (ev)-[x:ACTIVA]->(f2) SET x.fuerza = round(w2, 3))
FOREACH (_ IN CASE WHEN w3 > 0.01 THEN [1] ELSE [] END | MERGE (ev)-[x:ACTIVA]->(f3) SET x.fuerza = round(w3, 3))
FOREACH (_ IN CASE WHEN w4 > 0.01 THEN [1] ELSE [] END | MERGE (ev)-[x:ACTIVA]->(f4) SET x.fuerza = round(w4, 3))
FOREACH (_ IN CASE WHEN w5 > 0.01 THEN [1] ELSE [] END | MERGE (ev)-[x:ACTIVA]->(f5) SET x.fuerza = round(w5, 3))
// agregacion MAX por etiqueta de salida, leyendo el consecuente de cada regla
WITH ev, [{e:f1.etiqueta_consecuente, w:w1}, {e:f2.etiqueta_consecuente, w:w2},
          {e:f3.etiqueta_consecuente, w:w3}, {e:f4.etiqueta_consecuente, w:w4},
          {e:f5.etiqueta_consecuente, w:w5}] AS acts
WITH ev,
     reduce(m = 0.0, x IN acts | CASE WHEN x.e = 'alto'  AND x.w > m THEN x.w ELSE m END) AS wAlto,
     reduce(m = 0.0, x IN acts | CASE WHEN x.e = 'medio' AND x.w > m THEN x.w ELSE m END) AS wMedio,
     reduce(m = 0.0, x IN acts | CASE WHEN x.e = 'bajo'  AND x.w > m THEN x.w ELSE m END) AS wBajo
MATCH (sB:EtiquetaDifusa {variable:'riesgo_obsolescencia', nombre:'bajo'}),
      (sM:EtiquetaDifusa {variable:'riesgo_obsolescencia', nombre:'medio'}),
      (sA:EtiquetaDifusa {variable:'riesgo_obsolescencia', nombre:'alto'})
UNWIND range(0, 100) AS i
WITH ev, wAlto, wMedio, wBajo, sB, sM, sA, toFloat(i) AS y
WITH ev, sB, sM, sA, y,
     (CASE WHEN wBajo < (CASE WHEN y <= sB.centro THEN 1.0
                              ELSE exp(-((y - sB.centro)^2)/(2.0*sB.sigma^2)) END)
           THEN wBajo ELSE (CASE WHEN y <= sB.centro THEN 1.0
                                 ELSE exp(-((y - sB.centro)^2)/(2.0*sB.sigma^2)) END) END) AS cB,
     (CASE WHEN wMedio < exp(-((y - sM.centro)^2)/(2.0*sM.sigma^2))
           THEN wMedio ELSE exp(-((y - sM.centro)^2)/(2.0*sM.sigma^2)) END) AS cM,
     (CASE WHEN wAlto < (CASE WHEN y >= sA.centro THEN 1.0
                              ELSE exp(-((y - sA.centro)^2)/(2.0*sA.sigma^2)) END)
           THEN wAlto ELSE (CASE WHEN y >= sA.centro THEN 1.0
                                 ELSE exp(-((y - sA.centro)^2)/(2.0*sA.sigma^2)) END) END) AS cA
WITH ev, sB, sM, sA, y, (CASE WHEN cB >= cM AND cB >= cA THEN cB
                               WHEN cM >= cA THEN cM ELSE cA END) AS agg
WITH ev, sB, sM, sA, sum(y * agg) / sum(agg) AS y0
WITH ev, y0,
     (CASE WHEN y0 <= sB.centro THEN 1.0 ELSE exp(-((y0 - sB.centro)^2)/(2.0*sB.sigma^2)) END) AS mB,
     exp(-((y0 - sM.centro)^2)/(2.0*sM.sigma^2)) AS mM,
     (CASE WHEN y0 >= sA.centro THEN 1.0 ELSE exp(-((y0 - sA.centro)^2)/(2.0*sA.sigma^2)) END) AS mA
SET ev.riesgo_valor = round(y0, 2),
    ev.riesgo_etiqueta = CASE WHEN mA >= mM AND mA >= mB THEN 'alto'
                               WHEN mM >= mB THEN 'medio' ELSE 'bajo' END;

// FZ-R6: ampliabilidad desconocida -> rango [mejor ; peor] con a = 1 y a = 0.
// Se crean dos lecturas hipoteticas de la evaluacion, se fuzifican y se
// evaluan las mismas reglas.
MATCH (ev:Evaluacion)-[:SOBRE]->(:Notebook)-[:POSEE]->(r:RAM)
WHERE r.ampliabilidad = 'desconocida'
MERGE (ev)-[:TIENE_LECTURA]->(:Lectura {escenario:'mejor', dato:'indice_ampliabilidad',
                                        evaluacion:ev.requerimiento + '/' + ev.notebook, indice_ampliabilidad:1.0})
MERGE (ev)-[:TIENE_LECTURA]->(:Lectura {escenario:'peor',  dato:'indice_ampliabilidad',
                                        evaluacion:ev.requerimiento + '/' + ev.notebook, indice_ampliabilidad:0.0});

MATCH (:Evaluacion)-[:TIENE_LECTURA]->(l:Lectura {dato:'indice_ampliabilidad'})
MATCH (v:VariableDifusa {nombre:'indice_ampliabilidad'})-[:TIENE_ETIQUETA]->(e:EtiquetaDifusa)
WITH l, e, l.indice_ampliabilidad AS x
MERGE (l)-[f:PERTENECE_A]->(e)
SET f.grado = CASE
      WHEN e.tipo = 'hombro_izq' AND x <= e.centro THEN 1.0
      WHEN e.tipo = 'hombro_der' AND x >= e.centro THEN 1.0
      ELSE exp(-((x - e.centro)^2) / (2.0 * e.sigma^2)) END,
    f.valor_crisp = x;

// FZ-R6 (segunda parte): FZ-R1 a FZ-R5 sobre cada lectura; el rango
// [mejor ; peor] queda en la evaluacion, sin asignarle un valor unico.
MATCH (ev:Evaluacion)-[:TIENE_LECTURA]->(l:Lectura {dato:'indice_ampliabilidad'})
MATCH (ev)-[fs:PERTENECE_A]->(es:EtiquetaDifusa {variable:'suficiencia_ram'})
WITH ev, l, collect({et:es.nombre, mu:fs.grado}) AS S
MATCH (l)-[fa:PERTENECE_A]->(ea:EtiquetaDifusa {variable:'indice_ampliabilidad'})
WITH ev, l, S, collect({et:ea.nombre, mu:fa.grado}) AS A
WITH ev, l,
     [x IN S WHERE x.et = 'insuficiente'][0].mu AS sIN,
     [x IN S WHERE x.et = 'justa'       ][0].mu AS sJU,
     [x IN S WHERE x.et = 'suficiente'  ][0].mu AS sSU,
     [x IN S WHERE x.et = 'holgada'     ][0].mu AS sHO,
     [x IN A WHERE x.et = 'poca' ][0].mu AS aPO,
     [x IN A WHERE x.et = 'media'][0].mu AS aME,
     [x IN A WHERE x.et = 'mucha'][0].mu AS aMU
WITH ev, l, sIN, sJU, sSU, sHO, aPO, (CASE WHEN aME > aMU THEN aME ELSE aMU END) AS aSi
WITH ev, l,
     (CASE WHEN sIN < aPO THEN sIN ELSE aPO END) AS w1,
     (CASE WHEN sIN < aSi THEN sIN ELSE aSi END) AS w2,
     (CASE WHEN sJU < aPO THEN sJU ELSE aPO END) AS w3,
     (CASE WHEN sJU < aSi THEN sJU ELSE aSi END) AS w4,
     (CASE WHEN sSU > sHO THEN sSU ELSE sHO END) AS w5
MATCH (f1:Regla {id:'FZ-R1'}), (f2:Regla {id:'FZ-R2'}), (f3:Regla {id:'FZ-R3'}),
      (f4:Regla {id:'FZ-R4'}), (f5:Regla {id:'FZ-R5'}), (f6:Regla {id:'FZ-R6'})
MERGE (ev)-[:ACTIVA]->(f6)
FOREACH (_ IN CASE WHEN w1 > 0.01 THEN [1] ELSE [] END | MERGE (l)-[x:ACTIVA]->(f1) SET x.fuerza = round(w1, 3))
FOREACH (_ IN CASE WHEN w2 > 0.01 THEN [1] ELSE [] END | MERGE (l)-[x:ACTIVA]->(f2) SET x.fuerza = round(w2, 3))
FOREACH (_ IN CASE WHEN w3 > 0.01 THEN [1] ELSE [] END | MERGE (l)-[x:ACTIVA]->(f3) SET x.fuerza = round(w3, 3))
FOREACH (_ IN CASE WHEN w4 > 0.01 THEN [1] ELSE [] END | MERGE (l)-[x:ACTIVA]->(f4) SET x.fuerza = round(w4, 3))
FOREACH (_ IN CASE WHEN w5 > 0.01 THEN [1] ELSE [] END | MERGE (l)-[x:ACTIVA]->(f5) SET x.fuerza = round(w5, 3))
// agregacion MAX por etiqueta de salida, leyendo el consecuente de cada regla
WITH ev, l, [{e:f1.etiqueta_consecuente, w:w1}, {e:f2.etiqueta_consecuente, w:w2},
          {e:f3.etiqueta_consecuente, w:w3}, {e:f4.etiqueta_consecuente, w:w4},
          {e:f5.etiqueta_consecuente, w:w5}] AS acts
WITH ev, l,
     reduce(m = 0.0, x IN acts | CASE WHEN x.e = 'alto'  AND x.w > m THEN x.w ELSE m END) AS wAlto,
     reduce(m = 0.0, x IN acts | CASE WHEN x.e = 'medio' AND x.w > m THEN x.w ELSE m END) AS wMedio,
     reduce(m = 0.0, x IN acts | CASE WHEN x.e = 'bajo'  AND x.w > m THEN x.w ELSE m END) AS wBajo
MATCH (sB:EtiquetaDifusa {variable:'riesgo_obsolescencia', nombre:'bajo'}),
      (sM:EtiquetaDifusa {variable:'riesgo_obsolescencia', nombre:'medio'}),
      (sA:EtiquetaDifusa {variable:'riesgo_obsolescencia', nombre:'alto'})
UNWIND range(0, 100) AS i
WITH ev, l, wAlto, wMedio, wBajo, sB, sM, sA, toFloat(i) AS y
WITH ev, l, sB, sM, sA, y,
     (CASE WHEN wBajo < (CASE WHEN y <= sB.centro THEN 1.0
                              ELSE exp(-((y - sB.centro)^2)/(2.0*sB.sigma^2)) END)
           THEN wBajo ELSE (CASE WHEN y <= sB.centro THEN 1.0
                                 ELSE exp(-((y - sB.centro)^2)/(2.0*sB.sigma^2)) END) END) AS cB,
     (CASE WHEN wMedio < exp(-((y - sM.centro)^2)/(2.0*sM.sigma^2))
           THEN wMedio ELSE exp(-((y - sM.centro)^2)/(2.0*sM.sigma^2)) END) AS cM,
     (CASE WHEN wAlto < (CASE WHEN y >= sA.centro THEN 1.0
                              ELSE exp(-((y - sA.centro)^2)/(2.0*sA.sigma^2)) END)
           THEN wAlto ELSE (CASE WHEN y >= sA.centro THEN 1.0
                                 ELSE exp(-((y - sA.centro)^2)/(2.0*sA.sigma^2)) END) END) AS cA
WITH ev, l, sB, sM, sA, y, (CASE WHEN cB >= cM AND cB >= cA THEN cB
                               WHEN cM >= cA THEN cM ELSE cA END) AS agg
WITH ev, l, sB, sM, sA, sum(y * agg) / sum(agg) AS y0
SET l.riesgo_valor = round(y0, 2);

// La etiqueta del rango se toma del peor caso, con el mismo criterio que el
// resto del sistema: la etiqueta de mayor pertenencia del valor desborrosificado.
MATCH (ev:Evaluacion)-[:TIENE_LECTURA]->(l:Lectura {dato:'indice_ampliabilidad'})
WITH ev, min(l.riesgo_valor) AS mejor, max(l.riesgo_valor) AS peor
MATCH (sB:EtiquetaDifusa {variable:'riesgo_obsolescencia', nombre:'bajo'}),
      (sM:EtiquetaDifusa {variable:'riesgo_obsolescencia', nombre:'medio'}),
      (sA:EtiquetaDifusa {variable:'riesgo_obsolescencia', nombre:'alto'})
WITH ev, mejor, peor,
     (CASE WHEN peor <= sB.centro THEN 1.0 ELSE exp(-((peor - sB.centro)^2)/(2.0*sB.sigma^2)) END) AS mB,
     exp(-((peor - sM.centro)^2)/(2.0*sM.sigma^2)) AS mM,
     (CASE WHEN peor >= sA.centro THEN 1.0 ELSE exp(-((peor - sA.centro)^2)/(2.0*sA.sigma^2)) END) AS mA
SET ev.riesgo_min = mejor, ev.riesgo_max = peor,
    ev.riesgo_etiqueta = CASE WHEN mA >= mM AND mA >= mB THEN 'alto'
                               WHEN mM >= mB THEN 'medio' ELSE 'bajo' END;

// Alertas: las que comparan contra el perfil o el pedido cuelgan de la
// evaluacion; las que describen un hueco de la ficha cuelgan de la notebook,
// porque valen para cualquier comprador.
// FZ-R7: alerta cuando la etiqueta dominante del riesgo es alto
MATCH (ev:Evaluacion)-[:SOBRE]->(n:Notebook)
WHERE ev.riesgo_etiqueta = 'alto'
MERGE (ev)-[:GENERA]->(:Alerta {tipo:'Riesgo de obsolescencia', submodulo_origen:'SM2',
  regla_origen:'FZ-R7', requerimiento:ev.requerimiento, notebook:n.modelo,
  mensaje:'Riesgo alto de que la RAM quede corta para el perfil: ' +
          coalesce(toString(ev.riesgo_valor), '[' + toString(ev.riesgo_min) + ' ; ' + toString(ev.riesgo_max) + ']') +
          ' sobre 100'});

// REN-R10: alerta de ampliabilidad no verificada
MATCH (n:Notebook)-[:POSEE]->(r:RAM) WHERE r.ampliabilidad = 'desconocida'
MERGE (n)-[:GENERA]->(:Alerta {tipo:'Ampliabilidad no verificada', submodulo_origen:'SM2',
  regla_origen:'REN-R10', notebook:n.modelo,
  mensaje:'La ficha no informa si la RAM es ampliable: el riesgo se informa como rango'});

// REN-R7: RAM ampliable por debajo del minimo -> condicionado a ampliacion
// (no se descarta por la RAM; el costo del modulo sale del catalogo)
MATCH (cm:Parametro {nombre:'P_COSTO_MODULO_RAM_USD'})
MATCH (c:Requerimiento)-[:TIENE_PERFIL_DOMINANTE]->(pf:Perfil)
MATCH (c)-[:EVALUA]->(ev:Evaluacion)-[:SOBRE]->(n:Notebook)-[:POSEE]->(r:RAM)
WHERE r.ram_gb < pf.ram_min AND r.ampliabilidad = 'ampliable'
MERGE (ev)-[:GENERA]->(:Alerta {tipo:'Condicionado a ampliacion', submodulo_origen:'SM2',
  regla_origen:'REN-R7', requerimiento:c.id, notebook:n.modelo,
  mensaje:'La RAM no llega al minimo del perfil, pero se puede ampliar con un modulo de unos ' +
          toString(toInteger(cm.valor)) + ' USD'});
