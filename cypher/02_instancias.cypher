// =====================================================================
// cypher/02_instancias.cypher
// Bloques del canonico: 7 compradores y pedidos · 8 catalogo y SALIDA_PI2
// Duenio: Miranda
// Origen: docs/cypher/Grupo_2_PG2_U1_corregido.cypher, cortado sin cambiar el contenido (PG3-02).
// =====================================================================

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
