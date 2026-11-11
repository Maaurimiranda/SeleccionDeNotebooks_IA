# Manual de uso y README · Miranda · 2026-11-11 · PG3-16

## En tres líneas
- Se escribió [`docs/MANUAL_DE_USO.md`](../MANUAL_DE_USO.md) (ítem d de la entrega): alguien que no es del grupo puede instalar, cargar el grafo, hacer una consulta, leer la respuesta y ver la traza, con comandos de PowerShell y una tabla para Linux y macOS.
- El [`README.md`](../../README.md) ya no tiene secciones «Pendiente»: las §3 a §9 (arquitectura, estructura, requisitos, puesta en marcha, uso, pruebas y trazabilidad) quedaron completas, y la §10 dice dónde está cada ítem a–l del ZIP.
- Cada comando del manual se contrastó con el código y, donde se pudo sin Neo4j, **se corrió**. Lo que depende del grafo real (el `11/11 OK` y las respuestas de los E2E) **no se pudo verificar en esta sesión**; la lista está al final. El criterio «Olea sigue el manual desde cero» sigue abierto: lo tiene que hacer una persona.

## Qué cambió
| Archivo | Qué tiene ahora |
| --- | --- |
| [`docs/MANUAL_DE_USO.md`](../MANUAL_DE_USO.md) | Requisitos, instalación, `.env`, carga y verificación del grafo, consola y API, las consultas de E2E-1, 2, 5, 9, 10 y 8, cómo leer una respuesta, la traza, errores comunes y la tabla para Linux y macOS |
| [`README.md`](../../README.md) | §3 a §9 completas; §5 sin `[confirmar]`; §10 con el mapa de los ítems a–l; §11 con el estado al día |

## Cómo funciona (para alguien que no estuvo)
**Qué es el manual.** La consigna (§4, ítem d) pide un manual de uso para quien revisa el proyecto. Está escrito para un lector que no conoce el sistema: el docente. Sigue el orden en que se usa: instalar (Python, Ollama con el modelo `qwen2.5:3b`, Neo4j 5), cargar la base de conocimiento, hacer una consulta, entender qué se recibió.

**Lo que hay que saber del `.env`.** El código no lee el `.env` solo: [`asistente/config.py`](../../asistente/config.py) usa `os.getenv` y no hay `python-dotenv` (D-05). Por eso el manual trae un bloque de PowerShell que carga el `.env` en la ventana; `.env.example` solo mencionaba la forma de bash (`source .env`). Hay que correrlo en **cada** ventana nueva, junto con la activación del entorno virtual.

**Cómo se llama a la API desde Windows PowerShell 5.1.** `Invoke-RestMethod` rompe las tildes de las respuestas (lee el JSON como Latin-1), y al enviar texto con tildes hay que mandar los bytes en UTF-8. El manual da una función `Consultar` que hace las dos cosas bien. La alternativa más simple es `/docs` en el navegador.

**«Cómo leer una respuesta».** Se explican cuatro cosas, todas sacadas de [`asistente/contrato.py`](../../asistente/contrato.py) y [`asistente/explicador.py`](../../asistente/explicador.py): los cinco valores de `origen_respuesta` (`llm`, `plantilla_fija`, `validacion`, `fuera_de_alcance`, `error`), los seis estados de D-06 con un ejemplo de `req_01` cada uno, el tratamiento de rangos, `desconocida` e `indeterminado` (no se completan ni se promedian) y la advertencia fija de parámetros sin validar. `intento` vale 0 si no se llegó a explicar, 1 si el verificador aprobó a la primera y 2 o 3 si hubo que regenerar.

**De dónde salen los «qué tiene que decir el grafo».** De la tabla de [PG3-11](../plan/issues/PG3-11.md) (D-12) y de los fixtures de [`tests/fixtures/`](../../tests/fixtures/), que son filas reales del grafo (por ejemplo, A en el puesto 1 con 0,785; M con grado entre 0,504 y 0,826; G con riesgo entre 49,58 y 81,46 y las alertas REN-R10 y FZ-R7). **No hay texto de respuestas del modelo copiado**: todavía no existe ningún `docs/pruebas/E2E-n.md` real, y no se inventó ninguno.

## Decisiones y por qué
- **PowerShell primero y una tabla para Linux y macOS** (criterio del issue). Alternativa descartada: un script `.ps1` que cargue el `.env`. Es un archivo más para mantener y la arquitectura (§4.6) dice que el manual explica cómo cargarlo.
- **Se sumó E2E-3 como control** (`req_02`, perfil indeterminado), que el issue no lista. Cuesta una línea y muestra cómo se lee un pedido sin perfil, que es de lo que más se aclara en la consigna.
- **README §11:** se tildó solo lo que está hecho según `PROMPT_CONTINUACION.md` (integración de SM1 a SM4, router, API y consola, explicador con la salvedad de que falta ajustarlo, y el manual). No se tocaron las líneas de SM2 de PI4 ni las §12 a §14: son de otros y no están en el alcance del issue (ver «Qué queda»).
- **Tiempos:** el manual no promete un número. Cita lo que midió de Coninck (el plan, 10 a 50 s, `PLAN_PG3.md` §5) y avisa que la primera consulta es la más lenta.

