# Contexto y Especificación de Submódulo: SM3 — Evaluación Gráfica y de Movilidad

* **Proyecto:** Asistente Experto para la Selección Personalizada de Notebooks
* **Cátedra:** Inteligencia Artificial · Departamento de Sistemas de Información · UTN FRM (Ciclo 2026)
* **Grupo:** Grupo 2 · Comisión 5K09
* **Responsable:** de Coninck, Ramiro (Legajo: 49998)
* **Base de Conocimiento:** grafo canónico `docs/cypher/Grupo_2_PG2_U1_corregido.cypher` (D-01), superconjunto de `Grupo_2_PG2_U1_bloques_0a12.cypher`, con el que corrió `sm3_asistente.py` en PI4 (código en `docs/fuentes/SM3/`). Lo que este documento afirma y el grafo no tiene está en la nota de §3.
* **Propósito:** Documento de contexto técnico de SM3 para el equipo (Olea, Miranda, Luconi Furque) para la integración, enrutamiento, ejecución y orquestación final en **PG3**.

---

## 1. Resumen Ejecutivo y Alcance del Submódulo

### 1.1 ¿Qué resuelve SM3?
El Submódulo 3 (SM3) evalúa la **capacidad gráfica y la movilidad física** de cada notebook frente a los requerimientos del comprador. Resuelve tres problemas críticos que no se desprenden de una simple lectura de la ficha técnica:
1. **Efecto TGP en GPU dedicada:** Dos notebooks con el mismo chip gráfico (ej. RTX 4060) rinden de forma muy diferente según los Watts asignados por el fabricante (TGP de 35 W a 115 W). SM3 evalúa la potencia térmica real mediante lógica difusa.
2. **Optimismo en la autonomía declarada:** La cifra comercial suele ser un 30% a 40% superior a la real. SM3 prioriza mediciones de laboratorio (`autonomia_medida_h`), penaliza cifras del fabricante mediante la regla `GM-R12` ($0.7 \times \text{declarada}$) guardando el valor en `autonomia_usada_h`, y trata los datos faltantes como incertidumbre epistémica (intervalo $[0.0, 1.0]$ sin inventar valores).
3. **Movilidad no compensatoria:** Expresiones como "liviana" o "buena batería" son graduales. SM3 aplica un principio experto no compensatorio: una excelente batería no tapa un peso excesivo (un equipo de 2.5 kg con 12 h de batería es pesado, no "bastante móvil").

### 1.2 Límites Estrictos de Responsabilidad (Fronteras en PG3)
* **SM1 (Facundo Olea):** Interpretación lingüística del pedido, deducción del perfil dominante (`OFI`, `DEV`, `VIRT`, `DIS`, `VID3D`, `GAM`, `DATOS`), requisitos mínimos consolidados (`req_gama_gpu`, `prioridad`) e indicadores de contexto (`usa_monitor_externo`, `entrena_modelos_gpu`).
* **SM2 (Mauricio Miranda):** Evaluación de `CPU` (gama, núcleos, virtualización), memoria `RAM` (GB, soldada/ampliable, ranuras libres, canal simple/doble y riesgo de obsolescencia) y `Almacenamiento` (SSD, slot M.2 libre). **SM3 no evalúa ni filtra CPU, RAM ni discos.**
* **SM3 (Ramiro de Coninck):** Evaluación de `GPU` (integrada/dedicada, gama, TGP, potencia relativa), `Pantalla` (resolución, tasa de refresco, sRGB), `Batería` (medida, declarada, usada/efectiva), `Peso` y cálculo de las adecuaciones de gráfica y movilidad con sus alertas y trazas de reglas.
* **SM4 (Martina Luconi):** Evaluación económica (`precio_usd` vs. `presupuesto_usd`), verificación de descartes excluyentes, ponderación multicriterio de las adecuaciones recibidas de SM2 y SM3, ranking y recomendación final explicada.

---

## 2. Contrato de Interfaz y Enrutamiento en PG3

