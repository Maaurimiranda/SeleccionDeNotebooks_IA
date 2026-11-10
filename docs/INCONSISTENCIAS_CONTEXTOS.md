# Inconsistencias entre los contextos (previo a PG3)

> **Para qué sirve.** Lista lo que no coincide entre los cinco contextos de [`docs/contexto/`](contexto/) y las decisiones que hay que tomar para unificarlos antes de desarrollar PG3. Cada decisión dice qué archivos hay que tocar cuando se resuelva.
> **Revisado:** 09/11/2026 sobre `Contexto_PG1_PG2_Grupo`, `Contexto_SM1_Olea`, `Contexto_SM2_Miranda`, `Contexto_SM3_deConinck` y `Contexto_SM4_Luconi` (todos `_para_PG3.md`), contra `RESTRICCIONES.md` y `consigna/ConsignaPG3.md`.
> **Fuentes:** desde el 09/11/2026 el repo tiene los tres `.cypher` ([`docs/cypher/`](cypher/)) y los PI4 de los cuatro submódulos ([`docs/fuentes/`](fuentes/)). Lo que sigue marcado *verificar* necesita ejecutar el script en Neo4j.

## Veredicto

**Sí se pueden unir.** Los cuatro submódulos comparten lo esencial: el camino `Requerimiento → EVALUA → Evaluacion → SOBRE → Notebook`, Mamdani con gaussianas, «Neo4j maneja la verdad», el patrón sándwich con plantillas Cypher fijas, el verificador REC-R11 con plantilla fija y la política «desconocido ≠ supuesto».

**Todavía no son uniformes.** El origen de casi todo es que **cada contexto describe una versión distinta del grafo** (D-01). Hasta decidir cuál es la canónica no se pueden fijar los valores esperados de las pruebas E2E. *Actualización: D-01 está resuelta; el canónico es `docs/cypher/Grupo_2_PG2_U1_corregido.cypher` y los cinco contextos ya lo referencian.*

---

## 1. Ya corregido (sin decisión humana)

| # | Qué estaba mal | Qué se hizo |
| --- | --- | --- |
| S-01 | Nombres de archivo dispares (`CONTEXTO_PROYECTO_SM1…`, `contexto_sm3_pg3.md` fuera de la carpeta) | Renombrados a `Contexto_SMX_{Apellido}_para_PG3.md`; el grupal quedó `Contexto_PG1_PG2_Grupo_para_PG3.md` (no tiene SM ni apellido) |
| S-02 | El contexto PG1/PG2 citaba `CONTEXTO_PROYECTO_SM2_PARA_PG3.md`, que no existe | Apunta a `Contexto_SM2_Miranda_para_PG3.md` |
| S-03 | README decía que `docs/contexto/` tenía solo SM2 y SM4 | Actualizado |
| S-04 | SM3: fórmulas LaTeX rotas (`\t`, `\r`, `\f` convertidos en tabulación, retorno y salto de página: «	imes», «ightarrow», «rac») | Reparadas (47 caracteres) |
| S-05 | SM3: movilidades que no se reproducen (A 0,655 · B 0,914 · E 0,655 · H 0,428) | Recalculadas con GM-RD1..3 y los parámetros del grafo: A 0,625 · B 0,776 · C 0,231 · E 0,547 · H 0,430. Coinciden con PG1/PG2 §9.3 y con la adecuación global que obtuvo SM4 en Neo4j |
| S-06 | SM2 tenía como dudas cosas que el contexto PG1/PG2 ya resolvió | Marcadas como resueltas: 81,46 vs 81,1 · 0,863 (fuerza) vs 0,785 (grado) · autora de SM4 · REN-R16 cargada · TSK de SM3 reemplazado por Mamdani · §8 de SM2 reemplazada por §8 de PG1/PG2 |

---

## 2. Decisiones para el grupo

D-01 está resuelta. Orden sugerido para el resto: D-02 a D-05 y después las demás en paralelo.

### D-01 · Versión canónica del grafo — **RESUELTA (09/11/2026)**

> **Decisión del grupo:** el grafo canónico es **`docs/cypher/Grupo_2_PG2_U1_corregido.cypher`**, y se le portan desde el linaje A las piezas de SM1. Contextos actualizados:
> - PG1/PG2: §8 reescrita (modelo canónico y diferencias con el linaje A en §8.8) y notas en §0.3, §5–§7, §9, §10, §12, §15 y §16.
> - SM1: encabezado, §7 y 13-A.
> - SM2: §8, §12 y §14 (A, B y nueva K).
> - SM3: encabezado, nota de verificación en §3 y fila de K en §5.
> - SM4: §5, §6, §6.5, §7.1 y §7.8.
>
> **Queda como trabajo (no como decisión):** portar SM1 al canónico (PG1/PG2 §8.8) y llevar a `ev.*` las consultas de PI4 de SM2 (SM2 §14-K).

