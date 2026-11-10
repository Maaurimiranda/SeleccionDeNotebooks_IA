// =====================================================================
// Grupo 2 – PG2 Unidad 1 – Implementación de la Base de Conocimiento en Neo4j
// Asistente Experto para la Selección Personalizada de Notebooks
// Neo4j 5.x (Browser o cypher-shell), sin APOC. Catorce bloques (0 a 13) que
// se ejecutan en orden; cada sentencia termina en ';'.
//   0–1 limpieza y restricciones      2–3 frames, perfiles, requisitos y parámetros
//   4–5 variables difusas y reglas    6 léxico y gamas      7 compradores y requerimientos
//   8 catálogo                        9 fuzificación        10 inferencia SM1 → SM4
//   11 consultas C1–C3                12 casos de prueba    13 consultas para el LLM
// Gaussianas μ(x) = exp(−(x − c)² / 2σ²) con hombro en los extremos; Mamdani:
// AND = MIN, OR = MAX, recorte, agregación MAX y centroide sobre range(0, 100).
// =====================================================================

// ---------------------------------------------------------------------
// 0. LIMPIEZA
// ---------------------------------------------------------------------
MATCH (n) DETACH DELETE n;

// ---------------------------------------------------------------------
// 1. RESTRICCIONES
// ---------------------------------------------------------------------
CREATE CONSTRAINT comprador_id IF NOT EXISTS FOR (x:Comprador) REQUIRE x.id IS UNIQUE;
CREATE CONSTRAINT requerimiento_id IF NOT EXISTS FOR (x:Requerimiento) REQUIRE x.id IS UNIQUE;
CREATE CONSTRAINT notebook_id IF NOT EXISTS FOR (x:Notebook) REQUIRE x.id IS UNIQUE;
CREATE CONSTRAINT perfil_codigo IF NOT EXISTS FOR (x:Perfil) REQUIRE x.codigo IS UNIQUE;
CREATE CONSTRAINT evaluacion_id IF NOT EXISTS FOR (x:Evaluacion) REQUIRE x.id IS UNIQUE;
CREATE CONSTRAINT variable_nombre IF NOT EXISTS FOR (x:VariableDifusa) REQUIRE x.nombre IS UNIQUE;
CREATE CONSTRAINT regla_id IF NOT EXISTS FOR (x:Regla) REQUIRE x.id IS UNIQUE;
CREATE CONSTRAINT parametro_nombre IF NOT EXISTS FOR (x:Parametro) REQUIRE x.nombre IS UNIQUE;
CREATE CONSTRAINT alerta_id IF NOT EXISTS FOR (x:Alerta) REQUIRE x.id IS UNIQUE;
CREATE CONSTRAINT lectura_id IF NOT EXISTS FOR (x:Lectura) REQUIRE x.id IS UNIQUE;

// ---------------------------------------------------------------------
// 2. FRAMES (capa de soporte): clases del diccionario de PG1 y herencia
// ---------------------------------------------------------------------
UNWIND [
 {f:'Comprador',          p:null,                 s:['id']},
 {f:'Requerimiento',      p:null,                 s:['presupuesto_usd','prioridad','usa_monitor_externo','necesita_virtualizacion','perfil_dominante','intensidad_grafica']},
 {f:'Actividad',          p:null,                 s:['descripcion','evidencia','dedicacion_h','dedicacion_origen','peso_perfil']},
 {f:'ElementoMencionado', p:null,                 s:['nombre']},
 {f:'Software',           p:'ElementoMencionado', s:['exige_virtualizacion']},
 {f:'Juego',              p:'ElementoMencionado', s:['exigencia_grafica']},
 {f:'Carrera',            p:'ElementoMencionado', s:['perfil_por_defecto']},
 {f:'Perfil',             p:null,                 s:['codigo','orden_exigencia','w_rend','w_graf','w_mov']},
 {f:'Requisito',          p:null,                 s:['criterio','valor','es_excluyente']},
 {f:'Notebook',           p:null,                 s:['modelo','precio_usd','peso_kg','adecuacion_rendimiento','adecuacion_grafica','adecuacion_movilidad']},
 {f:'CPU',                p:null,                 s:['gama','virtualizacion']},
 {f:'RAM',                p:null,                 s:['ram_gb','tipo','ranuras_libres','max_gb','indice_ampliabilidad','nivel_ampliabilidad','riesgo_valor']},
 {f:'Almacenamiento',     p:null,                 s:['tipo','gb','m2_libre']},
 {f:'GPU',                p:null,                 s:['tipo','gama','tgp_w','tgp_max_w','potencia_relativa']},
 {f:'Pantalla',           p:null,                 s:['resolucion','refresco_hz','srgb','grado_pantalla']},
 {f:'Bateria',            p:null,                 s:['autonomia_medida_h','autonomia_declarada_h','tipo_dato','autonomia_h']},
 {f:'Evaluacion',         p:null,                 s:['adecuacion_global','excedente_presupuesto','grado_recomendacion','estado']},
 {f:'Recomendacion',      p:null,                 s:['id']},
 {f:'Alerta',             p:null,                 s:['tipo','regla_origen','mensaje']},
 {f:'Pregunta',           p:null,                 s:['texto','estado']}
] AS x
MERGE (f:Frame {nombre:x.f})
SET f.slots = x.s;

MATCH (h:Frame), (p:Frame)
WHERE h.nombre IN ['Software','Juego','Carrera'] AND p.nombre = 'ElementoMencionado'
MERGE (h)-[:ES_UN]->(p);

// ---------------------------------------------------------------------
// 3. PERFILES, REQUISITOS Y PARÁMETROS
//    orden_exigencia (INT-R12): 1 = más exigente (VID3D > GAM > DATOS > VIRT > DIS > DEV > OFI)
//    gamas CPU: 1 entrada, 2 media, 3 alta
//    gamas GPU: 1 integrada básica, 2 integrada moderna, 3 dedicada entrada, 4 dedicada media, 5 dedicada alta
// ---------------------------------------------------------------------
UNWIND [
 {c:'OFI',  o:7, rm:8,  rr:16, sm:256,  sr:512,  cpu:1, gpu:1, virt:false, hz:null, srgb:null, wr:0.30, wg:0.10, wm:0.60},
 {c:'DEV',  o:6, rm:16, rr:32, sm:512,  sr:1024, cpu:2, gpu:1, virt:false, hz:null, srgb:null, wr:0.50, wg:0.10, wm:0.40},
 {c:'DIS',  o:5, rm:16, rr:32, sm:512,  sr:1024, cpu:2, gpu:2, virt:false, hz:null, srgb:95,   wr:0.35, wg:0.45, wm:0.20},
 {c:'VIRT', o:4, rm:16, rr:32, sm:512,  sr:1024, cpu:2, gpu:1, virt:true,  hz:null, srgb:null, wr:0.70, wg:0.10, wm:0.20},
 {c:'DATOS',o:3, rm:16, rr:32, sm:1024, sr:2048, cpu:3, gpu:4, virt:false, hz:null, srgb:null, wr:0.50, wg:0.40, wm:0.10},
 {c:'GAM',  o:2, rm:16, rr:32, sm:512,  sr:1024, cpu:2, gpu:3, virt:false, hz:120,  srgb:null, wr:0.30, wg:0.60, wm:0.10},
 {c:'VID3D',o:1, rm:16, rr:32, sm:1024, sr:2048, cpu:3, gpu:4, virt:false, hz:null, srgb:null, wr:0.40, wg:0.50, wm:0.10}
] AS p
MERGE (x:Perfil {codigo:p.c})
SET x.orden_exigencia = p.o, x.w_rend = p.wr, x.w_graf = p.wg, x.w_mov = p.wm, x.estado_validacion = 'sin validar'
WITH x, p
MATCH (f:Frame {nombre:'Perfil'})
MERGE (x)-[:INSTANCIA_DE]->(f)
WITH x, p
UNWIND [
 {k:'ram_min',        v:p.rm,   ex:false},
 {k:'ram_rec',        v:p.rr,   ex:false},
 {k:'ssd_min',        v:p.sm,   ex:false},
 {k:'ssd_rec',        v:p.sr,   ex:false},
 {k:'gama_cpu',       v:p.cpu,  ex:false},
 {k:'gama_gpu',       v:p.gpu,  ex:true},    // excluyente solo con dos o más gamas por debajo (GM-R4 + GM-R14)
 {k:'virtualizacion', v:CASE WHEN p.virt THEN 'soportada' ELSE null END, ex:p.virt},
 {k:'refresco_hz',    v:p.hz,   ex:false},
 {k:'srgb',           v:p.srgb, ex:false}
] AS q
WITH x, q WHERE q.v IS NOT NULL
MERGE (x)-[:EXIGE]->(r:Requisito {perfil:x.codigo, criterio:q.k})
SET r.valor = q.v, r.es_excluyente = q.ex;

UNWIND [
 {n:'umbral_exigencia',         v:0.40, sm:'SM1', r:'INT-R5',  o:'Decisión del grupo; cruce Marginal/Relevante'},
 {n:'dedicacion_min_h',         v:0.0,  sm:'SM1', r:'INT-R14', o:'Borde del universo de dedicacion_h'},
 {n:'dedicacion_max_h',         v:40.0, sm:'SM1', r:'INT-R14', o:'Borde del universo de dedicacion_h'},
 {n:'peso_gpu',                 v:0.60, sm:'SM3', r:'GM',      o:'Decisión del grupo'},
 {n:'peso_pantalla',            v:0.40, sm:'SM3', r:'GM',      o:'Decisión del grupo'},
 {n:'factor_autonomia',         v:0.70, sm:'SM3', r:'GM-R12',  o:'Fabricantes frente a mediciones de Notebookcheck'},
 {n:'dif_alerta_tgp',           v:0.20, sm:'SM3', r:'GM-R8',   o:'Decisión del grupo'},
 {n:'alfa_alerta_autonomia',    v:0.50, sm:'SM3', r:'GM-R11',  o:'Decisión del grupo'},
 {n:'potencia_min_desconocida', v:0.30, sm:'SM3', r:'GM-R17',  o:'TGP mínimo configurable ÷ máximo (35 W / 115 W)'},
 {n:'incremento_prioridad',     v:0.20, sm:'SM4', r:'REC-R5',  o:'Decisión del grupo'},
 {n:'factor_movilidad_monitor', v:0.50, sm:'SM4', r:'REC-R16', o:'Decisión del grupo'},
 {n:'margen_empate',            v:0.05, sm:'SM4', r:'REC-R8',  o:'Entrevista al técnico y decisión del grupo'}
] AS p
MERGE (x:Parametro {nombre:p.n})
SET x.valor = p.v, x.submodulo = p.sm, x.regla = p.r, x.origen = p.o, x.estado_validacion = 'sin validar';

