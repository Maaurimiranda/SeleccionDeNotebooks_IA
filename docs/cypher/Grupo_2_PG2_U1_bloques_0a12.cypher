// =====================================================================
// Grupo 2 - Comision 5K09 - Ciclo 2026
// Asistente Experto para la Seleccion Personalizada de Notebooks
// PG2 - Unidad 1: implementacion de la base de conocimiento en Neo4j
//
// Estructura del script (catorce bloques, del 0 al 13, ejecutables en orden):
//   0. Limpieza inicial
//   1. Restricciones e indices
//   2. Frames (clases del dominio)
//   3. Perfiles de uso y tabla de requisitos por perfil
//   4. Variables difusas y etiquetas difusas (los cuatro submodulos)
//   5. Reglas (crisp y difusas) y catalogo de parametros
//   6. Lexico de expresiones de frecuencia y gamas de GPU
//   7. Instancias: compradores, requerimientos, actividades
//   8. Instancias: catalogo de notebooks y componentes
//   9. Fuzificacion de las entradas que no dependen del perfil (SM1, SM3)
//  10. Evaluaciones por requerimiento x notebook e inferencia difusa
//      (SM1, SM2, SM3, SM4)
//  11. Consultas de inferencia de la demostracion (C1, C2, C3)
//  12. Consultas de verificacion de los casos de prueba (CP1 a CP11)
//      y agenda de validacion con el tecnico (V1)
//  13. Consultas de salida para el LLM (PI4)
//
// Convenciones: los centros, sigmas, ponderaciones y umbrales de decision
// viven en nodos (:EtiquetaDifusa) o (:Parametro). En las consultas quedan
// escritos solo la discretizacion del universo (101 puntos), el umbral de
// 0,01 a partir del cual una activacion se registra en la traza y los topes
// de universo de las entradas (40 h, 3,0, 30 %), que repiten universo_max
// de cada (:VariableDifusa). AND = MIN, OR = MAX, implicacion por recorte,
// agregacion MAX y desborrosificacion por centroide sobre 101 puntos.
// Cada regla que se activa queda en el grafo como [:ACTIVA {fuerza}] desde
// el nodo evaluado, para poder recorrer la traza de una conclusion.
//
// Version corregida (devolucion de PG2):
//   - Todo resultado que depende del perfil o del pedido (suficiencia de
//     RAM, indice de ampliabilidad, riesgo de obsolescencia, grado de GPU,
//     adecuacion grafica, adecuacion de rendimiento, grado de pantalla y
//     las alertas que comparan contra el perfil) se guarda en la
//     (:Evaluacion) de cada requerimiento x notebook. En (:Notebook) y sus
//     componentes quedan solo las propiedades tecnicas y lo que no depende
//     de quien pregunta (la movilidad, que sale del peso y la autonomia).
//   - El consecuente de FZ-R1 a FZ-R5 se lee del nodo (:Regla), para que la
//     calibracion con el tecnico sea un cambio de dato y no de consulta.
//   - Agenda de validacion con el tecnico en nodos (:ConsultaExperto).
//   - CP11: dos compradores con requerimientos distintos evaluan la misma
//     notebook (Notebook_K) y cada evaluacion conserva su propia evidencia.
// =====================================================================


// ---------------------------------------------------------------------
// 0. LIMPIEZA INICIAL
// ---------------------------------------------------------------------
MATCH (n) DETACH DELETE n;


// ---------------------------------------------------------------------
// 1. RESTRICCIONES E INDICES
// ---------------------------------------------------------------------
CREATE CONSTRAINT frame_nombre IF NOT EXISTS
  FOR (f:Frame) REQUIRE f.nombre IS UNIQUE;
CREATE CONSTRAINT perfil_codigo IF NOT EXISTS
  FOR (p:Perfil) REQUIRE p.codigo IS UNIQUE;
CREATE CONSTRAINT notebook_modelo IF NOT EXISTS
  FOR (n:Notebook) REQUIRE n.modelo IS UNIQUE;
CREATE CONSTRAINT comprador_id IF NOT EXISTS
  FOR (c:Comprador) REQUIRE c.id IS UNIQUE;
CREATE CONSTRAINT requerimiento_id IF NOT EXISTS
  FOR (r:Requerimiento) REQUIRE r.id IS UNIQUE;
