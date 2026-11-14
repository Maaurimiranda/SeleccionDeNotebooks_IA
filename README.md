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

### Acordados por el grupo (propuestos desde SM2 en PI4)

3. **El LLM interpreta y explica en dos llamadas.** Una extrae la intención en JSON y otra redacta la respuesta a partir de una *evidencia* ya recuperada.
4. **El LLM no escribe Cypher.** Las consultas son plantillas fijas y parametrizadas, y la conexión es de **solo lectura** (`READ_ACCESS`).
5. **Todo se verifica en código.** Cada cifra, notebook y regla citada tiene que estar en la evidencia; si no, se regenera y, como último recurso, se usa una plantilla fija.
6. **La incertidumbre se conserva.** Un dato desconocido sigue siendo «desconocido» (no se convierte en «no ampliable»); un riesgo con rango se informa como rango; un pedido sin perfil definido no se «completa».
7. **Honestidad sobre la validación.** Si los parámetros de un modelo difuso no están validados por un técnico, cada respuesta que dependa de ellos lo dice.

## 3. Arquitectura

Definida en [`docs/ARQUITECTURA.md`](docs/ARQUITECTURA.md): componentes (§2), flujo de una consulta (§3), contrato de los submódulos (§4), grafo dividido por dueño (§5) y traza (§8). Las decisiones del grupo están en [`docs/INCONSISTENCIAS_CONTEXTOS.md`](docs/INCONSISTENCIAS_CONTEXTOS.md) (D-01 a D-13) y el plan de trabajo hasta la entrega (13/11/2026) en [`docs/plan/PLAN_PG3.md`](docs/plan/PLAN_PG3.md).

El camino de una consulta:

1. **Interfaz** (`asistente/api.py`, `asistente/cli.py`): la entrada única. Valida el texto y lo pasa al orquestador.
2. **Router** (`asistente/router.py`, `prompts/maestro.txt`): el LLM traduce el texto a un plan JSON de intenciones cerradas y Python lo valida. Nunca se asume un pedido ni se acepta un modelo que no está en el catálogo.
3. **Submódulos** (`asistente/submodulos/`): SM1 a SM4 y GRUPO. Cada uno expone solo `ejecutar(intencion, parametros, grafo)` y corre Cypher fijo, de solo lectura, sobre Neo4j.
4. **Explicador** (`asistente/explicador.py`, `prompts/explicacion.txt`): el LLM redacta usando únicamente la evidencia que devolvió el grafo. Un verificador controla cifras, notebooks, reglas, alertas y estados y, si la redacción no pasa tras los reintentos, se responde con una plantilla fija.
5. **Traza** (`asistente/traza.py`): un registro por consulta.

El orquestador (`asistente/orquestador.py`) coordina los pasos 2 a 5. Si la consulta describe un pedido nuevo, antes del paso 3 el extractor (`asistente/extractor.py`, `prompts/extraccion.txt`) saca sus datos y SM1 lo registra. Los diagramas de arquitectura, secuencia y grafo están en [`docs/diagramas/`](docs/diagramas/) (PNG y Draw.io editable).

## 4. Estructura del repositorio

La estructura completa y quién es dueño de cada archivo están en [`docs/ARQUITECTURA.md`](docs/ARQUITECTURA.md) §6. Hoy:

```
SeleccionDeNotebooks_IA/
├── README.md
├── requirements.txt  .env.example  # dependencias y plantilla de configuración (ítems e y g)
├── asistente/                      # código fuente (ítem e)
│   ├── api.py  cli.py  web/        # interfaz única: POST /consultar, GET /salud, web en /ui y consola
│   ├── orquestador.py  router.py  extractor.py  explicador.py  traza.py
│   ├── contrato.py  config.py  grafo.py  llm.py
│   └── submodulos/                 # sm1, sm2, sm3, sm4 y grupo: entrada → servicio → repositorio (+ esquemas)
├── prompts/                        # maestro.txt (router), extraccion.txt (pedido nuevo) y explicacion.txt
├── cypher/                         # el grafo en scripts por dueño, 00_ a 90_ (ítem f)
├── datos/                          # exportación de Neo4j y datos de ejemplo (ítems i y j)
├── scripts/                        # cargar_grafo, verificar_grafo, correr_e2e, exportar_grafo, limpiar_pedidos…
├── tests/                          # unittest; fixtures/ con filas reales del grafo
└── docs/
    ├── MANUAL_DE_USO.md            # manual de uso (ítem d)
    ├── ARQUITECTURA.md             # arquitectura y contrato de PG3
    ├── RESTRICCIONES.md            # qué técnicas y tecnologías se pueden usar
    ├── INCONSISTENCIAS_CONTEXTOS.md # inconsistencias entre contextos y decisiones (D-01 a D-13)
    ├── CORRECCIONES.md             # registro de correcciones (consigna §3.1)
    ├── diagramas/                  # arquitectura, secuencia y grafo, en PNG y Draw.io (ítem b)
    ├── pruebas/                    # casos de uso, E2E, funcionales y validación del técnico (ítem c)
    ├── consigna/                   # ConsignaPG3.md: consigna de la cátedra
    ├── contexto/                   # contexto para PG3: PG1/PG2 grupal y SM1–SM4
    ├── cypher/                     # scripts de PG2; canónico: Grupo_2_PG2_U1_corregido.cypher (D-01)
    └── fuentes/                    # PI4 de cada submódulo (SM1–SM4): código y prompts
```

Solo en el repositorio, no en el ZIP: `CLAUDE.md`, `docs/plan/` (tareas), `docs/sesiones/` (notas de trabajo) y `docs/informe/` (fuentes del PDF). La carpeta `trazas/` se crea sola al consultar y no se versiona.

## 5. Requisitos

| Herramienta | Versión | Nota |
| --- | --- | --- |
| Python | 3.10 o posterior (probado con 3.14) | La consigna pide el código en Python con `requirements.txt` |
| Neo4j | 5.x (probado con 5.26) | Base de conocimiento de PG2. Las consultas de SM2 usan subconsultas `EXISTS { … }` y el driver 5 |
| LLM | Ollama local, `qwen2.5:3b` (`qwen2.5:7b` opcional por `OLLAMA_MODEL`) | Temperatura 0 en las dos llamadas; LangChain (`ChatOllama`) como cliente, sin agentes ni Cypher generado (D-05) |
| Memoria | ~4 GB libres para `qwen2.5:3b` (~8 GB con `7b`) | Más lo que use Neo4j |

Cómo instalar cada uno, paso a paso: [`docs/MANUAL_DE_USO.md`](docs/MANUAL_DE_USO.md) §1 y §2. Cómo ver los cambios que subió el grupo (`git pull`, recargar el grafo, reiniciar y Ctrl+F5): §4.1.1.

## 6. Puesta en marcha

Resumen para Windows (PowerShell), desde la carpeta raíz del proyecto. El detalle y los errores comunes están en [`docs/MANUAL_DE_USO.md`](docs/MANUAL_DE_USO.md).

**Una sola vez:**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
ollama pull qwen2.5:3b
Copy-Item .env.example .env        # y completar NEO4J_PASSWORD con la de tu base local
```

**Cada vez que lo levantás:**

1. **Neo4j:** abrir Neo4j Desktop e iniciar (*Start*) la base local 5.x. Tiene que responder en `bolt://localhost:7687`.
2. **Ollama:** si no está el ícono en la bandeja, correr `ollama serve` en una terminal aparte y dejarla abierta.
3. **Terminal del proyecto:** activar el entorno y cargar el `.env`. El código **no lee el `.env` solo** (sin `python-dotenv`, D-05), así que hay que repetirlo en cada ventana nueva:

   ```powershell
   .venv\Scripts\Activate.ps1
   Get-Content .env | Where-Object { $_ -match '^\s*[^#\s][^=]*=' } | ForEach-Object {
       $nombre, $valor = $_ -split '=', 2
       Set-Item -Path "Env:$($nombre.Trim())" -Value $valor.Trim()
   }
   ```