// ---------------------------------------------------------------------
// 4. VARIABLES DIFUSAS Y ETIQUETAS (15 variables, 47 etiquetas)
// ---------------------------------------------------------------------
UNWIND [
 // SM1 – Olea
 {v:'dedicacion_h',          sm:'SM1', mn:0,   mx:40,  u:'h/semana', e:'rara_vez',           c:0.0,   s:1.5,  t:'hombro_izq'},
 {v:'dedicacion_h',          sm:'SM1', mn:0,   mx:40,  u:'h/semana', e:'ocasional',          c:4.0,   s:2.0,  t:'gauss'},
 {v:'dedicacion_h',          sm:'SM1', mn:0,   mx:40,  u:'h/semana', e:'frecuente',          c:12.0,  s:4.5,  t:'gauss'},
 {v:'dedicacion_h',          sm:'SM1', mn:0,   mx:40,  u:'h/semana', e:'principal',          c:28.0,  s:8.0,  t:'hombro_der'},
 {v:'exigencia_grafica',     sm:'SM1', mn:0,   mx:100, u:'índice',   e:'baja',               c:10.0,  s:12.0, t:'hombro_izq'},
 {v:'exigencia_grafica',     sm:'SM1', mn:0,   mx:100, u:'índice',   e:'media',              c:45.0,  s:12.0, t:'gauss'},
 {v:'exigencia_grafica',     sm:'SM1', mn:0,   mx:100, u:'índice',   e:'alta',               c:80.0,  s:14.0, t:'hombro_der'},
 {v:'peso_perfil',           sm:'SM1', mn:0,   mx:1,   u:'grado',    e:'marginal',           c:0.20,  s:0.12, t:'gauss'},
 {v:'peso_perfil',           sm:'SM1', mn:0,   mx:1,   u:'grado',    e:'relevante',          c:0.60,  s:0.12, t:'gauss'},
 {v:'peso_perfil',           sm:'SM1', mn:0,   mx:1,   u:'grado',    e:'determinante',       c:0.95,  s:0.10, t:'gauss'},
 {v:'intensidad_grafica',    sm:'SM1', mn:0,   mx:1,   u:'grado',    e:'baja',               c:0.15,  s:0.12, t:'gauss'},
 {v:'intensidad_grafica',    sm:'SM1', mn:0,   mx:1,   u:'grado',    e:'media',              c:0.50,  s:0.12, t:'gauss'},
 {v:'intensidad_grafica',    sm:'SM1', mn:0,   mx:1,   u:'grado',    e:'alta',               c:0.85,  s:0.12, t:'gauss'},
 // SM2 – Miranda (el riesgo se conserva en 0–100)
 {v:'suficiencia_ram',       sm:'SM2', mn:0,   mx:3,   u:'ρ',        e:'insuficiente',       c:0.50,  s:0.20, t:'hombro_izq'},
 {v:'suficiencia_ram',       sm:'SM2', mn:0,   mx:3,   u:'ρ',        e:'justa',              c:1.00,  s:0.20, t:'gauss'},
 {v:'suficiencia_ram',       sm:'SM2', mn:0,   mx:3,   u:'ρ',        e:'suficiente',         c:1.50,  s:0.20, t:'gauss'},
 {v:'suficiencia_ram',       sm:'SM2', mn:0,   mx:3,   u:'ρ',        e:'holgada',            c:2.00,  s:0.25, t:'hombro_der'},
 {v:'indice_ampliabilidad',  sm:'SM2', mn:0,   mx:1,   u:'índice',   e:'poca',               c:0.00,  s:0.20, t:'hombro_izq'},
 {v:'indice_ampliabilidad',  sm:'SM2', mn:0,   mx:1,   u:'índice',   e:'media',              c:0.50,  s:0.18, t:'gauss'},
 {v:'indice_ampliabilidad',  sm:'SM2', mn:0,   mx:1,   u:'índice',   e:'mucha',              c:1.00,  s:0.20, t:'hombro_der'},
 {v:'riesgo_obsolescencia',  sm:'SM2', mn:0,   mx:100, u:'puntos',   e:'bajo',               c:0.0,   s:18.0, t:'gauss'},
 {v:'riesgo_obsolescencia',  sm:'SM2', mn:0,   mx:100, u:'puntos',   e:'medio',              c:50.0,  s:15.0, t:'gauss'},
 {v:'riesgo_obsolescencia',  sm:'SM2', mn:0,   mx:100, u:'puntos',   e:'alto',               c:100.0, s:18.0, t:'gauss'},
 // SM3 – de Coninck
 {v:'peso_kg',               sm:'SM3', mn:0.8, mx:4,   u:'kg',       e:'liviana',            c:1.2,   s:0.20, t:'hombro_izq'},
 {v:'peso_kg',               sm:'SM3', mn:0.8, mx:4,   u:'kg',       e:'intermedia',         c:1.8,   s:0.25, t:'gauss'},
 {v:'peso_kg',               sm:'SM3', mn:0.8, mx:4,   u:'kg',       e:'pesada',             c:2.5,   s:0.30, t:'hombro_der'},
 {v:'autonomia_h',           sm:'SM3', mn:1,   mx:24,  u:'h',        e:'baja',               c:3.0,   s:1.0,  t:'hombro_izq'},
 {v:'autonomia_h',           sm:'SM3', mn:1,   mx:24,  u:'h',        e:'media',              c:6.5,   s:1.2,  t:'gauss'},
 {v:'autonomia_h',           sm:'SM3', mn:1,   mx:24,  u:'h',        e:'alta',               c:10.0,  s:1.5,  t:'hombro_der'},
 {v:'potencia_relativa',     sm:'SM3', mn:0,   mx:1,   u:'TGP/TGPmáx', e:'restringida',      c:0.35,  s:0.10, t:'hombro_izq'},
 {v:'potencia_relativa',     sm:'SM3', mn:0,   mx:1,   u:'TGP/TGPmáx', e:'moderada',         c:0.60,  s:0.10, t:'gauss'},
 {v:'potencia_relativa',     sm:'SM3', mn:0,   mx:1,   u:'TGP/TGPmáx', e:'plena',            c:0.80,  s:0.10, t:'hombro_der'},
 {v:'adecuacion_movilidad',  sm:'SM3', mn:0,   mx:1,   u:'grado',    e:'baja',               c:0.05,  s:0.12, t:'gauss'},
 {v:'adecuacion_movilidad',  sm:'SM3', mn:0,   mx:1,   u:'grado',    e:'media',              c:0.50,  s:0.12, t:'gauss'},
 {v:'adecuacion_movilidad',  sm:'SM3', mn:0,   mx:1,   u:'grado',    e:'alta',               c:0.95,  s:0.12, t:'gauss'},
 {v:'grado_gpu',             sm:'SM3', mn:0,   mx:1,   u:'grado',    e:'insuficiente',       c:0.20,  s:0.12, t:'gauss'},
 {v:'grado_gpu',             sm:'SM3', mn:0,   mx:1,   u:'grado',    e:'parcial',            c:0.55,  s:0.12, t:'gauss'},
 {v:'grado_gpu',             sm:'SM3', mn:0,   mx:1,   u:'grado',    e:'pleno',              c:0.95,  s:0.10, t:'gauss'},
 // SM4 – Luconi Furque
 {v:'adecuacion_global',     sm:'SM4', mn:0,   mx:1,   u:'grado',    e:'baja',               c:0.40,  s:0.14, t:'hombro_izq'},
 {v:'adecuacion_global',     sm:'SM4', mn:0,   mx:1,   u:'grado',    e:'media',              c:0.70,  s:0.07, t:'gauss'},
 {v:'adecuacion_global',     sm:'SM4', mn:0,   mx:1,   u:'grado',    e:'alta',               c:0.90,  s:0.07, t:'hombro_der'},
 {v:'excedente_presupuesto', sm:'SM4', mn:0,   mx:30,  u:'%',        e:'dentro',             c:0.0,   s:3.0,  t:'gauss'},
 {v:'excedente_presupuesto', sm:'SM4', mn:0,   mx:30,  u:'%',        e:'levemente_excedido', c:10.0,  s:4.0,  t:'gauss'},
 {v:'excedente_presupuesto', sm:'SM4', mn:0,   mx:30,  u:'%',        e:'muy_excedido',       c:25.0,  s:6.0,  t:'hombro_der'},
 {v:'grado_recomendacion',   sm:'SM4', mn:0,   mx:1,   u:'grado',    e:'descartar',          c:0.0,   s:0.15, t:'gauss'},
 {v:'grado_recomendacion',   sm:'SM4', mn:0,   mx:1,   u:'grado',    e:'considerar',         c:0.5,   s:0.15, t:'gauss'},
 {v:'grado_recomendacion',   sm:'SM4', mn:0,   mx:1,   u:'grado',    e:'recomendar',         c:1.0,   s:0.15, t:'gauss'}
] AS r
MERGE (v:VariableDifusa {nombre:r.v})
SET v.submodulo = r.sm, v.universo_min = r.mn, v.universo_max = r.mx, v.unidad = r.u
CREATE (e:EtiquetaDifusa {variable:r.v, nombre:r.e, centro:r.c, sigma:r.s, tipo:r.t,
        fuente:'PI3 de ' + r.sm, estado_validacion:'sin validar'})
CREATE (v)-[:TIENE_ETIQUETA]->(e)
// cada etiqueta queda ligada a su (:Parametro), como los demás valores calibrables de PG1
MERGE (p:Parametro {nombre:'mf_' + r.v + '_' + r.e})
SET p.valor = r.c, p.sigma = r.s, p.submodulo = r.sm, p.regla = 'función de pertenencia',
    p.origen = 'PI3 de ' + r.sm, p.estado_validacion = 'sin validar'
CREATE (e)-[:SE_PARAMETRIZA_CON]->(p);

// ---------------------------------------------------------------------
// 5. BASE DE REGLAS
// 5.1 Reglas difusas (FZ, GM-RD, INT-RD, REC-RD)
// ---------------------------------------------------------------------
UNWIND [
 {id:'INT-RD1', sm:'SM1', t:'SI dedicación ES rara_vez OR ocasional ENTONCES peso ES marginal',
  ant:[['dedicacion_h','rara_vez'],['dedicacion_h','ocasional']], con:['peso_perfil','marginal']},
 {id:'INT-RD2', sm:'SM1', t:'SI dedicación ES frecuente ENTONCES peso ES relevante',
  ant:[['dedicacion_h','frecuente']], con:['peso_perfil','relevante']},
 {id:'INT-RD3', sm:'SM1', t:'SI dedicación ES principal ENTONCES peso ES determinante',
  ant:[['dedicacion_h','principal']], con:['peso_perfil','determinante']},
 {id:'INT-RD4', sm:'SM1', t:'SI exigencia ES alta AND (dedicación ES frecuente OR principal) ENTONCES intensidad ES alta',
  ant:[['exigencia_grafica','alta'],['dedicacion_h','frecuente'],['dedicacion_h','principal']], con:['intensidad_grafica','alta']},
 {id:'INT-RD5', sm:'SM1', t:'SI exigencia ES alta AND (dedicación ES rara_vez OR ocasional) ENTONCES intensidad ES media',
  ant:[['exigencia_grafica','alta'],['dedicacion_h','rara_vez'],['dedicacion_h','ocasional']], con:['intensidad_grafica','media']},
 {id:'INT-RD6', sm:'SM1', t:'SI exigencia ES media AND (dedicación ES frecuente OR principal) ENTONCES intensidad ES media',
  ant:[['exigencia_grafica','media'],['dedicacion_h','frecuente'],['dedicacion_h','principal']], con:['intensidad_grafica','media']},
 {id:'INT-RD7', sm:'SM1', t:'SI exigencia ES baja OR (exigencia ES media AND (dedicación ES rara_vez OR ocasional)) ENTONCES intensidad ES baja',
  ant:[['exigencia_grafica','baja'],['exigencia_grafica','media'],['dedicacion_h','rara_vez'],['dedicacion_h','ocasional']], con:['intensidad_grafica','baja']},
 {id:'FZ-R1', sm:'SM2', t:'SI suficiencia ES insuficiente AND ampliabilidad ES poca ENTONCES riesgo ES alto',
  ant:[['suficiencia_ram','insuficiente'],['indice_ampliabilidad','poca']], con:['riesgo_obsolescencia','alto']},
 {id:'FZ-R2', sm:'SM2', t:'SI suficiencia ES insuficiente AND (ampliabilidad ES media OR mucha) ENTONCES riesgo ES medio',
  ant:[['suficiencia_ram','insuficiente'],['indice_ampliabilidad','media'],['indice_ampliabilidad','mucha']], con:['riesgo_obsolescencia','medio']},
 {id:'FZ-R3', sm:'SM2', t:'SI suficiencia ES justa AND ampliabilidad ES poca ENTONCES riesgo ES medio',
  ant:[['suficiencia_ram','justa'],['indice_ampliabilidad','poca']], con:['riesgo_obsolescencia','medio']},
 {id:'FZ-R4', sm:'SM2', t:'SI suficiencia ES justa AND (ampliabilidad ES media OR mucha) ENTONCES riesgo ES bajo',
  ant:[['suficiencia_ram','justa'],['indice_ampliabilidad','media'],['indice_ampliabilidad','mucha']], con:['riesgo_obsolescencia','bajo']},
 {id:'FZ-R5', sm:'SM2', t:'SI suficiencia ES suficiente OR holgada ENTONCES riesgo ES bajo',
  ant:[['suficiencia_ram','suficiente'],['suficiencia_ram','holgada']], con:['riesgo_obsolescencia','bajo']},
 {id:'GM-RD1', sm:'SM3', t:'SI peso ES liviana AND autonomía ES alta ENTONCES movilidad ES alta',
  ant:[['peso_kg','liviana'],['autonomia_h','alta']], con:['adecuacion_movilidad','alta']},
 {id:'GM-RD2', sm:'SM3', t:'SI (liviana AND media) OR (intermedia AND (media OR alta)) ENTONCES movilidad ES media',
  ant:[['peso_kg','liviana'],['peso_kg','intermedia'],['autonomia_h','media'],['autonomia_h','alta']], con:['adecuacion_movilidad','media']},
 {id:'GM-RD3', sm:'SM3', t:'SI peso ES pesada OR autonomía ES baja ENTONCES movilidad ES baja',
  ant:[['peso_kg','pesada'],['autonomia_h','baja']], con:['adecuacion_movilidad','baja']},
 {id:'GM-RD4', sm:'SM3', t:'SI (margen superior AND (potencia moderada OR plena)) OR (margen justa AND potencia plena) ENTONCES gpu ES pleno',
  ant:[['potencia_relativa','moderada'],['potencia_relativa','plena']], con:['grado_gpu','pleno']},
 {id:'GM-RD5', sm:'SM3', t:'SI (superior AND restringida) OR (justa AND moderada) OR (inferior AND plena) ENTONCES gpu ES parcial',
  ant:[['potencia_relativa','restringida'],['potencia_relativa','moderada'],['potencia_relativa','plena']], con:['grado_gpu','parcial']},
 {id:'GM-RD6', sm:'SM3', t:'SI (justa AND restringida) OR (inferior AND (restringida OR moderada)) ENTONCES gpu ES insuficiente',
  ant:[['potencia_relativa','restringida'],['potencia_relativa','moderada']], con:['grado_gpu','insuficiente']},
 {id:'REC-RD1', sm:'SM4', t:'SI adecuación ES alta AND excedente ES dentro ENTONCES recomendar',
  ant:[['adecuacion_global','alta'],['excedente_presupuesto','dentro']], con:['grado_recomendacion','recomendar']},
 {id:'REC-RD2', sm:'SM4', t:'SI adecuación ES media AND excedente ES dentro ENTONCES considerar',
  ant:[['adecuacion_global','media'],['excedente_presupuesto','dentro']], con:['grado_recomendacion','considerar']},
 {id:'REC-RD3', sm:'SM4', t:'SI adecuación ES alta AND excedente ES levemente_excedido ENTONCES considerar',
  ant:[['adecuacion_global','alta'],['excedente_presupuesto','levemente_excedido']], con:['grado_recomendacion','considerar']},
 {id:'REC-RD4', sm:'SM4', t:'SI adecuación ES media AND excedente ES levemente_excedido ENTONCES descartar',
  ant:[['adecuacion_global','media'],['excedente_presupuesto','levemente_excedido']], con:['grado_recomendacion','descartar']},
 {id:'REC-RD5', sm:'SM4', t:'SI adecuación ES baja OR excedente ES muy_excedido ENTONCES descartar',
  ant:[['adecuacion_global','baja'],['excedente_presupuesto','muy_excedido']], con:['grado_recomendacion','descartar']}
] AS r
MERGE (x:Regla {id:r.id})
SET x:ReglaDifusa, x.submodulo = r.sm, x.texto = r.t, x.antecedente = split(r.t, ' ENTONCES ')[0],
    x.consecuente = split(r.t, ' ENTONCES ')[1], x.tipo = 'Difusa (Mamdani)', x.fuente = 'PI3',
    x.estado = 'vigente', x.estado_validacion = 'sin validar'
WITH x, r
UNWIND r.ant AS a
MATCH (e:EtiquetaDifusa {variable:a[0], nombre:a[1]})
MERGE (x)-[:ANTECEDENTE]->(e)
WITH DISTINCT x, r
MATCH (c:EtiquetaDifusa {variable:r.con[0], nombre:r.con[1]})
MERGE (x)-[:CONSECUENTE]->(c);

