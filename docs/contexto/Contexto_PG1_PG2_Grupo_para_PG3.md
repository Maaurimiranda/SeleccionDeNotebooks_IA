# CONTEXTO DE LAS ENTREGAS GRUPALES (PG1 y PG2) PARA DESARROLLAR PG3

> **Proyecto:** Asistente Experto para la Selección Personalizada de Notebooks · **Grupo 2 · Comisión 5K09 · UTN FRM · Ciclo 2026**
> **Para qué sirve este archivo:** que cualquier persona o asistente de IA entienda, sin haber leído nada más, qué se entregó en PG1 y PG2, qué corrigió la profesora, cuál es el estado real de la base de conocimiento en Neo4j y qué falta hacer para PG3.
> **Complementa a:** `Contexto_SM2_Miranda_para_PG3.md` (detalle del submódulo SM2 y de PI4). Este archivo cubre lo **grupal**; no repite el detalle de SM2.
> **Generado:** 09/11/2026, a partir de `Grupo_2_PG1_U1` (docx), `Grupo_2_PG2_U1` (docx), `Grupo_2_PG2_U1.cypher` y las devoluciones de la profesora a PG1 y PG2.
> **Grafo canónico (D-01, 09/11/2026):** `docs/cypher/Grupo_2_PG2_U1_corregido.cypher`, descrito en §8. Las §5, §6, §7, §9 y §10 se escribieron sobre `Grupo_2_PG2_U1.cypher` (linaje A) y llevan una nota donde el canónico difiere.

---

## 0. Cómo usar este archivo

### 0.1 Etiquetas de procedencia
Cada dato importante lleva una etiqueta, porque la profesora pidió separar lo documentado, lo medido y lo decidido.

| Etiqueta | Significa |
| --- | --- |
| **[PG1]** / **[PG2]** | Está en el informe de esa entrega |
| **[CÓD]** | Está en el script `Grupo_2_PG2_U1.cypher` (la implementación). Si informe y script difieren, **manda el script** |
| **[PROF]** | Lo dijo la profesora en una devolución |
| **[DED]** | Lo deduje yo leyendo el código o recalculando. No está escrito en ningún informe |
| **[?]** | No se sabe; hay que confirmarlo con el grupo o la cátedra |

### 0.2 Qué se leyó y qué NO
- **Leído completo:** informe PG1, informe PG2, script `.cypher` (1083 líneas útiles), devoluciones de PG1 y PG2, texto de la consigna PG3.
- **No disponible:** **PG0** (se lo cita en PG1 y PG2 como origen del flujo Extraer → Consultar → Explicar con LangChain/FastAPI), PI1–PI3 y PI4 de SM1, SM3 y SM4, el Anexo C (entrevista al técnico) y los apuntes de la cátedra. Todo lo que se dice de esos materiales viene de cómo los citan PG1 y PG2. Tampoco se inspeccionaron las **imágenes** (diagramas y capturas) de los dos informes: solo su texto.
- **Verificación realizada [DED]:** reproduje en Python el modelo difuso de SM2 (gaussianas, FZ-R1..R5, centroide sobre 0–100) y **coincide con el informe en los seis valores de riesgo** (A 23,02 · B 50,00 · H 19,31 · K 49,55 · C 18,23 · G [49,58 ; 81,46]). Eso respalda los cálculos nuevos de §10.6.

### 0.3 Las cinco cosas más importantes para PG3
1. **Hay un defecto de diseño que la profesora ya detectó y que es más amplio de lo que ella dijo** (§10): los resultados que dependen del pedido se guardan en `Notebook`, `RAM` y `Lectura`, y un segundo comprador los pisa. Además, la regla REC-R3 **contamina entre compradores** (Notebook_E se descartaría también para quien no pide virtualización). Afecta al código de PI4 de SM2. **Resuelto en el grafo canónico** (§8.4); falta portar el código de SM2.
2. **El modelo difuso no está validado por ningún técnico** (47 etiquetas, 59 parámetros) y B y K dan casi el mismo riesgo por motivos opuestos (§11).
3. **Faltan pruebas que crucen compradores distintos sobre la misma notebook** (§14, caso E2E-6).
4. **Partes del informe PG1 están obsoletas** y no deben copiarse a PG3 (§3.3): la asunción de OFI, el "supuesto conservador", reglas reemplazadas.
5. **Todo funciona hoy sobre 9 notebooks y 2 pedidos de prueba**, no sobre los 30 modelos previstos en PG1.

---

## 1. Mapa de entregas

| Entrega | Qué es | Autoría | Estado en este archivo |
| --- | --- | --- | --- |
| **PG0** | Idea y flujo general (Extraer → Consultar → Explicar, LangChain sobre FastAPI, temperatura 0) | Grupo | **No disponible** [?] |
| **PI1–PI3 (U2)** | Individuales: problema, modelado, lógica difusa de cada submódulo | Cada integrante | Solo se conocen los de SM2 (ver contexto SM2) |
| **PG1 (U1/U2)** | Consolidación conceptual: depuración, macro-proceso, cuaderno de conocimiento, red semántica, frames, reglas, candidatos difusos | Grupo | **Leído** (§4) |
| **PG2 (U1)** | Implementación de la base de conocimiento en Neo4j (script de 14 bloques) + informe | Grupo | **Leído** (§5 a §9) |
| **PI4 (U4)** | Individuales: integración con LLM de cada submódulo | Cada integrante | SM2 en el contexto SM2; el resto [?] |
| **PG3 (U4)** | Orquestación final, pruebas E2E, carpeta final (ZIP) | Grupo | **Tarea pendiente** (§13) |

**Cadena de corrección** [PROF]: PG1 → devolución → PG2 (corrige PG1 y PI3) → devolución → PG3 (debe corregir PG2).

---

## 2. Equipo y convenciones

| Integrante | Legajo | Submódulo |
| --- | --- | --- |
| Olea, Facundo | 47855 | SM1 – Interpretación del requerimiento y perfil de uso |
| Miranda, Mauricio | 50101 | SM2 – Evaluación de rendimiento y capacidad |
| de Coninck, Ramiro | 49998 | SM3 – Evaluación gráfica y de movilidad |
| Luconi Furque, Martina | 48889 | SM4 – Integración, costo-beneficio y recomendación explicable |

[PG1][PG2] Esto resuelve la duda anterior sobre SM4: la responsable es **Luconi Furque (legajo 48889)**; ya no hace falta marcarla "(confirmar)".

**Convenciones**

| Prefijo | Significado | Ejemplo |
| --- | --- | --- |
| `INT-R` / `INT-RD` | SM1: reglas crisp / difusas | INT-R5, INT-RD1 |
| `REN-R` / `FZ-R` | SM2: reglas crisp / difusas | REN-R1, FZ-R4 |
| `GM-R` / `GM-RD` | SM3: crisp / difusas | GM-R12, GM-RD3 |
| `REC-R` / `REC-RD` | SM4: crisp / difusas | REC-R3, REC-RD1 |
| `NB_A` vs `Notebook_A` | `id` interno vs `modelo` visible en el grafo [CÓD] | `modelo = replace(id,'NB_','Notebook_')` |
| `req_01`, `comprador_01` | ids de pedido y de comprador [CÓD] | |
| `CP1`…`CP10`, `C1`…`C3`, `L1`…`L4` | casos de prueba, consultas de inferencia, consultas para el LLM [PG2] | |

**Principio de PG1 [PG1]:** *cada concepto tiene un único submódulo responsable* (el que lo calcula); los demás solo lo reciben. Usuario del sistema = **asesor**; beneficiario = **comprador**.

---

## 3. Devoluciones de la profesora y su estado

### 3.1 Devolución a PG1 [PROF] y cómo respondió PG2

| # | Qué dijo la profesora | Respuesta en PG2 [PG2] | Estado |
| --- | --- | --- | --- |
| P1-1 | Bien: virtualización no informada ≠ "no soportada"; RAM desconocida ≠ "no ampliable"; canal desconocido ≠ "simple". **Mantengan esa lógica** | D4: los valores "no informada", "desconocida", "desconocido" son propios y ninguna consulta los convierte | Cumplido |
| P1-2 | Aplicarlo al **perfil de uso**: asumir OFI **no es neutro** (introduce requisitos y pesos y puede cambiar el ranking). Si no se puede determinar, `perfil_dominante = indeterminado`; luego pedir aclaración o evaluar escenarios | D1: INT-R13 reformulada. `perfil_dominante='indeterminado'`, no se evalúa el catálogo, se crea `(:Pregunta)` y `(:Alerta)` (CP10) | Cumplido |
| P1-3 | "Dato faltante → supuesto conservador" no es la política. **Política general:** excluyente sin dato → *indeterminada*; dato que solo ordena → rango peor/mejor y recomendación *condicionada* | D2: política adoptada. INT-R14 ya no imputa 4 h: crea dos `(:Lectura)` con 0 h y 40 h; grado del perfil en [0,23 ; 0,90]; si el rango cruza 0,4 → `impone_requisitos = indeterminado` + pregunta | Cumplido |
| P1-4 | `Comprador` no es sinónimo de `Requerimiento formal`; si tiene identidad propia, no se fusionan; si se eliminó, explicarlo | D3: se separan `(:Comprador)-[:FORMULA]->(:Requerimiento)`. Un comprador puede hacer varios pedidos y las evaluaciones cuelgan del requerimiento | Cumplido |

### 3.2 Devolución a PG2 [PROF]: lo que **debe corregir PG3**

Lo bueno que reconoció (conservar): integración de los cuatro submódulos; corrección de OFI; diferencia excluyentes/ordenadores; variables difusas con parámetros y reglas **en el grafo**; consultas que muestran pertenencias; **Notebook_E** (adecuación alta no compensa un excluyente); **Notebook_M** (condicionada con rango por autonomía desconocida).

| # | Qué hay que corregir | Qué pide concretamente | Dónde se trata acá |
| --- | --- | --- | --- |
| **C-A** | **Dónde se almacenan los resultados.** Riesgo de obsolescencia, adecuación gráfica y grado de GPU dependen del perfil pero se guardan en la notebook: dos compradores con perfiles distintos se pisan | Guardar esos resultados **en el nodo `Evaluacion` de cada (requerimiento, notebook)**. Las propiedades técnicas del equipo se quedan en `Notebook` | §10 |
| **C-B** | **Calibración del modelo difuso.** FZ-R2 y FZ-R3 dan riesgos muy próximos para situaciones técnicas distintas (RAM suficiente pero soldada vs. insuficiente pero ampliable). Ninguna de las 47 etiquetas está validada: "la gradualidad no demuestra que la recomendación sea correcta" | Contrastar con el técnico; validar centros y dispersiones. Meta: que las reglas difusas **reproduzcan las decisiones de un técnico con experiencia** | §11 |
| **C-C** | **Ampliar las pruebas de integración.** Los 10 casos no prueban qué pasa cuando **dos compradores evalúan la misma notebook con requerimientos distintos** | Agregar esa prueba (detecta la sobrescritura) y verificar que cada recomendación conserva **sus propias evidencias y resultados** | §14 (E2E-6) |

