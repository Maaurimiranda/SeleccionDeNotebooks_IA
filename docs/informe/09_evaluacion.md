# 9. Evaluación del sistema

Esta sección analiza con espíritu crítico lo que el asistente hace bien, lo que no y lo que no probamos (consigna §3.6). Todas las cifras salen de las corridas del 11/11/2026 sobre Neo4j 5.26 y `qwen2.5:3b`, registradas en `docs/pruebas/` y resumidas en la sección 8. Donde algo no se midió, se dice.

## 9.1 Fortalezas

| Fortaleza | Evidencia |
| --- | --- |
| **Lo que se afirma sale del grafo, no del LLM.** Cada E2E aprueba por lo que devuelve Neo4j (puestos, estados, rangos, alertas), no por el texto | 7 de 7 E2E aprueban: 5 integrales y 2 controles |
| **Cruza submódulos de verdad.** Los casos integrales piden al menos dos submódulos distintos sin contar SM1, que el orquestador agrega siempre | E2E-1, 2, 5, 9 y 10: SM2 + SM4, SM2 + SM4, SM2 + SM4, GRUPO + SM2 y SM3 + SM4 |
| **La incertidumbre no se tapa.** Un dato faltante se informa como rango o como «falta verificar» | M: grado [0,504 ; 0,826] y `Recomendada condicionada por falta de informacion`. G: riesgo de RAM [49,58 ; 81,46] e `Indeterminada: completar informacion`. `req_02`: perfil indeterminado, sin asumir oficina (E2E-3) |
| **Un requisito excluyente no se compensa con puntaje.** | E queda `Descartada (excluyente incumplido)` aunque puntúa ≈ 0,81, casi igual que B (0,813) y H (0,811) |
| **El router se equivoca sin hacer daño.** La validación en Python descarta intenciones, modelos y pedidos inválidos antes de tocar el grafo, y nunca asume `req_01` | Una consulta fuera de dominio termina en un mensaje fijo, sin consultar el grafo (E2E-8: 0,69 s). Los modelos inexistentes terminan en una aclaración |
| **Cada respuesta es auditable.** La traza guarda plan, Cypher con parámetros, filas, evidencia, intentos y tiempos | Sección 10: reconstrucción completa del E2E-9 |
| **Es reproducible.** El grafo dividido por dueño equivale al canónico, y la regresión corre sola | 343 nodos y 683 relaciones iguales (57 de 57 filas); CP1 a CP11 en 11 de 11; 171 tests (2 salteados, los que piden Ollama) |
| **Corre local y sin costo de API**, en una notebook común | `qwen2.5:3b` ocupa unos 4 GB de RAM |

## 9.2 Limitaciones

**Los parámetros no están validados por el técnico.** Las 47 etiquetas difusas (centros y sigmas), los parámetros del grafo y los mínimos de RAM por perfil están marcados `'sin validar'`. Las consultas al técnico que aparecen en la traza del E2E-9 figuran como `pendiente`. Por eso toda respuesta lleva la advertencia de que los grados y riesgos son una referencia, no una certeza. Los resultados no se pueden presentar como una decisión de compra.

**El asistente lee, no infiere en vivo.** Las reglas y el difuso corren una vez, al cargar el grafo, y el asistente consulta lo que quedó calculado para tres pedidos (`req_01`, `req_02` y `req_03`) y nueve notebooks. Un comprador nuevo no se puede registrar: `SM1.registrar_pedido` y `SM1.aclarar_pedido` son de nivel 2 y el router las rechaza. Es la limitación más importante frente al objetivo de «realizar inferencias» de la consigna (§1), y el motivo por el que el sistema es una demostración y no una herramienta de uso diario.

**El modelo chico limita la redacción.** `qwen2.5:3b` planifica bien y redacta regular. Con poco contexto, la evidencia se compacta antes de dársela (listas cortadas a 12 filas): en el E2E-9 el LLM vio 12 de las 18 reglas. Probar `qwen2.5:7b` mejora la redacción, pero a un integrante se le colgó la computadora, y no se adoptó.

**Catálogo y pedidos chicos.** Son 9 modelos con precios al 01/10/2026 y 3 pedidos. Los precios envejecen y no hay consulta en tiempo real. Una pregunta abierta desde PG1 sigue sin respuesta: si los pesos y umbrales dan rankings razonables sobre un catálogo más grande (el catálogo real prevé 30 modelos).

**Sesión mínima.** El asistente recuerda solo el pedido de la sesión, no la conversación: cada pregunta se resuelve sola. El plan admite hasta tres consultas.

