# Contexto completo del SM4 para la PG3

**Submódulo 4 – Integración, Costo-Beneficio y Recomendación Explicable**
Autora: Martina Luconi Furque · Legajo 48889 · Comisión 5K09 · Grupo 2 · UTN FRM, Inteligencia Artificial, ciclo 2026
Proyecto: *Asistente Experto para la Selección Personalizada de Notebooks*

Este documento resume todo lo hecho en las actividades individuales del SM4 (PI1, PI2, PI3 y PI4) y lo ordena según lo que pide la PG3: prompt maestro, API única, pruebas E2E que crucen submódulos, arquitectura, trazabilidad, evaluación y reflexión sobre la metodología. Al final hay una sección con lo que el SM4 aporta a la PG3 y lo que queda pendiente.

---

## 0. Resumen en una página

- **Qué hace el SM4.** Cierra el razonamiento del sistema. Toma lo que entregan SM1 (perfil de uso, presupuesto, prioridad), SM2 (adecuación de rendimiento, riesgo de RAM, ampliabilidad) y SM3 (adecuación gráfica y de movilidad), y decide qué notebooks se recomiendan, en qué orden, con qué alertas y por qué. Deja la traza para que el LLM explique sin inventar.
- **Tarea experta.** Recomendación (principal), con Evaluación y Explicación como secundarias. Patrón: generar candidatas, filtrar por restricciones, ordenar por preferencia, explicar.
- **Evolución.**
  - PI1: cuaderno de conocimiento con reglas crisp R1 a R14.
  - PI2: red semántica, frames y reglas, más la entrevista al técnico.
  - PI3: lógica difusa Mamdani con dos entradas y una salida.
  - PG2 (grupal): todo eso implementado en Neo4j, bloque 10.f, con reglas REC-*.
  - PI4: el LLM conectado al grafo con el patrón sándwich, en Python con Ollama.
- **Principio rector, que la PG3 exige:** *Neo4j tiene la verdad.* El LLM solo interpreta la consulta y redacta la explicación. No decide, no calcula y no escribe Cypher. El verificador REC-R11 controla que no invente.
- **Pieza reutilizable para PG3:** `orquestar(texto, bc, llm, req_sesion)` en `Luconi_Martina_PI4_U4.py`. Es una función pura que ya se expone como `POST /consultar` con FastAPI.

---

## 1. Ubicación del SM4 en el sistema

### 1.1 Submódulos del grupo

| SM | Responsable | Función | Qué le entrega al SM4 |
|---|---|---|---|
| SM1 | Facundo Olea | Interpretación del requerimiento y perfil de uso | Perfil dominante (o "indeterminado"), grado de perfil, presupuesto, prioridad, excluyentes y preguntas pendientes |
| SM2 | Mauricio Miranda | Evaluación de rendimiento y capacidad (CPU, RAM, almacenamiento) | `adecuacion_rendimiento`, riesgo de obsolescencia de RAM (FZ-R1 a FZ-R7), `nivel_ampliabilidad` (REN-R16) y excluyente de virtualización (REN-R1) |
| SM3 | Ramiro de Coninck | Evaluación gráfica y de movilidad (GPU, pantalla, peso, autonomía) | `adecuacion_grafica` (por evaluación), `adecuacion_movilidad` (en la notebook) y alertas GM-R8 y GM-R11 |
| **SM4** | **Martina Luconi** | **Integración, costo-beneficio y recomendación explicable** | **Salida final: ranking, estados, alertas, traza y explicación** |
| LLM | Transversal | Interfaz en lenguaje natural | Recibe del SM4 la evidencia estructurada y no modifica la decisión |

### 1.2 Entradas y salidas del SM4

- **Entradas:** perfil dominante y prioridad (SM1), los tres grados de adecuación (SM2 y SM3), precio y presupuesto, el excluyente de virtualización, la ampliabilidad de la RAM y el catálogo.
- **Salidas:**
  - estado por notebook;
  - grado de recomendación (o rango);
  - hasta 3 recomendadas ordenadas, más una alternativa fuera de presupuesto como máximo;
  - "Sin alternativa adecuada" cuando corresponde;
  - alertas con su regla de origen;
  - índice costo-beneficio;
  - traza `[:ACTIVA {fuerza}]`.

### 1.3 Fuera del alcance (desde PI1, se mantiene)

- No evalúa por sí mismo si la CPU, la RAM o la GPU alcanzan: eso lo hacen SM2 y SM3.
- No redacta la explicación: arma los datos y el LLM los traduce.
- No usa precios en tiempo real. El catálogo tiene precios en USD al 01/10/2026 (Mercado Libre Argentina y tiendas oficiales), con el dólar oficial vendedor del BNA de esa fecha.
- No decide por el asesor: la recomendación es una sugerencia ordenada.
- El LLM no modifica el ranking, los grados ni las alertas, y no hace cálculos.
- No sugiere lugares de compra ni negocia precios.

---

## 2. PI1 – Cuaderno de Conocimiento (v1.0, 21/09/2026)

### 2.1 Flujo original del proceso experto

1. **Entrada:** perfil interpretado (SM1), grados de CPU/RAM/almacenamiento (SM2), GPU/pantalla/peso/autonomía (SM3) y catálogo con precios.
2. **Proceso 1 – Filtro:** se descartan las que exceden el presupuesto más la tolerancia o no cumplen un excluyente (por ejemplo, sin virtualización por hardware). Si no sobrevive ninguna, la salida es "Sin alternativa adecuada" con la brecha.
3. **Proceso 2 – Combinación:** promedio ponderado de rendimiento, gráfica y movilidad según el perfil y la prioridad. Si no hay prioridad clara, se usan pesos por defecto y se avisa.
4. **Proceso 3 – Costo-beneficio:** alertas de sobredimensionamiento, infradimensionamiento y riesgo de obsolescencia (RAM soldada por debajo de la recomendada).
5. **Proceso 4 – Orden:** hasta 3, desempate si la diferencia es menor al 5 %.
6. **Salida:** hasta 3 notebooks con nivel, alertas y trazabilidad para el LLM.

### 2.2 Adquisición de conocimiento (fuentes)

| Fuente | Tipo | Uso |
|---|---|---|
| Apuntes U1a, U1b y Guía de Adquisición (cátedra UTN FRM) | Documento | Patrón de recomendación, patrón sándwich, MIN/MAX, promedio ponderado, umbral |
| Russell y Norvig; García Martínez y Britos; Zadeh (1965) | Documento | Fundamentos teóricos |
| Catálogo de prueba (30 modelos previstos; 9 cargados en PG2) | Base de datos | Precios al 01/10/2026 |
| Cotización BNA del 01/10/2026 | Dato | Normalización a USD |
| r/SuggestALaptop | Análisis de casos | Trade-offs y sobrecostos |
| Notebookcheck, RTINGS | Reseñas técnicas | Umbrales de sobre e infradimensionamiento, autonomía medida |
| Fichas de fabricantes (psref.lenovo.com, Dell, HP, ASUS, Acer, MSI, Apple) | Documento | RAM soldada o ampliable, slot M.2 |

### 2.3 Glosario base

- **Restricción dura:** precio por encima del 110 % del presupuesto.
- **Grado de excluyentes:** MIN de los grados de los excluyentes. Si da 0, se descarta.
- **Adecuación global:** promedio ponderado de los tres grados.
- **Índice costo-beneficio:** adecuación global / (precio / presupuesto). En PG2 quedó como adecuación / (precio / 1000).
- **Umbral de recomendación:** alfa-corte de 0,6. "Alta" desde 0,8.
- **Tolerancia:** 10 %.
- **Sobredimensionamiento / infradimensionamiento / riesgo de obsolescencia:** alertas que no descartan la notebook.
- **Traza de inferencia:** reglas activadas más la evidencia.

### 2.4 Reglas candidatas de PI1 (R1 a R14) y qué pasó con cada una

| PI1 | Enunciado resumido | Tipo | Estado en PG2 |
|---|---|---|---|
| R1 | Precio > 110 % del presupuesto → descartar | Determinística | Reemplazada por REC-RD1 a RD5 (difusa) |
| R2 | Precio entre 100 y 110 % y adecuación ≥ mejor + 0,1 → "alternativa fuera de presupuesto" (máx. 1) | Contextual | Reemplazada por REC-RD3 y la consulta de alternativa fuera de presupuesto |
| R3 | MIN de excluyentes = 0 → descartar | Determinística | **REC-R3** (más "falta información → Indeterminada") |
| R4 | Pesos base del perfil dominante | Determinística | **REC-R4** |
| R5 | Prioridad declarada → +0,2 al peso y normalizar | Contextual | **REC-R5** (P_INCREMENTO_PRIORIDAD) |
| R6 | Adecuación < 0,6 → no recomendar | Determinística | Reemplazada por REC-RD* |
| R7 | Supera la gama requerida y hay otra ≥ 0,8 un 25 % más barata → sobredimensionamiento | Heurística | **REC-R7** (en PG2: RAM ≥ `ram_sobra` del perfil) |
| R8 | Diferencia < 0,05 → desempatar por prioridad y luego por precio | Contextual | **REC-R8** (en PG2 desempata por ampliabilidad, criterio del técnico) |
| R9 | Prioridad "precio" → ordenar por costo-beneficio | Contextual | **REC-R9** |
| R10 | Ninguna supera el umbral → "Sin alternativa adecuada" con la brecha | Determinística | **REC-R10** |
| R11 | Si el LLM menciona algo ausente del JSON → regenerar (hasta 2 veces) y luego plantilla fija | Determinística | **REC-R11**, implementada en PI4 con `verificar_explicacion()` |
| R12 | Más de una fuera de presupuesto → elegir la de mayor adecuación | Contextual | Retirada en PG2 (queda la de mayor grado) |
| R13 | Componente por debajo del mínimo del perfil → infradimensionamiento | Heurística | **REC-R13** (RAM < `ram_min`) |
| R14 | RAM soldada por debajo de la recomendada → riesgo de obsolescencia | Heurística | Pasó a SM2 (FZ-R3 y FZ-R7) |
| — | (nueva en PI2/PI3) Dato faltante → rango peor/mejor | Determinística | **REC-R15** |

