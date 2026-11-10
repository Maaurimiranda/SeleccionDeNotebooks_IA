// =====================================================================
// cypher/30_sm3.cypher
// Bloques del canonico: 9.c · 9.d · 9.e · 10.d · 10.e
// Duenio: de Coninck
// Origen: docs/cypher/Grupo_2_PG2_U1_corregido.cypher, cortado sin cambiar el contenido (PG3-02).
// =====================================================================

// 9.c SM3 - peso_kg
MATCH (n:Notebook)
MATCH (v:VariableDifusa {nombre:'peso_kg'})-[:TIENE_ETIQUETA]->(e:EtiquetaDifusa)
WITH n, e, n.peso_kg AS x
MERGE (n)-[f:PERTENECE_A]->(e)
SET f.grado = CASE
      WHEN e.tipo = 'hombro_izq' AND x <= e.centro THEN 1.0
      WHEN e.tipo = 'hombro_der' AND x >= e.centro THEN 1.0
      ELSE exp(-((x - e.centro)^2) / (2.0 * e.sigma^2)) END,
    f.valor_crisp = x, f.ts = datetime();

// 9.d SM3 - autonomia_h
MATCH (n:Notebook)-[:POSEE]->(b:Bateria) WHERE b.autonomia_usada_h IS NOT NULL
MATCH (v:VariableDifusa {nombre:'autonomia_h'})-[:TIENE_ETIQUETA]->(e:EtiquetaDifusa)
WITH b, e, b.autonomia_usada_h AS x
MERGE (b)-[f:PERTENECE_A]->(e)
SET f.grado = CASE
      WHEN e.tipo = 'hombro_izq' AND x <= e.centro THEN 1.0
      WHEN e.tipo = 'hombro_der' AND x >= e.centro THEN 1.0
      ELSE exp(-((x - e.centro)^2) / (2.0 * e.sigma^2)) END,
    f.valor_crisp = x, f.ts = datetime();

// 9.e SM3 - potencia_relativa de la GPU dedicada
MATCH (n:Notebook)-[:POSEE]->(g:GPU) WHERE g.potencia_relativa IS NOT NULL
MATCH (v:VariableDifusa {nombre:'potencia_relativa'})-[:TIENE_ETIQUETA]->(e:EtiquetaDifusa)
WITH g, e, g.potencia_relativa AS x
MERGE (g)-[f:PERTENECE_A]->(e)
SET f.grado = CASE
      WHEN e.tipo = 'hombro_izq' AND x <= e.centro THEN 1.0
      WHEN e.tipo = 'hombro_der' AND x >= e.centro THEN 1.0
      ELSE exp(-((x - e.centro)^2) / (2.0 * e.sigma^2)) END,
    f.valor_crisp = x, f.ts = datetime();


// 10.d SM3 - GM-RD1 a GM-RD3: adecuacion de movilidad
// (sale solo del peso y de la autonomia, no del perfil: es la unica
//  conclusion que queda en (:Notebook), porque vale igual para cualquier
//  comprador; lo que cambia con el pedido es su peso en la adecuacion global)
MATCH (n:Notebook)-[fp:PERTENECE_A]->(ep:EtiquetaDifusa {variable:'peso_kg'})
WITH n, collect({et:ep.nombre, mu:fp.grado}) AS P
MATCH (n)-[:POSEE]->(b:Bateria)-[fa:PERTENECE_A]->(ea:EtiquetaDifusa {variable:'autonomia_h'})
WITH n, P, collect({et:ea.nombre, mu:fa.grado}) AS A
WITH n,
     [x IN P WHERE x.et = 'liviana'   ][0].mu AS pL,
     [x IN P WHERE x.et = 'intermedia'][0].mu AS pI,
     [x IN P WHERE x.et = 'pesada'    ][0].mu AS pP,
     [x IN A WHERE x.et = 'baja' ][0].mu AS aB,
     [x IN A WHERE x.et = 'media'][0].mu AS aM,
     [x IN A WHERE x.et = 'alta' ][0].mu AS aA