**Inconsistencia.** Hay tres scripts y cada contexto describe uno:

| Script | Lo usa | Rasgos |
| --- | --- | --- |
| `Grupo_2_PG2_U1.cypher` | PG1/PG2, SM2 | Riesgo, grado de GPU y adecuación gráfica guardados en `Notebook`/`RAM` (corrección C-A **pendiente**); REC-R3 contamina entre pedidos; sin `req_03`; SM4 = bloque 10.e |
| `Grupo_2_PG2_U1_v2.cypher` | SM1 | «Reescrito, sin `$`», el que corrió en Aura; SM1 dice que el original era inconsistente con el informe |
| `Grupo_2_PG2_U1_bloques_0a12.cypher` | SM3, SM4 | «Versión corregida»: resultados por `Evaluacion` (C-A **hecha**), `req_03`, CP11, `ConsultaExperto`, `SinAlternativaAdecuada`, `PRODUCIDA_POR`, `ES_DE_GAMA`, `P_MAX_RECOMENDADAS`; SM4 = bloque 10.f |

**Opciones.**
- **a) `bloques_0a12` como base** y sumarle lo que cambió SM1 en `v2`. *(Recomendada: es la única que dice tener C-A resuelta.)*
- b) `v2` como base y rehacer el refactor C-A.
- c) Escribir uno nuevo a partir de los tres.

**Paso previo:** juntar los tres archivos en el repo y compararlos.

**Evidencia (09/11/2026).** El primer script que llegó, [`docs/cypher/Grupo_2_PG2_U1_bloques_0a12.cypher`](cypher/Grupo_2_PG2_U1_bloques_0a12.cypher), tiene 1659 líneas. Es la versión **`bloques_0a12`** (la de SM3 y SM4): el encabezado anuncia los bloques 0 a 13, pero termina en el 12 y **no trae las consultas L1–L4 del bloque 13**. No están `Grupo_2_PG2_U1.cypher` ni `_v2.cypher`.

Qué confirma:
- **C-A está hecha.** Riesgo, ρ, índice a, grado de GPU, adecuación gráfica, rendimiento y pantalla se guardan en `Evaluacion`. El rendimiento y la pantalla se cargan por perfil en `[:SALIDA_PI2]`, ya no en `Notebook`.
- **La contaminación de REC-R3 está corregida.** El estado se decide con `ev.excluyente_virtualizacion` de cada evaluación. Lo único que todavía escribe `INCUMPLE`/`NO_VERIFICADO` desde `Notebook` es la consulta de demostración C1 (bloque 11), y el estado no la lee.
- **`req_03` es el de SM4** (consulta puntual sobre K, prioridad portabilidad) y **CP11 está implementado**.
- **Los pesos son los de SM4** (OFI 0,40/0,10/0,50…), así que la tabla de PG1/PG2 §8.5 no corresponde a este script.
- **La RAM tiene `canal`** (K en `simple`, G en `desconocido`), pero ninguna regla lo usa: no hay GM-R15 ni REN-R11/R14.

Qué contradice a los otros contextos:
- **Tamaño:** hay **57 reglas** (23 difusas + 27 crisp + 7 retiradas, entre ellas GM-R10) y no 61; **30 parámetros** y no 59; **14 expresiones** de frecuencia y no 9.
- **Restricciones de unicidad:** `Notebook` se identifica por `modelo` (no hay `NB_A`), y no hay restricción de unicidad para `Evaluacion`, `Alerta` ni `Lectura`.
- **Relaciones:** no existen `ASOCIADO_A`, `LLEVA_A`, `TIENE_PREGUNTA` ni `ES_UN`; en su lugar aparecen `APUNTA_A`, `REQUIERE_ACLARACION`, `POSEE_SLOT`, `SALIDA_PI2` y `VALIDA`.
- **Contra SM1 (que corrió en `v2`):**
  - Faltan los nodos de INT-R2, R3, R4 y R6 y el software (Docker, VirtualBox), y no hay `necesita_virtualizacion` ni `orden_exigencia`.
  - El empate entre perfiles se desempata por `ram_min`.
  - `PERTENECE` no tiene `estado`, sino `impone_requisitos` y `en_frontera`.
  - INT-R14 no crea las dos lecturas de 0 h y 40 h.
  - **Las `REGLAS_SM1` de PI4 no corren tal cual contra este grafo.**
