# CONTEXTO DEL PROYECTO PARA PG3 — SM2 (Miranda, Mauricio)

> Asistente Experto para la Selección Personalizada de Notebooks · Grupo 2 · Comisión 5K09 · UTN FRM · Cátedra de Inteligencia Artificial · Ciclo 2026
> Archivo generado el 09/11/2026 a partir de: PI1, PI2, PI3 y PI4 de SM2 (informes), correcciones de la profesora a PI1–PI4, consigna de PG3, `Miranda_Mauricio_PI4_U4.py` y `test_offline_SM2.py`.

---

## 0. Cómo usar este archivo

**Propósito.** Darle a un asistente de IA (o a una persona) todo el contexto necesario para ayudar a desarrollar la actividad **PG3 (orquestación final, pruebas del prototipo y armado de carpeta)** sin perder lo hecho en SM2.

**Etiquetas de procedencia** (cada dato importante lleva una):

| Etiqueta | Significa |
| --- | --- |
| `[DOC]` | Está escrito en los informes PI1–PI4, en las correcciones o en la consigna de PG3 |
| `[CÓD]` | Se lee directamente en los `.py` adjuntos |
| `[DED]` | Deducido por inferencia a partir de lo anterior (puede ser incorrecto) |
| `[?]` | No se pudo confirmar; verificar antes de usar |

**Reglas para el asistente que use este archivo:**

1. **No inventar** nada de SM1, SM3, SM4, PG0, PG1 ni PG2: no están en los documentos disponibles. Lo que aparece aquí sobre ellos es lo que citan los informes de SM2. Pedir los archivos si hacen falta.
2. **Neo4j maneja la verdad.** Ninguna conclusión, cifra, regla ni estado puede salir del LLM: todo sale del grafo y el LLM solo interpreta la pregunta y redacta.
3. **«Desconocido» no es «supuesto».** Mantener separado el hecho original (ej. ampliabilidad `desconocida`) del tratamiento precautorio. Es una observación repetida de la profesora.
4. **Parámetros sin validar.** Ningún parámetro difuso o de grado está validado por un técnico; toda respuesta que dependa de ellos debe decirlo.
5. **Idioma y tono:** español rioplatense (voseo), claro, para una persona no técnica.
6. **Antes de modificar el código**, confirmar cuál es la versión final del `.py` (ver sección 14, ítem A).

---

## 1. Resumen ejecutivo (leer primero)

- **Qué es SM2:** submódulo de **evaluación de rendimiento y capacidad** (CPU, RAM, almacenamiento; foco de PI3 y PI4 en la **RAM**). Traduce el perfil de uso del comprador en requisitos de hardware y determina en qué grado cada notebook los cumple. `[DOC]`
- **Cómo razona:** reglas determinísticas y heurísticas (REN-R1 a R15), funciones de grado y, desde PI3, **lógica difusa tipo Mamdani** (FZ-R1 a R7) para el riesgo de obsolescencia de la RAM. Todo corre **en el grafo Neo4j** (PG2). `[DOC]`
- **Rol del LLM (PI4):** solo en los extremos. Llamada 1 extrae intención y parámetros en JSON; llamada 2 explica una **evidencia** ya recuperada. Entre ambas: validación en código, consulta Cypher fija de solo lectura y verificación anti-invención. `[DOC]` `[CÓD]`
- **Estado de la integración individual (PI4):** funciona (13 casos, 8 válidos y 5 de error). La profesora pidió, como corrección principal antes de PG3, una **verificación semántica** (que el LLM preserve rangos, perfil indeterminado y no afirme sin respaldo). `[DOC]`
- **Qué sigue (PG3):** un único asistente que integre SM1–SM4 con **prompt maestro de enrutamiento**, **API/interfaz única**, **≥ 3 pruebas E2E** que crucen submódulos, informe ejecutivo y ZIP final reproducible. `[DOC]`
- **Alerta sobre archivos:** el `.py` adjunto parece **anterior** al descrito en el informe PI4; falta además el Cypher de PG2 (sección 14). `[DED]`
- **Dato de calendario:** el cuaderno de PI1 planificaba la «integración con los demás submódulos» para el **13/11/2026**. `[DOC]`

---

## 2. El proyecto y el equipo

### 2.1 Submódulos

| Sub. | Responsabilidad | Autor | Fuente |
| --- | --- | --- | --- |
| SM1 | Interpretación del requerimiento: perfiles de uso con grado, presupuesto, requisitos explícitos e institucionales, `necesita_virtualizacion`, preguntas pendientes | Olea, F. | `[DOC]` |
| **SM2** | **Evaluación de rendimiento y capacidad (CPU, RAM, almacenamiento)** | **Miranda, M.** | `[DOC]` |
| SM3 | Evaluación gráfica y de movilidad (GPU, pantalla, peso, autonomía) | de Coninck, R. | `[DOC]` |
| SM4 | Integración y recomendación (combina grados de SM2/SM3 con prioridades, aplica excluyentes con MIN) | Luconi Furque, M. (48889; confirmado en PG1 y PG2) | `[DOC]` |

### 2.2 Línea de tiempo de entregas

| Etapa | Contenido | Estado |
| --- | --- | --- |
| PG0 | Formulación del proyecto y división de submódulos (grupo) | No disponible aquí |
| PI1 | Tarea experta, procesos, cuaderno de conocimiento (v1.0, 18/09/2026) | Entregado y corregido (riesgo **amarillo**) |
| PI2 | Redes semánticas, frames, reglas (cuaderno v1.1, 03/10/2026) | Entregado y corregido |
| PI3 | Lógica difusa (variables, gaussianas, FZ-R1..R7) | Entregado y corregido («modelo cerrado») |
| PG1 | Integración conceptual y consolidación del conocimiento (grupo) | Ver `Contexto_PG1_PG2_Grupo_para_PG3.md` |
| PG2 | Implementación de la base de conocimiento en Neo4j (grupo; `Grupo_2_PG2_U1.cypher`) | Ver `Contexto_PG1_PG2_Grupo_para_PG3.md` |
| PI4 | Integración LLM + Neo4j (individual) | Entregado y corregido |
| **PG3** | **Orquestación final, pruebas y carpeta (grupo)** | **Próxima actividad** |

### 2.3 Convenciones de identificadores `[DOC]`

| Prefijo | Significado | Ejemplos |
| --- | --- | --- |
| `INT-R` | Reglas de SM1 (interpretación) | INT-R3 (`necesita_virtualizacion`), INT-R5 (umbral 0,4 para imponer requisitos), INT-R13 (perfil indeterminado → pregunta pendiente) |
| `REN-R` | Reglas de SM2 (evaluación de rendimiento) | REN-R1 a REN-R15 (REN-R16 es otra regla de PG1: «Ampliabilidad» alta/media/baja de RAM y slot M.2, que SM4 usa para desempatar; está cargada en el grafo de PG2) |
| `GM-R` / `GM-RD` | Reglas de SM3 (gráfica y movilidad) | GM-R10 (inferencia TSK), GM-R15 (consume el aviso de canal simple), GM-RD1, GM-RD2 |
| `REC-R` / `REC-RD` | Reglas de SM4 (recomendación) | REC-R3 (operador MIN para excluyentes), REC-R11 (plantilla fija / rango), REC-R15 (recomendación condicionada con rango), REC-RD1 |
| `FZ-R` | Reglas difusas de SM2 (PI3) | FZ-R1 a FZ-R7 |
| `P_…` / `TAB_…` | Parámetros candidatos y tablas de SM2 | P_FACTOR_HDD, TAB_REQ_PERFIL |
| `CP1`…`CP10` | Casos de prueba de PG2 | CP1 (Notebook A recomendada), CP2/CP4 (virtualización), CP5 (K), CP8 (parámetros), CP10 (req_02) |
| `D1`…`D6` | Devoluciones/decisiones de PG2 | D1 (no asumir perfil OFI), D6 (la advertencia de parámetros sin validar viaja hasta la explicación) |

---

## 3. SM2: alcance, entradas y salidas

### 3.1 Tarea experta `[DOC]`
- **Principal:** evaluación. **Secundarias:** interpretación (especificación → estado con significado) y predicción (obsolescencia y pérdida de rendimiento en carga sostenida).
- **Descartadas:** diagnóstico, planificación, recomendación (esta última es de SM4).
- **Capas:** dato crudo → estado interpretado → evaluación → proyección.