WITH n, pL, pI, pP, aB, aM, aA, (CASE WHEN aM > aA THEN aM ELSE aA END) AS aMA
WITH n,
     (CASE WHEN pL < aA  THEN pL ELSE aA  END) AS w1,
     (CASE WHEN pL < aM  THEN pL ELSE aM  END) AS t1,
     (CASE WHEN pI < aMA THEN pI ELSE aMA END) AS t2,
     (CASE WHEN pP > aB  THEN pP ELSE aB  END) AS w3
WITH n, w1, (CASE WHEN t1 > t2 THEN t1 ELSE t2 END) AS w2, w3
MATCH (m1:Regla {id:'GM-RD1'}), (m2:Regla {id:'GM-RD2'}), (m3:Regla {id:'GM-RD3'})
FOREACH (_ IN CASE WHEN w1 > 0.01 THEN [1] ELSE [] END | MERGE (n)-[x:ACTIVA]->(m1) SET x.fuerza = round(w1, 3))
FOREACH (_ IN CASE WHEN w2 > 0.01 THEN [1] ELSE [] END | MERGE (n)-[x:ACTIVA]->(m2) SET x.fuerza = round(w2, 3))
FOREACH (_ IN CASE WHEN w3 > 0.01 THEN [1] ELSE [] END | MERGE (n)-[x:ACTIVA]->(m3) SET x.fuerza = round(w3, 3))
WITH n, w1, w2, w3
MATCH (sB:EtiquetaDifusa {variable:'adecuacion_movilidad', nombre:'baja'}),
      (sM:EtiquetaDifusa {variable:'adecuacion_movilidad', nombre:'media'}),
      (sA:EtiquetaDifusa {variable:'adecuacion_movilidad', nombre:'alta'})
UNWIND range(0, 100) AS i
WITH n, w1, w2, w3, sB, sM, sA, i / 100.0 AS y
WITH n, y, w1, w2, w3, sB, sM, sA,
     exp(-((y - sA.centro)^2)/(2.0*sA.sigma^2)) AS muA,
     exp(-((y - sM.centro)^2)/(2.0*sM.sigma^2)) AS muM,
     exp(-((y - sB.centro)^2)/(2.0*sB.sigma^2)) AS muB
WITH n, y, sB, sM, sA,
     (CASE WHEN w1 < muA THEN w1 ELSE muA END) AS cA,
     (CASE WHEN w2 < muM THEN w2 ELSE muM END) AS cM,
     (CASE WHEN w3 < muB THEN w3 ELSE muB END) AS cB
WITH n, y, sB, sM, sA, (CASE WHEN cA >= cM AND cA >= cB THEN cA
                             WHEN cM >= cB THEN cM ELSE cB END) AS agg
WITH n, sB, sM, sA, sum(y * agg) / sum(agg) AS y0
WITH n, y0,
     exp(-((y0 - sB.centro)^2)/(2.0*sB.sigma^2)) AS mB,
     exp(-((y0 - sM.centro)^2)/(2.0*sM.sigma^2)) AS mM,
     exp(-((y0 - sA.centro)^2)/(2.0*sA.sigma^2)) AS mA
SET n.adecuacion_movilidad = round(y0, 3),
    n.movilidad_etiqueta = CASE WHEN mA >= mM AND mA >= mB THEN 'alta'
                                 WHEN mM >= mB THEN 'media' ELSE 'baja' END;

// 10.e SM3 - GM-RD4 a GM-RD6: grado de la GPU dedicada, por evaluacion
// (el margen de gama se mide contra el perfil de cada pedido)
MATCH (c:Requerimiento)-[:TIENE_PERFIL_DOMINANTE]->(pf:Perfil)
MATCH (c)-[:EVALUA]->(ev:Evaluacion)-[:SOBRE]->(n:Notebook)-[:POSEE]->(g:GPU)-[:ES_DE_GAMA]->(gg:GamaGPU)
WHERE g.dedicada AND g.potencia_relativa IS NOT NULL AND pf.gama_gpu_min - gg.indice <= 1
WITH ev, g, pf.gama_gpu_min - gg.indice AS brecha
MATCH (g)-[fq:PERTENECE_A]->(eq:EtiquetaDifusa {variable:'potencia_relativa'})
WITH ev, brecha, collect({et:eq.nombre, mu:fq.grado}) AS Q
WITH ev, brecha,
     (CASE WHEN brecha < 0 THEN 1.0 ELSE 0.0 END) AS mS,
     (CASE WHEN brecha = 0 THEN 1.0 ELSE 0.0 END) AS mJ,
     (CASE WHEN brecha = 1 THEN 1.0 ELSE 0.0 END) AS mI,
     [x IN Q WHERE x.et = 'restringida'][0].mu AS qR,
     [x IN Q WHERE x.et = 'moderada'   ][0].mu AS qM,
     [x IN Q WHERE x.et = 'plena'      ][0].mu AS qP