Frase de cierre de la profesora [PROF]: *"lo principal es asegurar que los resultados sean independientes para cada requerimiento y validar que las reglas difusas reproduzcan las decisiones que tomaría un técnico con experiencia."*

### 3.3 Texto de PG1 que quedó **obsoleto** (no copiarlo a PG3)

| Qué dice PG1 | Qué vale hoy (PG2) |
| --- | --- |
| "Pedido ambiguo sin respuesta → se asume OFI con alerta 'perfil asumido'" (casos límite) · INT-R11 a R13 "sin datos → OFI con alerta" | Perfil `indeterminado`, pregunta pendiente, catálogo **no** evaluado (INT-R13 corregida) |
| Excepción "dato de ficha faltante (supuesto conservador con alerta)" | Excluyente sin dato → *Indeterminada*; dato que solo ordena → rango + *condicionada* |
| "El frame Comprador de SM4 se fusionó en Requerimiento formal" | Son dos conceptos separados (`FORMULA`) |
| INT-R14 con 4 h imputadas (PI3 SM1) | Dos lecturas 0 h / 40 h, grado en rango |
| Funciones lineales a trozos en SM2, TSK en SM3, "nivel de specs" en SM4 | Gaussianas con hombro en los extremos y Mamdani en los cuatro; "nivel de specs" fusionado en `suficiencia_ram` |
| REN-R6, REN-R9, REC-R1, REC-R2, REC-R6, REC-R12 como reglas vigentes | Marcadas `reemplazada en PG2` con `reemplazada_por` [CÓD] (§6) |
| Demostración de PG1 (A 0,85 · B 900 USD 0,62 · catálogo "30 notebooks") | Se recalculó con el catálogo de 9 notebooks (A 0,862 · B 700 USD 0,813) |
| GM-R10 como generador de movilidad (TSK) | GM-R10 queda solo para fuzificar y para GM-R11; la movilidad la infieren GM-RD1..3 |

---

## 4. PG1 — Consolidación conceptual

### 4.1 Depuración [PG1] (qué se encontró y cómo se resolvió)

| Tipo | Hallazgo | Resolución |
| --- | --- | --- |
| Terminología | "Notebook" vs "NotebookCandidata"; cuatro nombres de puntajes | Se unifica **Notebook** y *Adecuación de rendimiento / gráfica / movilidad* → SM4 las combina en **Adecuación global** |
| Inconsistencia | Para SM4 la explicación era para el comprador; para el resto, el asesor | Usuario: asesor. Beneficiario: comprador |
| Inconsistencia | "Excluyente" = pedido del comprador (SM4) o condición técnica (SM2, SM3) | Es todo requisito cuyo incumplimiento descarta. SM2/SM3 lo marcan; SM4 aplica MIN y descarta |
| Duplicado | 3 tablas de requisitos por perfil y 4 versiones del Perfil de uso | Una **Tabla de requisitos por perfil** dentro del frame Perfil de uso |
| Duplicado | Expandibilidad (SM4) y Ampliabilidad (SM2); riesgo de obsolescencia en SM2 y SM4 | Ambos quedan en SM2 (responsable de la RAM) |
| Reglas incompatibles | CPU sin virtualización: SM2 "no evaluado" vs SM4 "dato faltante" | **Primero se filtran excluyentes, después se trata la información incompleta** |
| Reglas incompatibles | La entrevista pide más RAM/SSD mínimos que SM2 | Se mantiene la tabla documental; queda como pregunta abierta |
| Vacíos | SM4 no trataba monitor externo ni la "posible contradicción" | REC-R16 y REC-R17 |
| Modelado | Redes con nodos Regla/Evidencia/Parámetro; 3 submódulos con demonios | La red muestra solo el dominio; parámetros a un catálogo; frames sin demonios; prefijos INT/REN/GM/REC |
| Dato desconocido | Ampliabilidad, canal y virtualización "no informada" tratados como "no ampliable", "simple", "no soportada" | Se conserva **"desconocido"**; falta información ≠ no cumple |

### 4.2 Macro-proceso funcional [PG1]

Entradas: pedido del comprador, catálogo (previsto de **30** notebooks, precios al 01/10/2026), tablas de conocimiento, cotización de referencia (BNA). Salida: hasta **3** notebooks con nivel, alertas y explicación, o "Sin alternativa adecuada".

| Subproceso | Responsable | Salida |
| --- | --- | --- |
| P1. Interpretar el pedido | SM1 | Requerimiento formal (perfiles con grado, presupuesto, prioridad, indicadores) |
| P2. Consolidar requisitos | SM2 y SM3 | Requisito más exigente por criterio |
| P3. Evaluar rendimiento y capacidad | SM2 | Adecuación de rendimiento, excluyentes, alertas, **aviso de ancho de banda a SM3** |
| P4. Evaluar gráfica y movilidad | SM3 | Adecuaciones gráfica y de movilidad, excluyentes, alertas |
| P5a. Filtrar | SM4 | Descarta por presupuesto o excluyente; excluyente con "falta información" → *Indeterminada: completar informacion* |
| P5b. Ordenar y recomendar | SM4 | Pondera, umbrales, desempate, alertas; dato que solo ordena → rango + recomendación condicionada |
| P6. Explicar | LLM controlado por SM4 | Explicación verificada para el asesor |

P3 y P4 se repiten **por notebook**, y P3 va primero porque avisa a P4 del ancho de banda reducido. Puntos de decisión compartidos: si un perfil impone requisitos (SM1 decide; SM2 y SM3 usan); si un excluyente se cumple (SM2/SM3 marcan; SM4 descarta); si falta un dato (cada uno aplica su tratamiento y SM4 calcula el rango); monitor externo (SM3 fija pantalla 1,0; SM4 reduce el peso de movilidad).

*Los diagramas (macro-proceso y red semántica integrada) están como imágenes dentro de `Grupo_2_PG1_U1.docx`; se pueden reutilizar en el informe de PG3.*

### 4.3 Cuaderno de conocimiento consolidado [PG1]

- **Alcance:** recomendar hasta tres notebooks según uso y presupuesto, con explicación trazable para el asesor. **Fuera:** decidir la compra, precios en tiempo real, medir componentes, teclado/sonido/construcción, procesadores ARM. **El LLM solo extrae datos y redacta; no decide ni calcula.**
- **Fuentes:** apuntes y guía de la cátedra; requisitos oficiales (Docker, Adobe, DaVinci, PyTorch, Steam); fichas (Intel ARK, AMD, NVIDIA, Lenovo PSREF); Notebookcheck y RTINGS; entrevista a un técnico; casos publicados (r/SuggestALaptop); Mercado Libre y tiendas oficiales; cotización Banco Nación.
- **Glosario unificado:** Comprador, Asesor, Pedido, Requerimiento formal, Perfil de uso (OFI, DEV, VIRT, DIS, VID3D, GAM, DATOS), Perfil dominante, Prioridad, Intensidad gráfica, Notebook, Tabla de requisitos por perfil, Requisito excluyente, Ampliabilidad, Adecuación (rendimiento / gráfica / movilidad / global), Estado de evaluación, Alerta, Índice costo-beneficio.
- **Incertidumbres declaradas:** frecuencia de uso, intensidad gráfica, "liviana", "buena batería", datos de ficha incompletos, grados faltantes entre submódulos.
- **Preguntas abiertas [PG1]:** ¿el "mínimo" del técnico equivale al "recomendado" documental? ¿qué valor de "sobra" corresponde a VIRT, VID3D y DATOS? ¿los pesos y umbrales dan rankings razonables en los 30 modelos?

### 4.4 Catálogo de parámetros provisionales [PG1]
**Todos son decisión del grupo y están sin validar**, salvo lo indicado.

| Parámetro | Valor | Origen | Decisión que modifica |
| --- | --- | --- | --- |
| Umbral de exigencia (INT-R5) | 0,4 | Grupo | Si un uso es requisito o solo preferencia |
| Pesos base por perfil (REC-R4) | Tabla §8.5 | Grupo | Orden del ranking |
| Incremento por prioridad (REC-R5) | +0,2 | Grupo | Orden del ranking |
| Umbrales de recomendación (REC-R6) | 0,6 y 0,8 | Grupo | Qué se recomienda y con qué nivel *(reemplazado por REC-RD)* |
| Tolerancia de presupuesto (REC-R1, R2) | 10 % | Grupo | Descarte o "fuera de presupuesto" *(reemplazado por REC-RD3/RD5)* |
| Margen de empate (REC-R8) | 0,05 | Entrevista + grupo | Cuándo se desempata por ampliabilidad |
| Grados por brecha de gama (REN-R3, GM-R4) | CPU 1,0/0,6/0,2 · GPU 1,0/0,5/0 | Orden de gamas documental; grados del grupo | Grado de CPU/GPU |
| Costo de ampliar RAM (REN-R7) | 30 USD por 8 GB | Mercado Libre 09/2026 | Costo que ve el asesor |
| Factor de autonomía (GM-R12) | 0,7 | Supuesto del grupo (fuente a documentar) | Autonomía estimada |

---

## 5. PG2 — Qué se entregó

**Archivos:** informe `Grupo_2_PG2_U1.docx` + script `Grupo_2_PG2_U1.cypher` (14 bloques, **sin APOC**, datos de carga embebidos). **Neo4j 5.x.** *Canónico desde D-01: `Grupo_2_PG2_U1_corregido.cypher` (§8).*

