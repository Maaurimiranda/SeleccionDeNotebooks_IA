# Plan de PG3 · Grupo 2

> **Entrega:** viernes **13/11/2026** (`Grupo_2_PG3_ProyectoFinal.zip`).
> **Capacidad:** 4 personas × 3 h por día. Del martes 10 (noche) al viernes 13 hay unas **36 a 48 horas** en total.
> **Arquitectura:** [`docs/ARQUITECTURA.md`](../ARQUITECTURA.md). **Decisiones:** [`docs/INCONSISTENCIAS_CONTEXTOS.md`](../INCONSISTENCIAS_CONTEXTOS.md) (D-01 a D-13).
> **Stack del LLM (D-05, 10/11/2026):** LangChain (`ChatOllama` + `ChatPromptTemplate`) sobre Ollama, como en el ejemplo de PG3 de la cátedra. Lo implementa PG3-01 en `asistente/llm.py` (cliente) y `asistente/orquestador.py` (despacho con `RunnableLambda`); los submódulos no importan LangChain.
> **Capas del backend:** controlador → servicio → repositorio, más esquemas, en el sistema y dentro de cada submódulo (ARQUITECTURA §2.1). PG3-01 deja los cinco paquetes armados.
> **Tareas:** una por archivo en [`issues/`](issues/), con el formato de un issue de GitHub, listas para crearse con `gh issue create --body-file`.

---

## 1. Cómo leer este plan

- **Nivel 1:** lo imprescindible para aprobar. Cubre cada criterio de evaluación de la consigna (§7) y cada ítem a–l del ZIP. Suma unas **42 h** y es lo único que se planifica con fecha.
- **Nivel 2:** si sobra tiempo. Son las mejoras de D-03, D-04, D-08, D-09, D-10 y D-11. Cada una está escrita como issue, así que se puede tomar cuando haya un hueco. Lo que no se haga se declara como **trabajo futuro** en el informe.
- **Asignación:**
  - Lo de cada submódulo va a su dueño: SM1 Olea, SM2 Miranda, SM3 de Coninck y SM4 Luconi.
  - Lo transversal va a quien tenía menos horas al repartir.
- **Dependencias:**
  - **dura:** no se puede empezar sin la otra;
  - **blanda:** se puede empezar contra el contrato de `ARQUITECTURA.md` §4 y los fixtures, y se integra después.

  Entre personas **solo hay dependencias blandas hasta el jueves**. Las duras aparecen recién en la integración (E2E, informe y ZIP).

## 2. Hitos

| Hito | Cuándo | Qué tiene que estar en `main` |
| --- | --- | --- |
| **H0 · Arranque** | Mar 10, 23:59 | Este plan, la arquitectura y `CLAUDE.md` unidos. Cada uno con Ollama `qwen2.5:3b`, Neo4j 5 propio y el canónico cargado (PG3-00) |
| **H1 · Esqueleto** | Mié 11, 13:00 | PG3-01 (esqueleto ejecutable con stubs y contrato) y PG3-02 (grafo modular con la regresión CP1–CP11 en verde) |
| **H2 · Módulos** | Mié 11, 23:59 | PG3-03, 04, 06, 07, 09, 12 y 13 con sus tests offline en verde y PR abierto |
| **H3 · Integración** | Jue 12, 20:00 | PR unidos, E2E-1, 2, 3, 5 y 8 corriendo de punta a punta (PG3-11). **Congelamiento de código a las 22:00**: después solo entran correcciones de bugs |
| **H4 · Textos** | Jue 12, 23:59 | Secciones del informe en `docs/informe/`, diagramas, manual y registro de correcciones |
| **H5 · Entrega** | Vie 13 | Informe PDF, video, infografía, exportación del grafo y ZIP subido |

## 3. Carga por persona (nivel 1)