### 3.2 Fuera de alcance `[DOC]`
GPU, pantalla, peso, autonomía (SM3); benchmarks propios; procesadores ARM; refrigeración y temperaturas; decidir si una notebook se recomienda; precio.

### 3.3 Entradas (desde SM1 y la base) `[DOC]`
- De SM1: perfiles con grado ≥ 0,4 (imponen requisitos), perfil dominante, `necesita_virtualizacion`, `requisitos_explicitos`, `requisitos_institucionales`.
- Del grafo: modelo, gama, núcleos, sufijo y virtualización del CPU; cantidad, tipo, canal y ampliabilidad de la RAM; capacidad y tipo de almacenamiento; tabla de requisitos por perfil; tabla de gamas; costo de ampliación de referencia; tipo de GPU (solo lectura).

### 3.4 Salidas `[DOC]`
Grados de CPU, RAM, almacenamiento y rendimiento (0 a 1); clasificación de cada requisito; grados excluyentes y marca de «excluyente no cumplido»; alertas y notas informativas; costo de ampliación; aviso a SM3; **riesgo de obsolescencia** (valor 0–100 o rango, etiqueta, reglas FZ activadas con fuerza); versión de cuaderno y parámetros sin validar.

### 3.5 Contratos con otros submódulos `[DOC]`

| Con | Contrato | Estado |
| --- | --- | --- |
| SM1 → SM2 | Perfiles ≥ 0,4, perfil dominante, `necesita_virtualizacion`, requisitos explícitos/institucionales. SM2 aplica virtualización si la pide el indicador **o** el perfil (VIRT) | Pedir a SM1 el slot `requisitos_explicitos` (o confirmar que se mapea a institucionales) `[?]` |
| SM2 → SM3 | Bandera `aviso_sm3 = "ancho_de_banda_reducido"` cuando GPU integrada + RAM en canal simple (REN-R11) o canal desconocido (REN-R14, con alerta). SM3 lo usa en GM-R15 | Propuesto por SM2 en PI2 (b.1.2); SM3 lo consume en GM-R15 según PI2/PI3. Confirmar el formato exacto del campo `[?]` |
| SM2 → SM4 | JSON de resultados (ver 3.6). SM4 aplica MIN (REC-R3) sobre excluyentes y trata «no evaluado» como grado ausente, no como 0 | Confirmar con SM4 que aplica MIN sobre este formato `[?]` |
| SM2 → asesor | Indirecto, a través de SM4 | — |

### 3.6 JSON de resultados SM2 → SM4 (ejemplo de la Notebook K, PI1) `[DOC]`

```json
{
  "notebook": "K",
  "requisitos": {"gama_cpu": "media", "nucleos_min": 6, "ram_gb": [16, 32], "ssd_gb": [512, 1024],
                 "virtualizacion": true, "carga_sostenida": true},
  "grados": {"cpu": 0.7, "ram": 0.5, "almacenamiento": 0.8, "rendimiento": 0.65},
  "clasificacion": {"virtualizacion": "cumple", "cpu": "cumple",
                    "ram": "parcial_condicionado", "almacenamiento": "cumple"},
  "excluyentes": {"virtualizacion": 1.0, "ram_minima": 0.5, "no_cumplido": false},
  "alertas": ["cpu_bajo_consumo_carga_sostenida", "ram_condicionada_a_ampliacion"],
  "costo_ampliacion_usd": 30,
  "aviso_sm3": "ancho_de_banda_reducido",
  "reglas_activadas": ["REN-R2", "REN-R1", "REN-R3", "REN-R8", "REN-R9", "REN-R7", "REN-R11", "REN-R12", "REN-R13"]
}
```
Desde PI2 el resultado suma también `version_cuaderno`, `parametros_sin_validar`, notas informativas y «no evaluado». Desde PI3 suma `riesgo_valor` / `riesgo_min` / `riesgo_max` / `riesgo_etiqueta` y reglas FZ con fuerza. `[DOC]`

---

## 4. Flujo de proceso SP1–SP8 `[DOC]`

> **En el prototipo (D-02 y D-03):** SM2 no corre SP1–SP8 en el grafo. Entrega `adecuacion_rendimiento` como dato por par notebook-perfil (`SALIDA_PI2`), calculado con sus reglas de PI2. **Pendiente:** completar los 6 perfiles que faltan (OFI, DEV, DIS, VID3D, GAM, DATOS) en `docs/cypher/salida_pi2.csv` y reemplazar el supuesto K–OFI 0,80. Hay que documentar el método, porque la fórmula de SP6 sin núcleos ni carga sostenida no reproduce los valores de VIRT: K da 0,75 en vez de 0,50 y G da 0,41 en vez de 0,55.

SP1 se ejecuta una vez por pedido; SP2–SP8 se repiten para cada notebook del catálogo.

| Paso | Qué hace | Reglas |
| --- | --- | --- |
| SP1 | Consolida requisitos: valor más exigente por criterio entre los perfiles con grado ≥ 0,4; un requisito explícito/institucional mayor reemplaza al mínimo | REN-R2 |
| SP2 | Virtualización: si se requiere y el CPU no la soporta → grado CPU 0, marca de excluyente, salto a SP7. Si la ficha no informa: consultar Intel ARK / AMD y agregar nota «verificar BIOS/UEFI» | REN-R1 |
| SP3 | Grado de CPU por gama, núcleos y sufijo | REN-R3, R4, R8 |
| SP4 | Grado de RAM: función de suficiencia, ampliabilidad, condicionado, alertas | REN-R6, R7, R9, R10, R15 |
| SP5 | Grado de almacenamiento, penalización HDD; aviso a SM3 por canal simple (o desconocido) | REN-R5, R11, R14 |
| SP6 | Rendimiento = 0,35·CPU + 0,40·RAM + 0,25·Almacenamiento | P_PESO_* |
| SP7 | Clasifica (≥ 0,7 cumple; 0,3–0,7 parcial; < 0,3 no cumple) y marca excluyentes | REN-R12, R13 |
| SP8 | Consolida alertas, registra traza en Neo4j, envía JSON a SM4 | — |

**Excepciones:** ampliabilidad sin datos; requisito explícito/institucional; perfiles múltiples; RAM mixta (soldada + SO-DIMM → se trata como ampliable); CPU sin virtualización (RAM, almacenamiento y rendimiento quedan `no evaluado`); virtualización no informada.

---

## 5. Reglas de SM2

### 5.1 Reglas REN-R1 a REN-R15 (v1.1) `[DOC]`

