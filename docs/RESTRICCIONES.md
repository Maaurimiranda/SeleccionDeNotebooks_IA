# Restricciones: qué podemos usar en el proyecto

> **Para qué sirve.** Es el arnés del proyecto: lista los conceptos y las tecnologías que vimos en la cátedra (Unidades 0 a 4) para que el asistente se construya **solo con lo aprendido**. Vale para personas y para agentes de IA que escriban código en este repo.
>
> **Fuente principal:** *Mapa de la Materia: Entregas, Herramientas y Metodología (U0 a U4)*. Complementan: [`docs/consigna/ConsignaPG3.md`](docs/consigna/ConsignaPG3.md) y los contextos de [`docs/contexto/`](docs/contexto/).

---

## 1. Regla de uso

1. Antes de agregar una librería, herramienta, técnica o servicio, buscarla en la [sección 4](#4-tecnologías-permitidas).
2. **Verde** → se usa sin más.
3. **Amarillo** → se usa solo en el rol indicado (lo avala la cátedra o ya lo usamos en el proyecto).
4. **Rojo o no listado** → **no se usa**. Si es imprescindible, se propone al grupo, se justifica con un contenido de la materia y se registra en la [sección 8](#8-excepciones-aprobadas) **antes** de escribir el código.
5. Ante la duda entre dos caminos, elegir el que se apoye en una entrega de la cátedra (A0 a A11).

**Para agentes de IA:** no instalar dependencias, no proponer frameworks ni técnicas fuera de la lista verde o amarilla. Si la tarea no se puede resolver con ellas, detenerse y avisar.

---

## 2. Contenidos de la materia por unidad

### Unidad 0 · Agentes y búsqueda

| Entrega | Qué se hizo | Conceptos |
| --- | --- | --- |
| **A0** | Agente recolector de residuos; simulador de pathfinding en grilla (3x3, 5x5) | Agente inteligente, **PEAS** (percepciones, acciones, estados, objetivos); problema como **espacio de estados** (estado inicial, función de transición, operadores, estado meta); **BFS, Dijkstra, A\***; heurísticas **Manhattan, Euclídea, Octile, Chebyshev**; admisibilidad, optimalidad, nodos expandidos; entornos dinámicos y no deterministas |
| **A1** | BFS, DFS y A\* en Python sobre grilla 10x10 con obstáculos | Bucle unificado **Sacar → Evaluar → Generar → Insertar**; la estructura de la frontera define el algoritmo: cola FIFO (`collections.deque`) para BFS, pila LIFO (`list`) para DFS, cola de prioridad (`heapq`) para A\*; benchmarking (nodos explorados, profundidad, costo, tiempo) |
| **A2** | CSP de asignación de casas a 4 familias en AIspace | **CSP**: variables, dominios finitos, restricciones unarias, binarias y `alldiff`; **consistencia de arco (AC-3/AC-4)**; **backtracking** con partición de dominios; enfoque procedural (búsqueda) vs. declarativo (CSP) |

**Idea central:** si importa la **secuencia de acciones**, es búsqueda con heurística; si importa una **configuración válida** que cumple muchas reglas a la vez, es CSP.

### Unidad 1 · Ingeniería del conocimiento, grafos y lógica difusa

| Entrega | Qué se hizo | Conceptos |
| --- | --- | --- |
| **A3** | Diagnóstico de fallas de PC desde manuales técnicos | Tarea experta (razonamiento abductivo-causal); **adquisición de conocimiento**; esquema por capas: **observación → estado interpretado → causa → acción**; flujo del sistema experto (entrada, interpretación, análisis, inferencia, comprobación) |
| **A4** | Ontología del dominio y caso de uso `PC_Cliente_01` | **Ontología** (tipos de nodo y relaciones como `IS_A`, `CAE_EN`, `SUGIERE`); **red semántica** conceptual e instanciada; **reglas de producción SI… ENTONCES**; **marcos (frames)**: slots, tipos, facetas de dominio, **demonios** (triggers) |
| **A5** | Base de conocimiento en Neo4j | Metamodelo de frames en grafo, jerarquías `IS_A`, nodos `:Demon`, simulación de disparo de demonios; Cypher: `CREATE`, `MERGE`, `MATCH camino = ...`, recorridos recursivos `[:IS_A*]`; validación de consistencia; trazabilidad de la inferencia; exportación a CSV |
| **A6** | Lógica difusa sobre el dominio | Variables lingüísticas (Bajo, Medio, Alto), universo de discurso; funciones de pertenencia **triangulares** y **gaussianas** (Xfuzzy también admite trapezoidales); **FIS** con base de reglas; t-norma **mínimo**; **entropía difusa**; análisis de sensibilidad; `INSTANCE_OF` en el grafo y consultas por umbral |

**Idea central:** primero la **ontología y el flujo de decisión**, después el código. Neo4j da la trazabilidad del razonamiento; Xfuzzy/Python calibran las reglas bajo incertidumbre.

### Unidad 2 · Redes neuronales y planificación de orden parcial

| Entrega | Qué se hizo | Conceptos |
| --- | --- | --- |
| **A7** | Clasificador de audio (5 clases) sin código + CNN sobre Fashion MNIST | **Aprendizaje supervisado**, etiquetado, espectrogramas; **CNN**: `Conv`, `MaxPooling`, `Dropout`, `Dense`; optimizador **Adam**; hiperparámetros (neuronas, épocas); **accuracy, loss, overfitting**; validación con muestras fuera de clase |
| **A8** | Planificador quirúrgico | **STRIPS/PDDL**: acciones con precondiciones, efectos aditivos (+) y supresivos (−); pasos `Start` y `Finish`; **POP**: plan como **DAG**, **enlaces causales**, precondiciones abiertas, **amenazas** resueltas por **promoción y degradación** con backtracking; **linealización** del plan |

**Idea central:** no-code para prototipar, código para medir. Un plan de orden parcial fija solo el orden imprescindible y debe quedar acíclico.

### Unidad 3 · PLN y minería de textos

| Entrega | Qué se hizo | Conceptos |
| --- | --- | --- |
| **A9** | Corpus de 30 opiniones sobre IA (5 tópicos, polaridad) | **Preprocesamiento**: minúsculas, tokenización (`word_tokenize`), filtro alfabético, **stopwords** en español; **coocurrencias** en ventana deslizante (k=2), colocaciones; **Bag of Words** (matriz documento-término, dispersión); **WordCloud**; **TF-IDF**; **stemming** (Snowball, español); **PCA**; **K-Means** (k=5); **Naive Bayes multinomial** con validación **Leave-One-Out** |

**Idea central:** el preprocesamiento define el espacio de datos. BoW pierde orden y negaciones; TF-IDF premia la especificidad. N-gramas y *embeddings* se mencionan como **siguiente paso, no se vieron**.

### Unidad 4 · LLMs y Graph RAG

| Entrega | Qué se hizo | Conceptos |
| --- | --- | --- |
| **A10** | Prompts para tareas creativa, especialista y de extracción/síntesis | **Prompt engineering** en tres niveles (básico, mejorado, «imbatible»): **rol/persona**, contexto, audiencia, **formato de salida cerrado**, **restricciones negativas**, prohibición de clichés, **ejemplos**, verificación y priorización; evaluación con **rúbrica** (claridad, extensión, fuentes, utilidad); limitaciones de los LLM (ignoran restricciones secundarias, priorizan exhaustividad, requieren supervisión humana) |
| **A11** | Q&A sobre un grafo forense (15 nodos, 19 relaciones) | **Graph RAG / Text-to-Cypher**; LLM local con **Ollama** (`qwen2.5:7b`, **temperatura 0**, sin costo de API); `GraphCypherQAChain` y `Neo4jGraph` de LangChain; batería de preguntas con **Cypher de referencia**; prompts del sistema en español adaptados a la ontología; **guardas de solo lectura** (validador propio); auditoría de pasos intermedios (`verbose=True`); resultados en CSV |

**Idea central:** el LLM no responde de memoria; traduce la pregunta, el grafo da los datos y el LLM redacta. Siempre con solo lectura y auditando la consulta generada.

---

## 3. Conceptos que el proyecto debe mostrar

La consigna de PG3 pide integrar: sistemas inteligentes, ingeniería del conocimiento, representación del conocimiento, sistemas basados en reglas, lógica difusa, grafos de conocimiento, PLN, modelos de lenguaje, asistentes inteligentes, explicabilidad y trazabilidad.

| Pieza del asistente | Contenido que la respalda |
| --- | --- |
| Prompt maestro y enrutamiento | A10 (rol, formato cerrado, restricciones negativas) |
| Extracción de la consulta a JSON | A10 (formato cerrado) + A11 (LLM local, temperatura 0) |
| Base de conocimiento | A4 (ontología, frames, reglas) + A5 (Neo4j, Cypher) |
| Reglas crisp | A4 (SI… ENTONCES), A5 (inferencia trazable en el grafo) |
| Lógica difusa | A6 (variables lingüísticas, gaussianas, t-norma mínimo); en PG2: **Mamdani** (AND = MIN, OR = MAX, agregación MAX, centroide) |
| Consulta al grafo | A5 (Cypher) + A11 (solo lectura, auditar la consulta) |
| Explicación | A11 (responder solo con lo que devuelve el grafo) |
| Trazabilidad | A3–A5 (observación → interpretación → causa) + A11 (registro de pasos intermedios) |
| Pruebas | A1 (benchmarking), A10 (rúbrica), A11 (preguntas con Cypher de referencia y CSV de resultados) |

---

## 4. Tecnologías permitidas

### Verde: vistas en la cátedra

| Tecnología | Rol permitido | Dónde se vio |
| --- | --- | --- |
| **Python 3** | Lenguaje principal del código | A0, A1, A5–A9, A11 |
| Biblioteca estándar de Python | `collections` (`deque`, `Counter`), `heapq`, `json`, `csv`, etc. | A1, A9 |
| **Google Colab / Jupyter** | Experimentos, prototipos y demos | A0, A1, A6, A7, A9, A11 |
| **Neo4j** (AuraDB o local) | Base de conocimiento: la verdad del sistema | A5, A6, A8, A11 |
| **Cypher** | Creación, consulta, recorridos jerárquicos y trazas | A5, A6, A11 |
| `neo4j` (driver de Python) | Conexión desde Python al grafo | A5 |
| **Ollama** | Servidor local de LLM, sin costo de API | A11 |
| Modelos abiertos en Ollama (`qwen2.5`) | Extracción y explicación, temperatura 0 | A11 |
| **LangChain** (`langchain-community`, `Neo4jGraph`, `GraphCypherQAChain`) | Orquestar LLM y Neo4j | A11 y ejemplo de PG3 de la cátedra |
| `scikit-fuzzy`, `numpy`, `matplotlib` | Modelado y gráficos de funciones de pertenencia | A6 |
| **Xfuzzy** (`.xfl`, XFL3) | Diseño y simulación del FIS | A6 |
| `pandas`, `numpy`, `matplotlib` | Datos tabulares y gráficos | A7, A9 |
| `nltk` | Tokenización y stopwords en español | A9 |
| `scikit-learn` | `CountVectorizer`, `MultinomialNB`, `LeaveOneOut` | A9 |
| `wordcloud` | Nubes de palabras | A9 |
| **R** con `tm`, `SnowballC`, `stats`, `ggplot2`, `ggrepel` | TF-IDF, stemming, PCA, K-Means y gráficos | A9 |
| **TensorFlow / Keras** | Redes neuronales (CNN) | A7 |
| Google Teachable Machine | Prototipo no-code de clasificación | A7 |
| **NetworkX** | Grafos dirigidos y verificación de aciclicidad | A8 |
| AIspace (Java/JRE) | CSP: consistencia de arco y backtracking | A2 |
| Neo4j LLM Graph Builder | Extracción asistida de grafos desde PDF | A3 |
| **Diagrams.net (Draw.io)** | Diagramas de flujo, redes semánticas y arquitectura | A3, A4 |
| Perplexity AI | Pruebas de prompts con fuentes citadas | A10 |
| CSV | Auditoría de nodos, relaciones y resultados de pruebas | A5, A11 |
| Procesador de texto y planillas | Informe, matrices de frames, rúbricas | Todas |

### Amarillo: avaladas por la cátedra o ya usadas en el proyecto

| Tecnología | Rol permitido | Por qué está permitida |
| --- | --- | --- |
| **FastAPI** + `uvicorn` | API única de entrada (`POST /consultar`) | El ejemplo de PG3 de la cátedra usa FastAPI; PG0 la propone; SM2 y SM4 la usaron en PI4 |
| `pydantic` | Modelos de entrada y salida de la API (`response_model`, documentación OpenAPI en `/docs`) | Viene con FastAPI |
| `langchain-core` + `langchain-ollama` (`ChatPromptTemplate`, `ChatOllama`) | **Cliente único del LLM** en `asistente/llm.py` (prompts con `ChatPromptTemplate`, temperatura 0, `with_structured_output` con esquema JSON) y **despacho a submódulos** con `RunnableLambda` en `asistente/orquestador.py`. Sin agentes ni *tool calling* | El ejemplo de PG3 de la cátedra extrae los datos con LangChain (`extraer_datos_llm`); A11 usa LangChain con Ollama; SM3 ya usó `ChatOllama` en PI4 (D-05, cambio del 10/11/2026) |
| `requests` | Solo el chequeo de salud de Ollama (`GET /api/tags`) | Usado por SM2 en PI4 |
| `httpx` | Solo para probar la API (cliente de pruebas de FastAPI) | Usado en los tests de SM2 |
| Salida estructurada de Ollama (`format` con esquema JSON) | Forzar JSON válido en la extracción | Usado por SM2 y SM4 en PI4; extiende el «formato cerrado» de A10 |
| Otros modelos abiertos en Ollama (`qwen2.5:3b`, `llama3.1:8b`) | Mismo rol que `qwen2.5:7b` | Usados en PI4 por limitaciones de hardware |
| `unittest` (biblioteca estándar) | Pruebas automáticas | Es parte de Python; no agrega dependencias |
| Consola (CLI) | Interfaz alternativa a la API | La consigna la admite como interfaz |

---

## 5. Lo que no se usa

Ninguna de estas cosas se vio en la cátedra. Usarlas exige pasar por la [sección 8](#8-excepciones-aprobadas).

| Categoría | Ejemplos | Alternativa dentro de lo visto |
| --- | --- | --- |
| LLM pagos en la nube | API de OpenAI, Anthropic, Gemini, Groq | Ollama local (A11) |
| Embeddings y bases vectoriales | Chroma, FAISS, Pinecone, índices vectoriales de Neo4j, `sentence-transformers` | Graph RAG sobre Cypher (A11); TF-IDF si hace falta texto (A9) |
| Frameworks de agentes | LangGraph, CrewAI, AutoGen, LlamaIndex, agentes con herramientas de LangChain (`AgentExecutor`, *tool calling*) | Prompt maestro + orquestación en Python plano con LangChain solo como cliente del LLM (A10, A11, ejemplo de PG3) |
| Ajuste fino de modelos | Fine-tuning, LoRA, Hugging Face `transformers`, PyTorch | Prompt engineering (A10) |
| PLN avanzado | spaCy, NER con modelos, transformers para sentimiento | `nltk`, BoW, TF-IDF (A9) o el propio LLM con prompt de extracción |
| Plugins de Neo4j no vistos | APOC, Graph Data Science (GDS) | Cypher estándar (A5) |
| Frontends web | React, Vue, Streamlit, Gradio | API FastAPI o consola |
| Infraestructura | Docker, Kubernetes, despliegue en la nube, colas de mensajes | Ejecución local con `requirements.txt` |
| Otras bases de datos | PostgreSQL, MongoDB, SQLite como fuente de verdad | Neo4j (la consigna lo exige) |
| Lógica difusa fuera de lo visto | Sugeno/TSK, neuro-fuzzy (ANFIS), funciones de pertenencia exóticas | Mamdani con gaussianas o triangulares (A6, PG2) |
| Frameworks de pruebas externos | `pytest`, `hypothesis` | `unittest` + casos esperado vs. obtenido |

---

## 6. Principios metodológicos (de la cátedra)

1. **Neo4j maneja la verdad.** Toda cifra, regla, estado o alerta sale del grafo. El LLM no calcula ni decide (consigna PG3, A11).
2. **El LLM es la interfaz.** Interpreta la consulta y redacta la explicación; el razonamiento vive en las reglas y en la lógica difusa (A11, ejemplo PG3).
3. **Ontología antes que código.** Definir tipos de nodo, relaciones y flujo de decisión antes de programar o cargar el grafo (resumen U1).
4. **Separar capas del conocimiento.** Dato observable ≠ estado interpretado ≠ causa/diagnóstico (A3).
5. **Solo lectura en las consultas del asistente.** Guardas que impidan que una consulta escriba en el grafo (A11).
6. **Temperatura 0** en el LLM para respuestas reproducibles (A11).
7. **Auditar los pasos intermedios.** Registrar la pregunta, el JSON extraído, el Cypher ejecutado, las filas devueltas y la explicación (A11, consigna 3.7).
8. **Responder solo con evidencia.** La explicación usa únicamente lo que devolvió Neo4j; no inventa datos (A11, anexo SM3 del mapa).
9. **Evaluar con criterios explícitos.** Casos con resultado esperado vs. obtenido, rúbricas y métricas (A1, A10, A11).
10. **Desconfiar del cumplimiento del LLM.** Los LLM omiten restricciones secundarias: lo que importa se verifica en código, no solo en el prompt (A10).

---

## 7. Checklist antes de agregar algo

- [ ] ¿Está en verde o amarillo, y lo uso en el rol indicado?
- [ ] ¿Puedo nombrar la entrega (A0–A11) o la parte de la consigna que lo respalda?
- [ ] ¿Respeta que Neo4j maneja la verdad y que el LLM solo interpreta y explica?
- [ ] ¿Se agrega a `requirements.txt` y corre en local sin servicios pagos?
- [ ] Si nada de lo anterior se cumple: ¿está registrado en la sección 8 con el acuerdo del grupo?

---

## 8. Excepciones aprobadas

Toda tecnología o técnica fuera de las listas verde y amarilla se registra acá antes de usarla.

| Fecha | Tecnología o técnica | Para qué | Justificación (contenido de la materia) | Aprobada por |
| --- | --- | --- | --- | --- |
| 10/11/2026 | `langchain-ollama` (paquete no listado; `langchain-community` sí) y paso de `requests` a LangChain como cliente del LLM | `ChatOllama` en `asistente/llm.py` | Ejemplo de PG3 de la cátedra (campus virtual), que usa LangChain para extraer; A11 (LangChain + Ollama) | Grupo (D-05) |
