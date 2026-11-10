# Explicador común: prompt, verificador y plantilla fija · Miranda · 2026-11-10 · PG3-13

## En tres líneas
- `asistente/explicador.py` ya no es un stub: el LLM redacta con `prompts/explicacion.txt`, un **verificador** (controles a–h de D-07 §6) revisa cada respuesta contra la evidencia, regenera hasta 2 veces y, si no pasa, sale una **plantilla fija** armada en código.
- Con `qwen2.5:3b` el verificador **corta lo inventado** (cifras, modelos, reglas, alertas ajenas, rangos reducidos a un número), pero **no garantiza que la respuesta sea buena**: el modelo chico a veces recomienda la notebook equivocada o contradice un estado. Esto es lo que más falta ajustar (ver «Qué queda»).
- 35 tests offline en `tests/test_explicador.py` (uno por control) y una prueba con LLM (`PG3_TEST_LLM=1`). Toda la suite: 151 tests en verde.

## Qué cambió
| Archivo | Qué tiene ahora |
| --- | --- |
| [`asistente/explicador.py`](../../asistente/explicador.py) | `verificar`, `plantilla_fija`, `explicar` (genera, verifica, regenera) |
| [`prompts/explicacion.txt`](../../prompts/explicacion.txt) | El prompt común en voseo, ≤ 150 palabras, con `{evidencia}` y `{correcciones}` |
| [`tests/test_explicador.py`](../../tests/test_explicador.py) | Controles a–h, plantilla, regeneración, prompt y la prueba con LLM |
| [`tests/comun.py`](../../tests/comun.py) | `LLMFalso.texto` devuelve vacío: el explicador no lo acepta y sale la plantilla fija |

## Cómo funciona (para alguien que no estuvo)
1. El orquestador junta la evidencia común (`pedido`, `SM2`, `SM4`…, `advertencia`). `explicar` se la pasa al LLM **compactada** (reglas repetidas juntas, listas largas cortadas a 12 filas: `qwen2.5:3b` tiene poco contexto) y guarda el original para verificar.
2. `verificar(respuesta, evidencia)` devuelve la lista de problemas. Controles:
   (a) cada cifra está en la evidencia (con redondeo, coma o punto, y grado como porcentaje) y, si la oración habla de **una sola** notebook, es un dato de esa notebook o del pedido;
   (b) cada `Notebook_X` y cada regla existen (también cazan «Notebood_G»);
   (c) cada alerta está en la notebook que la tiene;
   (d) ≤ 180 palabras y no vacía;
   (e) está la advertencia, literal;
   (f) un rango no se da como valor intermedio ni con un solo extremo;
   (g) pedido `indeterminado`: no se nombra un perfil;
   (h) los estados, comparados sin tildes, son los de la evidencia (decir «Descartada» alcanza si el grafo dice «Descartada (excluyente incumplido)»).
3. Si hay problemas, se vuelve a pedir pasando los problemas y la respuesta anterior. Tras `MAX_REGENERACIONES = 2` sale `plantilla_fija` (`origen_respuesta = "plantilla_fija"`).
4. La **advertencia la agrega el código** si el modelo no la copió (el modelo chico casi nunca la copia literal). Se cuenta dentro de las 180 palabras.

## Decisiones y por qué
- **El verificador es genérico:** recorre la evidencia sin conocer la forma de cada submódulo, así que un submódulo nuevo no lo rompe. Alternativa descartada: un verificador por submódulo (lo que había en SM2 y SM4).
- **La plantilla tiene su propio tope (250 palabras)**, más alto que el del LLM, y pone SM4 primero: si hay que recortar, se recorta por líneas, nunca se cambia un dato.
- **Sin ejemplo en el prompt:** con un ejemplo («la Notebook_X queda en primer lugar») el modelo lo copiaba tal cual.

## Cómo probarlo
```bash
python -m unittest tests.test_explicador                  # 35 offline
PG3_TEST_LLM=1 python -m unittest tests.test_explicador   # con Ollama y qwen2.5:3b (~30 s)
```

## Qué queda y dudas
- **Control de recomendación (falta):** con `qwen2.5:3b`, para req_01 dijo «Te recomiendo la Notebook_X» (fuera de presupuesto). Ninguno de a–h lo corta porque la oración no trae cifras ni estados. Idea: si una oración con un verbo de recomendar (`recomiend*`, `conviene`) nombra **una** notebook, esa notebook tiene que estar en `ranking` (`puesto`) o tener estado `Recomendada*` y no ser fuera de presupuesto (`excedente_presupuesto_pct > 0`); saltear las oraciones con «no».
- **Afirmaciones que contradicen el dato** («los parámetros están validados» cuando son `sin validar`) tampoco se cortan. Con `llama3.1:8b` la redacción mejora pero también inventa relaciones («23.02 es menor que 49.58»). Decisión para el grupo: ¿probar `qwen2.5:7b` (D-05 lo permite, pero colgaba la PC de Luconi)?
- **`num_ctx` de Ollama:** la evidencia de E2E-9 compactada pesa ~5,7 mil caracteres. Si hay cortes raros, subir `num_ctx` en `asistente/llm.py`.
- **Orquestador:** si el plan pide la misma intención para dos modelos (E2E-2: `SM4.explicar_notebook` para la M y para la G), la segunda evidencia **pisa** a la primera (`evidencia[sm][corta] = ...`). Hay que unir las listas `notebooks`. Los tests lo simulan en `evidencia_de`.
- **Dueña del archivo:** el explicador es de Luconi (PG3-13): ella revisa este PR. **No se corrió `/code-review`** sobre esta tarea.