- **Contra SM2:**
  - Los requisitos salen solo del perfil dominante: no hay REN-R2 que consolide el más exigente entre los perfiles que imponen requisitos.
  - No existe la alerta REN-R13, así que el CP4 de PG1/PG2 («3 alertas») no se cumple.
- **Contra SM3:**
  - La intensidad gráfica se calcula pero no fija la gama mínima de GPU, que sale solo de `Perfil.gama_gpu_min`.
  - No hay alertas GM-R12 ni GM-R17.
- **Contra SM4:** la corrección de REC-R9 con prioridad «precio» no está aplicada, y la prioridad `grafica` no suma peso en REC-R5.
- **Contra PG1/PG2 §8.5 y SM2 §6.1 (tabla de requisitos):** OFI SSD 512, DEV RAM 16/32 y SSD 1024, DIS GPU 3, DATOS CPU alta, GPU 4 y **sin** virtualización excluyente. No hay `ssd_rec`.

**Evidencia completa (09/11/2026, con los tres scripts en [`docs/cypher/`](cypher/) y los PI4 en [`docs/fuentes/`](fuentes/)).** No son tres versiones independientes, sino **dos linajes**:

| Linaje | Archivos | Quién lo usa en PI4 | Rasgos |
| --- | --- | --- | --- |
| **A** | `Grupo_2_PG2_U1.cypher` (1159 líneas) | **SM1** (el notebook lo cita por ese nombre: el «`v2`» que menciona SM1 es este esquema) y **SM2** (lee `riesgo_*` desde `RAM`) | 61 reglas, `NB_A`, `ASOCIADO_A`, `LLEVA_A`, `TIENE_PREGUNTA`, Docker y VirtualBox, `orden_exigencia`, `necesita_virtualizacion`, INT-R14 con lecturas `min`/`max`. **Defecto C-A presente:** riesgo en `RAM`, `grado_gpu` y `adecuacion_grafica` en `Notebook`, y REC-R3 contamina entre pedidos |
| **B** | `Grupo_2_PG2_U1_bloques_0a12.cypher` (1659) → **`Grupo_2_PG2_U1_corregido.cypher` (1739)** | **SM3** (`ES_DE_GAMA`, `ev.*`) y **SM4** (`REQUIERE_ACLARACION`, `CONSULTA_POR`, `ev.*`) | Lo descrito en la evidencia anterior. `corregido` = `bloques_0a12` + la corrección de REC-R9 con prioridad «precio» + el **bloque 13 (L1–L4)**. Es un superconjunto |

**Recomendación:** canónico = **`Grupo_2_PG2_U1_corregido.cypher`**, portándole desde A las piezas de SM1, todas en los bloques 3, 5, 6, 7 y 10.a/10.b:
- `ElementoMencionado`/`Software` (Docker, VirtualBox) con `ASOCIADO_A` y `exige_virtualizacion`, y `necesita_virtualizacion` en el `Requerimiento`.
- `orden_exigencia` para INT-R12 (B desempata por `ram_min`).
- INT-R14 con dos lecturas y `PERTENECE {grado_min, grado_max, estado}`.
- Los nodos de INT-R2, R3, R4 y R6, y los parámetros `dedicacion_min_h`/`dedicacion_max_h`.
- Unificar `APUNTA_A`/`LLEVA_A` y `REQUIERE_ACLARACION`/`TIENE_PREGUNTA` (decisión D-06).

Rehacer C-A sobre A (opción b) tocaría los bloques 10.c a 10.f, las consultas 11 a 13 y también los PI4 de SM3 y SM4, que ya funcionan sobre B.

**Qué implica para el código:**
- **SM1:** `REGLAS_SM1` del notebook se reescriben contra B, o B adopta los nombres de A.
- **SM2:** tu PI4 (`docs/fuentes/SM2/`) pasa a leer riesgo, ρ e índice desde `Evaluacion`, como ya anticipaba PG1/PG2 §10.4.
- **SM3 y SM4:** corren tal cual sobre `corregido`.

**SM2, versión final del PI4:** la copia de `Documents/UTN Mendoza/5. IA/` (53 KB) tiene las guardas del informe (`ampliabilidad_de_la_ram`, umbral de fuerza 0,10, verificación por párrafo). La de `PI/` (44 KB) es la anterior. En el repo quedó la primera. Esto cierra la duda 14-A de SM2.

**Al resolver, reescribir:** PG1/PG2 §6 (conteo de reglas), §8 (modelo), §9 (valores esperados), §10 (C-A: pendiente o hecha), §15–16; SM1 §7.4 y 13-A; SM2 §8 y §14-B; SM3 encabezado («alineada 100 %») y §3; SM4 §5.

### D-02 · Tablas de perfiles: pesos y requisitos — **RESUELTA (09/11/2026)**

