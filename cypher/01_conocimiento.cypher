// =====================================================================
// cypher/01_conocimiento.cypher
// Bloques del canonico: 3 perfiles y requisitos · 4 variables difusas · 5 reglas y parametros · 6 lexico y gamas
// Duenio: Miranda
// Origen: docs/cypher/Grupo_2_PG2_U1_corregido.cypher, cortado sin cambiar el contenido (PG3-02).
// =====================================================================

// ---------------------------------------------------------------------
// 3. PERFILES DE USO Y TABLA DE REQUISITOS POR PERFIL
//    (valores documentales de PG1 f); pesos del Anexo D de SM4 (P7,
//    REC-R4); 'ram_sobra' queda nulo en los perfiles que la entrevista no
//    cubre: P11 del catalogo de la PI2 de SM4, pendiente)
// ---------------------------------------------------------------------
UNWIND [
  {c:'OFI',   rmin: 8, rrec:16, rsob:32,   smin: 512, cpu:'entrada', gpu:1, virt:false, pr:0.40, pg:0.10, pm:0.50,
   fund:'Navegador y suites ofimaticas; pesa mas la movilidad que la potencia'},
  {c:'DEV',   rmin:16, rrec:32, rsob:null, smin:1024, cpu:'media',   gpu:1, virt:false, pr:0.60, pg:0.10, pm:0.30,
   fund:'Los IDE y la compilacion exigen CPU y almacenamiento agiles (Android Studio, IntelliJ)'},
  {c:'VIRT',  rmin:16, rrec:32, rsob:null, smin: 512, cpu:'media',   gpu:1, virt:true,  pr:0.70, pg:0.10, pm:0.20,
   fund:'Docker, WSL2 y los hipervisores exigen virtualizacion por hardware y cada VM reserva RAM propia'},
  {c:'DIS',   rmin:16, rrec:32, rsob:32,   smin:1024, cpu:'media',   gpu:3, virt:false, pr:0.40, pg:0.50, pm:0.10,
   fund:'La fidelidad de color es parte del trabajo (requisitos de Adobe): sRGB >= 95 %'},
  {c:'VID3D', rmin:16, rrec:32, rsob:null, smin:1024, cpu:'alta',    gpu:4, virt:false, pr:0.50, pg:0.40, pm:0.10,
   fund:'El render sostiene GPU y CPU por tiempos largos (DaVinci Resolve)'},
  {c:'GAM',   rmin:16, rrec:32, rsob:32,   smin: 512, cpu:'media',   gpu:3, virt:false, pr:0.30, pg:0.60, pm:0.10,
   fund:'La exigencia grafica depende del juego y la tasa de refresco da fluidez (Steam, Notebookcheck)'},
  {c:'DATOS', rmin:16, rrec:32, rsob:null, smin:1024, cpu:'alta',    gpu:4, virt:false, pr:0.70, pg:0.10, pm:0.20,
   fund:'El software de entrenamiento necesita CUDA (PyTorch)'}
] AS p
MERGE (x:Perfil {codigo:p.c})
SET x.ram_min = p.rmin, x.ram_rec = p.rrec, x.ram_sobra = p.rsob,
    x.ssd_min = p.smin, x.gama_cpu_min = p.cpu, x.gama_gpu_min = p.gpu,
    x.requiere_virtualizacion = p.virt,
    x.peso_rendimiento = p.pr, x.peso_grafica = p.pg, x.peso_movilidad = p.pm,
    x.fundamento = p.fund;

MATCH (f:Frame {nombre:'Perfil de uso'}), (p:Perfil)
MERGE (p)-[:INSTANCIA_DE]->(f);

// Requisitos derivados del perfil (la relacion EXIGE de PG1 e)
MATCH (p:Perfil)
MERGE (p)-[:EXIGE]->(r1:Requisito {criterio:'ram_gb', perfil:p.codigo})
SET r1.valor_min = p.ram_min, r1.valor_rec = p.ram_rec, r1.es_excluyente = false
MERGE (p)-[:EXIGE]->(r2:Requisito {criterio:'ssd_gb', perfil:p.codigo})
SET r2.valor_min = p.ssd_min, r2.es_excluyente = false
MERGE (p)-[:EXIGE]->(r3:Requisito {criterio:'gama_cpu', perfil:p.codigo})
SET r3.valor_texto = p.gama_cpu_min, r3.es_excluyente = false
MERGE (p)-[:EXIGE]->(r4:Requisito {criterio:'virtualizacion', perfil:p.codigo})
SET r4.valor_booleano = p.requiere_virtualizacion,
    r4.es_excluyente = p.requiere_virtualizacion