// 5.2 Reglas crisp vigentes y reglas reemplazadas en PG2 (con reemplazada_por)
UNWIND [
 {id:'INT-R2',  sm:'SM1', t:'Software, juego o carrera mencionado → perfil asociado', e:'vigente', rp:null},
 {id:'INT-R3',  sm:'SM1', t:'Software que exige virtualización → necesita_virtualizacion', e:'vigente', rp:null},
 {id:'INT-R4',  sm:'SM1', t:'Expresión de frecuencia → horas por semana (léxico del grafo)', e:'vigente', rp:null},
 {id:'INT-R5',  sm:'SM1', t:'Grado del perfil ≥ umbral_exigencia → impone requisitos; rango que cruza el umbral → indeterminado', e:'vigente', rp:null},
 {id:'INT-R6',  sm:'SM1', t:'Actividad de juego sin título reconocido → intensidad incierta', e:'vigente', rp:null},
 {id:'INT-R12', sm:'SM1', t:'Empate de grado → perfil dominante el más exigente', e:'vigente', rp:null},
 {id:'INT-R13', sm:'SM1', t:'Sin perfil y sin respuesta a la aclaración → perfil indeterminado y pregunta', e:'vigente', rp:null},
 {id:'INT-R14', sm:'SM1', t:'Dedicación desconocida → lecturas 0 h y 40 h y grado en rango', e:'vigente', rp:null},
 {id:'REN-R1',  sm:'SM2', t:'El perfil exige virtualización y la CPU no la soporta → excluyente incumplido', e:'vigente', rp:null},
 {id:'REN-R2',  sm:'SM2', t:'Requisito consolidado = el más exigente de los perfiles que imponen', e:'vigente', rp:null},
 {id:'REN-R6',  sm:'SM2', t:'RAM soldada menor a la recomendada → riesgo de obsolescencia', e:'reemplazada en PG2', rp:'FZ-R1..R5'},
 {id:'REN-R7',  sm:'SM2', t:'RAM menor al mínimo pero ampliable hasta cumplirlo → alerta "condicionado a ampliación"', e:'vigente', rp:null},
 {id:'REN-R9',  sm:'SM2', t:'Bonificación por RAM ampliable', e:'reemplazada en PG2', rp:'FZ-R2, FZ-R4'},
 {id:'REN-R10', sm:'SM2', t:'Ampliabilidad desconocida → alerta y riesgo en rango', e:'vigente', rp:null},
 {id:'REN-R13', sm:'SM2', t:'Virtualización no informada → falta información (excluyente no verificado)', e:'vigente', rp:null},
 {id:'REN-R16', sm:'SM2', t:'RAM ampliable y slot M.2 libre → nivel alto; una → medio; ninguna → bajo', e:'vigente', rp:null},
 {id:'FZ-R6',   sm:'SM2', t:'Ampliabilidad desconocida → lecturas a = 0 y a = 1', e:'vigente', rp:null},
 {id:'FZ-R7',   sm:'SM2', t:'Riesgo alto en el peor caso → alerta', e:'vigente', rp:null},
 {id:'GM-R4',   sm:'SM3', t:'GPU integrada: gama ≥ requerida → 1; un nivel abajo → 0,5; dos o más → 0', e:'vigente', rp:null},
 {id:'GM-R8',   sm:'SM3', t:'El grado difuso de la GPU cae más de dif_alerta_tgp respecto del de la sola gama → alerta', e:'vigente', rp:null},
 {id:'GM-R10',  sm:'SM3', t:'Peso y autonomía → pertenencias (solo fuzificación; la movilidad la infieren GM-RD1..RD3)', e:'vigente', rp:null},
 {id:'GM-R11',  sm:'SM3', t:'Prioridad autonomía y μ(autonomía baja) ≥ alfa_alerta_autonomia → alerta "autonomía insuficiente"', e:'vigente', rp:null},
 {id:'GM-R12',  sm:'SM3', t:'Autonomía medida, o estimada = 0,7 × declarada; ninguna → desconocida', e:'vigente', rp:null},
 {id:'GM-R14',  sm:'SM3', t:'GPU dos o más gamas por debajo → excluyente incumplido', e:'vigente', rp:null},
 {id:'GM-R16',  sm:'SM3', t:'Monitor externo → pantalla 1,0', e:'vigente', rp:null},
 {id:'GM-R17',  sm:'SM3', t:'TGP desconocido → lecturas con potencia mínima y plena', e:'vigente', rp:null},
 {id:'REC-R1',  sm:'SM4', t:'Precio > 110 % del presupuesto → descartar', e:'reemplazada en PG2', rp:'REC-RD3, REC-RD5'},
 {id:'REC-R2',  sm:'SM4', t:'Entre 100 % y 110 % con mejora ≥ 0,1 → fuera de presupuesto (máx. 1)', e:'reemplazada en PG2', rp:'REC-RD3'},
 {id:'REC-R3',  sm:'SM4', t:'Excluyente incumplido → descartar; excluyente sin dato → indeterminada', e:'vigente', rp:null},
 {id:'REC-R4',  sm:'SM4', t:'Pesos del perfil dominante', e:'vigente', rp:null},
 {id:'REC-R5',  sm:'SM4', t:'+0,2 al peso de la prioridad declarada', e:'vigente', rp:null},
 {id:'REC-R6',  sm:'SM4', t:'Global ≥ 0,8 Alta; 0,6 a 0,8 Media; < 0,6 descartar', e:'reemplazada en PG2', rp:'REC-RD1..RD5'},
 {id:'REC-R8',  sm:'SM4', t:'Diferencia < margen_empate → primero la más ampliable', e:'vigente', rp:null},
 {id:'REC-R10', sm:'SM4', t:'Ninguna propuesta → sin alternativa adecuada', e:'vigente', rp:null},
 {id:'REC-R11', sm:'SM4', t:'Explicación en tres bloques sin mencionar nada ausente de la traza', e:'vigente', rp:null},
 {id:'REC-R12', sm:'SM4', t:'Fuera de presupuesto solo si mejora en 0,1 a la mejor', e:'reemplazada en PG2', rp:'REC-RD3'},
 {id:'REC-R15', sm:'SM4', t:'Falta un dato que solo ordena → rango y recomendación condicionada', e:'vigente', rp:null},
 {id:'REC-R16', sm:'SM4', t:'Monitor externo → mitad del peso de movilidad', e:'vigente', rp:null}
] AS r
MERGE (x:Regla {id:r.id})
SET x:ReglaCrisp, x.submodulo = r.sm, x.texto = r.t, x.tipo = 'Crisp', x.estado = r.e,
    x.reemplazada_por = r.rp, x.estado_validacion = 'sin validar';

// ---------------------------------------------------------------------
// 6. LÉXICO Y GAMAS
// ---------------------------------------------------------------------
UNWIND [
 {t:'casi nunca', h:0.5}, {t:'a veces', h:4.0}, {t:'de vez en cuando', h:4.0},
 {t:'los fines de semana', h:6.0}, {t:'bastante', h:12.0}, {t:'varias veces por semana', h:12.0},
 {t:'todos los días', h:14.0}, {t:'principalmente', h:28.0}, {t:'la necesito para', h:28.0}
] AS x
MERGE (e:ExpresionFrecuencia {texto:x.t})
SET e.horas_ref = x.h, e.fuente = 'Casos publicados de asesoramiento (PI3 SM1)', e.estado_validacion = 'sin validar';

// Gamas de GPU con su índice de exigencia (lo usan SM1 para los juegos y SM3 para el margen)
UNWIND [
 {g:1, n:'integrada básica', i:5.0}, {g:2, n:'integrada moderna', i:30.0}, {g:3, n:'dedicada de entrada', i:45.0},
 {g:4, n:'dedicada media', i:70.0}, {g:5, n:'dedicada alta', i:90.0}
] AS x
MERGE (g:GamaGPU {nivel:x.g})
SET g.nombre = x.n, g.indice_exigencia = x.i, g.estado_validacion = 'sin validar';

// Elementos mencionados (INT-R2): software y juegos con su perfil
UNWIND [{n:'Docker', pf:'VIRT'}, {n:'VirtualBox', pf:'VIRT'}] AS x
MATCH (pf:Perfil {codigo:x.pf}), (f:Frame {nombre:'Software'})
MERGE (el:ElementoMencionado:Software {nombre:x.n})
SET el.exige_virtualizacion = true
MERGE (el)-[:ASOCIADO_A]->(pf)
MERGE (el)-[:INSTANCIA_DE]->(f);

UNWIND [{n:'Stardew Valley', g:1}, {n:'Cyberpunk 2077', g:4}] AS x
MATCH (pf:Perfil {codigo:'GAM'}), (gg:GamaGPU {nivel:x.g}), (f:Frame {nombre:'Juego'})
MERGE (el:ElementoMencionado:Juego {nombre:x.n})
SET el.exige_virtualizacion = false, el.exigencia_grafica = gg.indice_exigencia
MERGE (el)-[:RECOMIENDA_GAMA]->(gg)
MERGE (el)-[:ASOCIADO_A]->(pf)
MERGE (el)-[:INSTANCIA_DE]->(f);

// ---------------------------------------------------------------------
// 7. COMPRADORES Y REQUERIMIENTOS (Comprador ≠ Requerimiento)
// ---------------------------------------------------------------------
CREATE (c1:Comprador {id:'comprador_01'})
CREATE (c2:Comprador {id:'comprador_02'})
CREATE (c1)-[:FORMULA]->(:Requerimiento {id:'req_01', presupuesto_usd:1000, prioridad:'rendimiento',
        usa_monitor_externo:false, necesita_virtualizacion:false, perfil_dominante:'indeterminado',
        texto_pedido:'Necesito una notebook para programar, usar máquinas virtuales y Docker, y a veces jugar al Stardew Valley. Tengo 1000 USD.'})
CREATE (c2)-[:FORMULA]->(:Requerimiento {id:'req_02', presupuesto_usd:600, prioridad:'ninguna',
        usa_monitor_externo:false, necesita_virtualizacion:false, perfil_dominante:'indeterminado',
        aclaracion:'sin respuesta', texto_pedido:'Quiero una notebook para la facu, tengo 600 USD.'});

MATCH (x) WHERE x:Comprador OR x:Requerimiento
MATCH (f:Frame) WHERE f.nombre IN labels(x)
MERGE (x)-[:INSTANCIA_DE]->(f);

// Actividades extraídas por el LLM con su evidencia textual (INT-R7). El LLM solo extrae la
// expresión; las horas las pone el léxico. perfil_descripcion: perfil deducido de la descripción
// cuando la actividad no usa ningún elemento mencionado (programar → VIRT, como en la PI3 de SM1).
UNWIND [
 {id:'ACT_PROG',  d:'programar',                  ev:'la necesito para programar',       ex:'la necesito para', el:null,             pf:'VIRT'},
 {id:'ACT_VIRT',  d:'virtualizar (VMs y Docker)', ev:'usar máquinas virtuales y Docker', ex:'la necesito para', el:'Docker',         pf:null},
 {id:'ACT_JUGAR', d:'jugar',                      ev:'a veces jugar al Stardew Valley',  ex:'a veces',          el:'Stardew Valley', pf:null}
] AS a
MATCH (r:Requerimiento {id:'req_01'}), (f:Frame {nombre:'Actividad'})
CREATE (r)-[:INCLUYE]->(x:Actividad {id:a.id, descripcion:a.d, evidencia:a.ev, perfil_descripcion:a.pf})
CREATE (x)-[:INSTANCIA_DE]->(f)
WITH x, a
OPTIONAL MATCH (e:ExpresionFrecuencia {texto:a.ex})
OPTIONAL MATCH (el:ElementoMencionado {nombre:a.el})
FOREACH (_ IN CASE WHEN e IS NULL THEN [] ELSE [1] END | MERGE (x)-[:EXPRESADA_COMO]->(e))
FOREACH (_ IN CASE WHEN el IS NULL THEN [] ELSE [1] END | MERGE (x)-[:USA]->(el));

// ---------------------------------------------------------------------
// 8. CATÁLOGO DE PRUEBA (nueve notebooks; precios al 01/10/2026)
//    rend y pant: adecuación de rendimiento y grado de pantalla cargados como valores crisp
// ---------------------------------------------------------------------
UNWIND [
 {id:'NB_A', p:950,  kg:1.4, rend:0.90, vt:'soportada',    ram:16, rt:'ampliable', ran:1,    mx:64,   m2:false, gt:'integrada', gg:2, tgp:null, tmx:null, pant:1.00, med:8.0,  dec:null},
 {id:'NB_B', p:700,  kg:1.3, rend:0.80, vt:'soportada',    ram:16, rt:'soldada',   ran:0,    mx:16,   m2:false, gt:'integrada', gg:2, tgp:null, tmx:null, pant:1.00, med:10.0, dec:null},
 {id:'NB_H', p:1000, kg:2.0, rend:0.88, vt:'soportada',    ram:16, rt:'ampliable', ran:1,    mx:32,   m2:true,  gt:'integrada', gg:2, tgp:null, tmx:null, pant:0.90, med:6.0,  dec:null},
 {id:'NB_K', p:900,  kg:1.6, rend:0.50, vt:'soportada',    ram:8,  rt:'ampliable', ran:1,    mx:32,   m2:false, gt:'integrada', gg:2, tgp:null, tmx:null, pant:0.90, med:7.5,  dec:null},
 {id:'NB_X', p:1050, kg:1.8, rend:0.92, vt:'soportada',    ram:16, rt:'ampliable', ran:1,    mx:64,   m2:false, gt:'dedicada',  gg:4, tgp:60,   tmx:115,  pant:1.00, med:7.0,  dec:null},
 {id:'NB_E', p:980,  kg:1.5, rend:0.85, vt:'no soportada', ram:16, rt:'ampliable', ran:1,    mx:32,   m2:false, gt:'integrada', gg:2, tgp:null, tmx:null, pant:0.95, med:7.0,  dec:null},
 {id:'NB_C', p:1200, kg:2.3, rend:0.95, vt:'soportada',    ram:16, rt:'ampliable', ran:2,    mx:64,   m2:true,  gt:'dedicada',  gg:4, tgp:115,  tmx:115,  pant:1.00, med:5.0,  dec:null},
 {id:'NB_G', p:650,  kg:1.9, rend:0.55, vt:'no informada', ram:8,  rt:'desconocida', ran:null, mx:null, m2:false, gt:'integrada', gg:2, tgp:null, tmx:null, pant:0.80, med:null, dec:5.7},
 {id:'NB_M', p:880,  kg:1.5, rend:0.88, vt:'soportada',    ram:16, rt:'ampliable', ran:1,    mx:64,   m2:false, gt:'integrada', gg:2, tgp:null, tmx:null, pant:0.95, med:null, dec:null}
] AS d
CREATE (n:Notebook {id:d.id, modelo:replace(d.id, 'NB_', 'Notebook_'), precio_usd:d.p, peso_kg:d.kg,
        adecuacion_rendimiento:d.rend})