**Decisiones de PG2** [PG2], además de responder a las devoluciones (§3.1):
- **Dos capas en el grafo:** *dominio* (la red de PG1) y *soporte* (frames, variables, etiquetas, reglas, parámetros).
- **Mamdani en los cuatro submódulos:** AND = MIN, OR = MAX, recorte, agregación MAX, centroide sobre 101 puntos (0–100).
- **Gaussianas** μ(x)=exp(−(x−c)²/2σ²) con **hombro** en las etiquetas extremas (`hombro_izq`: 1 si x ≤ c; `hombro_der`: 1 si x ≥ c).
- **Etiqueta de salida = mayor pertenencia del valor desborrosificado** (en los cuatro; antes SM4 usaba la regla más activada). Efecto: Notebook_B pasa de "recomendar" a "considerar".
- **PERTENECE_A** reservada para la pertenencia difusa; elemento → perfil pasa a **ASOCIADO_A**.
- **Dos "ampliabilidad" separadas:** `indice_ampliabilidad` (difuso, 0–1) y `nivel_ampliabilidad` (ordinal alta/media/baja, REN-R16).
- **`orden_exigencia`** (INT-R12): 1 = más exigente: VID3D > GAM > DATOS > VIRT > DIS > DEV > OFI; ante empate gana el menor.
- **Riesgo de SM2 queda en 0–100**; el resto de las salidas en 0–1 (no se combinan).
- **Intensidad gráfica de SM1 → SM3:** si GAM impone requisitos, la gama mínima de GPU sale de la intensidad (baja → 2, media → 3, alta → 4).
- **Por qué Cypher y no Python [PG2]:** todo (exp, MIN/MAX con CASE, centroide con `UNWIND range(0,100)`) existe en Cypher; la base queda completa en un lugar y la traza se recorre hasta las reglas. Costo: verbosidad y 101× filas intermedias. *Si la base crece, mover el centroide a Python y dejar en el grafo solo parámetros y resultados.*
- **Incertidumbre en 3 lugares:** vaguedad (`PERTENECE_A.grado`, `ACTIVA.fuerza`); falta de dato (`Lectura` con extremos, `_min/_max`, `NO_VERIFICADO`, perfil `indeterminado`); falta de validación (`estado_validacion = 'sin validar'`).

---

## 6. Reglas: estado real en el grafo [CÓD]

**Grafo canónico:** **57 nodos `:Regla`**: **23 `:ReglaDifusa`**, **27 `:ReglaCrisp` vigentes** y **7 retiradas** (REN-R6, REN-R9, REC-R1, REC-R2, REC-R6, REC-R12 y GM-R10). *El linaje A tenía 61: 23 difusas y 38 crisp (32 vigentes + 6 reemplazadas).* *El informe PG2 dice "24 reglas difusas" (matriz b.3), pero el script carga 23 (FZ-R6 y FZ-R7 están como crisp); ver §15.*

### 6.1 Reglas difusas (23) — Mamdani, todas `sin validar`

| SM | Reglas | Qué infieren |
| --- | --- | --- |
| SM1 | INT-RD1..RD3 | `peso_perfil` (marginal / relevante / determinante) a partir de `dedicacion_h` |
| SM1 | INT-RD4..RD7 | `intensidad_grafica` (baja / media / alta) a partir de exigencia del juego × dedicación |
| SM2 | FZ-R1..FZ-R5 | `riesgo_obsolescencia` a partir de `suficiencia_ram` × `indice_ampliabilidad` |
| SM3 | GM-RD1..RD3 | `adecuacion_movilidad` a partir de `peso_kg` × `autonomia_h` |
| SM3 | GM-RD4..RD6 | `grado_gpu` a partir de margen de gama × `potencia_relativa` |
| SM4 | REC-RD1..RD5 | `grado_recomendacion` a partir de `adecuacion_global` × `excedente_presupuesto` |

**Reglas de SM2 (para tener a mano):**
- FZ-R1: insuficiente **y** ampliabilidad poca → **alto** · FZ-R2: insuficiente **y** (media **o** mucha) → **medio**
- FZ-R3: justa **y** poca → **medio** · FZ-R4: justa **y** (media **o** mucha) → **bajo** · FZ-R5: suficiente **o** holgada → **bajo**

**Reglas de SM4:** REC-RD1 alta+dentro → recomendar · RD2 media+dentro → considerar · RD3 alta+levemente excedido → considerar · RD4 media+levemente excedido → descartar · RD5 baja **o** muy excedido → descartar.

### 6.2 Reglas crisp (canónico)

| SM | Vigentes en el canónico | Retiradas (→ por) | Solo en el linaje A |
| --- | --- | --- | --- |
| SM1 (5) | INT-R5, R11, R12, R13, R14 | — | INT-R2, R3, R4, R6 |
| SM2 (6) | REN-R1, R7, R10, R16, FZ-R6, FZ-R7 | **REN-R6** (→ FZ-R3 y FZ-R7), **REN-R9** (→ FZ-R4) | REN-R2, REN-R13 |
| SM3 (6) | GM-R3, R4, R8, R11, R12, R17 | **GM-R10** (→ GM-RD1..RD3) | GM-R14, GM-R16 (y GM-R10 vigente) |
| SM4 (10) | REC-R3, R4, R5, R7, R8, R9, R10, R11, R13, R15 | **REC-R1**, **REC-R2**, **REC-R6**, **REC-R12** (→ REC-RD1..RD5) | REC-R16 |

**Reglas de PG1 que NO están cargadas en el grafo** [CÓD vs PG1] (están en el informe PG1 pero no como nodo): INT-R1, R7, R8, R9, R10, R11; REN-R3, R4, R5, R8, R11, R12, R14, R15; GM-R1..R3, R5..R7, R9, R13, R15; REC-R7, R9, R13, R17. Algunas pueden aplicarse fuera del grafo (PG2 dice que INT-R7 se aplica al cargar el pedido) y de otras no se sabe si están implementadas en el código de cada integrante [?]. **REN-R11, REN-R14 y GM-R15 (el aviso de canal simple a SM3) no existen en el script**: el dato `canal` ni siquiera existe en `:RAM` [CÓD]. *Decidir en PG3 cuáles se cargan, cuáles se implementan y cuáles se declaran fuera de alcance.*

### 6.3 Lo que hace cada regla clave

- **REN-R1 / REN-R13:** perfil exige virtualización → CPU `no soportada` ⇒ `[:INCUMPLE {excluyente:true}]`; CPU `no informada` ⇒ `[:NO_VERIFICADO]` + alerta REN-R13.
- **REN-R10 + FZ-R6:** ampliabilidad desconocida ⇒ dos `Lectura` con a = 0 (peor) y a = 1 (mejor) ⇒ riesgo en rango + alerta. **FZ-R7:** riesgo *alto* en el peor caso ⇒ alerta (no es "regla activada").
- **REN-R7:** RAM < mínimo pero ampliable hasta cumplirlo ⇒ alerta "Condicionado a ampliación" (**no descarta**).
- **GM-R12:** autonomía medida; o 0,7 × declarada (*estimada*); ninguna ⇒ `desconocida`, movilidad en [0 ; 1].
- **REC-R3:** excluyente incumplido ⇒ *Descartada (excluyente incumplido)*; excluyente sin dato ⇒ *Indeterminada: completar informacion*. Una adecuación alta **no** compensa.
- **REC-R15:** falta un dato que solo ordena ⇒ rango y *Recomendada condicionada por falta de informacion*, ordenada por el **peor** caso.
- **REC-R8:** si la diferencia de grado < `margen_empate` (0,05) gana la más ampliable (`nivel_ampliabilidad`: alta < media < baja < desconocida).

---

## 7. Lógica difusa (PG2) [CÓD]

**15 variables, 47 etiquetas, todas con `estado_validacion = 'sin validar'`.** Cada etiqueta es un nodo `(:EtiquetaDifusa {variable, nombre, centro, sigma, tipo, fuente})` ligado por `[:SE_PARAMETRIZA_CON]` a un `(:Parametro {nombre:'centros_y_sigmas_<variable>'})` por variable (en el linaje A era un `mf_<var>_<etiqueta>` por etiqueta). Ninguna consulta tiene valores embebidos.

| Variable (SM) | Universo | Etiquetas: centro · sigma (tipo) |
| --- | --- | --- |
| `dedicacion_h` (1) | 0–40 h/sem | rara_vez 0·1,5 (hi) · ocasional 4·2 · frecuente 12·4,5 · principal 28·8 (hd) |
| `exigencia_grafica` (1) | 0–100 | baja 10·12 (hi) · media 45·12 · alta 80·14 (hd) |
| `peso_perfil` (1, salida) | 0–1 | marginal 0,20·0,12 · relevante 0,60·0,12 · determinante 0,95·0,10 |
| `intensidad_grafica` (1, salida) | 0–1 | baja 0,15 · media 0,50 · alta 0,85 (σ 0,12) |
| `suficiencia_ram` (2) | 0–3 (ρ) | insuficiente 0,5·0,20 (hi) · justa 1,0·0,20 · suficiente 1,5·0,20 · holgada 2,0·0,25 (hd) |
| `indice_ampliabilidad` (2) | 0–1 | poca 0·0,20 (hi) · media 0,5·0,18 · mucha 1,0·0,20 (hd) |
| `riesgo_obsolescencia` (2, salida) | 0–100 | bajo 0·18 · medio 50·15 · alto 100·18 |
| `peso_kg` (3) | 0,8–4 kg | liviana 1,2·0,20 (hi) · intermedia 1,8·0,25 · pesada 2,5·0,30 (hd) |
| `autonomia_h` (3) | 1–24 h | baja 3·1,0 (hi) · media 6,5·1,2 · alta 10·1,5 (hd) |
| `potencia_relativa` (3) | 0–1 (TGP/TGPmáx) | restringida 0,35·0,10 (hi) · moderada 0,60·0,10 · plena 0,80·0,10 (hd) |
| `adecuacion_movilidad` (3, salida) | 0–1 | baja 0,05 · media 0,50 · alta 0,95 (σ 0,12) |
| `grado_gpu` (3, salida) | 0–1 | insuficiente 0,20·0,12 · parcial 0,55·0,12 · pleno 0,95·0,10 |
| `adecuacion_global` (4) | 0–1 | baja 0,40·0,14 (hi) · media 0,70·0,07 · alta 0,90·0,07 (hd) |
| `excedente_presupuesto` (4) | 0–30 % | dentro 0·3 · levemente 10·4 · muy 25·6 (hd) |
| `grado_recomendacion` (4, salida) | 0–1 | descartar 0·0,15 · considerar 0,5·0,15 · recomendar 1,0·0,15 |

**Quedan crisp (hechos verificables de la ficha):** gama de CPU y GPU (ordinal), suficiencia de almacenamiento, virtualización, tipo de disco, cobertura sRGB, condición de excluyente.

