# Validación con el técnico (devolución de PG2, corrección 2)

Respuestas del técnico a las 16 consultas del grafo (`(:ConsultaExperto)`, `cypher/01_conocimiento.cypher` §5.f), recibidas el **14/11/2026**, y qué se hizo con cada una. Se cargan en [`cypher/50_validacion_tecnico.cypher`](../../cypher/50_validacion_tecnico.cypher). Registro: C-46 en [`docs/CORRECCIONES.md`](../CORRECCIONES.md).

## Decisión del grupo

- **Las 7 respuestas que confirman el modelo** validan sus variables: las 21 etiquetas y los 7 `centros_y_sigmas_*` pasan a `'validado por el tecnico'`.
- **Las 6 que proponen otros centros y las 3 que proponen cambiar una regla** quedan registradas en el grafo (`ConsultaExperto.ajuste_propuesto`) y **no se aplican**. Sus etiquetas siguen `'sin validar'`.
- **Por qué no se aplican:** se probaron todos los ajustes en una copia (14/11) y movían los resultados del informe. La regresión daba 5 de 11: la A pasaba de `Recomendada (Alta)` 0,785 a `(Media)` 0,734 (por la autonomía «mucha» desde 12 h), el podio cambiaba de A, H, B a A, B, H (por el peso), la X subía de 0,534 a 0,602 (por el presupuesto) y el riesgo con RAM de sobra bajaba de 23,02 a 18,23. Aplicarlos es el primer paso pendiente (informe, sección 9).

## Resultado en el grafo

| | Antes | Después |
| --- | --- | --- |
| `ConsultaExperto` | 16 `pendiente` | 16 `respondida` (7 confirma, 6 ajuste propuesto, 3 cambio de regla propuesto) |
| Etiquetas difusas sin validar (CP8) | 47 en 15 variables | 26 en 8 variables |
| `Parametro` sin validar | 30 | 23 |
| Aviso de SM4 (Q8) | «Los 9 parametros de recomendacion…» | «3 de los 9 parametros de recomendacion…» (excedente de presupuesto) |
| Estados, grados, rankings, CP1 a CP7, CP9 a CP11 | — | **sin cambios** |

Siguen sin validar, además: las 50 reglas vigentes, los 15 parámetros fijos (umbrales, pesos y costos), el léxico de frecuencia, las gamas de GPU y los mínimos de RAM por perfil. El técnico no completó esas tablas: no se marcan validadas.

## Preguntas, respuestas y lectura

| N.º | SM | Variable o regla | Hoy en el modelo | Lectura | Propuesta (no aplicada) |
| ---: | --- | --- | --- | --- | --- |
| 1 | SM1 | `dedicacion_h` | ocasional 4 h · frecuente 12 h · principal 28 h | Ajuste propuesto | ocasional c=5; principal c=30 |
| 2 | SM1 | `exigencia_grafica` | Stardew Valley, Fortnite y Cyberpunk 2077 | **Confirma** | — |
| 3 | SM1 | `intensidad_grafica` | la frecuencia baja la exigencia | Cambio de regla propuesto | que la frecuencia no reduzca la GPU mínima |
| 4 | SM1 | `peso_perfil` | 28 h pesa más que 12 h | **Confirma** (con matiz) | — |
| 5 | SM2 | `indice_ampliabilidad` | K (1 ranura, hasta 32 GB): a = 0,625, «media» | Ajuste propuesto | que ese caso sea «mucha» |
| 6 | SM2 | `riesgo_obsolescencia` | B 50,00 y K 49,55, las dos medio | **Confirma** | — |
| 7 | SM2 | `suficiencia_ram` | mínimo = justa; holgada = 2 × mínimo | Ajuste propuesto | holgada recién con el doble de la recomendada |
| 8 | SM2 | `FZ-R2 y FZ-R3` | las dos riesgo medio | Cambio de regla propuesto | FZ-R3 a riesgo alto (B 80,84); revisar el costo de 30 USD |
| 9 | SM3 | `adecuacion_movilidad` | media tirando a baja | **Confirma** | — |
| 10 | SM3 | `autonomia_h` | 3 · 6,5 · 10 h | Ajuste propuesto | media c=6; alta c=12 |
| 11 | SM3 | `grado_gpu` | 0,5 para todos los perfiles | Cambio de regla propuesto | 0,5 en GAM, DIS y VID3D; 0 en DATOS |
| 12 | SM3 | `peso_kg` | 1,2 · 1,8 · 2,5 kg | Ajuste propuesto | liviana c=1,4; intermedia c=2,0 |
| 13 | SM3 | `potencia_relativa` | X (0,52) entre restringida y moderada | **Confirma** | — |
| 14 | SM4 | `adecuacion_global` | cortes en 0,6 y 0,8 | **Confirma** | — |
| 15 | SM4 | `excedente_presupuesto` | dentro c=0 (σ 3); levemente 10 %; muy 25 % | Ajuste propuesto | dentro hasta 5 % (σ 5); muy c=20; descartar desde 25 % |
| 16 | SM4 | `grado_recomendacion` | aparece aparte, «para considerar» | **Confirma** | — |

## Respuestas textuales

**1. ¿Desde cuántas horas por semana una actividad deja de ser ocasional y pasa a frecuente? ¿Y desde cuántas es la principal?**  
Ocasional lo considero 5 horas, para un uso corto en cada dia de la semana, y pasa a frecuente entre 10 y 15 horas. Y para que sea la actividad principal a partir de 30hs ya que se puede deber a su trabajo, o su hobby.