### 2.5 Casos típicos, límite y excepciones de PI1 (útiles para casos de uso de PG3)

- **Típico 1 (selección clara):** VIRT, 1000 USD, prioridad rendimiento. A (950 USD, 0,85) primera y B (900 USD, 0,62) segunda.
- **Típico 2 (equivalentes):** diferencia menor a 0,05, desempata el criterio de la prioridad.
- **Típico 3 (sobredimensionamiento):** OFI con una gamer de 1100 USD frente a otra de 600 USD con 0,85. Alerta de sobrecosto de 500 USD.
- **Límite 1:** se pasa un 5 % y tiene 0,90 contra 0,72 → "alternativa fuera de presupuesto".
- **Límite 2:** todas entre 0,55 y 0,62 → solo las que superan 0,6, como "Media – con limitaciones".
- **Límite 3:** prioridad precio → I = 0,84/1,0 = 0,84 y J = 0,78/0,7 = 1,11, así que J va primero.
- **Excepción 1:** presupuesto insuficiente. Se informa la más barata del catálogo que supera el umbral y la brecha.
- **Excepción 2:** requisito contradictorio marcado por SM1. Se respeta y se alerta el sobrecosto.
- **Excepción 3:** ninguna pasa el filtro. Se informa la restricción que nadie cubrió.

### 2.6 Incertidumbres detectadas en PI1 (origen de la lógica difusa)

Las cuatro fuentes de incertidumbre fueron:

- la tolerancia de presupuesto (imprecisión);
- los pesos de las prioridades (subjetividad);
- el umbral de recomendación (imprecisión);
- el costo-beneficio (subjetividad).

A eso se suma el tipo de cambio de referencia (incompletitud), que queda como pregunta abierta: con qué frecuencia actualizar la cotización y el catálogo.

### 2.7 Pesos base por perfil (Anexo B/D, parámetro P7, provisional)

| Perfil | Rendimiento | Gráfica | Movilidad | Nota |
|---|---|---|---|---|
| OFI | 0,4 | 0,1 | 0,5 | Prioriza portabilidad |
| DEV | 0,6 | 0,1 | 0,3 | |
| VIRT | 0,7 | 0,1 | 0,2 | Exige virtualización por hardware (excluyente) |
| DIS | 0,4 | 0,5 | 0,1 | |
| VID3D | 0,5 | 0,4 | 0,1 | |
| GAM | 0,3 | 0,6 | 0,1 | |
| DATOS | 0,7 | 0,1 | 0,2 | |

Con la prioridad se suma +0,2 y se renormaliza.

- VIRT con prioridad rendimiento → 0,9 / 0,1 / 0,2 → **0,75 / 0,083 / 0,167**.
- OFI con prioridad portabilidad → 0,4 / 0,1 / 0,7 → **0,333 / 0,083 / 0,583**.

---

## 3. PI2 – Redes semánticas, frames y reglas (Cuaderno v1.1)

### 3.1 Cambios por la devolución de PI1

1. **Conocimiento experto separado de los parámetros de diseño.** Cada número indica su fuente y su estado de validación:

| ID | Parámetro | Valor | Fuente | Estado |
|---|---|---|---|---|
| P1 | Umbral de recomendación | 0,6 | Diseño del grupo | Provisional |
| P2 | Corte Alta/Media | 0,8 | Diseño | Provisional |
| P3 | Tolerancia de presupuesto | 10 % | Diseño | Provisional |
| P4 | Margen de desempate | 0,05 | Diseño | Provisional |
| P5 | Mejora mínima para fuera de presupuesto | 0,1 | Diseño | Provisional |
| P6 | Incremento por prioridad | +0,2 | Diseño | Provisional |
| P7 | Pesos por perfil | Anexo D | Diseño | Provisional |
| P8 | Specs mínimas (OFI, DEV, DIS/GAM) | Entrevista | Técnico | Relevado |
| P9 | Specs "le sobra" | Entrevista | Técnico | A confirmar |
| P10 | RAM "muy poca" | Entrevista | Técnico | A confirmar |
| P11 | Specs de VIRT, VID3D y DATOS | — | Sin fuente experta | Pendiente |
| P12 | Precios del catálogo | 30 notebooks | Mercado | Válido al 02/10/2026 |

2. **Información incompleta.** Antes, si faltaba un grado se redistribuían los pesos, y eso ocultaba la falta. Ahora se calculan el peor caso (dato = 0) y el mejor caso (dato = 1):
   - si el peor caso llega a 0,6 → `Recomendada condicionada por falta de informacion` (en PI2 se llamaba "Recomendada (información incompleta)");
   - si ni el mejor caso llega → Descartada;
   - si el resultado depende del dato → "Indeterminada".

   Siempre se avisa qué dato faltó. Este es el antecedente directo de REC-R15.

3. **Fuente experta.** Entrevista semiestructurada a un técnico con 3 años de experiencia en armado y revisión de PC y notebooks (Anexo C):

| Perfil | Mínimo | Le sobra | RAM "muy poca" |
|---|---|---|---|
| Ofimática / estudio | 8 GB, i3/i5, SSD 512 GB | 32 GB, i7/i9, 2 TB | 8 GB |
| Programación | 16 GB, i5/i7, SSD 1 TB | A confirmar | 8 GB |
| Diseño / gaming | 16 GB, i7/i9, GPU dedicada 8 GB VRAM, ≥ 1 TB | 32 GB o más | 16 GB (diseño) / 8 GB (gaming) |

   - La RAM y el almacenamiento son donde más se "queda corto" un equipo. En diseño y gaming pesa más la VRAM.
   - **Criterio de priorización del experto:** ante dos opciones parecidas, conviene la que se puede mejorar. Se adaptó a notebooks como **ampliabilidad** (en PI2 se llamaba "Expandibilidad"; se unificó con el nombre de PG2): RAM no soldada y slot M.2 libre. La adaptación es decisión del grupo.
   - **Explicabilidad:** el comprador no sabe cuál es su cuello de botella. La explicación debe nombrar el componente limitante y las posibilidades de mejora.
   - **Limitaciones de la fuente:** un solo experto, con sesgo hacia PC de escritorio, que no cubre VIRT, VID3D ni DATOS.

### 3.2 Conceptos de la red semántica

- **Comprador** (centro), con RestricciónPresupuesto, RequisitoExcluyente, Prioridad (rendimiento, portabilidad, precio, autonomía) y PerfilDeUso (OFI, DEV, VIRT, DIS, VID3D, GAM, DATOS).
- **Catálogo** con NotebookCandidata, Precio, EspecificaciónTécnica y GradoAdecuación.
- **ReferenciaDeSpecs** por perfil y **NivelDeSpecs** (Insuficiente, Adecuado, Excedido).
- **Ampliabilidad** (alta, media, baja).
- **Ponderación**, **AdecuaciónGlobal** (o rango), **ÍndiceCostoBeneficio** y **UmbralRecomendación** (0,6 y 0,8).
- **EstadoEvaluación** (con los nombres de PG2, que son los que usa el grafo): `Recomendada (Alta)`, `Recomendada (Media)`, `Recomendada condicionada por falta de informacion`, `Indeterminada: completar informacion`, `Descartada (excluyente incumplido)` y `Descartada`. La "alternativa fuera de presupuesto" de PI2 dejó de ser un estado: en PG2 es una relación `[:PROPONE_FUERA_DE_PRESUPUESTO]`, y la notebook conserva su estado (por ejemplo, X es `Recomendada (Media)`).

> **Equivalencia de nombres PI2 → PG2** (en la PG3 se usan solo los de PG2): NotebookCandidata → `(:Notebook)` + `(:Evaluacion)`; Expandibilidad → `nivel_ampliabilidad`; AdecuaciónGlobal → `adecuacion_global` (o `_min`/`_max`); ÍndiceCostoBeneficio → `indice_costo_beneficio`; Recomendada (información incompleta) → `Recomendada condicionada por falta de informacion`; Indeterminada → `Indeterminada: completar informacion`; RiesgoObsolescencia → riesgo de obsolescencia de SM2 (FZ-R1 a FZ-R7); InformaciónIncompleta → alerta `Informacion incompleta` (REC-R15).
- **Alerta:** Sobredimensionamiento, Infradimensionamiento, RiesgoObsolescencia, InformaciónIncompleta. Una alerta *no implica necesariamente* descartar.
- **Resultados:** Recomendación (hasta 3), SinAlternativaAdecuada y Explicación.

