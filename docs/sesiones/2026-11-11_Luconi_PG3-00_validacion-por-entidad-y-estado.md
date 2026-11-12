# Validación por entidad y estado, y los 9 parámetros de SM4 · Luconi · 2026-11-11 · PG3-00

## En tres líneas
La devolución docente del PI4 de SM4 marcó dos errores del LLM: en CP1 dijo que Notebook_X estaba descartada (es `Recomendada (Media)`, fuera de presupuesto) y en CP5 le atribuyó a Notebook_B una alerta de falta de información que es de Notebook_M. También pidió dejar visible que los nueve parámetros de recomendación siguen sin validar con el técnico.
Ahora el verificador del explicador controla cada afirmación contra la notebook a la que corresponde, también cuando la alerta o el estado se dicen en palabras, y toda respuesta de SM4 lleva un aviso con la cuenta de parámetros sin validar, que sale del grafo.
Estado: hecho, con 193 tests en verde offline (29 salteados por falta de Neo4j u Ollama). No se corrió contra Neo4j ni con qwen2.5:3b.

## Qué cambió
| Archivo | Qué tiene ahora |
| --- | --- |
| `asistente/explicador.py` | Control (c) para alertas dichas en palabras («alerta de falta de información», «información incompleta», «no informa») y para «tiene una alerta» dicho de una notebook sin alertas. Control (h) para estados dichos como verbo («se descartó», «la descartamos»), antes del nombre y en enumeraciones; un estado negado («no fue descartada») no cuenta. Control (e) y la plantilla fija exigen y muestran todos los `aviso_validacion`, no solo la advertencia. |
| `asistente/submodulos/sm4/repositorio.py` | Consulta nueva `Q8_PARAMETROS_SM4`: cuenta las etiquetas difusas de SM4 y cuántas siguen `'sin validar'`. |
| `asistente/submodulos/sm4/servicio.py` | Las cuatro intenciones agregan Q8 y `validacion_parametros` a la evidencia, con el aviso «Los 9 parametros de recomendacion de SM4 todavia requieren validacion con el tecnico.» |
| `asistente/submodulos/sm4/esquemas.py` | `ValidacionParametros` y el campo en las cuatro evidencias. |
| `prompts/explicacion.txt` | Copiar también los avisos de validación; una alerta en palabras y un estado son de su notebook. |
| `tests/test_explicador.py` | `TestValidacionPorEntidadYEstado`: las frases reales de CP1 y CP5, variantes, lo correcto que tiene que pasar y un caso de SM2 (el verificador es común). |
| `tests/test_sm4.py`, `tests/test_orquestador.py` | Q8 en las listas de consultas esperadas, y el aviso en la respuesta de punta a punta. |
| `tests/fixtures/SM4.*.json` | La consulta Q8 con sus filas (9 de 9 sin validar) y la evidencia regenerada con el grafo falso. |
| `docs/MANUAL_DE_USO.md`, `docs/informe/09_evaluacion.md` | El aviso nuevo, y que CP1 y CP5 ya se detectan. |

## Cómo funciona (para alguien que no estuvo)
El verificador (REC-R11, D-07 §6) ya partía cada oración en **tramos**: cada tramo es de la notebook nombrada justo antes. «Notebook_A queda primera y Notebook_X, descartada» tiene un tramo de A y uno de X. Con eso comparaba cifras, alertas por su código (`REC-R15`) y estados escritos con el literal de D-06.

El hueco era lo que el LLM dice **sin código ni literal**. En CP5, «Notebook_B tiene una alerta de falta de información» no trae `REC-R15`, así que no se comparaba con nadie. Ahora el verificador arma, desde la evidencia, el conjunto de notebooks a las que les falta un dato (las que tienen una alerta o un texto con «no informa», «falta», «desconocida», «incompleta» o «indeterminada», o un `dato_faltante`). En `SM4.costo_beneficio` de req_01 ese conjunto es {Notebook_M}. Si un tramo de B habla de falta de información, falla con «(c) la falta de información es de Notebook_M, no de Notebook_B» y el LLM regenera.

Con los estados pasa lo mismo: «Se descartó la Notebook_X» usa un verbo y pone el estado antes del nombre. Ahora el verbo cuenta como `Descartada` y se atribuye a la primera notebook de la oración. Como X está `Recomendada (Media)`, falla el control (h).

Para los parámetros, Q8 cuenta en el grafo las etiquetas de las tres variables de SM4 (`adecuacion_global`, `excedente_presupuesto` y `grado_recomendacion`, tres cada una) y cuántas están `'sin validar'`. El servicio arma el aviso con esa cuenta. El explicador lo exige literal, como la advertencia, y si el LLM no lo copia lo agrega el código.

## Decisiones y por qué
- **El aviso va en SM4 y no en `contrato.py`.** La advertencia general (`ADVERTENCIA`) no se tocó, porque el contrato solo cambia con un PR aprobado por Miranda (CLAUDE.md). El aviso vive en la evidencia de SM4, que es de Luconi.
- **La cuenta sale del grafo, no está fija en el texto.** Si el técnico valida etiquetas, el número cambia sin tocar código, y con todas validadas el aviso desaparece. Así lo hacía Q8 en el PI4 («Siempre: Q8», contexto de SM4 §5). Se descartó escribir «9» a mano.
- **El control por tema es amplio pero acotado.** Solo mira tramos con una notebook nombrada y que no estén negados («Notebook_B no tiene falta de información» pasa). Como el verificador es común, también actúa sobre SM2 y SM3. Por eso hay un test con la G de SM2 (`REN-R10`), y todos los fixtures siguen pasando con su plantilla fija.

## Cómo probarlo
```
python -m unittest tests.test_explicador tests.test_sm4 tests.test_orquestador
python -m unittest discover -s tests -t .
```
Tiene que dar OK. Hoy, sin Neo4j ni Ollama: 193 tests y 29 salteados.

## Qué queda y dudas
- **No se corrió contra Neo4j.** Las filas de Q8 en los fixtures se escribieron a partir de `cypher/01_conocimiento.cypher` (líneas 128 a 136, 9 de 9 `'sin validar'`). Hay que correr `python -m scripts.generar_fixtures` con la base para confirmarlas.
- **No se midió con qwen2.5:3b.** El aviso nuevo suma 12 palabras a cada respuesta de SM4, dentro del máximo de 180. Falta ver si el modelo chico regenera más seguido por los controles nuevos (`PG3_TEST_LLM=1 python -m unittest tests.test_explicador`).
- Una falta de información dicha con otras palabras («le falta la batería») todavía no se reconoce.