MERGE (p)-[:EXIGE]->(r5:Requisito {criterio:'gama_gpu', perfil:p.codigo})
SET r5.valor_min = p.gama_gpu_min, r5.es_excluyente = false;


// ---------------------------------------------------------------------
// 4. VARIABLES DIFUSAS Y ETIQUETAS DIFUSAS
//    Nomenclatura unificada en PG2: (:VariableDifusa) y (:EtiquetaDifusa)
//    reemplazan a ConjuntoDifuso (SM1, SM3), VariableDifusa/
//    TerminoLinguistico (SM2) y VariableLinguistica/EtiquetaLinguistica (SM4).
//    'tipo': gaussiana | hombro_izq | hombro_der
// ---------------------------------------------------------------------
UNWIND [
  {n:'dedicacion_h',           min:0.0, max:40.0,  sm:'SM1', clase:'entrada'},
  {n:'exigencia_grafica',      min:0.0, max:100.0, sm:'SM1', clase:'entrada'},
  {n:'peso_perfil',            min:0.0, max:1.0,   sm:'SM1', clase:'salida'},
  {n:'intensidad_grafica',     min:0.0, max:1.0,   sm:'SM1', clase:'salida'},
  {n:'suficiencia_ram',        min:0.0, max:3.0,   sm:'SM2', clase:'entrada'},
  {n:'indice_ampliabilidad',   min:0.0, max:1.0,   sm:'SM2', clase:'entrada'},
  {n:'riesgo_obsolescencia',   min:0.0, max:100.0, sm:'SM2', clase:'salida'},
  {n:'peso_kg',                min:0.8, max:4.0,   sm:'SM3', clase:'entrada'},
  {n:'autonomia_h',            min:1.0, max:24.0,  sm:'SM3', clase:'entrada'},
  {n:'potencia_relativa',      min:0.0, max:1.0,   sm:'SM3', clase:'entrada'},
  {n:'adecuacion_movilidad',   min:0.0, max:1.0,   sm:'SM3', clase:'salida'},
  {n:'grado_gpu',              min:0.0, max:1.0,   sm:'SM3', clase:'salida'},
  {n:'adecuacion_global',      min:0.0, max:1.0,   sm:'SM4', clase:'entrada'},
  {n:'excedente_presupuesto',  min:0.0, max:30.0,  sm:'SM4', clase:'entrada'},
  {n:'grado_recomendacion',    min:0.0, max:1.0,   sm:'SM4', clase:'salida'}
] AS v
MERGE (x:VariableDifusa {nombre:v.n})
SET x.universo_min = v.min, x.universo_max = v.max,
    x.submodulo = v.sm, x.clase = v.clase,
    x.funcion = 'gaussiana', x.inferencia = 'Mamdani',
    x.desborrosificacion = 'centroide';

