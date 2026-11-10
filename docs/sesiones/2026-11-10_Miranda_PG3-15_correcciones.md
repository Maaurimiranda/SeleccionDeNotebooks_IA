# Registro de correcciones (consigna §3.1) · Miranda · 2026-11-10 · PG3-15

## En tres líneas
- Se armó [`docs/CORRECCIONES.md`](../CORRECCIONES.md), el anexo del informe que documenta lo que se revisó y corrigió en el proyecto: 43 correcciones repartidas en los seis aspectos que pide la consigna (§3.1), más 5 verificaciones que no necesitaron cambios.
- Cada fila dice qué estaba mal, dónde quedó la corrección (archivo o commit), cómo se comprobó y en qué estado está. De las 43: 28 están corregidas, 11 corregidas en parte, 2 sin prueba que las ejercite y 2 abiertas.
- Es solo documentación: no se tocó código, tests ni `cypher/`. Falta sumar lo que aparezca en los E2E (PG3-11) y en la revisión del PR #4.

## Qué cambió
| Archivo | Qué tiene ahora |
| --- | --- |
| [`docs/CORRECCIONES.md`](../CORRECCIONES.md) | Resumen por aspecto, tabla de 43 correcciones, 5 verificaciones sin cambios, las decisiones tomadas y no implementadas, lo pendiente y los límites del registro |
| esta nota | La explicación para quien no estuvo |

## Cómo funciona (para alguien que no estuvo)
**Qué pide la consigna.** La consigna de PG3 (la actividad final de la materia) pide, en su punto §3.1, revisar seis cosas y **documentar las correcciones**: coherencia conceptual (A1), consistencia terminológica (A2), funcionamiento de las consultas (A3), de las reglas (A4), de los componentes difusos (A5) y de la integración con el LLM (A6). El registro usa esos seis nombres como códigos A1 a A6.

**De dónde sale el contenido.** Casi todo ya estaba dicho en [`INCONSISTENCIAS_CONTEXTOS.md`](../INCONSISTENCIAS_CONTEXTOS.md), la lista de lo que no coincidía entre los cinco contextos del grupo. Allí hay dos grupos de entradas: las S-01 a S-06 (errores mecánicos ya corregidos) y las D-01 a D-13 (decisiones del grupo). El registro las convierte en filas, pero **una fila por corrección y no por decisión**: una decisión puede corregir tres cosas (D-05 dio tres filas) o ninguna en el código (D-08 no dio ninguna, porque el pedido nuevo todavía no está hecho).

**Qué se sumó.** Se leyeron las notas de sesión de PG3-01, 05, 06 y 09 y el historial de `git`. De ahí salieron las correcciones hechas durante PG3: los dos arreglos de D-06 en `cypher/` (tres sentencias con `'provisional'` que pasan a `'sin validar'`, y REC-R5, la regla que suma peso a la prioridad del comprador, que ignoraba `grafica`); el esperado equivocado del caso CP11; el cambio de modelo a `qwen2.5:3b` y de `requests` a LangChain; la fuente de las reglas que no existía en el grafo; y la X de SM3.

**Un ejemplo.** La fila C-26 cuenta un conflicto entre dos criterios del issue PG3-09. Uno pedía que la notebook X apareciera con grado de GPU 0,74; el otro, orden descendente por adecuación gráfica. Pero SM3 devuelve a lo sumo 5 resultados, y la X (la peor en gráfica para el pedido `req_01`) quedaba afuera. Se decidió probar el criterio con el filtro `dedicada: true`, donde la X sí aparece. La fila cita el test y los datos reales que lo respaldan.

**Cómo se lee el estado.**
- *Corregida:* el cambio está hecho y tiene una verificación citada.
- *Parcial:* se hizo una parte (por ejemplo, el texto de los contextos) y otra quedó diferida (por ejemplo, el código).
- *Sin verificar:* el cambio está, pero ninguna prueba lo ejercita (REC-R5 con prioridad `grafica`: ningún pedido cargado la usa).
- *Abierta:* se detectó y no se corrigió.

## Decisiones y por qué
- **Contar cada fila una sola vez, bajo su aspecto principal.** Alternativa descartada: marcar varios aspectos por fila, que habría inflado el resumen. Si una fila toca otro aspecto, el texto lo dice.
- **Marcar lo diferido como Parcial y no como Corregida.** Varias decisiones (D-03, D-04, D-09, D-10) arreglaron los textos y dejaron el código para los issues de nivel 2. Presentarlas como cerradas sería engañoso; la sección «Decisiones tomadas y no implementadas» las junta con su issue.
- **No reproducir lo que necesita Neo4j u Ollama.** Esas cifras (CP1 a CP11 en 11/11, los conteos 343 nodos y 683 relaciones, el acierto del router) se citan de las notas, marcadas como «no reproducido». Lo que sí se contrastó se lista en «Límites de este registro».
- **Citar commits de ramas sin unir con †.** PG3-05 y la validación del plan viven en las ramas `pg3-05-cierre-trazabilidad` y `docs/validacion-plan-pg3`. Esta rama sale de `main`, así que esos hashes pueden cambiar al unirse.

## Cómo probarlo
```bash
grep -c "^| C-" docs/CORRECCIONES.md    # 43
grep -c "^| V-" docs/CORRECCIONES.md    # 5
# los tests offline que no importan LangChain
python -m unittest tests.test_router tests.test_contrato tests.test_sm1 tests.test_sm2 tests.test_sm3 tests.test_grupo tests.test_estructura
# esperado: Ran 64 tests ... OK (skipped=12)
```
Para cualquier fila, abrir el archivo o el test que cita. Por ejemplo, C-16: `grep -rn "provisional" cypher/` no debe dar resultados.

## Qué queda y dudas
- **Hallazgo nuevo, abierto (C-20):** en `docs/contexto/` quedó `CONTEXTO_SM3_PG3.md`, una copia vieja del contexto de SM3 que conserva los errores que S-01, S-04 y S-05 habían arreglado en la otra. Nadie la referencia. Proponemos eliminarla; es de de Coninck.
- **Abierto (C-27):** el orden de las filas `peor` y `mejor` en `SM2.riesgo_ram` no está fijado. No afecta a la evidencia (el servicio ordena), sí a los fixtures. Es de Miranda.
- **Sin verificar (C-28 y C-30):** REC-R5 con `grafica` y REC-R9 con `precio` están aplicadas, pero ningún pedido cargado las usa (`req_04` y `req_05` no existen). Luconi debe revisar el cambio de REC-R5 en `cypher/40_sm4.cypher`.
- **Pendiente de agregar:** los bugs de los E2E (PG3-11); la revisión del PR #4 (`contrato.py`, la excepción de `langchain-ollama` en `RESTRICCIONES.md` §8 y `CLAUDE.md`); y las correcciones del explicador y el verificador cuando PG3-12 y PG3-13 salgan del stub.
- **No se verificó** nada que requiera Neo4j u Ollama, ni se pudo correr `test_orquestador` ni `test_api` (falta `langchain_core` en este entorno).
- **Pregunta para el grupo:** ¿el registro va como anexo tal cual, o PG3-14 prefiere una versión más corta (solo el resumen y las filas Corregida)?