CREATE CONSTRAINT variable_nombre IF NOT EXISTS
  FOR (v:VariableDifusa) REQUIRE v.nombre IS UNIQUE;
CREATE CONSTRAINT regla_id IF NOT EXISTS
  FOR (r:Regla) REQUIRE r.id IS UNIQUE;
CREATE CONSTRAINT parametro_nombre IF NOT EXISTS
  FOR (p:Parametro) REQUIRE p.nombre IS UNIQUE;
CREATE INDEX etiqueta_var IF NOT EXISTS
  FOR (e:EtiquetaDifusa) ON (e.variable, e.nombre);


// ---------------------------------------------------------------------
// 2. FRAMES (clases del dominio, una por concepto de la red de PG1)
// ---------------------------------------------------------------------
UNWIND [
  {n:'Comprador',            sm:'SM1'},
  {n:'Requerimiento formal', sm:'SM1'},
  {n:'Actividad',            sm:'SM1'},
  {n:'Juego',                sm:'SM1'},
  {n:'Perfil de uso',        sm:'SM1'},
  {n:'Notebook',             sm:'grupal'},
  {n:'CPU',                  sm:'SM2'},
  {n:'RAM',                  sm:'SM2'},
  {n:'Almacenamiento',       sm:'SM2'},
  {n:'GPU',                  sm:'SM3'},
  {n:'Pantalla',             sm:'SM3'},
  {n:'Bateria',              sm:'SM3'},
  {n:'Requisito',            sm:'grupal'},
  {n:'Resultado de requisito', sm:'grupal'},
  {n:'Evaluacion de notebook', sm:'SM4'},
  {n:'Alerta',               sm:'grupal'},
  {n:'Recomendacion',        sm:'SM4'}
] AS f
MERGE (x:Frame {nombre:f.n})
SET x.submodulo_responsable = f.sm;

// Herencias de la red semantica integrada (relaciones posee de PG1)
MATCH (sub:Frame), (sup:Frame {nombre:'Notebook'})
WHERE sub.nombre IN ['CPU','RAM','Almacenamiento','GPU','Pantalla','Bateria']
MERGE (sup)-[:POSEE_SLOT]->(sub);


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
    x.estado_validacion = 'provisional';

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
    e.estado_validacion = 'provisional';

UNWIND [
  {g:'integrada basica',  i:1, idx: 5.0},
  {g:'integrada moderna', i:2, idx:30.0},
  {g:'dedicada entrada',  i:3, idx:45.0},
  {g:'dedicada media',    i:4, idx:70.0},
  {g:'dedicada alta',     i:5, idx:90.0}
] AS g
MERGE (x:GamaGPU {nombre:g.g})
SET x.indice = g.i, x.indice_exigencia = g.idx,
    x.estado_validacion = 'provisional';

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


// ---------------------------------------------------------------------
// 7. INSTANCIAS: COMPRADORES, REQUERIMIENTOS Y ACTIVIDADES
//    Comprador y Requerimiento formal son conceptos distintos (devolucion
//    de PG1): el comprador es la persona, con identidad propia; el
//    requerimiento es un pedido concreto que formula. Un mismo comprador
//    puede formular varios (por ejemplo, despues de una aclaracion o de
//    cambiar el presupuesto), y la evaluacion depende del pedido, no de
//    la persona.
//
//    req_01 - Caso 1 de PI2/PG1: "necesito una notebook para programar,
//    usar maquinas virtuales y Docker, y a veces jugar al Stardew Valley.
//    Tengo 1000 USD" (prioridad declarada: rendimiento).
//    req_02 - Caso B de SM1: "quiero una notebook para la facu, tengo
//    600 USD", sin carrera ni actividades y sin respuesta a la aclaracion.
//    req_03 - CP11 (devolucion de PG2): otro comprador pregunta por la
//    misma Notebook_K que ya evaluo req_01: "Estoy mirando la Notebook_K.
//    Me sirve para la facu? La uso todos los dias para Word, Excel y el
//    navegador y la llevo a todos lados. Tengo 1000 USD" (prioridad
//    declarada: portabilidad). Es una consulta puntual: se evalua solo la
//    notebook consultada y la respuesta es su evaluacion, no un ranking.
// ---------------------------------------------------------------------
MERGE (p1:Comprador {id:'comprador_01'})
SET p1.carrera = 'Ingenieria en Sistemas de Informacion', p1.carrera_origen = 'declarada';
MERGE (p2:Comprador {id:'comprador_02'})
SET p2.carrera_origen = 'desconocida';
MERGE (p3:Comprador {id:'comprador_03'})
SET p3.carrera = 'Contador Publico', p3.carrera_origen = 'declarada';