UNWIND [
  // ---- SM1 (Olea): interpretacion del requerimiento ----
  {v:'dedicacion_h',         e:'rara_vez',      c: 0.00, s: 1.50, t:'hombro_izq'},
  {v:'dedicacion_h',         e:'ocasional',     c: 4.00, s: 2.00, t:'gaussiana'},
  {v:'dedicacion_h',         e:'frecuente',     c:12.00, s: 4.50, t:'gaussiana'},
  {v:'dedicacion_h',         e:'principal',     c:28.00, s: 8.00, t:'hombro_der'},
  {v:'exigencia_grafica',    e:'baja',          c:10.00, s:12.00, t:'hombro_izq'},
  {v:'exigencia_grafica',    e:'media',         c:45.00, s:12.00, t:'gaussiana'},
  {v:'exigencia_grafica',    e:'alta',          c:80.00, s:14.00, t:'hombro_der'},
  {v:'peso_perfil',          e:'marginal',      c: 0.20, s: 0.12, t:'gaussiana'},
  {v:'peso_perfil',          e:'relevante',     c: 0.60, s: 0.12, t:'gaussiana'},
  {v:'peso_perfil',          e:'determinante',  c: 0.95, s: 0.10, t:'gaussiana'},
  {v:'intensidad_grafica',   e:'baja',          c: 0.15, s: 0.12, t:'gaussiana'},
  {v:'intensidad_grafica',   e:'media',         c: 0.50, s: 0.12, t:'gaussiana'},
  {v:'intensidad_grafica',   e:'alta',          c: 0.85, s: 0.12, t:'gaussiana'},
  // ---- SM2 (Miranda): rendimiento y capacidad ----
  {v:'suficiencia_ram',      e:'insuficiente',  c: 0.50, s: 0.20, t:'hombro_izq'},
  {v:'suficiencia_ram',      e:'justa',         c: 1.00, s: 0.20, t:'gaussiana'},
  {v:'suficiencia_ram',      e:'suficiente',    c: 1.50, s: 0.20, t:'gaussiana'},
  {v:'suficiencia_ram',      e:'holgada',       c: 2.00, s: 0.25, t:'hombro_der'},
  {v:'indice_ampliabilidad', e:'poca',          c: 0.00, s: 0.20, t:'hombro_izq'},
  {v:'indice_ampliabilidad', e:'media',         c: 0.50, s: 0.18, t:'gaussiana'},
  {v:'indice_ampliabilidad', e:'mucha',         c: 1.00, s: 0.20, t:'hombro_der'},
  {v:'riesgo_obsolescencia', e:'bajo',          c: 0.00, s:18.00, t:'hombro_izq'},
  {v:'riesgo_obsolescencia', e:'medio',         c:50.00, s:15.00, t:'gaussiana'},
  {v:'riesgo_obsolescencia', e:'alto',          c:100.0, s:18.00, t:'hombro_der'},
  // ---- SM3 (de Coninck): grafica y movilidad ----
  {v:'peso_kg',              e:'liviana',       c: 1.20, s: 0.20, t:'hombro_izq'},
  {v:'peso_kg',              e:'intermedia',    c: 1.80, s: 0.25, t:'gaussiana'},
  {v:'peso_kg',              e:'pesada',        c: 2.50, s: 0.30, t:'hombro_der'},
  {v:'autonomia_h',          e:'baja',          c: 3.00, s: 1.00, t:'hombro_izq'},
  {v:'autonomia_h',          e:'media',         c: 6.50, s: 1.20, t:'gaussiana'},
  {v:'autonomia_h',          e:'alta',          c:10.00, s: 1.50, t:'hombro_der'},
  {v:'potencia_relativa',    e:'restringida',   c: 0.35, s: 0.10, t:'hombro_izq'},
  {v:'potencia_relativa',    e:'moderada',      c: 0.60, s: 0.10, t:'gaussiana'},
  {v:'potencia_relativa',    e:'plena',         c: 0.80, s: 0.10, t:'hombro_der'},
  {v:'adecuacion_movilidad', e:'baja',          c: 0.05, s: 0.12, t:'gaussiana'},
  {v:'adecuacion_movilidad', e:'media',         c: 0.50, s: 0.12, t:'gaussiana'},
  {v:'adecuacion_movilidad', e:'alta',          c: 0.95, s: 0.12, t:'gaussiana'},
  {v:'grado_gpu',            e:'insuficiente',  c: 0.20, s: 0.12, t:'gaussiana'},
  {v:'grado_gpu',            e:'parcial',       c: 0.55, s: 0.12, t:'gaussiana'},
  {v:'grado_gpu',            e:'pleno',         c: 0.95, s: 0.10, t:'gaussiana'},
  // ---- SM4 (Luconi Furque): integracion y recomendacion ----
  {v:'adecuacion_global',    e:'baja',          c: 0.40, s: 0.14, t:'hombro_izq'},
  {v:'adecuacion_global',    e:'media',         c: 0.70, s: 0.07, t:'gaussiana'},
  {v:'adecuacion_global',    e:'alta',          c: 0.90, s: 0.07, t:'hombro_der'},
  {v:'excedente_presupuesto',e:'dentro',        c: 0.00, s: 3.00, t:'gaussiana'},
  {v:'excedente_presupuesto',e:'levemente',     c:10.00, s: 4.00, t:'gaussiana'},
  {v:'excedente_presupuesto',e:'muy',           c:25.00, s: 6.00, t:'hombro_der'},
  {v:'grado_recomendacion',  e:'descartar',     c: 0.00, s: 0.15, t:'gaussiana'},
  {v:'grado_recomendacion',  e:'considerar',    c: 0.50, s: 0.15, t:'gaussiana'},
  {v:'grado_recomendacion',  e:'recomendar',    c: 1.00, s: 0.15, t:'gaussiana'}
] AS e
MATCH (v:VariableDifusa {nombre:e.v})
MERGE (v)-[:TIENE_ETIQUETA]->(x:EtiquetaDifusa {variable:e.v, nombre:e.e})
SET x.centro = e.c, x.sigma = e.s, x.tipo = e.t,
    x.fuente = 'Decision de diseno del grupo sobre casos publicados y fichas tecnicas',
    x.estado_validacion = 'sin validar';


