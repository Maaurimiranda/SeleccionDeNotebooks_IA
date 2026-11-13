# 6. Integración con el LLM

## Patrón sándwich
El LLM aparece en los dos extremos del flujo, y el conocimiento ocupa el medio:

1. **Router (LLM):** traduce la consulta a un plan JSON de intenciones cerradas.
2. **Validación (Python):** descarta intenciones, modelos y pedidos inválidos antes de tocar el grafo.
3. **Cypher fijo (Neo4j):** cada intención ejecuta consultas escritas de antemano, en modo solo lectura. El LLM nunca escribe Cypher.
4. **Explicador (LLM) y verificador (Python):** redactan la respuesta solo con la evidencia que devolvió el grafo. Si una cifra, un modelo o una regla no está en la evidencia, se regenera hasta dos veces y después se usa una plantilla fija.

## Prompt maestro
`prompts/maestro.txt` aplica las técnicas de A10:
- un **rol** acotado («sos el router; no respondas la pregunta»);
- **límites**: no calcula, no inventa modelos, cifras ni pedidos, y nunca supone `req_01`;
- las **13 intenciones**, una línea cada una, con cuándo usarla;
- **restricciones negativas** y un **formato cerrado**;
- **9 ejemplos**, uno de ellos multisubmódulo.

En cada llamada recibe el catálogo, los pedidos cargados y el pedido de la sesión. El plan admite hasta 3 consultas, de modo que una pregunta como «¿Por qué la G quedó indeterminada y qué riesgo de RAM tiene en req_01?» se responde con SM4 y SM2 a la vez.

## Modelo, temperatura y salida estructurada
- **Modelo:** `qwen2.5:3b` en Ollama local, sin costo de API y con unos 4 GB de RAM, por lo que corre en las cuatro notebooks del grupo (D-05).
- **Temperatura 0**, para que las respuestas sean reproducibles.
- **LangChain como cliente**, siguiendo el ejemplo de PG3 de la cátedra: `ChatPromptTemplate | ChatOllama.with_structured_output(esquema)`. El esquema JSON del plan, con un `enum` de intenciones y `maxItems: 3`, obliga al modelo a devolver un JSON válido, que compensa la debilidad de un modelo chico.
- **Despacho:** cada intención validada va a su submódulo mediante un mapa de `RunnableLambda`.
- **Sin agentes ni *tool calling*:** qué consulta se ejecuta lo decide el código, no el modelo.

## Explicador y verificador
`asistente/explicador.py` y `prompts/explicacion.txt` son comunes a todos los submódulos. El LLM recibe la evidencia común **compactada** (reglas repetidas juntas, listas largas cortadas a 12 filas, porque `qwen2.5:3b` tiene poco contexto) y redacta en voseo para el asesor, con un máximo de 150 palabras en el prompt. El verificador compara la respuesta contra la evidencia **original**, sin compactar, con ocho controles:

| Control | Qué exige |
| --- | --- |
| a | Cada cifra está en la evidencia (con redondeo y coma o punto) y, si la oración habla de una sola notebook, es un dato de esa notebook o del pedido |
| b | Cada `Notebook_X` y cada regla citada existen |
| c | Cada alerta está en la notebook que la tiene, también si se nombra en palabras («alerta de falta de información») y no por su código |
| d | Hasta 180 palabras y no vacía |
| e | Están la advertencia de parámetros sin validar y cada aviso de validación (en SM4, el de los 9 parámetros de recomendación), literales. Si el modelo no los copia, los agrega el código |
| f | Un rango no se da como un valor intermedio ni con un solo extremo |
| g | Si el pedido es `indeterminado`, no se nombra un perfil |
| h | El estado que se afirma de cada notebook es el suyo, comparado sin tildes, también cuando se dice como verbo («se descartó»), antes del nombre o en una enumeración |

Si algún control falla, se vuelve a pedir la respuesta pasándole al modelo los problemas y su respuesta anterior, hasta `MAX_REGENERACIONES = 2` veces. Si sigue fallando, sale la **plantilla fija**, armada en código solo con la evidencia (`origen_respuesta = "plantilla_fija"`). En los 5 E2E con explicación (11/11/2026) el verificador aprobó a la primera: 0 de 5 salieron de la plantilla. El verificador corta lo inventado, pero no garantiza que la redacción sea buena ni que cada cifra lleve el nombre correcto (sección 9).

**Validación por entidad y estado (devolución docente del PI4 de SM4).** En el PI4, `qwen2.5:3b` dijo que Notebook_X estaba descartada (CP1; es `Recomendada (Media)`, fuera de presupuesto) y le atribuyó a Notebook_B la alerta de falta de información de Notebook_M (CP5). El control de entonces verificaba que existieran los números y los nombres, pero no a qué notebook correspondía cada afirmación. Ahora cada oración se parte en tramos, uno por notebook nombrada, y los controles c y h comparan cada tramo con la evidencia de esa notebook. Con la evidencia real de `req_01`, el verificador anterior dejaba pasar «Se descartó la Notebook_X» y «Notebook_B tiene una alerta de falta de información», y el actual las rechaza (`tests/test_explicador.py::TestValidacionPorEntidadYEstado`).

## Qué hace el LLM y qué no
| Hace | No hace |
| --- | --- |
| Interpretar la consulta y elegir intenciones | Calcular grados, riesgos o puntajes |
| Extraer modelos, pedidos y filtros mencionados | Decidir si una notebook se recomienda o se descarta |
| Redactar la explicación para el asesor | Escribir o elegir Cypher |
| | Completar un pedido o un dato que el usuario no dio |

## Acierto real del router
El router se probó con `tests/datos/consultas_router.csv`, con `qwen2.5:3b` a temperatura 0. La medición final (11/11/2026) usa **31 consultas**: las 25 de la primera medición, que cubren las 13 intenciones, 4 multisubmódulo, 3 fuera de dominio, 2 sin pedido, 1 con pedido de sesión y 2 con modelos inexistentes, más las 6 consultas de los E2E.

| Medida (31 consultas) | Resultado |
| --- | --- |
| Intenciones correctas en el plan del LLM | **28 / 31 (90 %)** |
| Resultado final después de la validación en Python (plan, aclaración o fuera de alcance) | **30 / 31 (97 %)** |

Las tres intenciones que fallan son R13 (responder una pregunta pendiente, que es de nivel 2 y el router rechaza a propósito) y R26 y R30, donde el plan omite una de las intenciones esperadas. Los detalles están en la sección 8.3.

La primera medición (10/11/2026, 25 consultas, 217 s) había dado 24 de 25 intenciones (96 %) y 25 de 25 resultados finales. Su único error fue planificar «¿Cuál es la capital de Francia?» como `GRUPO.parametros`: la validación lo detectó (el texto no tiene ninguna palabra del dominio) y respondió con el mensaje fijo de fuera de alcance sin consultar el grafo. En esa corrida, las consultas sin pedido terminaron en una pregunta («¿Sobre qué pedido?»), nunca en `req_01`, y los modelos inexistentes (Notebook_Z y Notebook_Q) en una aclaración con el catálogo.

**Reparo.** La medición no es independiente del prompt: cada uno de los 9 ejemplos del prompt maestro tiene su consulta gemela, exacta o muy cercana, en el conjunto de prueba (sección 9.5).

El plan tardó entre 0,7 y 6,1 s en los E2E del 11/11 (una máquina). En otra, la notebook de Ramiro de Coninck (10/11), tardó entre 10 y 50 s; la primera consulta es la más lenta porque Ollama carga el modelo en memoria. Falta medir los tiempos de punta a punta en esa máquina.