WITH ev, brecha, mS, mJ, mI, qR, qM, qP,
     (CASE WHEN qM > qP THEN qM ELSE qP END) AS qMP,
     (CASE WHEN qR > qM THEN qR ELSE qM END) AS qRM
WITH ev, brecha,
     (CASE WHEN (CASE WHEN mS < qMP THEN mS ELSE qMP END) > (CASE WHEN mJ < qP THEN mJ ELSE qP END)
           THEN (CASE WHEN mS < qMP THEN mS ELSE qMP END)
           ELSE (CASE WHEN mJ < qP THEN mJ ELSE qP END) END) AS w4,
     reduce(m = 0.0, t IN [(CASE WHEN mS < qR THEN mS ELSE qR END),
                           (CASE WHEN mJ < qM THEN mJ ELSE qM END),
                           (CASE WHEN mI < qP THEN mI ELSE qP END)]
            | CASE WHEN t > m THEN t ELSE m END) AS w5,
     (CASE WHEN (CASE WHEN mJ < qR THEN mJ ELSE qR END) > (CASE WHEN mI < qRM THEN mI ELSE qRM END)
           THEN (CASE WHEN mJ < qR THEN mJ ELSE qR END)
           ELSE (CASE WHEN mI < qRM THEN mI ELSE qRM END) END) AS w6
MATCH (g4:Regla {id:'GM-RD4'}), (g5:Regla {id:'GM-RD5'}), (g6:Regla {id:'GM-RD6'})
FOREACH (_ IN CASE WHEN w4 > 0.01 THEN [1] ELSE [] END | MERGE (ev)-[x:ACTIVA]->(g4) SET x.fuerza = round(w4, 3))
FOREACH (_ IN CASE WHEN w5 > 0.01 THEN [1] ELSE [] END | MERGE (ev)-[x:ACTIVA]->(g5) SET x.fuerza = round(w5, 3))
FOREACH (_ IN CASE WHEN w6 > 0.01 THEN [1] ELSE [] END | MERGE (ev)-[x:ACTIVA]->(g6) SET x.fuerza = round(w6, 3))
WITH ev, brecha, w4, w5, w6
MATCH (sI:EtiquetaDifusa {variable:'grado_gpu', nombre:'insuficiente'}),
      (sP:EtiquetaDifusa {variable:'grado_gpu', nombre:'parcial'}),
      (sL:EtiquetaDifusa {variable:'grado_gpu', nombre:'pleno'})
UNWIND range(0, 100) AS i
WITH ev, brecha, w4, w5, w6, sI, sP, sL, i / 100.0 AS y
WITH ev, brecha, y, w4, w5, w6,
     exp(-((y - sL.centro)^2)/(2.0*sL.sigma^2)) AS muL,
     exp(-((y - sP.centro)^2)/(2.0*sP.sigma^2)) AS muP,
     exp(-((y - sI.centro)^2)/(2.0*sI.sigma^2)) AS muI
WITH ev, brecha, y,
     (CASE WHEN w4 < muL THEN w4 ELSE muL END) AS cL,
     (CASE WHEN w5 < muP THEN w5 ELSE muP END) AS cP,
     (CASE WHEN w6 < muI THEN w6 ELSE muI END) AS cI
WITH ev, brecha, y, (CASE WHEN cL >= cP AND cL >= cI THEN cL
                         WHEN cP >= cI THEN cP ELSE cI END) AS agg