// ---------------------------------------------------------------------
// 5. REGLAS Y CATALOGO DE PARAMETROS
// ---------------------------------------------------------------------
// 5.a Reglas difusas (una fila por regla; el antecedente queda como texto
//     para la traza y se ejecuta en los bloques 10.x)
UNWIND [
  {id:'INT-RD1', sm:'SM1', ant:'MAX(D.rara_vez, D.ocasional)',                              con:'peso_perfil = marginal'},
  {id:'INT-RD2', sm:'SM1', ant:'D.frecuente',                                               con:'peso_perfil = relevante'},
  {id:'INT-RD3', sm:'SM1', ant:'D.principal',                                               con:'peso_perfil = determinante'},
  {id:'INT-RD4', sm:'SM1', ant:'MIN(E.alta, MAX(D.frecuente, D.principal))',                con:'intensidad_grafica = alta'},
  {id:'INT-RD5', sm:'SM1', ant:'MIN(E.alta, MAX(D.rara_vez, D.ocasional))',                 con:'intensidad_grafica = media'},
  {id:'INT-RD6', sm:'SM1', ant:'MIN(E.media, MAX(D.frecuente, D.principal))',               con:'intensidad_grafica = media'},
  {id:'INT-RD7', sm:'SM1', ant:'MAX(E.baja, MIN(E.media, MAX(D.rara_vez, D.ocasional)))',   con:'intensidad_grafica = baja'},
  {id:'FZ-R1',   sm:'SM2', ant:'MIN(S.insuficiente, A.poca)',                               con:'riesgo_obsolescencia = alto'},
  {id:'FZ-R2',   sm:'SM2', ant:'MIN(S.insuficiente, MAX(A.media, A.mucha))',                con:'riesgo_obsolescencia = medio'},
  {id:'FZ-R3',   sm:'SM2', ant:'MIN(S.justa, A.poca)',                                      con:'riesgo_obsolescencia = medio'},
  {id:'FZ-R4',   sm:'SM2', ant:'MIN(S.justa, MAX(A.media, A.mucha))',                       con:'riesgo_obsolescencia = bajo'},
  {id:'FZ-R5',   sm:'SM2', ant:'MAX(S.suficiente, S.holgada)',                              con:'riesgo_obsolescencia = bajo'},
  {id:'GM-RD1',  sm:'SM3', ant:'MIN(P.liviana, A.alta)',                                    con:'adecuacion_movilidad = alta'},
  {id:'GM-RD2',  sm:'SM3', ant:'MAX(MIN(P.liviana, A.media), MIN(P.intermedia, MAX(A.media, A.alta)))', con:'adecuacion_movilidad = media'},
  {id:'GM-RD3',  sm:'SM3', ant:'MAX(P.pesada, A.baja)',                                     con:'adecuacion_movilidad = baja'},
  {id:'GM-RD4',  sm:'SM3', ant:'MAX(MIN(mS, MAX(Q.moderada, Q.plena)), MIN(mJ, Q.plena))',  con:'grado_gpu = pleno'},
  {id:'GM-RD5',  sm:'SM3', ant:'MAX(MIN(mS, Q.restringida), MIN(mJ, Q.moderada), MIN(mI, Q.plena))', con:'grado_gpu = parcial'},
  {id:'GM-RD6',  sm:'SM3', ant:'MAX(MIN(mJ, Q.restringida), MIN(mI, MAX(Q.restringida, Q.moderada)))', con:'grado_gpu = insuficiente'},
  {id:'REC-RD1', sm:'SM4', ant:'MIN(G.alta, X.dentro)',                                     con:'grado_recomendacion = recomendar'},
  {id:'REC-RD2', sm:'SM4', ant:'MIN(G.media, X.dentro)',                                    con:'grado_recomendacion = considerar'},
  {id:'REC-RD3', sm:'SM4', ant:'MIN(G.alta, X.levemente)',                                  con:'grado_recomendacion = considerar'},
  {id:'REC-RD4', sm:'SM4', ant:'MIN(G.media, X.levemente)',                                 con:'grado_recomendacion = descartar'},
  {id:'REC-RD5', sm:'SM4', ant:'MAX(G.baja, X.muy)',                                        con:'grado_recomendacion = descartar'}
] AS r
MERGE (x:Regla:ReglaDifusa {id:r.id})
SET x.submodulo = r.sm, x.tipo = 'Difusa (Mamdani)', x.operadores = 'AND = MIN / OR = MAX',
    x.antecedente = r.ant, x.consecuente = r.con, x.implicacion = 'recorte',
    x.etiqueta_consecuente = split(r.con, ' = ')[1],
    x.agregacion = 'MAX', x.desborrosificacion = 'centroide',
    x.estado_validacion = 'sin validar';

