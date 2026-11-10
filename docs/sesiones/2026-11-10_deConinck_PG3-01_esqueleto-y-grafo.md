# Esqueleto ejecutable y grafo dividido · de Coninck · 2026-11-10 · PG3-00, PG3-01 y PG3-02

## En tres líneas
El asistente ya corre de punta a punta: la API y la consola reciben una consulta, el router (LLM) arma un plan, los submódulos consultan Neo4j y una plantilla mínima responde, dejando una traza por consulta. El grafo canónico quedó dividido en un archivo por dueño, con el script de carga y la regresión CP1–CP11 (11 de 11 OK). Falta el explicador real (PG3-13) y SM4 (PG3-12), que hoy son stubs.

## Qué cambió
| Archivo | Qué tiene ahora |
| --- | --- |
| [asistente/config.py](../../asistente/config.py) | Variables de entorno de ARQUITECTURA §4.6 (`os.getenv`, sin dotenv) |
| [asistente/contrato.py](../../asistente/contrato.py) | 13 intenciones con sus parámetros, `ESQUEMA_PLAN`, excepciones, literales D-06 y textos fijos |
| [asistente/grafo.py](../../asistente/grafo.py) | `Grafo.leer` en `READ_ACCESS` (no puede escribir), `catalogo`, `pedidos`, `salud` |
| [asistente/llm.py](../../asistente/llm.py) | `LLM.json` y `LLM.texto` con LangChain (`ChatPromptTemplate` y `ChatOllama`, temperatura 0, `with_structured_output`); `salud` con `requests` |
| [asistente/orquestador.py](../../asistente/orquestador.py) | Flujo completo y despacho con un mapa de `RunnableLambda` por submódulo |
| [asistente/traza.py](../../asistente/traza.py) | Una línea JSONL por consulta en `trazas/AAAA-MM-DD.jsonl` |
| [asistente/api.py](../../asistente/api.py), [asistente/cli.py](../../asistente/cli.py) | `POST /consultar`, `GET /salud` con modelos Pydantic y `/docs`; consola con `/pedido` y `--traza` |
| [asistente/explicador.py](../../asistente/explicador.py) | STUB: plantilla mínima que solo lista la evidencia (PG3-13 lo reemplaza) |
| [asistente/submodulos/](../../asistente/submodulos/) | Cinco paquetes con `entrada`, `servicio`, `repositorio` y `esquemas`; `sm4/` es stub |
| [cypher/](../../cypher/) | `00_…90_*.cypher`: el canónico cortado por dueño, con un encabezado en cada archivo |
| [scripts/cargar_grafo.py](../../scripts/cargar_grafo.py), [verificar_grafo.py](../../scripts/verificar_grafo.py), [generar_fixtures.py](../../scripts/generar_fixtures.py) | Carga, regresión CP1–CP11 y regeneración de fixtures con filas reales |
| `requirements.txt`, `.env.example`, `.gitignore` | Dependencias permitidas y configuración |
| [tests/](../../tests/) | 78 tests con `unittest` |

## Cómo funciona (para alguien que no estuvo)
Se toma como ejemplo la consulta «¿Por qué la G quedó indeterminada y qué riesgo de RAM tiene en req_01?».

1. **Prevalidar** ([orquestador.py](../../asistente/orquestador.py)): rechaza la consulta si está vacía, si no tiene letras o si supera los 1500 caracteres. No la recorta.
2. **Planificar** ([router.py](../../asistente/router.py)): el LLM recibe el prompt maestro y devuelve un JSON forzado por el esquema: `SM4.explicar_notebook` con `Notebook_G` y `SM2.riesgo_ram` con `["Notebook_G"]`, sobre `req_01`.
3. **Validar** (Python): controla que las intenciones sean de la lista, que el modelo exista en el catálogo y que el pedido lo haya escrito el usuario o venga de la sesión.
4. **Despachar** con LangChain: `despachos["SM2"]` es un `RunnableLambda` que llama a `sm2.ejecutar(...)`. Antes se agrega siempre la consulta L1 de SM1 (qué pidió el comprador). El LLM eligió la intención; el Cypher lo elige el submódulo.
5. **Evidencia común:** `{"pedido": ..., "SM2": {"riesgo_ram": ...}, "SM4": {...}, "advertencia": ...}`.
6. **Explicar:** hoy, la plantilla mínima. Después, el explicador de PG3-13.
7. **Traza:** se registran el plan, las observaciones de la validación, cada consulta con su Cypher, sus parámetros y sus filas, el submódulo y los milisegundos, y la respuesta.

