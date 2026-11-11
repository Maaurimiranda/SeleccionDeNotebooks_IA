# Estado al 10/11/2026 (noche) y prompt para seguir

Quién lo lea no necesita saber a quién estaba asignada cada tarea: se sigue por dependencias.

## Hecho
| Tarea | Estado | Dónde |
| --- | --- | --- |
| Validación de la consigna contra el plan, arquitectura B, PG3-05 agregada | Hecho | `docs/plan/`, `docs/ARQUITECTURA.md` |
| PG3-01 a 04, 06 a 09 (esqueleto, grafo modular, SM1, SM2, SM3, GRUPO, router) | Hecho (PR #4, de otra persona) | `asistente/`, `cypher/` |
| PG3-05 Cierre de trazabilidad y conteos (origen del conocimiento en `GRUPO.traza_reglas`, conteos 343/683) | Hecho y validado con Neo4j 5.26 | `asistente/submodulos/grupo/`, `scripts/contar_grafo.py` |
| PG3-12 SM4 (recomendar, explicar_notebook, comparar, costo_beneficio) | Hecho, esperados del issue coinciden con el grafo | `asistente/submodulos/sm4/` |
| PG3-13 Explicador común | **Casi**: prompt, verificador a–h, plantilla y regeneración listos | `asistente/explicador.py`, `prompts/explicacion.txt` |
| PG3-15 Registro de correcciones (43 filas) | Hecho | `docs/CORRECCIONES.md` |
| Medición del router con `qwen2.5:3b` | Intenciones 24/25 = 96 %, resultado final 23/25 = 92 % | R04 (no extrajo `req_01`) y R13 (espera `SM1.aclarar_pedido`, que la arquitectura B no emite) |

Suite: 151 tests en verde con Neo4j, 2 salteados (router y explicador con LLM, que piden `PG3_TEST_LLM=1`).

## Pendiente (en este orden)
1. **`/code-review` de PG3-05, 12 y 13: corrido y corregido el 11/11** (PG3-15 es solo documentación y no se revisó como código). Falta volver a correrlo sobre los commits `fix(...)`.
2. **PG3-13, lo que falta**: ajustar el prompt y el verificador con los E2E reales. Siguen abiertos del review: el parseo de números con separador de miles (`1.200` se lee como 1,2), el redondeo muy permisivo de enteros y las afirmaciones que contradicen un dato sin nombrar notebook ni estado (por ejemplo, «los parámetros están validados»).
3. **Orquestador**: la misma intención para dos modelos (E2E-2) ya une las listas `notebooks` (corregido el 11/11, con test).
4. **PG3-11, hecho el 11/11:** los 7 E2E aprueban (`python -m scripts.correr_e2e`), con casos de uso, pruebas funcionales y secciones 07 y 08 del informe. Falta medir los tiempos en otra máquina. **PG3-17, hecho a medias:** `scripts/exportar_grafo.py` y `scripts/armar_zip.py` andan; faltan b) diagramas, k) video y l) infografía en el ZIP, y la prueba de reproducción en una carpeta limpia.
5. **En curso con agentes (11/11):** PG3-16 manual y README, PG3-10 diagramas, PG3-14 informe PDF (con el resumen de una página como cobertura del ítem l). Revisar sus ramas o archivos y commitear. **De personas:** PG3-19 video, PG3-20 lectura cruzada.
6. **Compuerta de PG3-21:** se cumplen las condiciones técnicas (PG3-12 y 13 en `main`, E2E-1 andando), pero **no se toma**: falta tiempo y el nivel 1 cubre la consigna. Nivel 2 (PG3-21 a 27) queda fuera; el informe lo dice como limitación.
7. **Abiertos menores**: `ORDER BY` sin desempate en SM2 (`riesgo_ram`), `GRUPO.parametros` y `GRUPO.traza_reglas` (los fixtures cambian de orden sin que cambie el grafo); `q.fuente` siempre nula en L3; mover `NO_REGISTRADA` a `contrato.py` (lo aprueba Miranda); `docs/contexto/CONTEXTO_SM3_PG3.md` es una copia vieja (C-20).
8. **De las personas, no del código**: aprobar `contrato.py` del PR #4, confirmar la excepción de `langchain-ollama` en `RESTRICCIONES.md` §8, avisar a de Coninck que se tocó `grupo/`, y decidir si se prueba `qwen2.5:7b`.

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
