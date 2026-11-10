# Asistente Experto para la Selección Personalizada de Notebooks

> **Proyecto final · Inteligencia Artificial · Grupo 2 · Comisión 5K09 · UTN FRM · Ciclo 2026**
> Un único asistente que entiende preguntas en español, consulta una base de conocimiento en Neo4j, razona con reglas y lógica difusa, y explica sus conclusiones de forma verificable.

---

## 1. ¿Qué es?

Elegir una notebook no es comparar fichas técnicas: «16 GB» no significa lo mismo para ofimática que para máquinas virtuales, y «Core i7» no garantiza rendimiento sostenido. Este asistente traduce el **perfil de uso del comprador** en requisitos de hardware, evalúa cada notebook del catálogo y **justifica** por qué una quedó recomendada, condicionada, indeterminada o descartada.

Está formado por cuatro submódulos que comparten una única base de conocimiento:

| Submódulo | Responsabilidad | Autor |
| --- | --- | --- |
| **SM1** · Interpretación del requerimiento y perfil de uso | Convierte el pedido del comprador en perfiles de uso con grado, presupuesto y requisitos | Olea, Facundo (47855) |
| **SM2** · Evaluación de rendimiento y capacidad | Evalúa CPU, RAM y almacenamiento; riesgo de obsolescencia de la RAM (lógica difusa) | Miranda, Mauricio (50101) |
| **SM3** · Evaluación gráfica y de movilidad | Evalúa GPU, pantalla, peso y autonomía | de Coninck, Ramiro (49998) |
| **SM4** · Integración, costo-beneficio y recomendación explicable | Combina los grados, aplica los requisitos excluyentes y recomienda | Luconi Furque, Martina (48889) |

## 2. Principios de diseño

### Fijados por la consigna

1. **Neo4j maneja la verdad.** Toda cifra, regla, estado o alerta sale del grafo. El LLM no calcula ni decide.
2. **El LLM es la interfaz de interacción y explicación.** Interpreta la consulta y redacta la respuesta; el razonamiento está en las reglas y en la lógica difusa.

### Propuestos desde SM2 (PI4), a acordar con el grupo

3. **El LLM interpreta y explica en dos llamadas.** Una extrae la intención en JSON y otra redacta la respuesta a partir de una *evidencia* ya recuperada.
4. **El LLM no escribe Cypher.** Las consultas son plantillas fijas y parametrizadas, y la conexión es de **solo lectura** (`READ_ACCESS`).
5. **Todo se verifica en código.** Cada cifra, notebook y regla citada tiene que estar en la evidencia; si no, se regenera y, como último recurso, se usa una plantilla fija.
6. **La incertidumbre se conserva.** Un dato desconocido sigue siendo «desconocido» (no se convierte en «no ampliable»); un riesgo con rango se informa como rango; un pedido sin perfil definido no se «completa».
7. **Honestidad sobre la validación.** Si los parámetros de un modelo difuso no están validados por un técnico, cada respuesta que dependa de ellos lo dice.

## 3. Arquitectura

Definida en [`docs/ARQUITECTURA.md`](docs/ARQUITECTURA.md): router con prompt maestro, cuatro submódulos con un contrato común, explicador con verificador y traza. El plan de trabajo hasta la entrega (13/11/2026) está en [`docs/plan/PLAN_PG3.md`](docs/plan/PLAN_PG3.md).

## 4. Estructura del repositorio

> La estructura final está en [`docs/ARQUITECTURA.md`](docs/ARQUITECTURA.md) §6. Por ahora:

```
SeleccionDeNotebooks_IA/
├── README.md
├── CLAUDE.md                       # reglas para agentes y personas; nota de sesión obligatoria
└── docs/
    ├── ARQUITECTURA.md             # arquitectura y contrato de PG3
    ├── plan/                       # PLAN_PG3.md + issues/ (una tarea por archivo)
    ├── sesiones/                   # explicación de cada sesión de trabajo, para el grupo
    ├── RESTRICCIONES.md            # qué técnicas y tecnologías se pueden usar
    ├── INCONSISTENCIAS_CONTEXTOS.md # inconsistencias entre contextos y decisiones pendientes (D-01 a D-13)
    ├── consigna/                   # ConsignaPG3.md: consigna de la cátedra y ejemplo de referencia
    ├── contexto/                   # contexto para PG3: PG1/PG2 grupal y SM1–SM4 (Contexto_SMX_{Apellido}_para_PG3.md)
    ├── cypher/                     # scripts de PG2; canónico: Grupo_2_PG2_U1_corregido.cypher (D-01)
    └── fuentes/                    # PI4 de cada submódulo (SM1–SM4): código y prompts
```

## 5. Requisitos

| Herramienta | Versión | Nota |
| --- | --- | --- |
| Python | `[confirmar]` | La consigna pide el código en Python con `requirements.txt` |
| Neo4j | 5.x `[confirmar]` | Base de conocimiento de PG2. Las consultas de SM2 usan subconsultas `EXISTS { … }` y el driver 5 |
| LLM | Ollama local, `qwen2.5:3b` (`qwen2.5:7b` opcional por `OLLAMA_MODEL`) | Temperatura 0 en las dos llamadas; HTTP directo a `/api/chat` con `requests`, sin LangChain (D-05) |
| Memoria | ~4 GB libres para `qwen2.5:3b` (~8 GB con `7b`) | Más lo que use Neo4j |

## 6. Puesta en marcha

> **Pendiente.** Los comandos, las variables de entorno y la carga del grafo dependen de la arquitectura y la estructura (secciones 3 y 4).

## 7. Uso

> **Pendiente.** La interfaz (chat, API o las dos) y su contrato se definen con la arquitectura. La consigna pide una **entrada única** para el usuario.

### Preguntas de ejemplo *(ideas, a validar contra el grafo)*

| Pregunta | Submódulos que debería usar |
| --- | --- |
| «¿Qué riesgo corre cada notebook de quedarse corta de RAM?» | SM2 |
| «¿Qué notebooks se descartan porque no soportan virtualización?» | SM2 (y SM4 para el estado final) |
| «Explicame por qué la Notebook G quedó indeterminada» | SM2 + SM4 |
| «¿Qué reglas se activaron para la Notebook A?» | SM2 + SM3 + SM4 |
| «¿Qué riesgo de RAM tienen las notebooks para mi pedido?» (con `req_02`) | SM1 + SM2 (perfil indeterminado) |
| «¿Cuál es la capital de Francia?» | Ninguno: respuesta fija de alcance |

## 8. Pruebas

> **Pendiente.** Herramientas y organización de las pruebas se definen con la arquitectura. Lo que pide la consigna: pruebas funcionales con esperado vs obtenido (sección 3.5) y al menos tres E2E que crucen submódulos (sección 7), ver [`docs/consigna/ConsignaPG3.md`](docs/consigna/ConsignaPG3.md).

Casos E2E candidatos *(ideas, a validar contra el grafo)*: explicar una recomendación completa (SM2 + SM3 + SM4), dato faltante que atraviesa módulos (Notebook G), perfil indeterminado (`req_02`), RAM y gráfica integrada (SM2 → SM3), y excluyentes con ranking (SM2 + SM4).

## 9. Trazabilidad y auditoría

> **Pendiente.** Cómo se registra la traza depende de la arquitectura.

La consigna (sección 3.7) pide poder reconstruir, para una respuesta: **fuente** del conocimiento, **regla** utilizada, **evidencia** considerada, **consulta** ejecutada y **explicación** generada.

Lo que ya existe:

- **En el grafo (PG2):** las reglas activadas quedan registradas (`[:ACTIVA]`, con su fuerza) y cada regla enlaza con la fuente que la respalda.
- **En el flujo de SM2 (PI4):** se guarda la pregunta y el JSON extraído, los parámetros validados, la consulta Cypher con sus filas, la evidencia que recibió el LLM y cada intento de explicación con lo que detectó el verificador (modo `--log archivo.jsonl`).

## 10. Entregable PG3 (`Grupo_2_PG3_ProyectoFinal.zip`)