**Tiempos de punta a punta medidos en una sola máquina.** En la máquina de los E2E, las respuestas que redacta el LLM tardaron entre 4,3 y 7,1 s; las de control, 0,7 y 1,3 s. Entre el 93 % y el 99 % de ese tiempo lo consumen las dos llamadas al LLM, y las consultas a Neo4j tardaron entre 0,04 y 0,3 s. El primer E2E es el más lento (6,1 s de plan), algo compatible con la carga del modelo, pero no lo medimos por separado. En la notebook de Ramiro de Coninck (10/11), el plan **solo** tardó entre 10 y 50 s, así que en otro equipo una consulta completa puede llevar de varios segundos a más de un minuto, como avisa el manual. No sabemos qué explica la diferencia entre las dos máquinas, y no hay una medición de punta a punta en la segunda.

## 9.3 Situaciones problemáticas observadas

Son casos reales de las corridas. En todos, **el E2E aprobó**, porque aprueba por la evidencia del grafo: lo que falla es el texto que lo acompaña.

1. **Un número de otro concepto (E2E-2).** Se preguntó por el riesgo de RAM de la G. El grafo da el rango [49,58 ; 81,46]. La respuesta dijo «un riesgo de RAM del 52.9%». Ese 0,529 es la adecuación global de la G, otra magnitud. El verificador lo dejó pasar porque la cifra existe en la evidencia de esa notebook, y además perdió el rango. Es el error más serio que encontramos: un dato verdadero con el nombre equivocado.
2. **Una respuesta más pobre que su traza (E2E-9).** Se preguntó qué reglas se activaron y de dónde sale cada dato. La traza tiene 18 reglas, 14 con origen y 4 «no registrada». La respuesta nombra 3 reglas (FZ-R2, FZ-R4 y FZ-R5, las de SM2), dice que «los datos vienen de la evaluación del grupo (PI3)» y no menciona la fuente del precio ni de la autonomía ni las reglas sin origen.
3. **Una respuesta que no contesta lo que se pidió (E2E-10).** Se pidieron las mejores en movilidad y el costo-beneficio. La respuesta dice «Vos te conviene la Notebook_A, está recomendada (Alta) en movilidad», mezcla el estado de recomendación con la movilidad, no da el orden y no aclara que la B tiene un índice de costo-beneficio mayor (1,161 contra 0,907 de la A).
4. **Redacción vaga o torpe (E2E-1 y E2E-5).** Para la pregunta «¿cómo andan de RAM?», la respuesta dice «la RAM es mixta», que es el tipo de memoria y no el riesgo. En el E2E-5 aparece «cumpliendo con la alerta excluyente». Nada de eso se contradice con el grafo, pero un asesor lo leería como confuso.
5. **El plan del router a veces omite una intención.** En el E2E-1 falta `SM3.buscar` y en el E2E-9, `SM4.explicar_notebook`. Por eso el criterio de aprobado exige al menos dos submódulos distintos y no un conjunto exacto.
6. **El desempate puede contradecir el costo-beneficio.** La H (grado 0,626, ampliabilidad alta) queda segunda y la B (0,632, ampliabilidad baja) tercera, porque sus grados caen en la misma franja de 0,05 (`P_MARGEN_EMPATE`) y desempata la ampliabilidad. Eso sale de una entrevista y de una decisión del grupo, pero la B rinde más por dólar (1,161 contra 0,811). Cambiar el margen cambia el orden: es un ejemplo de por qué importa validar los parámetros.

## 9.4 Posibles errores y qué los cubre

| Error posible | Qué lo detecta o lo limita | Qué no cubre |
| --- | --- | --- |
| El router elige una intención que no existe, un modelo inexistente o un pedido inventado | `validar()` en Python: intención del conjunto cerrado, modelo del catálogo, fragmento literal, pedido existente | Una intención válida pero equivocada, o que falta (casos R26 y R30 del router) |
| La respuesta cita una cifra, un modelo o una regla inventados | Verificador (controles a a h): regenera hasta 2 veces y después usa la plantilla fija | Una cifra real atribuida a otro concepto (lo encontramos en el E2E-2). Los errores de relación de PI4 de SM4 (CP1: Notebook_X «descartada»; CP5: la alerta de falta de información de M atribuida a B) ya se detectan: el control es por notebook también para alertas dichas en palabras y estados dichos como verbo (`tests/test_explicador.py::TestValidacionPorEntidadYEstado`). Siguen abiertos desde la revisión de código de PG3-13 otros dos: una afirmación que contradice un dato sin nombrar notebook ni estado (por ejemplo, «los parámetros están validados») y el parseo de números con separador de miles (`1.200` se lee como 1,2) |
| Un rango se reduce a un número | Control (f) del verificador | Lo que no se dice como rango pero lo parece, como el caso del 52,9 % |
| Un parámetro mal calibrado cambia un estado | La advertencia de `sin validar` en cada respuesta | Nada hasta que el técnico los valide |
| Un precio o una ficha desactualizados | La fuente y la fecha del precio salen en la traza | No hay actualización automática |
| Ollama o Neo4j no responden | El sistema devuelve `origen_respuesta = "error"` con un mensaje fijo | — |
| Cargar el grafo en una base compartida | `python -m scripts.cargar_grafo` **borra la base**: se usa solo en una instancia propia | No hay confirmación antes de borrar |
| Subir una credencial en el ZIP | `armar_zip` se niega si encuentra una contraseña o una URI de Aura | El control es por patrón, no reemplaza una lectura final |