MERGE (c:Requerimiento {id:'req_01'})
SET c.presupuesto_usd = 1000.0, c.prioridad = 'rendimiento',
    c.usa_monitor_externo = false, c.moneda_original = 'USD',
    c.texto_pedido = 'Necesito una notebook para programar, usar maquinas virtuales y Docker, y a veces jugar al Stardew Valley. Tengo 1000 USD.';
MERGE (c2:Requerimiento {id:'req_02'})
SET c2.presupuesto_usd = 600.0, c2.prioridad = 'ninguna',
    c2.usa_monitor_externo = false, c2.moneda_original = 'USD',
    c2.aclaracion = 'sin respuesta',
    c2.texto_pedido = 'Quiero una notebook para la facu, tengo 600 USD.';
MERGE (c3:Requerimiento {id:'req_03'})
SET c3.presupuesto_usd = 1000.0, c3.prioridad = 'portabilidad',
    c3.usa_monitor_externo = false, c3.moneda_original = 'USD',
    c3.notebook_consultada = 'Notebook_K',
    c3.texto_pedido = 'Estoy mirando la Notebook_K. Me sirve para la facu? La uso todos los dias para Word, Excel y el navegador y la llevo a todos lados. Tengo 1000 USD.';

MATCH (p:Comprador {id:'comprador_01'}), (c:Requerimiento {id:'req_01'})
MERGE (p)-[:FORMULA {fecha:date('2026-10-15')}]->(c);
MATCH (p:Comprador {id:'comprador_02'}), (c:Requerimiento {id:'req_02'})
MERGE (p)-[:FORMULA {fecha:date('2026-10-15')}]->(c);
MATCH (p:Comprador {id:'comprador_03'}), (c:Requerimiento {id:'req_03'})
MERGE (p)-[:FORMULA {fecha:date('2026-11-05')}]->(c);

MERGE (a1:Actividad {id:'act_virtualizar'})
SET a1.descripcion = 'Usar maquinas virtuales y Docker', a1.perfil_asociado = 'VIRT',
    a1.expresion = 'la necesito para', a1.dedicacion_origen = 'lexico';
MERGE (a2:Actividad {id:'act_programar'})
SET a2.descripcion = 'Programar', a2.perfil_asociado = 'VIRT',  // como en la PI3 de SM1
    a2.expresion = 'la necesito para', a2.dedicacion_origen = 'lexico';
MERGE (a3:Actividad {id:'act_jugar'})
SET a3.descripcion = 'Jugar al Stardew Valley', a3.perfil_asociado = 'GAM',
    a3.expresion = 'a veces', a3.dedicacion_origen = 'lexico';

MERGE (a4:Actividad {id:'act_ofimatica'})
SET a4.descripcion = 'Word, Excel y el navegador para la facu', a4.perfil_asociado = 'OFI',
    a4.expresion = 'todos los dias', a4.dedicacion_origen = 'lexico';

MATCH (c:Requerimiento {id:'req_01'}), (a:Actividad)
WHERE a.id IN ['act_virtualizar','act_programar','act_jugar']
MERGE (c)-[:INCLUYE]->(a);
MATCH (c:Requerimiento {id:'req_03'}), (a:Actividad {id:'act_ofimatica'})
MERGE (c)-[:INCLUYE]->(a);

MATCH (a:Actividad {id:'act_jugar'}), (j:Juego {nombre:'Stardew Valley'})
MERGE (a)-[:USA]->(j);

MATCH (a:Actividad), (p:Perfil)
WHERE a.perfil_asociado = p.codigo
MERGE (a)-[:APUNTA_A]->(p);

MATCH (a:Actividad), (e:ExpresionFrecuencia)
WHERE a.expresion = e.texto
MERGE (a)-[:EXPRESADA_COMO]->(e);

// Valor crisp de la dedicacion: horas explicitas o expresion del lexico
MATCH (a:Actividad)
OPTIONAL MATCH (e:ExpresionFrecuencia {texto:a.expresion})
SET a.dedicacion_h = coalesce(a.horas_explicitas_semana, e.horas_ref),
    a.dedicacion_origen = CASE
      WHEN a.horas_explicitas_semana IS NOT NULL THEN 'declarada'
      WHEN e IS NOT NULL THEN 'lexico'
      ELSE 'desconocida' END;

