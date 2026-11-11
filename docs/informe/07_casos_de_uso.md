# 7. Casos de uso integrados

La consigna pide al menos tres E2E y cinco casos de uso que **crucen información entre submódulos** (§2, §3.4 y §7). El sistema los resuelve con un plan del router que pide intenciones de más de un submódulo; el orquestador agrega siempre `SM1.interpretacion_pedido` cuando hay un pedido, y eso **no cuenta** como cruce.

| Caso | Consulta | Submódulos del plan | Qué muestra |
| --- | --- | --- | --- |
| E2E-1 | «Para req_01, ¿qué notebook me recomendás? ¿Cómo andan de RAM y de gráfica?» | SM4 + SM2 (+ SM3 según el plan) | Ranking A, H, B; X fuera de presupuesto; M condicionada; E y C descartadas; G indeterminada |
| E2E-2 | «¿Por qué la M quedó condicionada y la G indeterminada? ¿Qué riesgo de RAM tiene la G?» | SM4 + SM2 | Los rangos se conservan: M [0,504 ; 0,826] y riesgo de G [49,58 ; 81,46] |
| E2E-5 | «La E tiene casi el mismo puntaje que la B y la H, ¿por qué no la recomiendan?» | SM4 + SM2 | La excluyente (REC-R3) gana al puntaje (≈ 0,81) |
| E2E-9 | «¿Qué reglas se activaron para la A, de dónde sale cada dato y qué riesgo de RAM tiene?» | GRUPO + SM2 | Trazabilidad (§3.7): 18 reglas de los 4 submódulos, 14 con origen y 4 «no registrada» |
| E2E-10 | «¿Cuáles son las mejores en movilidad y cómo queda el costo-beneficio?» | SM3 + SM4 | Orden por movilidad con los datos faltantes al final; índice costo-beneficio de REC-R9 |

Además hay dos **controles**, que no cuentan como casos integrales: E2E-3 (pedido con perfil indeterminado: el sistema no asume un perfil y pide responder la pregunta pendiente) y E2E-8 (fuera de alcance: mensaje fijo y ninguna consulta al grafo).

**Cómo se decide que un E2E aprueba.** No por lo que dice el LLM, sino por lo que devuelve el grafo: cada E2E tiene esperados (puestos, estados, rangos, alertas, conteos de reglas) que se comparan con la evidencia de la traza. La explicación en lenguaje natural la escribe el LLM y la revisa un verificador contra la misma evidencia.

**Detalle:** [`docs/pruebas/casos_de_uso.md`](../pruebas/casos_de_uso.md) (los cinco campos de §3.4 por caso) y un `E2E-n.md` por corrida con la entrada, el plan JSON, las consultas Cypher con sus valores, los datos enviados al LLM, los intentos del verificador y el esperado contra el obtenido.

**Límites que el informe tiene que decir.** (1) El router con `qwen2.5:3b` no siempre pide el mismo conjunto de submódulos (E2E-1 a veces omite SM3); el aprobado exige al menos dos submódulos distintos, no un conjunto exacto. (2) Para E2E-2 y E2E-5 se agregó a la consulta una segunda pregunta (riesgo de RAM, virtualización) para que crucen submódulos. (3) Los tiempos se midieron en una sola máquina.
