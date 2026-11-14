# Pendientes y cifras de pruebas · Miranda · 2026-11-13 · PG3-00

## En tres líneas
Se unificó el conteo de pruebas en 197 en el informe, en `docs/pruebas/funcionales.md` y en el PDF, y se rehízo el PDF. En `PROMPT_CONTINUACION.md` quedaron solo cuatro pendientes para entregar; todo lo demás pasó a una sección opcional, fuera del alcance. Es solo documentación.

## Qué cambió
| Archivo | Qué tiene ahora |
| --- | --- |
| [`docs/informe/02_resumen.md`](../informe/02_resumen.md), [`08_pruebas.md`](../informe/08_pruebas.md), [`09_evaluacion.md`](../informe/09_evaluacion.md) | 197 pruebas, corrida offline del 13/11, 29 salteadas |
| [`docs/pruebas/funcionales.md`](../pruebas/funcionales.md) | 197 pruebas; 29 se saltean sin Neo4j ni Ollama |
| `docs/informe/Grupo_2_PG3_Informe.pdf`, `docs/presentacion/resumen_ejecutivo.pdf` | Rehechos con `python docs/informe/armar_pdf.py` |
| [`docs/plan/PROMPT_CONTINUACION.md`](../plan/PROMPT_CONTINUACION.md) | Secciones Hecho, Pendiente (4 ítems) y Opcional |

## Cómo funciona (para alguien que no estuvo)
Los 4 pendientes son: el video (PG3-19), correr E2E-1 desde el ZIP descomprimido, mantener las cifras y el PDF al día, y leer el PDF confirmando los nombres. Lo opcional agrupa revisiones, verificaciones, defectos conocidos y limpieza que el informe ya declara como limitación o que no bloquean la entrega.

## Decisiones y por qué
- **197, no 193.** El informe tenía 193 (cuenta de la rama del PR #5, sin los 4 tests del PR #7); con todo unido son 197, como ya decía el manual §9.
- **Se quitó del informe la mención a la corrida con Neo4j de 171 tests**: era de otra versión del código. Alternativa descartada: dejarla como histórica.
- `funcionales.md` conserva su fecha del 11/11 y el CP1 a CP11 de esa corrida; solo cambió el conteo de `unittest`.

## Cómo probarlo
```bash
python -m unittest discover -s tests -t .   # 197 con las dependencias instaladas
```
En esta sesión no lo corrí: el 197 sale del manual §9 y de la nota de Luconi del 12/11.

## Qué queda y dudas
- Los 4 pendientes de `PROMPT_CONTINUACION.md`. Nadie leyó el PDF rehecho.
- Los cambios están sin commitear y sobre `main`; según `CLAUDE.md` va una rama y un PR revisado.