CREATE (n)-[:POSEE]->(:CPU {virtualizacion:d.vt})
CREATE (n)-[:POSEE]->(:RAM {ram_gb:d.ram, tipo:d.rt, ranuras_libres:d.ran, max_gb:d.mx})
CREATE (n)-[:POSEE]->(:Almacenamiento {tipo:'SSD', m2_libre:d.m2})
CREATE (n)-[:POSEE]->(:GPU {tipo:d.gt, gama:d.gg, tgp_w:d.tgp, tgp_max_w:d.tmx})
CREATE (n)-[:POSEE]->(:Pantalla {grado_pantalla:d.pant})
CREATE (n)-[:POSEE]->(:Bateria {autonomia_medida_h:d.med, autonomia_declarada_h:d.dec,
        tipo_dato: CASE WHEN d.med IS NOT NULL THEN 'medida' WHEN d.dec IS NOT NULL THEN 'estimada' ELSE 'desconocida' END});

MATCH (x) WHERE x:Notebook OR x:CPU OR x:RAM OR x:Almacenamiento OR x:GPU OR x:Pantalla OR x:Bateria
MATCH (f:Frame) WHERE f.nombre IN labels(x)
MERGE (x)-[:INSTANCIA_DE]->(f);

// ---------------------------------------------------------------------
// 9. FUZIFICACIÓN DE LOS DATOS DE ENTRADA (materializa [:PERTENECE_A {grado, valor_crisp, ts}])
// ---------------------------------------------------------------------
// 9.1 INT-R4: de la expresión al valor crisp (horas por semana). Sin dato → 'desconocida' (D4)
MATCH (a:Actividad)
OPTIONAL MATCH (a)-[:EXPRESADA_COMO]->(e:ExpresionFrecuencia)
SET a.dedicacion_h = coalesce(a.horas_explicitas_semana, e.horas_ref),
    a.dedicacion_origen = CASE WHEN a.horas_explicitas_semana IS NOT NULL THEN 'declarada'
                               WHEN e IS NOT NULL THEN 'léxico' ELSE 'desconocida' END;

// 9.2 Lecturas de dedicación: valor conocido → una; desconocido → 0 h y 40 h (INT-R14 corregida)
MATCH (a:Actividad)
MATCH (pmin:Parametro {nombre:'dedicacion_min_h'}), (pmax:Parametro {nombre:'dedicacion_max_h'})
UNWIND CASE WHEN a.dedicacion_h IS NULL THEN [{esc:'min', x:pmin.valor}, {esc:'max', x:pmax.valor}]
            ELSE [{esc:'unico', x: CASE WHEN a.dedicacion_h > 40 THEN 40.0 ELSE toFloat(a.dedicacion_h) END}] END AS es
MERGE (a)-[:TIENE_LECTURA]->(l:Lectura {id: a.id + '_dedicacion_' + es.esc})
SET l.variable = 'dedicacion_h', l.escenario = es.esc, l.valor_crisp = es.x;

// 9.3 Fuzificación genérica de las entradas que son datos del pedido o de la ficha
//     (dedicación en la lectura, exigencia del juego, peso de la notebook)
MATCH (n) WHERE (n:Lectura AND n.variable = 'dedicacion_h') OR (n:Juego AND n.exigencia_grafica IS NOT NULL) OR n:Notebook
WITH n, CASE WHEN n:Lectura THEN 'dedicacion_h' WHEN n:Juego THEN 'exigencia_grafica' ELSE 'peso_kg' END AS var,
        CASE WHEN n:Lectura THEN n.valor_crisp WHEN n:Juego THEN n.exigencia_grafica ELSE n.peso_kg END AS x
MATCH (:VariableDifusa {nombre:var})-[:TIENE_ETIQUETA]->(e:EtiquetaDifusa)
MERGE (n)-[f:PERTENECE_A]->(e)
SET f.grado = CASE
      WHEN e.tipo = 'hombro_izq' AND x <= e.centro THEN 1.0
      WHEN e.tipo = 'hombro_der' AND x >= e.centro THEN 1.0
      ELSE exp(-((x - e.centro)^2) / (2.0 * e.sigma^2)) END,
    f.valor_crisp = x, f.ts = datetime();

// 9.4 Autonomía (GM-R12): medida, o 0,7 × declarada; ninguna → 'desconocida' y sin fuzificar
MATCH (b:Bateria), (fa:Parametro {nombre:'factor_autonomia'})
SET b.autonomia_h = CASE WHEN b.autonomia_medida_h IS NOT NULL THEN toFloat(b.autonomia_medida_h)
                         WHEN b.autonomia_declarada_h IS NOT NULL THEN round(fa.valor * b.autonomia_declarada_h, 2)
                         ELSE null END;

MATCH (b:Bateria) WHERE b.autonomia_h IS NOT NULL
MATCH (:VariableDifusa {nombre:'autonomia_h'})-[:TIENE_ETIQUETA]->(e:EtiquetaDifusa)
WITH b, e, b.autonomia_h AS x
MERGE (b)-[f:PERTENECE_A]->(e)
SET f.grado = CASE
      WHEN e.tipo = 'hombro_izq' AND x <= e.centro THEN 1.0
      WHEN e.tipo = 'hombro_der' AND x >= e.centro THEN 1.0
      ELSE exp(-((x - e.centro)^2) / (2.0 * e.sigma^2)) END,
    f.valor_crisp = x, f.ts = datetime();

// 9.5 Potencia relativa de la GPU dedicada; TGP desconocido → lecturas 0,30 y 1,0 (GM-R17)
MATCH (g:GPU {tipo:'dedicada'}), (pm:Parametro {nombre:'potencia_min_desconocida'})
SET g.potencia_relativa = CASE WHEN g.tgp_w IS NULL OR g.tgp_max_w IS NULL THEN null
                               ELSE round(toFloat(g.tgp_w) / g.tgp_max_w, 3) END
WITH g, pm
UNWIND CASE WHEN g.potencia_relativa IS NULL THEN [{esc:'peor', x:pm.valor}, {esc:'mejor', x:1.0}]
            ELSE [{esc:'unico', x:g.potencia_relativa}] END AS es
MATCH (n:Notebook)-[:POSEE]->(g)
MERGE (g)-[:TIENE_LECTURA]->(l:Lectura {id: n.id + '_potencia_' + es.esc})
SET l.variable = 'potencia_relativa', l.escenario = es.esc, l.valor_crisp = es.x
WITH l, es.x AS x
MATCH (:VariableDifusa {nombre:'potencia_relativa'})-[:TIENE_ETIQUETA]->(e:EtiquetaDifusa)
MERGE (l)-[f:PERTENECE_A]->(e)
SET f.grado = CASE
      WHEN e.tipo = 'hombro_izq' AND x <= e.centro THEN 1.0
      WHEN e.tipo = 'hombro_der' AND x >= e.centro THEN 1.0
      ELSE exp(-((x - e.centro)^2) / (2.0 * e.sigma^2)) END,
    f.valor_crisp = x, f.ts = datetime();

// =====================================================================
// 10. INFERENCIA (SM1 → SM2 → SM3 → SM4); cada regla activada queda como [:ACTIVA {fuerza}]
// =====================================================================
// ---------- 10.a SM1 – Interpretación del pedido ----------
// INT-R2 / INT-R11: la actividad lleva al perfil del elemento que usa; si no usa ninguno, al de su descripción
MATCH (a:Actividad)
OPTIONAL MATCH (a)-[:USA]->(:ElementoMencionado)-[:ASOCIADO_A]->(pe:Perfil)
OPTIONAL MATCH (pd:Perfil {codigo:a.perfil_descripcion})
WITH a, pe, pd, coalesce(pe, pd) AS pf
WHERE pf IS NOT NULL
MERGE (a)-[l:LLEVA_A]->(pf)
SET l.regla_origen = CASE WHEN pe IS NOT NULL THEN 'INT-R2' ELSE 'INT-R11 (descripción)' END;

// INT-R3: necesidad de virtualización deducida de los elementos mencionados
MATCH (r:Requerimiento)
SET r.necesita_virtualizacion = EXISTS {
      MATCH (r)-[:INCLUYE]->(:Actividad)-[:USA]->(:ElementoMencionado {exige_virtualizacion:true}) };

// INT-RD1..3 + centroide → peso de la actividad en el perfil (una vez por lectura)
MATCH (a:Actividad)-[:TIENE_LECTURA]->(l:Lectura {variable:'dedicacion_h'})-[p:PERTENECE_A]->(e:EtiquetaDifusa)
WITH a, l, collect({e:e.nombre, mu:p.grado}) AS D
WITH a, l, [x IN D WHERE x.e = 'rara_vez'][0].mu AS rv, [x IN D WHERE x.e = 'ocasional'][0].mu AS oc,
           [x IN D WHERE x.e = 'frecuente'][0].mu AS fr, [x IN D WHERE x.e = 'principal'][0].mu AS pr
WITH a, l, [{r:'INT-RD1', o:'marginal',     w: CASE WHEN rv > oc THEN rv ELSE oc END},   // OR = MAX
            {r:'INT-RD2', o:'relevante',    w: fr},
            {r:'INT-RD3', o:'determinante', w: pr}] AS reglas
CALL {
  WITH a, l, reglas
  UNWIND reglas AS rg
  WITH a, l, rg WHERE rg.w > 0.01
  MATCH (x:Regla {id:rg.r})
  MERGE (a)-[t:ACTIVA {escenario:l.escenario}]->(x) SET t.fuerza = round(rg.w, 3)
}
MATCH (:VariableDifusa {nombre:'peso_perfil'})-[:TIENE_ETIQUETA]->(o)
UNWIND range(0, 100) AS i
WITH a, l, i / 100.0 AS y, exp(-((i / 100.0 - o.centro)^2) / (2.0 * o.sigma^2)) AS g,
     reduce(w = 0.0, rg IN reglas | CASE WHEN rg.o = o.nombre AND rg.w > w THEN rg.w ELSE w END) AS wo
WITH a, l, y, max(CASE WHEN g < wo THEN g ELSE wo END) AS mu          // recorte = MIN; agregación = MAX
WITH a, l, sum(y * mu) / sum(mu) AS peso                               // centroide
SET l.peso_perfil = round(peso, 3);

MATCH (a:Actividad)-[:TIENE_LECTURA]->(l:Lectura {variable:'dedicacion_h'})
WITH a, min(l.peso_perfil) AS pmin, max(l.peso_perfil) AS pmax
SET a.peso_perfil_min = pmin, a.peso_perfil_max = pmax,
    a.peso_perfil = CASE WHEN pmin = pmax THEN pmin ELSE null END;

// Asignación de perfil (MAX entre actividades) + INT-R5 (alfa-corte). Rango que cruza el umbral → indeterminado
MATCH (r:Requerimiento)-[:INCLUYE]->(a:Actividad)-[:LLEVA_A]->(pf:Perfil)
WITH r, pf, max(a.peso_perfil_min) AS gmin, max(a.peso_perfil_max) AS gmax
MATCH (u:Parametro {nombre:'umbral_exigencia'})
MERGE (r)-[t:PERTENECE]->(pf)
SET t.grado_min = gmin, t.grado_max = gmax,
    t.grado = CASE WHEN gmin = gmax THEN gmin ELSE null END,
    t.impone_requisitos = CASE WHEN gmin >= u.valor THEN true WHEN gmax < u.valor THEN false ELSE null END,
    t.estado = CASE WHEN gmin >= u.valor THEN 'impone requisitos' WHEN gmax < u.valor THEN 'preferencia'
                    ELSE 'indeterminado' END,
    t.regla_origen = 'INT-RD1..3 + INT-R5';

MATCH (r:Requerimiento)-[t:PERTENECE {estado:'indeterminado'}]->(pf:Perfil)
MERGE (q:Pregunta {id: r.id + '_INT-R14_' + pf.codigo})
SET q.texto = '¿Cuántas horas por semana va a dedicar a las actividades del perfil ' + pf.codigo + '?',
    q.regla_origen = 'INT-R14', q.estado = 'pendiente'
MERGE (r)-[:TIENE_PREGUNTA]->(q)
MERGE (al:Alerta {id: r.id + '_INT-R14_' + pf.codigo})
SET al.tipo = 'Dedicación desconocida', al.submodulo_origen = 'SM1', al.regla_origen = 'INT-R14',
    al.mensaje = 'El grado del perfil ' + pf.codigo + ' queda en [' + toString(t.grado_min) + ' ; ' +
                 toString(t.grado_max) + '] y no se sabe si impone requisitos'
MERGE (r)-[:GENERA]->(al);

// INT-R12: perfil dominante = mayor grado; ante empate, el más exigente (orden_exigencia ascendente)
MATCH (r:Requerimiento)-[t:PERTENECE]->(pf:Perfil)
WITH r, pf, t ORDER BY coalesce(t.grado, t.grado_min) DESC, pf.orden_exigencia ASC
WITH r, collect(pf)[0] AS dom
SET r.perfil_dominante = dom.codigo
MERGE (r)-[:TIENE_PERFIL_DOMINANTE]->(dom);

// INT-R13 corregida: sin perfil y sin respuesta → 'indeterminado', pregunta pendiente, no se evalúa el catálogo
MATCH (r:Requerimiento {perfil_dominante:'indeterminado'})
SET r.resultado = 'Pendiente: perfil indeterminado', r.regla_resultado = 'INT-R13'
MERGE (q:Pregunta {id: r.id + '_INT-R13'})
SET q.texto = '¿Qué carrera cursa o para qué actividades va a usar la notebook?', q.regla_origen = 'INT-R13',
    q.estado = 'pendiente'
MERGE (r)-[:TIENE_PREGUNTA]->(q)
MERGE (al:Alerta {id: r.id + '_INT-R13'})
SET al.tipo = 'Perfil indeterminado', al.submodulo_origen = 'SM1', al.regla_origen = 'INT-R13',
    al.mensaje = 'No se pudo determinar el perfil y la aclaración no tuvo respuesta. No se asume OFI.'
MERGE (r)-[:GENERA]->(al);

// INT-RD4..7: intensidad gráfica (dedicación × exigencia); varios juegos → MAX por regla
MATCH (r:Requerimiento)-[:INCLUYE]->(a:Actividad)-[:USA]->(j:Juego)
MATCH (a)-[:TIENE_LECTURA]->(l:Lectura {variable:'dedicacion_h'})-[pd:PERTENECE_A]->(ed:EtiquetaDifusa)
WITH r, j, l, collect({e:ed.nombre, mu:pd.grado}) AS D
MATCH (j)-[pj:PERTENECE_A]->(ej:EtiquetaDifusa {variable:'exigencia_grafica'})
WITH r, l, D, collect({e:ej.nombre, mu:pj.grado}) AS E
WITH r, l,
     [x IN D WHERE x.e = 'rara_vez'][0].mu AS rv, [x IN D WHERE x.e = 'ocasional'][0].mu AS oc,
     [x IN D WHERE x.e = 'frecuente'][0].mu AS fr, [x IN D WHERE x.e = 'principal'][0].mu AS pr,
     [x IN E WHERE x.e = 'baja'][0].mu AS eB, [x IN E WHERE x.e = 'media'][0].mu AS eM,
     [x IN E WHERE x.e = 'alta'][0].mu AS eA
