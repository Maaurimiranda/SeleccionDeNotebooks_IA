# Pruebas funcionales (consigna §3.5)

Generado el 2026-11-11 sobre Neo4j 5.26 con el grafo cargado desde `cypher/`. Corrida completa: `python -m unittest` (171 tests, 2 salteados que piden Ollama) y `python -m scripts.verificar_grafo` (CP1 a CP11, 11/11).

| Tipo | Qué verifica | Prueba | Esperado | Obtenido (corrida) | OK |
| --- | --- | --- | --- | --- | --- |
| Recuperación | SM3.buscar con el filtro `dedicada`: X con grado de GPU 0,74 | tests/test_sm3.py · `test_x_grado_gpu_074` | Solo X (y las dedicadas) con 0,74 | pasa | sí |
| Recuperación | SM3.ficha de la M: la autonomía desconocida viaja como `null`, no como un número | tests/test_sm3.py · `test_ficha_m` | autonomía `null`, tipo `desconocida` | pasa | sí |
| Recuperación | SM4 consulta solo las evaluaciones del pedido pedido (los pedidos no se mezclan) | tests/test_sm4.py · `test_los_pedidos_no_se_mezclan` | Ningún dato de otro pedido | pasa | sí |
| Consulta | Cada intención ejecuta su plantilla Cypher fija y de solo lectura | tests/test_sm4.py · `test_solo_lectura`; tests/test_grafo.py | Sin MERGE/CREATE/SET/DELETE; `READ_ACCESS` | pasa | sí |
| Consulta | SM2.virtualizacion coincide con la consulta C1 del canónico | tests/test_sm2.py · `test_virtualizacion_coincide_con_c1` | Mismas notebooks descartadas | pasa | sí |
| Consulta | Los conteos del grafo dividido igualan al canónico | scripts/contar_grafo.py · docs/pruebas/conteos_grafo.md | 343 nodos y 683 relaciones | coincide | sí |
| Regla | REC-R3: E sin virtualización queda descartada aunque puntúe 0,81 | scripts/verificar_grafo.py · CP2; tests/test_sm4.py · `test_e2e_5_el_excluyente_gana_al_puntaje` | `Descartada (excluyente incumplido)` | 11/11 CP | sí |
| Regla | REC-R8: desempate por ampliabilidad (A 1, H 2, B 3) | scripts/verificar_grafo.py · CP7 | A, H, B | OK | sí |
| Regla | La traza de A trae reglas de los 4 submódulos, con su origen cuando el grafo lo tiene | tests/test_grupo.py · `test_traza_a`, `test_origen_de_la_traza_de_a` | 18 reglas, 14 con origen, 4 «no registrada» | pasa | sí |
| Difuso | G indeterminada: riesgo de RAM como rango [49,58 ; 81,46] y alertas REN-R10 y FZ-R7 | scripts/verificar_grafo.py · CP4; tests/test_sm2.py | Rango sin promediar | OK | sí |
| Difuso | M sin autonomía: condicionada, grado [0,504 ; 0,826] | scripts/verificar_grafo.py · CP9; tests/test_sm4.py · `test_e2e_2_m_rango_y_falta_la_autonomia` | Rango, no un número | OK | sí |
| Difuso | 47 etiquetas difusas sin validar en 15 variables | scripts/verificar_grafo.py · CP8 | 47 y 15 | OK | sí |
| Respuesta | Los literales de estado y validación son los de D-06 en todo lo que devuelve SM4 | tests/test_sm4.py · `test_literales_d06_en_todo_lo_que_devuelve` | Sin tildes, `sin validar` | pasa | sí |
| Respuesta | El verificador rechaza cifras, modelos, reglas y alertas sin respaldo | tests/test_explicador.py (≈50 casos, uno por control a–h) | Cada control se dispara | pasa | sí |
| Respuesta | Si el LLM falla dos veces, sale la plantilla fija, que pasa su propio verificador | tests/test_explicador.py · `TestExplicar`, `TestPlantillaFija` | `origen_respuesta = plantilla_fija` | pasa | sí |
| Respuesta | E2E-1, 2, 3, 5, 8, 9 y 10 contra el orquestador real | scripts/correr_e2e.py · docs/pruebas/resultados_e2e.md | Los esperados salen del grafo | 7 de 7 | sí |

Cubre los cinco tipos de §3.5: recuperación, consulta, regla, difuso y respuesta. Los E2E (casos que cruzan submódulos) están en [`resultados_e2e.md`](resultados_e2e.md) y [`casos_de_uso.md`](casos_de_uso.md).