WITH ev, brecha, sum(y * agg) / sum(agg) AS g0
SET ev.grado_gpu = round(g0, 3),
    ev.margen_gama = CASE WHEN brecha < 0 THEN 'superior'
                          WHEN brecha = 0 THEN 'justa' ELSE 'inferior' END;

// Las GPU integradas que cumplen la gama del perfil no pasan por S2 (GM-R3)
MATCH (c:Requerimiento)-[:TIENE_PERFIL_DOMINANTE]->(pf:Perfil)
MATCH (c)-[:EVALUA]->(ev:Evaluacion)-[:SOBRE]->(n:Notebook)-[:POSEE]->(g:GPU)-[:ES_DE_GAMA]->(gg:GamaGPU)
WHERE NOT g.dedicada AND gg.indice >= pf.gama_gpu_min
SET ev.grado_gpu = 1.0,
    ev.margen_gama = CASE WHEN gg.indice > pf.gama_gpu_min THEN 'superior' ELSE 'justa' END
WITH ev
MATCH (q:Regla {id:'GM-R3'})
MERGE (ev)-[:ACTIVA]->(q);

// GM-R4: GPU por debajo de la gama del perfil sin graduacion difusa
// (integrada un nivel abajo -> P_GRADO_GPU_UN_NIVEL_ABAJO; dos o mas -> 0).
// Ningun pedido de la prueba la dispara: VIRT y OFI piden gama 1, y
// ningun perfil pide mas que la gama de la dedicada del catalogo (4).
MATCH (u:Parametro {nombre:'P_GRADO_GPU_UN_NIVEL_ABAJO'})
MATCH (c:Requerimiento)-[:TIENE_PERFIL_DOMINANTE]->(pf:Perfil)
MATCH (c)-[:EVALUA]->(ev:Evaluacion)-[:SOBRE]->(:Notebook)-[:POSEE]->(g:GPU)-[:ES_DE_GAMA]->(gg:GamaGPU)
WITH u, ev, g, pf.gama_gpu_min - gg.indice AS brecha
WHERE (NOT g.dedicada AND brecha >= 1) OR (g.dedicada AND brecha >= 2)
SET ev.grado_gpu = CASE WHEN brecha = 1 THEN u.valor ELSE 0.0 END,
    ev.margen_gama = CASE WHEN brecha = 1 THEN 'inferior' ELSE 'dos o mas niveles abajo' END
WITH ev
MATCH (q:Regla {id:'GM-R4'})
MERGE (ev)-[:ACTIVA]->(q);

// GM-R8 reformulada: alerta de potencia grafica reducida (contra el grado que
// daria GM-R4 por la sola gama)
MATCH (d:Parametro {nombre:'P_DIF_ALERTA_TGP'}), (u:Parametro {nombre:'P_GRADO_GPU_UN_NIVEL_ABAJO'})
MATCH (ev:Evaluacion)-[:SOBRE]->(n:Notebook)-[:POSEE]->(g:GPU)
WHERE ev.grado_gpu IS NOT NULL AND g.potencia_relativa IS NOT NULL
  AND (CASE WHEN ev.margen_gama = 'inferior' THEN u.valor ELSE 1.0 END) - ev.grado_gpu > d.valor
MERGE (ev)-[:GENERA]->(:Alerta {tipo:'Potencia grafica reducida', submodulo_origen:'SM3',
  regla_origen:'GM-R8', requerimiento:ev.requerimiento, notebook:n.modelo,
  mensaje:'El TGP configurado (' + toString(g.tgp_w) + ' W de ' + toString(g.tgp_max_w) +
          ' W) reduce el rendimiento de la GPU respecto de su gama'});

// Adecuacion grafica (promedio ponderado de GPU y pantalla; se mantiene crisp)
MATCH (pg:Parametro {nombre:'P_PESO_GPU_GRAFICA'}), (pp:Parametro {nombre:'P_PESO_PANTALLA_GRAFICA'})
MATCH (ev:Evaluacion) WHERE ev.grado_gpu IS NOT NULL
SET ev.adecuacion_grafica = round(pg.valor * ev.grado_gpu + pp.valor * ev.grado_pantalla, 3);