| Persona | Submódulo | Tareas | Horas |
| --- | --- | --- | --- |
| **Miranda, Mauricio** | SM2 | PG3-01 Esqueleto y contrato (3,5) · PG3-02 Grafo modular y regresión (2) · PG3-03 SM2 (2) · PG3-16 Manual de uso (1) · PG3-17 Exportación y ZIP (1,5) | **10** |
| **Olea, Facundo** | SM1 | PG3-06 Prompt maestro y router (3) · PG3-07 SM1 (2) · PG3-08 Secciones del informe: problema, LLM y metodología (1,5) · PG3-18 Infografía (1,5) · PG3-19 Video (1,5) | **9,5** |
| **de Coninck, Ramiro** | SM3 | PG3-09 SM3 (2,5) · PG3-04 GRUPO: traza y parámetros (1) · PG3-10 Diagramas (2) · PG3-11 E2E, casos de uso y pruebas (3) · PG3-15 Registro de correcciones (1) | **9,5** |
| **Luconi, Martina** | SM4 | PG3-12 SM4 (3) · PG3-13 Explicador común (3) · PG3-14 Informe ejecutivo PDF (3) | **9** |
| **Todos** | — | PG3-00 Entorno (0,5 c/u) · PG3-20 Lectura cruzada (0,5 c/u) | 4 |

**Total del nivel 1: ~42 h.** Es más de lo que da 3 h × 3 días (36 h) y entra si se usa la noche del martes. Si el miércoles a la noche (H2) alguien viene atrasado, se recorta primero la infografía (la consigna pide «video **o** infografía»), después el manual separado (se lo puede reemplazar por el README) y por último el diagrama de secuencia.

## 4. Cronograma

| Bloque | Miranda (SM2) | Olea (SM1) | de Coninck (SM3) | Luconi (SM4) |
| --- | --- | --- | --- | --- |
| **Mar 10 noche** | PG3-00 · PG3-01 | PG3-00 · leer arquitectura · empezar PG3-06 (prompt) | PG3-00 · leer arquitectura · empezar PG3-09 | PG3-00 · leer arquitectura · empezar PG3-12 |
| **Mié 11** | PG3-01 (cierre, H1) · PG3-02 · PG3-03 | PG3-06 · PG3-07 | PG3-09 · PG3-04 · PG3-10 | PG3-12 · PG3-13 |
| **Jue 12** | Revisar y unir los PR · integración · PG3-16 | Ajustar el prompt con los E2E · PG3-08 · PG3-20 | PG3-11 (E2E) · PG3-15 · PG3-20 | Ajustar el verificador con los E2E · secciones · PG3-20 |
| **Vie 13** | PG3-17 (exportación y ZIP) | PG3-19 (video) · PG3-18 (infografía) | Repasar las pruebas y la traza final | PG3-14 (PDF final) |

## 5. Dependencias

```mermaid
flowchart TD
    P00[PG3-00 Entorno · todos] --> P01 & P02
    P01[PG3-01 Esqueleto y contrato · Miranda]
    P02[PG3-02 Grafo modular · Miranda]
    P01 -.blanda.-> P03[PG3-03 SM2 · Miranda]
    P01 -.blanda.-> P04[PG3-04 GRUPO · de Coninck]
    P01 -.blanda.-> P06[PG3-06 Router · Olea]
    P01 -.blanda.-> P07[PG3-07 SM1 · Olea]
    P01 -.blanda.-> P09[PG3-09 SM3 · de Coninck]
    P01 -.blanda.-> P12[PG3-12 SM4 · Luconi]
    P01 -.blanda.-> P13[PG3-13 Explicador · Luconi]
    P02 -.blanda.-> P03 & P07 & P09 & P12 & P04
    P03 & P04 & P06 & P07 & P09 & P12 & P13 ==> P11[PG3-11 E2E y pruebas · de Coninck]
    P01 -.blanda.-> P10[PG3-10 Diagramas · de Coninck]
    P11 ==> P19[PG3-19 Video · Olea]
    P01 ==> P16[PG3-16 Manual · Miranda]
    P08[PG3-08 Secciones · Olea] ==> P14
    P10 & P11 & P15[PG3-15 Correcciones · de Coninck] ==> P14[PG3-14 Informe PDF · Luconi]
    P11 ==> P20[PG3-20 Lectura cruzada · todos]
    P14 & P16 & P19 & P18[PG3-18 Infografía · Olea] & P02 ==> P17[PG3-17 Exportación y ZIP · Miranda]
```

