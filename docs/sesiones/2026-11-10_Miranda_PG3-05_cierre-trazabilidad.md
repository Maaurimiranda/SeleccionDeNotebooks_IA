# Cierre de PG3-02 y PG3-04: origen del conocimiento y conteos · Miranda · 2026-11-10 · PG3-05

## En tres líneas
- La traza de reglas (`GRUPO.traza_reglas`) ahora dice **de dónde sale** cada dato: los parámetros que respaldan cada regla, la consulta pendiente al técnico que los valida y la fuente del precio y de la autonomía de la notebook. Lo que el grafo no tiene sale como `"no registrada"`.
- Se probó **sin Neo4j** que cortar el canónico en `cypher/` no cambió su contenido: de 101 sentencias, difieren 4, que son los arreglos de D-06.
- **Validado contra Neo4j 5.26** (instancia local nueva): las consultas de origen funcionan con datos reales, se regeneraron los fixtures de GRUPO, la regresión CP1–CP11 da 11/11, los 88 tests pasan con la base (1 se saltea: el del router con Ollama) y los conteos coinciden (343 nodos y 683 relaciones).

## Qué cambió
| Archivo | Qué tiene ahora |
| --- | --- |
| [`grupo/repositorio.py`](../../asistente/submodulos/grupo/repositorio.py) | Tres consultas nuevas: `origen_reglas`, `origen_notebook` y `origen_parametros` |
| [`grupo/servicio.py`](../../asistente/submodulos/grupo/servicio.py) | Arma `evidencia.origen` (traza) y el `origen` de cada parámetro; `"no registrada"` si falta |
| [`grupo/esquemas.py`](../../asistente/submodulos/grupo/esquemas.py) | Las formas de ese origen |
| [`scripts/contar_grafo.py`](../../scripts/contar_grafo.py) | `--sentencias` (sin Neo4j), `--guardar` y `--comparar` (con Neo4j) |
| [`scripts/cargar_grafo.py`](../../scripts/cargar_grafo.py) | `--canonico`: carga el canónico entero hasta el bloque 10 |
| [`tests/test_grupo.py`](../../tests/test_grupo.py), [`tests/test_contar_grafo.py`](../../tests/test_contar_grafo.py) | 7 tests nuevos offline y 1 con grafo (más una aserción nueva en otro) |
| [`docs/pruebas/conteos_grafo.md`](../pruebas/conteos_grafo.md) | El resultado de la comparación de sentencias y lo que falta correr |

## Cómo funciona (para alguien que no estuvo)
**El problema.** La consigna (§3.7) pide poder reconstruir la fuente del conocimiento. Pero en el grafo las `:Regla` **no tienen** una propiedad `fuente`: el origen está repartido en otros nodos. Por eso `traza_reglas` devolvía `fuente: null` en todas las filas de la traza de la A (20 filas, 18 reglas).

**Qué se hizo.** Para cada regla activada se busca qué parámetros la respaldan:
1. si es una regla difusa, el parámetro `centros_y_sigmas_<variable>` de la variable de su **consecuente** (por ejemplo, FZ-R3 → `riesgo_obsolescencia`);
2. cualquier parámetro cuyo `origen` nombra el id de la regla (por ejemplo, «Decision del grupo (REC-R5)»). Se compara con borde de palabra para que REC-R1 no se confunda con REC-R15.

De cada parámetro se informan su `origen`, su estado de validación y la `ConsultaExperto` pendiente que lo va a validar con el técnico. Para la notebook se informan `fuente_precio` y la fuente de la autonomía (`Bateria.fuente`).

**Límites, que el informe tiene que decir:**
- El origen que se muestra es el de los **parámetros** (centros, sigmas, umbrales), no el de la regla misma: el texto de la regla no tiene fuente registrada en el grafo.
- Solo se mira la variable del consecuente, no las del antecedente.
- Las `ConsultaExperto` que validan una `:Regla` directamente (por ejemplo, CE-FZ-R2-R3) todavía no se devuelven.

## Decisiones y por qué
- **Consultas nuevas y aparte, sin tocar L3 ni L4:** así los fixtures reales siguen valiendo y los tests offline no se rompen. Cuando haya Neo4j se regeneran y entran las filas reales.
- **Primero la comparación de sentencias:** un conteo por label no detecta que cambie el contenido de una propiedad y obliga a borrar la base dos veces. Comparar las sentencias una por una es más fuerte, no toca la base y se puede correr en cualquier máquina. Los conteos quedan como verificación complementaria.
- **`"no registrada"` y no un valor inventado.** Es una limitación real del grafo (§3.6), no se esconde.

## Cómo probarlo
```bash
python -m unittest                          # 88 tests; los de Neo4j (15) se saltean sin NEO4J_PASSWORD
python -m scripts.contar_grafo --sentencias # 101 contra 101, difieren 4 (D-06)
```
Con Neo4j (borra la base):
```bash
python -m scripts.cargar_grafo
python -m unittest tests.test_grupo         # incluye los ConGrafo de origen
python -m scripts.generar_fixtures          # regenera los fixtures con las consultas nuevas
```

## Qué queda y dudas
- **Resultado con Neo4j:** en la traza de la A, **14 de las 18 reglas tienen origen** y 4 salen «no registrada»: GM-R3, INT-R11, REC-R4 y REC-R9. Los 77 parámetros tienen origen. La regex de `origen_reglas` funciona con los datos reales.
- **Observación sobre SM2 (de Miranda):** al regenerar los fixtures, `SM2.riesgo_ram` cambió el orden de las filas `peor` y `mejor` entre corridas, porque su consulta ordena por regla y no desempata por escenario. No afecta a los tests, pero los fixtures cambian sin que cambie el grafo. No se tocó; conviene agregar `escenario` al `ORDER BY`. Esos dos fixtures quedaron como estaban.
- **Tamaño de la evidencia:** `GRUPO.parametros` ya pesaba ~11,7 mil caracteres y el `origen` de cada parámetro suma unos 4 mil más. Con `qwen2.5:3b` el explicador (PG3-13) tiene que resumirla, no pasarla entera.
- **Pendientes de la revisión del PR #4 (tuyos, Miranda):** aprobar `contrato.py`, confirmar la excepción de `langchain-ollama` en `RESTRICCIONES.md` §8 y los cambios de `CLAUDE.md`.
- **Aviso al dueño:** `grupo/` es de de Coninck; este cambio lo toca, así que él revisa el PR.
- Más adelante: quitar la columna `q.fuente` de L3 (siempre `null`) y mover `NO_REGISTRADA` a `contrato.py`, con el visto bueno de Miranda.
