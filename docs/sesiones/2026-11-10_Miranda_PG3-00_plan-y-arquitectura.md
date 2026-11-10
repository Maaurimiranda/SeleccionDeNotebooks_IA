# Plan y arquitectura de PG3 · Miranda · 2026-11-10 · PG3-00

## En tres líneas
- Se definió **cómo va a ser el asistente final** ([`docs/ARQUITECTURA.md`](../ARQUITECTURA.md)) y **quién hace qué hasta el viernes 13/11** ([`docs/plan/PLAN_PG3.md`](../plan/PLAN_PG3.md) + 27 issues en `docs/plan/issues/`).
- Se cambió el LLM a **`qwen2.5:3b`**.
- Todavía no hay código de PG3: esto es el plano.

## Qué cambió
| Archivo | Qué tiene ahora |
| --- | --- |
| `docs/ARQUITECTURA.md` | Componentes, flujo de una consulta, **contrato en código** (firmas exactas), grafo dividido por dueño, estructura del repo, pruebas y traza |
| `docs/plan/PLAN_PG3.md` | Hitos H0–H5, carga por persona, cronograma, dependencias, reglas de trabajo y qué tarea cubre cada punto de la consigna |
| `docs/plan/issues/PG3-NN.md` | Una tarea por archivo, con objetivo, contexto, qué hacer, criterios de aceptación y dependencias |
| `CLAUDE.md` + `docs/sesiones/` | La regla de dejar una nota como esta en cada sesión, y su plantilla |
| `INCONSISTENCIAS_CONTEXTOS.md` D-05, README y contextos | `qwen2.5:3b` por defecto, `7b` opcional |

## Cómo funciona el asistente (resumen de la arquitectura)
1. El usuario escribe, por ejemplo: «En req_01, ¿por qué la G quedó indeterminada y qué riesgo de RAM tiene?».
2. El **router** (prompt maestro, de Olea) le pide al LLM un **plan JSON**: `SM4.explicar_notebook(G)` + `SM2.riesgo_ram(G)`. Python valida el plan: que las intenciones existan, que la G esté en el catálogo y que el pedido esté en el texto.
3. El **orquestador** llama a `sm4.ejecutar(...)` y a `sm2.ejecutar(...)`. Cada submódulo corre **sus** consultas Cypher fijas y devuelve una **evidencia**. Siempre se agrega el pedido interpretado (L1, de SM1).
4. El **explicador** (de Luconi) le pasa al LLM toda la evidencia junta y le pide una sola respuesta en voseo, de 180 palabras o menos. El **verificador** controla que cada cifra y cada notebook estén en la evidencia. Si falla dos veces, se usa una plantilla armada en código.
5. Todo queda en una **traza** JSONL: pregunta, plan, Cypher, filas, evidencia, intentos y respuesta. Con eso se reconstruye de dónde salió cada cosa.

**Por qué así:** la consigna evalúa que el prompt maestro enrute y que «Neo4j maneje la verdad». El LLM nunca calcula ni escribe Cypher; solo traduce y redacta.

**Por qué se puede trabajar en paralelo:** cada submódulo tiene **una sola función** con una firma fija (ARQUITECTURA §4.1) y un fixture JSON de ejemplo. Cada uno programa y prueba contra eso sin esperar a nadie. Integrar es reemplazar un stub.

## Decisiones y por qué
- **`qwen2.5:3b` en vez de `7b`:** corre en todas las máquinas (~4 GB de RAM) y es 2 a 3 veces más rápido. Lo que pierde (JSON y redacción) se compensa así:
  - el `format` con esquema y `enum` de intenciones;
  - la validación en Python;
  - el verificador con plantilla fija.

  El `7b` queda disponible cambiando `OLLAMA_MODEL`.
- **Dos niveles:** el nivel 1 (~41,5 h) cubre cada criterio de evaluación y cada ítem del ZIP. Las reglas pendientes de D-04, el pedido nuevo (D-08), los dos escenarios (D-09) y `SALIDA_PI2` completo (D-03) son de nivel 2. Si no se llega, el informe los presenta como trabajo futuro.
- **Grafo dividido por dueño:** el canónico se parte en `cypher/00_…90_*.cypher`, uno por submódulo más los comunes, para que nadie edite el archivo de otro. Las reglas nuevas van en el archivo del submódulo.
- **Asignación:** cada uno hace su submódulo. Lo transversal se repartió por menor carga:
  - esqueleto y ZIP: Miranda;
  - router, video e infografía: Olea;
  - E2E, diagramas y GRUPO: de Coninck;
  - explicador e informe: Luconi.
- **Neo4j propio de cada uno**, no compartido, para no pisarse los datos.
- **Sin plan B ni seguimiento formal**, por decisión del grupo. **Sí** hay notas de sesión y una lectura cruzada (PG3-20), porque lo crítico es que todos entiendan todo.

## Cómo probarlo
Por ahora no hay código. Revisar:
1. el cronograma de `PLAN_PG3.md` §4;
2. el issue propio;
3. el contrato de ARQUITECTURA §4.

## Qué queda y dudas
- **Crear los issues en GitHub:** queda pendiente; se decide después. `docs/plan/crear_issues.sh` lo hace en un paso.
- Cada uno: PG3-00 (entorno) hoy a la noche.
- **Sin verificar:** que el canónico cargue y pase CP1–CP11. Nunca se corrió en Neo4j, y es lo primero de PG3-02.
- No se conoce la hora exacta de entrega del viernes. Si es temprano, el bloque del viernes se adelanta al jueves a la noche.
