# Informe ejecutivo final en PDF · Miranda · 2026-11-11 · PG3-14

## En tres líneas
- Se escribieron las secciones que faltaban del informe (portada, resumen, arquitectura, evaluación, trazabilidad, conclusiones y referencias) y se armó `docs/informe/Grupo_2_PG3_Informe.pdf` (59 páginas, 12 secciones y 5 anexos). El resumen de una página (`docs/presentacion/resumen_ejecutivo.pdf`) cubre el ítem l).
- Las cifras salen de las corridas de `docs/pruebas/` y de las notas de sesión.
- **El PDF no fue revisado por una persona**: leerlo antes de entregar.

## Qué cambió
| Archivo | Qué tiene ahora |
| --- | --- |
| `docs/informe/01_portada.md` a `12_referencias.md` | Las 12 secciones de la consigna §5 |
| `docs/informe/armar_pdf.py`, `figuras.py` | Cómo se arma el PDF y las dos figuras de página vertical |
| `docs/informe/Grupo_2_PG3_Informe.pdf` | El informe, con portada, índice, numeración y los anexos A a E |
| `docs/presentacion/resumen_ejecutivo.pdf` | La sección 02 en una página |

## Decisiones y por qué
- **PDF con `mistune` y PyMuPDF:** no había otra herramienta instalada. **No están en `RESTRICCIONES.md` ni en `requirements.txt`**: el grupo tiene que aceptarlo como excepción o volver a armar el PDF desde Google Docs o Word (lista verde). No se usan en el sistema, solo para armar el PDF.
- Se unificaron las cifras viejas de `06` y `11_reflexion` con la medición final (router 28 de 31 intenciones, 30 de 31 en resultado).

## Cómo probarlo
```bash
python docs/informe/figuras.py
python docs/informe/armar_pdf.py
```

## Qué queda y dudas
- **Hallazgo dicho en el informe:** en E2E-2 la respuesta dio como riesgo de RAM de la G un 52,9 %, que es su adecuación global. El verificador no lo corta y el E2E aprueba igual porque decide el grafo.
- **Router:** seis de las 31 consultas son casi iguales a ejemplos del prompt; descontándolas, el acierto de intenciones es 19 de 22 (86 %).
- **Nombres:** se tomaron del README («Olea, Facundo», comisión 5K09, «Luconi Furque»): confirmarlos.
- `CORRECCIONES.md` todavía dice que SM4 y el explicador son stub y cita 24 de 25: el PDF lo marca con una nota.
