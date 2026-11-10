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
- **8 ejemplos**, dos de ellos multisubmódulo.

En cada llamada recibe el catálogo, los pedidos cargados y el pedido de la sesión. El plan admite hasta 3 consultas, de modo que una pregunta como «¿Por qué la G quedó indeterminada y qué riesgo de RAM tiene en req_01?» se responde con SM4 y SM2 a la vez.

## Modelo, temperatura y salida estructurada
- **Modelo:** `qwen2.5:3b` en Ollama local, sin costo de API y con unos 4 GB de RAM, por lo que corre en las cuatro notebooks del grupo (D-05).
- **Temperatura 0**, para que las respuestas sean reproducibles.
- **LangChain como cliente**, siguiendo el ejemplo de PG3 de la cátedra: `ChatPromptTemplate | ChatOllama.with_structured_output(esquema)`. El esquema JSON del plan, con un `enum` de intenciones y `maxItems: 3`, obliga al modelo a devolver un JSON válido, que compensa la debilidad de un modelo chico.
- **Despacho:** cada intención validada va a su submódulo mediante un mapa de `RunnableLambda`.
- **Sin agentes ni *tool calling*:** qué consulta se ejecuta lo decide el código, no el modelo.

## Qué hace el LLM y qué no
| Hace | No hace |
| --- | --- |
| Interpretar la consulta y elegir intenciones | Calcular grados, riesgos o puntajes |
| Extraer modelos, pedidos y filtros mencionados | Decidir si una notebook se recomienda o se descarta |
| Redactar la explicación para el asesor | Escribir o elegir Cypher |
| | Completar un pedido o un dato que el usuario no dio |

## Acierto real del router
El router se probó con `tests/datos/consultas_router.csv`: 25 consultas que cubren las 13 intenciones, 4 multisubmódulo, 3 fuera de dominio, 2 sin pedido, 1 con pedido de sesión y 2 con modelos inexistentes. La corrida se hizo con `qwen2.5:3b` a temperatura 0 el 10/11/2026 y tardó 217 s.

| Medida | Resultado |
| --- | --- |
| Intenciones correctas en el plan del LLM | **24 / 25 (96 %)** |
| Resultado final después de la validación en Python (plan, aclaración o fuera de alcance) | **25 / 25 (100 %)** |

El único error del modelo fue planificar «¿Cuál es la capital de Francia?» como `GRUPO.parametros`. La validación lo detectó (el texto no tiene ninguna palabra del dominio) y respondió con el mensaje fijo de fuera de alcance sin consultar el grafo.

Las consultas sin pedido terminaron en una pregunta («¿Sobre qué pedido?»), nunca en `req_01`, y los modelos inexistentes (Notebook_Z y Notebook_Q) en una aclaración con el catálogo. Ninguna terminó en una excepción no controlada.

El plan tarda entre 5 y 50 s por consulta en una notebook sin GPU dedicada, según si el modelo ya estaba cargado en memoria.
