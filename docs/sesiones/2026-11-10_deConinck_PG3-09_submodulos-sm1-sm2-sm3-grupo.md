# Submódulos SM1, SM2, SM3 y GRUPO en el contrato · de Coninck · 2026-11-10 · PG3-03, PG3-04, PG3-07 y PG3-09

## En tres líneas
Los cuatro submódulos que no dependen de SM4 ya responden con datos reales del grafo: el pedido interpretado (SM1), el riesgo de RAM y la virtualización (SM2), la búsqueda y la ficha (SM3), y la traza de reglas y los parámetros (GRUPO). Cada uno tiene la misma forma de cuatro capas, sus fixtures con filas reales y tests offline y contra Neo4j. **Olea y Miranda:** el código de SM1 y SM2 es de ustedes; revísenlo como si fuera un PR.

## Qué cambió
| Paquete | Intenciones | Consultas |
| --- | --- | --- |
| [sm1/](../../asistente/submodulos/sm1/) | `SM1.interpretacion_pedido` | L1 (bloque 13), con `grado_min`/`grado_max` por D-09 |
| [sm2/](../../asistente/submodulos/sm2/) | `SM2.riesgo_ram`, `SM2.virtualizacion` | C2 y C1 del bloque 11, portadas a `ev.*` y sin `MERGE` |
| [sm3/](../../asistente/submodulos/sm3/) | `SM3.buscar`, `SM3.ficha` | Unificada (3 órdenes) y por modelo, ahora **filtradas por el pedido** |
| [grupo/](../../asistente/submodulos/grupo/) | `GRUPO.traza_reglas`, `GRUPO.parametros` | L3 (más validación y fuente) y L4 (etiquetas difusas y `Parametro`) |

Tests: [test_sm1.py](../../tests/test_sm1.py), [test_sm2.py](../../tests/test_sm2.py), [test_sm3.py](../../tests/test_sm3.py), [test_grupo.py](../../tests/test_grupo.py). Informe: [05_sm1](../informe/05_sm1.md), [05_sm2](../informe/05_sm2.md), [05_sm3](../informe/05_sm3.md) y [05_base_conocimiento](../informe/05_base_conocimiento.md).

## Cómo funciona (para alguien que no estuvo)
Cada paquete tiene cuatro capas, y cada una llama solo a la de abajo:

- `entrada.py` («controlador» del módulo): `ejecutar(intencion, parametros, grafo)` valida lo barato (por ejemplo, que haya pedido o que el peso máximo no sea de 50 kg) y despacha a la función del servicio. Si falta algo, lanza `Aclaracion` y no consulta el grafo.
- `servicio.py`: pide las filas al repositorio y arma la evidencia. **No calcula ni decide:** redondea a 3 decimales, arma rangos `{min, max}`, deja `desconocida` intacta y pega la notebook a cada alerta.
- `repositorio.py`: el diccionario `CONSULTAS` con el Cypher fijo y funciones que llaman a `grafo.leer`. Ahí viven las reglas.
- `esquemas.py`: la forma de los parámetros y de la evidencia, como `TypedDict` de la biblioteca estándar. Pydantic queda solo para la API.

Ejemplo, con `SM2.riesgo_ram` para Notebook_G en `req_01`:
- La consulta C2 lee la `Evaluacion` de ese par. Como la ampliabilidad de G es desconocida, el grafo guardó dos `Lectura` (peor y mejor caso).
- El servicio devuelve `riesgo: {"min": 49.58, "max": 81.46}`, `indice_ampliabilidad: "desconocida"`, las reglas FZ-R1..R4 con su escenario y fuerza, y las alertas REN-R10 y FZ-R7, cada una con `"notebook": "Notebook_G"`.

## Decisiones y por qué
- **SM2 lee el excluyente de la evaluación** (`ev.excluyente_virtualizacion`) en lugar de recalcularlo como el C1 del bloque 11. Es el mismo dato, sin escritura, y hay un test que lo compara contra la CPU de cada notebook.
- **Filtro `tipo_ram`:** usa `RAM.tipo`, que en el grafo vale `ampliable`, `soldada`, `mixta` o `desconocida`. Por eso se agregó `mixta` a la lista.
- **SM3, conflicto entre dos criterios de PG3-09:** el issue pide «la X aparece con grado de GPU 0,74» y «orden descendente por adecuación gráfica», pero con el límite de 5 resultados la X (0,844, la más baja para VIRT) queda afuera. Se prueba con el filtro `dedicada: true`, donde la X aparece con 0,74 y el orden se cumple. **Ramiro / grupo:** ¿alcanza o preferimos otro orden para «grafica»?
- **SM3, orden `mixta`:** suma la adecuación gráfica y la de movilidad dentro del `ORDER BY` de Cypher (las nulas cuentan 0). Es un orden, no una cifra que se informe.
- **GRUPO.parametros** devuelve las 47 etiquetas difusas y los 30 `Parametro`: 77 en total, todos `'sin validar'`.
- **SM1, rango de D-09:** el canónico todavía no guarda grados como rango (`req_01`, `req_02` y `req_03` tienen grados puntuales). El código está listo y lo cubre un test con filas armadas a mano.

## Cómo probarlo
```bash
python -m unittest tests.test_sm1 tests.test_sm2 tests.test_sm3 tests.test_grupo
python -m scripts.generar_fixtures     # regenera tests/fixtures/ si cambia el grafo
```
Con el grafo cargado:
- `req_01` + `riesgo_ram` de G da [49,58 ; 81,46], `desconocida`, REN-R10 y FZ-R7.
- `virtualizacion` deja a E con `no cumple` y `Descartada (excluyente incumplido)`.
- `req_02` queda `indeterminado`, sin perfiles y con la pregunta pendiente.
- La traza de A cubre SM1 a SM4 (20 reglas).
- `buscar` de `req_03` trae solo a K, con perfil OFI.

## Qué queda y dudas
- SM4 (PG3-12) y el explicador (PG3-13) son de Luconi. Cuando SM4 esté, conviene sumar la explicación L2 (`SM4.explicar_notebook`) al E2E-2.
- No se agregaron alertas de SM2 que el canónico no tiene (REN-R13, D-04): para G salen dos alertas, no tres.