### 3.3 Relaciones principales (origen → verbo → destino)

- Comprador **tiene** RestricciónPresupuesto y RequisitoExcluyente; **declara** Prioridad; **tiene_asociado** PerfilDeUso.
- PerfilDeUso **define** Ponderación y ReferenciaDeSpecs. Prioridad **ajusta** Ponderación.
- Catálogo **contiene** NotebookCandidata. La notebook **tiene** Precio y EspecificaciónTécnica, y **tiene_grado** GradoAdecuación.
- RestricciónPresupuesto y RequisitoExcluyente **filtran** NotebookCandidata.
- EspecificaciónTécnica **se_compara_con** ReferenciaDeSpecs, **cae_en** NivelDeSpecs y **determina** Ampliabilidad.
- Ponderación **pondera** GradoAdecuación, que **compone** AdecuaciónGlobal. Esta **se_compara_con** UmbralRecomendación y **determina** EstadoEvaluación.
- ÍndiceCostoBeneficio **se_calcula_con** AdecuaciónGlobal y Precio. InformaciónIncompleta **modifica** AdecuaciónGlobal.
- EstadoEvaluación **conforma** Recomendación y **genera** SinAlternativaAdecuada. Ampliabilidad **desempata** Recomendación.
- Excedido **sugiere** Sobredimensionamiento. Insuficiente **sugiere** Infradimensionamiento. Ampliabilidad **contribuye_a** RiesgoObsolescencia.
- Alerta **acompaña_a** Recomendación. EstadoEvaluación e ÍndiceCostoBeneficio **fundamentan** Explicación.

### 3.4 Frames (slots y facetas clave)

- **Comprador:**
  - slots: presupuesto > 0, `limite_tolerado` = presupuesto + 10 %, `requisitos_excluyentes`, prioridad y perfil;
  - facetas: prioridad dentro de {rendimiento, portabilidad, precio, autonomía o vacía} y perfil dentro de los 7 códigos.
- **NotebookCandidata:**
  - slots: modelo, precio, ram_gb, ram_soldada, slot_m2_libre, almacenamiento, procesador, gpu, vram, los tres grados, `adecuacion_min` y `adecuacion_max`, indice_costo_beneficio, nivel_ampliabilidad (alta, media o baja), estado_evaluacion y alertas;
  - facetas: grados entre 0 y 1 o vacíos, y `adecuacion_min` ≤ `adecuacion_max`.
- **PerfilDeUso:** tres pesos que suman 1, también después del ajuste por prioridad.
- **ReferenciaDeSpecs:** ram_minima < ram_sobra, estado_validacion. VIRT, VID3D y DATOS quedan pendientes.
- **UmbralRecomendación:** 0 < puntaje_minimo < corte_alta ≤ 1.
- **Alerta:** tipo, notebook y motivo. No cambia el estado.
- **Recomendación:** hasta 3, ordenadas por puntaje (o por costo-beneficio si la prioridad es precio). Si hay empate, va primero la de mayor ampliabilidad.
- **SinAlternativaAdecuada:** notebook_mas_cercana, brecha_precio ≥ 0 y motivo.
- **Explicación:** solo menciona estados, alertas y datos del modelo. Dice qué dato faltó y nombra el componente limitante y si se puede mejorar.

### 3.5 Reglas de conocimiento de PI2 y su clasificación

| Regla | Tipo | Origen |
|---|---|---|
| Presupuesto con tolerancia | Determinística | Grupo |
| Requisito excluyente | Determinística | Grupo |
| Ajuste por prioridad | Determinística | Grupo |
| Asignación por puntaje | Determinística | Grupo |
| Información incompleta | Determinística | Grupo |
| Ampliabilidad | Determinística | Grupo |
| Sin alternativa adecuada | Determinística | Grupo |
| Nivel de specs | Heurística | Técnico |
| Sobredimensionamiento | Heurística | Técnico |
| Infradimensionamiento | Heurística | Técnico |
| Riesgo de obsolescencia | Heurística | Técnico |
| Desempate | Heurística | Criterio del técnico; margen 0,05 del grupo |
| Alternativa fuera de presupuesto | Heurística | Grupo |

Dos detalles de las reglas:

- **Ampliabilidad:** RAM no soldada y M.2 libre → alta; solo una de las dos → media; ninguna → baja.
- **Desempate:** primero la mayor ampliabilidad. Si empatan, la prioridad del comprador, y el menor precio solo si la prioridad es el precio.

**Idea clave para la PG3:** que una regla sea determinística no significa que sus valores estén validados. Todo lo que aportó el técnico es heurístico, y todos los cortes exactos los puso el grupo.

### 3.6 Casos de PI2

- **Caso 1 (Recomendación):** Comprador_1, VIRT, 1000 USD, prioridad rendimiento, pesos 0,75 / 0,08 / 0,17.
  - A: 950 USD, RAM ampliable y M.2 libre, global 0,86.
  - B: 700 USD, RAM soldada, global 0,83.
  - Ambas quedan Alta. La diferencia es 0,03 < 0,05, así que desempata la ampliabilidad y A va primera.
  - La explicación agrega que B es 250 USD más barata, con costo-beneficio 1,19 contra 0,91.
- **Caso 2 (Sin alternativa):** 800 USD, límite 880. C (1200 USD) y D (1100 USD) quedan descartadas. La brecha a la más barata es de 220 USD.

### 3.7 Candidatos a lógica difusa identificados en PI2

- Nivel de specs (8 GB es a la vez "mínimo" y "muy poca").
- Tolerancia de presupuesto (9,9 % frente a 10,1 %).
- Nivel de adecuación (0,79 frente a 0,81).
- "Parecidas" en el desempate.

---

## 4. PI3 – Lógica difusa del SM4

### 4.1 Por qué

Los cortes 0,6, 0,8 y 10 % producen saltos que ninguna persona haría: 0,79 sale "Media" y 0,81 "Alta"; 0,59 se descarta y 0,61 se recomienda; 9,9 % entra y 10,1 % no. Además, las dos variables se compensan: una notebook muy adecuada justifica pasarse un poco del presupuesto. El nivel de specs quedó para una iteración posterior, porque las referencias del técnico son ambiguas.

### 4.2 Variables lingüísticas (gaussianas; hombro en los extremos)

μ(x) = exp(−(x − c)² / (2σ²)). Las de hombro valen 1 desde el borde del universo hasta el centro.

| Variable | Universo | Etiqueta | Tipo | c | σ |
|---|---|---|---|---|---|
| adecuacion_global (entrada) | 0–1 | baja | hombro izq. | 0,40 | 0,14 |
| | | media | gaussiana | 0,70 | 0,07 |
| | | alta | hombro der. | 0,90 | 0,07 |
| excedente_presupuesto (entrada, % sobre el presupuesto; 0 si está dentro) | 0–30 | dentro | gaussiana | 0 | 3 |
| | | levemente | gaussiana | 10 | 4 |
| | | muy | hombro der. | 25 | 6 |
| grado_recomendacion (salida) | 0–1 | descartar | gaussiana | 0 | 0,15 |
| | | considerar | gaussiana | 0,5 | 0,15 |
| | | recomendar | gaussiana | 1 | 0,15 |

- Los cruces caen justo en los cortes de PI2: en 0,6, baja y media valen 0,36 cada una; en 0,8, media y alta también. Así se conserva el criterio documentado, pero sin el salto.
- Más de 30 % de excedente queda fuera del universo y se descarta como restricción dura.
- Fuente de todo: decisión de diseño. Estado: a validar. Son **9 etiquetas provisionales**.

### 4.3 Reglas borrosas (REC-RD1 a REC-RD5 en PG2)

AND = MIN, OR = MAX, agregación MAX, inferencia Mamdani (recorte), desborrosificación por centroide.

| ID | Antecedente | Consecuente |
|---|---|---|
| REC-RD1 | adecuación ALTA y excedente DENTRO | recomendar |
| REC-RD2 | adecuación MEDIA y excedente DENTRO | considerar |
| REC-RD3 | adecuación ALTA y excedente LEVEMENTE | considerar (reemplaza la "alternativa fuera de presupuesto") |
| REC-RD4 | adecuación MEDIA y excedente LEVEMENTE | descartar (no conviene pagar más por algo solo aceptable) |
| REC-RD5 | adecuación BAJA o excedente MUY | descartar |

- El estado sale de la etiqueta de salida con mayor activación. El centroide se usa para ordenar.
- **Ejemplo de PI3:** con 0,79 y 0,81, ambas dentro del presupuesto, el grado da 0,57 y 0,62, una transición gradual.
- **Notebook_C de prueba:** 0,86 con 10,1 % de excedente. Con reglas crisp se descartaba; ahora queda "Considerar" (0,49).

### 4.4 Ventajas y limitaciones (las mismas valen para la evaluación de PG3)

- **Ventajas:**
  - elimina los saltos;
  - deja que una adecuación alta compense un exceso chico;
  - el grado numérico ordena mejor que tres categorías;
  - los parámetros se ajustan sin tocar las reglas.
- **Limitaciones:**
  - sin respaldo experto, el modelo es más gradual pero no más correcto;
  - hay más parámetros que calibrar;
  - **el centroide comprime la salida** (en PG2 va de ≈ 0,19 a ≈ 0,79), así que una notebook perfecta no llega a 1;
  - "pertenece 0,85 a Alta" es menos directo para el usuario, y por eso el LLM debe traducir a la etiqueta.

