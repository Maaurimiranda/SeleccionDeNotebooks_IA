# Estado al 14/11/2026 y prompt para seguir

Quién lo lea no necesita saber a quién estaba asignada cada tarea: se sigue por dependencias.

## Hecho
PG3 entregado en `Grupo_2_PG3_ProyectoFinal.zip`: informe final (`Grupo_2_PG3_Informe_Final.pdf`, 24 páginas), resumen ejecutivo de una página, presentación de la defensa (`.pptx`, ítem k), exportación de Neo4j, datos de ejemplo y el código con `docs/` (diagramas, pruebas, manual). El 14/11 se agregaron consultas libres con pedido nuevo, la web en `/ui`, las respuestas del técnico y `SALIDA_PI2` provisional. Pruebas: 249 `unittest` (con Neo4j, 244 OK y 5 salteadas que piden Ollama), CP1 a CP11 en 11 de 11 y router 34 de 37 (92 %).

## Pendiente
1. **Videos individuales PI6** (`Apellido_Nombre_PI6_VideoFinal.mp4`, 3 a 5 minutos, con rostro).
2. **Revisiones de dueño** de lo que se unió el 14/11 tocando archivos ajenos (ver las notas de Luconi del 14/11 en `docs/sesiones/`), y confirmar o reemplazar los 53 pares provisionales de `SALIDA_PI2` (SM2 y SM3).
3. **Commitear con PR** el README, el manual, `funcionales.md`, `02_resumen.md` y el resumen ejecutivo corregidos el 14/11.

## Opcional, fuera del alcance de la entrega
Nada de esto bloquea la entrega. Se hace solo si sobra tiempo.
- **Revisiones:** revisión retroactiva del PR #4 (`contrato.py`, excepción de `langchain-ollama`); revisión de los PR #5 y #7 por otro integrante.
- **Verificaciones:** seguir el manual desde cero; tiempos de los E2E en otra máquina; abrir los `.drawio` en draw.io de escritorio; medir `qwen2.5:3b` con los controles nuevos (`PG3_TEST_LLM=1 python -m unittest tests.test_explicador`); regenerar los fixtures de SM4 con Neo4j (`python -m scripts.generar_fixtures`); lectura cruzada del sistema (PG3-20); confirmar que `mistune` y PyMuPDF (solo para armar el PDF) están bien fuera de `RESTRICCIONES.md`.
- **Defectos conocidos:**
  - Verificador del explicador: el `?` del control (g) exime a toda la oración; el redondeo de enteros es permisivo; no corta afirmaciones sin cifra ni notebook; no reconoce una falta de información dicha con otras palabras.
  - Orquestador: fusiona mal dos `SM3.buscar` con filtros distintos.
  - SM4: falta `franja_con_peor_caso` en notebooks de grado exacto que empatan con una de rango; la prioridad `precio` (REC-R9) no explica el orden; el motivo está armado en el Cypher.
  - Orden inestable de filas en `SM2.riesgo_ram`, `GRUPO.parametros` y `GRUPO.traza_reglas`.
- **Limpieza:** borrar `docs/contexto/CONTEXTO_SM3_PG3.md` (copia vieja con errores); `tests/test_armar_zip.py` corre el `main()` real y puede fallar por la contraseña del `.env` de quien lo corre.

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