**2. ¿Qué juegos pondría como ejemplo de exigencia baja, media y alta? ¿Coinciden con Stardew Valley, Fortnite y Cyberpunk 2077?**  
Exigencia baja: Counter strike 1.6, terraria, o juegos indie de que suelen tener un bajo consumo por ser la mayoria en 2d. Se asemejan a la exigencia de Stardew Valley  
Exigencia media: League of legends, valorant, counter strike 2, minecraft, etc.. Se asemejan a la exigencia de fortnite  
Exigencia alta: Elder Ring, GTA6, Clair Obscure: Expedición 33. Coinciden con la exigencia de Cyberpunk 2077

**3. Un juego exigente que se juega de vez en cuando, ¿pide GPU media o alcanza con una integrada moderna?**  
En este caso no importa la frecuencia con la que se juega, sino la exigencia del renderizado de gráficos y texturas de los mismos juegos. Con una gpu media se puede llegar a jugar juegos de alta exigencia con calidad de gráficos bajos, y con la integrada te quedas más corto

**4. Una actividad de 12 h por semana, ¿pesa lo mismo que una de 28 h para decidir el perfil?**  
Pesa pero con ciertos matices, como por ejemplo la tarea que emplea. 12hs de render pesan mucho mas que 28hs de oficin. Tambien si la pc se queda un poco corta, la persona que lo usa 28hs lo va a “sufrir” mucho mas que alguien que la usa ocasionalmente.

**5. Una ranura libre con margen hasta 32 GB, ¿es ampliabilidad media o mucha? ¿Y con dos ranuras libres?**  
Una ranura para una ram de 32GB es una ampliabilidad grande. Pero un equipo de 2 no solo es grande (siempre considerando que si hay otro slot de ram ocupada sean compatibles), sino que permite poner 2 Ram para que trabajen en Dual-Channel con la misma frecuencia.

**6. ¿Qué riesgo de quedarse corta tiene una notebook con 16 GB soldados para virtualizar, y una con 8 GB ampliables?**  
El riesgo de una notebook con componentes soldados es la obsolescencia y el ‘quedarse corto’ ya que el sistema operativo, los programas, los juegos, etc. Cada vez consumen más. Con 16GB de barias tener suficiente para un uso normal. Con 8GB es probable que sea tu cuello de botella, pero es preferible arrancar con eso (y tener mejor procesador, gpu, que no se puede cambiar en una notebook) y luego agregar más en un futuro.

**7. Con la RAM justo en el mínimo del perfil, ¿es justa o suficiente? ¿Desde cuánta sobra?**  
La ram con el minimo del perfil lo considero justo, ya que muchas veces se terminan instalando programas que se ejecutan en segundo plano, y cada vez se ocupa mas ram. Con el doble de ram que la recomendada te sobra bastante.

**8. RAM justa y soldada contra RAM insuficiente pero ampliable con unos 30 USD: ¿corren el mismo riesgo?**  
No corren el mismo riesgo, ya que la que esta soldada justa, si se queda corta necesitas pensar en un cambio de notebook. La que está por debajo del mínimo pero es ampliable se arregla con un modulo nuevo (Dudo que salga 30 dolares revisen esto). Me quedo con la alternativa: FZ-R3 pasa a alto y FZ-R2 queda en medio. Si la ampliable tiene dos ranuras, conviene poner dos módulos para usar dual channel.

**9. Una notebook liviana con 5 h de batería, ¿movilidad media o baja?**  
Yo considero 5hs de bateria como movilidad media (cerca de baja). Rinde para una jornada de estudio pero no para una jornada entera de trabajo sin cargador.

**10. ¿Cuántas horas reales de batería son poca, aceptable y mucha?**  
Poca 3hs aprox, aceptable 5hs a 7hs y mucha a partir de 12hs

**11. Una GPU un nivel por debajo de la que pide el perfil, ¿sirve a medias o no sirve?**  
Depende del perfil, para juegos, diseño y video serviria a medias, bajas la calidad del programa que utilices. Pero para alguien que utiliza modelos de lenguaje con una GPU un nivel por debajo, que suele tener menos VRAM, directamente no te sirve.

**12. ¿Desde qué peso una notebook deja de ser cómoda para llevarla todos los días?**  
Liviana diria menos de 1,5KG, intermedia aproximadamente 2KG y pesada mas de 2,5KG

**13. Una RTX 4060 a 60 W de 115 W, ¿rinde como gama media, de entrada o en el medio?**  
Pasar de 115W a 60W produce una bajada de rendimiento muy alta, y diria que se queda en el medio entre gama media y de entrada.

**14. ¿Con qué puntaje global recomendaría sin dudar, y con cuál la dejaría para considerar?**  
Si, a partir de 0,8 en adelante sin dudarlo, teniendo en cuenta, como mucho, algún detalle menor. Entre 0,6 y 0,8 sirve pero el asesor deberia considerar y mencionar las limitaciones. Por debajo de 0,6 no la ofreceria.

**15. ¿Cuánto por encima del presupuesto acepta ofrecer un equipo?**  
Consideraría un 5% como dentro del presupuesto, mas del 10% levemente excedido. Mas del 15% unicamente si el cliente lo pide, y ya a partir del 25% se descarta.

**16. ¿Prefiere ver como «para considerar» una notebook que cumple todo pero se pasa un poco del presupuesto, o que no aparezca?**  
Sí, considero necesario mostrar las notebooks para considerar, separada de las recomendadas y diciendo cuanto se pasa del presupuesto (en precio y porcentaje). Si cumple todo lo que pide el cliente, se muestra (siempre que no exceda el 25% del presupuesto acordado).