// 5.b Reglas crisp que se conservan de PG1 (filtros, politicas y alertas)
UNWIND [
  {id:'REN-R1',  sm:'SM2', t:'Deterministica', reg:'SI el perfil exige virtualizacion Y la CPU no la soporta ENTONCES grado 0 y excluyente incumplido'},
  {id:'REN-R7',  sm:'SM2', t:'Heuristica',     reg:'SI la RAM es ampliable Y no llega al minimo del perfil ENTONCES "condicionado a ampliacion" con el costo del modulo (P_COSTO_MODULO_RAM_USD); no se descarta por la RAM'},
  {id:'REN-R10', sm:'SM2', t:'Deterministica', reg:'SI la ficha no informa la ampliabilidad ENTONCES conservar "desconocida", no descartar y alertar'},
  {id:'REN-R16', sm:'SM2', t:'Heuristica',     reg:'SI RAM ampliable Y slot M.2 libre ENTONCES nivel_ampliabilidad alta; una de dos media; ninguna baja'},
  {id:'FZ-R6',   sm:'SM2', t:'Control (crisp)',reg:'SI la ampliabilidad es desconocida ENTONCES evaluar FZ-R1..R5 con a = 0 y a = 1 e informar rango'},
  {id:'FZ-R7',   sm:'SM2', t:'Control (crisp)',reg:'SI la etiqueta dominante del riesgo (o la del peor caso) es alto ENTONCES alerta riesgo de obsolescencia'},
  {id:'GM-R3',   sm:'SM3', t:'Deterministica', reg:'SI la intensidad grafica es baja ENTONCES alcanza una GPU integrada moderna; una integrada que cumple la gama del perfil tiene grado_gpu 1'},
  {id:'GM-R4',   sm:'SM3', t:'Heuristica',     reg:'SI la GPU integrada queda un nivel por debajo de la gama del perfil ENTONCES grado_gpu = P_GRADO_GPU_UN_NIVEL_ABAJO; SI queda dos o mas niveles abajo (integrada o dedicada) ENTONCES grado_gpu = 0. La dedicada a un nivel abajo la gradua GM-RD5 y GM-RD6'},
  {id:'GM-R12',  sm:'SM3', t:'Heuristica',     reg:'SI hay medicion independiente ENTONCES autonomia "medida"; SI solo hay valor declarado ENTONCES "estimada" (P_FACTOR_AUTONOMIA x declarada); SI no hay ninguno ENTONCES "desconocida"'},
  {id:'GM-R8',   sm:'SM3', t:'Heuristica',     reg:'SI grado_gpu cae mas de P_DIF_ALERTA_TGP respecto del grado por sola gama ENTONCES alerta de potencia grafica reducida'},
  {id:'GM-R11',  sm:'SM3', t:'Contextual',     reg:'SI la prioridad es autonomia Y mu_baja(autonomia) >= P_ALFA_ALERTA_AUTONOMIA ENTONCES alerta de autonomia insuficiente'},
  {id:'GM-R17',  sm:'SM3', t:'Control (crisp)',reg:'SI la GPU es dedicada Y su TGP es desconocido ENTONCES informar intervalo de grado y alertar'},
  {id:'INT-R5',  sm:'SM1', t:'Contextual',     reg:'SI el grado del perfil >= umbral_exigencia ENTONCES impone requisitos; si no, es preferencia'},
  {id:'INT-R11', sm:'SM1', t:'Contextual',     reg:'Las actividades declaradas prevalecen sobre la carrera para asignar el perfil'},
  {id:'INT-R12', sm:'SM1', t:'Heuristica',     reg:'SI dos perfiles empatan en grado ENTONCES el dominante es el mas exigente'},
  {id:'INT-R13', sm:'SM1', t:'Deterministica', reg:'SI no se pudo determinar ningun perfil Y la aclaracion no tuvo respuesta ENTONCES perfil_dominante = indeterminado, alertar y no evaluar el catalogo (no se asume OFI)'},
  {id:'INT-R14', sm:'SM1', t:'Control (crisp)',reg:'SI la dedicacion es desconocida Y la aclaracion no tuvo respuesta ENTONCES evaluar los dos escenarios del perfil (preferencia / impone requisitos) y producir una recomendacion condicionada; no se imputa una dedicacion'},
  {id:'REC-R3',  sm:'SM4', t:'Deterministica', reg:'SI MIN de excluyentes = 0 ENTONCES descartar; SI algun excluyente tiene falta de informacion ENTONCES Indeterminada y no comparar'},
  {id:'REC-R4',  sm:'SM4', t:'Contextual',     reg:'La adecuacion global pondera rendimiento, grafica y movilidad con los pesos del perfil dominante'},
  {id:'REC-R5',  sm:'SM4', t:'Contextual',     reg:'SI el comprador declara una prioridad ENTONCES se suma P_INCREMENTO_PRIORIDAD a ese peso y se renormaliza'},
  {id:'REC-R7',  sm:'SM4', t:'Heuristica',     reg:'SI una spec alcanza el valor "sobra" del perfil ENTONCES alerta de sobredimensionamiento, sin descartar'},
  {id:'REC-R8',  sm:'SM4', t:'Heuristica',     reg:'SI la diferencia de grado_recomendacion < P_MARGEN_EMPATE ENTONCES desempatar por nivel_ampliabilidad'},
  {id:'REC-R9',  sm:'SM4', t:'Contextual',     reg:'Indice costo-beneficio = adecuacion global / (precio / 1000); SI la prioridad es precio ENTONCES ordena por este indice'},
  {id:'REC-R10', sm:'SM4', t:'Deterministica', reg:'SI ninguna notebook queda recomendada ENTONCES "Sin alternativa adecuada" con la restriccion no cubierta'},
  {id:'REC-R11', sm:'SM4', t:'Deterministica', reg:'La explicacion va en tres bloques (cumple, no cumple, falta verificar) y no menciona nada ausente de la traza'},
  {id:'REC-R13', sm:'SM4', t:'Heuristica',     reg:'SI un requisito queda parcialmente cumplido (RAM por debajo del minimo) ENTONCES alerta de infradimensionamiento, sin descartar'},
  {id:'REC-R15', sm:'SM4', t:'Deterministica', reg:'SI falta un dato que solo ordena ENTONCES calcular la adecuacion global minima y maxima (grado faltante = 0 y = 1), inferir el grado en los dos escenarios y: peor caso no descartar -> Recomendada condicionada; mejor caso descartar -> Descartada; si no -> Indeterminada'}
] AS r
MERGE (x:Regla:ReglaCrisp {id:r.id})
SET x.submodulo = r.sm, x.tipo = r.t, x.enunciado = r.reg,
    x.estado_validacion = 'sin validar';