| ID | Regla (los números se citan por parámetro) | Tipo |
| --- | --- | --- |
| REN-R1 | SI `necesita_virtualizacion` (SM1) O algún perfil que impone requisitos la exige (VIRT) ENTONCES requerir VT-x/AMD-V como **excluyente**; sin soporte → grado CPU 0 y marca; ficha sin dato → consultar fabricante y nota BIOS/UEFI | Determinístico, documental |
| REN-R2 | SI un perfil impone requisitos (grado ≥ P_UMBRAL_IMPONE = 0,4) ENTONCES usar mínimo y recomendado más exigentes de TAB_REQ_PERFIL; un explícito/institucional mayor pasa a ser el mínimo | Determinístico, documental |
| REN-R3 | Brecha de gama: ≥ requerida → P_BRECHA_0 (1,0); un nivel menos → P_BRECHA_1 (0,6); dos → P_BRECHA_2 (0,2) | Heurístico |
| REN-R4 | Núcleos < mínimo del perfil → restar P_PEN_NUCLEOS (0,2) | Heurístico. **Fuera de alcance del prototipo (D-02)** |
| REN-R5 | Almacenamiento principal HDD → grado × P_FACTOR_HDD (0,3) y alerta `almacenamiento_hdd` | Heurístico |
| REN-R6 | RAM soldada Y < recomendada → alerta `ram_no_ampliable` (excepción: mixta = ampliable) | Heurístico, predictivo. **Retirada en el canónico** (→ FZ-R3 y FZ-R7) |
| REN-R7 | RAM < mínimo Y ampliable hasta alcanzarlo (`max_gb ≥ M` y ranuras suficientes) → grado = máx(calculado, P_GRADO_RAM_COND = 0,5), «cumple parcialmente, condicionado a ampliación», alerta `ram_condicionada_a_ampliacion`, costo = ⌈(M − RAM)/P_TAM_MODULO_GB (8)⌉ × P_COSTO_MODULO_USD (30) | Heurístico (casos) |
| REN-R8 | Carga sostenida Y sufijo U o V → restar P_PEN_CARGA_SOST (0,3) y alerta `cpu_bajo_consumo_carga_sostenida` | Heurístico, predictivo. **Fuera de alcance del prototipo (D-02)** |
| REN-R9 | RAM ampliable → sumar P_BONIF_AMPLIABLE (0,1), máx. 1,0. **La regla con menos respaldo; candidata a eliminarse** | Supuesto del grupo. **Retirada en el canónico** (→ FZ-R4: no contar dos veces la ampliabilidad) |
| REN-R10 | Ampliabilidad desconocida → **conservar «desconocida»**, no descartar y alertar `ampliabilidad_no_verificada`; el riesgo se informa como rango (FZ-R6). *En PI1/PI2 decía «asumir no ampliable»: la profesora lo corrigió (PG1, P1-1) y así está en el canónico* | Determinístico |
| REN-R11 | GPU integrada Y RAM canal simple → `aviso_sm3 = ancho_de_banda_reducido`; si REN-R7 completa el doble canal → nota `ampliacion_completa_doble_canal` | Heurístico, empírico |
| REN-R12 | ≥ P_UMBRAL_CUMPLE (0,7) cumple; ≥ P_UMBRAL_PARCIAL (0,3) parcial; resto no cumple (con REN-R7: «condicionado») | Determinístico (umbral del grupo) |
| REN-R13 | Excluyentes: virtualización (1 ó 0) y RAM mínima (su grado). Si alguno vale 0 → «requisito excluyente no cumplido» para que SM4 aplique MIN | Determinístico, documental |
| REN-R14 | (Nueva PI2) GPU integrada Y canal desconocido → tratar como simple + alerta `canal_memoria_no_verificado` | Supuesto conservador |
| REN-R15 | (Nueva PI2) RAM ≥ M y < R y ampliable → nota `ram_ampliable_hasta_recomendada`, sin cambiar grados | Heurístico (casos) |

### 5.2 Reglas difusas FZ (PI3) `[DOC]`

Operadores: AND = MIN, OR = MAX, implicación Mamdani por mínimo, agregación MAX, desborrosificación por **centroide**.

| ID | Condición | Conclusión | Formaliza |
| --- | --- | --- | --- |
| FZ-R1 | suficiencia **insuficiente** Y ampliabilidad **poca** | riesgo **alto** | REN-R6 |
| FZ-R2 | insuficiente Y (ampliabilidad **media** O **mucha**) | riesgo **medio** | REN-R7 |
| FZ-R3 | suficiencia **justa** Y ampliabilidad poca | riesgo medio | REN-R6 |
| FZ-R4 | justa Y (media O mucha) | riesgo **bajo** | REN-R9 |
| FZ-R5 | suficiencia **suficiente** O **holgada** | riesgo bajo | — |
| FZ-R6 | (Control, crisp) ampliabilidad de la ficha **desconocida** → evaluar FZ-R1..R5 con a = 0 y a = 1; informar riesgo como **rango [mejor ; peor]** y alerta `ampliabilidad_no_verificada` | — | REN-R10, REC-R15 |
| FZ-R7 | (Control, crisp) etiqueta dominante (o del peor caso) = alto → alerta «Riesgo de obsolescencia alto» con `regla_origen = FZ-R7` | — | REN-R6 (alerta) |

*PI3 proponía mantener REN-R6, R7 y R9 vigentes hasta validar el modelo difuso. En el grafo canónico **REN-R7 sigue vigente**, y **REN-R6 y REN-R9 están retiradas** (`reemplazada en PG2`), para no contar dos veces la ampliabilidad.*

> **D-04 (09/11/2026), se implementan en el canónico:**
> - **REN-R11:** GPU integrada y canal simple generan la alerta de ancho de banda reducido que consume SM3 (GM-R15).
> - **REN-R14:** canal desconocido genera la alerta `canal_memoria_no_verificado`, **sin tratarlo como simple** (desconocido ≠ simple, corrección P1-1).
> - **REN-R13:** alerta de virtualización no informada.
> - **REN-R2:** los requisitos salen del más exigente entre todos los perfiles que imponen requisitos, no solo del dominante.
>
> Hoy ninguna de las cuatro está en el grafo (PG1/PG2 §8.8). Los excluyentes no cambian: un riesgo bajo nunca compensa un excluyente incumplido (REC-R3).

> Nota: FZ-R7 **origina una alerta**; no es una «regla activada» con fuerza. Esa confusión fue un error real del LLM en PI4 (sección 11.7).

---

## 6. Tablas de conocimiento y funciones de grado `[DOC]`

### 6.1 Requisitos por perfil (TAB_REQ_PERFIL; M = mínimo, R = recomendado)

> **Tabla de PI1/PI2 (histórica).** La vigente es la del grafo canónico (`Contexto_PG1_PG2_Grupo_para_PG3.md` §8.6, decisión D-01). Diferencias:
> - **OFI:** SSD mínimo 512 GB, no 256.
> - **DEV:** RAM 16/32 GB y SSD mínimo 1024 GB (no 8/16 y 256). Coincide con el técnico de SM4: «programación: 16 GB, SSD 1 TB».
> - **VID3D:** SSD mínimo 1024 GB, igual que en esta tabla.
> - **DATOS:** CPU alta (no media), SSD mínimo 1024 GB.
> - **SSD recomendado:** el canónico no guarda ninguno, solo el mínimo.
>
> **Decidido (D-02, 09/11/2026):** DATOS **no** exige virtualización (como en el canónico: REN-R1 aplica solo a VIRT). **Núcleos**, **carga sostenida** y **SSD recomendado** quedan fuera del alcance del prototipo: son diseño de PI1/PI2 no implementado (REN-R4 y REN-R8 incluidas), y el rendimiento sigue llegando por `SALIDA_PI2`.

| Perfil | Gama CPU mín. | Núcleos | RAM M / R | SSD M / R | Virt. | Carga sost. |
| --- | --- | --- | --- | --- | --- | --- |
| OFI | Entrada | 4 | 8 / 16 GB | 256 / 512 GB | No | No |
| DEV | Media | 6 | 8 / 16 GB | 256 / 512 GB | No | No |
| VIRT | Media | 6 | 16 / 32 GB | 512 GB / 1 TB | **Sí** | No |
| DIS | Media | 6 | 16 / 32 GB | 512 GB / 1 TB | No | No |
| VID3D | Alta | 8 | 16 / 32 GB | 1 TB / 2 TB | No | **Sí** |
| GAM | Media | 6 | 16 / 32 GB | 512 GB / 1 TB | No | **Sí** |
| DATOS | Media | 8 | 16 / 32 GB | 512 GB / 1 TB | **Sí** | **Sí** |

En los siete perfiles R = 2·M para la RAM (usado para normalizar en PI3).

### 6.2 Gamas y sufijos
- **Entrada:** Core i3, Core 3, Intel N; Ryzen 3, Athlon. **Media:** Core i5, Core 5, Core Ultra 5; Ryzen 5, Ryzen AI 5. **Alta:** i7/i9, Core 7, Core Ultra 7/9; Ryzen 7/9, Ryzen AI 7/9.
- **Sufijos:** U y V = bajo consumo (REN-R8); P = intermedio; H/HS/HX = alto rendimiento; sin sufijo = no clasificado (sin ajuste).

### 6.3 Funciones de grado
- **CPU:** base por gama (1,0 / 0,6 / 0,2); −0,2 si faltan núcleos; −0,3 si bajo consumo con carga sostenida; acotado [0,1]; virtualización requerida y no soportada → 0.
- **RAM:** ≥ R → 1,0; M ≤ RAM < R → 0,7; M/2 < RAM < M → (RAM − M/2)/(M/2) × 0,7; ≤ M/2 → 0; +0,1 si ampliable (máx. 1,0); REN-R7 fija mínimo 0,5.
- **Almacenamiento:** ≥ R → 1,0; M–R → 0,8; M/2–M → 0,4; < M/2 → 0; × 0,3 si HDD.

### 6.4 Catálogo de 22 parámetros candidatos (19 numéricos + 3 tablas)
Valor actual → procedencia del **valor** (todas sin validar salvo indicación):