Línea continua gruesa = dura. Punteada = blanda.

**Camino crítico:** PG3-01 → (módulos) → PG3-11 → PG3-19 / PG3-14 → PG3-17. Lo que más riesgo tiene es PG3-11, porque junta todo. Para que no se trabe:
1. Cada módulo llega con sus tests offline en verde.
2. El orquestador del esqueleto ya corre de punta a punta con stubs desde el miércoles al mediodía. Integrar un módulo es reemplazar su stub, nada más.

## 6. Reglas de trabajo

1. **Una rama por issue:** `pg3-NN-descripcion-corta`. PR a `main` revisado por **otro** integrante; el que tenga menos carga en ese momento.
2. **Dueño por archivo** (ARQUITECTURA §2 y §5). Si hay que tocar un archivo ajeno, se le avisa al dueño y él revisa el PR. `asistente/contrato.py` lo revisa siempre Miranda.
3. **Definición de terminado**, para todas las tareas de código:
   - los criterios de aceptación tildados;
   - `python -m unittest` en verde;
   - sin credenciales en el diff;
   - la nota de sesión en `docs/sesiones/` (ver `CLAUDE.md`);
   - el PR unido.
4. **Literales:** los de D-06, sin tildes en el código y en el grafo.
5. **Tecnologías:** solo lo de `RESTRICCIONES.md`. Si algo no está, se frena y se avisa al grupo.
6. **Entendimiento compartido** (prioridad del grupo): cada sesión de trabajo, con o sin IA, deja su explicación en `docs/sesiones/`. El jueves, cada uno lee las de los demás (PG3-20).

## 7. Cobertura de la consigna

| Consigna | Dónde se cumple |
| --- | --- |
| §2 Prompt maestro que enruta | PG3-06 |
| §2 API o interfaz única | PG3-01 (`POST /consultar`, CLI) |
| §2 y §7 Pruebas que cruzan submódulos (≥ 3 E2E) | PG3-11: E2E-1, 2, 3, 5 y 8 |
| §3.1 Revisión, depuración y correcciones documentadas | PG3-02 (regresión), PG3-15 |
| §3.2 Integración (Neo4j, reglas, difuso, LLM, interfaz) | PG3-01, 03, 04, 06, 07, 09, 12 y 13 |
| §3.3 Arquitectura y diagrama con la función de cada componente | `ARQUITECTURA.md`, PG3-10 |
| §3.4 ≥ 5 casos de uso integrados | PG3-11 (los 5 E2E también son casos de uso, D-12) |
| §3.5 Pruebas funcionales con esperado y obtenido | PG3-03, 07, 09, 12 (funcionales por submódulo) y PG3-11 (documento) |
| §3.6 Evaluación del sistema | PG3-14 |
| §3.7 Trazabilidad | PG3-01 (traza), PG3-11 (ejemplos), PG3-14 (sección) |
| §3.8 Reflexión sobre la metodología | PG3-08 |
| §4 a) Informe PDF | PG3-14 |
| §4 b) Diagramas | PG3-10 |
| §4 c) Casos de prueba | PG3-11 |
| §4 d) Manual de uso | PG3-16 |
| §4 e) Código + `requirements.txt` | PG3-01 y los módulos |
| §4 f) Scripts Cypher | PG3-02 |
| §4 g) Configuración | PG3-01 (`.env.example`) |
| §4 h) Recursos complementarios | PG3-17 (prompts, contextos, fuentes PI4) |
| §4 i) Exportación de Neo4j | PG3-17 |
| §4 j) Datos de ejemplo | PG3-17 |
| §4 k) Video | PG3-19 |
| §4 l) Infografía | PG3-18 |

## 8. Lista de issues

### Nivel 1

