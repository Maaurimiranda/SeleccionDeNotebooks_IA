# Router con prompt maestro e informe (problema, LLM, metodología) · de Coninck · 2026-11-10 · PG3-06 y PG3-08

## En tres líneas
El router traduce cualquier consulta a un plan JSON con el prompt maestro y lo valida en Python antes de tocar el grafo. Con `qwen2.5:3b` acertó las intenciones en el 96 % de 25 consultas, y el resultado final, después de la validación, fue correcto en el 100 %. Quedaron escritas las secciones 3, 6 y 11 del informe. **Olea:** el router y esas secciones son tuyos según el plan; revisalos.

## Qué cambió
| Archivo | Qué tiene ahora |
| --- | --- |
| [prompts/maestro.txt](../../prompts/maestro.txt) | Rol, límites, 13 intenciones, datos disponibles y 8 ejemplos |
| [asistente/router.py](../../asistente/router.py) | `planificar` (LLM con salida estructurada) y `validar` (reglas en Python) |
| [tests/datos/consultas_router.csv](../../tests/datos/consultas_router.csv) | 25 consultas con su plan y su resultado esperados |
| [tests/test_router.py](../../tests/test_router.py) | 19 tests offline de `validar`, cobertura del CSV y la medición con el LLM |
| [docs/informe/03_problema.md](../informe/03_problema.md), [06_integracion_llm.md](../informe/06_integracion_llm.md), [11_reflexion_metodologia.md](../informe/11_reflexion_metodologia.md) | Secciones del informe con las cifras reales |

## Cómo funciona (para alguien que no estuvo)
El LLM **propone** y Python **dispone**. Para «¿Qué riesgo de RAM tiene la Notebook_G?», sin pedido en la sesión:

1. `planificar` llena el prompt maestro con el catálogo y los pedidos, y LangChain le pide al modelo un JSON que cumpla `ESQUEMA_PLAN`. Llega `SM2.riesgo_ram` con `modelos: ["Notebook_G"]`. A veces el modelo «completa» `requerimiento_id: "req_01"`.
2. `validar` aplica sus reglas, en este orden:
   - **Fuera de alcance:** se respeta, salvo que el texto tenga palabras del dominio.
   - **Fragmentos:** solo quedan los literales.
   - **Pedido:** manda el que escribió el usuario, después el de la sesión. El que inventa el LLM se descarta y queda anotado en las observaciones.
   - **Modelos:** se normalizan («la G» → Notebook_G) y tienen que existir en el catálogo; un Notebook_Z escrito en el texto da una aclaración.
   - **Consultas:** se descartan las intenciones inválidas, las de nivel 2 se rechazan con aclaración, sobran parámetros que se ignoran y el plan se corta en 3 consultas.
3. En el ejemplo no hay pedido escrito ni de sesión, así que la respuesta es «¿Sobre qué pedido?». **Nunca se asume `req_01`.**

## Decisiones y por qué
- **La intención va con su prefijo en un solo campo** (`"SM2.riesgo_ram"`), con un `enum` en el esquema. Un modelo de 3B se equivoca menos con un campo cerrado que con dos (`sm` + `intencion`). `validar` acepta igual la forma de dos campos.
- **Guarda de dominio:** el LLM a veces marca `fuera_de_alcance` en consultas del dominio y, al revés, planificó la capital de Francia como `GRUPO.parametros` (R18). Una lista corta de palabras del dominio corrige los dos casos.
- **La prueba con LLM se corre aparte** (`PG3_TEST_LLM=1`): tarda unos 4 minutos y no tiene que frenar el `python -m unittest` de todos.
- **El texto de la aclaración es fijo**, no el que propone el LLM en `aclaracion`, para que el modelo no le hable directamente al usuario.

## Cómo probarlo
```bash
python -m unittest tests.test_router                       # offline, 1 s
PG3_TEST_LLM=1 python -m unittest tests.test_router        # con Ollama: imprime el acierto por consulta
```
Resultado del 10/11/2026: 24/25 intenciones (96 %) y 25/25 resultados finales, en 217 s.

## Qué queda y dudas
- Ajustar el prompt con los E2E del jueves (PG3-11) si aparece algún caso nuevo.
- La sección 6 describe el explicador y el verificador como se definieron en D-07. Cuando Luconi cierre PG3-13, hay que confirmar que el texto coincide con lo implementado.
- La reflexión menciona etapas de PG0 y PG1 que conozco por los contextos, no por los informes originales. Conviene que alguien que los escribió la relea.
