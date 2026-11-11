# E2E, casos de uso y pruebas funcionales · Miranda · 2026-11-11 · PG3-11

## En tres líneas
- `scripts/correr_e2e.py` corre los 7 E2E (5 integrales y 2 controles) con el orquestador real y escribe un `E2E-n.md` por corrida, la tabla de resultados y `casos_de_uso.md`. **Los 7 aprueban** con Neo4j y `qwen2.5:3b`.
- El aprobado se decide por la **evidencia del grafo** (puestos, estados, rangos, alertas, conteos de reglas), no por el texto del LLM.
- Salió de acá una mejora del router (descarta filtros que el texto no pide) y un ejemplo nuevo en el prompt maestro (comparar).

## Qué cambió
| Archivo | Qué tiene ahora |
| --- | --- |
| [`scripts/correr_e2e.py`](../../scripts/correr_e2e.py) | Los 7 E2E con sus esperados, y los documentos generados |
| [`tests/test_e2e.py`](../../tests/test_e2e.py) | Los mismos E2E como `unittest` (piden Neo4j y Ollama) |
| [`asistente/router.py`](../../asistente/router.py) | `_filtro_en_texto`: un filtro de SM3 vale solo si el usuario lo dijo |
| [`prompts/maestro.txt`](../../prompts/maestro.txt) | Un ejemplo de `SM4.comparar` («casi el mismo puntaje… ¿por qué no la recomiendan?») |
| [`tests/datos/consultas_router.csv`](../../tests/datos/consultas_router.csv) | 6 consultas nuevas (los E2E): 31 en total |
| [`docs/pruebas/`](../pruebas/) | `E2E-n.md`, `resultados_e2e.md`, `casos_de_uso.md`, `funcionales.md`, trazas JSONL |
| [`docs/informe/07_casos_de_uso.md`](../informe/07_casos_de_uso.md), [`08_pruebas.md`](../informe/08_pruebas.md) | Secciones del informe |

## Cómo funciona (para alguien que no estuvo)
Cada E2E es una consulta en texto libre (por ejemplo, «En req_01, ¿qué reglas se activaron para la A…?»). `correr_e2e` se la pasa a `Orquestador.consultar`, que arma el plan con el LLM, ejecuta las consultas Cypher y explica. Después compara la **traza** con lo que tiene que dar el grafo: por ejemplo, para E2E-9, que la traza de la A tenga 18 reglas de los cuatro submódulos, 14 con origen y cuatro «no registrada».

Un caso integral tiene que pedir **al menos dos submódulos distintos** en el plan, sin contar SM1 (que el orquestador agrega siempre). Por eso E2E-2 y E2E-5 llevan una segunda pregunta (riesgo de RAM, virtualización): con la pregunta de D-12 sola, el plan tenía un único submódulo.

## Decisiones y por qué
- **Esperados por evidencia y no por texto:** el LLM puede redactar distinto cada vez; el grafo no.
- **Exigir ≥ 2 submódulos distintos y no un conjunto exacto:** `qwen2.5:3b` a veces omite una intención (E2E-1 omite SM3 de vez en cuando). Un conjunto exacto haría fallar un E2E por una variación del modelo que no cambia lo que dice el grafo.
- **Filtros de SM3 solo si el texto los pide:** E2E-10 mostró que el modelo copiaba `peso_max` y `bateria_min` del ejemplo del prompt, y eso excluía notebooks que el usuario no pidió excluir.

## Cómo probarlo
```bash
python -m scripts.correr_e2e                              # todos; reescribe docs/pruebas
PG3_TEST_LLM=1 python -m unittest tests.test_e2e          # como tests
PG3_TEST_LLM=1 python -m unittest tests.test_router       # acierto del router (90 %)
```

## Qué queda y dudas
- **Tiempos en otra máquina** (el issue pide más de una): hoy hay una sola medición (4 a 7 s por E2E con respuesta del LLM).
- **Router:** 28 de 31 intenciones (90 %). R13 es de nivel 2; R26 y R30 omiten una intención.
- **La redacción de `qwen2.5:3b` es torpe** y el verificador no corta afirmaciones sueltas sin cifra. Ver `docs/informe/08_pruebas.md`.
- **Revisión de código:** no se corrió sobre esta tarea.