## Cómo probarlo
Para revisar este PR, en una carpeta limpia:
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m unittest                  # esta sesión: 171 pruebas, OK, 26 salteadas (sin Neo4j ni Ollama)
```
Y después seguir el manual de la §2.5 en adelante con Neo4j y Ollama: tiene que terminar en `11/11 OK` (`verificar_grafo`) y en la respuesta de E2E-1 (A primera con 0,785).

Lo que se corrió en esta sesión, en un entorno con Ollama y sin credenciales de Neo4j: `pip install -r requirements.txt` en un entorno virtual nuevo (Python 3.14.5); `python -m unittest`; `scripts.cargar_grafo` sin contraseña (da `Falta NEO4J_PASSWORD…`); el conteo de sentencias por archivo de `cypher/` (101 en total, igual que la salida que muestra el manual); `asistente.cli` con `--help`, `--traza`, `--pedido` y el modo conversación (`/pedido`); la API (`/salud`, `/consultar`, `/docs`) con un Neo4j inalcanzable a propósito, para comprobar los mensajes de error, la validación (vacío, sin letras, más de 1500 caracteres) y la traza en disco; el bloque que carga el `.env`; la función `Consultar`; el puerto ocupado; la salud de Ollama con un modelo inexistente y con Ollama apagado; y el `curl` y el `.env` en bash.

## Qué queda y dudas
**No se pudo verificar (hace falta Neo4j con credenciales y una persona):**
- El **criterio de aceptación 1**: Olea siguiendo el manual desde cero y obteniendo la respuesta de E2E-1. Hay que dejarlo comentado en el issue.
- La salida real de `cargar_grafo` y `verificar_grafo` con Neo4j (el manual muestra el formato leído del código y los conteos por archivo calculados sin conectar), y que la consulta Cypher de «Para controlar una respuesta contra el grafo» devuelva lo esperado (tiene la forma de las de `verificar_grafo.py`, pero no se ejecutó).
- Las respuestas reales de las seis consultas de ejemplo. Lo que dice el manual de cada una viene de D-12 y de los fixtures, no de una corrida. Para E2E-10 el orden exacto por movilidad y para E2E-9 el riesgo de RAM de la A quedan «como los devuelva el grafo»: se fijan con PG3-11.
- Los pasos de Neo4j Desktop y de AuraDB Free (los menús cambian) y la tolerancia a Python 3.10 a 3.13 (solo se probó 3.14); el mensaje de `Set-ExecutionPolicy` y el `AuthError` por contraseña incorrecta, escritos por lo que hace el código y por lo conocido, no por haberlos visto.
- Tiempos de punta a punta, que PG3-11 tiene que medir en más de una máquina.

**Hallazgos para el grupo:**
- **E2E-8 y el grafo.** El orquestador lee el catálogo y los pedidos de Neo4j **antes** de pedirle el plan al router (`orquestador.py`, `consultar`). Con Neo4j apagado, hasta «¿Cuál es la capital de Francia?» devuelve el error de Neo4j. La traza de E2E-8 sí queda con `consultas: []`, pero el criterio de PG3-11 («no ejecuta ninguna consulta Cypher») es cierto solo para los submódulos: el catálogo sí se lee. Conviene redactarlo así en PG3-11 (de Coninck). El manual lo dice.
- **La API no tiene sesión:** cada `POST /consultar` arma una sesión vacía (`sesion={}` en `api.py`), así que hay que mandar el pedido en cada llamada. La consola sí lo recuerda.
- **README, partes que quedaron desactualizadas y no se tocaron:** en §11, las dos líneas de SM2 (verificación semántica y script de PI4); §12, «Del flujo de SM2 en PI4»; §13, que sigue como «propuesta» y sugiere ramas como `sm2/verificador-semantico` mientras que `CLAUDE.md` define `pg3-NN-descripcion`; §14, con `[completar]`. Quien es dueño de cada tema decide si se reescriben.
- **`PROMPT_CONTINUACION.md`** todavía lista PG3-16 como pendiente y cuenta 151 pruebas; hay que actualizarlo al unir este PR.
- **Pregunta:** ¿se quiere que el manual muestre una respuesta real completa (texto del modelo) cuando PG3-11 la tenga? Hoy no hay ninguna que copiar, y copiar una a mano sería inventarla.