El contenido mínimo del ZIP (ítems a–l) está en [`docs/consigna/ConsignaPG3.md`](docs/consigna/ConsignaPG3.md#4-formato-del-entregable). Dónde queda cada ítem en el repo se define junto con la estructura (sección 4, **pendiente**).

**Criterios de evaluación de PG3:** prompt maestro que enrute y respete que Neo4j maneja la verdad; API o interfaz única sin errores críticos; al menos tres pruebas E2E que crucen submódulos; informe coherente y profesional; ZIP que permita revisar y reproducir.

## 11. Estado del proyecto

- [x] Base de conocimiento en Neo4j (PG2)
- [x] SM2 integrado con LLM: flujo, prompts, verificador, plantilla fija y tests offline (PI4)
- [ ] SM2: verificación semántica (rangos, perfil indeterminado, afirmaciones sin respaldo) — **prioridad**
- [ ] SM2: confirmar la versión final del script de PI4 (ver `docs/contexto/`)
- [x] Consigna de PG3 en el repo (`docs/consigna/`)
- [x] Entender el contexto de SM1, SM3 y SM4 (unificados, D-01 a D-13)
- [x] Definir la arquitectura y la estructura del repositorio (`docs/ARQUITECTURA.md`)
- [x] Plan de PG3 con tareas, responsables y dependencias (`docs/plan/`)
- [ ] Integrar SM1, SM3 y SM4
- [ ] Prompt maestro con enrutamiento
- [ ] API única con enrutamiento a varios submódulos
- [ ] Pruebas E2E (≥ 3) con esperado vs obtenido
- [ ] Informe, diagramas, manual, video e infografía
- [ ] Exportación de Neo4j y ZIP final

## 12. Limitaciones conocidas

### De la base de conocimiento

- **Los parámetros del modelo difuso de SM2 no están validados por un técnico.** Los resultados son una referencia, no una certeza.
- Las notebooks se nombran hoy con una sola letra (`Notebook_A` a `Notebook_Z`); el catálogo real prevé 30 modelos.

### Del flujo de SM2 en PI4 (pueden cambiar con la arquitectura)

- Una intención por mensaje y un pedido activo por sesión.
- El verificador controla cifras, notebooks, reglas y atribución, pero todavía no el sentido de la frase.
- El extractor es un modelo local de 8 B: puede clasificar mal una consulta ambigua.

## 13. Cómo trabajamos

> **Propuesta, a acordar con el grupo.**

- **Ramas:** `main` estable y una rama por tarea (por ejemplo, `sm2/verificador-semantico`). Si hace falta una rama `dev` de integración se decide con la arquitectura.
- **Commits:** mensajes en imperativo con tipo y área, como los que ya hay en el historial (`docs(README): ...`).
- **Pull requests:** revisión de al menos otro integrante antes de unir a `main`.
- **Responsables:** cada submódulo tiene un dueño (sección 1); los cambios en el grafo compartido y en el prompt maestro se acuerdan entre todos.
- **Registro de correcciones:** la consigna pide documentarlas (sección 3.1); dónde se registran se define con la estructura del repositorio.

## 14. Referencias

- Cátedra de Inteligencia Artificial, UTN FRM (2026). Unidad 4, apuntes U1a, U1b y U1e, y actividades PI1 a PI4 y PG0 a PG3.
- Neo4j, Inc. Cypher Manual y Neo4j Python Driver Manual. https://neo4j.com/docs
- Ollama. Documentación de la API y de salidas estructuradas. https://ollama.com *(usado por SM2 en PI4; se mantiene si se elige ese LLM)*
- Lewis, P. et al. (2020). *Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks*. NeurIPS 33.
- Zadeh, L. A. (1965). Fuzzy sets. *Information and Control*, 8(3). Mamdani, E. H. y Assilian, S. (1975). *International Journal of Man-Machine Studies*, 7(1).
- Fuentes de conocimiento de cada submódulo: `[completar]` a partir de los informes de PG2 y de los PI de cada integrante.

## 15. Licencia y uso

Trabajo académico de la Cátedra de Inteligencia Artificial (UTN FRM). Uso educativo. 
