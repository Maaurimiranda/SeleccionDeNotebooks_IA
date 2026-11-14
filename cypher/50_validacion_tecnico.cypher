// =====================================================================
// 50 · VALIDACION CON EL TECNICO (devolucion de PG2, correccion 2)
// ---------------------------------------------------------------------
// Respuestas del tecnico recibidas el 14/11/2026 a las 16 (:ConsultaExperto)
// de 01_conocimiento.cypher (5.f). Decision del grupo (14/11/2026):
//   - las 7 respuestas que confirman el modelo pasan sus etiquetas y su
//     parametro centros_y_sigmas_<variable> a 'validado por el tecnico';
//   - las 6 que proponen otros centros o sigmas y las 3 que proponen
//     cambiar una regla quedan registradas (ajuste_propuesto) y NO se
//     aplican: sus etiquetas siguen 'sin validar'.
// Ningun valor numerico cambia: los resultados de CP1 a CP11 son los mismos.
// Detalle: docs/pruebas/validacion_tecnico.md.
// Va en un archivo aparte para que 01 a 40 sigan iguales al canonico de PG2.
// =====================================================================

// Las 16 respuestas, textuales (sin tildes, como el resto del grafo)
UNWIND [
  {ce:'CE-dedicacion_h', r:'Ocasional lo considero 5 horas, para un uso corto en cada dia de la semana, y pasa a frecuente entre 10 y 15 horas. Y para que sea la actividad principal a partir de 30hs ya que se puede deber a su trabajo, o su hobby.', l:'ajuste propuesto', a:'ocasional c=5 (hoy 4); principal c=30 (hoy 28); frecuente sin cambio'},
  {ce:'CE-exigencia_grafica', r:'Exigencia baja: Counter strike 1.6, terraria, o juegos indie de que suelen tener un bajo consumo por ser la mayoria en 2d. Se asemejan a la exigencia de Stardew Valley Exigencia media: League of legends, valorant, counter strike 2, minecraft, etc.. Se asemejan a la exigencia de fortnite Exigencia alta: Elder Ring, GTA6, Clair Obscure: Expedicion 33. Coinciden con la exigencia de Cyberpunk 2077', l:'confirma', a:null},
  {ce:'CE-intensidad_grafica', r:'En este caso no importa la frecuencia con la que se juega, sino la exigencia del renderizado de graficos y texturas de los mismos juegos. Con una gpu media se puede llegar a jugar juegos de alta exigencia con calidad de graficos bajos, y con la integrada te quedas mas corto', l:'cambio de regla propuesto', a:'que la frecuencia de juego no reduzca la GPU minima; el grupo decidio no aplicarlo en PG3'},
  {ce:'CE-peso_perfil', r:'Pesa pero con ciertos matices, como por ejemplo la tarea que emplea. 12hs de render pesan mucho mas que 28hs de oficin. Tambien si la pc se queda un poco corta, la persona que lo usa 28hs lo va a "sufrir" mucho mas que alguien que la usa ocasionalmente.', l:'confirma', a:null},
  {ce:'CE-indice_ampliabilidad', r:'Una ranura para una ram de 32GB es una ampliabilidad grande. Pero un equipo de 2 no solo es grande (siempre considerando que si hay otro slot de ram ocupada sean compatibles), sino que permite poner 2 Ram para que trabajen en Dual-Channel con la misma frecuencia.', l:'ajuste propuesto', a:'una ranura con margen hasta 32 GB (hoy a=0,625, media) deberia ser mucha: bajar el centro de mucha o subir el peso del margen'},
  {ce:'CE-riesgo_obsolescencia', r:'El riesgo de una notebook con componentes soldados es la obsolescencia y el quedarse corto ya que el sistema operativo, los programas, los juegos, etc. Cada vez consumen mas. Con 16GB de barias tener suficiente para un uso normal. Con 8GB es probable que sea tu cuello de botella, pero es preferible arrancar con eso (y tener mejor procesador, gpu, que no se puede cambiar en una notebook) y luego agregar mas en un futuro.', l:'confirma', a:null},
  {ce:'CE-suficiencia_ram', r:'La ram con el minimo del perfil lo considero justo, ya que muchas veces se terminan instalando programas que se ejecutan en segundo plano, y cada vez se ocupa mas ram. Con el doble de ram que la recomendada te sobra bastante.', l:'ajuste propuesto', a:'justa en el minimo confirmado; holgada recien con el doble de la RAM recomendada (hoy 2 veces el minimo)'},
  {ce:'CE-FZ-R2-R3', r:'No corren el mismo riesgo, ya que la que esta soldada justa, si se queda corta necesitas pensar en un cambio de notebook. La que esta por debajo del minimo pero es ampliable se arregla con un modulo nuevo (Dudo que salga 30 dolares revisen esto). Me quedo con la alternativa: FZ-R3 pasa a alto y FZ-R2 queda en medio. Si la ampliable tiene dos ranuras, conviene poner dos modulos para usar dual channel.', l:'cambio de regla propuesto', a:'FZ-R3 -> alto y FZ-R2 medio; revisar P_COSTO_MODULO_RAM_USD (el tecnico duda de 30 USD); el grupo decidio no aplicarlo en PG3'},
  {ce:'CE-adecuacion_movilidad', r:'Yo considero 5hs de bateria como movilidad media (cerca de baja). Rinde para una jornada de estudio pero no para una jornada entera de trabajo sin cargador.', l:'confirma', a:null},
  {ce:'CE-autonomia_h', r:'Poca 3hs aprox, aceptable 5hs a 7hs y mucha a partir de 12hs', l:'ajuste propuesto', a:'media c=6 (hoy 6,5); alta c=12 (hoy 10)'},
  {ce:'CE-grado_gpu', r:'Depende del perfil, para juegos, diseno y video serviria a medias, bajas la calidad del programa que utilices. Pero para alguien que utiliza modelos de lenguaje con una GPU un nivel por debajo, que suele tener menos VRAM, directamente no te sirve.', l:'cambio de regla propuesto', a:'una GPU un nivel abajo: 0,5 en GAM, DIS y VID3D, 0 en DATOS; el grupo decidio no aplicarlo en PG3'},
  {ce:'CE-peso_kg', r:'Liviana diria menos de 1,5KG, intermedia aproximadamente 2KG y pesada mas de 2,5KG', l:'ajuste propuesto', a:'liviana c=1,4 (hoy 1,2); intermedia c=2,0 (hoy 1,8); pesada sin cambio'},
  {ce:'CE-potencia_relativa', r:'Pasar de 115W a 60W produce una bajada de rendimiento muy alta, y diria que se queda en el medio entre gama media y de entrada.', l:'confirma', a:null},
  {ce:'CE-adecuacion_global', r:'Si, a partir de 0,8 en adelante sin dudarlo, teniendo en cuenta, como mucho, algun detalle menor. Entre 0,6 y 0,8 sirve pero el asesor deberia considerar y mencionar las limitaciones. Por debajo de 0,6 no la ofreceria.', l:'confirma', a:null},
  {ce:'CE-excedente_presupuesto', r:'Consideraria un 5% como dentro del presupuesto, mas del 10% levemente excedido. Mas del 15% unicamente si el cliente lo pide, y ya a partir del 25% se descarta.', l:'ajuste propuesto', a:'dentro hasta 5 % (sigma 5, hoy 3); muy excedido c=20 (hoy 25); descartar desde 25 %'},
  {ce:'CE-grado_recomendacion', r:'Si, considero necesario mostrar las notebooks para considerar, separada de las recomendadas y diciendo cuanto se pasa del presupuesto (en precio y porcentaje). Si cumple todo lo que pide el cliente, se muestra (siempre que no exceda el 25% del presupuesto acordado).', l:'confirma', a:null}
] AS x
MATCH (ce:ConsultaExperto {id:x.ce})
SET ce.estado = 'respondida', ce.respuesta = x.r, ce.fecha_respuesta = '2026-11-14',
    ce.lectura = x.l, ce.ajuste_propuesto = x.a;

// Las 7 variables que el tecnico confirma: etiquetas y parametro validados
UNWIND ['exigencia_grafica', 'peso_perfil', 'riesgo_obsolescencia', 'adecuacion_movilidad', 'potencia_relativa', 'adecuacion_global', 'grado_recomendacion'] AS v
MATCH (vd:VariableDifusa {nombre:v})-[:TIENE_ETIQUETA]->(e:EtiquetaDifusa)
MATCH (p:Parametro {nombre:'centros_y_sigmas_' + v})
SET e.estado_validacion = 'validado por el tecnico', e.validado_con = 'CE-' + v,
    p.estado_validacion = 'validado por el tecnico', p.validado_con = 'CE-' + v;
