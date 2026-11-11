# 8. Pruebas y resultados

Todo se corrió el 11/11/2026 sobre Neo4j 5.26 (instancia local con el grafo cargado desde `cypher/`) y Ollama con `qwen2.5:3b`, temperatura 0.

## 8.1 Resumen

| Prueba | Qué cubre | Resultado |
| --- | --- | --- |
| `python -m unittest` | Submódulos, grafo, router, orquestador, explicador, API | 171 tests, 2 salteados (los que piden Ollama) |
| `python -m scripts.verificar_grafo` | Casos de prueba CP1 a CP11 del grafo | 11 de 11 |
| `python -m scripts.contar_grafo` | El grafo dividido (`cypher/`) contra el canónico | 343 nodos y 683 relaciones, coinciden |
| `python -m scripts.correr_e2e` | Los 7 E2E con el orquestador real | 7 de 7 aprueban (5 integrales y 2 controles) |
| `PG3_TEST_LLM=1 python -m unittest tests.test_router` | Acierto del router sobre 31 consultas | Intenciones 28 de 31 (90 %); resultado final 30 de 31 (97 %) |

Las pruebas funcionales por tipo (recuperación, consulta, regla, difuso y respuesta, consigna §3.5) están en [`docs/pruebas/funcionales.md`](../pruebas/funcionales.md).

## 8.2 E2E

Detalle en [`docs/pruebas/resultados_e2e.md`](../pruebas/resultados_e2e.md). Cada E2E aprueba por lo que dice el grafo, no por el texto del LLM.

| E2E | Tipo | Origen de la respuesta | Tiempo (s) |
| --- | --- | --- | --- |
| E2E-1 | integral | llm | 7,1 |
| E2E-2 | integral | llm | 5,1 |
| E2E-3 | control | validación | 1,3 |
| E2E-5 | integral | llm | 4,5 |
| E2E-8 | control | fuera de alcance | 0,7 |
| E2E-9 | integral | llm | 4,3 |
| E2E-10 | integral | llm | 4,3 |

Los tiempos son de **una** máquina (el plan del router es lo que más tarda, entre 2 y 4 s). Falta medirlos en otra.

## 8.3 Router

Intenciones acertadas: 28 de 31. Las tres que fallan:
- **R13** (responder una pregunta pendiente): es una intención de nivel 2, que el router rechaza a propósito; el modelo elige `interpretacion_pedido`.
- **R26** y **R30**: el plan omite una intención de las esperadas (SM3.buscar y SM4.explicar_notebook). El E2E igual aprueba, porque exige al menos dos submódulos distintos y no un conjunto exacto.

Una mejora del 11/11: el router descarta los filtros de SM3 que el texto no pide (el modelo copiaba los del ejemplo del prompt: `peso_max` y `bateria_min`).

## 8.4 Explicador y verificador

- 0 de 5 respuestas con explicación salieron de la plantilla fija en la corrida de los E2E: las redactó el LLM y las aprobó el verificador a la primera.
- El verificador **corta lo inventado** (cifras, modelos, reglas, alertas de otra notebook, rangos reducidos a un número, perfil asumido, recomendar lo descartado), pero **no garantiza que la redacción sea buena**: con `qwen2.5:3b` hay frases torpes y alguna afirmación suelta sin respaldo numérico (por ejemplo, «GPU integrada moderna» en E2E-1). Esa es la limitación principal del modelo chico.
- Pasar a `qwen2.5:7b` mejora la redacción, pero a un integrante le colgaba la PC.

## 8.5 Lo que no se verificó

- Los tiempos en más de una máquina.
- Un E2E por nivel 2 (pedido nuevo con inferencia): PG3-21 y PG3-22 a 27 no están hechos.