**Parámetros crisp del canónico (15) [CÓD]** (más 15 `centros_y_sigmas_*`; total **30** `:Parametro`, con `estado_validacion = 'provisional'`, que D-06 unifica en `'sin validar'`): `umbral_exigencia` 0,40 · `banda_frontera` 0,05 · `entropia_max` 0,60 · `P_COSTO_MODULO_RAM_USD` 30 · `P_PESO_RANURAS_AMPLIABILIDAD` 0,50 · `P_RANURAS_REFERENCIA` 2 · `P_DIF_ALERTA_TGP` 0,20 · `P_GRADO_GPU_UN_NIVEL_ABAJO` 0,50 · `P_PESO_GPU_GRAFICA` 0,60 · `P_PESO_PANTALLA_GRAFICA` 0,40 · `P_ALFA_ALERTA_AUTONOMIA` 0,50 · `P_FACTOR_AUTONOMIA` 0,70 · `P_INCREMENTO_PRIORIDAD` 0,20 · `P_MARGEN_EMPATE` 0,05 · `P_MAX_RECOMENDADAS` 3. *El linaje A tenía 12 base (incluidos `dedicacion_min_h`, `dedicacion_max_h`, `potencia_min_desconocida` y `factor_movilidad_monitor`, que el canónico no tiene) + 47 `mf_*` = 59.*

**Cómo se calcula el riesgo de RAM (SM2) [CÓD]:** ρ = `ram_gb` ÷ `req_ram_min` (tope 3) · índice a = 0,25 × ranuras libres (máx. 2) + 0,5 × min(1, (max_gb − ram_gb) ÷ `req_ram_rec`) · FZ-R1..R5 con MIN/MAX · centroide.

---

## 8. Modelo del grafo canónico [CÓD]

> **Grafo canónico del proyecto (decisión D-01, 09/11/2026): [`docs/cypher/Grupo_2_PG2_U1_corregido.cypher`](../cypher/Grupo_2_PG2_U1_corregido.cypher)** (1739 líneas). Es la «versión corregida» tras la devolución de PG2 que usan SM3 y SM4. Esta sección lo describe y **reemplaza** al modelo de `Grupo_2_PG2_U1.cypher` (linaje A), que es el que usaron SM1 y SM2 en PI4. Las diferencias entre los dos y lo que falta portar están en §8.8. También reemplaza a la sección 8 de `Contexto_SM2_Miranda_para_PG3.md`.

### 8.1 Script por bloques (se ejecutan en orden; `MATCH (n) DETACH DELETE n` al inicio **borra todo**)

| Bloque | Contenido |
| --- | --- |
| 0–1 | Limpieza; **8 restricciones de unicidad** (`Frame.nombre`, `Perfil.codigo`, `Notebook.modelo`, `Comprador.id`, `Requerimiento.id`, `VariableDifusa.nombre`, `Regla.id`, `Parametro.nombre`) y un índice sobre `EtiquetaDifusa(variable, nombre)` |
| 2–3 | Frames (`INSTANCIA_DE`, `POSEE_SLOT`); 7 perfiles con pesos y requisitos; un `Requisito` por perfil y criterio (`ram_gb`, `ssd_gb`, `gama_cpu`, `virtualizacion`, `gama_gpu`) |
| 4 | 15 variables y 47 etiquetas difusas, todas `sin validar` |
| 5 | 5.a 23 reglas difusas · 5.b 27 crisp · 5.c 7 retiradas · 5.d 15 parámetros crisp · 5.e 15 parámetros `centros_y_sigmas_<variable>` · 5.f agenda de validación (`ConsultaExperto`) |
| 6 | Léxico de 14 expresiones de frecuencia, 5 gamas de GPU y 3 juegos (Stardew Valley, Fortnite, Cyberpunk 2077) |
| 7 | 3 compradores, 3 requerimientos y 4 actividades |
| 8 | Catálogo de 9 notebooks; salidas crisp de PI2 por par notebook-perfil (`SALIDA_PI2`); consulta puntual (`CONSULTA_POR`); GM-R12, REN-R16 y potencia relativa |
| 9 | Fuzificación de dedicación, exigencia del juego, peso, autonomía y potencia de GPU |
| 10 | Inferencia **10.a–10.b SM1 · 10.c SM2 · 10.d–10.e SM3 · 10.f SM4** |
| 11 | Consultas C1–C3 |
| 12 | Casos de prueba CP1–CP11 y agenda V1 |
| 13 | Consultas para el LLM L1–L4 (parametrizadas con `$requerimiento_id` y `$modelo`) |

**Sigue vigente [CÓD]:** el bloque 10 corre una sola vez sobre todos los requerimientos. No hay forma de evaluar un pedido nuevo sin volver a ejecutar el script (D-08).

### 8.2 Nodos (labels)

**Dominio:** `Comprador`, `Requerimiento`, `Actividad`, `Juego`, `ExpresionFrecuencia`, `GamaGPU`, `Perfil`, `Requisito`, `Notebook`, `CPU`, `RAM`, `Almacenamiento`, `GPU`, `Pantalla`, `Bateria`, `Evaluacion`, `Lectura`, `Alerta`, `Pregunta`, `Recomendacion`, `SinAlternativaAdecuada`.
**Soporte:** `Frame`, `VariableDifusa`, `EtiquetaDifusa`, `Regla` (+ `ReglaDifusa`/`ReglaCrisp`), `Parametro`, `ConsultaExperto`.
**No existen en el canónico:** `ElementoMencionado`/`Software` (Docker, VirtualBox) ni `Carrera`.

### 8.3 Relaciones

| Relación | Origen → destino | Propiedades |
| --- | --- | --- |
| `FORMULA` | Comprador → Requerimiento | `fecha` |
| `INCLUYE` | Requerimiento → Actividad | |
| `APUNTA_A` | Actividad → Perfil | (perfil de la actividad; en A era `LLEVA_A`) |
| `EXPRESADA_COMO` / `USA` | Actividad → ExpresionFrecuencia / Juego | |
| `RECOMIENDA_GAMA` | Juego → GamaGPU | `fuente` |
| `PERTENECE` | Requerimiento → Perfil | `grado`, `origen`, `impone_requisitos`, `en_frontera` |
| `TIENE_PERFIL_DOMINANTE` | Requerimiento → Perfil | |
| `REQUIERE_ACLARACION` | Requerimiento → Pregunta | (en A era `TIENE_PREGUNTA`) |
| `CONSULTA_POR` | Requerimiento → Notebook | consulta puntual: solo se evalúa esa notebook y no hay ranking |
| `EXIGE` | Perfil → Requisito | |
| `POSEE` | Notebook → CPU, RAM, Almacenamiento, GPU, Pantalla, Bateria | |
| `ES_DE_GAMA` | GPU → GamaGPU | |
| `SALIDA_PI2` | Notebook → Perfil | `adecuacion_rendimiento`, `grado_pantalla`, `origen` |
| `EVALUA` / `SOBRE` | Requerimiento → Evaluacion → Notebook | cruce pedido × notebook |
| `TIENE_LECTURA` | Evaluacion → Lectura | `escenario` `peor`/`mejor` para dato faltante: ampliabilidad desconocida (FZ-R6) o movilidad sin autonomía (REC-R15) |
| `PERTENECE_A` | Actividad, Juego, Notebook, Bateria, GPU, Evaluacion, Lectura → EtiquetaDifusa | `grado`, `valor_crisp`, `ts` |
| `ACTIVA` | Actividad, Requerimiento, Notebook, Evaluacion, Lectura, Recomendacion → Regla | `fuerza` (el escenario está en la `Lectura`: `peor`/`mejor`) |
| `GENERA` | Requerimiento, Notebook o **Evaluacion** → Alerta | |
| `PRODUCIDA_POR` | Alerta → Regla | |
| `RECIBE` | Requerimiento → Recomendacion / SinAlternativaAdecuada | |
| `PROPONE` / `PROPONE_FUERA_DE_PRESUPUESTO` | Recomendacion → Notebook | `orden` |
| `INSTANCIA_DE` / `POSEE_SLOT` | instancia → Frame / Frame → Frame | |
| `TIENE_ETIQUETA` / `SE_PARAMETRIZA_CON` / `VALIDA` | Variable → Etiqueta / Etiqueta → Parametro / ConsultaExperto → Parametro o Regla | |
| `INCUMPLE` / `NO_VERIFICADO` | Notebook → Requisito | **solo las escribe la consulta de demostración C1**; el estado no las lee (§10.3 resuelto) |

### 8.4 Dónde queda cada resultado (corrección C-A aplicada)

| Nodo | Propiedades |
| --- | --- |
| `Evaluacion` (una por requerimiento × notebook; clave `requerimiento` + `notebook`) | `perfil`, `adecuacion_rendimiento`, `grado_pantalla`, `excluyente_virtualizacion` (`no aplica`/`cumple`/`no cumple`/`falta informacion`), `suficiencia_rho`, `indice_ampliabilidad`, `riesgo_valor` o `riesgo_min`/`riesgo_max`, `riesgo_etiqueta`, `grado_gpu`, `margen_gama` (`superior`/`justa`/`inferior`), `adecuacion_grafica`, pesos, `adecuacion_global` o `_min`/`_max`, `excedente_presupuesto`, `dato_faltante`, `grado_recomendacion` o `_min`/`_max`, `etiqueta_recomendacion`/`etiqueta_peor`/`etiqueta_mejor`, `estado`, `indice_costo_beneficio` |
| `Notebook` | `modelo`, `precio_usd`, `peso_kg`, `adecuacion_movilidad`, `movilidad_etiqueta` (la movilidad no depende de quién pregunta) |
| `RAM` | `ram_gb`, `tipo`, `ranuras_libres`, `max_gb`, `canal`, `ampliabilidad`, `nivel_ampliabilidad` (REN-R16) |
| `Bateria` | `autonomia_medida_h`, `autonomia_declarada_h`, `autonomia_usada_h` (GM-R12), `tipo_dato`, `fuente`, `verificada` |
| `GPU` | `gama`, `dedicada`, `vram_gb`, `tgp_w`, `tgp_max_w`, `potencia_relativa` |
| `Requerimiento` | `presupuesto_usd`, `prioridad`, `usa_monitor_externo`, `texto_pedido`, `notebook_consultada`, `perfil_dominante`, `grado_perfil_dominante`, `intensidad_grafica`, `intensidad_valor` |

Alertas que dependen del pedido cuelgan de `Evaluacion`: riesgo de obsolescencia (FZ-R7), condicionado a ampliación (REN-R7), potencia gráfica reducida (GM-R8), autonomía insuficiente (GM-R11), infradimensionamiento (REC-R13) y sobredimensionamiento (REC-R7). Las de la ficha cuelgan de `Notebook`: ampliabilidad no verificada (REN-R10) e información incompleta (REC-R15).

### 8.5 Catálogo de prueba (9 notebooks; precios al 01/10/2026) [CÓD]