WITH r, l, eB, eM, eA,
     CASE WHEN rv > oc THEN rv ELSE oc END AS dPoca,
     CASE WHEN fr > pr THEN fr ELSE pr END AS dMucha
WITH r, l, eB,
     CASE WHEN eA < dMucha THEN eA ELSE dMucha END AS w4,
     CASE WHEN eA < dPoca  THEN eA ELSE dPoca  END AS w5,
     CASE WHEN eM < dMucha THEN eM ELSE dMucha END AS w6,
     CASE WHEN eM < dPoca  THEN eM ELSE dPoca  END AS t7
WITH r, l.escenario AS esc, max(w4) AS w4, max(w5) AS w5, max(w6) AS w6,
     max(CASE WHEN eB > t7 THEN eB ELSE t7 END) AS w7
WITH r, esc, [{r:'INT-RD4', o:'alta', w:w4}, {r:'INT-RD5', o:'media', w:w5},
              {r:'INT-RD6', o:'media', w:w6}, {r:'INT-RD7', o:'baja', w:w7}] AS reglas
CALL {
  WITH r, esc, reglas
  UNWIND reglas AS rg
  WITH r, esc, rg WHERE rg.w > 0.01
  MATCH (x:Regla {id:rg.r})
  MERGE (r)-[t:ACTIVA {escenario:esc}]->(x) SET t.fuerza = round(rg.w, 3)
}
MATCH (:VariableDifusa {nombre:'intensidad_grafica'})-[:TIENE_ETIQUETA]->(o)
UNWIND range(0, 100) AS i
WITH r, esc, i / 100.0 AS y, exp(-((i / 100.0 - o.centro)^2) / (2.0 * o.sigma^2)) AS g,
     reduce(w = 0.0, rg IN reglas | CASE WHEN rg.o = o.nombre AND rg.w > w THEN rg.w ELSE w END) AS wo
WITH r, esc, y, max(CASE WHEN g < wo THEN g ELSE wo END) AS mu
WITH r, esc, sum(y * mu) / sum(mu) AS inten
MATCH (:VariableDifusa {nombre:'intensidad_grafica'})-[:TIENE_ETIQUETA]->(o2)
WITH r, esc, inten, o2 ORDER BY exp(-((inten - o2.centro)^2) / (2.0 * o2.sigma^2)) DESC
WITH r, esc, inten, collect(o2.nombre)[0] AS etiqueta             // mayor pertenencia del valor desborrosificado
WITH r, collect({esc:esc, v:inten, et:etiqueta}) AS res
SET r.intensidad_min = round(reduce(m = 1.0, x IN res | CASE WHEN x.v < m THEN x.v ELSE m END), 3),
    r.intensidad_max = round(reduce(m = 0.0, x IN res | CASE WHEN x.v > m THEN x.v ELSE m END), 3),
    r.intensidad_valor = CASE WHEN size(res) = 1 THEN round(res[0].v, 3) ELSE null END,
    r.intensidad_grafica = CASE WHEN all(x IN res WHERE x.et = res[0].et) THEN res[0].et ELSE 'incierta' END;

// INT-R6: juego sin título reconocido → 'incierta'; sin actividad de juego → 'nula'
MATCH (r:Requerimiento) WHERE r.intensidad_grafica IS NULL
SET r.intensidad_grafica = CASE WHEN EXISTS { MATCH (r)-[:INCLUYE]->(:Actividad)-[:LLEVA_A]->(:Perfil {codigo:'GAM'}) }
                                THEN 'incierta' ELSE 'nula' END;

// REN-R2: requisito consolidado = el más exigente de los perfiles que imponen requisitos.
//         Para GAM, la gama de GPU sale de la intensidad gráfica (GM-R1..R3).
MATCH (r:Requerimiento)-[:PERTENECE {impone_requisitos:true}]->(pf:Perfil)-[:EXIGE]->(q:Requisito)
WITH r, q.criterio AS k,
     max(CASE WHEN q.criterio = 'gama_gpu' AND pf.codigo = 'GAM'
              THEN CASE r.intensidad_grafica WHEN 'alta' THEN 4 WHEN 'media' THEN 3 WHEN 'baja' THEN 2 ELSE q.valor END
              WHEN q.criterio = 'virtualizacion' THEN 1 ELSE q.valor END) AS v,
     collect(DISTINCT pf.codigo) AS origen
WITH r, collect({k:k, v:v, o:origen}) AS req
SET r.req_ram_min  = [x IN req WHERE x.k = 'ram_min'][0].v,
    r.req_ram_rec  = [x IN req WHERE x.k = 'ram_rec'][0].v,
    r.req_gama_gpu = [x IN req WHERE x.k = 'gama_gpu'][0].v,
    r.req_virtualizacion = r.necesita_virtualizacion OR size([x IN req WHERE x.k = 'virtualizacion']) > 0,
    r.perfiles_que_imponen = reduce(s = [], x IN req | s + [p IN x.o WHERE NOT p IN s]);

// Una Evaluacion por (requerimiento con perfil determinado × notebook) y su excedente de presupuesto
MATCH (r:Requerimiento) WHERE r.perfil_dominante <> 'indeterminado'
MATCH (n:Notebook), (f:Frame {nombre:'Evaluacion'})
MERGE (ev:Evaluacion {id: r.id + '_' + n.id})
MERGE (r)-[:EVALUA]->(ev)
MERGE (ev)-[:SOBRE]->(n)
MERGE (ev)-[:INSTANCIA_DE]->(f)
SET ev.excedente_presupuesto = CASE WHEN n.precio_usd <= r.presupuesto_usd THEN 0.0
      ELSE round(100.0 * (n.precio_usd - r.presupuesto_usd) / r.presupuesto_usd, 2) END,
    ev.origen_salida = 'modelo', ev.validada_por_experto = false;

// ---------- 10.b SM2 – Excluyente de virtualización (REN-R1 / REN-R13); C1 en el bloque 11 ----------
MATCH (c:Requerimiento)-[:TIENE_PERFIL_DOMINANTE]->(p:Perfil)-[:EXIGE]->(req:Requisito {criterio:'virtualizacion'})
WHERE req.es_excluyente
MATCH (c)-[:EVALUA]->(:Evaluacion)-[:SOBRE]->(n:Notebook)-[:POSEE]->(cpu:CPU)
WITH req, n, cpu,
     CASE cpu.virtualizacion WHEN 'soportada' THEN 'cumple'
                             WHEN 'no soportada' THEN 'no cumple'
                             ELSE 'falta informacion' END AS estado
FOREACH (_ IN CASE WHEN estado = 'no cumple' THEN [1] ELSE [] END |
  MERGE (n)-[:INCUMPLE {excluyente:true, regla:'REN-R1'}]->(req))
FOREACH (_ IN CASE WHEN estado = 'falta informacion' THEN [1] ELSE [] END |
  MERGE (n)-[:NO_VERIFICADO {regla:'REN-R1'}]->(req));

MATCH (n:Notebook)-[:NO_VERIFICADO {regla:'REN-R1'}]->(:Requisito)
MERGE (al:Alerta {id: n.id + '_REN-R13'})
SET al.tipo = 'Información incompleta', al.submodulo_origen = 'SM2', al.regla_origen = 'REN-R13',
    al.mensaje = 'La ficha no informa si la CPU soporta virtualización: completar información'
MERGE (n)-[:GENERA]->(al);

// ---------- 10.c SM2 – Riesgo de obsolescencia de la RAM (C2: FZ-R1..R5; FZ-R6 escenarios; FZ-R7 alerta) ----------
// ρ = RAM / mínimo del perfil; índice a = 0,25 × ranuras libres (máx. 2) + 0,5 × margen de ampliación ÷ RAM recomendada (máx. 1)
MATCH (c:Requerimiento)-[:EVALUA]->(:Evaluacion)-[:SOBRE]->(n:Notebook)-[:POSEE]->(r:RAM)
WITH c, n, r, toFloat(r.ram_gb) / c.req_ram_min AS rho
SET r.suficiencia_rho = round(rho, 3),
    r.indice_ampliabilidad = CASE WHEN r.tipo = 'desconocida' THEN null ELSE round(
        0.25 * (CASE WHEN r.ranuras_libres > 2 THEN 2 ELSE r.ranuras_libres END)
      + 0.5 * (CASE WHEN r.max_gb <= r.ram_gb THEN 0.0
                    WHEN toFloat(r.max_gb - r.ram_gb) / c.req_ram_rec > 1 THEN 1.0
                    ELSE toFloat(r.max_gb - r.ram_gb) / c.req_ram_rec END), 3) END
WITH n, r
MATCH (n)-[:POSEE]->(alm:Almacenamiento)
SET r.nivel_ampliabilidad = CASE WHEN r.tipo = 'desconocida' THEN 'desconocida'          // REN-R16 (ordinal)
        WHEN r.tipo = 'ampliable' AND alm.m2_libre THEN 'alta'
        WHEN r.tipo = 'ampliable' OR alm.m2_libre THEN 'media' ELSE 'baja' END;

// Lecturas: ρ e índice a conocidos → una; ampliabilidad desconocida → a = 0 (peor) y a = 1 (mejor) (FZ-R6)
MATCH (n:Notebook)-[:POSEE]->(r:RAM)
UNWIND CASE WHEN r.indice_ampliabilidad IS NULL THEN [{esc:'peor', a:0.0}, {esc:'mejor', a:1.0}]
            ELSE [{esc:'unico', a:r.indice_ampliabilidad}] END AS es
MERGE (r)-[:TIENE_LECTURA]->(l:Lectura {id: n.id + '_ram_' + es.esc})
SET l.variable = 'riesgo_ram', l.escenario = es.esc,
    l.suficiencia_rho = CASE WHEN r.suficiencia_rho > 3 THEN 3.0 ELSE r.suficiencia_rho END, l.indice_ampliabilidad = es.a
WITH l
MATCH (v:VariableDifusa)-[:TIENE_ETIQUETA]->(e:EtiquetaDifusa)
WHERE v.nombre IN ['suficiencia_ram', 'indice_ampliabilidad']
WITH l, e, CASE e.variable WHEN 'suficiencia_ram' THEN l.suficiencia_rho ELSE l.indice_ampliabilidad END AS x
MERGE (l)-[f:PERTENECE_A]->(e)
SET f.grado = CASE
      WHEN e.tipo = 'hombro_izq' AND x <= e.centro THEN 1.0
      WHEN e.tipo = 'hombro_der' AND x >= e.centro THEN 1.0
      ELSE exp(-((x - e.centro)^2) / (2.0 * e.sigma^2)) END,
    f.valor_crisp = x, f.ts = datetime();

MATCH (n:Notebook)-[:POSEE]->(r:RAM)-[:TIENE_LECTURA]->(l:Lectura {variable:'riesgo_ram'})-[p:PERTENECE_A]->(e:EtiquetaDifusa)
WITH n, r, l, collect({k: e.variable + '.' + e.nombre, mu: p.grado}) AS M
WITH n, r, l,
     [x IN M WHERE x.k = 'suficiencia_ram.insuficiente'][0].mu AS sIN,
     [x IN M WHERE x.k = 'suficiencia_ram.justa'][0].mu AS sJU,
     [x IN M WHERE x.k = 'suficiencia_ram.suficiente'][0].mu AS sSU,
     [x IN M WHERE x.k = 'suficiencia_ram.holgada'][0].mu AS sHO,
     [x IN M WHERE x.k = 'indice_ampliabilidad.poca'][0].mu AS aPO,
     [x IN M WHERE x.k = 'indice_ampliabilidad.media'][0].mu AS aME,
     [x IN M WHERE x.k = 'indice_ampliabilidad.mucha'][0].mu AS aMU
WITH n, r, l, sIN, sJU, sSU, sHO, aPO, CASE WHEN aME > aMU THEN aME ELSE aMU END AS aSi   // OR = MAX
WITH n, r, l,
     (CASE WHEN sIN < aPO THEN sIN ELSE aPO END) AS w1,   // FZ-R1 -> alto
     (CASE WHEN sIN < aSi THEN sIN ELSE aSi END) AS w2,   // FZ-R2 -> medio
     (CASE WHEN sJU < aPO THEN sJU ELSE aPO END) AS w3,   // FZ-R3 -> medio
     (CASE WHEN sJU < aSi THEN sJU ELSE aSi END) AS w4,   // FZ-R4 -> bajo
     (CASE WHEN sSU > sHO THEN sSU ELSE sHO END) AS w5    // FZ-R5 -> bajo
WITH n, r, l, [{r:'FZ-R1', o:'alto', w:w1}, {r:'FZ-R2', o:'medio', w:w2}, {r:'FZ-R3', o:'medio', w:w3},
               {r:'FZ-R4', o:'bajo', w:w4}, {r:'FZ-R5', o:'bajo', w:w5}] AS reglas
CALL {
  WITH r, l, reglas
  UNWIND reglas AS rg
  WITH r, l, rg WHERE rg.w > 0.01
  MATCH (x:Regla {id:rg.r})
  MERGE (r)-[t:ACTIVA {escenario:l.escenario}]->(x) SET t.fuerza = round(rg.w, 3)
}
MATCH (:VariableDifusa {nombre:'riesgo_obsolescencia'})-[:TIENE_ETIQUETA]->(o)
UNWIND range(0, 100) AS i                                // universo 0–100
WITH n, r, l, toFloat(i) AS y, exp(-((i - o.centro)^2) / (2.0 * o.sigma^2)) AS g,
     reduce(w = 0.0, rg IN reglas | CASE WHEN rg.o = o.nombre AND rg.w > w THEN rg.w ELSE w END) AS wo
WITH n, r, l, y, max(CASE WHEN g < wo THEN g ELSE wo END) AS mu
WITH n, r, l, sum(y * mu) / sum(mu) AS y0
MATCH (:VariableDifusa {nombre:'riesgo_obsolescencia'})-[:TIENE_ETIQUETA]->(o2)
WITH n, r, l, y0, o2 ORDER BY exp(-((y0 - o2.centro)^2) / (2.0 * o2.sigma^2)) DESC
WITH n, r, l, y0, collect(o2.nombre)[0] AS etiqueta
SET l.riesgo_valor = round(y0, 2), l.riesgo_etiqueta = etiqueta;