4. **Grafo** (la primera vez, o si cambió algo en `cypher/`):

   ```powershell
   python -m scripts.cargar_grafo      # BORRA la base y carga cypher/
   python -m scripts.verificar_grafo   # regresión CP1–CP11: tiene que dar 11/11 OK
   ```

5. **Asistente:** `uvicorn asistente.api:app` y abrir `http://localhost:8000/ui` (web) o `http://localhost:8000/docs` (Swagger). `GET /salud` tiene que decir que Neo4j y Ollama responden.

**Para probarlo, en este orden** (cada paso necesita el anterior):

| Paso | Comando | Qué tiene que dar |
| --- | --- | --- |
| Sin servicios | `python -m unittest` | `OK`, con pruebas salteadas (`s`) porque faltan Neo4j u Ollama. Al 14/11: 249 pruebas, 34 salteadas |
| Con Neo4j | `python -m scripts.verificar_grafo` y otra vez `python -m unittest` | 11/11 OK, y menos salteadas |
| Con Ollama | `$env:PG3_TEST_LLM = "1"; python -m unittest tests.test_router tests.test_e2e` | OK (lento, varios minutos) |
| Un caso a mano | `python -m asistente.cli --traza "Para req_01, ¿qué notebook me recomendás? ¿Cómo andan de RAM y de gráfica?"` | `Notebook_A` primera, después `Notebook_H` y `Notebook_B` (E2E-1) |
| En la web | En `/ui`, escribir «Quiero una notebook para programar y usar Docker, tengo 900 dólares» | Registra un `req_1NN` nuevo y muestra el ranking con la traza. `python -m scripts.limpiar_pedidos` borra esos pedidos |

Sin Neo4j ni Ollama, el botón «Ver ejemplo grabado» de `/ui` muestra una traza real guardada.

La configuración (`NEO4J_*`, `OLLAMA_*`, `MAX_CARACTERES`, `MAX_REGENERACIONES`, `DIR_TRAZAS`) está en `.env.example` y se describe en [`docs/ARQUITECTURA.md`](docs/ARQUITECTURA.md) §4.6. **El `.env` no se sube nunca: el repositorio es público.**

## 7. Uso

La consigna pide una **entrada única**: el sistema tiene dos formas de usarla, y las dos pasan por el mismo orquestador.

```powershell
python -m asistente.cli "Para req_01, ¿qué notebook me recomendás? ¿Cómo andan de RAM y de gráfica?"
uvicorn asistente.api:app
```

- **Consulta libre:** no hace falta nombrar un pedido. «Quiero una notebook para programar y usar Docker, tengo 900 dólares» pasa primero por Ollama, que extrae un JSON con usos, juegos y presupuesto; SM1 lo valida y lo guarda en Neo4j como `req_101`, y Neo4j corre las reglas solo para ese pedido. El LLM interpreta y explica; Neo4j decide. `python -m scripts.limpiar_pedidos` borra esos pedidos.
- **Consola** (`asistente/cli.py`): sin texto abre el modo conversación (`/pedido req_01` fija el pedido, `/nuevo` empieza otra conversación y `/salir` termina); `--traza` muestra la traza de cada respuesta.
- **API** (`asistente/api.py`): `POST /consultar` recibe `texto` y, opcionalmente, `requerimiento_id` y `sesion_id` (para seguir una conversación), y devuelve `respuesta`, `requerimiento_id`, `sesion_id`, `pedido_nuevo`, `repregunta`, `pedido`, `submodulos_consultados`, `origen_respuesta`, `intento` y `traza`. `GET /salud` informa si Neo4j y Ollama responden. La documentación interactiva (OpenAPI) está en `http://localhost:8000/docs`. No hay endpoints por submódulo.
- **Interfaz web** (`asistente/web/index.html`): en `http://localhost:8000/ui`, con la misma API levantada. Usa el mismo `POST /consultar` que Swagger y muestra la respuesta, el pedido interpretado, las recomendaciones con sus grados (los rangos se ven como tramo rayado), el riesgo de RAM y la traza paso a paso con cada Cypher y sus filas. El botón «Ver ejemplo grabado» muestra la traza de `datos/traza_ejemplo.jsonl` sin necesitar Neo4j ni Ollama.