// 5.c Reglas retiradas en PG2 (se conserva el nodo para trazabilidad)
UNWIND ['REN-R6','REN-R9','REC-R1','REC-R2','REC-R6','REC-R12','GM-R10'] AS id
MERGE (x:Regla {id:id})
SET x.estado_validacion = 'reemplazada en PG2',
    x.reemplazada_por = CASE id
      WHEN 'REN-R6'  THEN 'FZ-R3 y FZ-R7 (RAM soldada y justa -> riesgo; alerta si es alto)'
      WHEN 'REN-R9'  THEN 'FZ-R4 (SM2 proponia esperar a la validacion; se retira para no contar dos veces la ampliabilidad)'
      WHEN 'GM-R10'  THEN 'GM-RD1..GM-RD3 (se conserva solo como fuzificacion y para GM-R11)'
      ELSE 'REC-RD1..REC-RD5' END;

// 5.d Catalogo de parametros (los que siguen siendo crisp)
UNWIND [
  {n:'umbral_exigencia',           v:0.40, sm:'SM1', o:'Decision del grupo; cruce marginal/relevante de peso_perfil'},
  {n:'banda_frontera',             v:0.05, sm:'SM1', o:'Decision del grupo'},
  {n:'entropia_max',               v:0.60, sm:'SM1', o:'Decision del grupo'},
  {n:'P_COSTO_MODULO_RAM_USD',     v:30.0, sm:'SM2', o:'Precios de Mercado Libre, 09/2026'},
  {n:'P_PESO_RANURAS_AMPLIABILIDAD', v:0.50, sm:'SM2', o:'Formula del indice a de la PI3 de SM2 (peso de las ranuras; el resto es el margen hasta el maximo)'},
  {n:'P_RANURAS_REFERENCIA',       v:2.00, sm:'SM2', o:'Formula del indice a de la PI3 de SM2 (ranuras libres que cuentan como ampliabilidad plena)'},
  {n:'P_DIF_ALERTA_TGP',           v:0.20, sm:'SM3', o:'Decision del grupo'},
  {n:'P_GRADO_GPU_UN_NIVEL_ABAJO', v:0.50, sm:'SM3', o:'GM-R4 de PG1 (GPU un nivel abajo -> 0,5; dos o mas -> 0)'},
  {n:'P_PESO_GPU_GRAFICA',         v:0.60, sm:'SM3', o:'Ponderacion de la adecuacion grafica de la PI2 de SM3'},
  {n:'P_PESO_PANTALLA_GRAFICA',    v:0.40, sm:'SM3', o:'Ponderacion de la adecuacion grafica de la PI2 de SM3'},
  {n:'P_ALFA_ALERTA_AUTONOMIA',    v:0.50, sm:'SM3', o:'Decision del grupo'},
  {n:'P_FACTOR_AUTONOMIA',         v:0.70, sm:'SM3', o:'Supuesto del grupo (GM-R12)'},
  {n:'P_INCREMENTO_PRIORIDAD',     v:0.20, sm:'SM4', o:'Decision del grupo (REC-R5)'},
  {n:'P_MARGEN_EMPATE',            v:0.05, sm:'SM4', o:'Decision del grupo (REC-R8)'},
  {n:'P_MAX_RECOMENDADAS',         v:3.00, sm:'SM4', o:'Consigna y decision del grupo'}
] AS p
MERGE (x:Parametro {nombre:p.n})
SET x.valor = p.v, x.submodulo = p.sm, x.origen = p.o,
    x.estado_validacion = 'sin validar';