Si algo falla, el usuario recibe un mensaje fijo y la causa queda en la traza, sin *traceback*. Los casos son `validacion` (falta un dato), `fuera_de_alcance` (no es del dominio) y `error` (Neo4j u Ollama caídos).

## Decisiones y por qué
- **Neo4j local para probar:** en esta máquina se usó Neo4j 5.26 Community (tarball, fuera del repo). Cada uno sigue con su Neo4j Desktop o AuraDB, como dice PG3-00.
- **`cypher/90_verificacion.cypher` no se carga:** C1 hace `MERGE` de `INCUMPLE` (escribe) y ninguna otra parte lo necesita. Los CP los corre `verificar_grafo.py` en modo lectura.
- **Esperado de CP11:** para `req_01`, K queda `Descartada` a secas (así lo dice PG1/PG2 §9.4), no por excluyente. El primer esperado que escribí estaba mal; el grafo estaba bien.
- **Arreglos de D-06 en el `.cypher`:** las 3 sentencias con `'provisional'` pasan a `'sin validar'` en `01_conocimiento`, y REC-R5 suma la prioridad `grafica` en `40_sm4`. **Luconi:** revisá ese cambio en tu archivo (una línea en «Pesos del perfil»). CP1–CP11 siguen igual.
- **`CALL { WITH ... }` y no `CALL (x) { }`:** la segunda forma exige Neo4j ≥ 5.23, y alguien puede tener una versión anterior.
- **Prompts como plantilla:** `LLM.json(..., variables=...)` trata el prompt como plantilla de `ChatPromptTemplate`. En `maestro.txt` las llaves literales del JSON se escriben `{{ }}`.
- **Tiempos cortos del driver:** con Neo4j apagado, el error llega en unos 2 s y no después de ~30 s de reintentos.
- **La API no recuerda la sesión:** cada pedido HTTP manda su `requerimiento_id`. La consola sí recuerda el pedido.
- **Una ayuda común** ([submodulos/comun.py](../../asistente/submodulos/comun.py)): `leer_consulta`, `redondear` y `rango`, para que los cinco paquetes armen la traza y los rangos igual.

## Cómo probarlo
```bash
python -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env   # completar NEO4J_PASSWORD
set -a; source .env; set +a
python -m scripts.cargar_grafo          # 101 sentencias
python -m scripts.verificar_grafo       # 11/11 OK
python -m unittest                      # 78 tests, 1 salteado (router con LLM)
python -m asistente.cli --traza "¿Qué parámetros del sistema están sin validar?"
uvicorn asistente.api:app               # y abrir http://localhost:8000/docs
```
Sin `NEO4J_PASSWORD`, las pruebas `ConGrafo` se saltean y las offline pasan igual.

## Qué queda y dudas
- El explicador (PG3-13) y SM4 (PG3-12) son stubs: la respuesta hoy es una lista de datos, no un texto redactado.
- Los fixtures de SM4 tienen solo la forma. Luconi los regenera cuando implemente las consultas.
- Con `qwen2.5:3b` en esta máquina, el plan tarda entre 10 y 50 s. Conviene medirlo en las otras notebooks.
- Falta registrar en `docs/CORRECCIONES.md` (PG3-15) los dos arreglos de D-06 y la corrección del esperado de CP11.