// Exigencia grafica del titulo (IF-NEEDED de SM1)
MATCH (j:Juego)-[:RECOMIENDA_GAMA]->(g:GamaGPU)
WHERE j.exigencia IS NULL
SET j.exigencia = g.indice_exigencia;


// ---------------------------------------------------------------------
// 8. INSTANCIAS: CATALOGO DE NOTEBOOKS Y COMPONENTES
//    Precios al 01/10/2026 (relevamiento en Mercado Libre Argentina y
//    tiendas oficiales). Nueve modelos del catalogo de prueba, elegidos
//    para cubrir los casos positivo, negativo, difuso, indeterminado y
//    condicionado por un dato que solo ordena.
//    Las propiedades de (:Notebook) y de sus componentes son solo datos
//    tecnicos de la ficha. 'adecuacion_rendimiento' y 'grado_pantalla'
//    (las salidas crisp que SM2 y SM3 ya producian en PI2 y que PG2 no
//    vuelve a calcular) dependen del perfil, asi que se cargan por par
//    notebook-perfil en [:SALIDA_PI2] y pasan a la (:Evaluacion).
// ---------------------------------------------------------------------
UNWIND [
  {m:'Notebook_A', pr: 950.0, peso:1.4, cpu_gama:'alta',    cpu_nuc: 8, virt:'soportada',
   ram:16, ram_tipo:'mixta',     ranuras:1, max_gb:64, canal:'doble',
   ssd:1024, m2:true,  gpu:'integrada moderna', vram:0, tgp:null, tgp_max:null,
   res:'FHD', hz:60,  srgb:65, aut_med:8.0,  aut_dec:null},
  {m:'Notebook_B', pr: 700.0, peso:1.3, cpu_gama:'media',   cpu_nuc: 8, virt:'soportada',
   ram:16, ram_tipo:'soldada',   ranuras:0, max_gb:16, canal:'doble',
   ssd: 512, m2:false, gpu:'integrada moderna', vram:0, tgp:null, tgp_max:null,
   res:'FHD', hz:60,  srgb:62, aut_med:10.0, aut_dec:null},
  {m:'Notebook_H', pr:1000.0, peso:2.0, cpu_gama:'alta',    cpu_nuc:10, virt:'soportada',
   ram:16, ram_tipo:'mixta',     ranuras:1, max_gb:32, canal:'doble',
   ssd:1024, m2:true,  gpu:'integrada moderna', vram:0, tgp:null, tgp_max:null,
   res:'FHD', hz:60,  srgb:58, aut_med:6.0,  aut_dec:null},
  {m:'Notebook_K', pr: 900.0, peso:1.6, cpu_gama:'media',   cpu_nuc: 8, virt:'soportada',
   ram: 8, ram_tipo:'mixta',     ranuras:1, max_gb:32, canal:'simple',
   ssd: 512, m2:true,  gpu:'integrada moderna', vram:0, tgp:null, tgp_max:null,
   res:'FHD', hz:60,  srgb:60, aut_med:7.5,  aut_dec:null},
  {m:'Notebook_X', pr:1050.0, peso:1.8, cpu_gama:'alta',    cpu_nuc:10, virt:'soportada',
   ram:16, ram_tipo:'mixta',     ranuras:1, max_gb:64, canal:'doble',
   ssd:1024, m2:true,  gpu:'dedicada media',    vram:8, tgp:60,  tgp_max:115,
   res:'FHD', hz:144, srgb:95, aut_med:7.0,  aut_dec:null},
  {m:'Notebook_E', pr: 980.0, peso:1.5, cpu_gama:'media',   cpu_nuc: 6, virt:'no soportada',
   ram:16, ram_tipo:'mixta',     ranuras:1, max_gb:32, canal:'doble',
   ssd:1024, m2:true,  gpu:'integrada moderna', vram:0, tgp:null, tgp_max:null,
   res:'FHD', hz:60,  srgb:70, aut_med:7.0,  aut_dec:null},
  {m:'Notebook_C', pr:1200.0, peso:2.3, cpu_gama:'alta',    cpu_nuc:14, virt:'soportada',
   ram:16, ram_tipo:'ampliable', ranuras:2, max_gb:64, canal:'doble',
   ssd:1024, m2:true,  gpu:'dedicada media',    vram:8, tgp:115, tgp_max:115,
   res:'QHD', hz:144, srgb:98, aut_med:5.0,  aut_dec:null},
  {m:'Notebook_G', pr: 650.0, peso:1.9, cpu_gama:'entrada', cpu_nuc: 4, virt:'no informada',
   ram: 8, ram_tipo:'desconocida', ranuras:null, max_gb:null, canal:'desconocido',
   ssd: 512, m2:false, gpu:'integrada moderna', vram:0, tgp:null, tgp_max:null,
   res:'FHD', hz:60,  srgb:55, aut_med:null, aut_dec:5.7,  rend:0.55, pant:0.80},
  {m:'Notebook_M', pr: 880.0, peso:1.5, cpu_gama:'alta',    cpu_nuc: 8, virt:'soportada',
   ram:16, ram_tipo:'mixta',     ranuras:1, max_gb:64, canal:'doble',
   ssd:1024, m2:true,  gpu:'integrada moderna', vram:0, tgp:null, tgp_max:null,
   res:'FHD', hz:60,  srgb:66, aut_med:null, aut_dec:null}
] AS n
MERGE (x:Notebook {modelo:n.m})
SET x.precio_usd = n.pr, x.peso_kg = n.peso,
    x.fuente_precio = 'Mercado Libre Argentina y tiendas oficiales, 01/10/2026'