| Parámetro | Valor | Procedencia del valor |
| --- | --- | --- |
| P_PESO_CPU / P_PESO_RAM / P_PESO_ALM | 0,35 / 0,40 / 0,25 | Decisión del grupo |
| P_BRECHA_0 / _1 / _2 | 1,0 / 0,6 / 0,2 | Decisión del grupo (criterio empírico) |
| P_PEN_NUCLEOS | 0,2 | Decisión del grupo |
| P_PEN_CARGA_SOST | 0,3 | Decisión del grupo |
| P_GRADO_RAM_M_R | 0,7 | Decisión del grupo |
| P_BONIF_AMPLIABLE | 0,1 | Decisión del grupo |
| P_GRADO_RAM_COND | 0,5 | Decisión del grupo (criterio: casos) |
| P_COSTO_MODULO_USD | 30 USD | Empírico (Mercado Libre AR, 09/2026); en investigación DDR4 vs DDR5 |
| P_TAM_MODULO_GB | 8 | Decisión del grupo |
| P_FACTOR_HDD | 0,3 | Decisión del grupo |
| P_GRADO_ALM_M_R / M2_M | 0,8 / 0,4 | Decisión del grupo |
| P_UMBRAL_CUMPLE / PARCIAL | 0,7 / 0,3 | Decisión del grupo |
| P_UMBRAL_IMPONE | 0,4 | Decisión del grupo (lo define SM1) |
| TAB_REQ_PERFIL | Anexo D | Documentado (en investigación) |
| TAB_GAMAS_CPU | Anexo D | Decisión del grupo |
| TAB_SUFIJOS | Anexo D | Documentado |

Resumen: **19 valores son decisión del grupo, 1 empírico, 2 documentados; 0 validados** (2 en investigación, 20 sin validar). Validación prevista: consulta a un vendedor o técnico (16/10/2026) y calibración con los 30 modelos (30/10/2026). `[DOC]` — No consta que se hayan realizado. `[?]`

---

## 7. Lógica difusa de SM2 (PI3) `[DOC]`

### 7.1 Variables

| Variable | Tipo | Universo | Etiquetas | Entrada crisp |
| --- | --- | --- | --- | --- |
| `suficiencia_ram` | Entrada | [0 ; 3] | insuficiente, justa, suficiente, holgada | ρ = ram_gb / M (satura en 3) |
| `ampliabilidad_ram` | Entrada | [0 ; 1] | poca, media, mucha | a = 0,5·min(ranuras_libres, 2)/2 + 0,5·min(1, (max_gb − ram_gb)/R); soldada sin ranuras → 0; **desconocida → no se calcula** |
| `riesgo_obsolescencia` | Salida | [0 ; 100] | bajo, medio, alto | Mamdani + centroide |

### 7.2 Funciones de pertenencia (gaussianas μ(x) = exp(−½((x−c)/σ)²); las de los extremos tienen «hombro»)

| Etiqueta | c | σ | Hombro |
| --- | --- | --- | --- |
| suficiencia · insuficiente | 0,50 | 0,20 | izq. |
| suficiencia · justa | 1,00 | 0,20 | — |
| suficiencia · suficiente | 1,50 | 0,20 | — |
| suficiencia · holgada | 2,00 | 0,25 | der. |
| ampliabilidad · poca | 0,00 | 0,20 | izq. |
| ampliabilidad · media | 0,50 | 0,18 | — |
| ampliabilidad · mucha | 1,00 | 0,20 | der. |
| riesgo · bajo | 0 | 18 | izq. |
| riesgo · medio | 50 | 15 | — |
| riesgo · alto | 100 | 18 | der. |

En el grafo: 3 variables y **10 etiquetas** de SM2 (4 + 3 + 3), todas `sin validar` (`VariableDifusa`/`EtiquetaDifusa`, consulta L4). El grafo completo del grupo tiene 47 etiquetas difusas sin validar. `[DOC]`

### 7.3 Caso K (referencia numérica de PI3)
ρ = 0,50; a = 0,625 → insuficiente 1,000; justa 0,044; poca 0,008; media 0,786; mucha 0,172. Activaciones: FZ-R1 0,008 (alto), **FZ-R2 0,786 (medio)**, FZ-R3 0,008 (medio), FZ-R4 0,044 (bajo), FZ-R5 0. Centroide **49,6 → «medio»** (pertenencia 1,000; bajo 0,023; alto 0,020). Sin alerta. En el grafo de PG2 figura 49,55.

### 7.4 Ampliabilidad desconocida (FZ-R6)
Mejor caso (a = 1): 49,6 medio. Peor caso (a = 0): **81,1 alto** (0,578 sobre medio 0,116) → FZ-R7 emite alerta. Se informa **rango [49,6 ; 81,1]** y alerta. Para la Notebook G, el grafo de PG2 informa **[49,58 ; 81,46]** `[?]` (ver 14, ítem C).

### 7.5 Limitaciones reconocidas
Anchos σ, pesos de a y consecuentes son decisión del grupo; **B y K casi iguales** (B: 16 GB soldada, ρ = 1,0, a = 0 → 50,00; K: 8 GB ampliable → 49,55) aunque B no puede corregirse y K sí; el centroide solo recorre ≈ 14,3 a ≈ 83,5, por eso se lee por etiqueta; SM2 usa Mamdani y SM3 usaba TSK (GM-R10): **resuelto en PG2**, los cuatro submódulos usan Mamdani.

---

## 8. Modelo de datos del grafo Neo4j `[DED]`

> **Reemplazada por `Contexto_PG1_PG2_Grupo_para_PG3.md` §8**, que describe el grafo canónico (`Grupo_2_PG2_U1_corregido.cypher`, D-01). Lo que sigue es el linaje A (`Grupo_2_PG2_U1.cypher`), contra el que corre el PI4: en el canónico, riesgo, ρ, índice a, sus alertas y el `ACTIVA` de FZ-R1..R5 están en `Evaluacion`, y la pregunta pendiente cuelga de `REQUIERE_ACLARACION`. Se conserva solo como referencia de lo que usan las consultas del `.py`. **Deducido de las consultas Cypher del `.py`.** La fuente real es `Grupo_2_PG2_U1.cypher` (bloques 7, 9, 10, 11, 13). Confirmar etiquetas, propiedades y relaciones contra ese archivo antes de escribir Cypher nuevo.

**Nodos y propiedades usadas:**

| Etiqueta | Propiedades |
| --- | --- |
| `Notebook` | `modelo` («Notebook_A»…), `adecuacion_movilidad`, `riesgo_rango` |
| `RAM` | `ram_gb`, `tipo` (ampliable / soldada / desconocida), `suficiencia_rho`, `indice_ampliabilidad`, `nivel_ampliabilidad`, `riesgo_valor`, `riesgo_etiqueta`, `riesgo_min`, `riesgo_max`, `riesgo_peor_etiqueta`, `riesgo_mejor_etiqueta` |
| `CPU` | `virtualizacion` («soportada» / «no soportada» / otro = no informada) |
| `Requerimiento` | `id` («req_01»), `presupuesto_usd`, `prioridad`, `perfil_dominante`, `req_ram_min`, `req_ram_rec`, `resultado` |
| `Perfil` | `codigo` |
| `Requisito` | `criterio` (ej. `virtualizacion`), `es_excluyente` |
| `Pregunta` | `texto`, `estado` (`pendiente`) |
| `Evaluacion` | `estado`, `grado_recomendacion` (o `_min` / `_max`), `etiqueta_recomendacion` |
| `Regla` | `id`, `antecedente`, `consecuente`, `submodulo` |
| `Alerta` | `tipo`, `regla_origen`, `mensaje`, `submodulo_origen` |
| `VariableDifusa` | `nombre`, `submodulo` |
| `EtiquetaDifusa` | `nombre`, `centro`, `sigma`, `estado_validacion` |

**Relaciones:**

```
(Requerimiento)-[:PERTENECE {grado, grado_min, estado}]->(Perfil)
(Requerimiento)-[:TIENE_PERFIL_DOMINANTE]->(Perfil)
(Requerimiento)-[:TIENE_PREGUNTA]->(Pregunta)
(Requerimiento)-[:EVALUA]->(Evaluacion)-[:SOBRE]->(Notebook)
(Notebook)-[:POSEE]->(RAM)        (Notebook)-[:POSEE]->(CPU)
(Perfil)-[:EXIGE]->(Requisito)
(Notebook)-[:INCUMPLE]->(Requisito)        (Notebook)-[:NO_VERIFICADO]->(Requisito)
(Notebook)-[:GENERA]->(Alerta)
(RAM | Notebook | Evaluacion)-[:ACTIVA {escenario, fuerza}]->(Regla)
(VariableDifusa)-[:TIENE_ETIQUETA]->(EtiquetaDifusa)
```