### 2.1 Flujo Integrado E2E (Llamada Programática en Pipeline)
En el flujo principal de recomendación (cuando el usuario pide una sugerencia global de compra):
1. **SM1** extrae perfil y requisitos (`req_gama_gpu`, `prioridad`, `usa_monitor_externo`, etc.).
2. **SM2** procesa CPU/RAM y emite el aviso de canal de memoria (`canal_simple` o `desconocido`).
3. **SM3** recibe los requisitos, consulta el grafo PG2 y entrega a **SM4**:
   - `adecuacion_grafica` (en `Evaluacion`).
   - `adecuacion_movilidad` (en `Notebook`).
   - `alertas_sm3` (alertas de TGP recortado `GM-R8`, autonomía `GM-R11`/`GM-R12`, o ancho de banda `GM-R15`).
   - `excluyente_incumplido`: `true` si la GPU está 2 o más gamas por debajo del requisito (`GM-R14`).
   - Trazas de reglas difusas activadas (`GM-RD1..6`) con su fuerza.
4. **SM4** combina las adecuaciones de SM2 y SM3 con el presupuesto y formula la recomendación final.

### 2.2 Flujo Conversacional Especialista (Enrutamiento por Prompt Maestro)
Cuando el usuario realiza una pregunta orientada a aspectos visuales, gráficos o de traslado, el **System Prompt Maestro de PG3** deriva la consulta directamente a SM3:

| Intención del Usuario | Palabras Clave / Criterios | Submódulo Destino |
|---|---|:---:|
| Placa de video, rendimiento en juegos, render 3D, TGP, FPS, fidelidad de color, pantalla, sRGB, refresco | "placa de video", "GPU", "dedicada", "RTX", "pantalla", "OLED", "144Hz", "sRGB", "colores", "juegos", "render" | **SM3** |
| Peso, portabilidad, llevar a la facultad/viajes, duración de batería, cargador | "liviana", "peso", "kilos", "mochila", "batería", "autonomía", "horas sin enchufar", "viajar" | **SM3** |
| Consultas mixtas de potencia gráfica y portabilidad | "gamer liviana", "diseño con buena batería", "potente pero transportable" | **SM3** |
| Consultas sobre un modelo puntual en GPU, pantalla o batería | "¿Qué GPU tiene la Notebook_X?", "¿Cuánto dura la batería de la Notebook_M?" | **SM3** |
| Preguntas sobre procesador, memoria RAM, ampliabilidad, disco SSD | "procesador", "Ryzen", "Intel i7", "RAM", "8GB vs 16GB", "ampliar memoria", "SSD" | **SM2** (derivar a Miranda) |
| Preguntas de perfil o presupuesto global | "para qué sirve", "estudio abogacía", "tengo 800 USD", "¿cuál me conviene por mi plata?" | **SM1 / SM4** |

---

## 3. Ontología y Base de Conocimiento en Neo4j (`bloques_0a12.cypher`)

> **Verificado contra el canónico (09/11/2026):**
> - `margen_gama` toma `superior`, `justa` o `inferior`: no existe `excluye`.
> - `RAM.canal` está cargado (K en `simple`), pero **no hay regla GM-R15 ni alerta de ancho de banda**. Tampoco existen GM-R14 (con `INCUMPLE`) ni GM-R16, ni las alertas de GM-R12 y GM-R17.
> - Sin autonomía, `adecuacion_movilidad` queda en `null` y el rango [0 ; 1] lo arma SM4 (REC-R15).
> - La gama mínima de GPU sale de `Perfil.gama_gpu_min` (DIS 3, GAM 3, VID3D 4), no de la intensidad de SM1.
> - `entrena_modelos_gpu` y `req_gama_gpu` no existen.
> - `grado_pantalla` no se calcula en el grafo: llega como dato por par notebook-perfil (`SALIDA_PI2`). **D-03:** SM3 completa los 6 perfiles que faltan en `docs/cypher/salida_pi2.csv` con sus reglas de PI2 y documenta el método.
>
> Ver D-04 y D-10 en `docs/INCONSISTENCIAS_CONTEXTOS.md`.

