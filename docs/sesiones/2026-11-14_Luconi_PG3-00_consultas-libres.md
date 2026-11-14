# Consultas libres: Ollama extrae el pedido y Neo4j decide · Luconi · 2026-11-14 · PG3-00

## En tres líneas
Hasta hoy el asistente solo respondía sobre los pedidos precargados `req_01` a `req_03`. Ahora una consulta inventada («quiero una notebook para programar y jugar, tengo 900 dólares») entra primero a Ollama, que saca un JSON con usos, juegos y presupuesto. Python lo valida, Neo4j lo guarda como `req_101` y corre las reglas solo para ese pedido, y SM4 recomienda. Resuelve los issues #12 a #24 (épica #11) en la rama `cl-consultas-libres`. Las pruebas pasan contra Neo4j real con un LLM guionado. **Falta correrlo con Ollama real.**

## Qué cambió
| Archivo | Qué tiene ahora |
| --- | --- |
| [`asistente/extractor.py`](../../asistente/extractor.py), [`prompts/extraccion.txt`](../../prompts/extraccion.txt) | Nuevos. Esquema JSON del pedido (`ESQUEMA_PEDIDO`) y prompt con el vocabulario cerrado del grafo: tipos de actividad, expresiones de frecuencia y juegos. `extraer(texto, llm, vocabulario)` usa `LLM.json` (`with_structured_output`). |
| [`asistente/inferencia.py`](../../asistente/inferencia.py) | Nuevo. Lista los archivos de reglas (`cypher/10`, `15`, `20`, `30`, `40`) y `inferir(grafo, req)` los corre en una transacción solo para ese pedido. |
| `cypher/10_sm1` … `40_sm4.cypher` | Cada `MATCH (c:Requerimiento ...)` tiene el filtro `($req IS NULL OR c.id = $req)`. Con `req = NULL` (carga completa) hace lo mismo que antes. |
| [`asistente/grafo.py`](../../asistente/grafo.py) | `escribir_lote` (varias sentencias en una transacción; si una falla no queda nada a medias) y `vocabulario()`. |
| [`asistente/submodulos/sm1/`](../../asistente/submodulos/sm1/) | `servicio.py` valida el JSON contra el texto (`validar_pedido`), `registrar_pedido` y `aclarar_pedido`. `repositorio.py` tiene el Cypher de alta, aclaración y borrado. `esquemas.py` suma los tipos del pedido. |
| [`asistente/router.py`](../../asistente/router.py), [`prompts/maestro.txt`](../../prompts/maestro.txt) | `parece_pedido(texto)`. Si el texto describe una necesidad y no nombra un pedido, antepone `SM1.registrar_pedido` y, si no hay otra consulta, agrega `SM4.recomendar`. |
| [`asistente/orquestador.py`](../../asistente/orquestador.py) | Corre la escritura antes que las lecturas, llama al extractor y guarda en la sesión el pedido, la repregunta pendiente y el borrador. |
| [`asistente/api.py`](../../asistente/api.py), [`cli.py`](../../asistente/cli.py), [`web/index.html`](../../asistente/web/index.html) | `sesion_id` en la API. La salida suma `pedido_nuevo`, `repregunta` y `pedido`. En la consola, `/nuevo`. En la web, el botón «Nueva conversación» y la tarjeta del pedido nuevo. |
| [`scripts/limpiar_pedidos.py`](../../scripts/limpiar_pedidos.py) | Nuevo. Borra los pedidos creados desde consultas (`origen: 'consulta'`). |
| `scripts/correr_e2e.py`, `verificar_grafo.py`, `contar_grafo.py`, `cargar_grafo.py` | Agregan el caso E2E-6. Los controles CP1, CP7 y CP11 se limitan a `req_01` a `req_03`. |
| [`tests/test_pedido_nuevo.py`](../../tests/test_pedido_nuevo.py) y otros tests | Validación, router, orquestador y grafo (con limpieza). También casos R32 a R37 en `consultas_router.csv`. |

## Cómo funciona (para alguien que no estuvo)
Ejemplo: «Quiero una notebook para programar y usar Docker, y a veces jugar al Fortnite. Tengo 900 dólares.»

