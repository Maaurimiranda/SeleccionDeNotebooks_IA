# El ZIP se puede correr desde `e_codigo_fuente/` · Luconi · 2026-11-12 · PG3-17

## En tres líneas
Al descomprimir el ZIP de la entrega y seguir el manual desde `e_codigo_fuente/`, `cargar_grafo` borraba la base y cargaba 0 sentencias sin dar error, y fallaban 11 tests. La causa era que esa carpeta no tenía `cypher/`, `docs/cypher/` ni `tests/`. Ahora `e_codigo_fuente/` es un proyecto completo por sí solo, y `cargar_grafo` frena antes de borrar si no tiene qué cargar. Se probó en una carpeta limpia: carga 101 sentencias, da 11/11 en la regresión y pasan 186 tests.

## Qué cambió
| Archivo | Qué tiene ahora |
| --- | --- |
| [scripts/cargar_grafo.py](../../scripts/cargar_grafo.py) | `comprobar_archivos()`: si no hay ningún `cypher/NN_*.cypher` (o falta el canónico, con `--canonico`), sale con código 1 **antes de conectarse a Neo4j** |
| [scripts/armar_zip.py](../../scripts/armar_zip.py) | El ítem e) suma `cypher/`, `docs/cypher/`, `tests/` y `.env.example`. El LEEME del ZIP aclara que los comandos se corren desde `e_codigo_fuente/`. Tiene una opción nueva, `--salida RUTA.zip` |
| [docs/MANUAL_DE_USO.md](../MANUAL_DE_USO.md) §2.1 | Explica cuál es la «raíz» con Git (el repo clonado) y cuál con el ZIP (`e_codigo_fuente/`) |
| [tests/test_cargar_grafo.py](../../tests/test_cargar_grafo.py) | Nuevo: comprueba que sin archivos `cargar_grafo` sale con error y nunca crea el driver de Neo4j |
| [tests/test_armar_zip.py](../../tests/test_armar_zip.py) | Test nuevo: arma el ZIP en una carpeta temporal, lo descomprime y busca en `e_codigo_fuente/` los 9 `.cypher`, `tests/`, `docs/cypher/` y la configuración (y que no esté `.env`) |

## Cómo funciona (para alguien que no estuvo)
El ZIP de la entrega tiene una carpeta por ítem de la consigna §4 (a–l): `a_informe/`, `e_codigo_fuente/`, `f_scripts_cypher/`, etc. Antes, cada archivo iba a una sola carpeta: el código en `e_`, los Cypher en `f_` y los tests en `c_`. Pero el manual dice «corré los comandos desde la raíz», y la única carpeta con `requirements.txt` era `e_`.

El problema grave estaba en `cargar_grafo`. El script busca `cypher/NN_*.cypher` **relativo a su propia ubicación**, y el primer archivo (`00_esquema.cypher`) es el que borra la base. Si no encontraba ninguno, de todas formas se conectaba, no ejecutaba nada y decía «Listo: 0 sentencias». En el caso real, el profesor habría visto un éxito con un grafo vacío o viejo.

Ahora pasa esto:
1. `main()` llama a `comprobar_archivos()` **antes** de crear el driver de Neo4j. Sin driver no hay sesión, y sin sesión no se puede borrar nada.
2. Si la lista está vacía, sale con `ERROR: ... No se tocó la base` y código 1. Pasa si falta `cypher/` o si `--hasta` deja afuera todos los archivos. Ojo: en el proyecto real, `--hasta 5` **no** frena. Incluye `00_esquema.cypher`, así que borra la base y carga los bloques 00 a 02. Solo un `--hasta` negativo deja la lista vacía.
3. El ZIP repite en `e_codigo_fuente/` lo necesario para correr todo. Las carpetas `c_`, `f_` y `g_` no cambian, así cada ítem se puede revisar por separado.

## Decisiones y por qué
- **Duplicar en vez de mover.** El pedido fue no sacar nada de las demás carpetas por ítem. El ZIP sigue pesando unos 6,8 MB, porque los Cypher y los tests son texto.
- **Se comprueba en `main()` y no adentro de `cargar()`.** Así la comprobación ocurre antes de abrir la conexión. `cargar()` y `cargar_canonico()` quedaron iguales, y otros scripts y tests los siguen usando.
- **`--salida` en `armar_zip`.** Sirve para que el test arme el ZIP en una carpeta temporal sin pisar `dist/`.

## Cómo probarlo
Desde el repo:
```powershell
python -m unittest tests.test_cargar_grafo tests.test_armar_zip   # 8 tests, OK
python -m scripts.armar_zip                                       # 267 archivos en 11 de 12 ítems
```
La prueba real que se hizo el 12/11 (Neo4j 5.26 local, Ollama corriendo):
1. Se descomprimió `dist/Grupo_2_PG3_ProyectoFinal.zip` en una carpeta vacía.
2. Desde `e_codigo_fuente/` se creó `.venv`, se corrió `pip install -r requirements.txt` y se copió el `.env`.
3. `python -m scripts.cargar_grafo` → `Listo: 101 sentencias.`
4. `python -m scripts.verificar_grafo` → `11/11 OK`.
5. `python -m unittest discover -s tests -t .` → `Ran 186 tests ... OK (skipped=5)`. Los 5 salteados son los que piden `PG3_TEST_LLM=1`.
6. Se renombró `cypher/` y se volvió a correr `cargar_grafo` → exit 1, y la base siguió con 343 nodos antes y después.

## Qué queda y dudas
- **Falta cerrar un criterio de aceptación de PG3-17:** correr el E2E-1 desde el ZIP descomprimido (`python -m scripts.correr_e2e E2E-1` desde `e_codigo_fuente/`). Tampoco se corrieron desde ahí los tests con LLM (`PG3_TEST_LLM=1`, son lentos).
- **`e_codigo_fuente/` no trae `docs/pruebas/` ni `datos/`.** `correr_e2e` crea la carpeta que le falta (`mkdir`, no se probó desde el ZIP), así que dejaría los resultados en `e_codigo_fuente/docs/pruebas/` y no junto a los E2E de `c_casos_de_prueba/`. `exportar_grafo` lee las trazas de `docs/pruebas/trazas/`, así que desde el ZIP no las encuentra y no genera `traza_ejemplo.jsonl`. Para reproducir el sistema no hacen falta, pero hay que tenerlo en cuenta si se quiere regenerar la evidencia desde el ZIP.
- **Las cifras de tests en el informe** (actualizado el 13/11, después de unir `main`): `docs/informe/02_resumen.md`, `08_pruebas.md` y `09_evaluacion.md` dicen 193, y el PDF también. Esa cuenta es la de la rama `pg3-00-validacion-entidad-estado` (PR #5), que no incluía los 4 tests de este PR. Con todo unido son **197** (29 salteadas sin Neo4j ni Ollama), y el manual §9 ya lo dice. `docs/pruebas/funcionales.md` sigue en 171. No se tocaron acá: se actualizan junto con el PDF.
- Correr un comando desde una carpeta que no es `e_codigo_fuente/` (por ejemplo `f_scripts_cypher/`) da `ModuleNotFoundError: scripts`, que tampoco toca la base.
- **Revisor:** Miranda, porque `scripts/` es suyo.
