// =====================================================================
// cypher/00_esquema.cypher
// Bloques del canonico: 0 limpieza · 1 indices · 2 frames
// Duenio: Miranda
// Origen: docs/cypher/Grupo_2_PG2_U1_corregido.cypher, cortado sin cambiar el contenido (PG3-02).
// =====================================================================

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
// Correccion para PG3 (revision final del SM4):
//   - REC-R9: con prioridad declarada 'precio', la recomendacion final se
//     ordena primero por indice costo-beneficio (bloque 10.f), como dice el
//     enunciado de la regla. Antes el orden no miraba la prioridad. Los
//     pedidos req_01, req_02 y req_03 no tienen esa prioridad y no cambian.
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