// 5.e Trazabilidad: un parametro del catalogo por juego de centros y sigmas,
//     para que ningun numero quede escondido dentro de una regla
MATCH (v:VariableDifusa)
MERGE (p:Parametro {nombre:'centros_y_sigmas_' + v.nombre})
SET p.submodulo = v.submodulo,
    p.origen = 'Decision de diseno del grupo (PI3)',
    p.estado_validacion = 'sin validar',
    p.decision_que_modifica = 'Activacion de las reglas difusas de ' + v.nombre;
MATCH (v:VariableDifusa)-[:TIENE_ETIQUETA]->(e:EtiquetaDifusa)
MATCH (p:Parametro {nombre:'centros_y_sigmas_' + v.nombre})
MERGE (e)-[:SE_PARAMETRIZA_CON]->(p);

// 5.f Agenda de validacion con el tecnico (devolucion de PG2, correccion 2).
//     Una (:ConsultaExperto) por variable difusa, ligada al parametro que
//     guarda sus centros y sigmas, y una aparte para FZ-R2 y FZ-R3, que hoy
//     dan casi el mismo riesgo (50,0 y 49,6) para situaciones opuestas.
//     Las preguntas estan en terminos del dominio, para hacerlas tal cual.
UNWIND [
  {v:'dedicacion_h',          q:'Desde cuantas horas por semana una actividad deja de ser ocasional y pasa a frecuente? Y desde cuantas es la actividad principal?'},
  {v:'exigencia_grafica',     q:'Que juegos pondria como ejemplo de exigencia baja, media y alta? Coinciden con Stardew Valley, Fortnite y Cyberpunk 2077?'},
  {v:'peso_perfil',           q:'Una actividad de 12 h por semana pesa lo mismo que una de 28 h a la hora de decidir el perfil, o la de 28 h manda?'},
  {v:'intensidad_grafica',    q:'Un juego exigente que se juega de vez en cuando, pide GPU media o alcanza con una integrada moderna?'},
  {v:'suficiencia_ram',       q:'Con la RAM justo en el minimo del perfil, la considera justa o suficiente? A partir de cuanta RAM sobra?'},
  {v:'indice_ampliabilidad',  q:'Una ranura libre con margen hasta 32 GB, es ampliabilidad media o mucha? Y un equipo con dos ranuras libres?'},
  {v:'riesgo_obsolescencia',  q:'Que riesgo de quedarse corta le asigna a una notebook con 16 GB soldados para virtualizar, y a una con 8 GB ampliables?'},
  {v:'peso_kg',               q:'Desde que peso una notebook deja de ser comoda para llevarla todos los dias?'},
  {v:'autonomia_h',           q:'Cuantas horas reales de bateria considera poca, aceptable y mucha? Hoy entre 4 y 5 h ninguna etiqueta pasa de 0,6.'},
  {v:'potencia_relativa',     q:'Una RTX 4060 configurada a 60 W de 115 W, rinde como gama media, como gama de entrada o en el medio?'},
  {v:'adecuacion_movilidad',  q:'Una notebook liviana con 5 h de bateria, la ubicaria en movilidad media o baja?'},
  {v:'grado_gpu',             q:'Una GPU un nivel por debajo de la que pide el perfil, sirve a medias o directamente no sirve?'},
  {v:'adecuacion_global',     q:'Con que puntaje global recomendaria una notebook sin dudar, y con cual la dejaria como opcion para considerar? Hoy los cruces estan en 0,6 y 0,8.'},
  {v:'excedente_presupuesto', q:'Cuanto por encima del presupuesto acepta ofrecer un equipo? Hoy "levemente excedido" se centra en el 10 % y mas del 30 % se descarta.'},
  {v:'grado_recomendacion',   q:'Prefiere ver como "para considerar" una notebook que cumple todo pero se pasa un poco del presupuesto, o que no aparezca?'}
] AS x
MATCH (p:Parametro {nombre:'centros_y_sigmas_' + x.v})
MERGE (ce:ConsultaExperto {id:'CE-' + x.v})
SET ce.pregunta = x.q, ce.estado = 'pendiente', ce.submodulo = p.submodulo,
    ce.que_se_valida = 'Centros y sigmas de las etiquetas de ' + x.v
