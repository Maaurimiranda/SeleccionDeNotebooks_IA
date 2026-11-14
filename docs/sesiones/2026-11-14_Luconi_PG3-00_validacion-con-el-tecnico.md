# Validación con el técnico · Luconi · 2026-11-14 · PG3-00

## En tres líneas
El técnico respondió las 16 preguntas que el grafo tenía pendientes (`ConsultaExperto`). Era la corrección de PG2 que seguía abierta: validar los centros y sigmas del modelo difuso y FZ-R2/FZ-R3.
Cargamos sus respuestas en el grafo y validamos las 7 variables que confirma. Sus 9 propuestas de cambio quedan registradas, pero no se aplican.
Estado: hecho. Con Neo4j: CP1 a CP11 en 11 de 11 y 197 tests OK (5 salteados porque piden Ollama). Ningún estado, grado ni ranking cambió.

## Qué cambió
| Archivo | Qué tiene ahora |
| --- | --- |
| `cypher/50_validacion_tecnico.cypher` | Archivo nuevo, 2 sentencias. (1) Las 16 `ConsultaExperto` pasan a `respondida`, con `respuesta` (textual), `fecha_respuesta`, `lectura` y `ajuste_propuesto`. (2) Las etiquetas y el `centros_y_sigmas_*` de las 7 variables confirmadas pasan a `'validado por el tecnico'`. |
| `scripts/verificar_grafo.py` | CP8 espera 26 etiquetas sin validar en 8 variables (antes 47 en 15). |
| `tests/` | Los avisos de SM4 dicen «3 de los 9…», GRUPO cuenta 49 de 77 sin validar, el ZIP lleva 10 `.cypher` y la comparación con el canónico admite las 2 sentencias nuevas. |
| `tests/fixtures/SM4.*`, `GRUPO.*` | Regenerados con Neo4j (`python -m scripts.generar_fixtures`). Solo cambia el estado de validación; el resto es orden de filas. |
| `datos/export/` | Exportación del grafo regenerada (ítem i del ZIP). |
| `docs/pruebas/validacion_tecnico.md` | Las 16 preguntas, las respuestas textuales, la lectura de cada una y qué pasaría si se aplicaran los ajustes. |
| `docs/CORRECCIONES.md` | Fila C-46. C-45 actualizada: los fixtures de Q8 ya se regeneraron contra Neo4j. |
| `docs/informe/` (2, 5, 6, 9, 10 y 11), `docs/MANUAL_DE_USO.md`, `docs/pruebas/funcionales.md` | Dicen que la validación es parcial, en lugar de «nada validado». |
| `docs/informe/Grupo_2_PG3_Informe.pdf`, `docs/presentacion/resumen_ejecutivo.pdf` | Rehechos con `python docs/informe/armar_pdf.py` (59 páginas y 1 página). |

## Cómo funciona (para alguien que no estuvo)
Cada variable difusa (por ejemplo `peso_kg`) tiene etiquetas («liviana», «intermedia», «pesada») definidas por un centro y una sigma, y un `Parametro` `centros_y_sigmas_peso_kg` que las respalda. En PG2 dejamos una `ConsultaExperto` por variable, con la pregunta que había que hacerle al técnico. Ahora guardamos su respuesta ahí mismo.

Si la respuesta coincide con lo que ya tenemos (por ejemplo, la 14: «desde 0,8 la recomiendo sin dudar, entre 0,6 y 0,8 para considerar», que son justo nuestros cortes), la variable pasa a `'validado por el tecnico'`. Si propone otro número (por ejemplo, la 10: «mucha batería es desde 12 h», y nosotros usamos 10), lo anotamos en `ajuste_propuesto` y la variable sigue `'sin validar'`.

Todo lo que cuenta parámetros sin validar lee el grafo, así que se actualizó sin tocar código. CP8 baja a 26. `GRUPO.parametros` da 49 de 77. El aviso de SM4 (consulta Q8) pasa de «Los 9 parametros…» a «3 de los 9 parametros…», porque el técnico validó la adecuación global y el grado de recomendación; queda el excedente de presupuesto.

## Decisiones y por qué
- **No aplicar los 6 ajustes ni los 3 cambios de regla (decisión del grupo, 14/11).** Los probamos en una copia. La autonomía «mucha» desde 12 h baja a la A de `Recomendada (Alta)` 0,785 a `(Media)` 0,734. El peso nuevo cambia el podio de A, H, B a A, B, H. El 5 % de presupuesto sube a la X de 0,534 a 0,602. Son los resultados que cuentan el informe, los E2E y el video. Se descartó aplicarlos ahora: habría que rehacer los esperados de CP1, 3, 5, 6, 7 y 11, los E2E y el informe.
- **Un archivo aparte (`50_…`) en lugar de editar `01_conocimiento.cypher`.** Así 01 a 40 siguen iguales al canónico de PG2, y la comparación de sentencias (`tests/test_contar_grafo.py`) solo tiene que admitir 2 sentencias nuevas y rastreables.
- **El literal `'validado por el tecnico'`.** D-06 solo define `'sin validar'`. Elegimos uno sin tildes, como el resto de los literales. Si el grupo prefiere otro, se cambia en un solo lugar.
- **No se tocó `contrato.py`.** La `ADVERTENCIA` general («Los parametros difusos y los umbrales del sistema estan sin validar…») sigue siendo cierta para la mayoría de los parámetros. Si se quiere decir «la mayoría», el cambio es de Miranda (CLAUDE.md).
- **Lo que el técnico no completó no se marca.** Las tablas de parámetros fijos, léxico, gamas y reglas quedaron en blanco: siguen `'sin validar'`.

## Cómo probarlo
```
python -m scripts.cargar_grafo         # borra la base y carga 00 a 50 (103 sentencias)
python -m scripts.verificar_grafo      # 11/11 OK; CP8 da (26, 8)
python -m unittest                     # 197 tests, OK (5 salteados sin Ollama)
```
En Neo4j Browser: `MATCH (c:ConsultaExperto) RETURN c.id, c.lectura, c.ajuste_propuesto`.

## Qué queda y dudas
- **Aplicar las 9 propuestas**, con el grupo: las 3 de regla tocan SM1 (Olea), SM2 (Miranda) y SM3 (de Coninck). La de FZ-R3 es la que pidió la profesora.
- **El técnico duda de que el módulo de RAM cueste 30 USD** (`P_COSTO_MODULO_RAM_USD`): conviene revisar el precio.
- **No se corrieron los E2E con Ollama.** Las explicaciones de SM4 ahora copian «3 de los 9…»; los tests con el explicador real (`PG3_TEST_LLM=1`) no se corrieron.