| ID | Título | Responsable | Horas | Depende de |
| --- | --- | --- | --- | --- |
| [PG3-00](issues/PG3-00.md) | Entorno local igual para todos | Todos | 0,5 c/u | — |
| [PG3-01](issues/PG3-01.md) | Esqueleto ejecutable, contrato y API | Miranda | 3,5 | PG3-00 |
| [PG3-02](issues/PG3-02.md) | Grafo modular por dueño y regresión CP1–CP11 | Miranda | 2 | PG3-00 |
| [PG3-03](issues/PG3-03.md) | SM2 en el contrato: riesgo de RAM y virtualización | Miranda | 2 | 01·, 02· |
| [PG3-04](issues/PG3-04.md) | GRUPO: traza de reglas (L3) y parámetros (L4) | de Coninck | 1 | 01·, 02· |
| [PG3-06](issues/PG3-06.md) | Prompt maestro y router | Olea | 3 | 01· |
| [PG3-07](issues/PG3-07.md) | SM1 en el contrato: pedido interpretado | Olea | 2 | 01·, 02· |
| [PG3-08](issues/PG3-08.md) | Informe: problema, integración con el LLM y metodología | Olea | 1,5 | 06, 07 |
| [PG3-09](issues/PG3-09.md) | SM3 en el contrato: búsqueda y ficha | de Coninck | 2,5 | 01·, 02· |
| [PG3-10](issues/PG3-10.md) | Diagramas de arquitectura, secuencia y grafo | de Coninck | 2 | 01· |
| [PG3-11](issues/PG3-11.md) | E2E, casos de uso y pruebas funcionales documentadas | de Coninck | 3 | 03, 04, 06, 07, 09, 12, 13 |
| [PG3-12](issues/PG3-12.md) | SM4 en el contrato: recomendar, explicar, comparar y costo-beneficio | Luconi | 3 | 01·, 02· |
| [PG3-13](issues/PG3-13.md) | Explicador común: prompt, verificador y plantilla fija | Luconi | 3 | 01· |
| [PG3-14](issues/PG3-14.md) | Informe ejecutivo final (PDF) | Luconi | 3 | 08, 10, 11, 15 |
| [PG3-15](issues/PG3-15.md) | Registro de correcciones (consigna §3.1) | de Coninck | 1 | 02 |
| [PG3-16](issues/PG3-16.md) | Manual de uso | Miranda | 1 | 01 |
| [PG3-17](issues/PG3-17.md) | Exportación del grafo, datos de ejemplo y ZIP final | Miranda | 1,5 | 02, 14, 16, 18, 19 |
| [PG3-18](issues/PG3-18.md) | Infografía | Olea | 1,5 | 10 |
| [PG3-19](issues/PG3-19.md) | Video demostrativo | Olea | 1,5 | 11 |
| [PG3-20](issues/PG3-20.md) | Lectura cruzada del sistema | Todos | 0,5 c/u | 11 |

`·` = dependencia blanda.

### Nivel 2 (si sobra tiempo)

| ID | Título | Responsable | Horas | Decisión |
| --- | --- | --- | --- | --- |
| [PG3-21](issues/PG3-21.md) | Pedido nuevo: registrar y aclarar, con inferencia por `$req` | Olea (+ Miranda revisa) | 4 | D-08, D-01 |
| [PG3-22](issues/PG3-22.md) | SM1: requisitos explícitos, INT-R8/R9, entropía y dos escenarios | Olea | 4 | D-04, D-09, D-10 |
| [PG3-23](issues/PG3-23.md) | SM2: canal de memoria (REN-R11, REN-R14), REN-R13 y REN-R2 | Miranda | 3 | D-04 |
| [PG3-24](issues/PG3-24.md) | SM3: intensidad → gama (GM-R1/R2), GM-R14, GM-R15 y monitor externo (GM-R16) | de Coninck | 3 | D-04 |
| [PG3-25](issues/PG3-25.md) | `SALIDA_PI2` de los 7 perfiles, `req_04` y `req_05`, y E2E-4 | Miranda (rendimiento) + de Coninck (pantalla) | 3 + 2 | D-03, D-11 |
| [PG3-26](issues/PG3-26.md) | SM4: REC-R16 (monitor externo) y REC-R9 con `req_05` | Luconi | 2 | D-04, D-11 |
| [PG3-27](issues/PG3-27.md) | Contextos de SM3 y SM4 con etiquetas de procedencia | de Coninck, Luconi | 1 c/u | D-13 |