## 9.5 Cómo leer las cifras del router

El router acertó las intenciones en 28 de 31 consultas (90 %) y el resultado final en 30 de 31 (97 %). Hay que leerlo con un reparo: **la medición no es independiente del prompt maestro**. Seis de las 31 consultas (R01, R02, R05, R14, R17 y R18) coinciden, salvo las tildes, con ejemplos que están en el prompt, y otras tres (R10, R11 y R29) son variantes muy cercanas. Las tres que fallan (R13, R26 y R30) están todas entre las otras 22, de modo que sobre esas el acierto de intenciones es 19 de 22 (86 %), una cifra más honesta de lo que generaliza el modelo. Es un cálculo nuestro a partir de la lista de fallas de la sección 8.3. Tampoco existe todavía un conjunto de consultas escritas por alguien que no vio el prompt.

## 9.6 Oportunidades de mejora

| Mejora | Qué resuelve | Referencia |
| --- | --- | --- |
| **Validar los parámetros con el técnico**, con una tabla de escenarios de RAM y las consultas `CE-*` | Pasa los parámetros de `sin validar` a validados y permite sacar la advertencia | PG1, `ConsultaExperto` |
| **Registrar pedidos nuevos con inferencia en vivo** (`registrar_pedido` y `aclarar_pedido`, con el Cypher parametrizado por pedido) | Que el asistente razone para un comprador real y no solo lea | D-08, PG3-21 |
| **Completar las reglas del nivel 2**: canal de memoria y otras reglas de SM2 (REN-R2, R11, R13, R14), intensidad a gama (GM-R1, R2, R14 a R16), requisitos explícitos y dos escenarios de SM1, monitor externo (REC-R16) | Cerrar lo que PG1 y PG2 describieron y el grafo todavía no tiene | D-04, D-09, D-10; PG3-22 a 24 y 26 |
| **Cargar `SALIDA_PI2` de los 7 perfiles**, `req_04` y `req_05`, y el caso de dos compradores (E2E-4) | Más pedidos y más cobertura de las pruebas | D-03, D-11; PG3-25 |
| **Verificador por concepto**: atar cada cifra al campo del que sale, cortar afirmaciones que contradicen un dato y arreglar el parseo de miles | El error del E2E-2 y sus parientes | Abiertos del review de PG3-13 |
| **Probar un modelo más grande** (`qwen2.5:7b` o `llama3.1:8b`, ya permitidos) | Mejor redacción, a costa de hardware | `docs/RESTRICCIONES.md` §4 |
| **Medir el router con consultas independientes** y repetir los tiempos en otras máquinas | Cifras que generalicen | Sección 9.5 |
| **Guardar la fuente en cada regla** y agregar nodos de fuente con referencia concreta | Cerrar los 4 «no registrada» y llegar de la regla a una cita | Sección 10, D-13, PG3-27 |
| **Catálogo de 30 modelos con precios actualizados** | Sacar al sistema de la demostración | PG1 |

## 9.7 Lo que no está hecho o no se verificó

Al 11/11/2026, cuando se redactó este informe:

| Qué | Estado |
| --- | --- |
| Pedido nuevo con inferencia en vivo (PG3-21) | No se hizo. El sistema lo declara fuera de su alcance |
| Nivel 2 (PG3-22 a 27) | No se hizo. Es trabajo futuro, con su diseño ya documentado en los contextos |
| Tiempos de punta a punta en otra máquina | No se midieron (solo el plan, de 10 a 50 s, en la notebook de Ramiro de Coninck) |
| Video demostrativo (PG3-19) | Pendiente, lo hace una persona |
| Infografía (PG3-18) | Se cubre con el resumen ejecutivo de una página (`docs/presentacion/resumen_ejecutivo.pdf`) |
| Regeneración del verificador con el modelo real | Probada con un LLM falso (`tests/test_explicador.py`). En las 5 respuestas reales de los E2E el verificador aprobó a la primera, así que ninguna usó la regeneración ni la plantilla |
| Reproducción desde un ZIP limpio siguiendo el manual | No se hizo |
| Revisión de código (`/code-review`) sobre PG3-11 | No se corrió |