Cómo se llama a la API desde PowerShell, cómo leer una respuesta (estados, rangos, advertencia y `origen_respuesta`) y qué hacer ante un error: [`docs/MANUAL_DE_USO.md`](docs/MANUAL_DE_USO.md) §4 a §8.

### Preguntas de ejemplo

Son los casos de las pruebas E2E (PG3-11). Lo que se controla es lo que dice el grafo, no la redacción del modelo.

| Pregunta | Submódulos | Qué tiene que decir el grafo |
| --- | --- | --- |
| «Para req_01, ¿qué notebook me recomendás? ¿Cómo andan de RAM y de gráfica?» (E2E-1) | SM1, SM2, SM3 y SM4 | `Notebook_A` primera (grado 0,785), después `Notebook_H` y `Notebook_B`; `Notebook_X` aparte, fuera de presupuesto |
| «En req_01, ¿por qué la M quedó condicionada y la G indeterminada?» (E2E-2) | SM2, SM3 y SM4 | M: grado entre 0,504 y 0,826 por falta de la autonomía. G: riesgo de RAM entre 49,58 y 81,46, alertas REN-R10 y FZ-R7 |
| «En req_01, la E tiene casi el mismo puntaje que la B y la H, ¿por qué no la recomiendan?» (E2E-5) | SM2 y SM4 | E es `Descartada (excluyente incumplido)`: su CPU no soporta virtualización (REN-R1 y REC-R3) |
| «En req_01, ¿qué reglas se activaron para la A, de dónde sale cada dato y qué riesgo de RAM tiene?» (E2E-9) | GRUPO, SM2 y SM4 | Las 18 reglas de la A con su fuerza y su origen (14 con origen; el resto, «no registrada») y el riesgo de RAM del grafo |
| «Para req_01, ¿cuáles son las mejores en movilidad y cómo queda el costo-beneficio?» (E2E-10) | SM3 y SM4 | Orden por movilidad; el dato faltante se informa como faltante; costo-beneficio del grafo |
| «¿Cuál es la capital de Francia?» (E2E-8, control) | Ninguno | `fuera_de_alcance`, mensaje fijo, sin consultas a los submódulos |
| «Quiero una notebook para programar y usar Docker, y a veces jugar al Fortnite. Tengo 900 dólares.» (E2E-6, pedido nuevo) | SM1, SM2, SM3 y SM4 | Se registra `req_101` con perfil dominante VIRT; `Notebook_B` primera y todas dentro de 900 USD |

## 8. Pruebas

Con `unittest` (no `pytest`, ver [`docs/RESTRICCIONES.md`](docs/RESTRICCIONES.md) §5):

```powershell
python -m unittest                  # sin Neo4j ni Ollama se saltean las pruebas que los necesitan
python -m scripts.verificar_grafo   # regresión CP1–CP11 contra el grafo cargado
$env:PG3_TEST_LLM = "1"; python -m unittest tests.test_router tests.test_explicador   # con Ollama (lento)
```

| Nivel | Qué prueba | Necesita |
| --- | --- | --- |
| Unitarias offline | `ejecutar()` de cada submódulo con un grafo falso que devuelve filas reales (`tests/fixtures/`), el `validar()` del router, el verificador y la plantilla fija | Nada |
| Grafo | Los 11 casos de PG1/PG2 §9 contra el grafo cargado | Neo4j |
| Funcionales (consigna §3.5) | Recuperación, consultas, reglas, difuso y respuesta, con esperado contra obtenido: clases `ConGrafo` de `tests/test_smX.py` | Neo4j |
| E2E (consigna §7) | E2E-1, 2, 5, 9 y 10 (casos integrales, cruzan submódulos) y E2E-3 y 8 (controles), con la traza en el formato de la cátedra | Neo4j + Ollama |

