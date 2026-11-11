# Exportación del grafo, datos de ejemplo y ZIP · Miranda · 2026-11-11 · PG3-17

## En tres líneas
- `scripts/exportar_grafo.py` exporta el grafo a CSV (343 nodos, 683 relaciones) y arma los datos de ejemplo; `scripts/armar_zip.py` arma `dist/Grupo_2_PG3_ProyectoFinal.zip` con una carpeta por ítem a–l de la consigna §4.
- El ZIP **se niega a armarse si encuentra una credencial** (contraseñas distintas del placeholder o URIs de Aura).
- Hoy el ZIP tiene 9 de los 12 ítems: **faltan b) diagramas, k) video y l) infografía**, que dependen de PG3-10, 19 y 18. El `LEEME.md` los marca «pendiente».

## Qué cambió
| Archivo | Qué tiene ahora |
| --- | --- |
| [`scripts/exportar_grafo.py`](../../scripts/exportar_grafo.py) | `datos/export/nodos.csv` y `relaciones.csv` (Cypher estándar, sin APOC), `datos/salida_pi2.csv`, `consultas_ejemplo.csv`, `traza_ejemplo.jsonl` |
| [`scripts/armar_zip.py`](../../scripts/armar_zip.py) | El ZIP, el `LEEME.md` y el control de credenciales (`--verificar` solo controla) |
| [`datos/`](../../datos/) | Lo exportado, versionado para poder revisarlo |

## Cómo funciona (para alguien que no estuvo)
La exportación lee con el driver: cada nodo sale con su `elementId`, sus labels y sus propiedades en JSON; cada relación, con origen, tipo, destino y propiedades. No hace falta APOC. `armar_zip` recorre cada ítem (carpetas o archivos), excluye `.env`, `.venv`, `trazas/`, `__pycache__`, `.git` y `.claude`, busca credenciales en los textos y escribe el ZIP.

## Cómo probarlo
```bash
python -m scripts.exportar_grafo         # necesita Neo4j con el grafo cargado
python -m scripts.armar_zip --verificar  # credenciales y qué ítems faltan
python -m scripts.armar_zip              # arma dist/Grupo_2_PG3_ProyectoFinal.zip
```

## Qué queda y dudas
- **Prueba de reproducción** (descomprimir en una carpeta limpia, seguir el manual, cargar el grafo y correr E2E-1): **no se hizo**. Hacerla antes de entregar.
- **Dump de Neo4j** (`neo4j-admin database dump`): no se agregó; los `.cypher` y los CSV reproducen el grafo.
- El control de credenciales es por patrón; no reemplaza una lectura final del ZIP.
- Los `elementId` cambian si se recarga el grafo: el CSV sirve para leer, no como clave estable.
