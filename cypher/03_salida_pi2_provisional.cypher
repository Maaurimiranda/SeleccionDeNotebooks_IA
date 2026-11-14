// =====================================================================
// cypher/03_salida_pi2_provisional.cypher
// SALIDA_PI2 provisional de OFI, DEV, DIS, VID3D, GAM y DATOS (D-03, PG3-25).
// Generado por: python -m scripts.proponer_salida_pi2 (el metodo esta en ese script).
// Duenio de los datos: Miranda (rendimiento, SM2) y de Coninck (pantalla, SM3).
// Todos los valores son 'sin validar': se reemplazan cuando SM2 y SM3 carguen
// los de sus reglas de PI2. No toca los 9 pares de VIRT ni el supuesto K-OFI,
// asi que req_01 y req_03 no cambian.
// Va en un archivo aparte para que 01 a 40 sigan iguales al canonico de PG2.
// =====================================================================

UNWIND [
  {m:'Notebook_A', p:'OFI', rend:1.00, pant:1.00, op:'igual'},
  {m:'Notebook_B', p:'OFI', rend:1.00, pant:1.00, op:'igual'},
  {m:'Notebook_C', p:'OFI', rend:1.00, pant:1.00, op:'igual'},
  {m:'Notebook_E', p:'OFI', rend:1.00, pant:0.95, op:'igual'},
  {m:'Notebook_G', p:'OFI', rend:0.88, pant:0.80, op:'igual'},
  {m:'Notebook_H', p:'OFI', rend:1.00, pant:0.90, op:'igual'},
  {m:'Notebook_M', p:'OFI', rend:1.00, pant:0.95, op:'igual'},
  {m:'Notebook_X', p:'OFI', rend:1.00, pant:1.00, op:'igual'},
  {m:'Notebook_A', p:'DEV', rend:0.88, pant:1.00, op:'igual'},
  {m:'Notebook_B', p:'DEV', rend:0.73, pant:1.00, op:'igual'},
  {m:'Notebook_C', p:'DEV', rend:0.88, pant:1.00, op:'igual'},
  {m:'Notebook_E', p:'DEV', rend:0.88, pant:0.95, op:'igual'},
  {m:'Notebook_G', p:'DEV', rend:0.31, pant:0.80, op:'igual'},
  {m:'Notebook_H', p:'DEV', rend:0.88, pant:0.90, op:'igual'},
  {m:'Notebook_K', p:'DEV', rend:0.65, pant:0.90, op:'igual'},
  {m:'Notebook_M', p:'DEV', rend:0.88, pant:0.95, op:'igual'},
  {m:'Notebook_X', p:'DEV', rend:0.88, pant:1.00, op:'igual'},
  {m:'Notebook_A', p:'DIS', rend:0.88, pant:0.68, op:'srgb'},
  {m:'Notebook_B', p:'DIS', rend:0.73, pant:0.65, op:'srgb'},
  {m:'Notebook_C', p:'DIS', rend:0.88, pant:1.00, op:'srgb'},
  {m:'Notebook_E', p:'DIS', rend:0.88, pant:0.74, op:'srgb'},
  {m:'Notebook_G', p:'DIS', rend:0.31, pant:0.58, op:'srgb'},
  {m:'Notebook_H', p:'DIS', rend:0.88, pant:0.61, op:'srgb'},
  {m:'Notebook_K', p:'DIS', rend:0.65, pant:0.63, op:'srgb'},
  {m:'Notebook_M', p:'DIS', rend:0.88, pant:0.69, op:'srgb'},
  {m:'Notebook_X', p:'DIS', rend:0.88, pant:1.00, op:'srgb'},
  {m:'Notebook_A', p:'VID3D', rend:0.88, pant:0.68, op:'srgb'},
  {m:'Notebook_B', p:'VID3D', rend:0.59, pant:0.65, op:'srgb'},
  {m:'Notebook_C', p:'VID3D', rend:0.88, pant:1.00, op:'srgb'},
  {m:'Notebook_E', p:'VID3D', rend:0.74, pant:0.74, op:'srgb'},
  {m:'Notebook_G', p:'VID3D', rend:0.17, pant:0.58, op:'srgb'},
  {m:'Notebook_H', p:'VID3D', rend:0.88, pant:0.61, op:'srgb'},
  {m:'Notebook_K', p:'VID3D', rend:0.51, pant:0.63, op:'srgb'},
  {m:'Notebook_M', p:'VID3D', rend:0.88, pant:0.69, op:'srgb'},
  {m:'Notebook_X', p:'VID3D', rend:0.88, pant:1.00, op:'srgb'},
  {m:'Notebook_A', p:'GAM', rend:0.88, pant:0.42, op:'hz'},
  {m:'Notebook_B', p:'GAM', rend:0.88, pant:0.42, op:'hz'},
  {m:'Notebook_C', p:'GAM', rend:0.88, pant:1.00, op:'hz'},
  {m:'Notebook_E', p:'GAM', rend:0.88, pant:0.42, op:'hz'},
  {m:'Notebook_G', p:'GAM', rend:0.46, pant:0.42, op:'hz'},
  {m:'Notebook_H', p:'GAM', rend:0.88, pant:0.42, op:'hz'},
  {m:'Notebook_K', p:'GAM', rend:0.80, pant:0.42, op:'hz'},
  {m:'Notebook_M', p:'GAM', rend:0.88, pant:0.42, op:'hz'},
  {m:'Notebook_X', p:'GAM', rend:0.88, pant:1.00, op:'hz'},
  {m:'Notebook_A', p:'DATOS', rend:0.88, pant:1.00, op:'igual'},
  {m:'Notebook_B', p:'DATOS', rend:0.59, pant:1.00, op:'igual'},
  {m:'Notebook_C', p:'DATOS', rend:0.88, pant:1.00, op:'igual'},
  {m:'Notebook_E', p:'DATOS', rend:0.74, pant:0.95, op:'igual'},
  {m:'Notebook_G', p:'DATOS', rend:0.17, pant:0.80, op:'igual'},
  {m:'Notebook_H', p:'DATOS', rend:0.88, pant:0.90, op:'igual'},
  {m:'Notebook_K', p:'DATOS', rend:0.51, pant:0.90, op:'igual'},
  {m:'Notebook_M', p:'DATOS', rend:0.88, pant:0.95, op:'igual'},
  {m:'Notebook_X', p:'DATOS', rend:0.88, pant:1.00, op:'igual'}
] AS x
MATCH (n:Notebook {modelo:x.m}), (p:Perfil {codigo:x.p})
MERGE (n)-[s:SALIDA_PI2]->(p)
SET s.adecuacion_rendimiento = x.rend, s.grado_pantalla = x.pant,
    s.origen = 'Propuesta provisional del grupo, sin validar por SM2 y SM3',
    s.origen_rendimiento = 'Propuesta provisional SP6 (Contexto SM2 6.3), sin validar por SM2',
    s.origen_pantalla = CASE x.op
      WHEN 'srgb' THEN 'Propuesta provisional: min(1, sRGB/95), sin validar por SM3'
      WHEN 'hz'   THEN 'Propuesta provisional: min(1, Hz/144), sin validar por SM3'
      ELSE 'Propuesta provisional: igual que VIRT (el perfil no exige pantalla), sin validar por SM3' END,
    s.validacion = 'sin validar';