MERGE (x)-[:POSEE]->(cpu:CPU {notebook:n.m})
SET cpu.gama = n.cpu_gama, cpu.nucleos = n.cpu_nuc, cpu.virtualizacion = n.virt
MERGE (x)-[:POSEE]->(ram:RAM {notebook:n.m})
SET ram.ram_gb = n.ram, ram.tipo = n.ram_tipo, ram.ranuras_libres = n.ranuras,
    ram.max_gb = n.max_gb, ram.canal = n.canal,
    ram.ampliabilidad = CASE WHEN n.ram_tipo = 'desconocida' THEN 'desconocida'
                             WHEN n.ram_tipo = 'soldada' THEN 'no ampliable'
                             ELSE 'ampliable' END
MERGE (x)-[:POSEE]->(alm:Almacenamiento {notebook:n.m})
SET alm.capacidad_gb = n.ssd, alm.tipo = 'SSD', alm.slot_m2_libre = n.m2
MERGE (x)-[:POSEE]->(gpu:GPU {notebook:n.m})
SET gpu.gama = n.gpu, gpu.vram_gb = n.vram, gpu.tgp_w = n.tgp, gpu.tgp_max_w = n.tgp_max,
    gpu.dedicada = (n.gpu STARTS WITH 'dedicada')
MERGE (x)-[:POSEE]->(pan:Pantalla {notebook:n.m})
SET pan.resolucion = n.res, pan.refresco_hz = n.hz, pan.srgb = n.srgb
MERGE (x)-[:POSEE]->(bat:Bateria {notebook:n.m})
SET bat.autonomia_medida_h = n.aut_med, bat.autonomia_declarada_h = n.aut_dec,
    bat.tipo_dato = CASE WHEN n.aut_med IS NOT NULL THEN 'medida'
                         WHEN n.aut_dec IS NOT NULL THEN 'estimada'
                         ELSE 'desconocida' END,
    bat.fuente = CASE WHEN n.aut_med IS NOT NULL THEN 'Notebookcheck / RTINGS' ELSE 'ficha del fabricante' END,
    bat.condicion_uso = 'carga mixta';

MATCH (g:GPU), (gg:GamaGPU)
WHERE g.gama = gg.nombre
MERGE (g)-[:ES_DE_GAMA]->(gg);