| Modelo | USD | CPU (gama, núcleos, virt.) | RAM (GB, tipo, ranuras, máx., canal) | SSD / M.2 | GPU | Pantalla | Autonomía | `SALIDA_PI2` VIRT (rend / pant) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | 950 | alta, 8, soportada | 16 mixta, 1, 64, doble | 1024 / sí | integrada moderna | FHD 60 Hz 65 % | 8,0 h medida | 0,90 / 1,00 |
| B | 700 | media, 8, soportada | 16 **soldada**, 0, 16, doble | 512 / no | integrada moderna | FHD 60 Hz 62 % | 10,0 h medida | 0,80 / 1,00 |
| H | 1000 | alta, 10, soportada | 16 mixta, 1, 32, doble | 1024 / sí | integrada moderna | FHD 60 Hz 58 % | 6,0 h medida | 0,88 / 0,90 |
| K | 900 | media, 8, soportada | **8** mixta, 1, 32, **simple** | 512 / sí | integrada moderna | FHD 60 Hz 60 % | 7,5 h medida | 0,50 / 0,90 |
| X | 1050 | alta, 10, soportada | 16 mixta, 1, 64, doble | 1024 / sí | dedicada media, **60 de 115 W** | FHD 144 Hz 95 % | 7,0 h medida | 0,92 / 1,00 |
| E | 980 | media, 6, **no soportada** | 16 mixta, 1, 32, doble | 1024 / sí | integrada moderna | FHD 60 Hz 70 % | 7,0 h medida | 0,85 / 0,95 |
| C | 1200 | alta, 14, soportada | 16 ampliable, 2, 64, doble | 1024 / sí | dedicada media, 115 de 115 W | QHD 144 Hz 98 % | 5,0 h medida | 0,95 / 1,00 |
| G | 650 | entrada, 4, **no informada** | 8 **desconocida**, —, —, desconocido | 512 / no | integrada moderna | FHD 60 Hz 55 % | 5,7 h declarada (3,99 usada) | 0,55 / 0,80 |
| M | 880 | alta, 8, soportada | 16 mixta, 1, 64, doble | 1024 / sí | integrada moderna | FHD 60 Hz 66 % | **no informada** | 0,88 / 0,95 |

El rendimiento y la pantalla **no se calculan**: se cargan por par notebook-perfil en `SALIDA_PI2` («salidas crisp que SM2 y SM3 ya producían en PI2»). Solo hay pares para VIRT, más **K–OFI (0,80 / 0,90), que es un supuesto del grupo para CP11, pendiente de que SM2 lo recalcule**. Sin un par, la notebook no se evalúa para ese perfil. **D-03 (resuelta):** se completan los 7 perfiles; SM2 calcula el rendimiento y SM3 la pantalla con sus reglas de PI2, sobre la planilla `docs/cypher/salida_pi2.csv`. Hasta cargarlos, solo VIRT y K–OFI son evaluables.

### 8.6 Perfiles (valores provisionales, sin validar) [CÓD]

| Perfil | RAM mín / rec / sobra (GB) | SSD mín (GB) | Gama CPU / GPU mín | Virtualización excluyente | Pesos rend / gráf / mov |
| --- | --- | --- | --- | --- | --- |
| OFI | 8 / 16 / 32 | 512 | entrada / 1 | no | 0,40 / 0,10 / 0,50 |
| DEV | 16 / 32 / — | 1024 | media / 1 | no | 0,60 / 0,10 / 0,30 |
| VIRT | 16 / 32 / — | 512 | media / 1 | **sí** | 0,70 / 0,10 / 0,20 |
| DIS | 16 / 32 / 32 | 1024 | media / 3 | no | 0,40 / 0,50 / 0,10 |
| VID3D | 16 / 32 / — | 1024 | alta / 4 | no | 0,50 / 0,40 / 0,10 |
| GAM | 16 / 32 / 32 | 512 | media / 3 | no | 0,30 / 0,60 / 0,10 |
| DATOS | 16 / 32 / — | 1024 | alta / 4 | no | 0,70 / 0,10 / 0,20 |

Los pesos son los del Anexo D de SM4 (P7). No hay `ssd_rec` ni `orden_exigencia`. Solo el `Requisito` de virtualización de VIRT es excluyente; el de `gama_gpu` no lo es (actúa vía GM-R4 con dos o más gamas abajo). La gama mínima de GPU sale **solo del perfil dominante**: la intensidad gráfica de SM1 se calcula, pero no la modifica. **D-04:** se implementa GM-R1/GM-R2 (la gama sale de la intensidad cuando GAM impone requisitos) y el requisito `gama_gpu` pasa a excluyente con dos o más gamas abajo (GM-R14).

### 8.7 Pedidos cargados [CÓD]

- **`req_01`** (`comprador_01`, Ingeniería en Sistemas; 1000 USD; prioridad rendimiento): *«Necesito una notebook para programar, usar máquinas virtuales y Docker, y a veces jugar al Stardew Valley. Tengo 1000 USD.»* Actividades `act_virtualizar` y `act_programar` (las dos con «la necesito para» → 28 h → VIRT) y `act_jugar` (Stardew Valley, «a veces» → 4 h → GAM).
- **`req_02`** (`comprador_02`; 600 USD; prioridad `ninguna`; `aclaracion: 'sin respuesta'`): *«Quiero una notebook para la facu, tengo 600 USD.»* Sin actividades: perfil `indeterminado`, alerta y pregunta (INT-R13), 0 evaluaciones (CP10).
- **`req_03`** (`comprador_03`, Contador Público; 1000 USD; prioridad portabilidad; **consulta puntual por Notebook_K**): *«Estoy mirando la Notebook_K. ¿Me sirve para la facu? La uso todos los días para Word, Excel y el navegador y la llevo a todos lados. Tengo 1000 USD.»* `act_ofimatica` («todos los días» → 14 h → OFI). Solo se evalúa K (CP11).

### 8.8 Diferencias con el linaje A (`Grupo_2_PG2_U1.cypher`) y qué falta portar

| Tema | Linaje A (SM1 y SM2 en PI4) | Canónico | Acción |
| --- | --- | --- | --- |
| Resultados por pedido | En `RAM` y `Notebook` (defecto C-A) | En `Evaluacion` | Portar las consultas de PI4 de SM2 a `ev.*` |
| Identificador de notebook | `id: 'NB_A'` + `modelo` | solo `modelo` | — |
| Software | `ElementoMencionado`/`Software` (Docker, VirtualBox) con `ASOCIADO_A` y `exige_virtualizacion` | No existe | **Portar** (SM1 lo usa) |
| Virtualización del pedido | `necesita_virtualizacion` (INT-R3) | Sale de `Perfil.requiere_virtualizacion` del dominante | Portar |
| Empate de perfiles (INT-R12) | `orden_exigencia` | `ram_min` | Portar |
| Dedicación desconocida (INT-R14) | Dos lecturas de 0 h y 40 h; `PERTENECE {grado_min, grado_max, estado}` | No hay lecturas; `PERTENECE {impone_requisitos, en_frontera}` | Portar |
| Reglas | 61 nodos | 57 (sin INT-R2, R3, R4, R6, REN-R2, REN-R13, GM-R14, GM-R16 ni REC-R16; suma INT-R11, GM-R3, REC-R7, REC-R9, REC-R13 y GM-R10 como retirada) | **Portar e implementar** (D-04: INT-R2/R3/R4/R6 de SM1, REN-R2, REN-R11, REN-R13, REN-R14, GM-R1/R2, GM-R14, GM-R15, GM-R16, REC-R16, INT-R8, INT-R9 y la entropía) |
| Parámetros | 12 base + 47 `mf_*` = 59 | 15 crisp + 15 `centros_y_sigmas_*` = 30 | — |
| Nombres | `LLEVA_A`, `TIENE_PREGUNTA`, `ACTIVA {escenario}` | `APUNTA_A`, `REQUIERE_ACLARACION`, escenario en `Lectura` | Unificar (D-06) |

---

## 9. Resultados de referencia (valores esperados para las pruebas) [PG2]

Todos sobre `req_01` (perfil VIRT). Reproducibles ejecutando el script completo. Para `req_01` el canónico da los mismos valores que el linaje A (los pesos y requisitos de VIRT no cambiaron), como muestra la corrida de SM4 en Neo4j.

### 9.1 C1 — Excluyente de virtualización (REN-R1 + REC-R3)
**Notebook_E: Descartada** (no soporta virtualización; adecuación 0,810, casi igual que B 0,813 y H 0,811). **Notebook_G: Indeterminada** (virtualización no informada). Las otras 7 siguen en evaluación.

### 9.2 C2 — Riesgo de obsolescencia de la RAM (FZ-R1..R7)

| Notebook | RAM | ρ | índice a | Regla dominante | Riesgo | Etiqueta |
| --- | --- | --- | --- | --- | --- | --- |
| G | 8 GB, desconocida | 0,50 | — | FZ-R1 (peor) / FZ-R2 (mejor) | **[49,58 ; 81,46]** | alto (peor caso) |
| B | 16 GB soldada | 1,00 | 0,000 | FZ-R3 = 1,000 | 50,00 | medio |
| K | 8 GB ampliable | 0,50 | 0,625 | FZ-R2 = 0,786 | 49,55 | medio |
| A, M, X | 16 GB ampliable | 1,00 | 0,750 | FZ-R4 = 0,458 | 23,02 | bajo |
| H, E | 16 GB ampliable | 1,00 | 0,500 | FZ-R4 = 1,000 | 19,31 | bajo |
| C | 16 GB ampliable | 1,00 | 1,000 | FZ-R4 = 1,000 | 18,23 | bajo |

**Lectura [PG2]:** B y K dan casi el mismo riesgo por motivos opuestos. **Es el problema de calibración C-B** (§11). A G no se le asigna un valor: recibe un rango y alerta de riesgo alto por el peor caso.

### 9.3 C3 — Inferencia cruzada SM1→SM4

| Nb | USD | Rend. | Riesgo | Gráf. | Mov. | Global | Exced. | Grado | Estado | En la recomendación |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | 950 | 0,90 | bajo | 1,000 | 0,625 | 0,862 | 0 % | 0,785 | Recomendada (Alta) | puesto 1 |
| B | 700 | 0,80 | medio | 1,000 | 0,776 | 0,813 | 0 % | 0,632 | Recomendada (Media) | puesto 3 |
| H | 1000 | 0,88 | bajo | 0,960 | 0,430 | 0,811 | 0 % | 0,626 | Recomendada (Media) | puesto 2 |
| X | 1050 | 0,92 | bajo | 0,844 | 0,486 | 0,841 | 5 % | 0,534 | Recomendada (Media) | fuera de presupuesto |
| M | 880 | 0,88 | bajo | 0,980 | sin dato | [0,741 ; 0,908] | 0 % | [0,504 ; 0,826] | Recomendada condicionada por falta de informacion | — |
| K | 900 | 0,50 | medio | 0,960 | 0,537 | 0,544 | 0 % | 0,244 | Descartada (alerta REN-R7) | — |
| C | 1200 | 0,95 | bajo | 0,941 | 0,231 | 0,829 | 20 % | 0,191 | Descartada | — |
| E | 980 | 0,85 | bajo | 0,980 | 0,547 | 0,810 | 0 % | — | Descartada (excluyente incumplido) | — |
| G | 650 | 0,55 | [medio ; alto] | 0,920 | 0,239 | 0,529 | 0 % | — | Indeterminada: completar informacion | — |