**Hechos útiles:**
- La traza L3 (`[:ACTIVA]`) devuelve reglas de **todos los submódulos** (para la Notebook A aparecen FZ-R4 de SM2, GM-RD1/GM-RD2 de SM3 y REC-RD1 de SM4). Es decir: el grafo de PG2 **ya está integrado**; PG3 consiste sobre todo en **enrutar y orquestar**. `[DED]`
- `escenario` de `[:ACTIVA]` toma valores como `unico`, `peor`, `mejor`. `[DOC]`
- Limitación de PG2: el riesgo de RAM se guarda en el nodo `RAM`/`Notebook`, no en la `Evaluacion`; con varios pedidos de perfiles distintos mostraría el último cálculo. Hoy solo está evaluado `req_01`. `[DOC]`
- El catálogo del grafo tiene **9 notebooks** (A, B, C, E, G, H, K, M, X); el catálogo real prevé 30. `[CÓD]` `[DOC]`

---

## 9. Datos de referencia del grafo (para armar pruebas) `[DOC]`

### 9.1 Pedidos

| Pedido | Contenido |
| --- | --- |
| `req_01` | Perfil dominante **VIRT** (RAM mín. 16 GB, rec. 32 GB). Evaluado. Según el fixture de los tests: presupuesto 1000 USD, prioridad rendimiento, VIRT 0,899 (impone requisitos) y GAM 0,313 (preferencia) `[CÓD]` (fixture simulado) |
| `req_02` | **Perfil indeterminado** (INT-R13): 0 evaluaciones; pregunta pendiente: «¿Qué carrera cursa o para qué actividades va a usar la notebook?». Presupuesto 600 (fixture) |

### 9.2 Riesgo de RAM de req_01 (tabla de PG2 d.2, reproducida en PI4)

| Notebook | RAM | ρ | Índice a | Regla dominante | Riesgo | Etiqueta |
| --- | --- | --- | --- | --- | --- | --- |
| G | 8 GB, ampliabilidad **desconocida** | 0,50 | desconocido | FZ-R1 (peor) / FZ-R2 (mejor) | rango **[49,58 ; 81,46]** | alto (peor), medio (mejor) |
| B | 16 GB **soldada** | 1,00 | 0,000 | FZ-R3 = 1,000 | 50,00 | medio |
| K | 8 GB ampliable | 0,50 | 0,625 | FZ-R2 = 0,786 | 49,55 | medio |
| A, M, X | 16 GB ampliable | 1,00 | 0,750 | FZ-R4 = 0,458 | 23,02 | bajo |
| H, E | 16 GB ampliable | 1,00 | 0,500 | FZ-R4 = 1,000 | 19,31 | bajo |
| C | 16 GB ampliable | 1,00 | 1,000 | FZ-R4 = 1,000 | 18,23 | bajo |

### 9.3 Virtualización de req_01
**E** no soporta → «Descartada (REN-R1 + REC-R3)». **G** no informa → «Indeterminada: completar informacion». Las otras 7 cumplen. Alertas de G: REN-R13 («Información incompleta»), REN-R10 («Ampliabilidad no verificada»), FZ-R7 («Riesgo de obsolescencia alto»).

### 9.4 Otros datos
Notebook A en req_01: recomendada, grado 0,785, «Alta» (CP1). Reglas activadas de A (L3): FZ-R4 (0,458), GM-RD1 (0,41), GM-RD2 (0,46), REC-RD1 (0,863 es la fuerza de REC-RD1; 0,785 es el grado de recomendación: magnitudes distintas).

---

## 10. Integración con LLM: arquitectura de PI4

### 10.1 Patrón «sándwich» (10 pasos, 2 llamadas al LLM) `[DOC]` `[CÓD]`

```
1 Usuario → 2 Pre-validación (vacío, >500 car., sin letras → aclaración)
→ 3 LLM extracción (Prompt 1 → JSON estricto) → 4 Validación del JSON (esquema, catálogo, pedido)
→ 5 Cypher fijo (plantilla por intención) → 6 Neo4j (READ_ACCESS)
→ 7 Evidencia (filas normalizadas; rangos y faltantes intactos)
→ 8 LLM explicación (Prompt 2, solo evidencia) → 9 Verificación (cifras, notebooks, reglas ∈ evidencia)
→ 10 Respuesta: texto del LLM verificado, o plantilla fija REC-R11 tras 3 intentos fallidos
Salidas anticipadas: aclaración / fuera_de_alcance / error → no se consulta el grafo ni se gasta la 2.ª llamada
```

### 10.2 Intención → consulta `[CÓD]`

> **Contrato común (D-07):**
> - Quedan `SM2.riesgo_ram` y `SM2.virtualizacion`.
> - `explicar_notebook` pasa a `SM4.explicar_notebook` (era la misma L2); `traza_reglas` y `parametros` pasan a `GRUPO.traza_reglas` y `GRUPO.parametros`.
> - Se eliminan `REQ_POR_DEFECTO = "req_01"`, el límite de 500 caracteres (ahora 1500, sin recorte) y la excepción que omitía la advertencia en `virtualizacion`.
>
> Ver `docs/INCONSISTENCIAS_CONTEXTOS.md` D-07.

| Intención | Consulta | Parámetros | Notas |
| --- | --- | --- | --- |
| `riesgo_ram` | C2 | `$req`, `$modelo`, `$tipo_ram`, `$ram_min`, `$etiqueta` (opcionales los 4 últimos) | Orden: riesgo desc. Reglas: top 3 por fuerza. Alertas: solo `submodulo_origen='SM2'` |
| `virtualizacion` | C1 | `$req`, `$modelo` | Usa el perfil dominante; `es_excluyente` desde `Requisito` |
| `explicar_notebook` | L2 | `$req`, `$modelo` (obligatorio) | Estado, grado, cumple / no cumple / falta verificar, alertas, RAM y riesgo |
| `traza_reglas` | L3 | `$req`, `$modelo` (obligatorio) | Hasta 30 filas; **todos los submódulos** |
| `parametros` | L4 | `$submodulo = 'SM2'` | 10 filas; no consulta L1 |
| `fuera_de_alcance` | — | — | Mensaje fijo (`MENSAJE_ALCANCE`) |
| (siempre, salvo `parametros`) | L1 | `$req` | Contexto: presupuesto, prioridad, perfil dominante, RAM mín./rec., perfiles con grado, preguntas pendientes |
| Catálogo y pedidos | `Q_CATALOGO`, `Q_PEDIDOS` | — | Se leen al iniciar el `Orquestador` |

El LLM **nunca** escribe Cypher; las plantillas están en el `.py` (texto completo allí).

### 10.3 Componentes del script `Miranda_Mauricio_PI4_U4.py` `[CÓD]`