MATCH (n:Notebook)-[:POSEE]->(r:RAM)-[:TIENE_LECTURA]->(l:Lectura {variable:'riesgo_ram'})
WITH n, r, collect(l) AS ls
WITH n, r, ls, [x IN ls WHERE x.escenario = 'unico'] AS u
SET r.riesgo_valor = CASE WHEN size(u) = 1 THEN u[0].riesgo_valor ELSE null END,
    r.riesgo_min = reduce(m = 100.0, x IN ls | CASE WHEN x.riesgo_valor < m THEN x.riesgo_valor ELSE m END),
    r.riesgo_max = reduce(m = 0.0, x IN ls | CASE WHEN x.riesgo_valor > m THEN x.riesgo_valor ELSE m END),
    r.riesgo_etiqueta = CASE WHEN size(u) = 1 THEN u[0].riesgo_etiqueta ELSE null END,
    r.riesgo_peor_etiqueta = CASE WHEN size(u) = 1 THEN u[0].riesgo_etiqueta
                                  ELSE [x IN ls WHERE x.escenario = 'peor'][0].riesgo_etiqueta END,
    r.riesgo_mejor_etiqueta = CASE WHEN size(u) = 1 THEN u[0].riesgo_etiqueta
                                   ELSE [x IN ls WHERE x.escenario = 'mejor'][0].riesgo_etiqueta END
// el riesgo depende del perfil pero se copia a la notebook (limitación 5 del informe)
SET n.riesgo_obsolescencia = r.riesgo_valor, n.riesgo_etiqueta = r.riesgo_etiqueta,
    n.riesgo_rango = CASE WHEN size(u) = 1 THEN null
                          ELSE '[' + r.riesgo_mejor_etiqueta + ' ; ' + r.riesgo_peor_etiqueta + ']' END;

// Alertas de SM2: REN-R10 (ampliabilidad desconocida), FZ-R7 (riesgo alto en el peor caso),
//                 REN-R7 (RAM bajo el mínimo, pero ampliable hasta cumplirlo)
MATCH (c:Requerimiento)-[:EVALUA]->(:Evaluacion)-[:SOBRE]->(n:Notebook)-[:POSEE]->(r:RAM)
WITH n, r, c,
     [x IN [
       CASE WHEN r.tipo = 'desconocida' THEN
         {r:'REN-R10', t:'Ampliabilidad no verificada', m:'La ficha no informa si la RAM es ampliable; el riesgo se informa como rango'} END,
       CASE WHEN r.riesgo_peor_etiqueta = 'alto' THEN
         {r:'FZ-R7', t:'Riesgo de obsolescencia alto', m:'El riesgo de quedarse corta de RAM es alto en el peor caso'} END,
       CASE WHEN r.ram_gb < c.req_ram_min AND r.tipo = 'ampliable' AND r.max_gb >= c.req_ram_min THEN
         {r:'REN-R7', t:'Condicionado a ampliación', m:'La RAM (' + toString(r.ram_gb) + ' GB) no llega al mínimo; cumple solo si se amplía'} END
     ] WHERE x IS NOT NULL] AS alertas
UNWIND alertas AS a
MERGE (al:Alerta {id: n.id + '_' + a.r})
SET al.tipo = a.t, al.submodulo_origen = 'SM2', al.regla_origen = a.r, al.mensaje = a.m
MERGE (n)-[:GENERA]->(al);

// ---------- 10.d SM3 – Gráfica y movilidad ----------
// GPU integrada (GM-R4 crisp) y GM-R14 (dos o más gamas por debajo → excluyente)
MATCH (c:Requerimiento)-[:EVALUA]->(:Evaluacion)-[:SOBRE]->(n:Notebook)-[:POSEE]->(g:GPU)
WITH c, n, g, g.gama - c.req_gama_gpu AS dif
SET n.margen_gama = CASE WHEN dif > 0 THEN 'superior' WHEN dif = 0 THEN 'justa' WHEN dif = -1 THEN 'inferior' ELSE 'excluye' END,
    n.grado_gpu_por_gama = CASE WHEN dif >= 0 THEN 1.0 WHEN dif = -1 THEN 0.5 ELSE 0.0 END
WITH c, n, g, dif
FOREACH (_ IN CASE WHEN g.tipo = 'integrada' THEN [1] ELSE [] END |
  SET n.grado_gpu = n.grado_gpu_por_gama, n.grado_gpu_min = n.grado_gpu_por_gama, n.grado_gpu_max = n.grado_gpu_por_gama)
WITH c, n, dif WHERE dif <= -2
MATCH (c)-[:TIENE_PERFIL_DOMINANTE]->(:Perfil)-[:EXIGE]->(req:Requisito {criterio:'gama_gpu'})
MERGE (n)-[:INCUMPLE {excluyente:true, regla:'GM-R14'}]->(req);

// GPU dedicada: GM-RD4..6 sobre cada lectura de potencia (margen nítido 1/0)
MATCH (n:Notebook)-[:POSEE]->(g:GPU {tipo:'dedicada'})-[:TIENE_LECTURA]->(l:Lectura {variable:'potencia_relativa'})-[p:PERTENECE_A]->(e:EtiquetaDifusa)
WITH n, l, collect({e:e.nombre, mu:p.grado}) AS P
WITH n, l, [x IN P WHERE x.e = 'restringida'][0].mu AS res, [x IN P WHERE x.e = 'moderada'][0].mu AS mo,
     [x IN P WHERE x.e = 'plena'][0].mu AS pl,
     CASE WHEN n.margen_gama = 'superior' THEN 1.0 ELSE 0.0 END AS mS,
     CASE WHEN n.margen_gama = 'justa' THEN 1.0 ELSE 0.0 END AS mJ,
     CASE WHEN n.margen_gama = 'inferior' THEN 1.0 ELSE 0.0 END AS mI
WITH n, l, res, mo, pl, mS, mJ, mI,
     CASE WHEN mo > pl THEN mo ELSE pl END AS mp, CASE WHEN res > mo THEN res ELSE mo END AS rm
WITH n, l,
     [{r:'GM-RD4', o:'pleno',
       w: reduce(m = 0.0, t IN [CASE WHEN mS < mp THEN mS ELSE mp END, CASE WHEN mJ < pl THEN mJ ELSE pl END] | CASE WHEN t > m THEN t ELSE m END)},
      {r:'GM-RD5', o:'parcial',
       w: reduce(m = 0.0, t IN [CASE WHEN mS < res THEN mS ELSE res END, CASE WHEN mJ < mo THEN mJ ELSE mo END,
                                CASE WHEN mI < pl THEN mI ELSE pl END] | CASE WHEN t > m THEN t ELSE m END)},
      {r:'GM-RD6', o:'insuficiente',
       w: reduce(m = 0.0, t IN [CASE WHEN mJ < res THEN mJ ELSE res END, CASE WHEN mI < rm THEN mI ELSE rm END] | CASE WHEN t > m THEN t ELSE m END)}] AS reglas
CALL {
  WITH n, l, reglas
  UNWIND reglas AS rg
  WITH n, l, rg WHERE rg.w > 0.01
  MATCH (x:Regla {id:rg.r})
  MERGE (n)-[t:ACTIVA {escenario:l.escenario}]->(x) SET t.fuerza = round(rg.w, 3)
}
MATCH (:VariableDifusa {nombre:'grado_gpu'})-[:TIENE_ETIQUETA]->(o)
UNWIND range(0, 100) AS i
WITH n, l, i / 100.0 AS y, exp(-((i / 100.0 - o.centro)^2) / (2.0 * o.sigma^2)) AS g,
     reduce(w = 0.0, rg IN reglas | CASE WHEN rg.o = o.nombre AND rg.w > w THEN rg.w ELSE w END) AS wo
WITH n, l, y, max(CASE WHEN g < wo THEN g ELSE wo END) AS mu
WITH n, l, sum(y * mu) AS num, sum(mu) AS den
SET l.grado_gpu = CASE WHEN n.margen_gama = 'excluye' OR den = 0 THEN 0.0 ELSE round(num / den, 3) END;

MATCH (n:Notebook)-[:POSEE]->(g:GPU {tipo:'dedicada'})-[:TIENE_LECTURA]->(l:Lectura {variable:'potencia_relativa'})
WITH n, collect(l.grado_gpu) AS gs
SET n.grado_gpu_min = reduce(m = 1.0, x IN gs | CASE WHEN x < m THEN x ELSE m END),
    n.grado_gpu_max = reduce(m = 0.0, x IN gs | CASE WHEN x > m THEN x ELSE m END),
    n.grado_gpu = CASE WHEN size(gs) = 1 THEN gs[0] ELSE null END;

// Adecuación gráfica = 0,6 × GPU + 0,4 × pantalla (GM-R16: monitor externo → pantalla 1,0)
MATCH (c:Requerimiento)-[:EVALUA]->(:Evaluacion)-[:SOBRE]->(n:Notebook)-[:POSEE]->(pa:Pantalla)
MATCH (wg:Parametro {nombre:'peso_gpu'}), (wp:Parametro {nombre:'peso_pantalla'})
WITH n, wg, wp, CASE WHEN c.usa_monitor_externo THEN 1.0 ELSE pa.grado_pantalla END AS gp
SET n.grado_pantalla = gp,
    n.adecuacion_grafica_min = round(wg.valor * n.grado_gpu_min + wp.valor * gp, 3),
    n.adecuacion_grafica_max = round(wg.valor * n.grado_gpu_max + wp.valor * gp, 3),
    n.adecuacion_grafica = CASE WHEN n.grado_gpu IS NULL THEN null ELSE round(wg.valor * n.grado_gpu + wp.valor * gp, 3) END;

// GM-R8 reformulada: alerta si el TGP baja el grado más de dif_alerta_tgp respecto del de la sola gama
MATCH (n:Notebook)-[:POSEE]->(g:GPU {tipo:'dedicada'}), (d:Parametro {nombre:'dif_alerta_tgp'})
WITH n, g, d WHERE g.tgp_w IS NOT NULL AND n.grado_gpu_por_gama - n.grado_gpu > d.valor
MERGE (al:Alerta {id: n.id + '_GM-R8'})
SET al.tipo = 'Potencia gráfica reducida', al.submodulo_origen = 'SM3', al.regla_origen = 'GM-R8',
    al.mensaje = 'El TGP configurado (' + toString(g.tgp_w) + ' W de ' + toString(g.tgp_max_w) + ' W) reduce el rendimiento de la GPU'
MERGE (n)-[:GENERA]->(al);

// GM-R17: TGP desconocido → alerta (las lecturas ya se crearon en 9.5)
MATCH (n:Notebook)-[:POSEE]->(g:GPU {tipo:'dedicada'}) WHERE g.tgp_w IS NULL
MERGE (al:Alerta {id: n.id + '_GM-R17'})
SET al.tipo = 'Rendimiento gráfico no verificado', al.submodulo_origen = 'SM3', al.regla_origen = 'GM-R17',
    al.mensaje = 'La ficha no informa el TGP; el grado de la GPU se informa como rango'
MERGE (n)-[:GENERA]->(al);

// Movilidad GM-RD1..3 (peso de la notebook × autonomía de la batería)
MATCH (n:Notebook)-[p1:PERTENECE_A]->(e1:EtiquetaDifusa {variable:'peso_kg'})
WITH n, collect({e:e1.nombre, mu:p1.grado}) AS P
MATCH (n)-[:POSEE]->(b:Bateria)-[p2:PERTENECE_A]->(e2:EtiquetaDifusa {variable:'autonomia_h'})
WITH n, P, collect({e:e2.nombre, mu:p2.grado}) AS H
WITH n, [x IN P WHERE x.e = 'liviana'][0].mu AS li, [x IN P WHERE x.e = 'intermedia'][0].mu AS it,
        [x IN P WHERE x.e = 'pesada'][0].mu AS pe, [x IN H WHERE x.e = 'baja'][0].mu AS hb,
        [x IN H WHERE x.e = 'media'][0].mu AS hm, [x IN H WHERE x.e = 'alta'][0].mu AS ha
WITH n, li, it, pe, hb, hm, ha, CASE WHEN hm > ha THEN hm ELSE ha END AS hma
WITH n, [{r:'GM-RD1', o:'alta',  w: CASE WHEN li < ha THEN li ELSE ha END},
         {r:'GM-RD2', o:'media', w: CASE WHEN (CASE WHEN li < hm THEN li ELSE hm END) > (CASE WHEN it < hma THEN it ELSE hma END)
                                         THEN (CASE WHEN li < hm THEN li ELSE hm END) ELSE (CASE WHEN it < hma THEN it ELSE hma END) END},
         {r:'GM-RD3', o:'baja',  w: CASE WHEN pe > hb THEN pe ELSE hb END}] AS reglas
CALL {
  WITH n, reglas
  UNWIND reglas AS rg
  WITH n, rg WHERE rg.w > 0.01
  MATCH (x:Regla {id:rg.r})
  MERGE (n)-[t:ACTIVA {escenario:'unico'}]->(x) SET t.fuerza = round(rg.w, 3)
}
MATCH (:VariableDifusa {nombre:'adecuacion_movilidad'})-[:TIENE_ETIQUETA]->(o)
UNWIND range(0, 100) AS i
WITH n, i / 100.0 AS y, exp(-((i / 100.0 - o.centro)^2) / (2.0 * o.sigma^2)) AS g,
     reduce(w = 0.0, rg IN reglas | CASE WHEN rg.o = o.nombre AND rg.w > w THEN rg.w ELSE w END) AS wo
WITH n, y, max(CASE WHEN g < wo THEN g ELSE wo END) AS mu
WITH n, sum(y * mu) / sum(mu) AS mov
SET n.adecuacion_movilidad = round(mov, 3), n.adecuacion_movilidad_min = round(mov, 3), n.adecuacion_movilidad_max = round(mov, 3);

// GM-R11: prioridad autonomía y pertenencia a 'autonomía baja' sobre el alfa-corte → alerta
MATCH (c:Requerimiento {prioridad:'autonomia'})-[:EVALUA]->(:Evaluacion)-[:SOBRE]->(n:Notebook)-[:POSEE]->(b:Bateria)
MATCH (b)-[p:PERTENECE_A]->(:EtiquetaDifusa {variable:'autonomia_h', nombre:'baja'})
MATCH (al_p:Parametro {nombre:'alfa_alerta_autonomia'})
WITH n, p, al_p WHERE p.grado >= al_p.valor
MERGE (al:Alerta {id: n.id + '_GM-R11'})
SET al.tipo = 'Autonomía insuficiente', al.submodulo_origen = 'SM3', al.regla_origen = 'GM-R11',
    al.mensaje = 'El comprador prioriza la autonomía y la batería pertenece a "baja" con grado ' + toString(round(p.grado, 2))