La base de datos oficial del proyecto implementa una distinción clave surgida de las devoluciones de PG2:
* **En `(:Notebook)` y sus componentes** residen los datos técnicos objetivos y las conclusiones que **no dependen del comprador**: la **movilidad** (`adecuacion_movilidad`), calculada a partir del peso y la batería.
* **En `(:Evaluacion)`** (`(c:Requerimiento)-[:EVALUA]->(ev:Evaluacion)-[:SOBRE]->(n:Notebook)`) residen los resultados que **dependen del perfil del comprador**: `grado_gpu`, `margen_gama`, `grado_pantalla`, `adecuacion_grafica` y las alertas relativas al perfil.

### 3.1 Estructura de Nodos y Propiedades del Grafo Real

```
(:Comprador)-[:FORMULA]->(:Requerimiento)-[:EVALUA]->(:Evaluacion)-[:SOBRE]->(:Notebook)
                                                         │                      │
                                       (alertas_ev) ◄────┤                      ├──[:POSEE]──► (:GPU)-[:ES_DE_GAMA]->(:GamaGPU)
                                       (reglas_ev)  ◄────┘                      ├──[:POSEE]──► (:Pantalla)
                                                                                ├──[:POSEE]──► (:Bateria)
                                                               (reglas_mov) ◄───┤
```

#### Nodo `(:Notebook)`
* `modelo`: String único y canónico (`'Notebook_A'`, `'Notebook_B'`, ..., `'Notebook_X'`).
* `precio_usd`: Float (`650.0` a `1200.0`).
* `peso_kg`: Float ($1.3$ a $2.3$ kg).
* `adecuacion_movilidad`: Float en $[0.0, 1.0]$ defuzificado por centroide (o `null` si no hay batería).
* `movilidad_etiqueta`: String (`'alta'`, `'media'`, `'baja'`).

#### Nodo `(:GPU)` — Relación: `(n)-[:POSEE]->(g:GPU)`
* `gama`: String con el nombre de la gama (ej. `'integrada moderna'`, `'dedicada media'`).
* `dedicada`: Booleano (`true` si es dedicada, `false` si es integrada).
* `vram_gb`: Entero ($0$ en integradas, $8$ en dedicadas del catálogo).
* `tgp_w`: Entero en Watts o `null` (ej. $60$ en `Notebook_X`, $115$ en `Notebook_C`).
* `tgp_max_w`: Entero en Watts (límite máximo del chip, ej. $115$).
* `potencia_relativa`: Float en $[0.0, 1.0]$ ($\text{tgp\_w} / \text{tgp\_max\_w}$, ej. $0.522$ en `Notebook_X`, $1.0$ en `Notebook_C`).

#### Nodo `(:GamaGPU)` — Relación: `(g)-[:ES_DE_GAMA]->(gg:GamaGPU)`
* `indice`: Entero del 1 al 5:
  - `1`: Integrada básica
  - `2`: Integrada moderna (todas las integradas del catálogo)
  - `3`: Dedicada de entrada
  - `4`: Dedicada media (`Notebook_X` y `Notebook_C`)
  - `5`: Dedicada alta
* `nombre`: String idéntico a `g.gama`.

#### Nodo `(:Pantalla)` — Relación: `(n)-[:POSEE]->(p:Pantalla)`
* `resolucion`: String (`'FHD'`, `'QHD'`).
* `refresco_hz`: Entero ($60$ o $144$).
* `srgb`: Entero en porcentaje ($55$ a $98$).

#### Nodo `(:Bateria)` — Relación: `(n)-[:POSEE]->(b:Bateria)`
* `autonomia_medida_h`: Float o `null` (horas reales en pruebas de laboratorio).
* `autonomia_declarada_h`: Float o `null` (cifra comercial).
* `autonomia_usada_h`: Float (calculada por regla `GM-R12`: medida si existe, o $0.7 \times \text{declarada}$; `null` si ninguna).
* `tipo_dato`: String (`'medida'`, `'estimada'`, `'desconocida'`).
* `fuente`: String (`'Notebookcheck / RTINGS'` o `'ficha del fabricante'`).