> **Decisión del grupo:**
> - Vale la tabla del grafo canónico: pesos de SM4 y requisitos de PG1/PG2 §8.6.
> - **DATOS no exige virtualización**, así que REN-R1 aplica solo a VIRT.
> - **Núcleos, carga sostenida y SSD recomendado quedan fuera del alcance del prototipo**, junto con REN-R4 y REN-R8.
>
> Contextos actualizados: SM2 §3.5, §5.1 y §6.1 (nota sobre la tabla histórica de PI1/PI2), y SM3 §9.2 (gamas de DIS y VID3D).
>
> **Hallazgo nuevo para D-03:** el canónico solo tiene `SALIDA_PI2` para VIRT (y K–OFI), así que un pedido de otro perfil no evalúa ninguna notebook. Lo de abajo describe la situación previa.

**Inconsistencia.**
- **Pesos base:** PG1/PG2 (grafo) y SM4 (PI1) solo coinciden en VIRT y GAM. OFI: 0,30/0,10/0,60 vs 0,4/0,1/0,5; DEV 0,50/0,10/0,40 vs 0,6/0,1/0,3; DIS 0,35/0,45/0,20 vs 0,4/0,5/0,1; VID3D 0,40/0,50/0,10 vs 0,5/0,4/0,1; DATOS 0,50/0,40/0,10 vs 0,7/0,1/0,2. **Los pesos de `req_03` que informa SM4 (0,333/0,083/0,583) salen de la tabla de PI1, no de la de PG2**: con la de PG2 darían 0,25/0,083/0,667. Una de las dos no es la del grafo.
- **Requisitos:** DEV en SM2 es RAM 8/16 y SSD 256/512, y en el grafo 16/32 y 512/1024. DATOS en SM2 es CPU media, SSD 512/1024 y **virtualización excluyente**; en el grafo es CPU alta, SSD 1024/2048 y solo VIRT exige virtualización. Núcleos y carga sostenida solo existen en SM2.
- **GPU:** SM3 (E2E 1) dice que DIS exige dedicada gama ≥ 4 y sRGB ≥ 95 %; el grafo dice DIS gama 2 (y sRGB ≥ 95 %). El extractor de SM3 traduce «gamer» a gama ≥ 4; GAM exige 3, o 2 a 4 según la intensidad.

**Opciones.** a) Manda la tabla del Cypher canónico y se corrigen los contextos *(recomendada)*. b) Adoptar la de SM2/SM4 y cambiar el grafo (cambian todos los valores esperados).
**Archivos:** SM2 §6.1, SM4 §2.7, SM3 §7.3 y §9.2, PG1/PG2 §8.5.

### D-03 · ¿Quién calcula la adecuación de rendimiento (y la de pantalla)? — **RESUELTA (09/11/2026)**

> **Decisión del grupo:** se **completa `SALIDA_PI2`** para los **7 perfiles**. El rendimiento y la pantalla siguen siendo dato de entrada, no se calculan en el grafo, así que `req_01` no cambia.
>
> **Trabajo asignado:**
> - **SM2 (Miranda):** `adecuacion_rendimiento` de las 9 notebooks en OFI, DEV, DIS, VID3D, GAM y DATOS.
> - **SM3 (de Coninck):** `grado_pantalla` para los mismos pares.
> - Se completa la planilla [`docs/cypher/salida_pi2.csv`](cypher/salida_pi2.csv) (53 filas pendientes, más K–OFI, que hoy es un supuesto) y después se carga en el bloque 8 del canónico con su `origen`.
>
> **Condición:** cada uno documenta el método. La fórmula de SP6 sin núcleos ni carga sostenida no reproduce los valores de VIRT (K 0,75 en vez de 0,50; G 0,41 en vez de 0,55), así que el informe tiene que decir con qué reglas se obtuvieron.
>
> Contextos actualizados: PG1/PG2 §8.5, SM2 §4 y SM3 §3. Lo de abajo describe la situación previa.

**Inconsistencia.** SM2 describe el cálculo (SP1–SP8: grados de CPU, RAM y almacenamiento con 0,35/0,40/0,25 y REN-R3, R4, R5, R8 y R12) y el JSON SM2 → SM4. En el grafo, `rend` se **carga como dato fijo** (A 0,90, B 0,80…) y ninguna de esas reglas está cargada. SM4 consume `adecuacion_rendimiento` como si la calculara SM2. Pasa lo mismo con la pantalla: el grafo de PG2 la carga fija y SM3 dice calcular `grado_pantalla` desde sRGB y refresco (depende de D-01).

