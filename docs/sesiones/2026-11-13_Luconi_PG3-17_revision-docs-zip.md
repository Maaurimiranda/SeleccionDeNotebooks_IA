# Revisión de la documentación del ZIP reproducible · Luconi · 2026-11-13 · PG3-17

## En tres líneas
Se revisó la rama `pg3-17-zip-reproducible` en busca de inconsistencias entre el código, el manual, el README y la nota de sesión del 12/11. El código estaba bien. Se corrigieron tres datos en la documentación y la nota del 12/11 ahora lista dos pendientes que faltaban. No se tocó código.

## Qué cambió
| Archivo | Qué tiene ahora |
| --- | --- |
| [docs/MANUAL_DE_USO.md](../MANUAL_DE_USO.md) §9 | La cuenta de pruebas pasó de 182 a **186** (29 salteadas sin Neo4j ni Ollama). Antes contradecía la nota del 12/11 |
| [README.md](../../README.md) §8 | Ya no dice que `docs/pruebas/` tiene solo los conteos: también tiene los `E2E-n.md`, `resultados_e2e.md` y `funcionales.md` |
| [Nota del 12/11](2026-11-12_Luconi_PG3-17_zip-reproducible.md) | (1) Corrige el ejemplo de `--hasta 5`. (2) Marca el E2E-1 desde el ZIP como criterio de aceptación pendiente. (3) Aclara que `e_codigo_fuente/` no trae `docs/pruebas/` ni `datos/`. (4) Suma `docs/informe/02_resumen.md` a los archivos que todavía dicen «171 tests» |

## Cómo funciona (para alguien que no estuvo)
`scripts/cargar_grafo.py` carga los archivos `cypher/NN_*.cypher` cuyo prefijo NN sea menor o igual que `--hasta`. El primero, `00_esquema.cypher`, **borra la base**. La nota decía que `--hasta 5` deja la lista vacía y frena, pero en el proyecto real `00`, `01` y `02` son ≤ 5: con `--hasta 5` se borra la base y se cargan esos tres bloques. La protección nueva (`comprobar_archivos()`) solo actúa cuando no hay nada para cargar, por ejemplo si falta `cypher/`.

## Decisiones y por qué
- **No se cambiaron las cifras del informe** (`02_resumen`, `08`, `09`, `funcionales`). Se actualizan junto con el PDF, después de unir la rama `pg3-00-validacion-entidad-estado`, que suma tests. Así se recuenta una sola vez.
- **No se agregó `docs/pruebas/` a `e_codigo_fuente/`.** Para reproducir el sistema no hace falta, y ya está en `c_casos_de_prueba/`. Queda anotado como duda para el grupo.

## Cómo probarlo
```powershell
.venv\Scripts\python.exe -m unittest discover -s tests -t .   # sin Neo4j: Ran 186 tests, OK (skipped=29)
python -m scripts.armar_zip --verificar                       # 267 archivos en 11 de 12 ítems. Sin credenciales.
```

## Qué queda y dudas
- Correr el E2E-1 desde el ZIP descomprimido, con Neo4j y Ollama.
- `README.md` es de Miranda: revisa este cambio en el PR.
- Duda menor: `tests/test_armar_zip.py` corre el `main()` real. Si un archivo del repo tiene la contraseña del `.env` de quien corre el test, el test falla por un motivo que no tiene que ver con lo que prueba.