MERGE (n)-[:GENERA]->(al);

// Autonomía desconocida: la movilidad no se inventa; lecturas con los extremos 0 y 1 (REC-R15)
MATCH (n:Notebook)-[:POSEE]->(b:Bateria {tipo_dato:'desconocida'})
UNWIND [{esc:'peor', x:0.0}, {esc:'mejor', x:1.0}] AS es
MERGE (n)-[:TIENE_LECTURA]->(l:Lectura {id: n.id + '_movilidad_' + es.esc})
SET l.variable = 'adecuacion_movilidad', l.escenario = es.esc, l.valor_crisp = es.x
WITH DISTINCT n
SET n.adecuacion_movilidad = null, n.adecuacion_movilidad_min = 0.0, n.adecuacion_movilidad_max = 1.0
MERGE (al:Alerta {id: n.id + '_GM-R12'})
SET al.tipo = 'Autonomía no informada', al.submodulo_origen = 'SM3', al.regla_origen = 'GM-R12',
    al.mensaje = 'No hay autonomía medida ni declarada; la movilidad se informa como rango [0 ; 1]'
MERGE (n)-[:GENERA]->(al);

// ---------- 10.e SM4 – Integración y recomendación ----------
// REC-R3: excluyente incumplido → descartada; excluyente sin dato → indeterminada
MATCH (c:Requerimiento)-[:EVALUA]->(ev:Evaluacion)-[:SOBRE]->(n:Notebook)
SET ev.estado = CASE WHEN EXISTS { MATCH (n)-[:INCUMPLE {excluyente:true}]->(:Requisito) } THEN 'Descartada (excluyente)'
                     WHEN EXISTS { MATCH (n)-[:NO_VERIFICADO]->(:Requisito {es_excluyente:true}) } THEN 'Indeterminada: completar información'
                     ELSE 'En evaluación' END,
    ev.regla_estado = CASE WHEN EXISTS { MATCH (n)-[:INCUMPLE]->(:Requisito) }
                             OR EXISTS { MATCH (n)-[:NO_VERIFICADO]->(:Requisito) } THEN 'REC-R3' ELSE null END;

// REC-R4, R5, R16: pesos del perfil dominante, +0,2 a la prioridad, mitad de movilidad con monitor externo
MATCH (c:Requerimiento)-[:TIENE_PERFIL_DOMINANTE]->(pf:Perfil), (c)-[:EVALUA]->(ev:Evaluacion)-[:SOBRE]->(n:Notebook)
MATCH (inc:Parametro {nombre:'incremento_prioridad'}), (fm:Parametro {nombre:'factor_movilidad_monitor'})
WITH c, ev, n,
     pf.w_rend + CASE WHEN c.prioridad = 'rendimiento' THEN inc.valor ELSE 0.0 END AS wr,
     pf.w_graf + CASE WHEN c.prioridad = 'grafica' THEN inc.valor ELSE 0.0 END AS wg,
     (pf.w_mov + CASE WHEN c.prioridad IN ['portabilidad', 'autonomia'] THEN inc.valor ELSE 0.0 END)
       * CASE WHEN c.usa_monitor_externo THEN fm.valor ELSE 1.0 END AS wm
WITH c, ev, n, round(wr / (wr + wg + wm), 3) AS nr, round(wg / (wr + wg + wm), 3) AS ng, round(wm / (wr + wg + wm), 3) AS nm
WITH c, ev, n, nr, ng, nm,
     round(nr * n.adecuacion_rendimiento + ng * n.adecuacion_grafica_min + nm * n.adecuacion_movilidad_min, 3) AS gmin,
     round(nr * n.adecuacion_rendimiento + ng * n.adecuacion_grafica_max + nm * n.adecuacion_movilidad_max, 3) AS gmax
SET ev.peso_rend = nr, ev.peso_graf = ng, ev.peso_mov = nm,
    ev.adecuacion_global_min = gmin, ev.adecuacion_global_max = gmax,
    ev.adecuacion_global = CASE WHEN gmin = gmax THEN gmin ELSE null END,
    ev.indice_costo_beneficio = round(gmin / (toFloat(n.precio_usd) / c.presupuesto_usd), 3);

// Lecturas de SM4 (adecuación global y excedente): una, o peor/mejor cuando la adecuación es un rango (REC-R15)
MATCH (ev:Evaluacion {estado:'En evaluación'})
UNWIND CASE WHEN ev.adecuacion_global IS NOT NULL THEN [{esc:'unico', g:ev.adecuacion_global}]
            ELSE [{esc:'peor', g:ev.adecuacion_global_min}, {esc:'mejor', g:ev.adecuacion_global_max}] END AS es
MERGE (ev)-[:TIENE_LECTURA]->(l:Lectura {id: ev.id + '_global_' + es.esc})
SET l.variable = 'recomendacion', l.escenario = es.esc, l.adecuacion_global = es.g,
    l.excedente_presupuesto = CASE WHEN ev.excedente_presupuesto > 30 THEN 30.0 ELSE ev.excedente_presupuesto END
WITH l
MATCH (v:VariableDifusa)-[:TIENE_ETIQUETA]->(e:EtiquetaDifusa)
WHERE v.nombre IN ['adecuacion_global', 'excedente_presupuesto']
WITH l, e, CASE e.variable WHEN 'adecuacion_global' THEN l.adecuacion_global ELSE l.excedente_presupuesto END AS x
MERGE (l)-[f:PERTENECE_A]->(e)
SET f.grado = CASE
      WHEN e.tipo = 'hombro_izq' AND x <= e.centro THEN 1.0
      WHEN e.tipo = 'hombro_der' AND x >= e.centro THEN 1.0
      ELSE exp(-((x - e.centro)^2) / (2.0 * e.sigma^2)) END,
    f.valor_crisp = x, f.ts = datetime();

// REC-RD1..5: grado de recomendación por centroide; etiqueta = mayor pertenencia del valor desborrosificado
MATCH (ev:Evaluacion)-[:TIENE_LECTURA]->(l:Lectura {variable:'recomendacion'})-[p:PERTENECE_A]->(e:EtiquetaDifusa)
WITH ev, l, collect({k: e.variable + '.' + e.nombre, mu: p.grado}) AS M
WITH ev, l,
     [x IN M WHERE x.k = 'adecuacion_global.baja'][0].mu AS gB,
     [x IN M WHERE x.k = 'adecuacion_global.media'][0].mu AS gM,
     [x IN M WHERE x.k = 'adecuacion_global.alta'][0].mu AS gA,
     [x IN M WHERE x.k = 'excedente_presupuesto.dentro'][0].mu AS eD,
     [x IN M WHERE x.k = 'excedente_presupuesto.levemente_excedido'][0].mu AS eL,
     [x IN M WHERE x.k = 'excedente_presupuesto.muy_excedido'][0].mu AS eM
WITH ev, l, [{r:'REC-RD1', o:'recomendar', w: CASE WHEN gA < eD THEN gA ELSE eD END},
             {r:'REC-RD2', o:'considerar', w: CASE WHEN gM < eD THEN gM ELSE eD END},
             {r:'REC-RD3', o:'considerar', w: CASE WHEN gA < eL THEN gA ELSE eL END},
             {r:'REC-RD4', o:'descartar',  w: CASE WHEN gM < eL THEN gM ELSE eL END},
             {r:'REC-RD5', o:'descartar',  w: CASE WHEN gB > eM THEN gB ELSE eM END}] AS reglas
CALL {
  WITH ev, l, reglas
  UNWIND reglas AS rg
  WITH ev, l, rg WHERE rg.w > 0.01
  MATCH (x:Regla {id:rg.r})
  MERGE (ev)-[t:ACTIVA {escenario:l.escenario}]->(x) SET t.fuerza = round(rg.w, 3)
}
MATCH (:VariableDifusa {nombre:'grado_recomendacion'})-[:TIENE_ETIQUETA]->(o)
UNWIND range(0, 100) AS i
WITH ev, l, i / 100.0 AS y, exp(-((i / 100.0 - o.centro)^2) / (2.0 * o.sigma^2)) AS g,
     reduce(w = 0.0, rg IN reglas | CASE WHEN rg.o = o.nombre AND rg.w > w THEN rg.w ELSE w END) AS wo
WITH ev, l, y, max(CASE WHEN g < wo THEN g ELSE wo END) AS mu
WITH ev, l, sum(y * mu) / sum(mu) AS gr
MATCH (:VariableDifusa {nombre:'grado_recomendacion'})-[:TIENE_ETIQUETA]->(o2)
WITH ev, l, gr, o2 ORDER BY exp(-((gr - o2.centro)^2) / (2.0 * o2.sigma^2)) DESC
WITH ev, l, gr, collect(o2.nombre)[0] AS etiqueta
SET l.grado_recomendacion = round(gr, 3), l.etiqueta = etiqueta;

MATCH (ev:Evaluacion)-[:TIENE_LECTURA]->(l:Lectura {variable:'recomendacion'})
WITH ev, collect(l) AS ls
WITH ev, ls,
     reduce(m = 1.0, x IN ls | CASE WHEN x.grado_recomendacion < m THEN x.grado_recomendacion ELSE m END) AS gmin,
     reduce(m = 0.0, x IN ls | CASE WHEN x.grado_recomendacion > m THEN x.grado_recomendacion ELSE m END) AS gmax,
     [x IN ls | x.etiqueta] AS ets
SET ev.grado_recomendacion_min = gmin, ev.grado_recomendacion_max = gmax,
    ev.grado_recomendacion = CASE WHEN size(ls) = 1 THEN gmin ELSE null END,
    ev.etiqueta_recomendacion = CASE WHEN size(ls) = 1 THEN ets[0] ELSE null END,
    ev.fuera_de_presupuesto = ev.excedente_presupuesto > 0,
    ev.estado = CASE
      WHEN all(x IN ets WHERE x = 'descartar') THEN 'Descartada'
      WHEN size(ls) > 1 THEN 'Recomendada condicionada'
      WHEN ets[0] = 'recomendar' THEN 'Recomendada (Alta)'
      ELSE 'Recomendada (Media)' END,
    ev.regla_estado = CASE WHEN size(ls) > 1 THEN 'REC-RD1..5 + REC-R15' ELSE 'REC-RD1..5' END;

// REC-R8: orden por grado (peor caso si es rango); dentro de margen_empate gana la más ampliable (REN-R16).
//         Hasta tres dentro del presupuesto y, aparte, la mejor fuera de presupuesto.
MATCH (me:Parametro {nombre:'margen_empate'})
MATCH (c:Requerimiento)-[:EVALUA]->(ev:Evaluacion)-[:SOBRE]->(n:Notebook)-[:POSEE]->(ram:RAM)
WHERE ev.estado IN ['Recomendada (Alta)', 'Recomendada (Media)', 'Recomendada condicionada']
WITH me, c, collect({ev:ev, g:ev.grado_recomendacion_min, fuera:ev.fuera_de_presupuesto,
     amp: CASE ram.nivel_ampliabilidad WHEN 'alta' THEN 0 WHEN 'media' THEN 1 WHEN 'baja' THEN 2 ELSE 3 END}) AS cs
UNWIND cs AS x
WITH me, c, x, size([o IN cs WHERE o.fuera = x.fuera AND o.ev <> x.ev AND (
        (abs(o.g - x.g) < me.valor AND o.amp < x.amp) OR
        ((abs(o.g - x.g) >= me.valor OR o.amp = x.amp) AND o.g > x.g))]) + 1 AS pos
WITH c, x.ev AS ev, x.fuera AS fuera, pos
SET ev.posicion = pos, ev.en_recomendacion = (NOT fuera AND pos <= 3) OR (fuera AND pos = 1);

MATCH (c:Requerimiento)-[:EVALUA]->(ev:Evaluacion {en_recomendacion:true})-[:SOBRE]->(n:Notebook)
MERGE (c)-[:RECIBE]->(rec:Recomendacion {id: c.id + '_recomendacion'})
FOREACH (_ IN CASE WHEN ev.fuera_de_presupuesto THEN [] ELSE [1] END | MERGE (rec)-[:PROPONE {orden:ev.posicion}]->(n))
FOREACH (_ IN CASE WHEN ev.fuera_de_presupuesto THEN [1] ELSE [] END | MERGE (rec)-[:PROPONE_FUERA_DE_PRESUPUESTO]->(n));

// REC-R10: ninguna propuesta → 'Sin alternativa adecuada' con la restricción no cubierta
MATCH (c:Requerimiento)-[:EVALUA]->(ev:Evaluacion)
WITH c, count(CASE WHEN ev.en_recomendacion AND NOT ev.fuera_de_presupuesto THEN 1 END) AS elegidas,
     count(CASE WHEN ev.estado = 'Descartada (excluyente)' THEN 1 END) AS por_excluyente,
     count(CASE WHEN ev.estado STARTS WITH 'Indeterminada' THEN 1 END) AS indeterminadas,
     count(CASE WHEN ev.estado = 'Descartada' THEN 1 END) AS por_grado
SET c.resultado = CASE WHEN elegidas > 0 THEN 'Con recomendaciones' ELSE 'Sin alternativa adecuada' END,
    c.regla_resultado = CASE WHEN elegidas > 0 THEN 'REC-RD1..5 / REC-R8' ELSE 'REC-R10' END,
    c.restriccion_no_cubierta = CASE WHEN elegidas > 0 THEN null ELSE
        'Descartadas por excluyente: ' + toString(por_excluyente) + '; por grado de recomendación: ' +
        toString(por_grado) + '; indeterminadas: ' + toString(indeterminadas) END
WITH c, elegidas WHERE elegidas = 0
MERGE (al:Alerta {id: c.id + '_REC-R10'})
SET al.tipo = 'Sin alternativa adecuada', al.submodulo_origen = 'SM4', al.regla_origen = 'REC-R10',
    al.mensaje = c.restriccion_no_cubierta
MERGE (c)-[:GENERA]->(al);

// =====================================================================
// 11. CONSULTAS DE INFERENCIA C1–C3 (las del informe, sección d)
// =====================================================================
// C1 – Inferencia crisp: ¿qué notebooks se descartan porque el perfil exige virtualización, y de cuáles no lo sabemos?
MATCH (c:Requerimiento {id:'req_01'})-[:TIENE_PERFIL_DOMINANTE]->(p:Perfil)
      -[:EXIGE]->(req:Requisito {criterio:'virtualizacion'})