**Opciones.**
- a) Implementar en Cypher el cálculo de SM2 (cambian los valores de §9).
- b) Declararlo dato de entrada, fuera del prototipo, y reescribir SM2 §3.4, §4 y §5.1 como diseño no implementado. *(Recomendada si no hay tiempo: es lo honesto y no mueve las pruebas.)*

### D-04 · Reglas descritas como vigentes que no están en el grafo — **RESUELTA (09/11/2026)**

> **Decisión del grupo:** se implementan en el canónico **todas** las reglas pendientes. Ya estaban resueltas por D-01 REC-R7, REC-R9 (con prioridad «precio») y REC-R13. Se alinearon a lo que dice el canónico REN-R6 y REN-R9 (retiradas) y REN-R10 (conservar «desconocida»).
>
> | Regla | Qué implementar en `Grupo_2_PG2_U1_corregido.cypher` | Condición |
> | --- | --- | --- |
> | REN-R11 + GM-R15 | Alerta de ancho de banda reducido con GPU integrada y `canal = 'simple'` (K) | No cambia estados ni grados |
> | REN-R14 | Alerta `canal_memoria_no_verificado` con `canal = 'desconocido'` (G) | **No** tratar desconocido como simple (P1-1) |
> | REN-R13 | Alerta de virtualización no informada | Lo esperaba CP4 (3 alertas para G) |
> | REN-R2 | Requisitos = el más exigente entre los perfiles que imponen requisitos | Cambia pedidos mixtos; `req_01` no (solo VIRT impone) |
> | GM-R14 | `gama_gpu` excluyente con 2+ gamas abajo; REC-R3 lo tiene que leer junto con la virtualización | En VID3D y DATOS solo C y X lo superan |
> | GM-R1/GM-R2 | Gama mínima de GPU = f(intensidad) si GAM impone requisitos (baja 2, media 3, alta 4) | Qué hacer con intensidad `incierta`: D-09 |
> | GM-R16 + REC-R16 | Monitor externo: pantalla 1,0 y peso de movilidad × `factor` | SM1 ya extrae `usa_monitor_externo` |
> | INT-R8 | Carrera como pista | **No** fijar el perfil por carrera como conocimiento (pedido de la profesora): solo pregunta o supuesto con alerta |
> | INT-R9 | «Posible contradicción» entre un requisito explícito y el recomendado | Depende de D-10 (`requisitos_explicitos`) |
> | Entropía (INT-R5) | Usar `entropia_max`, que hoy está cargado y sin uso | — |
> | INT-R2/R3/R4/R6 | Se portan desde el linaje A junto con el resto de SM1 (D-01) | — |
>
> Contextos actualizados: SM1 13-C, SM2 §5.1 y nota, SM3 §3 y PG1/PG2 §8.6 y §8.8. Lo de abajo describe la situación previa.

| Regla | Qué dicen los contextos | Opciones |
| --- | --- | --- |
| REN-R11, REN-R14, GM-R15 (aviso de canal simple SM2 → SM3) | SM2 y SM3 las dan por vigentes; SM3 dice que K dispara GM-R15; el E2E-4 de SM2 depende de eso. PG1/PG2: **no existen y `canal` no está en `:RAM`** | Cargar `canal` y las reglas, o declararlas fuera de alcance y sacar el E2E-4 de SM2 y la fila de K en SM3 |
| REN-R6, REN-R9 | SM2: «siguen vigentes hasta validar». Grafo: reemplazadas por FZ-R1..R5 | Alinear el texto de SM2 con el grafo, o volver a activarlas |
| REN-R10 | SM2 §5.1: «asumir no ampliable», lo que contradice la política de la profesora (P1-1) | Reescribir como en FZ-R6 (rango + alerta) |
| REC-R7, REC-R9, REC-R13 | SM4: vigentes. PG1/PG2: no cargadas | Se resuelve con D-01 |
| GM-R1..R3 (intensidad → gama de GPU) | SM1 las cita como implementadas; PG1/PG2 dice que no hay nodo | Cargar el nodo para la traza, o citar la consulta que lo hace |
| INT-R8, INT-R9, banda de frontera y entropía (SM1), REC-R16/R17 | Diseñadas, no implementadas | Declararlas fuera del prototipo en el informe *(recomendada)* |
| REC-R9 con prioridad «precio» | SM4 propone un `ORDER BY` nuevo y un `req_04` para probarlo | Aceptar o no el cambio |

### D-05 · LLM y técnicas permitidas — **RESUELTA (09/11/2026)**