Los E2E los corre `scripts/correr_e2e.py`, que escribe un `docs/pruebas/E2E-n.md` por caso (PG3-11). [`docs/pruebas/`](docs/pruebas/) tiene los `E2E-n.md`, el resumen [`resultados_e2e.md`](docs/pruebas/resultados_e2e.md), las pruebas funcionales ([`funcionales.md`](docs/pruebas/funcionales.md)) y la comparación de conteos del grafo ([`conteos_grafo.md`](docs/pruebas/conteos_grafo.md)). El criterio de aprobado de un E2E es lo que dice el grafo (estados, grados, puestos y alertas), no el texto del modelo ([`docs/ARQUITECTURA.md`](docs/ARQUITECTURA.md) §7). Lo que pide la consigna: pruebas funcionales con esperado vs obtenido (sección 3.5) y al menos tres E2E que crucen submódulos (sección 7), ver [`docs/consigna/ConsignaPG3.md`](docs/consigna/ConsignaPG3.md).

## 9. Trazabilidad y auditoría

La consigna (sección 3.7) pide poder reconstruir, para una respuesta: **fuente** del conocimiento, **regla** utilizada, **evidencia** considerada, **consulta** ejecutada y **explicación** generada.

Cada consulta del usuario deja **un registro JSON** en `trazas/AAAA-MM-DD.jsonl` (carpeta `DIR_TRAZAS`, ignorada por Git). La API lo devuelve en el campo `traza` y la consola lo muestra con `--traza`. Tiene la pregunta, el plan del router y su validación, cada consulta Cypher con sus parámetros y las filas que devolvió Neo4j, la evidencia que recibió el explicador, cada intento de redacción con lo que detectó el verificador, la respuesta, su origen y la duración de cada paso. Con esa traza y el grafo se reconstruyen los cinco puntos:

| La consigna pide | Dónde está |
| --- | --- |
| **Regla** | `[:ACTIVA]` en el grafo, con su fuerza, y la intención `GRUPO.traza_reglas` |
| **Fuente** | El grafo canónico **no** guarda `fuente` en las `:Regla`: el origen está en `Parametro.origen` (los parámetros que respaldan cada regla difusa), `EtiquetaDifusa.fuente`, `Juego.fuente`, `Notebook.fuente_precio` y `Bateria.fuente`. `GRUPO` los expone y lo que falta sale como «no registrada», sin inventar nada. Es el origen de los parámetros, no el del texto de la regla |
| **Evidencia** | El campo `evidencia` de la traza: lo único que ve el explicador |
| **Consulta** | `consultas[]`: el Cypher, sus parámetros y las filas |
| **Explicación** | `intentos[]` y `respuesta` |

Cómo ver la traza, con los comandos: [`docs/MANUAL_DE_USO.md`](docs/MANUAL_DE_USO.md) §7. Detalle del diseño: [`docs/ARQUITECTURA.md`](docs/ARQUITECTURA.md) §8.

## 10. Entregable PG3 (`Grupo_2_PG3_ProyectoFinal.zip`)

El contenido mínimo del ZIP (ítems a–l) está en [`docs/consigna/ConsignaPG3.md`](docs/consigna/ConsignaPG3.md#4-formato-del-entregable). Dónde queda cada ítem en el repo:

| Ítem | Dónde |
| --- | --- |
| a) Informe ejecutivo (PDF) | ZIP: `1_Documentacion/Grupo_2_PG3_Informe_Final.pdf` |
| b) Diagramas | ZIP: `1_Documentacion/Diagramas/` · repo: `docs/diagramas/` |
| c) Casos de prueba | ZIP: `1_Documentacion/Casos_de_prueba/` · repo: `docs/pruebas/` |
| d) Manual de uso | ZIP: `1_Documentacion/Manual_de_uso.md` · repo: [`docs/MANUAL_DE_USO.md`](docs/MANUAL_DE_USO.md) |
| e) Código fuente | `asistente/`, `prompts/`, `scripts/` y `requirements.txt` (ZIP: `2_Implementacion/`) |
| f) Scripts Cypher | `cypher/` |
| g) Archivos de configuración | `.env.example` |
| h) Recursos complementarios | `prompts/`, `docs/contexto/` y `docs/fuentes/` |
| i) Exportación de Neo4j | ZIP: `3_Base_de_conocimiento/Exportacion_neo4j/` · repo: `datos/export/` |
| j) Datos de ejemplo | ZIP: `3_Base_de_conocimiento/Datos_de_ejemplo/` · repo: `datos/` |
| k) Presentación multimedia | ZIP: `4_Presentacion/Grupo_2_Defensa_Proyecto.pptx` |
| l) Resumen ejecutivo | ZIP: `4_Presentacion/resumen_ejecutivo.pdf` · repo: `docs/presentacion/` |