**Recomendación final:** 1.º **A** (0,785) · 2.º **H** (0,626; empata con B dentro de 0,05 y gana por ampliabilidad) · 3.º **B** (0,632; mejor costo-beneficio 1,161, RAM soldada) · aparte, fuera de presupuesto: **X** (0,534). "Recomendada (Media)" = etiqueta *considerar*. Ejemplo de cálculo [PG2]: A = 0,750×0,90 + 0,083×1,000 + 0,167×0,625 = 0,862.

### 9.4 Casos de prueba CP1–CP11 [PG2] (CP11 solo existe en el canónico)

| # | Situación | Esperado | Obtenido |
| --- | --- | --- | --- |
| CP1 | A cumple todo | Recomendada con el mayor grado | 0,785, Alta, puesto 1 |
| CP2 | E con 0,810 sin virtualización | Descartada | `INCUMPLE`, Descartada (excluyente incumplido) |
| CP3 | X con 0,841 pero 5 % sobre presupuesto | Alternativa, no primera | 0,534, fuera de presupuesto |
| CP4 | G sin virtualización ni ampliabilidad | No descartar; rango y pedir el dato | Indeterminada, [49,58 ; 81,46], **3 alertas** (REN-R13, REN-R10, FZ-R7). *En el canónico no existe REN-R13: quedan 2 (REN-R10 y FZ-R7)* |
| CP5 | K con 8 GB y ranura libre | Riesgo medio, no alto | 49,55, medio; alerta "Condicionado a ampliación" |
| CP6 | C con 2,3 kg y 5 h | Movilidad baja | 0,231, baja |
| CP7 | H y B a 0,006 de diferencia | Desempate por ampliabilidad | H (puesto 2) antes que B (puesto 3) |
| CP8 | Parámetros sin validar | 47 etiquetas sin validar | 47 en 15 variables |
| CP9 | M sin autonomía | Rango y condicionada | [0,504 ; 0,826] |
| CP10 | `req_02` sin respuesta | No asumir OFI | Perfil indeterminado, 0 evaluadas, pregunta pendiente |
| CP11 | `req_03` (OFI, portabilidad) sobre Notebook_K, que `req_01` descarta | Cada evaluación conserva su evidencia | K: Recomendada (Media), grado 0,469, pesos 0,333/0,083/0,583 (corrida de SM4); para `req_01`, Descartada |

### 9.5 Limitaciones que reconoce PG2 [PG2]
1. FZ-R2 y FZ-R3 no distinguen B de K → calibrar consecuentes.
2. El centroide **comprime** las salidas: el grado va de 0,19 a 0,79, por eso se leen por etiqueta.
3. Entre 4 y 5 h de autonomía ninguna etiqueta pasa de 0,6.
4. Rendimiento y pantalla se cargan como crisp (en el canónico, por perfil en `SALIDA_PI2`).
5. **Riesgo, grado de GPU y adecuación gráfica dependen del perfil pero se guardan en la notebook** (⇒ C-A). **Resuelto en el canónico.**
6. Ningún parámetro está validado: "más gradual, no más correcto".

---

## 10. C-A: resultados que se pisan entre compradores

> **Estado (D-01):** el grafo canónico ya aplica el esquema de §10.5 (ver §8.4), y REC-R3 decide por `ev.excluyente_virtualizacion` de cada evaluación, sin la contaminación de §10.3. Esta sección queda como **historia del defecto** y como **guía para portar el código de PI4 de SM2** (§10.4). El `req_03` del canónico no es el de §10.6: es una consulta puntual sobre K (§8.7), así que la prueba de que E y G no queden contaminadas sigue pendiente (D-11).

### 10.1 Qué dijo la profesora y qué encontré [DED]
La profesora señala tres propiedades (riesgo, adecuación gráfica, grado de GPU). **Leyendo el script, el problema es más amplio** y tiene dos efectos: *sobrescritura silenciosa* y *contaminación cruzada de estados*.

### 10.2 Mapa de dónde se guarda cada cosa [CÓD]

`Depende del pedido` = el valor cambia según el requerimiento (perfil, `req_ram_min/rec`, `req_gama_gpu`, monitor externo, prioridad).

| Qué | Dónde se guarda hoy | ¿Depende del pedido? | Veredicto |
| --- | --- | --- | --- |
| `suficiencia_rho` (ρ) | `RAM` | **Sí** (usa `req_ram_min`) | Mover a `Evaluacion` |
| `indice_ampliabilidad` | `RAM` | **Sí**, aunque el nombre no lo sugiere: usa `req_ram_rec` | Mover |
| `nivel_ampliabilidad` (REN-R16) | `RAM` | No (tipo de RAM + M.2) | **Queda en RAM** |
| `riesgo_valor/min/max/etiqueta/peor/mejor` | `RAM` (y copia `riesgo_obsolescencia/etiqueta/rango` en `Notebook`) | **Sí** | Mover |
| `(:Lectura {id: n.id+'_ram_'+esc})` | cuelga de `RAM` | **Sí**; el `id` **solo lleva la notebook** y es **único** ⇒ un segundo pedido hace `MERGE` sobre la misma lectura y la reescribe | Re-keyear con `ev.id` |
| `[:ACTIVA]` de FZ-R1..R5 | `RAM → Regla` | **Sí** (`MERGE` por escenario: sobrescribe `fuerza`) | Mover a `Evaluacion` |
| `margen_gama`, `grado_gpu_por_gama` | `Notebook` | **Sí** (`req_gama_gpu`) | Mover |
| `grado_gpu`, `_min`, `_max` | `Notebook` | **Sí** | Mover |
| `grado_gpu` de cada lectura de potencia | `Lectura n.id+'_potencia_'+esc` | **Sí** (la lectura de potencia en sí no depende; su `grado_gpu` sí) | Separar |
| `adecuacion_grafica`, `_min`, `_max`, `grado_pantalla` | `Notebook` | **Sí** (`usa_monitor_externo`) | Mover |
| `[:ACTIVA]` de GM-RD4..RD6 | `Notebook → Regla` | **Sí** | Mover |
| `adecuacion_movilidad(_min/_max)` + `ACTIVA` GM-RD1..3 + lecturas `_movilidad_` | `Notebook` | **No** (solo peso y autonomía) | **Puede quedarse** (decisión del grupo) |
| `adecuacion_rendimiento` | `Notebook` (crisp de entrada) | Hoy no; en teoría sí [?] | Decidir (§15) |
| Alertas REN-R7, REN-R13, FZ-R7, GM-R8, GM-R11 | `(Notebook)-[:GENERA]->(:Alerta {id: n.id+'_'+regla})` | **Sí** | Re-keyear con `ev.id`, colgar de `Evaluacion` |
| Alertas REN-R10, GM-R12, GM-R17 | ídem | No (dato faltante de la ficha) | Pueden quedar en `Notebook` |
| `[:INCUMPLE]` / `[:NO_VERIFICADO]` | `Notebook → Requisito` | El `Requisito` es del perfil, pero **REC-R3 los lee sin filtrar por perfil** | **Bug de contaminación (§10.3)** |
| `Evaluacion.*`, `Requerimiento.req_*`, `Recomendacion` | `Evaluacion` / `Requerimiento` | Sí, y **ya están bien ubicados** (`id = req + '_' + nb`) | Sin cambios |

### 10.3 Contaminación cruzada por REC-R3 [DED, por lectura del código; no ejecutado]
En el bloque 10.e el estado de cada `Evaluacion` se decide con:
`EXISTS { MATCH (n)-[:INCUMPLE {excluyente:true}]->(:Requisito) }` y `EXISTS { MATCH (n)-[:NO_VERIFICADO]->(:Requisito {es_excluyente:true}) }`.
Esas condiciones **no restringen el `Requisito` al perfil del requerimiento evaluado**. Consecuencia: si `req_01` (VIRT) marca `Notebook_E -[:INCUMPLE]-> Requisito(VIRT, virtualizacion)`, entonces **cualquier otro pedido** (por ejemplo uno de perfil OFI, que no exige virtualización) también verá a E como *Descartada (excluyente incumplido)*. Lo mismo para G (*Indeterminada*). Es el caso inverso al de Notebook_E de PG2 y es exactamente lo que la prueba C-C debe detectar.

### 10.4 Impacto en el código de PI4 de SM2 [CÓD]
En `Miranda_Mauricio_PI4_U4.py` las consultas `Q_C2_RIESGO_RAM`, `Q_L2_EXPLICAR` y `Q_L3_TRAZA` empiezan con `MATCH (c:Requerimiento {id:$req})-[:EVALUA]->(:Evaluacion)-[:SOBRE]->(n)...`, lo que **parece** acotar al pedido, pero luego leen `r.riesgo_valor/min/max/etiqueta`, `r.suficiencia_rho`, `r.indice_ampliabilidad`, `n.riesgo_rango` y `ACTIVA` desde `ram`. Esos valores son **los del último pedido evaluado, sin importar `$req`**. Es peor que un error visible: la respuesta saldría bien formada, citando una regla y un número **de otro comprador**, y el verificador (que solo compara contra la evidencia) **no lo detectaría**.
Cambios necesarios en SM2 (PI4): leer riesgo, ρ, índice y `ACTIVA` desde la `Evaluacion` (`ev`), y que `falta_verificar` use `ev`/`NO_VERIFICADO` del pedido.