### 4.5 Preparación para Neo4j (se cumplió en PG2)

- No se guardan estados fijos sino los valores de entrada.
- Los parámetros difusos son conocimiento editable, en `(:VariableDifusa)` y `(:EtiquetaDifusa)` con centro, sigma, tipo, fuente y estado_validacion.
- Las reglas viven en `(:Regla)`.
- La pertenencia se guarda como `[:PERTENECE_A {grado}]`.
- Cuando el técnico valide un parámetro, solo cambia el dato, no la consulta.

---

## 5. PG2 – Implementación del SM4 en Neo4j (bloque 10.f del script grupal)

Script canónico (D-01): `docs/cypher/Grupo_2_PG2_U1_corregido.cypher` (bloques 0 a 13, con la corrección de REC-R9 de §7.1 ya aplicada). `docs/cypher/Grupo_2_PG2_U1_bloques_0a12.cypher` es la misma versión cortada antes del bloque 13 y sin esa corrección; con ella corrieron los casos de PI4. Es la **versión corregida** tras la devolución de PG2.

### 5.1 Corrección clave de PG2 (condiciona todo)

Todo resultado que depende del perfil o del pedido vive en `(:Evaluacion)`, uno por cada par requerimiento × notebook, y **no** en `(:Notebook)`. Eso incluye pesos, adecuación global, excedente, grado, estado, riesgo de RAM, grado de GPU y las alertas que comparan contra el perfil.

- Camino de toda consulta del SM4: `(:Requerimiento)-[:EVALUA]->(:Evaluacion)-[:SOBRE]->(:Notebook)`.
- En `(:Notebook)` solo quedan los datos técnicos y la `adecuacion_movilidad`, que no depende de quién pregunta.
- **CP11:** dos compradores evalúan la misma Notebook_K y cada evaluación conserva su evidencia.
- Comprador y Requerimiento son nodos distintos (devolución de PG1): un comprador puede formular varios pedidos.

### 5.2 Pasos del bloque 10.f (SM4)

1. **Pesos (REC-R4, REC-R5):** pesos del perfil más `P_INCREMENTO_PRIORIDAD` (0,2) según la prioridad, renormalizados, guardados en la evaluación con `[:ACTIVA]` a REC-R4 y REC-R5.
2. **Adecuación global:** `peso_r·adec_rend + peso_g·adec_graf + peso_m·adec_mov`. Excedente = (precio − presupuesto) / presupuesto × 100, o 0 si está dentro.
3. **REC-R15 (dato faltante que solo ordena):** si falta la movilidad (autonomía no informada) se crean dos `(:Lectura)`, peor (mov = 0) y mejor (mov = 1). En la evaluación queda `adecuacion_global_min/max`, `dato_faltante` y una alerta "Información incompleta".
4. **Fuzificación** de adecuacion_global y excedente (tope 30) con `[:PERTENECE_A {grado}]`.
5. **REC-RD1 a RD5:** Mamdani sobre 101 puntos, centroide → `grado_recomendacion` y `etiqueta_recomendacion`, con traza `[:ACTIVA {fuerza, escenario}]`. Con rango, `grado_recomendacion_min/max`, `etiqueta_peor` y `etiqueta_mejor`.
6. **Estado (política general de dato faltante):**
   - excluyente "no cumple" → `Descartada (excluyente incumplido)`;
   - excluyente "falta informacion" → `Indeterminada: completar informacion`;
   - con rango, peor caso ≠ descartar → `Recomendada condicionada por falta de informacion`;
   - con rango, mejor caso = descartar → `Descartada`;
   - con rango en el resto de los casos → `Indeterminada`;
   - sin rango, etiqueta recomendar → `Recomendada (Alta)`;
   - sin rango, etiqueta considerar → `Recomendada (Media)`;
   - si no → `Descartada`.
7. **Costo-beneficio (REC-R9):** adecuación (o la mínima) / (precio / 1000).
8. **Alertas:**
   - REC-R13: Infradimensionamiento, RAM < `ram_min` del perfil.
   - REC-R7: Sobredimensionamiento, RAM ≥ `ram_sobra` del perfil.
   - Todas quedan ligadas `(:Alerta)-[:PRODUCIDA_POR]->(:Regla)`.
9. **Recomendación (REC-R8 y REC-R9):** recomendadas dentro del presupuesto, sin consulta puntual, ordenadas por:
   - **si la prioridad del pedido es "precio"**, primero por `indice_costo_beneficio` descendente (REC-R9);
   - `floor(grado / P_MARGEN_EMPATE)` descendente, de modo que las que caen en la misma franja de 0,05 empatan;
   - luego por ampliabilidad (alta 3, media 2, baja 1);
   - luego por costo-beneficio.

   Con rango se ordena por el peor caso. El primer criterio es la corrección de REC-R9 para la PG3 (ver 7.1). En el script de PG2 tal como se entregó, el orden no miraba la prioridad. Se toman hasta `P_MAX_RECOMENDADAS` (3) y se arma `(:Recomendacion)-[:PROPONE {orden}]`.
10. **Alternativa fuera de presupuesto:** la recomendada con excedente > 0 y mayor grado, como `[:PROPONE_FUERA_DE_PRESUPUESTO]` (máximo 1).
11. **REC-R10:** si no hay recomendación (y el perfil no es indeterminado ni es una consulta puntual), se crea `(:SinAlternativaAdecuada {motivo})`.

### 5.3 Reglas REC vigentes (nodos `(:Regla)`, estado "sin validar")

| ID | Tipo | Enunciado |
|---|---|---|
| REC-R3 | Determinística | SI MIN de excluyentes = 0 → descartar; SI algún excluyente tiene falta de información → Indeterminada y no comparar |
| REC-R4 | Contextual | La adecuación global pondera rendimiento, gráfica y movilidad con los pesos del perfil dominante |
| REC-R5 | Contextual | SI el comprador declara una prioridad → se suma P_INCREMENTO_PRIORIDAD a ese peso y se renormaliza |
| REC-R7 | Heurística | SI una spec alcanza el valor "sobra" del perfil → alerta de sobredimensionamiento, sin descartar |
| REC-R8 | Heurística | SI la diferencia de grado_recomendacion < P_MARGEN_EMPATE → desempatar por nivel_ampliabilidad |
| REC-R9 | Contextual | Índice costo-beneficio = adecuación global / (precio / 1000); SI la prioridad es precio → ordena por este índice |
| REC-R10 | Determinística | SI ninguna queda recomendada → "Sin alternativa adecuada" con la restricción no cubierta |
| REC-R11 | Determinística | La explicación va en tres bloques (cumple, no cumple, falta verificar) y no menciona nada ausente de la traza |
| REC-R13 | Heurística | SI un requisito queda parcialmente cumplido (RAM < mínimo) → infradimensionamiento, sin descartar |
| REC-R15 | Determinística | SI falta un dato que solo ordena → adecuación mín./máx., grado en los dos escenarios; peor caso no descartar → condicionada; mejor caso descartar → Descartada; si no → Indeterminada |
| REC-RD1..RD5 | Difusas | Ver 4.3 |

Las reglas retiradas (REC-R1, R2, R6 y R12) se conservan como nodo, con `estado_validacion = 'reemplazada en PG2'` y `reemplazada_por = 'REC-RD1..REC-RD5'`, para la trazabilidad.

**Parámetros crisp del SM4** (`(:Parametro)`, todos "provisional"): `P_INCREMENTO_PRIORIDAD = 0,20`, `P_MARGEN_EMPATE = 0,05` y `P_MAX_RECOMENDADAS = 3`.

**Agenda de validación con el técnico** (`(:ConsultaExperto)`, bloque 5.f, preguntas en términos del dominio):

- *adecuacion_global:* "¿Con qué puntaje global recomendaría una notebook sin dudar, y con cuál la dejaría para considerar? Hoy los cruces están en 0,6 y 0,8."
- *excedente_presupuesto:* "¿Cuánto por encima del presupuesto acepta ofrecer un equipo? Hoy 'levemente excedido' se centra en el 10 % y más del 30 % se descarta."
- *grado_recomendacion:* "¿Prefiere ver como 'para considerar' una notebook que cumple todo pero se pasa un poco, o que no aparezca?"

### 5.4 Datos de ejemplo cargados

**Catálogo de 9 notebooks** (precios al 01/10/2026):

| Modelo | USD | CPU / virtualización | RAM | Ampliabilidad | GPU | Autonomía | Papel en las pruebas |
|---|---|---|---|---|---|---|---|
| Notebook_A | 950 | alta / sí | 16 mixta, 1 ranura, máx. 64 | alta | integrada | 8 h medida | Positivo, puesto 1 |
| Notebook_B | 700 | media / sí | 16 soldada | baja | integrada | 10 h | Desempate, mejor costo-beneficio |
| Notebook_H | 1000 | alta / sí | 16 mixta, máx. 32 | alta | integrada | 6 h | Desempate con B |
| Notebook_K | 900 | media / sí | 8 mixta, máx. 32 | alta | integrada | 7,5 h | CP11 (dos compradores) |
| Notebook_X | 1050 | alta / sí | 16 mixta | alta | dedicada media, TGP 60 de 115 W | 7 h | Fuera de presupuesto (5 %), alerta GM-R8 |
| Notebook_E | 980 | media / **no** | 16 mixta | alta | integrada | 7 h | Excluyente incumplido |
| Notebook_C | 1200 | alta / sí | 16 ampliable, 2 ranuras | alta | dedicada media 115 W | 5 h | Muy excedida → descartada |
| Notebook_G | 650 | entrada / **no informada** | 8 desconocida | desconocida | integrada | 5,7 h declarada | Indeterminada (falta un dato excluyente) |
| Notebook_M | 880 | alta / sí | 16 mixta | alta | integrada | **sin dato** | Dato que solo ordena → rango (REC-R15) |

