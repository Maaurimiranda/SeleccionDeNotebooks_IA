# 12. Referencias y fuentes consultadas

Esta lista junta lo que figura en el repositorio y en los informes previos del grupo. No agregamos ninguna referencia que no hayamos usado.

## Material de la cátedra

- Cátedra de Inteligencia Artificial, UTN FRM (2026). *Actividad PG3 – Unidad 4 (Grupal): orquestación final, pruebas del prototipo y armado de carpeta* (consigna). Transcripta en `docs/consigna/ConsignaPG3.md`.
- Cátedra de Inteligencia Artificial, UTN FRM (2026). *Ejemplo_PG3_Evaluacion_CVs.docx*: ejemplo de entrega del Grupo 1 (evaluación de CV), usado como guía de forma.
- Cátedra de Inteligencia Artificial, UTN FRM (2026). *Mapa de la Materia: Entregas, Herramientas y Metodología (U0 a U4)*, y apuntes de la Unidad 4 (U1a, U1b y U1e). Base de `docs/RESTRICCIONES.md`.
- Entregas de la cátedra A0 a A11 y actividades PI1 a PI4 y PG0 a PG3 del Grupo 2, en particular A10 (prompt engineering) y A11 (Graph RAG con Ollama y Neo4j).

## Trabajos previos del grupo

- Grupo 2 (2026). *PG1*: cuaderno de conocimiento, red semántica y macro-proceso (`Grupo_2_PG1_U1.docx`, no incluido en este repositorio).
- Grupo 2 (2026). *PG2*: informe y script `Grupo_2_PG2_U1.cypher`. La versión canónica corregida es `docs/cypher/Grupo_2_PG2_U1_corregido.cypher` (decisión D-01).
- Entregas PI4 de cada submódulo, en `docs/fuentes/`: `Olea_Facundo_PI4_U4.ipynb` (SM1), `Miranda_Mauricio_PI4_U4.py` (SM2), `sm3_asistente.py` y sus prompts (SM3) y `Luconi_Martina_PI4_U4.py` (SM4).
- Contextos para PG3 en `docs/contexto/`: `Contexto_PG1_PG2_Grupo_para_PG3.md` y `Contexto_SM1_Olea_para_PG3.md`, `Contexto_SM2_Miranda_para_PG3.md`, `Contexto_SM3_deConinck_para_PG3.md` y `Contexto_SM4_Luconi_para_PG3.md`.
- Documentos de PG3 del repositorio: `docs/ARQUITECTURA.md`, `docs/RESTRICCIONES.md`, `docs/INCONSISTENCIAS_CONTEXTOS.md` (decisiones D-01 a D-13), `docs/plan/PLAN_PG3.md`, `docs/CORRECCIONES.md` y las notas de `docs/sesiones/`.
- Corridas citadas en este informe, en `docs/pruebas/`: `resultados_e2e.md`, `E2E-n.md` (E2E-1, 2, 3, 5, 8, 9 y 10), `casos_de_uso.md`, `funcionales.md` y `conteos_grafo.md`.

## Fuentes de conocimiento del dominio

Son las que el grupo registró en el cuaderno de conocimiento de PG1 para construir los perfiles, los requisitos, los parámetros y el catálogo. Las URL y las fechas de consulta de cada una figuran en los informes de PG1 y PG2, que no están en este repositorio.

- Apuntes y guía de la cátedra.
- Requisitos oficiales de software: Docker, Adobe, DaVinci, PyTorch y Steam.
- Fichas de fabricantes: Intel ARK, AMD, NVIDIA y Lenovo PSREF.
- Notebookcheck y RTINGS (autonomía y mediciones).
- Entrevista a un técnico (mínimos por perfil, margen de empate y tratamiento de datos faltantes). La validación de los parámetros con el técnico sigue pendiente (sección 9.2).
- Casos publicados (r/SuggestALaptop).
- Mercado Libre y tiendas oficiales (precios al 01/10/2026) y cotización del Banco Nación.

## Bibliografía técnica

- Zadeh, L. A. (1965). Fuzzy sets. *Information and Control*, 8(3).
- Mamdani, E. H. y Assilian, S. (1975). An experiment in linguistic synthesis with a fuzzy logic controller. *International Journal of Man-Machine Studies*, 7(1).
- Lewis, P. et al. (2020). Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks. *Advances in Neural Information Processing Systems (NeurIPS)*, 33.
- Neo4j, Inc. *Cypher Manual* y *Neo4j Python Driver Manual*. https://neo4j.com/docs
- Ollama. Documentación de la API y de las salidas estructuradas. https://ollama.com

## Software utilizado

Python 3.14 y su biblioteca estándar (`unittest`, `json`, `csv`); Neo4j 5.26 y su driver de Python (`neo4j`); Ollama con el modelo `qwen2.5:3b`; LangChain (`langchain-core` y `langchain-ollama`); FastAPI, Uvicorn y Pydantic; `requests` y `httpx`. Las versiones mínimas están en `requirements.txt`. Todo está dentro de las listas verde y amarilla de `docs/RESTRICCIONES.md`, salvo la excepción registrada en su sección 8 (`langchain-ollama`).

Para armar este informe se usaron además `matplotlib` (las dos figuras), `mistune` y PyMuPDF (el PDF), que no son parte del sistema y no están en `requirements.txt`. Se usan en `docs/informe/figuras.py` y `docs/informe/armar_pdf.py`.