1. **Router.** No hay `req_XX` en el texto y el texto parece un pedido, porque nombra un uso y un monto. Arma el plan `SM1.registrar_pedido` + `SM4.recomendar`.
2. **Ollama extrae** (no decide). Devuelve un JSON como este:
   ```json
   {
     "presupuesto": {"monto": 900, "moneda": "USD"},
     "actividades": [
       {"tipo": "programacion", "evidencia": "programar y usar Docker"},
       {"tipo": "juegos", "juegos": ["Fortnite"], "expresion_frecuencia": "a veces"}
     ]
   }
   ```
   Cada dato trae la `evidencia`, es decir, el fragmento literal del texto de donde salió.
3. **SM1 valida en Python:**
   - la evidencia tiene que estar en el texto (INT-R7);
   - el presupuesto tiene que estar entre 0 y 20 000 USD (INT-R1);
   - un monto en pesos se pasa a dólares solo si hay `COTIZACION_ARS_USD` (INT-R10);
   - el perfil sale del tipo de actividad (INT-R11): «programar» con Docker o una máquina virtual (VM) da VIRT (virtualización), y sin eso da DEV (desarrollo);
   - los juegos y las frecuencias tienen que existir en el grafo.

   Si falta algo, como el presupuesto o los usos, no se escribe nada y se repregunta. La respuesta siguiente de la misma conversación completa ese borrador.
4. **Neo4j escribe e infiere en una sola transacción.** Crea el `Requerimiento` `req_101` (los ids empiezan en 101 porque `req_04` y `req_05` están reservados para PG3-25) con sus actividades. Después corre las reglas de SM1 a SM4 filtradas por `$req = 'req_101'`. Los otros pedidos no se tocan (D-08).
5. **SM4 recomienda y el explicador redacta**, igual que para `req_01`. La respuesta empieza con «Registré tu pedido como req_101.» y el pedido queda en la sesión para las preguntas siguientes («¿y de RAM?»).

## Decisiones y por qué
- **El JSON lo valida Python y no el LLM.** Así se cumple «el LLM interpreta y explica, Neo4j decide»: un modelo de 3 B puede inventar un monto, y la validación contra el texto lo frena. Se descartó dejar que el LLM escriba Cypher, porque CLAUDE.md lo prohíbe.
- **Filtro `$req` en vez de copiar los archivos de reglas.** Hay una sola versión de cada regla para la carga y para el pedido nuevo. Se verificó que con `req = NULL` el grafo queda igual que antes; la única diferencia es la marca de tiempo `generada`.
- **Todo en una transacción** (`escribir_lote`). Si una regla falla, no queda un pedido sin evaluar.
- **Sesión en memoria en la API** (2 h, 1000 sesiones como máximo). Alcanza para el prototipo; un reinicio la borra.
- **La aclaración actualiza el mismo pedido** y marca la `Pregunta` como `respondida` (D-08, SM1 13-G).

## Cómo probarlo
```powershell
python -m unittest                                    # 233 OK, 5 salteadas (las de Ollama)
$env:PG3_TEST_LLM="1"; python -m unittest tests.test_pedido_nuevo   # con Ollama levantado
python -m scripts.correr_e2e                          # incluye E2E-6
python -m asistente.cli --traza "Quiero una notebook para programar y usar Docker, y a veces jugar al Fortnite. Tengo 900 dólares."
python -m scripts.limpiar_pedidos                     # deja solo req_01 a req_03
```
En E2E-6 tiene que salir: pedido nuevo registrado, perfil dominante VIRT, `Notebook_B` primera y todas las notebooks dentro de 900 USD.

## Qué queda y dudas
- **No se probó con Ollama real.** En este entorno no se pudo bajar el modelo. Las pruebas usaron un LLM guionado contra Neo4j real. Alguien con Ollama tiene que correr las pruebas con `PG3_TEST_LLM=1` y el E2E-6, y ajustar `prompts/extraccion.txt` si `qwen2.5:3b` extrae mal.
- **SM4 solo rankea perfiles con `SALIDA_PI2`** (hoy VIRT; OFI solo para `Notebook_K`). Un pedido DEV u OFI queda registrado y SM4 avisa que no hay evaluaciones (D-03, D-11).
- **Se tocaron archivos de otros dueños** (ARQUITECTURA §2):
  - SM1, el router y `prompts/maestro.txt` son de Olea;
  - el orquestador, la API, la consola, `cypher/15` y `cypher/20` son de Miranda;
  - `cypher/30` es de de Coninck;
  - `index.html` puede chocar con el PR #10.

  Pido que cada dueño revise su parte. `contrato.py` **no** se tocó.
- PG3-21 queda reemplazado por esta implementación.