**Pedidos:**

- **req_01** (comprador_01): "Necesito una notebook para programar, usar máquinas virtuales y Docker, y a veces jugar al Stardew Valley. Tengo 1000 USD." Prioridad rendimiento, perfil dominante VIRT (grado 0,899).
- **req_02** (comprador_02): "Quiero una notebook para la facu, tengo 600 USD." Perfil indeterminado y pregunta pendiente. No se evalúa ninguna notebook y no se asume OFI (INT-R13 reformulada).
- **req_03** (comprador_03): "Estoy mirando la Notebook_K. ¿Me sirve para la facu? La uso todos los días para Word, Excel y el navegador y la llevo a todos lados. Tengo 1000 USD." Prioridad portabilidad, perfil OFI. Es una **consulta puntual** (`[:CONSULTA_POR]`): se responde con la evaluación, sin ranking.

**Resultado real de Neo4j para req_01** (pesos 0,75 / 0,083 / 0,167):

| Notebook | Adecuación | Grado | Estado | Costo-beneficio | Lugar |
|---|---|---|---|---|---|
| A | — | 0,785 | Recomendada (Alta) | 0,907 | Puesto 1 |
| H | 0,811 | 0,626 | Recomendada (Media) | 0,811 | Puesto 2 (ampliabilidad alta) |
| B | 0,813 | 0,632 | Recomendada (Media) | 1,161 | Puesto 3 (ampliabilidad baja; REC-R8) |
| X | — | 0,534 | Recomendada (Media), excedente 5 % | 0,801 | Alternativa fuera de presupuesto, alerta GM-R8 |
| M | [0,741 ; 0,908] | [0,504 ; 0,826] | Recomendada condicionada por falta de información | 0,842 | No entra en el ranking; alerta REC-R15 |
| E | 0,81 | 0,623 | Descartada (excluyente incumplido, REC-R3) | 0,827 | — |
| K | — | — | Descartada | — | — |
| C | — | — | Descartada (excedente de 20 %) | — | — |
| G | — | — | Indeterminada: completar información | — | — |

Para req_03, Notebook_K queda OFI, pesos 0,333 / 0,083 / 0,583, adecuación 0,659, grado 0,469, "Recomendada (Media)", sin alertas. La misma K está descartada para req_01: eso demuestra CP11.

**Consulta cruzada C3** (bloque 11): "¿Cuál conviene recomendarle a este comprador y por qué?" Atraviesa SM1 (perfil), SM2 (rendimiento y riesgo), SM3 (gráfica y movilidad) y SM4 (grado). **Es la base natural de un caso E2E de PG3.**

---

## 6. PI4 – Integración del LLM con la base de conocimiento (patrón sándwich)

Archivos en `/mnt/project-files/PI4/` (en el repo: `docs/fuentes/SM4/` y `docs/cypher/`):

- `Luconi_Martina_PI4_U4.py`: prototipo, unas 900 líneas.
- `prompts_PI4_SM4.txt`
- `README_ejecucion.md`
- `Grupo_2_PG2_U1_bloques_0a12.cypher`
- `flujo_orquestacion_SM4.png`: Figura 1, el flujo.
- `ejecucion_PI4.png`: Figura 2, los comandos.
- Informe: `Luconi_Martina_PI4_U4.docx`/`.pdf`. La versión entregada final tiene además las correcciones de `Correcciones_PI4_buscar_y_reemplazar.md` y las capturas reales que Martina pegó en su copia.
- Drive de la entrega: https://drive.google.com/drive/folders/1pMWvnSrZhVMzhPu0kddXrSC578qVCjek?usp=sharing

### 6.1 Flujo de orquestación (8 pasos)

1. **Usuario (asesor)** escribe en lenguaje natural. La sesión tiene un pedido de contexto (por defecto `req_01`), que se reemplaza si el texto nombra otro comprador o pedido. `/pedido req_03` lo cambia.
2. **Extracción (LLM):** el prompt de extracción convierte el texto en un JSON con intención, entidades, filtros, conceptos y el fragmento literal de cada dato. Se fuerza con el esquema JSON de Ollama (`format`) y temperatura 0.
3. **Validación (Python):**
   - rechaza cualquier texto fuera del JSON;
   - comprueba que la intención esté en el enum;
   - comprueba que cada notebook exista en el catálogo del grafo;
   - comprueba que el comprador o pedido aparezca escrito en la consulta;
   - comprueba que el tope de precio tenga respaldo literal y esté entre 100 y 10 000 USD.

   Si algo falla, responde con una aclaración y **no consulta Neo4j**.
4. **Generación de consultas (Python):** según la intención elige plantillas Cypher parametrizadas. **El LLM nunca escribe Cypher.**
5. **Recuperación (Neo4j):** sesiones de solo lectura (`routing_="r"`). Devuelve lo que el grafo ya infirió.
6. **Paquete de evidencia:** un único JSON, lo único que ve el segundo prompt. Siempre trae la `advertencia` de parámetros sin validar.
7. **Explicación (LLM):** respuesta empática y justificada solo con esa evidencia, a temperatura 0,2. *D-05 (09/11/2026): Ollama local con `qwen2.5:7b` (alternativa `qwen2.5:3b` por `OLLAMA_MODEL`), temperatura 0 en las dos llamadas y HTTP directo a `/api/chat` con `requests`, sin LangChain. La explicación pasa de 0,2 a 0, y `urllib` se reemplaza por `requests`.*
8. **Verificación REC-R11 (Python):** si la respuesta menciona modelos, reglas o números ausentes de la evidencia, se regenera indicando el problema (hasta 2 veces). Si sigue fallando, responde una **plantilla fija** determinista.

### 6.2 Consultas Cypher del SM4 (diccionario `CONSULTAS`)

| Id | Pregunta que responde | Origen en PG2 | Parámetros |
|---|---|---|---|
| L1_REQUERIMIENTO | ¿Cómo se interpretó el pedido? (presupuesto, prioridad, perfil, grado, notebook consultada, preguntas pendientes) | L1 (bloque 13) | `$requerimiento_id` |
| REQ_DE_COMPRADOR | Pedido de un comprador | — | `$comprador_id` |
| Q1_RECOMENDACION | ¿Qué le recomendamos y en qué orden? | 10.f (REC-R8) + C3 | `$requerimiento_id`, `$precio_max_usd`, `$incluir_fuera_de_presupuesto`, `$solo_sin_alertas` |
| Q2_NO_PROPUESTAS | ¿Qué pasó con las que no aparecen? | C3 | `$requerimiento_id` |
| Q3_SIN_ALTERNATIVA | ¿Quedó sin alternativa? | 10.f (REC-R10) | `$requerimiento_id` |
| Q4_EXPLICAR_NOTEBOOK | ¿Por qué esta notebook quedó así? Devuelve listas `cumple`, `no_cumple`, `falta_verificar` y `alertas`, armadas en Cypher | L2 | `$requerimiento_id`, `$modelo` |
| Q5_TRAZA | ¿Qué reglas lo produjeron? (regla, submódulo, antecedente, consecuente, escenario, fuerza) | L3 | `$requerimiento_id`, `$modelo` |
| Q6_COMPARAR + Q6B_CRITERIO_DESEMPATE | ¿Por qué una quedó antes que otra? (motivo_excluyente; regla REC-R8 y P_MARGEN_EMPATE leídos del grafo) | C3 + REC-R8 | `$requerimiento_id`, `$modelos` |
| Q7_COSTO_BENEFICIO | ¿Cuál rinde más por lo que cuesta? | 10.f (REC-R9) | `$requerimiento_id` + filtros |
| Q8_PARAMETROS_SM4 | ¿Está validado lo que sostiene la respuesta? (etiquetas del SM4 sin validar) | L4 | — |

Qué consultas se ejecutan según la intención (`consultar_grafo`):

- **recomendar:** L1, Q1, Q2, Q3 y Q6B. Si es una consulta puntual, Q4. Si el perfil es indeterminado, solo L1 más el aviso.
- **explicar_notebook:** L1, Q4 y Q5.
- **comparar:** L1, Q6 y Q6B.
- **costo_beneficio:** L1 y Q7.
- **Siempre:** Q8.

### 6.3 Prompt de extracción (resumen; el texto exacto está en `prompts_PI4_SM4.txt` y en `PROMPT_EXTRACCION`)

Es un "extractor estricto de parámetros". Sus reglas:

1. Solo JSON.
2. No responde ni calcula.
3. Solo extrae lo escrito; si falta un dato, usa null, [] o false.
4. La intención es una de: `recomendar | explicar_notebook | comparar | costo_beneficio | desconocida`.
5. Las notebooks van como "Notebook_<letra>" ("la H" → Notebook_H).
6. `comprador_NN` y `req_NN`, solo si aparecen.
7. Filtros: `precio_max_usd`, `incluir_fuera_de_presupuesto` (false solo si lo pide explícitamente) y `solo_sin_alertas`.
8. Conceptos de una lista cerrada: presupuesto, costo_beneficio, ampliabilidad, alertas, sobredimensionamiento, infradimensionamiento, dato_faltante, excluyente, desempate.
9. Evidencia: el fragmento literal de cada dato; sin fragmento, no se extrae.
10. Si no se entiende: `desconocida`, `requiere_aclaracion` y una pregunta.

Esquema de salida:

```json
{"intencion": "...", "comprador_id": null, "requerimiento_id": null, "notebooks": [],
 "filtros": {"precio_max_usd": null, "incluir_fuera_de_presupuesto": true, "solo_sin_alertas": false},
 "conceptos": [], "evidencia": [{"dato": "...", "fragmento": "..."}],
 "requiere_aclaracion": false, "pregunta_aclaracion": null}
```

### 6.4 Prompt de explicación (resumen; el texto exacto está en `PROMPT_EXPLICACION`)

"Eres el asistente explicativo de un sistema experto que recomienda notebooks. Le hablas a un asesor de ventas… El sistema experto (Neo4j) ya tomó todas las decisiones." Recibe `CONSULTA:` y `EVIDENCIA:` (JSON, la única fuente de verdad). Sus reglas:

1. Solo datos de la evidencia, sin conocimiento general.
2. No calcular nada nuevo y copiar los números tal cual.
3. No cambiar estado, orden ni alertas, y no sugerir descartadas.
4. Justificar con cumple / no cumple / falta verificar / alertas, citando la regla entre paréntesis (por ejemplo, "(REC-R8)").
5. Traducir los grados con la etiqueta o el estado.
6. Los rangos se dicen como rango, nunca como un valor intermedio.
7. Si hay preguntas pendientes, "sin alternativa" o un aviso, explicarlo y sugerir el paso siguiente.
8. Si la evidencia no alcanza, decirlo.
9. Cerrar recordando que los parámetros son provisionales si hay advertencia.
10. Entre 4 y 10 oraciones, sin títulos, JSON ni tablas.

### 6.5 Arquitectura y decisiones técnicas del prototipo

| Componente | Elección | Por qué |
|---|---|---|
| Orquestación | Python 3 con funciones propias (`orquestar()`) | El flujo es fijo, no un agente: así cada control queda explícito y se puede probar |
| LLM | Ollama local, **qwen2.5:3b** en las corridas de PI4 (el `.py` trae `qwen2.5:7b` por defecto; se configura con `OLLAMA_MODEL`) | Gratis, local y con salida estructurada. Se usó 3B porque el 7B colgaba la PC de prueba por RAM y disco. **PG3 (D-05):** `qwen2.5:7b`, alternativa `3b`, temperatura 0 | |
| Base de conocimiento | Neo4j 5.x (probado en 5.26) con el driver `neo4j` (6.4.1), solo lectura | El grafo de PG2 es la base: el prototipo no escribe ni recalcula |
| Consultas | Plantillas parametrizadas | Evitan Text2Cypher, con el que el LLM podría consultar otra cosa, inventar filtros o modificar el grafo |
| Verificador | `verificar_explicacion()` + `plantilla_fija()` | REC-R11 automático: el control no depende de que el modelo obedezca |
| API | FastAPI opcional: `--api` expone `POST /consultar {texto, requerimiento_id}` en 127.0.0.1:8000 | `orquestar()` es pura y se monta igual que los otros submódulos en PG3 |
| LangChain | No se usó | Para dos llamadas no aporta. `GraphCypherQAChain` hace que el LLM escriba Cypher, que es justo lo que se quiere evitar. Si PG3 usa LangChain, `extraer_con_llm()` y `explicar()` se reemplazan por `ChatOllama` sin tocar el resto |

Estructura del código:

- `PROMPT_EXTRACCION`, `ESQUEMA_EXTRACCION` y `PROMPT_EXPLICACION`.
- `CONSULTAS`.
- `BaseConocimiento`: conexión, catálogo y lectura.
- `LLMOllama`: `/api/chat`.
- `_json_estricto`, `extraer_con_llm` (un reintento) y `extraer_sin_llm` (extractor por reglas de respaldo).
- `validar_extraccion`, `consultar_grafo`, `explicar`, `verificar_explicacion` y `plantilla_fija`.
- `orquestar`, que devuelve una traza con cada etapa.
- `mostrar`: terminal con bloques [1] a [5].
- `CASOS` y `correr_casos` (vuelca a `ejecucion_casos_PI4.json`), `levantar_api` y `main`.

Ejecución (Windows PowerShell):

```
ollama pull qwen2.5:3b
pip install neo4j            # fastapi uvicorn solo para --api
# En Neo4j: ejecutar Grupo_2_PG2_U1_bloques_0a12.cypher (verificar: MATCH (n:Notebook) RETURN count(n) -> 9)
$env:NEO4J_PASSWORD="<clave>"
python Luconi_Martina_PI4_U4.py            # interactivo (Asesor>), "salir" termina
python Luconi_Martina_PI4_U4.py --casos    # corre los casos y guarda trazas
python Luconi_Martina_PI4_U4.py --sin-llm  # respaldo: extractor por reglas + plantilla fija
python Luconi_Martina_PI4_U4.py --api      # POST /consultar
```