#### Nodo `(:Evaluacion)` — Relación: `(ev:Evaluacion)-[:SOBRE]->(n:Notebook)`
* `perfil`: Código del perfil evaluado (`'VIRT'`, `'GAM'`, `'OFI'`, etc.).
* `grado_gpu`: Float en $[0.0, 1.0]$.
* `margen_gama`: String (`'superior'`, `'justa'`, `'inferior'`, `'excluye'`).
* `grado_pantalla`: Float en $[0.0, 1.0]$.
* `adecuacion_grafica`: Float en $[0.0, 1.0]$ ($0.6 \times \text{grado\_gpu} + 0.4 \times \text{grado\_pantalla}$).

#### Nodo `(:Alerta)`
* Relaciones: `(ev)-[:GENERA]->(al:Alerta)` para alertas relativas al perfil, o `(n)-[:GENERA]->(al)` para alertas absolutas.
* `submodulo_origen`: `'SM3'`.
* `regla_origen`: String identificador (`'GM-R8'`, `'GM-R11'`, `'GM-R12'`, `'GM-R15'`, `'GM-R17'`).
* `tipo`: String (`'Potencia grafica reducida'`, `'Autonomia insuficiente'`, `'Autonomia no informada'`, etc.).
* `mensaje`: Descripción detallada de la evidencia.

---

## 4. Motor de Inferencia: Lógica Difusa y Reglas de Conocimiento

### 4.1 Conjuntos Difusos (Bloque 4 del Cypher)
Funciones gaussianas $\mu(x) = \exp\left(-\frac{(x - c)^2}{2\sigma^2}\right)$ con hombros en los extremos:

| Variable Difusa | Etiqueta | Centro ($c$) | Ancho ($\sigma$) | Tipo | Comportamiento |
|---|---|:---:|:---:|:---:|---|
| **`peso_kg`** | `liviana` | 1.2 kg | 0.20 | Hombro izq. | $x \le 1.2 \Rightarrow \mu=1.0$. En 1.5 kg da $\mu=0.32$. |
| (Universo $[0.8, 4.0]$) | `intermedia` | 1.8 kg | 0.25 | Gaussiana | En 1.8 kg da $\mu=1.0$. |
| | `pesada` | 2.5 kg | 0.30 | Hombro der. | $x \ge 2.5 \Rightarrow \mu=1.0$. |
| **`autonomia_h`** | `baja` | 3.0 h | 1.00 | Hombro izq. | $x \le 3.0 \Rightarrow \mu=1.0$. |
| (Universo $[1, 24]$) | `media` | 6.5 h | 1.20 | Gaussiana | En 6.5 h da $\mu=1.0$. En 8.0 h da $\mu=0.46$. |
| | `alta` | 10.0 h | 1.50 | Hombro der. | $x \ge 10.0 \Rightarrow \mu=1.0$. En 8.0 h da $\mu=0.41$. |
| **`potencia_relativa`** | `restringida` | 0.35 | 0.10 | Hombro izq. | $x \le 0.35 \Rightarrow \mu=1.0$. |
| ($\text{TGP}/\text{TGP}_{\text{máx}}$) | `moderada` | 0.60 | 0.10 | Gaussiana | En 0.52 (Notebook_X) da $\mu=0.74$. |
| | `plena` | 0.80 | 0.10 | Hombro der. | $x \ge 0.80 \Rightarrow \mu=1.0$. En 1.0 da $\mu=1.0$. |
| **`adecuacion_movilidad`** | `baja`, `media`, `alta` | 0.05 / 0.50 / 0.95 | 0.12 | Gaussianas salida | Defuzificación por centroide sobre 101 puntos. |
| **`grado_gpu`** | `insuficiente`, `parcial`, `pleno` | 0.20 / 0.55 / 0.95 | 0.12 / 0.12 / 0.10 | Gaussianas salida | Defuzificación por centroide sobre 101 puntos. |