> **Decisión del grupo:**
> - **Ollama local** con **`qwen2.5:7b`** por defecto (A11, verde) y **`qwen2.5:3b`** como alternativa por `OLLAMA_MODEL`.
> - **Temperatura 0** en extracción y en explicación.
> - **HTTP directo a `/api/chat` con `requests`** (amarillo) y salida estructurada (`format`). **Sin LangChain.**
> - **Se quitan** `rich`, `python-dotenv`, `langchain-*` y `ollama`. `pydantic` queda solo para la API y `httpx` solo para los tests.
>
> **Qué tiene que cambiar cada uno:**
> - **SM1:** deja Groq y `langchain-openai`.
> - **SM2:** cambia el modelo por defecto (`llama3.1:8b` → `qwen2.5:7b`).
> - **SM3:** deja LangChain y los extras, y la explicación pasa de 0,3 a 0.
> - **SM4:** la explicación pasa de 0,2 a 0, y `urllib` se reemplaza por `requests`.
>
> Contextos actualizados: SM1 13-H, SM2 §10.3, SM3 §7.3, SM4 §6.1 y §6.5, y README §5. Lo de abajo describe la situación previa.

**Inconsistencia.**
- **SM1** usa **Groq** (`openai/gpt-oss-120b`) con `langchain-openai`. Groq está en rojo en `RESTRICCIONES.md` y `langchain-openai` no está en la lista.
- **SM2** usa Ollama `llama3.1:8b` con `requests`.
- **SM4** usa Ollama `qwen2.5:3b`.
- **SM3** no dice qué modelo usa; usa `pydantic` para la extracción, cuando la lista amarilla lo permite solo para la API.
- **Temperatura:** la explicación va a 0,3 en SM3 y a 0,2 en SM4; el principio 6 de las restricciones pide 0.

**Verificado en el código (`docs/fuentes/`):**
- **SM3** usa `ChatOllama` (`langchain_ollama`) con `qwen2.5:3b`, más `langchain_core`, `rich`, `python-dotenv` y `pydantic`. `langchain_ollama`, `rich` y `python-dotenv` no están en las listas verde ni amarilla.
- **SM4** usa `urllib` (biblioteca estándar) y trae `qwen2.5:7b` por defecto, aunque los casos de PI4 corrieron con `3b`.
- Las temperaturas de explicación, 0,3 en SM3 y 0,2 en SM4, están confirmadas.

**Opciones.** Un solo proveedor (Ollama), un modelo (`qwen2.5:7b`, o `3b`/`llama3.1:8b` si el hardware no da), temperatura 0 en las dos llamadas y un único cliente (`requests` o `ChatOllama`). *(Recomendada: Ollama con qwen2.5 a temperatura 0, con `requests`.)* SM1 tiene que migrar.
**Archivos:** SM1 §9.2 y 13-H; SM3 §7; SM4 §6.5; README §5.

### D-06 · Literales canónicos (estados, escenarios, validación, prioridad, parámetros)

| Concepto | Variantes |
| --- | --- |
| Estado excluyente | `Descartada (excluyente)` (PG2, SM1, SM2) / `Descartada (excluyente incumplido)` (SM4) |
| Estado indeterminado | `Indeterminada: completar información` / `…informacion` sin tilde (SM4) / `Indeterminada` a secas (SM4, REC-R15) |
| Condicionada | `Recomendada condicionada` / `Recomendada condicionada por falta de informacion` |
| Media | `Recomendada (Media)` = etiqueta `considerar` (PG1/PG2 §15.12) |
| `ACTIVA.escenario` | `unico/peor/mejor` (PG2, SM2, SM4) / `unico/min/max` (SM1) |
| `estado_validacion` | `sin validar` (PG2, SM1, SM2) / `provisional` (SM4) |
| Prioridad | SM1: `rendimiento/grafica/portabilidad/autonomia/precio/ninguna`; SM4: sin `grafica` y vacía en lugar de `ninguna` |
| Parámetros | `incremento_prioridad`, `margen_empate` (PG2) / `P_INCREMENTO_PRIORIDAD`, `P_MARGEN_EMPATE` (SM4) / `P_PESO_CPU`… (SM2, no están en el grafo) |
| `GamaGPU` | `nivel`, `indice_exigencia` (SM1) / `indice`, `nombre` + `ES_DE_GAMA` (SM3) |
| `origen_respuesta` | `plantilla fija` (SM1) / `plantilla fija (REC-R11)` (SM2) |

**Opción recomendada:** mandan los literales del Cypher canónico (D-01); los contextos y los prompts se ajustan a ellos.

### D-07 · Contrato común del orquestador