### 10.5 Esquema objetivo propuesto [propuesta; decisión del grupo]
- **`Evaluacion` (id `req_NB`)** guarda: ρ, `indice_ampliabilidad`, `riesgo_*`, `margen_gama`, `grado_gpu*`, `adecuacion_grafica*`, `grado_pantalla`, y todo lo de SM4 que ya tiene.
- **Lecturas:** `id = ev.id + '_ram_' + esc` (idem potencia y global), colgando de `Evaluacion`.
- **`ACTIVA`:** desde `Evaluacion` para todas las reglas que dependen del pedido (FZ, GM-RD4..6, REC-RD). Opcional: propiedad `submodulo` para filtrar en L3.
- **Alertas dependientes del pedido:** `id = ev.id + '_' + regla`, `(ev)-[:GENERA]->(al)`. Las independientes (REN-R10, GM-R12, GM-R17) pueden quedar en `Notebook`.
- **`INCUMPLE` / `NO_VERIFICADO`:** pasar a `(ev)-[:INCUMPLE]->(req)` y que REC-R3 consulte `ev`.
- **Quedan en `Notebook`/componentes:** modelo, precio, peso, `ram_gb`, `tipo`, `ranuras_libres`, `max_gb`, `nivel_ampliabilidad`, TGP, pantalla, batería, `adecuacion_movilidad` y sus lecturas.
- **Consultas C2, C3, CP4, CP5, CP7, L2, L3 y las de PI4** deben reescribirse para leer de `Evaluacion`. **Hay que re-ejecutar y reconfirmar CP1–CP10** (los valores de §9 no deben cambiar para `req_01`: es una prueba de regresión del refactor).
- **Frames:** actualizar los slots de `Notebook`, `RAM` y `Evaluacion` en el bloque 2.

### 10.6 Prueba de dos compradores: valores esperados [DED]
Pedido propuesto `req_03` (nuevo `comprador_03`, o `comprador_01` con un segundo pedido, que el modelo permite), **mismo presupuesto 1000 USD** para aislar la variable, perfil **OFI** (p. ej. *"Quiero una notebook para la facu, para ofimática y navegar todos los días, tengo 1000 USD"*; "todos los días" = 14 h por el léxico; hay que **verificar que el grado de OFI supere 0,4** [?]). Para OFI: `req_ram_min = 8`, `req_ram_rec = 16`, y OFI **no** exige virtualización.

Riesgo de RAM esperado por perfil (recalculado con el modelo reproducido, validado contra §9.2):

| Notebook | `req_01` (VIRT: mín 16, rec 32) | `req_03` (OFI: mín 8, rec 16) |
| --- | --- | --- |
| A, M, X | 23,02 (bajo) | **14,05** (bajo; ρ = 2,0) |
| B (soldada) | 50,00 (medio) | **14,05** (bajo) |
| H, E | 19,31 (bajo) | **14,05** (bajo) |
| K (8 GB) | 49,55 (medio) | **23,02** (bajo; ρ = 1,0, a = 0,75) |
| C | 18,23 (bajo) | **14,05** (bajo) |
| G | [49,58 ; 81,46] (alto, peor caso) | **[18,23 ; 50,00]** (medio, peor caso) |

**Qué debe verificar la prueba:** (1) tras evaluar `req_03`, `req_01` sigue dando exactamente los valores de §9 (B 50,00; K 49,55; G [49,58 ; 81,46]); (2) **Notebook_E no queda "Descartada (excluyente incumplido)" para `req_03`** (hoy lo estaría, §10.3); (3) **Notebook_G no queda "Indeterminada" para `req_03`** (OFI no exige virtualización; hoy lo estaría por el mismo bug de §10.3); su RAM de ampliabilidad desconocida solo afecta al rango de riesgo; (4) cada respuesta del asistente cita las reglas y valores de **su** requerimiento. *Estos valores salen de reproducir el modelo en Python, no de ejecutar Neo4j; confirmarlos al correr el script refactorizado.*

---

## 11. C-B: calibración y validación del modelo difuso

### 11.1 El problema, con números [PG2][DED]
B (16 GB soldada) y K (8 GB ampliable) obtienen riesgo casi igual (50,00 vs 49,55) por motivos opuestos:

| Caso | ρ | a | Regla dominante | Riesgo | Situación real |
| --- | --- | --- | --- | --- | --- |
| B | 1,00 | 0,000 | FZ-R3 (justa + poca → medio) | 50,00 | Cumple hoy, **no puede crecer** |
| K | 0,50 | 0,625 | FZ-R2 (insuficiente + media/mucha → medio) | 49,55 | **No cumple hoy**, se arregla con un módulo (~30 USD, REN-R7) |

La profesora no dice cuál es el valor correcto: dice que **lo diga el técnico**. Cualquier ajuste que hagamos sin él es una **decisión del grupo, no una validación**, y así debe figurar en PG3.

### 11.2 Qué se puede hacer
1. **Preparar el contraste con el técnico** (lo que pide la profesora). Llevar una tabla de escenarios de RAM con el riesgo que da el modelo hoy y preguntar: *¿qué riesgo le asignaría y por qué?* Mínimo: B, K, G (rango), A y H (referencia), más 2–3 inventados (p. ej. 8 GB soldada; 32 GB soldada; 16 GB con 2 ranuras libres). Registrar fecha, nombre/rol del técnico y respuestas **como fuente documental** del grafo (`estado_validacion`, `origen`).
2. **Ajustar los consecuentes de FZ-R2/FZ-R3** (centros o reglas) según lo que diga, y **re-ejecutar CP1–CP10** para ver qué cambia en el ranking.
3. **Validar centros y σ de las etiquetas más sensibles** con 3 valores ancla por variable (p. ej. "¿cuántas horas/semana es 'ocasional'?"; "¿desde qué peso es 'pesada'?"). Priorizar las que más pesan: `suficiencia_ram`, `indice_ampliabilidad`, `peso_kg`, `autonomia_h`, `adecuacion_global`, `excedente_presupuesto`.
4. **Si el técnico no está disponible a tiempo [propuesta]:** hacer y documentar un **análisis de sensibilidad** (variar σ ±20 % y centros ±10 % y ver si el ranking de `req_01` y el estado de cada notebook cambian) y declarar con honestidad que la validación sigue pendiente. Eso no reemplaza la validación, pero demuestra qué conclusiones son robustas.
5. **En el informe:** distinguir siempre *valor documental* / *valor de entrevista* / *decisión del grupo* / *sin validar*, y mantener la advertencia que ya viaja hasta la explicación del LLM (L2, `advertencia`).

### 11.3 Otras observaciones de calibración [PG2]
- El centroide comprime el rango de salida (0,19–0,79); por eso la explicación debe usar la **etiqueta**, no el número ("la adecuación es alta", no "0,86").
- Entre 4 y 5 h de autonomía ninguna etiqueta supera 0,6 (zona de baja resolución de GM-RD).
- Los cortes de 0,6 / 0,8 / 10 % de PG1 son **referencias de transición** y, según la profesora (D6), sin validar lo difuso no es más correcto que lo crisp.

---

## 12. Integración con LLM (contrato de PG2) y su relación con PI4

**Regla de oro [PG2][PG1]:** el LLM solo **extrae** datos del pedido y **redacta** la explicación con lo que devuelve el grafo; **no calcula ni decide**. Lo que no tiene evidencia textual se descarta (INT-R7); las horas las pone el léxico del grafo, no el LLM.

| Consulta (bloque 13) | Para qué | Entrada | Salida |
| --- | --- | --- | --- |
| Carga del pedido (bloque 7) | Registrar lo que extrajo el LLM | requerimiento, actividades con evidencia y expresión | Ninguna |
| **L1** Requerimiento formal | Confirmar cómo se entendió el pedido, o qué preguntar si es indeterminado | `$requerimiento_id` | presupuesto, prioridad, perfil dominante, perfiles con grado/estado, intensidad, preguntas pendientes |
| **L2** Explicación de una notebook | Redactar el "por qué" | `$requerimiento_id`, `$modelo` | estado, grado o rango, etiqueta, listas `cumple` / `no_cumple` / `falta_verificar`, alertas, advertencia |
| **L3** Traza de reglas | Citar reglas activadas | ídem | regla, antecedente, consecuente, nodo, escenario, fuerza |
| **L4** Parámetros | Decir qué está validado | — | variable, etiqueta, centro, sigma, estado |

**Formato de salida esperado** (ejemplo Notebook_M [PG2]): `{requerimiento, perfil_dominante, notebook, estado:"Recomendada condicionada por falta de informacion", grado_recomendacion:[0.504,0.826], adecuacion_global:[0.741,0.908], cumple:[…], no_cumple:[], falta_verificar:["autonomía"], alertas:[{tipo:"Autonomía no informada", regla:"GM-R12"}], reglas:[{id:"REC-RD2", escenario:"peor", fuerza:0.842},{id:"REC-RD1", escenario:"mejor", fuerza:1.0}], advertencia:"Los parámetros del modelo difuso están sin validar por el técnico."}`

**Qué necesita el LLM para explicar [PG2]:** (1) estado y **etiqueta** lingüística; (2) los **tres bloques de REC-R11** (cumple / no cumple / falta verificar); (3) alertas con su regla de origen; (4) la regla de mayor fuerza por escenario; (5) la advertencia de parámetros sin validar. **Si el resultado es un rango o un perfil indeterminado, el LLM lo dice así y no completa el dato.** Si la explicación menciona algo ausente de la traza: regenerar hasta 2 veces y luego **plantilla fija** (REC-R11).

**Nota para PG3 [DED]:** L1–L4 de PG2 están escritas con literales (`req_01`, `Notebook_A`); en PI4 SM2 las reemplaza por `$req` y `$modelo` y las amplía (C2 completa, L2 por notebook). Los PI4 de SM1–SM4 están en `docs/fuentes/`; hay que revisar el flujo, los prompts, las consultas y el formato de salida de cada uno antes de diseñar el router y el contrato común (D-07).

---

## 13. PG3 — qué hay que hacer (resumen; detalle en el contexto de SM2 §13)

**Objetivo:** un único asistente que integre Neo4j, reglas, lógica difusa, LLM e interfaz, que **interprete, recupere, infiera, gestione incertidumbre y explique**. No debe parecer "una suma de scripts independientes".

**Actividades:** (1) revisión y depuración final con correcciones documentadas; (2) integración (Neo4j + reglas + difusos + LLM + interfaz: consola, web, API); (3) arquitectura final con diagrama (usuario, interfaz, LLM, orquestación, base de conocimiento, razonamiento, fuentes); (4) **≥ 5 casos de uso integrados** (situación, información, razonamiento, resultado, explicación); (5) pruebas funcionales (recuperación, consultas, reglas, difusa, respuestas) con esperado vs. obtenido; (6) evaluación crítica; (7) trazabilidad (fuente, regla, evidencia, consulta, explicación); (8) reflexión metodológica.

**Productos evaluados:** prompt maestro (enrutamiento y límites; **Neo4j maneja la verdad**) · API/interfaz única sin errores críticos · **≥ 3 pruebas E2E que crucen submódulos** · informe coherente y profesional · ZIP que permita revisar y reproducir.