### 4.2 Reglas Difusas de Mamdani (Bloque 5 del Cypher)
* **`GM-RD1`:** `SI peso ES liviana AND autonomia ES alta ENTONCES movilidad ES alta` ($w_1 = \min(\mu_{\text{liv}}, \mu_{\text{alt}})$).
* **`GM-RD2`:** `SI (liviana AND media) OR (intermedia AND (media OR alta)) ENTONCES movilidad ES media`.
* **`GM-RD3` (No compensatoria):** `SI peso ES pesada OR autonomia ES baja ENTONCES movilidad ES baja` ($w_3 = \max(\mu_{\text{pes}}, \mu_{\text{baj}})$).
* **`GM-RD4`:** `SI (margen superior AND potencia moderada/plena) OR (margen justa AND potencia plena) ENTONCES gpu ES pleno`.
* **`GM-RD5`:** `SI (superior AND restringida) OR (justa AND moderada) OR (inferior AND plena) ENTONCES gpu ES parcial`.
* **`GM-RD6`:** `SI (justa AND restringida) OR (inferior AND restringida/moderada) ENTONCES gpu ES insuficiente`.

### 4.3 Reglas Crisp de Negocio y Políticas
* **`GM-R4`:** Brecha de gamas de GPU (gama $\ge$ requerida $\rightarrow 1.0$; 1 nivel inferior $\rightarrow 0.5$; 2 o más $\rightarrow 0.0$).
* **`GM-R8`:** Alerta si el TGP reduce el grado de GPU en más de 0.20 respecto a la sola gama.
* **`GM-R11`:** Alerta si prioridad es autonomía y $\mu_{\text{baja}}(\text{autonomía}) \ge 0.50$.
* **`GM-R12`:** Autonomía efectiva: si no hay medida, se aplica $0.7 \times \text{declarada}$ y se marca como estimada.
* **`GM-R14`:** Grado GPU = 0.0 marca requisito excluyente no cumplido (`[:INCUMPLE {excluyente: true}]`).
* **`GM-R15`:** GPU integrada y RAM en canal simple dispara alerta de ancho de banda reducido.
* **`GM-R16`:** Monitor externo fija grado de pantalla en 1.0 y reduce el peso de la movilidad al 50%.
* **`GM-R17`:** TGP desconocido genera intervalo $[\text{peor}, \text{mejor}]$ y alerta sin asumir potencia plena.

---

## 5. Catálogo de Prueba Real en Neo4j (Bloque 8 del Cypher)

> **Corrección (09/11/2026):** las adecuaciones de movilidad de esta tabla se recalcularon con GM-RD1..RD3 y los parámetros del grafo (Mamdani, centroide sobre 101 puntos). Los valores coinciden con `Contexto_PG1_PG2_Grupo_para_PG3.md` §9.3 y con los resultados de SM4 en Neo4j (A 0,625 · B 0,776 · C 0,231 · E 0,547 · G 0,239 · H 0,430 · K 0,537 · X 0,486). Los valores anteriores (A 0,655 · B 0,914 · E 0,655) no se reproducían.

| Modelo | Precio | Peso | GPU (`g.gama`, `g.dedicada`) | TGP / Máx | Pantalla | Batería (`autonomia_usada_h`, tipo) | Rol de Prueba en SM3 |
|---|:---:|:---:|:---:|:---:|:---:|:---:|---|
| **`Notebook_A`** | $950 | 1.4 kg | `'integrada moderna'` (Falso) | — | FHD 60Hz 65% | 8.0 h (medida) | Movilidad media (0.625). |
| **`Notebook_B`** | $700 | 1.3 kg | `'integrada moderna'` (Falso) | — | FHD 60Hz 62% | 10.0 h (medida) | **Campeona de Movilidad:** Adecuación 0.776, alta (`GM-RD1` fuerza 0.88). |
| **`Notebook_C`** | $1200 | 2.3 kg | `'dedicada media'` (Verdadero) | **115 / 115 W** | QHD 144Hz 98% | 5.0 h (medida) | **Máxima Gráfica:** TGP pleno ($\text{potencia}=1.0$, grado GPU 0.916), pero pesada y movilidad baja (0.231). |
| **`Notebook_E`** | $980 | 1.5 kg | `'integrada moderna'` (Falso) | — | FHD 60Hz 70% | 7.0 h (medida) | Movilidad media (0.547), pero SM2 la descarta por CPU sin virtualización. |
| **`Notebook_G`** | $650 | 1.9 kg | `'integrada moderna'` (Falso) | — | FHD 60Hz 55% | **3.99 h (estimada)** | **Regla GM-R12:** 5.7 h declaradas castigadas al 70%. Pantalla básica (55% sRGB). |
| **`Notebook_H`** | $1000 | 2.0 kg | `'integrada moderna'` (Falso) | — | FHD 60Hz 58% | 6.0 h (medida) | Movilidad media (0.430) y peso de 2.0 kg. |
| **`Notebook_K`** | $900 | 1.6 kg | `'integrada moderna'` (Falso) | — | FHD 60Hz 60% | 7.5 h (medida) | Canal simple de RAM (dato `canal` cargado; la alerta `GM-R15` **no está implementada**, ver D-04). |
| **`Notebook_M`** | $880 | 1.5 kg | `'integrada moderna'` (Falso) | — | FHD 60Hz 66% | **null (desconocida)** | **Incertidumbre:** Batería `null`, movilidad `null`, alerta `GM-R12`. |
| **`Notebook_X`** | $1050 | 1.8 kg | `'dedicada media'` (Verdadero) | **60 / 115 W** | FHD 144Hz 95% | 7.0 h (medida) | **TGP Recortado:** Potencia relativa 0.522, grado GPU 0.55 y alerta `GM-R8`. Pantalla apta diseño. |