WHERE req.es_excluyente
MATCH (n:Notebook)-[:POSEE]->(cpu:CPU)
WITH req, n, cpu,
     CASE cpu.virtualizacion WHEN 'soportada' THEN 'cumple'
                             WHEN 'no soportada' THEN 'no cumple'
                             ELSE 'falta informacion' END AS estado
FOREACH (_ IN CASE WHEN estado = 'no cumple' THEN [1] ELSE [] END |
  MERGE (n)-[:INCUMPLE {excluyente:true, regla:'REN-R1'}]->(req))
FOREACH (_ IN CASE WHEN estado = 'falta informacion' THEN [1] ELSE [] END |
  MERGE (n)-[:NO_VERIFICADO {regla:'REN-R1'}]->(req))
RETURN n.modelo AS notebook, cpu.virtualizacion AS virtualizacion, estado,
       CASE estado WHEN 'no cumple' THEN 'Descartada (REN-R1 + REC-R3)'
                   WHEN 'falta informacion' THEN 'Indeterminada: completar informacion'
                   ELSE 'Sigue en evaluacion' END AS conclusion
ORDER BY estado, notebook;

// C2 – Fuzificación: ¿qué riesgo corre cada notebook de quedarse corta de RAM? (calculado en 10.c)
MATCH (c:Requerimiento {id:'req_01'})-[:EVALUA]->(:Evaluacion)-[:SOBRE]->(n:Notebook)-[:POSEE]->(r:RAM)
OPTIONAL MATCH (r)-[t:ACTIVA]->(rg:Regla)
WITH n, r, t, rg ORDER BY t.fuerza DESC
WITH n, r, collect(rg.id + ' = ' + toString(t.fuerza))[0] AS regla_dominante
RETURN n.modelo AS notebook, r.ram_gb AS ram_gb, r.tipo AS ram, r.suficiencia_rho AS rho,
       r.indice_ampliabilidad AS indice_a, regla_dominante,
       coalesce(toString(r.riesgo_valor), '[' + toString(r.riesgo_min) + ' ; ' + toString(r.riesgo_max) + ']') AS riesgo,
       coalesce(r.riesgo_etiqueta, r.riesgo_peor_etiqueta + ' (peor caso)') AS etiqueta
ORDER BY coalesce(r.riesgo_valor, r.riesgo_max) DESC;

// C3 – Inferencia cruzada: ¿cuál le conviene a este comprador y por qué?
MATCH (p:Comprador)-[:FORMULA]->(c:Requerimiento {id:'req_01'})-[:TIENE_PERFIL_DOMINANTE]->(pf:Perfil)
MATCH (c)-[:EVALUA]->(ev:Evaluacion)-[:SOBRE]->(n:Notebook)-[:POSEE]->(r:RAM)
OPTIONAL MATCH (n)-[:GENERA]->(al:Alerta)
OPTIONAL MATCH (c)-[:RECIBE]->(:Recomendacion)-[pr:PROPONE|PROPONE_FUERA_DE_PRESUPUESTO]->(n)
RETURN p.id AS comprador, pf.codigo AS perfil_SM1, n.modelo AS notebook, n.precio_usd AS precio,
       n.adecuacion_rendimiento AS rend_SM2,
       coalesce(n.riesgo_etiqueta + ' ' + toString(n.riesgo_obsolescencia), n.riesgo_rango) AS riesgo_SM2,
       n.adecuacion_grafica AS graf_SM3, n.adecuacion_movilidad AS mov_SM3,
       coalesce(toString(ev.adecuacion_global),
         '[' + toString(ev.adecuacion_global_min) + ' ; ' + toString(ev.adecuacion_global_max) + ']') AS global_SM4,
       ev.excedente_presupuesto AS excedente,
       coalesce(toString(ev.grado_recomendacion),
         '[' + toString(ev.grado_recomendacion_min) + ' ; ' + toString(ev.grado_recomendacion_max) + ']') AS grado_SM4,
       ev.estado AS estado, ev.indice_costo_beneficio AS costo_beneficio,
       CASE type(pr) WHEN 'PROPONE' THEN 'puesto ' + toString(pr.orden)
                     WHEN 'PROPONE_FUERA_DE_PRESUPUESTO' THEN 'fuera de presupuesto'
                     ELSE '-' END AS en_la_recomendacion,
       collect(DISTINCT al.tipo) AS alertas,
       coalesce(ev.grado_recomendacion, ev.grado_recomendacion_min) AS orden
ORDER BY orden DESC;

// =====================================================================
// 12. CASOS DE PRUEBA CP1–CP10 (esperado frente a obtenido)
// =====================================================================
// CP1 – Notebook_A cumple todo y está dentro del presupuesto → recomendada con el mayor grado
// CP9 – Notebook_M sin autonomía informada → rango y recomendación condicionada
MATCH (:Requerimiento {id:'req_01'})-[:EVALUA]->(ev:Evaluacion)-[:SOBRE]->(n:Notebook)
WHERE n.modelo IN ['Notebook_A', 'Notebook_M']
RETURN CASE n.modelo WHEN 'Notebook_A' THEN 'CP1' ELSE 'CP9' END AS caso, n.modelo AS notebook,
       CASE n.modelo WHEN 'Notebook_A' THEN 'Recomendada con el mayor grado' ELSE 'Rango y recomendación condicionada' END AS esperado,
       coalesce(toString(ev.grado_recomendacion),
         '[' + toString(ev.grado_recomendacion_min) + ' ; ' + toString(ev.grado_recomendacion_max) + ']') + ', ' + ev.estado AS obtenido;

// CP2 – Notebook_E (adecuación 0,810) sin virtualización → descartada
MATCH (:Requerimiento {id:'req_01'})-[:EVALUA]->(ev:Evaluacion)-[:SOBRE]->(n:Notebook {modelo:'Notebook_E'})
RETURN 'CP2' AS caso, 'Descartada' AS esperado, ev.adecuacion_global AS adecuacion,
       EXISTS { MATCH (n)-[:INCUMPLE {regla:'REN-R1'}]->() } AS tiene_incumple, ev.estado AS obtenido;

// CP3 – Notebook_X con 0,841 pero 5 % sobre el presupuesto → alternativa, no primera
MATCH (:Requerimiento {id:'req_01'})-[:EVALUA]->(ev:Evaluacion)-[:SOBRE]->(n:Notebook {modelo:'Notebook_X'})
OPTIONAL MATCH (:Recomendacion)-[pr:PROPONE_FUERA_DE_PRESUPUESTO]->(n)
RETURN 'CP3' AS caso, 'Alternativa fuera de presupuesto' AS esperado, ev.adecuacion_global AS adecuacion,
       ev.excedente_presupuesto AS excedente, ev.grado_recomendacion AS grado, pr IS NOT NULL AS fuera_de_presupuesto;

// CP4 – Notebook_G sin virtualización ni ampliabilidad informadas → no descartar; rango y pedir el dato
MATCH (:Requerimiento {id:'req_01'})-[:EVALUA]->(ev:Evaluacion)-[:SOBRE]->(n:Notebook {modelo:'Notebook_G'})-[:POSEE]->(r:RAM)
OPTIONAL MATCH (n)-[:GENERA]->(al:Alerta)
RETURN 'CP4' AS caso, 'Indeterminada, rango y alertas' AS esperado, ev.estado AS estado,
       '[' + toString(r.riesgo_min) + ' ; ' + toString(r.riesgo_max) + ']' AS riesgo, count(al) AS alertas;

// CP5 – Notebook_K con 8 GB y una ranura libre → riesgo medio, no alto
MATCH (n:Notebook {modelo:'Notebook_K'})-[:POSEE]->(r:RAM)
OPTIONAL MATCH (n)-[:GENERA]->(al:Alerta {regla_origen:'REN-R7'})
RETURN 'CP5' AS caso, 'Riesgo medio' AS esperado, r.riesgo_valor AS riesgo, r.riesgo_etiqueta AS etiqueta,
       al.tipo AS alerta;

// CP6 – Notebook_C con 2,3 kg y 5 h → movilidad baja
MATCH (n:Notebook {modelo:'Notebook_C'})-[:PERTENECE_A]->(:EtiquetaDifusa {variable:'peso_kg'})
MATCH (:VariableDifusa {nombre:'adecuacion_movilidad'})-[:TIENE_ETIQUETA]->(o)
WITH DISTINCT n, o ORDER BY exp(-((n.adecuacion_movilidad - o.centro)^2) / (2.0 * o.sigma^2)) DESC
WITH n, collect(o.nombre)[0] AS etiqueta
RETURN 'CP6' AS caso, 'Movilidad baja' AS esperado, n.adecuacion_movilidad AS movilidad, etiqueta AS obtenido;

// CP7 – Notebook_H y Notebook_B a 0,006 → desempate por ampliabilidad (H antes que B)
MATCH (:Requerimiento {id:'req_01'})-[:EVALUA]->(ev:Evaluacion)-[:SOBRE]->(n:Notebook)-[:POSEE]->(r:RAM)
WHERE n.modelo IN ['Notebook_H', 'Notebook_B']
RETURN 'CP7' AS caso, n.modelo AS notebook, ev.grado_recomendacion AS grado, r.nivel_ampliabilidad AS ampliabilidad,
       ev.posicion AS posicion
ORDER BY ev.posicion;

// CP8 – Parámetros sin validar → 47 etiquetas en 15 variables
MATCH (v:VariableDifusa)-[:TIENE_ETIQUETA]->(e:EtiquetaDifusa)
RETURN 'CP8' AS caso, '47 etiquetas sin validar' AS esperado, count(DISTINCT v) AS variables, count(e) AS etiquetas,
       count(CASE WHEN e.estado_validacion = 'sin validar' THEN 1 END) AS sin_validar;

// CP10 – req_02 "para la facu, 600 USD" sin respuesta a la aclaración → no asumir OFI
MATCH (c:Requerimiento {id:'req_02'})
OPTIONAL MATCH (c)-[:EVALUA]->(ev:Evaluacion)
OPTIONAL MATCH (c)-[:TIENE_PREGUNTA]->(q:Pregunta {estado:'pendiente'})
RETURN 'CP10' AS caso, 'No asumir OFI' AS esperado, c.perfil_dominante AS perfil, count(DISTINCT ev) AS evaluadas,
       collect(DISTINCT q.texto) AS preguntas_pendientes;

// =====================================================================
// 13. CONSULTAS PARA EL LLM (contrato Extraer → Consultar → Explicar)
//     Se dejan con valores de ejemplo (req_01, Notebook_A) para que el script corra completo.
//     En PI4 la aplicación reemplaza esos literales por parámetros (requerimiento_id y modelo).
// =====================================================================
// L1 – Requerimiento formal: cómo se entendió el pedido, o qué preguntar si el perfil es indeterminado
MATCH (c:Requerimiento {id:'req_01'})
OPTIONAL MATCH (c)-[t:PERTENECE]->(pf:Perfil)
OPTIONAL MATCH (c)-[:TIENE_PREGUNTA]->(q:Pregunta {estado:'pendiente'})
RETURN c.presupuesto_usd AS presupuesto, c.prioridad AS prioridad, c.perfil_dominante AS perfil_dominante,
       collect(DISTINCT {perfil:pf.codigo, grado:coalesce(t.grado, t.grado_min), estado:t.estado}) AS perfiles,
       c.intensidad_grafica AS intensidad, c.intensidad_valor AS intensidad_valor,
       collect(DISTINCT q.texto) AS preguntas_pendientes;

// L2 – Explicación de una notebook: estado, grado o rango, cumple / no cumple / falta verificar, alertas y advertencia
MATCH (c:Requerimiento {id:'req_01'})-[:EVALUA]->(ev:Evaluacion)-[:SOBRE]->(n:Notebook {modelo:'Notebook_A'})
OPTIONAL MATCH (c)-[:TIENE_PERFIL_DOMINANTE]->(:Perfil)-[:EXIGE]->(q:Requisito)
WITH c, ev, n, collect(q) AS reqs
OPTIONAL MATCH (n)-[:GENERA]->(al:Alerta)
WITH c, ev, n, reqs, collect({tipo:al.tipo, regla:al.regla_origen, mensaje:al.mensaje}) AS alertas
RETURN ev.estado AS estado,
       coalesce(toString(ev.grado_recomendacion),
         '[' + toString(ev.grado_recomendacion_min) + ' ; ' + toString(ev.grado_recomendacion_max) + ']') AS grado,
       ev.etiqueta_recomendacion AS etiqueta,
       [q IN reqs WHERE NOT EXISTS { MATCH (n)-[:INCUMPLE]->(q) } AND NOT EXISTS { MATCH (n)-[:NO_VERIFICADO]->(q) } | q.criterio] AS cumple,
       [q IN reqs WHERE EXISTS { MATCH (n)-[:INCUMPLE]->(q) } | q.criterio] AS no_cumple,
       [q IN reqs WHERE EXISTS { MATCH (n)-[:NO_VERIFICADO]->(q) } | q.criterio] +
         CASE WHEN n.adecuacion_movilidad IS NULL THEN ['autonomía'] ELSE [] END +
         CASE WHEN n.riesgo_rango IS NOT NULL THEN ['ampliabilidad de la RAM'] ELSE [] END AS falta_verificar,
       alertas,
       'Los parámetros del modelo difuso están sin validar por el técnico: el resultado es una referencia, no una certeza.' AS advertencia;

// L3 – Traza de reglas activadas para una notebook (desde la evaluación, la notebook y su RAM)
MATCH (c:Requerimiento {id:'req_01'})-[:EVALUA]->(ev:Evaluacion)-[:SOBRE]->(n:Notebook {modelo:'Notebook_A'})-[:POSEE]->(ram:RAM)
MATCH (x)-[t:ACTIVA]->(rg:Regla)
WHERE x = ev OR x = n OR x = ram
RETURN rg.id AS regla, rg.antecedente AS antecedente, rg.consecuente AS consecuente,
       labels(x)[0] AS nodo, t.escenario AS escenario, t.fuerza AS fuerza
ORDER BY rg.submodulo, rg.id, escenario;

// L4 – Parámetros: qué está validado
MATCH (v:VariableDifusa)-[:TIENE_ETIQUETA]->(e:EtiquetaDifusa)
RETURN v.nombre AS variable, e.nombre AS etiqueta, e.centro AS centro, e.sigma AS sigma, e.estado_validacion AS estado
ORDER BY v.submodulo, variable, centro;