**ZIP `Grupo_2_PG3_ProyectoFinal.zip`:** a) informe ejecutivo PDF · b) diagramas · c) casos de prueba · d) manual de uso · e) código fuente + `requirements.txt` · f) scripts Cypher · g) configuración · h) recursos complementarios · i) **exportación de Neo4j** · j) datos de ejemplo · k) video/presentación · l) infografía/resumen.

**Estructura del informe:** portada; resumen ejecutivo; problema; arquitectura; base de conocimiento; integración con LLM; casos de uso; pruebas; evaluación; trazabilidad; reflexiones; referencias.

**Cómo se enlazan las devoluciones con PG3:** C-A y C-C alimentan *revisión y depuración* (1) y *pruebas* (5); C-B alimenta *evaluación crítica* (6) y *trazabilidad* (7: cada parámetro lleva `origen` y `estado_validacion`); P1-1..P1-4 son la base del **prompt maestro** (límites: nunca completar un dato desconocido ni un perfil indeterminado).

---

## 14. Casos E2E sugeridos con valores esperados

Cada caso cruza submódulos y usa valores de §9 (verificables contra el grafo). **[a validar]**: la redacción de la consulta depende del router que se diseñe.

| ID | Consulta del usuario (ejemplo) | Submódulos | Debe devolver |
| --- | --- | --- | --- |
| **E2E-1** | `req_01`: "¿Cuál me conviene y por qué?" | SM1 + SM2 + SM3 + SM4 | A (0,785) puesto 1; H puesto 2; B puesto 3; X fuera de presupuesto; explicación en 3 bloques y advertencia de parámetros sin validar |
| **E2E-2** | "¿Por qué la Notebook_M quedó condicionada?" | SM3 + SM4 (+ SM2) | *Recomendada condicionada por falta de informacion*; grado [0,504 ; 0,826]; global [0,741 ; 0,908]; falta verificar: **autonomía**; alerta GM-R12; no inventa una autonomía |
| **E2E-3** | "¿Qué pasa con la Notebook_G?" | SM2 + SM4 | *Indeterminada: completar informacion*; riesgo [49,58 ; 81,46]; alertas REN-R13, REN-R10, FZ-R7; **no** dice "no soporta virtualización" ni "no ampliable" |
| **E2E-4** | `req_02`: "Quiero una notebook para la facu, 600 USD" | SM1 (+ router) | Perfil **indeterminado**, 0 evaluadas, pregunta de aclaración; **no asume OFI** |
| **E2E-5** | "Explicame por qué E no se recomienda, si tiene casi la misma adecuación que B" | SM2 + SM4 | *Descartada (excluyente incumplido)*; REN-R1 + REC-R3; adecuación 0,810 ≈ B 0,813; una adecuación alta no compensa |
| **E2E-6** | **Dos compradores, misma notebook** (`req_01` VIRT y `req_03` OFI sobre B, K y G) | SM1 + SM2 + SM4 | Valores de §10.6 independientes por pedido; E **no** descartada para `req_03`; cada explicación cita las reglas de **su** pedido (**responde a C-C**) |
| **E2E-7** | "¿Qué parámetros del modelo están validados?" | L4 (parámetros) | 47 etiquetas en 15 variables, todas **sin validar** (L4 devuelve solo etiquetas; los 12 parámetros base también están sin validar); no afirma validación |
| **E2E-8** | "¿Cuál es la capital de Francia?" | ninguno | Respuesta fija de fuera de alcance, sin consultar el grafo |
| **E2E-9** | "¿Qué riesgo de RAM tiene la Notebook_K?" en `req_01` y en `req_03` | SM2 | `req_01`: 49,55 medio + alerta REN-R7 "Condicionado a ampliación" (8 GB < 16). `req_03`: 23,02 bajo y **sin** REN-R7 (8 GB ≥ 8) [DED] |

**Para cumplir la consigna** (≥ 3 E2E complejos que crucen submódulos): E2E-1, E2E-2 y E2E-6 alcanzan; E2E-3 a E2E-5 dan los casos de uso integrales (≥ 5).

---

## 15. Discrepancias y notas abiertas

| # | Tema | Detalle |
| --- | --- | --- |
| 1 | **Reglas difusas: 24 vs 23** | PG2 b.3 dice "24 reglas"; el script carga 23 `:ReglaDifusa` (7 INT-RD + 5 FZ + 6 GM-RD + 5 REC-RD). FZ-R6 y FZ-R7 están como crisp. Unificar la cifra en el informe de PG3 [CÓD] |
| 2 | **Riesgo del peor caso de G / K** | PI3 de SM2: [49,6 ; 81,1] · PG2, PI4 y mi reproducción (101 puntos enteros, a = 0): **[49,58 ; 81,46]**. El 49,6 de PI3 coincide con el mejor caso de G (49,58); el 81,1 **no se reproduce** con la discretización del script (probable diferencia de discretización en PI3 [?]). Vale 81,46 [CÓD][DED] |
| 3 | **REC-RD1 de A: 0,863 vs 0,785** | **Resuelto [DED]: no es una contradicción.** 0,863 es la **fuerza** de la regla REC-RD1 (μ_alta de la adecuación 0,862, con excedente "dentro" = 1) y 0,785 es el **grado de recomendación** desborrosificado (CP1). Son magnitudes distintas. Resuelve las discrepancias C y D del contexto de SM2 |
| 4 | **Demo de PG1 vs PG2** | PG1: A 0,85, B 900 USD 0,62 · PG2: A 0,862, B 700 USD 0,813. La demo de PG1 se recalculó; no citar la de PG1 |
| 5 | **Catálogo** | PG1 prevé 30 notebooks; hay 9 cargadas. PI4 de SM2 acepta nombres de una letra (`Notebook_A`..`Z`) |
| 6 | **IDs de notebook** | `NB_A` (id) vs `Notebook_A` (modelo) vs "Notebook K" o "la K" en lenguaje natural |
| 7 | **`rend` y `pantalla` crisp** | SM2 no calcula la adecuación de rendimiento; la recibe. Si el informe de PG3 dice que SM2 "evalúa CPU, RAM y almacenamiento", aclarar que hoy solo calcula virtualización y riesgo de RAM [DED]. En el canónico llegan por perfil en `SALIDA_PI2` (D-03) |
| 8 | **Reglas sin nodo ni implementación** | §6.2: p. ej. REN-R11/R14 y GM-R15 (aviso de canal simple a SM3) no existen en el script. El informe PG1 las describe como vigentes |
| 9 | **`Carrera` sin datos** | INT-R8 y el frame `Carrera` no tienen nodos |
| 10 | **Pedido sin ningún perfil que imponga requisitos** | Si todos los perfiles de un pedido quedan "solo preferencia" (grado < 0,4) pero hay perfil dominante, REN-R2 no consolida requisitos y `req_ram_min`/`req_ram_rec` quedan `null`; luego 10.c divide `ram_gb / null` [DED por lectura; no ejecutado: confirmar con un pedido de prueba] |
| 11 | **Un solo mensaje por vez** | El bloque 10 corre sobre todos los requerimientos a la vez; no hay forma de "evaluar un pedido nuevo" sin re-ejecutar y borrar todo (`MATCH (n) DETACH DELETE n`). Para PG3 necesitamos un procedimiento incremental o un script de carga separado de uno de inferencia |
| 12 | **Estado "Recomendada (Media)" vs "considerar"** | Mismo concepto con dos nombres; unificar en la explicación |
| 13 | **Ranking sin contrastar con los 30 modelos** | La pregunta abierta de PG1 ("¿los pesos dan rankings razonables en los 30 modelos?") sigue sin respuesta: hay 9 notebooks |

---

## 16. Pendientes priorizados para PG3

**Críticos (corrigen lo que pidió la profesora)**
- [x] **C-A en el grafo:** resuelto en el canónico (§8.4).
- [ ] **C-A en el código:** portar a `ev.*` las consultas de PI4 de SM2 (§10.4).
- [ ] **Regresión:** CP1–CP10 deben dar lo mismo para `req_01` sobre el canónico (la corrida de SM4 ya coincide en el ranking; falta confirmar todos los casos).
- [ ] **C-C (parcial):** el canónico tiene CP11 (`req_03` puntual sobre K); falta un pedido OFI que evalúe el catálogo completo (E2E-6, §10.6; D-11).
- [ ] **C-B:** sesión con el técnico (o análisis de sensibilidad como mínimo) y calibrar FZ-R2/FZ-R3; validar centros y σ prioritarios; documentar el estado de validación.

**Integración (lo que pide PG3)**
- [ ] Conseguir y revisar los PI4 de SM1, SM3 y SM4; definir un **contrato común de adaptador** (`submodulos/base.py`).
- [ ] **Prompt maestro** + router (LLM) con límites explícitos: nunca completar dato desconocido ni perfil indeterminado; Neo4j manda.
- [ ] API/interfaz única (`POST /consultar`, `GET /salud`) con `submodulos_consultados`.
- [ ] Verificación **semántica** del verificador (rangos, perfil indeterminado, afirmaciones sin respaldo).
- [ ] Separar el **script de carga** del de **inferencia** (§15.11) y exportar el dump de Neo4j para el ZIP.
- [ ] ≥ 3 E2E y ≥ 5 casos de uso integrales con esperado vs. obtenido (§14).

**Documentación**
- [ ] Informe ejecutivo (PDF), diagramas (reusar los de PG1 y PG2), manual de uso, infografía/resumen, video.
- [ ] Documentar las **correcciones** (PG1→PG2 y PG2→PG3) en `CHANGELOG.md`, como pide la actividad 1.
- [ ] Reconciliar las discrepancias de §15 en una sola cifra por dato.
- [ ] Conseguir **PG0** y el **Anexo C** (entrevista) y completar este archivo.

---

## 17. Glosario mínimo

**Adecuación global:** combinación ponderada de rendimiento, gráfica y movilidad (SM4). **Alerta:** advertencia que **no cambia** el estado de la notebook. **Centroide:** método de desborrosificación sobre 0–100. **Comprador / Requerimiento:** persona vs. su pedido formal; un comprador puede hacer varios. **Evaluación:** nodo del cruce (requerimiento × notebook); debe contener todo lo que depende del pedido. **Excluyente:** requisito cuyo incumplimiento descarta; con dato faltante deja la notebook *indeterminada*. **Lectura:** nodo con un valor de escenario (único, peor, mejor) para propagar un rango. **Mamdani:** inferencia difusa con MIN, MAX, recorte, agregación MAX y centroide. **Perfil indeterminado:** no se pudo determinar el perfil; no se asume ninguno. **Rango peor/mejor:** forma de informar un dato que solo ordena y falta. **Traza:** reglas activadas (`ACTIVA {fuerza, escenario}`) recorridas desde la conclusión.