---

## 6. Consultas Cypher Canónicas Validadas en `sm3_asistente.py`

Las consultas implementadas por SM3 en PI4 están optimizadas por etapas (evitan productos cartesianos de reglas y alertas) y reflejan la separación entre `Notebook` y `Evaluacion`:

### 6.1 Consulta Unificada Canónica
```cypher
MATCH (n:Notebook)-[:POSEE]->(g:GPU)-[:ES_DE_GAMA]->(gg:GamaGPU)
MATCH (n)-[:POSEE]->(p:Pantalla)
MATCH (n)-[:POSEE]->(b:Bateria)
WHERE ($dedicada    IS NULL OR g.dedicada = $dedicada)
  AND ($gama_min    IS NULL OR gg.indice >= $gama_min)
  AND ($peso_max    IS NULL OR n.peso_kg <= $peso_max)
  AND ($bateria_min IS NULL OR (b.autonomia_usada_h IS NOT NULL AND b.autonomia_usada_h >= $bateria_min))
  AND ($srgb_min    IS NULL OR p.srgb >= $srgb_min)

// (1) Movilidad: reglas GM-RD1..RD3 activadas desde la notebook (absolutas)
OPTIONAL MATCH (n)-[am:ACTIVA]->(rm:Regla {submodulo: 'SM3'})
WITH n, g, gg, p, b,
     collect(CASE WHEN rm IS NULL THEN null ELSE
       {regla: rm.id, antecedente: rm.antecedente, consecuente: rm.consecuente,
        fuerza: am.fuerza, validacion: rm.estado_validacion} END) AS reglas_movilidad

// (2) Gráfica: evaluaciones por requerimiento x notebook
OPTIONAL MATCH (c:Requerimiento)-[:EVALUA]->(ev:Evaluacion)-[:SOBRE]->(n)
OPTIONAL MATCH (c)-[:TIENE_PERFIL_DOMINANTE]->(pf:Perfil)
OPTIONAL MATCH (ev)-[ag:ACTIVA]->(rg:Regla {submodulo: 'SM3'})
WITH n, g, gg, p, b, reglas_movilidad, c, ev, pf,
     collect(CASE WHEN rg IS NULL THEN null ELSE
       {regla: rg.id, fuerza: ag.fuerza,
        texto: coalesce(rg.enunciado, rg.antecedente + ' -> ' + rg.consecuente),
        validacion: rg.estado_validacion} END) AS reglas_ev
OPTIONAL MATCH (ev)-[:GENERA]->(al:Alerta {submodulo_origen: 'SM3'})
WITH n, g, gg, p, b, reglas_movilidad, c, ev, pf, reglas_ev,
     collect(CASE WHEN al IS NULL THEN null ELSE
       {tipo: al.tipo, regla: al.regla_origen, mensaje: al.mensaje} END) AS alertas_ev
WITH n, g, gg, p, b, reglas_movilidad,
     collect(CASE WHEN ev IS NULL THEN null ELSE
       {requerimiento: c.id, perfil: ev.perfil, perfil_gama_gpu_min: pf.gama_gpu_min,
        grado_gpu: ev.grado_gpu, margen_gama: ev.margen_gama,
        grado_pantalla: ev.grado_pantalla, adecuacion_grafica: ev.adecuacion_grafica,
        reglas: reglas_ev, alertas: alertas_ev} END) AS evaluaciones

RETURN n.modelo AS modelo, n.precio_usd AS precio, n.peso_kg AS peso,
       g.dedicada AS gpu_dedicada, gg.nombre AS gpu_gama, gg.indice AS gpu_gama_indice,
       g.vram_gb AS vram_gb, g.tgp_w AS tgp_watts, g.tgp_max_w AS tgp_max_watts,
       g.potencia_relativa AS potencia_relativa,
       p.resolucion AS resolucion, p.refresco_hz AS refresco_hz, p.srgb AS srgb,
       b.autonomia_usada_h AS bateria_horas, b.tipo_dato AS fiabilidad_bateria,
       b.fuente AS fuente_bateria,
       n.adecuacion_movilidad AS adecuacion_movilidad,
       n.movilidad_etiqueta AS movilidad_etiqueta,
       reglas_movilidad, evaluaciones
ORDER BY __ORDEN__
LIMIT $limite;
```