**Criterios de evaluación de PG3:** prompt maestro que enrute y respete que Neo4j maneja la verdad; API o interfaz única sin errores críticos; al menos tres pruebas E2E que crucen submódulos; informe coherente y profesional; ZIP que permita revisar y reproducir.

## 11. Estado del proyecto

Al 14/11/2026, entregado (`Grupo_2_PG3_ProyectoFinal.zip`):

- [x] Base de conocimiento en Neo4j (PG2), con las respuestas del técnico del 14/11 cargadas
- [x] SM1 a SM4 y GRUPO integrados bajo el contrato común
- [x] Prompt maestro con enrutamiento (router) y validación en Python
- [x] Entrada única: API, web en `/ui` y consola
- [x] Pedidos nuevos en lenguaje libre, con inferencia en vivo para cada uno
- [x] Explicador común con verificador y plantilla fija
- [x] Pruebas: 249 `unittest`, CP1 a CP11 y 7 E2E con esperado contra obtenido
- [x] Informe final, resumen ejecutivo, diagramas, manual, presentación, exportación de Neo4j y ZIP

## 12. Limitaciones conocidas

- **Validación con el técnico, parcial.** Confirmó 7 de las 15 variables difusas; sus 9 propuestas de cambio están registradas pero no aplicadas. El resto de los parámetros sigue `'sin validar'` y cada respuesta lo advierte.
- **Datos de rendimiento provisionales** para seis de los siete perfiles (todos menos virtualización), marcados `'sin validar'`.
- **El verificador controla cifras, notebooks, reglas, alertas y estados, pero no el sentido de la frase:** una cifra real puede salir con el nombre de otro concepto (E2E-2).
- **`qwen2.5:3b` es un modelo chico:** puede omitir una intención en una pregunta compuesta o perder un uso al extraer un pedido. Python completa y valida lo que puede, y la web ofrece un formulario para corregir el pedido.
- Catálogo de prueba de 9 notebooks, con precios al 01/10/2026.

## 13. Cómo trabajamos

- **Ramas:** `main` estable y una rama por tarea (`pg3-NN-descripcion`).
- **Commits:** mensajes en imperativo con tipo y área (`feat(sm2): ...`, `docs(README): ...`).
- **Pull requests:** revisión de al menos otro integrante antes de unir a `main`.
- **Responsables:** cada submódulo tiene un dueño (sección 1); los cambios en el grafo compartido y en el prompt maestro se acuerdan entre todos.
- **Registro de correcciones:** [`docs/CORRECCIONES.md`](docs/CORRECCIONES.md) (consigna §3.1).

## 14. Referencias

- Cátedra de Inteligencia Artificial, UTN FRM (2026). Unidad 4, apuntes U1a, U1b y U1e, y actividades PI1 a PI4 y PG0 a PG3.
- Neo4j, Inc. Cypher Manual y Neo4j Python Driver Manual. https://neo4j.com/docs
- Ollama. Documentación de la API y de salidas estructuradas. https://ollama.com
- Lewis, P. et al. (2020). *Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks*. NeurIPS 33.
- Zadeh, L. A. (1965). Fuzzy sets. *Information and Control*, 8(3). Mamdani, E. H. y Assilian, S. (1975). *International Journal of Man-Machine Studies*, 7(1).
- Fuentes de conocimiento del dominio (requisitos oficiales de software, fichas de fabricantes, Notebookcheck, RTINGS, precios al 01/10/2026 y el técnico): detalladas en los informes de PG1 y PG2 y en la sección 11 del informe final.

## 15. Licencia y uso

Trabajo académico de la Cátedra de Inteligencia Artificial (UTN FRM). Uso educativo. 