Variables de entorno: `NEO4J_URI` (bolt://localhost:7687), `NEO4J_USER` (neo4j), `NEO4J_PASSWORD`, `OLLAMA_URL` (http://localhost:11434) y `OLLAMA_MODEL`.

### 6.6 Casos de prueba de PI4 (ejecutados con qwen2.5:3b y Neo4j local)

| Caso | Consulta | Intención → consultas | Resultado de Neo4j | Qué demuestra |
|---|---|---|---|---|
| CP1 | ¿Qué le recomendamos al comprador_01? | recomendar → L1, Q1, Q2, Q3, Q6B, Q8 | A puesto 1 (0,785, Alta); H 2 y B 3 por REC-R8; X fuera de presupuesto (5 %, GM-R8); E y C descartadas, M condicionada, G indeterminada | Ranking completo |
| CP2 | ¿Por qué la Notebook_E quedó afuera si tiene casi el mismo puntaje que la H? | explicar_notebook, corregida a comparar por Python → L1, Q6, Q6B | E 0,81 pero "Descartada (excluyente incumplido)", REC-R3; H 0,811, puesto 2 | Un excluyente no se compensa |
| CP3 | ¿Por qué la H quedó antes que la B si la B es más barata? | explicar_notebook, corregida a comparar → L1, Q6, Q6B | H 0,626 ampliabilidad alta, puesto 2; B 0,632 baja, puesto 3; margen 0,05 | Desempate REC-R8 |
| CP4 | Contame qué pasa con la Notebook_M, ¿se la puedo ofrecer? | explicar_notebook → L1, Q4, Q5 | "Recomendada condicionada", grado [0,504 ; 0,826], adecuación [0,741 ; 0,908], falta la autonomía, REC-R15, traza por escenario | Dato faltante como rango |
| CP5 | … ¿cuál es la de mejor relación precio-calidad de menos de 900 dólares? | costo_beneficio, precio_max 900 → L1, Q7 | B (700 USD, 1,161) y M (880 USD, 0,842, condicionada) | Filtros más REC-R9 |
| CP6 | ¿Le sirve la Notebook_K al comprador_03? | explicar_notebook, req_03 → L1, Q4, Q5 | OFI, "Recomendada (Media)", grado 0,469, sin ranking (la misma K está descartada para req_01) | CP11: evaluación por pedido |
| CP7* | ¿Qué le recomiendo al comprador_02? | recomendar → L1 | Perfil indeterminado, 0 evaluadas, pregunta pendiente | No se inventa un perfil (SM1) |
| CP8 | Recomendame una pizza de muzzarella para 3 personas | desconocida → no consulta | "La consulta no trata sobre notebooks…" | Fuera de dominio |
| CP9 | ¿Y la Notebook_Z le sirve? | Notebook_Z no está en el catálogo → no consulta | "No encuentro Notebook_Z…" | Entidad inexistente |
| CP10 | Quiero las opciones de menos de 5 dólares | Tope fuera de 100 a 10 000 → pide confirmación | — | Filtro irrazonable |

\* CP7 se sacó del informe final porque no tenía captura con LLM. Igual funciona: la corrida `--sin-llm` lo muestra (Captura de control B) y la regla 7 del prompt de explicación lo cubre.

Otros controles probados:

- Consulta vacía, o de más de 1500 caracteres (se recorta).
- JSON precedido de texto, rechazado por `_json_estricto`.
- Un id de comprador o pedido no escrito en la consulta se ignora.
- "Comparar" con una sola notebook pasa a explicar_notebook.

### 6.7 Hallazgos reales de la corrida con qwen2.5:3b (clave para la evaluación de PG3)

- **CP3, verificador en acción:** la primera explicación decía "la H tiene un margen de recomendación de 0.006", un número que el modelo calculó restando. REC-R11 la rechazó con "usa el numero 0.006, que no esta en la evidencia". El segundo intento pasó y explica el desempate solo con los datos del grafo (0,626 / 0,632, margen 0,05, ampliabilidad alta frente a baja).
- **CP2 y CP3:** el extractor devolvió `explicar_notebook` con dos notebooks y Python lo corrigió a `comparar`.
- **Errores cualitativos que el verificador NO detecta:**
  - CP1: dijo que Notebook_X "fue descartada por el excedente del 5 %", cuando es la alternativa fuera de presupuesto con estado Recomendada (Media).
  - CP5: le atribuyó a B una "alerta de falta de información" que es de M.

  No traen números, modelos ni reglas ajenos, así que pasan el control. Son errores de **relación** entre datos.
- **Alucinación del extractor:** ante "soy diseñador gráfico y juego al Valorant…, decímelo en tabla", inventó Notebook_X1/X2/X3 y req_1. La validación contra el catálogo lo frenó antes de consultar Neo4j. En el fondo, es un **pedido nuevo**: interpretarlo le toca a SM1, no a SM4. **Es exactamente el problema de enrutamiento que resuelve el prompt maestro de la PG3.**
- El 3B también completó el campo `evidencia` con fragmentos que no correspondían (CP5).
- **Rendimiento:** en la notebook de Martina, sin GPU, cada consulta tarda entre 1 y 4 minutos (dos llamadas al LLM). El 7B se cerraba por falta de RAM y disco.

### 6.8 Explicabilidad (sección h de PI4)

- **Viene del grafo:**
  - la decisión completa (estado, grado, orden, fuera de presupuesto, sin alternativa);
  - la justificación (listas armadas en Cypher, alertas con `regla_origen`, traza `[:ACTIVA {fuerza}]` por escenario);
  - los criterios (enunciados de REC-R8, R9 y R15 y el margen, leídos de los nodos `(:Regla)` y `(:Parametro)`; si el técnico cambia el margen, la explicación cambia sin tocar el código);
  - la incertidumbre (rangos, perfil indeterminado, parámetros sin validar).
- **Genera el LLM:**
  - en la extracción, solo la clasificación y la normalización ("la H" → Notebook_H, "de menos de 900 dólares" → 900);
  - en la explicación, solo la redacción, el tono y la conexión con la pregunta.
- **Cinco barreras contra la invención:**
  1. El LLM ve un paquete cerrado, no el grafo.
  2. No escribe Cypher.
  3. El prompt es restrictivo.
  4. El verificador REC-R11 deja 2 regeneraciones y después usa la plantilla.
  5. Trazabilidad punta a punta: cada ejecución guarda el texto, el JSON extraído, las consultas con sus parámetros, la evidencia y la respuesta.
- **Respecto del ejemplo de la cátedra:** además de "el LLM no decide", el sistema *comprueba* que no haya decidido nada al redactar.

### 6.9 Limitaciones y mejoras declaradas en PI4

- **Limitaciones:**
  - el 3B clasifica mal algunas intenciones e inventa entidades;
  - el verificador es sintáctico: no detecta afirmaciones cualitativas ni números escritos en palabras;
  - solo lee lo ya inferido: "¿y si estira a 1100?" no se recalcula, porque requiere un requerimiento nuevo e inferir de nuevo el bloque 10;
  - el catálogo es de 9 modelos con precios al 01/10/2026;
  - las 9 etiquetas del SM4 siguen sin validar;
  - el grado está comprimido por el centroide (≈ 0,19 a 0,79);
  - no hay memoria de conversación ("¿y la otra?" pide aclaración).
- **Mejoras:**
  - correr con modelos más grandes (qwen2.5:7b, llama3.1:8b) y medir la tasa de JSON válido, de intención correcta y de rechazos;
  - un verificador semántico que, en cada oración que nombra una notebook, compruebe que el estado y las alertas son los suyos;
  - una intención "¿qué pasa si…?" con un requerimiento hipotético;
  - memoria corta (última notebook e intención);
  - **integración en PG3: montar `orquestar()` en el FastAPI del grupo, compartir la extracción con SM1 y usar este prompt de explicación como salida común de los cuatro submódulos**;
  - una vista colapsable con la traza para el asesor.

---

## 7. Qué aporta el SM4 a cada punto de la PG3

### 7.1 Revisión y depuración final (punto 1)

Puntos a verificar o corregir en el SM4 antes de integrar:

- **Terminología (corregido en este documento con los nombres de PG2):**
  - el nombre del submódulo es "Integración, Costo-Beneficio y Recomendación Explicable";
  - los estados son `Recomendada (Alta)`, `Recomendada (Media)`, `Recomendada condicionada por falta de informacion`, `Indeterminada: completar informacion`, `Descartada (excluyente incumplido)` y `Descartada`;
  - se usa "ampliabilidad" (`nivel_ampliabilidad`), no "expandibilidad". La tabla de equivalencias está en 3.2.
- **Numeración de reglas.** Las R1 a R14 de PI1 pasaron a REC-* en PG2 (tabla 2.4). En PG3 se usan solo las REC-*.
- **REC-R9 con prioridad "precio" (corrección para el script de PG3; ya aplicada en el canónico `Grupo_2_PG2_U1_corregido.cypher`).** En el bloque 10.f entregado en PG2, el ranking ordenaba siempre por franja de grado, ampliabilidad y costo-beneficio, sin mirar la prioridad. Ningún pedido de prueba tenía prioridad "precio", por eso no se notó. En la PG3, el `ORDER BY` de la consulta "Recomendacion final" del bloque 10.f pasa a ser:

  ```cypher
  ORDER BY CASE WHEN c.prioridad = 'precio' THEN ev.indice_costo_beneficio ELSE 0 END DESC,  // REC-R9
           floor(coalesce(ev.grado_recomendacion, ev.grado_recomendacion_min) / me.valor) DESC, // REC-R8
           amp DESC, ev.indice_costo_beneficio DESC
  ```

  Cuando la prioridad es "precio", también se agrega `[:ACTIVA]` de la recomendación a la regla REC-R9, para que quede en la traza. Para probarlo hace falta un pedido de prueba con prioridad "precio" (por ejemplo, un req_04 VIRT de 1000 USD): el puesto 1 tiene que ser la recomendada con mayor índice costo-beneficio. Los resultados de req_01, req_02 y req_03 no cambian, porque ninguno tiene esa prioridad.
- **REC-R7 y REC-R13** solo miran la RAM (`ram_sobra` y `ram_min`). Los otros componentes quedan en SM2 y SM3. `ram_sobra` es nulo en DEV, VIRT, VID3D y DATOS (P11 pendiente).
- **El índice costo-beneficio** usa precio/1000, no precio/presupuesto como en PI1. Dejarlo explícito.
- **Funcionamiento.** Verificar con `MATCH (:Recomendacion)-[p:PROPONE]->(n) RETURN p.orden, n.modelo ORDER BY p.orden` → 1 A, 2 H, 3 B.

### 7.2 Integración y prompt maestro (punto 2 y tabla de productos)

- **Principio que el prompt maestro debe respetar:** "Neo4j maneja la verdad". El SM4 ya lo aplica:
  - el LLM no decide, no calcula y no escribe Cypher;
  - las consultas son plantillas;
  - todo se verifica contra la evidencia.
- **Enrutamiento sugerido:**
  - si el texto es un **pedido nuevo** de un comprador (describe un uso, un presupuesto o actividades), va a **SM1**, que lo interpreta, crea el `(:Requerimiento)` y dispara la inferencia de los bloques 9 y 10;
  - si pregunta sobre CPU, RAM o almacenamiento, riesgo de obsolescencia o ampliabilidad, va a **SM2**;
  - si pregunta sobre GPU, pantalla, peso o autonomía, va a **SM3**;
  - si pregunta qué se recomienda, por qué una quedó antes que otra, costo-beneficio, presupuesto o alternativas, va a **SM4**;
  - fuera de dominio, se pide aclaración.

  El caso del "Valorant" (6.7) es la prueba de que hace falta: hoy el SM4 lo frena, pero no lo deriva.
- **Reutilizable tal cual:**
  - el esquema de extracción con enum de intenciones y `evidencia` literal (se amplía con las intenciones de los demás SM);
  - `validar_extraccion()` (catálogo, ids escritos, rangos razonables);
  - el prompt de explicación y `verificar_explicacion()` como **salida común de los cuatro submódulos**;
  - la plantilla fija como respaldo;
  - el modo `--sin-llm` para demos sin Ollama.
- **API unificada:** `POST /consultar {texto, requerimiento_id}` ya existe en el SM4. En PG3 se monta un único FastAPI con el router del prompt maestro, y cada SM aporta su `consultar_grafo` (o sus plantillas Cypher).

### 7.3 Arquitectura (punto 3)

Componentes del SM4 para el diagrama:

- **Usuario:** el asesor de ventas.
- **Interfaz:** consola (`Asesor>`) o FastAPI.
- **Modelo de lenguaje:** Ollama qwen2.5:3b, con dos llamadas (extracción y explicación).
- **Orquestación:** `orquestar()`, con validación, selección de plantillas, paquete de evidencia y verificador REC-R11.
- **Base de conocimiento:** Neo4j con el script de PG2.
- **Módulos de razonamiento:** el bloque 10.f (Mamdani REC-RD1 a RD5 más las reglas crisp REC-R*).
- **Fuentes de información:**
  - el catálogo (Mercado Libre y tiendas oficiales, 01/10/2026; BNA);
  - la entrevista al técnico;
  - Notebookcheck y RTINGS;
  - las fichas de fabricantes;
  - los apuntes de la cátedra.

Ver `PI4/flujo_orquestacion_SM4.png`.

### 7.4 Casos de uso integrados que cruzan submódulos (puntos 4 y 5; mínimo 3 E2E)

1. **Recomendación completa para req_01** (SM1 → SM2 → SM3 → SM4):
   - SM1: perfil VIRT 0,899 y prioridad rendimiento;
   - SM2: excluyente de virtualización (E descartada), riesgo de RAM y ampliabilidad;
   - SM3: movilidad, GPU de X con TGP reducido (GM-R8) y autonomía faltante en M;
   - SM4: ranking A, H, B, X aparte, M condicionada y G indeterminada.

   Consulta: "¿Qué le recomendamos al comprador_01?" (CP1) más C3.
2. **Excluyente frente a puntaje** (SM2 + SM4): CP2. E tiene 0,81 pero no virtualiza (REN-R1 de SM2 → REC-R3 de SM4).
3. **Desempate por ampliabilidad** (SM2 + SM4): CP3. `nivel_ampliabilidad` (REN-R16, SM2) decide el orden por REC-R8.
4. **Dato faltante** (SM3 + SM4): CP4. SM3 no tiene la autonomía de M, así que no hay movilidad, y SM4 aplica REC-R15 con rango y traza por escenario.
5. **Misma notebook, dos compradores** (SM1 + SM4): CP6/CP11. K para req_03 (OFI, portabilidad) queda Recomendada (Media), y para req_01 (VIRT) queda Descartada.
6. **Pedido incompleto** (SM1 + SM4): req_02, con perfil indeterminado. El SM4 no evalúa y devuelve la pregunta pendiente de SM1.
7. **Pedido nuevo enrutado** (prompt maestro → SM1 → SM4): "Soy diseñador gráfico y juego al Valorant, tengo X USD". Hoy falla en el SM4; en PG3 debería crear el requerimiento en SM1 y recién después recomendar.

Pruebas funcionales del SM4 con resultado esperado y obtenido: la tabla 6.6 más los hallazgos de 6.7, que son los resultados *obtenidos* con el 3B frente a los *esperados* de PI4.

### 7.5 Trazabilidad (punto 7): ejemplo reconstruible con Notebook_M en req_01

- **Fuente del conocimiento:** la ficha del fabricante no informa la autonomía (`Bateria.tipo_dato = 'desconocida'`). Precio de Mercado Libre al 01/10/2026.
- **Regla utilizada:** REC-R15 (nodo `(:Regla)` con su enunciado), más REC-RD1 a RD5 en dos escenarios, más REC-R4, R5 y R9.
- **Evidencia considerada:**
  - `adecuacion_global_min/max` = 0,741 / 0,908;
  - `grado_recomendacion_min/max` = 0,504 / 0,826;
  - pesos 0,75 / 0,083 / 0,167;
  - la alerta "Información incompleta", `PRODUCIDA_POR` REC-R15;
  - las fuerzas `[:ACTIVA]`: RD2 = 0,842 en el peor caso y RD1 = 1,0 en el mejor.
- **Consulta ejecutada:** Q4_EXPLICAR_NOTEBOOK y Q5_TRAZA con `{requerimiento_id: "req_01", modelo: "Notebook_M"}`, registradas en la traza de `orquestar()`.
- **Explicación generada:** "Sí, se la podés ofrecer, pero aclarándole al comprador que falta un dato… su grado va de 0,504 en el peor caso a 0,826 en el mejor (REC-R15)…". Pasa el verificador REC-R11.
- **Validación de los parámetros:** `(:EtiquetaDifusa)` y `(:Parametro)` con `estado_validacion = 'provisional'`, más la pregunta de la agenda `(:ConsultaExperto)`.

### 7.6 Evaluación del sistema (punto 6), desde el SM4

- **Fortalezas:**
  - decisión 100 % en el grafo y auditable;
  - incertidumbre explícita (rangos, indeterminada, provisional);
  - tres capas de control (esquema, validación en Python y verificador);
  - respaldo determinista sin LLM;
  - parámetros editables sin tocar el código.
- **Limitaciones y situaciones problemáticas:**
  - los errores de relación del 3B (CP1, CP5);
  - las entidades inventadas por el extractor;
  - los parámetros sin validar;
  - el centroide comprimido;
  - el catálogo chico;
  - sin "¿qué pasa si…?";
  - latencia de 1 a 4 minutos en CPU;
  - el orden por REC-R9 con prioridad "precio" se corrige en PG3 (7.1), pero falta probarlo con un pedido de esa prioridad.
- **Oportunidades de mejora:** las de 6.9, más validar con el técnico (agenda V1) y ampliar el catálogo hacia los 30 modelos previstos en PI1.

### 7.7 Reflexión metodológica (punto 8): aporte de cada etapa al SM4

- **Formulación (PG0) y análisis de la tarea experta (PI1):** se clasificó como Recomendación y se definió el flujo de filtrar, ponderar, alertar, ordenar y explicar.
- **Adquisición de conocimiento (PI1 y PI2):** fuentes documentales, casos publicados y la entrevista al técnico. De ahí salieron la ampliabilidad como desempate y el componente limitante en la explicación. También la lección de separar el conocimiento experto de los parámetros del grupo.
- **Modelado conceptual (PI2 y PG1):** red semántica y frames con estados, alertas y la política de información incompleta.
- **Lógica difusa (PI3):** reemplazo de los cortes 0,6, 0,8 y 10 % por un Mamdani de dos entradas, y parámetros como conocimiento editable.
- **Implementación en grafos (PG2):** bloque 10.f, evaluación por pedido (CP11), traza `[:ACTIVA {fuerza}]` y agenda de validación.
- **Integración con LLM (PI4):** patrón sándwich, plantillas en lugar de Text2Cypher, verificador REC-R11 y hallazgos reales con un modelo chico.

### 7.8 Entregables del SM4 que entran en el ZIP de PG3

| Ítem del ZIP | Archivo del SM4 |
|---|---|
| e) Código fuente | `Luconi_Martina_PI4_U4.py` (integrar en el FastAPI común); `requirements.txt`: `neo4j`, `fastapi`, `uvicorn`, `pydantic` (Ollama se instala aparte) |
| f) Scripts Cypher | `Grupo_2_PG2_U1_corregido.cypher` (canónico; bloque 10.f, SM4) y las plantillas del diccionario `CONSULTAS` |
| g) Configuración | Variables `NEO4J_*` y `OLLAMA_*`; `prompts_PI4_SM4.txt` |
| c) Casos de prueba | Tabla 6.6 más las trazas de `--casos` (`ejecucion_casos_PI4.json`, regenerar con el LLM real) |
| b) Diagramas | `flujo_orquestacion_SM4.png` |
| d) Manual de uso | `README_ejecucion.md` (comandos de PowerShell) |
| j) Datos de ejemplo | req_01, req_02, req_03 y el catálogo de 9 notebooks (bloques 7 y 8) |