### 6.2 Lista Blanca de Ordenamientos (Python)
Para no ordenar por datos relativos al requerimiento (Decisión D14):
* `"grafica"`: `gpu_gama_indice DESC, coalesce(potencia_relativa, 0) DESC, srgb DESC, precio ASC`
* `"movilidad"`: `coalesce(adecuacion_movilidad, -1) DESC, peso ASC`
* `"mixta"`: `gpu_gama_indice DESC, coalesce(adecuacion_movilidad, -1) DESC`

---

## 7. Pipeline de Orquestación y Prompts (PI4)

### 7.1 Esquema Pydantic del Extractor (`Extraccion`)
```python
class Extraccion(BaseModel):
    intencion: Literal["grafica", "movilidad", "mixta", "modelo", "fuera_de_alcance"]
    modelo_especifico: str | None = None
    tipo_gpu: Literal["dedicada", "integrada"] | None = None
    gama_min: int | None = Field(default=None, ge=1, le=5)
    peso_max_kg: float | None = None
    bateria_min_horas: float | None = None
    pantalla_exigente: bool = False
    consulta_incompleta_o_absurda: bool = False
    motivo_absurdo: str | None = None
```

### 7.2 Guardrails Deterministas en Python
1. `intencion == "fuera_de_alcance"`: Derivación automática a SM2 (sin consultar Neo4j).
2. `peso_max_kg` fuera de $[0.5, 5.0]$ kg $\rightarrow$ Error de plausibilidad física.
3. `bateria_min_horas` fuera de $(0, 30]$ h $\rightarrow$ Error de plausibilidad física.
4. `gama_min` fuera de $\{1, 2, 3, 4, 5\} \rightarrow$ Error de parámetro.
5. `consulta_incompleta_o_absurda == True`: Respuesta guiada sin golpear la base.

### 7.3 System Prompts
* **Extracción (`prompts/extraccion.txt`):** Parser semántico puro (temperature 0). Heurísticas: gamer $\rightarrow$ dedicada gama $\ge 4$; liviana $\rightarrow$ peso $\le 1.5$ kg; buena batería $\rightarrow$ batería $\ge 8.0$ h; diseño $\rightarrow$ sRGB $\ge 95\%$.
* **Explicación (`prompts/explicacion.txt`):** Asesor técnico empático (temperature 0.3). Prohibición estricta de inventar datos; justificación obligatoria con peso, horas efectivas, TGP en Watts, reglas `GM-RDx` y alertas preventivas.

---

## 8. Banco de Casos de Prueba Validados (11 Casos)