MERGE (ce)-[:VALIDA]->(p);

MERGE (ce:ConsultaExperto {id:'CE-FZ-R2-R3'})
SET ce.submodulo = 'SM2', ce.estado = 'pendiente',
    ce.que_se_valida = 'Consecuentes de FZ-R2 y FZ-R3',
    ce.pregunta = 'Una notebook con la RAM justa y soldada (no se puede ampliar) y otra con la RAM por debajo del minimo pero ampliable con un modulo de unos 30 USD: corren el mismo riesgo de quedarse cortas? Si no, cual corre mas riesgo?',
    ce.situacion_actual = 'FZ-R2 (insuficiente y ampliable) y FZ-R3 (justa y soldada) concluyen las dos riesgo medio: Notebook_K da 49,55 y Notebook_B 50,00',
    ce.alternativa_a_evaluar = 'FZ-R3 -> alto, como la alerta de REN-R6 de PG1 para RAM soldada por debajo de la recomendada: Notebook_B pasaria a 80,84 (alto) y FZ-R7 emitiria su alerta; el orden de la recomendacion no cambia porque el riesgo no entra en la adecuacion global'
WITH ce
MATCH (q:Regla) WHERE q.id IN ['FZ-R2','FZ-R3']
MERGE (ce)-[:VALIDA]->(q);


// ---------------------------------------------------------------------
// 6. LEXICO DE EXPRESIONES DE FRECUENCIA Y GAMAS DE GPU
// ---------------------------------------------------------------------
UNWIND [
  {t:'casi nunca', h:0.5}, {t:'muy de vez en cuando', h:0.5},
  {t:'a veces', h:4.0}, {t:'de vez en cuando', h:4.0}, {t:'cada tanto', h:4.0},
  {t:'los fines de semana', h:6.0},
  {t:'bastante', h:12.0}, {t:'seguido', h:12.0}, {t:'varias veces por semana', h:12.0},
  {t:'todos los dias', h:14.0}, {t:'a diario', h:14.0},
  {t:'principalmente', h:28.0}, {t:'la necesito para', h:28.0}, {t:'es para trabajar', h:28.0}
] AS x
MERGE (e:ExpresionFrecuencia {texto:x.t})
SET e.horas_ref = x.h, e.origen = 'Casos publicados de asesoramiento',
    e.estado_validacion = 'sin validar';

UNWIND [
  {g:'integrada basica',  i:1, idx: 5.0},
  {g:'integrada moderna', i:2, idx:30.0},
  {g:'dedicada entrada',  i:3, idx:45.0},
  {g:'dedicada media',    i:4, idx:70.0},
  {g:'dedicada alta',     i:5, idx:90.0}
] AS g
MERGE (x:GamaGPU {nombre:g.g})
SET x.indice = g.i, x.indice_exigencia = g.idx,
    x.estado_validacion = 'sin validar';

UNWIND [
  {j:'Stardew Valley', g:'integrada basica',  f:'Steam: 256 MB de VRAM, Shader Model 3.0'},
  {j:'Fortnite',       g:'integrada moderna', f:'Epic Games: recomendado GTX 960 / R9 280 con 2 GB'},
  {j:'Cyberpunk 2077', g:'dedicada media',    f:'CD PROJEKT RED: recomendado RTX 2060 Super / RX 5700 XT'}
] AS j
MERGE (x:Juego {nombre:j.j})
SET x.fuente = j.f
WITH x, j
MATCH (g:GamaGPU {nombre:j.g})
MERGE (x)-[:RECOMIENDA_GAMA {fuente:j.f}]->(g);
