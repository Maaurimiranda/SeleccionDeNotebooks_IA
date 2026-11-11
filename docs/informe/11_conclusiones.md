## 11.2 Conclusiones del grupo

**Lo que logramos.** Construimos un asistente que no es una suma de scripts: un prompt maestro que enruta cada consulta, una única entrada (API y consola), cuatro submódulos que cumplen el mismo contrato y comparten un grafo en Neo4j, y cinco casos integrales que cruzan al menos dos submódulos distintos. La idea central de la materia se sostiene en el código: el LLM interpreta y explica, y el conocimiento verificable decide.

**Contra los objetivos de la consigna (§1).**

| Objetivo | Estado | Qué lo respalda |
| --- | --- | --- |
| Interpretar consultas | Cumplido | Router más validación: 28 de 31 intenciones (90 %) y 30 de 31 resultados finales (97 %); las consultas fuera de dominio y los pedidos inexistentes se controlan sin tocar el grafo |
| Recuperar conocimiento | Cumplido | 11 intenciones con Cypher fijo sobre un grafo de 343 nodos y 683 relaciones; CP1 a CP11 en 11 de 11 |
| Realizar inferencias | **Parcial** | Las reglas crisp y las difusas Mamdani corren al cargar el grafo y el asistente consulta lo que dejaron calculado. No infiere en vivo para un pedido nuevo (PG3-21 no se hizo) |
| Gestionar la incertidumbre | Cumplido | Rangos, `desconocida` e indeterminado llegan intactos a la respuesta; los parámetros sin validar se advierten en cada una |
| Explicar de manera comprensible | Cumplido, con reparos | Las 5 explicaciones pasaron el verificador, pero con redacción pobre y un error de atribución (E2E-2). La traza, en cambio, es completa |

**Lo que aprendimos.**

1. **Aprobar por la evidencia y no por el texto fue una buena decisión, pero insuficiente.** Probar contra lo que devuelve el grafo nos dio pruebas estables aunque el LLM redacte distinto cada vez. A la vez, un E2E aprobado convivió con una explicación equivocada. El verificador controla que una cifra exista, no que tenga el nombre correcto.
2. **Lo que importa se verifica en código, no en el prompt.** Un modelo de 3 mil millones de parámetros tiende a ignorar las instrucciones secundarias; lo que lo contuvo fue el plan validado, las consultas fijas y el verificador.
3. **«Falta información» no es «no cumple».** La lección de dominio más fuerte: la G queda indeterminada y la M, condicionada, en lugar de descartadas o completadas con un dato inventado. Mostrar un rango en vez de un número falso es más incómodo y más honesto.
4. **Un contrato fijo permitió trabajar en paralelo.** La misma interfaz, fixtures con filas reales y un único punto de entrada dejaron que cuatro personas avanzaran a la vez. Antes de integrar hubo que resolver 13 decisiones (D-01 a D-13) por inconsistencias entre los contextos de cada submódulo: reconciliar eso fue trabajo, no un trámite.
5. **Hay que medir con consultas que el modelo no vio.** Nuestra primera medición del router (25 consultas, 96 %) fue más optimista que la final (31 consultas, 90 %), y después advertimos que cada ejemplo del prompt tiene su gemela, exacta o muy cercana, en el conjunto de prueba. Convendría haber separado desde el principio las consultas de ejemplo de las de evaluación.
6. **Una sola fuente para las cifras.** Al armar este informe encontramos cifras desfasadas entre documentos (la cantidad de consultas del router, las filas contra las reglas de la traza). Las unificamos contra las corridas de `docs/pruebas/`, que son la referencia.
7. **El modelo chico es una decisión de compromiso.** `qwen2.5:3b` corre en la notebook de cada integrante, sin costo, y alcanza para enrutar. No alcanza para redactar con soltura. Un modelo más grande mejoraría el texto, pero a un integrante se le colgó la computadora.

**Lo que no logramos, y lo que sigue.** Dejamos sin hacer el pedido nuevo con inferencia en vivo y todo el nivel 2 (PG3-21 a 27), no medimos los tiempos de punta a punta en otra máquina y los parámetros siguen sin validar por el técnico. Esto último es lo que más pesa: hasta que no se validen, el sistema es una demostración funcional de la arquitectura y no una herramienta que alguien deba usar para decidir una compra. Si siguiéramos, el orden sería: validar los parámetros con el técnico, habilitar el pedido nuevo con inferencia en vivo, reforzar el verificador para que ate cada cifra a su concepto y recién después ampliar el catálogo y las reglas. El detalle está en la sección 9.
