# Router y tests con Ollama real · Luconi · 2026-11-14 · PG3-00

## En tres líneas
Fam corrió por primera vez la suite completa con Ollama real (`PG3_TEST_LLM=1`). Fallaron 4 tests: el acierto del router dio 76 % contra el 85 % pedido, E2E-10 falló dos veces y `test_grafo` falló porque quedaron pedidos creados desde la web. Esta rama hace que Python complete las preguntas que el LLM omite, mide el acierto sobre el plan que de verdad se ejecuta y hace que `test_grafo` ignore los pedidos creados desde consultas.

## Qué pasaba
- **El LLM planifica solo la primera pregunta.** Ante «¿qué me recomendás? ¿Cómo andan de RAM y de gráfica?», `qwen2.5:3b` devolvió solo `SM4.recomendar`. Pasó en R17, R26, R30, R31 y R34, aunque R17 es literalmente un ejemplo del prompt. E2E-10 es R31: sin `SM3.buscar`, no hubo orden por movilidad.
- **El test medía el plan crudo del LLM.** En R18, R21 y R37 el LLM agregó `SM1.registrar_pedido`, pero `validar()` ya lo descartaba y el resultado final era correcto (37/37). El test contaba como error algo que nunca se ejecuta.
- **`test_grafo` esperaba exactamente `req_01` a `req_03`**, pero en la base de Fam quedaron `req_101` y `req_102` de probar la web.

## Qué cambió
| Archivo | Qué tiene ahora |
| --- | --- |
| [`asistente/router.py`](../../asistente/router.py) | `_SENALES` y `_completar_por_senales`: si el texto tiene una frase inequívoca («por su precio», «costo-beneficio», «de RAM», «movilidad», «de gráfica», «qué reglas») y el plan no trae esa intención, Python la agrega, hasta 3 consultas. Queda en `observaciones`. |
| [`tests/test_router.py`](../../tests/test_router.py) | `TestSenales`: ninguna señal agrega una intención que el CSV no espera (control contra falsos positivos) y los tres casos de la corrida real. El test con LLM mide el plan validado e imprime aparte el acierto del LLM solo. |
| [`tests/test_grafo.py`](../../tests/test_grafo.py) | Ignora los pedidos con `origen: 'consulta'`. |

## Decisiones y por qué
- **Señales en Python y no un prompt más largo.** El prompt ya tenía R17 como ejemplo y el modelo de 3 B igual lo omitió. Un prompt más largo no se puede probar acá (no hay Ollama) y es menos confiable. Las señales son frases literales, y el CSV las controla. El LLM sigue armando el plan y Python solo completa lo que el texto pide literalmente, igual que ya hacía con `SM1.registrar_pedido`.
- **Medir el plan que se ejecuta.** Es lo que ve el usuario. Se sigue imprimiendo el acierto del LLM solo, para ver si un cambio en el prompt mejora o empeora.

## Cómo probarlo
```powershell
python -m unittest                                        # 240 OK, 5 salteadas
$env:PG3_TEST_LLM="1"; python -m unittest tests.test_router tests.test_e2e
python -m scripts.limpiar_pedidos                         # borra req_101 en adelante
```

## Qué queda y dudas
- Con las señales, las omisiones de R17, R26, R31 y R34 se completan. R30 («de dónde sale cada dato», `SM4.explicar_notebook`) y el `SM3.buscar` de más en R35 dependen del LLM. Falta que alguien con Ollama confirme el porcentaje.
- `router.py` y el prompt son de Olea: pido que revise las señales.