1. *"Quiero una notebook gamer para jugar juegos pesados"* $\rightarrow$ Recupera `Notebook_C` (potencia 1.0) y `Notebook_X` (potencia 0.52).
2. *"Necesito algo liviano, menos de 1.5 kg, con 10 horas de batería"* $\rightarrow$ Recupera únicamente `Notebook_B` (1.3 kg, 10 h).
3. *"Gamer pero que pese menos de 2 kilos"* $\rightarrow$ Filtra `Notebook_C` (2.3 kg) y recupera `Notebook_X` (1.8 kg, dedicada, pero alerta por TGP de 60 W).
4. *"Soy diseñador gráfico, necesito buena pantalla"* $\rightarrow$ Filtra `Notebook_G` (55% sRGB) y recupera pantallas con sRGB $\ge 95\%$.
5. *"¿Qué tal la Notebook_X?"* $\rightarrow$ Recupera ficha completa de X, alerta `GM-R8` por TGP recortado y reglas difusas activadas.
6. *"Quiero una que pese 50 gramos y dure 200 horas"* $\rightarrow$ Bloqueo por guardrail en Python sin consultar la base.
7. *"¿Cuánta RAM tiene la mejor?"* $\rightarrow$ Derivación determinista a SM2 (Mauricio Miranda).
8. *"Recomendame una"* $\rightarrow$ Mensaje de clarificación solicitando criterios.
9. *"¿Cuánto dura la batería de la Notebook_M?"* $\rightarrow$ Muestra `bateria_horas = null`, tipo de dato `'desconocida'`, movilidad en rango $[0 ; 1]$ y alerta `GM-R12` sin inventar números.
10. *"¿Qué tal la Notebook_Z?"* $\rightarrow$ Modelo no existente en el catálogo; lista los 9 modelos disponibles.
11. *"¿Cuánto dura la batería de la Notebook_G?"* $\rightarrow$ Muestra 3.99 h estimadas (70% de 5.7 h declaradas según `GM-R12`) con advertencia de estimación.

---

## 9. Guía de Integración para el Grupo (PG3)

### 9.1 Componentes Exportables de `sm3_asistente.py`
Para el backend unificado de PG3, SM3 provee:
* `BaseConocimiento`: Clase que gestiona el driver oficial de Neo4j y expone `ejecutar(cypher, params)`.
* `cypher_unificada(orden)` y `CYPHER_MODELO`: Consultas canónicas ya probadas y optimizadas.
* `responder(pregunta: str) -> Traza`: Función pública que ejecuta el sándwich completo si el Prompt Maestro le transfiere el control.

### 9.2 Integración en Casos de Uso E2E Cruzados de PG3
* **Caso E2E 1 — Diseñador Gráfico / Modelador 3D (DIS / VID3D):**
  - **SM1:** Deduce el perfil. Según el grafo canónico (PG1/PG2 §8.6), DIS exige GPU gama $\ge 3$ y VID3D gama $\ge 4$. El sRGB $\ge 95\%$ de DIS figura solo en el `fundamento` del perfil, no como `Requisito`, y el filtro lo aplica `sm3_asistente.py` con `SRGB_DISENO = 95`.
  - **SM2:** DIS exige CPU media y VID3D CPU alta; los dos piden RAM 16/32 GB y SSD mínimo 1024 GB.
  - **Limitación del canónico:** solo hay `SALIDA_PI2` (rendimiento y pantalla) para VIRT, más K para OFI, así que un pedido DIS o VID3D **no evalúa ninguna notebook** hasta resolver D-03. Lo mismo vale para el E2E 2 (OFI), salvo K.
  - **SM3:** Evalúa `Notebook_C` (TGP 115 W, pantalla 98% sRGB, peso 2.3 kg) y `Notebook_X` (TGP 60 W, pantalla 95% sRGB, peso 1.8 kg, alerta `GM-R8`).
  - **SM4:** Contrasta con presupuesto y decide ranking.
* **Caso E2E 2 — Estudiante Universitario con Alta Movilidad (OFI):**
  - **SM1:** Deduce perfil `OFI`, prioridad `'autonomia'` y `'portabilidad'`.
  - **SM2:** Verifica RAM básica (8 o 16 GB).
  - **SM3:** Rankea primera a `Notebook_B` (1.3 kg, 10 h, adecuación 0.776) y alerta sobre `Notebook_G` por batería baja estimada y pantalla pobre.
  - **SM4:** Recomienda `Notebook_B` como la opción más costo-eficiente.