---

## 8. Referencias usadas en las PI del SM4

- Cátedra de Inteligencia Artificial, UTN FRM (2026):
  - Apuntes U1a (Sistemas Expertos) y U1b (Lógica Difusa);
  - Guía de Adquisición de Conocimiento y Modelado para Proyectos de IC + LLM;
  - Unidad 4 – Implementación de Modelos de IA;
  - ejemplos resueltos de PI3 y PI4 (Evaluación de CVs).
- Grupo 2 (2026): PG0 – Formulación; PG1 – Integración Conceptual y Consolidación; PG2 – Base de Conocimiento en Neo4j (versión corregida).
- Luconi Furque, M. (2026): PI1 – Cuaderno de Conocimiento; PI2 – Redes Semánticas, Frames y Reglas; PI3 – Lógica Difusa; PI4 – Integración de LLM con la Base de Conocimiento.
- Entrevista a técnico en armado y revisión de PC y notebooks (Anexo C de PI2).
- Zadeh, L. A. (1965). Fuzzy sets. *Information and Control*, 8(3), 338–353.
- Mamdani, E. H., & Assilian, S. (1975). An experiment in linguistic synthesis with a fuzzy logic controller. *Int. J. Man-Machine Studies*, 7(1), 1–13.
- Russell, S. y Norvig, P. (2010). *Inteligencia Artificial: Un Enfoque Moderno* (3.ª ed.). Pearson.
- García Martínez, R. y Britos, P. (2004). *Ingeniería de Sistemas Expertos*. Nueva Librería.
- Lewis, P. et al. (2020). Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks. *NeurIPS* 33.
- Pan, S. et al. (2024). Unifying Large Language Models and Knowledge Graphs: A Roadmap. *IEEE TKDE*, 36(7).
- Qwen Team (2024). Qwen2.5 Technical Report.
- Documentación de Neo4j (Cypher Manual, Python Driver), Ollama (`/api/chat`, Structured outputs), FastAPI y LangChain.
- Fuentes de datos: Notebookcheck, RTINGS, r/SuggestALaptop, fichas de Lenovo, Dell, HP, ASUS, Acer, MSI y Apple, Mercado Libre Argentina y BNA.