// Salidas crisp de PI2 por par notebook-perfil (SM2: rendimiento; SM3:
// pantalla). Las nueve de VIRT son las del Caso 1. La de Notebook_K para
// OFI es un supuesto del grupo para CP11, pendiente de que SM2 la
// recalcule con sus reglas de PI2: es el mismo cuadro que Notebook_B en
// VIRT (CPU por encima de la gama pedida y RAM justo en el minimo), por
// eso 0,80. El estado de CP11 no cambia para cualquier valor entre 0,50 y
// 0,80 (ver informe, d.5).
UNWIND [
  {m:'Notebook_A', p:'VIRT', rend:0.90, pant:1.00, o:'PI2 de SM2 y SM3'},
  {m:'Notebook_B', p:'VIRT', rend:0.80, pant:1.00, o:'PI2 de SM2 y SM3'},
  {m:'Notebook_H', p:'VIRT', rend:0.88, pant:0.90, o:'PI2 de SM2 y SM3'},
  {m:'Notebook_K', p:'VIRT', rend:0.50, pant:0.90, o:'PI2 de SM2 y SM3'},
  {m:'Notebook_X', p:'VIRT', rend:0.92, pant:1.00, o:'PI2 de SM2 y SM3'},
  {m:'Notebook_E', p:'VIRT', rend:0.85, pant:0.95, o:'PI2 de SM2 y SM3'},
  {m:'Notebook_C', p:'VIRT', rend:0.95, pant:1.00, o:'PI2 de SM2 y SM3'},
  {m:'Notebook_G', p:'VIRT', rend:0.55, pant:0.80, o:'PI2 de SM2 y SM3'},
  {m:'Notebook_M', p:'VIRT', rend:0.88, pant:0.95, o:'PI2 de SM2 y SM3'},
  {m:'Notebook_K', p:'OFI',  rend:0.80, pant:0.90, o:'Supuesto del grupo para CP11, pendiente de SM2'}
] AS x
MATCH (n:Notebook {modelo:x.m}), (p:Perfil {codigo:x.p})
MERGE (n)-[s:SALIDA_PI2]->(p)
SET s.adecuacion_rendimiento = x.rend, s.grado_pantalla = x.pant, s.origen = x.o;

// Consulta puntual: el requerimiento pregunta por una notebook concreta
MATCH (c:Requerimiento) WHERE c.notebook_consultada IS NOT NULL
MATCH (n:Notebook {modelo:c.notebook_consultada})
MERGE (c)-[:CONSULTA_POR]->(n);

// GM-R12: autonomia usada (medida, o P_FACTOR_AUTONOMIA x declarada)
MATCH (p:Parametro {nombre:'P_FACTOR_AUTONOMIA'})
MATCH (n:Notebook)-[:POSEE]->(b:Bateria)
SET b.autonomia_usada_h = coalesce(b.autonomia_medida_h, p.valor * b.autonomia_declarada_h),
    b.verificada = (b.autonomia_medida_h IS NOT NULL);

// REN-R16: nivel de ampliabilidad (ordinal, para el desempate de SM4)
MATCH (n:Notebook)-[:POSEE]->(r:RAM), (n)-[:POSEE]->(a:Almacenamiento)
SET r.nivel_ampliabilidad = CASE
  WHEN r.ampliabilidad = 'desconocida' THEN 'desconocida'
  WHEN r.ampliabilidad = 'ampliable' AND a.slot_m2_libre THEN 'alta'
  WHEN r.ampliabilidad = 'ampliable' OR  a.slot_m2_libre THEN 'media'
  ELSE 'baja' END;

// Potencia relativa de la GPU dedicada (entrada difusa de SM3)
MATCH (n:Notebook)-[:POSEE]->(g:GPU)
WHERE g.dedicada AND g.tgp_w IS NOT NULL AND g.tgp_max_w IS NOT NULL
SET g.potencia_relativa = toFloat(g.tgp_w) / g.tgp_max_w,
    g.potencia_verificada = true;


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

// 10.f SM4 - filtro de excluyentes (REC-R3) y evaluacion por notebook
// (la (:Evaluacion) y su excluyente se crearon en 10.c.0)

// Pesos del perfil con el incremento por prioridad (REC-R4, REC-R5)
MATCH (ip:Parametro {nombre:'P_INCREMENTO_PRIORIDAD'})
MATCH (c:Requerimiento)-[:TIENE_PERFIL_DOMINANTE]->(pf:Perfil)
MATCH (c)-[:EVALUA]->(ev:Evaluacion)
WITH ev,
     pf.peso_rendimiento + (CASE WHEN c.prioridad = 'rendimiento' THEN ip.valor ELSE 0.0 END) AS br,
     pf.peso_grafica AS bg,
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
ORDER BY floor(coalesce(ev.grado_recomendacion, ev.grado_recomendacion_min) / me.valor) DESC,
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