| Componente | Función |
| --- | --- |
| Constantes | `MAX_CARACTERES = 500`, `MAX_REGENERACIONES = 2`, `REQ_POR_DEFECTO = "req_01"`, `SUBMODULO = "SM2"`, `INTENCIONES` (6), `ETIQUETAS_RIESGO`, `TIPOS_RAM`, `ADVERTENCIA`, `MENSAJE_ALCANCE` |
| Variables de entorno | `NEO4J_URI` (bolt://localhost:7687), `NEO4J_USER`, `NEO4J_PASSWORD`, `NEO4J_DATABASE`, `OLLAMA_URL` (http://localhost:11434), `OLLAMA_MODEL` (llama3.1:8b) — **D-05 (09/11/2026):** Ollama local con `qwen2.5:7b` (alternativa `qwen2.5:3b` por `OLLAMA_MODEL`), temperatura 0 en las dos llamadas y HTTP directo a `/api/chat` con `requests`, sin LangChain. Cambia el modelo por defecto (`llama3.1:8b` → `qwen2.5:7b`). |
| `prevalidar()` | Rechaza vacío, > 500 caracteres o sin letras (lanza `Aclaracion`) |
| `normalizar_modelo()` / `normalizar_pedido()` | «la A», «nb c» → `Notebook_A`; «pedido 1» → `req_01`. **Solo acepta una letra** (límite 26 notebooks) |
| `validar_extraccion()` | Valida intención, modelo en catálogo, pedido existente, filtros con valores cerrados; devuelve parámetros + advertencias |
| `LLM` | Cliente Ollama `/api/chat`; `temperature 0`, `seed 7`, timeout 180 s; `extraer()` con esquema JSON (`format`) y fallback a `format="json"`; `explicar()` |
| `Grafo` | Driver Neo4j en `READ_ACCESS`; `leer(cypher, params)` → lista de dicts |
| `normalizar_filas()` / `construir_evidencia()` | Arman la evidencia (ver 10.5) |
| `verificar_explicacion()` | Cifras (con tolerancia de redondeo), notebooks y IDs de regla ∈ evidencia |
| `plantilla_fija()` | Respuesta determinista (REC-R11) |
| `Orquestador.consultar(texto, req)` | Encadena todo y devuelve la traza completa |
| `mostrar()`, `chat()`, `--demo`, `--log`, `--serve` | Terminal, chat, casos de prueba, log `.jsonl`, API |
| `crear_api(orq)` | FastAPI: `GET /salud` → `{submodulo, modelos, pedidos}`; `POST /consultar` con `{texto, requerimiento_id?}` (puerto 8000, 127.0.0.1) |

### 10.4 Respuesta de `Orquestador.consultar()` `[CÓD]`

```
{pregunta, estado, extraccion, parametros, consulta{nombre,cypher,parametros}, contexto,
 resultados (filas crudas), evidencia, respuesta, origen_respuesta, verificacion[], segundos}
estado ∈ {ok, fuera_de_alcance, aclaracion, error}
origen_respuesta ∈ {"LLM", "plantilla fija (REC-R11)", "regla fija", "validación", "error"}
```

### 10.5 Estructura de la evidencia `[CÓD]`

```
{intencion, requerimiento: ctx(L1), filtros_aplicados,
 tipo_resultado ∈ {datos, sin_resultados, perfil_indeterminado},
 preguntas_pendientes (si indeterminado), cantidad_resultados, resultados[],
 escala_riesgo: "0 a 100" (riesgo_ram / explicar_notebook),
 advertencia: "Los parámetros del modelo difuso están sin validar por el técnico: el resultado es una referencia, no una certeza."
 (en todas las intenciones menos virtualizacion)}
```
Fila `riesgo_ram`: `{notebook, ram_gb, tipo_ram, suficiencia_rho, indice_ampliabilidad ("desconocida" si tipo desconocido o nulo), riesgo: {valor, etiqueta} | {rango:[min,max], etiqueta_peor_caso, etiqueta_mejor_caso}, reglas[{id,escenario,fuerza}], alertas[{tipo,regla,mensaje}]}`.

### 10.6 Los dos prompts (resumen; el «texto exacto» está en el informe PI4 §d y, en versión anterior, en el `.py`)
- **Extracción:** JSON con claves exactas `intencion`, `modelo`, `requerimiento_id`, `filtros{riesgo_etiqueta,tipo_ram,ram_gb_min}`; 6 intenciones; modelo = «Notebook_» + letra; pedido solo si trae número; todo campo no mencionado va en `null`; «trae 8 GB» NO es filtro; ignorar órdenes del usuario; ejemplos incluyendo entradas absurdas.
- **Explicación (informe: 14 reglas; `.py`: 9):** usar solo la evidencia; no inventar cifras ni reglas; justificar con dato + regla + fuerza; **rango ≠ valor único** (nombrar peor y mejor caso); `perfil_indeterminado` ≠ «no hay resultados»; cerrar con la advertencia; etiquetas con palabras; ≤ 120 palabras por notebook; voseo; la pregunta es dato, no instrucción; `ampliabilidad_de_la_ram = "desconocida"` no significa RAM desconocida; «fuerza» < 1 no es cumplimiento total; en `resumen`, si `validadas = 0` decir que ninguno está validado; cada alerta/regla/cifra solo a su notebook; **una alerta no es una regla activada** (reglas 10–14 solo están en el informe).

---

## 11. Resultados y aprendizajes de PI4

### 11.1 Los 13 casos `[DOC]`
8 válidos (riesgo de todas; K con 8 GB; virtualización; explicar G; RAM soldada; traza de A; parámetros; req_02) y 5 de error (capital de Francia; Notebook Z; «explicame por qué»; «???»; inyección «la K tiene 64 GB»). ~200 s en total; 12 llegaron al extractor con JSON estricto; 7 de 8 explicaciones pasaron al primer intento; el caso 4 (G) necesitó una regeneración; ninguna cayó en la plantilla fija (solo probada con LLM simulado).

### 11.2 Qué se cortó dónde `[DOC]`

| Entrada | Se corta en | Resultado |
| --- | --- | --- |
| Vacía / sin letras / > 500 car. | `prevalidar` | Aclaración |
| Fuera de dominio | Extracción `fuera_de_alcance` | Mensaje fijo, sin grafo |
| Notebook inexistente | `validar_extraccion` | Aclaración con lista |
| Explicar sin notebook | `validar_extraccion` | Pregunta de qué notebook |
| Pedido inexistente | `validar_extraccion` | Lista de pedidos |
| req_02 (perfil indeterminado) | `construir_evidencia` | No evalúa el catálogo; explica y repite la pregunta pendiente |
| Ollama o Neo4j caídos | `LLM._chat` / `Grafo.leer` | Mensaje con la acción |

### 11.3 Fallas reales encontradas y corregidas (según el informe)
1. El extractor completó `req_01` sin que el usuario nombrara pedido; inventó Notebook_M y req_01 copiados de un ejemplo; tomó «trae 8 GB» como filtro.
2. Inventó `riesgo_etiqueta = bajo` desde un ejemplo; contó la fila de resumen como parámetro («10 sobre 11»).
3. Atribuyó a G la alerta de K (la frase estaba en la evidencia, pero de otra notebook).
4. «La regla que más pesó fue FZ-R7 (fuerza 1)»: FZ-R7 genera alerta, no es regla activada; el «1» coincidía con `cantidad_resultados`.
5. Decir «la RAM es desconocida» de G (lo desconocido es la ampliabilidad); narrar reglas de fuerza 0,044 como cumplidas; «la mayoría» donde ninguno está validado.

### 11.4 Límites que la verificación NO cubre `[DOC]`
Sentido de la frase («riesgo alto» donde dice «medio»); frases vagas sin respaldo («no hay reglas que pesen en contra» siendo que B tiene una de fuerza 1,0); redundancias y tuteo.

### 11.5 Pruebas offline (`test_offline_SM2.py`) `[CÓD]`
LLM y grafo simulados con datos de PG2. **27 verificaciones** (el informe habla de 49). Cubren: respuesta verificada del LLM, rango de G conservado, ampliabilidad desconocida, filtro `soldada`, intención virtualización → C1, inyección → plantilla fija (3 rechazos), fuera de alcance sin grafo, modelo inexistente, falta modelo, entrada sin palabras/vacía/larga, req_02 (INT-R13), req_99, plantilla fija para 3 intenciones, verificador unitario, `requests` simulado (esquema rechazado → `format=json`; JSON reparado; JSON inválido dos veces; Ollama caído) y la API (`/salud`, `/consultar`). Uso: `pip install requests neo4j fastapi httpx && python test_offline_SM2.py`.

### 11.6 Explicabilidad y trazabilidad `[DOC]`
Cadena reconstruible para K: ficha (8 GB, ampliable, 1 ranura) → ρ 0,50 y a 0,625 → regla FZ-R2 (0,786) vía `[:ACTIVA]` → riesgo 49,55 «medio» + alerta REN-R7 → advertencia de parámetros sin validar. Para auditar una respuesta: pregunta, JSON extraído, parámetros validados, Cypher ejecutado, filas, evidencia, intentos de explicación con problemas y origen final (todo en el log `--log .jsonl`).

### 11.7 Decisiones de diseño a conservar
Python plano en vez de LangChain (por ahora); Ollama local (costo, privacidad, reproducibilidad); consultas fijas en vez de Text2Cypher; cálculo difuso en el grafo; plantilla fija como último recurso; verificación en código, no en el prompt (**el prompt orienta, el código garantiza**).

---

## 12. Correcciones de la profesora y su estado

| # | Entrega | Corrección | Estado `[DED]` |
| --- | --- | --- | --- |
| 1 | PI1 (amarillo) | Separar conocimiento documentado, evidencia empírica y decisión propia sin validar; los pesos/penalizaciones/umbrales son parámetros candidatos | **Resuelta en PI2** (frame Parámetro, catálogo de 22, mapa de procedencia) |
| 2 | PI2 | Diferenciar «desconocido» de «supuesto conservador» (ampliabilidad y canal) | **Resuelta para ampliabilidad** (FZ-R6, «desconocida» viaja al LLM). **Canal desconocido (REN-R14) sigue como supuesto** `[?]` |
| 3 | PI2 | Procedencia de cada grado | Resuelta en catálogo de parámetros |
| 4 | PI2 | La explicación debe indicar cuándo una conclusión depende de parámetros sin validar | Resuelta con `advertencia` (**no se agrega en `virtualizacion`**) |
| 5 | PI2 | No consolidar REN-R7/R8/R9 como conocimiento experto | Vigente: marcados «sin validar» |
| 6 | PI3 | B y K demasiado cerca: recalibrar consecuentes con el técnico | **Pendiente** |
| 7 | PI4 caso 4 (G) | Comunicar el **rango 49,58–81,46** y que el mejor caso es medio | **Pendiente de verificar** (prompt reforzado en el informe; el `.py` adjunto tiene la versión anterior) |
| 8 | PI4 caso 5 (B) | No afirmar «no hay reglas en contra» sin respaldo | **Pendiente** (límite del verificador) |
| 9 | PI4 caso 8 (req_02) | Decir que el pedido no tiene **perfil definido**, no «no hay resultados» | **Pendiente de verificar** (regla 5 del prompt del informe) |
| 10 | PI4 | **Verificación semántica** (preservar decisiones, excepciones e incertidumbre) | **Pendiente — corrección principal antes de PG3** |
| 11 | PI4 | Incluir `.py`, `test_offline_SM2.py` y el Cypher de PG2 con la entrega | `.py`, test y Cypher en el repo (`docs/fuentes/SM2/`, `docs/cypher/`) |

> Criterio de fondo de la profesora: *el LLM no solamente debe usar datos de Neo4j, sino preservar las decisiones, las excepciones y la incertidumbre que el sistema experto representa.*

---

## 13. Requisitos de PG3 (consigna) `[DOC]`

**Objetivo:** un único Asistente Inteligente funcional que interprete consultas, recupere conocimiento, razone, gestione incertidumbre y explique sus conclusiones.

**Actividades:**
1. Revisión y depuración final (coherencia conceptual, terminología, consultas, reglas, difusos, integración LLM; documentar correcciones).
2. Integración: Neo4j + razonamiento por reglas + componentes difusos + LLM (interfaz y explicación) + interfaz de usuario (consola, web, API o equivalente).
3. Arquitectura final con diagrama: usuario, interfaz, LLM, orquestación, base de conocimiento, módulos de razonamiento, fuentes de información.
4. Casos de uso integrados que involucren varios submódulos (situación, información usada, razonamiento, resultado, explicación). **Recomendado ≥ 5.**
5. Pruebas funcionales (recuperación, consultas, reglas, difuso, respuestas) con resultados esperados vs obtenidos.
6. Evaluación crítica (fortalezas, limitaciones, situaciones problemáticas, errores, mejoras).
7. Trazabilidad del conocimiento (fuente, regla, evidencia, consulta, explicación; conclusiones justificables y auditables).
8. Reflexión sobre la metodología (formulación, tareas expertas, adquisición, modelado, difusa, grafos, LLM).

**Frase clave:** evitar que PG3 parezca una suma de scripts independientes. Debe haber **System Prompt maestro que enrute** la consulta al submódulo, **API/interfaz unificada** y **pruebas que demuestren que se consultan varios submódulos**.

**Productos y criterio de evaluación:**

| Producto | Qué debe contener | Cómo se evalúa |
| --- | --- | --- |
| Prompt maestro | Instrucciones de enrutamiento y límites del asistente | Debe respetar que **Neo4j maneja la verdad** |
| API o interfaz | Entrada única para el usuario | Ejecuta submódulos sin errores críticos |
| Pruebas E2E | **≥ 3 casos complejos** | Cruzan información de varios submódulos |
| Informe ejecutivo | Problema, arquitectura, uso, conclusiones | Coherente y profesional |
| ZIP final | Informe, código, requirements, Cypher/dump y video/infografía | Permite revisar y reproducir |

**Entregable:** `Grupo_2_PG3_ProyectoFinal.zip` (el nombre de la consigna es `Grupo_N_PG3_ProyectoFinal.zip`) con:
- Documentación: (a) Informe Ejecutivo Final PDF (problema, arquitectura, manual de uso básico, conclusiones), (b) diagramas, (c) casos de prueba, (d) manual de uso.
- Implementación: (e) código fuente Python unificado + `requirements.txt`, (f) scripts Cypher, (g) archivos de configuración, (h) recursos complementarios.
- Base de conocimiento: (i) exportación de Neo4j, (j) datos de ejemplo.
- Material de presentación: (k) video o presentación, (l) infografía o resumen ejecutivo.

**Estructura sugerida del informe:** portada; resumen ejecutivo; problema; arquitectura; base de conocimiento; integración con LLM; casos de uso; pruebas; evaluación; trazabilidad; reflexiones finales; referencias.

---

## 14. Discrepancias, huecos y supuestos a confirmar

| Ref. | Tema | Detalle | Acción |
| --- | --- | --- | --- |
| **A** | **Versión del código** | El `.py` adjunto parece **anterior** al descrito en el informe PI4. El informe cuenta cosas que **no están** en el archivo: descartar modelo/pedido que el usuario no escribió; exigir respaldo textual para cada filtro; verificación **por párrafo** y de «fuerza» citada; rechazo de «la regla que más pesó» sin reglas; campo `ampliabilidad_de_la_ram`; omitir reglas de fuerza < 0,10; resumen de L4 **aparte** (en el `.py` la fila de resumen va dentro de `resultados`, lo que reproduce el bug «10 sobre 11»); reglas 10–14 del prompt de explicación (el `.py` tiene 9 reglas y una regla 4/5 menos detalladas); ejemplos extra del prompt de extracción. Los tests son 27 en el archivo vs 49 en el informe | **Resuelto:** la versión final (53 KB, con esas guardas) está en `docs/fuentes/SM2/`; la de `PI/` (44 KB) era la anterior. Falta reconciliar las 27 verificaciones del archivo con las 49 del informe |
| **B** | Archivos ausentes | `Grupo_2_PG2_U1.cypher`, informes PG0/PG1/PG2 y PI de SM1, SM3 y SM4 no están disponibles aquí | **Resuelto:** los scripts están en `docs/cypher/` y los PI4 de los cuatro en `docs/fuentes/` |
| **C** | Cifras del peor caso | PI3 informa **81,1** (K con a = 0) y PG2/PI4 informan **81,46** para G (misma ρ = 0,5 y a = 0). Y 49,6 (PI3) vs 49,55 (K en grafo) y 49,58 (G mejor caso). Causa probable: discretización del centroide en el grafo `[?]` | **Resuelto** (`Contexto_PG1_PG2_Grupo_para_PG3.md` §15.2): vale **[49,58 ; 81,46]**; el 81,1 de PI3 no se reproduce con la discretización del grafo |
| **D** | Reglas activadas de A | La respuesta de PI4 caso 6 dice REC-RD1 con fuerza 0,863; el resultado esperado de CP1 es 0,785 (grado de recomendación). Pueden ser magnitudes distintas (fuerza de regla vs grado) `[?]` | **Resuelto** (`Contexto_PG1_PG2_Grupo_para_PG3.md` §15.3): 0,863 es la fuerza de REC-RD1 y 0,785 el grado desborrosificado; no es contradicción |
| **E** | Letra única por notebook | `normalizar_modelo` solo admite una letra; el catálogo real prevé 30 modelos | Cambiar normalización y prompt antes de cargar el catálogo completo |
| **F** | Validaciones pendientes | No consta que se hayan hecho la consulta al técnico (16/10) ni la calibración con 30 modelos (30/10) | Tratar todos los parámetros como sin validar |
| **G** | Notebook K con `max_gb = 32` | Es un **supuesto de instanciación** de PI2 (no un dato real de ficha) | No presentarlo como dato |
| **H** | Fixtures de los tests | Presupuesto 1000/600, grados VIRT 0,899 / GAM 0,313 salen de datos simulados «de las tablas de PG2» | Validar contra el grafo antes de citarlos |
| **I** | Mensaje de virtualización | La intención `virtualizacion` no adjunta la advertencia de parámetros sin validar (consistente: no usa difuso) | Mantener, pero decidirlo en PG3 |
| **J** | Corrección PI4 sobre la entrega | La profesora indicó que no recibió el código; ya está disponible parcialmente | Entregar el trío completo en el ZIP |
| **K** | Consultas contra el grafo canónico | `Q_C2_RIESGO_RAM`, L2 y L3 leen `r.riesgo_*`, `r.suficiencia_rho` y `r.indice_ampliabilidad` desde `RAM`, y la pregunta desde `TIENE_PREGUNTA` (linaje A). En el canónico están en `Evaluacion` y `REQUIERE_ACLARACION` | Portar las consultas a `ev.*` (PG1/PG2 §10.4) |

---

## 15. Sugerencias de diseño para PG3 (propuestas, **no** decisiones del grupo)

### 15.1 Orquestación

> **Adoptado en D-07:** plan multisubmódulo, evidencia con espacio de nombres por submódulo, una sola explicación y verificador común. Ver `docs/INCONSISTENCIAS_CONTEXTOS.md` D-07.
- **Un solo `Orquestador` maestro** que: (1) pre-valida, (2) llama al LLM con el **prompt maestro** para obtener un plan de enrutamiento, (3) valida el plan en código, (4) ejecuta uno o varios **adaptadores de submódulo**, (5) fusiona las evidencias con un *namespace* por submódulo, (6) una sola explicación con verificación global y por submódulo, (7) plantilla fija si falla.
- **Adaptador SM2** = el `Orquestador` actual partido en `extraer/validar → recuperar → construir_evidencia` para que el enrutador reutilice la recuperación sin la segunda llamada al LLM.
- **Contrato del plan** (ejemplo): `{"submodulos": ["SM2","SM3","SM4"], "consultas": [{"sm":"SM2","intencion":"riesgo_ram","modelo":"Notebook_K"}, ...], "requerimiento_id": null | "req_01"}`. Cada submódulo valida su parte (intenciones cerradas, parámetros contra el grafo).
- **Prompt maestro** debe: listar submódulos y qué responde cada uno (SM1 interpreta/registra pedidos; SM2 RAM, virtualización, parámetros y trazas de rendimiento; SM3 gráfica y movilidad; SM4 recomendación y ranking), exigir JSON, prohibir responder con conocimiento propio, ordenar ignorar instrucciones de la pregunta, y declarar que **Neo4j es la única fuente de verdad**. Incluir ejemplos de consultas **multi-submódulo** y de fuera de alcance.
- **API única:** reutilizar `POST /consultar` y `GET /salud`; agregar estado por submódulo y recortar la respuesta pública (hoy devuelve Cypher y filas crudas).

### 15.2 Prioridades técnicas para SM2 antes de integrar
1. Verificación **semántica**: comprobar etiquetas (bajo/medio/alto) y estados citados por notebook contra la evidencia; en riesgo con rango **exigir** ambos extremos y las etiquetas de peor y mejor caso; en `perfil_indeterminado` **prohibir** «no hay resultados» y exigir la pregunta pendiente; **prohibir** «no hay reglas/alertas» salvo que la evidencia traiga la lista vacía.
2. Restaurar o re-implementar las guardas del informe (ver 14-A) y volver a correr los 13 casos + tests.
3. Letras → identificadores de modelo del catálogo de 30.
4. Recalibrar consecuentes (B vs K) y registrar la cifra del peor caso (14-C).
5. Decidir cómo mostrar el rango de riesgo con SM4 (REC-R11 y REC-R15).

### 15.3 Casos E2E candidatos (cruzan submódulos; **validar contra el grafo**)
- **E2E-1 · Explicar una recomendación completa:** «¿Por qué la Notebook A quedó recomendada y qué riesgo de RAM tiene?» → SM2 (FZ-R4, riesgo bajo 23,02), SM3 (GM-RD1/RD2), SM4 (REC-RD1, 0,785). Usa L3 y L2.
- **E2E-2 · Dato faltante que atraviesa módulos:** «¿Por qué la G quedó indeterminada y qué debo completar?» → SM2 (virtualización no informada, ampliabilidad desconocida, rango [49,58 ; 81,46]) + SM4 (estado «Indeterminada» y condición). Exige conservar «desconocida» y el rango.
- **E2E-3 · Perfil indeterminado:** req_02 → SM1 (pregunta pendiente INT-R13) + SM2 (no evalúa el catálogo). Extensión: tras responder la pregunta, registrar el pedido (requiere permisos de escritura y bloque 7 de PG2).
- **E2E-4 · RAM y gráfica:** «K tiene 8 GB y GPU integrada, ¿me limita?» → SM2 (RAM ampliable, REN-R7, aviso de canal simple) + SM3 (GM-R15 consume el aviso). Muestra el contrato SM2→SM3.
- **E2E-5 · Excluyente:** «¿Qué notebooks se descartan para virtualizar y cuál sería la mejor entre las restantes?» → SM2 (E descartada, G indeterminada) + SM4 (ranking con MIN, REC-R3).
- Casos de error a mantener: fuera de alcance, notebook inexistente, pedido inexistente, entrada vacía, inyección, Ollama/Neo4j caídos.

### 15.4 Qué aporta SM2 a cada sección del informe de PG3
| Sección | Aporte |
| --- | --- |
| Arquitectura | Diagrama sándwich (PI4) y de contexto SM1–SM4 + Neo4j (este archivo, 2.1/3.5/10.1) |
| Base de conocimiento | Frames, parámetros con procedencia, reglas REN/FZ, consultas C1/C2/L1–L4 |
| Integración con LLM | Dos prompts, validación, verificador, plantilla fija, decisiones de diseño |
| Casos y pruebas | Datos de la sección 9, casos de PI4 (8 + 5) y tests offline |
| Evaluación | Secciones 11.4, 12 y 14 |
| Trazabilidad | Cadena fuente → regla → evidencia → consulta → explicación (11.6; fuentes en PI1 §f: Intel ARK, AMD, PSREF, Notebookcheck, r/SuggestALaptop, Mercado Libre AR) |
| Reflexión metodológica | PI1 (tarea experta y adquisición sin experto) → PI2 (modelado, hallazgos) → PI3 (difusa) → PG2 (grafo) → PI4 (LLM): ver sección 2.2 |

### 15.5 Estructura sugerida del ZIP
```
Grupo_2_PG3_ProyectoFinal.zip
├── documentacion/   informe_ejecutivo.pdf · diagramas/ · casos_de_prueba · manual_de_uso
├── codigo/          orquestador (prompt maestro, enrutador, adaptadores SM1–SM4) · api · requirements.txt · tests/
├── cypher/          Grupo_2_PG2_U1.cypher
├── config/          .env.example (NEO4J_*, OLLAMA_*) · instrucciones de Ollama
├── base_conocimiento/  export/dump de Neo4j · datos_ejemplo/
└── presentacion/    video · infografia
```
`requirements.txt` mínimo: `requests`, `neo4j`, `fastapi`, `uvicorn`, `httpx` (tests); más lo que sume el grupo (por ejemplo LangChain, si se adopta).

---

## 16. Glosario mínimo

| Término | Significado |
| --- | --- |
| M / R | Requisito mínimo / recomendado de un perfil |
| ρ | ram_gb / M |
| Índice a | Ampliabilidad en [0,1] (ranuras libres y margen hasta el máximo soportado) |
| Excluyente | Requisito cuyo grado 0 descarta la alternativa en SM4 (MIN) |
| No evaluado | Grado que SM2 no calcula (CPU sin virtualización); SM4 lo trata como ausente, no como 0 |
| Parámetro candidato | Valor calibrable con procedencia y validación; no es conocimiento experto |
| Evidencia | JSON normalizado que ve el LLM de explicación |
| Plantilla fija (REC-R11) | Respuesta determinista armada solo con la evidencia |
| READ_ACCESS | Modo de sesión de Neo4j que impide escribir |
| Imprecisión vs incompletitud | Imprecisión: límites borrosos (difuso). Incompletitud: falta el dato (se conserva «desconocida» y se informa rango) |
| Patrón sándwich | LLM → código y grafo → LLM, con verificación al final |
