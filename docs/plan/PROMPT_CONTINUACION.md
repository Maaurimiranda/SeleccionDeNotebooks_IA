# Estado al 10/11/2026 (noche) y prompt para seguir

Quién lo lea no necesita saber a quién estaba asignada cada tarea: se sigue por dependencias.

## Estado de todas las tareas (11/11, noche)
| Tarea | Estado | Code review |
| --- | --- | --- |
| Validación del plan contra la consigna, arquitectura B | Hecho | — |
| PG3-01 a 04, 06 a 09 (esqueleto, grafo, SM1 a SM3, GRUPO, router; PR #4 de otra persona) | Hecho | **Por hacer:** revisión retroactiva del PR #4 (aprobar `contrato.py`, la excepción de `langchain-ollama`) |
| PG3-05 Cierre de trazabilidad y conteos | Hecho, validado con Neo4j | Corrido y corregido |
| PG3-12 SM4 | Hecho | Corrido; 7 de 10 hallazgos corregidos (quedan prioridad `precio`, motivo armado en el Cypher) |
| PG3-13 Explicador | Hecho | Corrido; corregidos los de corrección. Corregido el parseo de miles (`1.200`). Quedan: redondeo permisivo de enteros, afirmaciones sin cifra ni notebook |
| PG3-11 E2E, casos de uso y pruebas | Hecho: 7 de 7 E2E aprueban | Corrido; 10 de 10 atendidos (filtros en letras y con punto de miles, aviso del video en el LEEME del ZIP, test de E2E con una corrida por caso). Falta el re-review de esas correcciones |
| PG3-15 Registro de correcciones | Hecho (`docs/CORRECCIONES.md`) | Solo documentación: no revisada. Actualizada el 11/11 (SM4 y el explicador ya no son stub) |
| PG3-16 Manual y README | Hecho | Sin revisar; **falta que una persona lo siga desde cero** |
| PG3-10 Diagramas | Hecho (`.drawio` y `.png`) | Sin revisar; Draw.io de escritorio no probado |
| PG3-14 Informe PDF (59 páginas) | Hecho | Sin revisar; **nadie leyó el PDF completo**; usa `mistune` y PyMuPDF (fuera de `RESTRICCIONES.md`) |
| PG3-17 Exportación y ZIP | Hecho: 11 de 12 ítems | Corrido; parcialmente corregido. **Falta** descomprimir en carpeta limpia y probar |
| PG3-18 Infografía | Cubierta con `docs/presentacion/resumen_ejecutivo.pdf` (una página) | — |
| PG3-19 Video | **Por hacer** (persona) | — |
| PG3-20 Lectura cruzada | **Por hacer** (personas) | — |
| PG3-21 a 27 (nivel 2) | No se hacen: el informe lo dice como limitación | — |

**Por hacer del review:** volver a correr `/code-review` sobre los commits `fix(...)` (`81417ff`, `539ccae`, `fd535ef`, `8cad4eb`) y revisar el PR #4.
**Por hacer de verificación:** tiempos de los E2E en otra máquina; seguir el manual desde cero; descomprimir el ZIP y correr E2E-1 (el 11/11 se descomprimió y pasan los 182 tests offline; falta E2E-1 con Neo4j y Ollama); al volver a correr con Neo4j, actualizar los «171 tests» de `docs/informe/08_pruebas.md`, `09_evaluacion.md` y `docs/pruebas/funcionales.md` (hoy son 182) y rehacer el PDF; leer el PDF y confirmar nombres (README: «Olea, Facundo», comisión 5K09, «Luconi Furque»).

## Prompt para otra persona (o para otra sesión de IA)

```text
Seguís el trabajo del "Asistente experto para la selección de notebooks" (Grupo 2, UTN FRM; entrega viernes 13/11/2026 en Grupo_2_PG3_ProyectoFinal.zip). Da igual a quién estaba asignada cada tarea: seguí por dependencias.

1. Leé en este orden: CLAUDE.md, docs/ARQUITECTURA.md, docs/RESTRICCIONES.md, docs/plan/PLAN_PG3.md, docs/plan/PROMPT_CONTINUACION.md (el estado), y el issue de cada tarea en docs/plan/issues/PG3-NN.md. La consigna es docs/consigna/ConsignaPG3.md. Las decisiones están en docs/INCONSISTENCIAS_CONTEXTOS.md (D-01 a D-13).
2. Reglas que no se negocian: Neo4j maneja la verdad y el LLM solo interpreta (router) y explica (explicador); consultas Cypher fijas, de solo lectura salvo SM1.registrar_pedido y aclarar_pedido (nivel 2); cada submódulo es un paquete entrada -> servicio -> repositorio + esquemas y no importa a otros; la incertidumbre se conserva ({min,max}, desconocida, indeterminado); literales de D-06 sin tildes; pruebas con unittest (no pytest); ninguna credencial en archivos versionados (todo va en .env); no instalar nada fuera de RESTRICCIONES.md.
3. Entorno: Python 3.14, Neo4j 5.26 local (bolt://localhost:7687, base neo4j; cargar con `python -m scripts.cargar_grafo`, que BORRA la base), Ollama con qwen2.5:3b (`ollama serve`). Copiá .env.example a .env y poné NEO4J_PASSWORD vos; nunca lo escribas en un archivo versionado. Tests: `python -m unittest`; con modelo: `PG3_TEST_LLM=1 python -m unittest tests.test_router tests.test_explicador`.
4. Trabajá la lista "Pendiente" de docs/plan/PROMPT_CONTINUACION.md en orden. Para cada tarea: una rama pg3-NN-descripcion, tests, `/code-review`, una nota en docs/sesiones/AAAA-MM-DD_Apellido_PG3-NN_tema.md (plantilla en docs/sesiones/README.md; para alguien que no estuvo) y un PR a main revisado por otra persona. Mensajes de commit en imperativo, con tipo y área (feat(sm4): ...), y sin trailer de coautoría de IA.
5. Verificá antes de decir que algo está hecho: corré los tests y, para los E2E, controlá contra lo que dice el grafo, no contra el texto del LLM. Informá con honestidad lo que no pudiste verificar.
6. Si algo no se puede resolver con las tecnologías permitidas, o hay que decidir algo que es del grupo, frená y preguntá.
```
