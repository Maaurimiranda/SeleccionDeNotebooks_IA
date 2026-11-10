# CLAUDE.md · Asistente experto para la selección de notebooks (Grupo 2, UTN FRM)

Instrucciones para cualquier agente de IA, y también para las personas, que trabajen en este repo.

## Antes de tocar nada

Leer, en este orden:
1. [`docs/ARQUITECTURA.md`](docs/ARQUITECTURA.md): componentes, contrato en código (§4) y dueño de cada archivo.
2. [`docs/RESTRICCIONES.md`](docs/RESTRICCIONES.md): qué tecnologías se pueden usar. **No instalar ni proponer nada fuera de las listas verde y amarilla.** Si algo no se puede hacer con ellas, frenar y avisar.
3. [`docs/plan/PLAN_PG3.md`](docs/plan/PLAN_PG3.md) y el issue de la tarea, en `docs/plan/issues/PG3-NN.md`: objetivo, criterios de aceptación y dependencias.
4. Si la tarea toca un submódulo, su contexto: `docs/contexto/Contexto_SMX_{Apellido}_para_PG3.md`. Si hay que decidir algo, mirar [`docs/INCONSISTENCIAS_CONTEXTOS.md`](docs/INCONSISTENCIAS_CONTEXTOS.md) (D-01 a D-13).

## Reglas

- **Neo4j maneja la verdad.** El LLM no calcula ni decide: interpreta (router) y explica (explicador). Las consultas Cypher son plantillas fijas y el LLM no las escribe.
- **Contrato:** cada submódulo expone solo `ejecutar(intencion, parametros, grafo) -> {"consultas", "evidencia"}` y no importa a otros submódulos. Cada submódulo es un paquete con `entrada.py` → `servicio.py` → `repositorio.py`, más `esquemas.py` (ARQUITECTURA §2.1): el Cypher va solo en `repositorio.py`, y no hay endpoints por submódulo. `asistente/contrato.py` se cambia solo con un PR aprobado por Miranda.
- **Literales de D-06**, sin tildes en el código y en el grafo: `Recomendada (Alta)`, `Recomendada (Media)`, `Recomendada condicionada por falta de informacion`, `Indeterminada: completar informacion`, `Descartada (excluyente incumplido)`, `Descartada`, `'sin validar'`.
- **La incertidumbre se conserva:** rangos `{min, max}`, `desconocida` e `indeterminado` no se completan ni se promedian.
- **LLM:** Ollama `qwen2.5:3b`, temperatura 0, vía LangChain (`ChatOllama` + `ChatPromptTemplate`) con `with_structured_output`, en `asistente/llm.py`; el orquestador despacha a los submódulos con `RunnableLambda` (D-05). LangChain no escribe Cypher ni se usan agentes.
- **Pruebas:** `unittest` (no `pytest`). Las que necesitan Neo4j u Ollama se saltean si no están.
- **El repo es público:** ninguna credencial, URI de Aura ni contraseña en archivos versionados. Todo va en `.env`.
- **Dueño por archivo** (ARQUITECTURA §2 y §5): para tocar un archivo de otro, avisarle; él revisa el PR.
- **Git:** una rama por issue (`pg3-NN-descripcion`) y un PR a `main` revisado por otro integrante. Mensajes en imperativo, con tipo y área: `feat(sm2): ...`, `docs(plan): ...`.

## Al terminar cada sesión: nota para el grupo (obligatorio)

La prioridad del grupo es que **los cuatro entiendan todo el sistema**. Por eso cada sesión de trabajo, con IA o sin ella, termina con una nota en `docs/sesiones/`, en el mismo PR que el trabajo.

- **Nombre:** `docs/sesiones/AAAA-MM-DD_Apellido_PG3-NN_tema-corto.md`. Si la sesión no tiene un issue, se usa `PG3-00`.
- **Lector:** un compañero que **no estuvo en la sesión** y no conoce ese submódulo. No asumir contexto, explicar las siglas y enlazar los archivos.
- **Plantilla:** la de [`docs/sesiones/README.md`](docs/sesiones/README.md).
- **Extensión:** una a dos páginas. Si hace falta más, el detalle va al contexto o a la arquitectura, y la nota enlaza ahí.

Un agente de IA escribe esa nota **antes** de dar la tarea por terminada, sin que se lo pidan.