**Inconsistencia.**
- **Intenciones:**
  - SM1: `registrar_pedido`, `aclarar_pedido`, `interpretacion_pedido`.
  - SM2: `riesgo_ram`, `virtualizacion`, `explicar_notebook`, `traza_reglas`, `parametros`.
  - SM3: `grafica`, `movilidad`, `mixta`, `modelo`.
  - SM4: `recomendar`, `explicar_notebook`, `comparar`, `costo_beneficio`.
  - `explicar_notebook` aparece en SM2 y en SM4 con consultas distintas (L2 y Q4).
  - El fuera de dominio se llama `fuera_de_alcance` en SM1–SM3 y `desconocida` en SM4. En SM3, `fuera_de_alcance` **deriva a SM2**.
- **Traza:** las cuatro tienen forma distinta (claves y nombres).
- **Advertencia de parámetros sin validar:** SM2 la omite en `virtualizacion`; SM4 la pone siempre.
- **Explicación:** ≤ 180 palabras (SM1), ≤ 120 por notebook (SM2), 4 a 10 oraciones (SM4), sin límite (SM3). El prompt de SM4 tutea («Eres…, le hablas»), mientras SM1 y SM2 piden voseo. La audiencia es el asesor (PG1, SM1, SM4) o «una persona no técnica» (SM2).
- **Entrada:** máximo 500 caracteres (SM2) o 1500 recortados (SM4).
- **Pedido por defecto:** SM4 usa `req_01` como pedido de sesión. SM2 corrigió en PI4 justamente que el extractor completara `req_01` sin que el usuario lo nombrara.

**Decisiones:** una lista única de intenciones con prefijo de submódulo, una forma de traza y de evidencia con espacio de nombres por submódulo (lo proponen SM1 §12.3 y SM2 §15.1), un prompt de explicación común (SM4 §7.2 lo ofrece), audiencia, tono, longitud y política de pedido por defecto.

### D-08 · Pedidos nuevos: escritura e inferencia incremental

**Inconsistencia.** SM1 escribe un `Requerimiento` por consulta, pero el bloque 10 (SM2–SM4) corre una sola vez sobre todos los pedidos y el script empieza con `MATCH (n) DETACH DELETE n`. Un pedido nuevo **no se puede evaluar** sin recargar todo (PG1/PG2 §15.11, SM1 §12.4-4, SM4 §6.9). Además, una aclaración crea **otro** `Requerimiento` en lugar de actualizar el original (SM1 13-G).

**Opciones.**
- a) Parametrizar los bloques 9 y 10 por `$req`, como ya hizo SM1 con `REGLAS_SM1`, y ejecutarlos con una sesión de escritura solo para el pedido nuevo. *(Recomendada: la piden los E2E de pedido nuevo de SM1 y SM4.)*
- b) Trabajar solo con pedidos precargados y declarar el pedido nuevo como fuera del prototipo.

Además: ¿la aclaración actualiza el mismo pedido y cierra la `Pregunta`?

### D-09 · Incertidumbre de SM1 que nadie consume

**Inconsistencia.**
- **Perfil `indeterminado` por un rango que cruza 0,4:** hoy no impone requisitos de hecho y nadie decidió qué hacer (SM1 §3.5).
- **Perfil dominante con rango:** se ordena por el grado mínimo, y en el CP1 de PI4 salió GAM (SM1 13-E).
- **Intensidad `incierta`:** SM3 no define qué gama mínima exige.

**Opciones.** a) No evaluar el catálogo hasta la aclaración (como con `req_02`). b) Evaluar los dos escenarios. c) Evaluar solo con los perfiles que imponen requisitos y avisar. Para el dominante con rango: dejarlo vacío o marcarlo «provisional». Para la intensidad incierta: tomar la gama del peor caso, la del mejor, o pedir aclaración.

### D-10 · Datos que un submódulo espera y ninguno produce

| Dato | Lo espera | Situación |
| --- | --- | --- |
| `requisitos_explicitos`, `requisitos_institucionales` | SM2 (REN-R2) | SM1 no los extrae ni los guarda |
| `entrena_modelos_gpu` | SM3 §1.2 | SM1 no lo produce |
| `aviso_sm3` (canal) | SM3 (GM-R15) | Ver D-04 |
| JSON de grados SM2 → SM4 | SM2 §3.6 | No existe; SM4 lee del grafo (ver D-03) |

**Opciones:** implementarlos o borrarlos de los contextos y declararlos trabajo futuro.

### D-11 · `req_03` y la prueba de dos compradores (corrección C-C)

**Inconsistencia.** Hay tres propuestas distintas para la misma prueba:
- **PG1/PG2 §10.6:** `req_03` nuevo, OFI («para la facu, ofimática y navegar todos los días, 1000 USD»), con riesgos esperados y la comprobación de que E y G **no** queden descartada o indeterminada (contaminación de REC-R3).
- **SM4:** ya existe un `req_03` con **otro texto**: consulta puntual sobre K, prioridad portabilidad, `CONSULTA_POR` y CP11 (K Recomendada (Media), 0,469).
- **SM1:** propone otro pedido, GAM dominante sobre la Notebook A.

**Opciones.** a) Usar el `req_03` de SM4 y agregar las comprobaciones de PG1/PG2 (E y G no contaminadas, riesgos por pedido). *(Recomendada.)* b) Usar el `req_03` de PG1/PG2 y renombrar el de SM4.
En las dos hay que *verificar* que la versión corregida ya no tenga la contaminación de REC-R3 (PG1/PG2 §10.3).

### D-12 · Numeración de casos y selección de E2E

**Inconsistencia.**
- `CP1`…`CP10` significan cosas distintas en PG2, en el PI4 de SM1 (6 casos) y en el PI4 de SM4 (10 casos).
- `E2E-1`…`E2E-n` tienen contenido distinto en PG1/PG2 (9), SM1 (5), SM2 (5), SM3 (2) y SM4 (7).
- Todos dicen «≥ 3 E2E» con sets diferentes.

**Decisión:** un prefijo por origen (`PG2-CP1`, `SM1-PI4-CP1`, `SM4-PI4-CP1`) y **una sola lista de E2E de PG3**. Candidatos que aparecen en tres contextos o más:
1. recomendación completa de `req_01`;
2. dato faltante (G o M);
3. perfil indeterminado (`req_02`);
4. dos compradores sobre la misma notebook;
5. excluyente frente a puntaje (E).

### D-13 · Estructura común de los contextos

**Inconsistencia.** SM1 y SM2 siguen la misma plantilla: etiquetas `[DOC]`/`[CÓD]`/`[DED]`/`[?]`, correcciones de la profesora, discrepancias y glosario. PG1/PG2 usa otras etiquetas (`[PG1]`, `[PG2]`, `[PROF]`). SM4 no tiene etiquetas ni sección de discrepancias. **SM3 no tiene etiquetas, ni correcciones de la profesora, ni discrepancias, ni línea de tiempo**, y afirma estar «alineado 100 %» con un script que contradice otros contextos.

**Opciones.** a) Llevar los cinco a la plantilla de SM1/SM2. *(Recomendada: hace verificable cada dato.)* b) Agregar solo las secciones faltantes a SM3 y SM4.
Esto le corresponde a cada autor (SM3: de Coninck; SM4: Luconi).

---

## 3. Verificaciones pendientes (necesitan el script, no una decisión)

- **SM3, grado de GPU de X 0,55 y de C 0,916:** con las adecuaciones gráficas de PG2 para `req_01` (X 0,844, C 0,941, pantalla 1,0) darían ≈ 0,74 y ≈ 0,90. SM3 no dice para qué perfil son.
- ~~**SM3, M con «movilidad `null`»**~~ **Resuelto en el canónico:** SM3 deja `adecuacion_movilidad` en `null` y SM4 arma el rango con las lecturas peor y mejor (REC-R15).
- ~~**Alertas de SM3**~~ **Resuelto en el canónico:** solo existen GM-R8 y GM-R11, como dice SM4. GM-R12, GM-R15 y GM-R17 no generan alerta (D-04).
- **SM2 PI4:** la versión final ya está confirmada (SM2 §14-A); falta reconciliar las 27 verificaciones del archivo con las 49 del informe.
- **PG1/PG2 §15.10:** un pedido sin perfil que imponga requisitos deja `req_ram_min` en `null` y luego se divide por `null`.

## 4. Material del repo y lo que todavía falta

En el repo:
- **[`docs/cypher/`](cypher/):** `Grupo_2_PG2_U1.cypher` (linaje A), `Grupo_2_PG2_U1_bloques_0a12.cypher` y `Grupo_2_PG2_U1_corregido.cypher` (**canónico**).
- **[`docs/fuentes/`](fuentes/):** SM1 `Olea_Facundo_PI4_U4.ipynb` (con el host de Aura enmascarado); SM2 `Miranda_Mauricio_PI4_U4.py` (versión final), `test_offline_SM2.py` y `ejecuciones.jsonl`; SM3 `sm3_asistente.py` y `prompts/`; SM4 `Luconi_Martina_PI4_U4.py`.

Todavía falta:
- **PG0** y el **Anexo C** (entrevista al técnico).
- `prompts_PI4_SM4.txt`. No es imprescindible: los prompts de SM4 están dentro del `.py`.
- La `SPEC.md` que cita `sm3_asistente.py`.

El contexto de SM4 cita además rutas `/mnt/project-files/PI4/` y un Drive externo.
