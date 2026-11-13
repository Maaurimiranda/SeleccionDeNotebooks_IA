# Manual de uso · Asistente experto para la selección de notebooks

> **Para quién:** para alguien que no es del grupo (por ejemplo, el docente) y quiere instalar el asistente, cargar su base de conocimiento y hacer una consulta sin ayuda. Es el ítem d) de la entrega ([consigna §4](consigna/ConsignaPG3.md#4-formato-del-entregable)).
> **Sistema operativo:** los comandos son de **PowerShell en Windows**, que es lo que usa el grupo. Las diferencias para Linux y macOS están en la [sección 11](#11-linux-y-macos).
> **Probado con:** Windows 11, Python 3.14, Ollama con `qwen2.5:3b` y, por el grupo, Neo4j 5.26 local (ver [`docs/pruebas/conteos_grafo.md`](pruebas/conteos_grafo.md)).

## Índice

1. [Requisitos](#1-requisitos)
2. [Instalación](#2-instalación)
3. [Cargar y verificar el grafo](#3-cargar-y-verificar-el-grafo)
4. [Usar el asistente](#4-usar-el-asistente)
5. [Consultas de ejemplo](#5-consultas-de-ejemplo)
6. [Cómo leer una respuesta](#6-cómo-leer-una-respuesta)
7. [Ver la traza](#7-ver-la-traza)
8. [Errores comunes](#8-errores-comunes)
9. [Probar el sistema](#9-probar-el-sistema)
10. [Dónde seguir](#10-dónde-seguir)
11. [Linux y macOS](#11-linux-y-macos)

## De cero a la primera respuesta, en una mirada

| Paso | Qué | Sección |
| --- | --- | --- |
| 1 | Instalar Python, Ollama y Neo4j 5 | 1 y 2 |
| 2 | Crear el entorno virtual e instalar `requirements.txt` | 2.2 |
| 3 | Descargar el modelo: `ollama pull qwen2.5:3b` | 2.3 |
| 4 | Copiar `.env.example` a `.env` y poner la contraseña de Neo4j | 2.5 |
| 5 | Cargar el grafo y comprobar que da `11/11 OK` | 3 |
| 6 | Hacer una consulta con la consola o con la API | 4 y 5 |

---

## 1. Requisitos

### Hardware

| Recurso | Mínimo | Nota |
| --- | --- | --- |
| Memoria RAM | ~4 GB libres para el modelo `qwen2.5:3b` (~8 GB si usás `qwen2.5:7b`) | Más lo que consuma Neo4j |
| Disco | ~2 GB para el modelo (`qwen2.5:3b` pesa 1,9 GB) más el espacio de Neo4j y de las dependencias de Python | |
| Red | Solo para instalar (paquetes de Python y descarga del modelo) | Después el sistema corre local, sin APIs pagas |

El proyecto no exige placa de video. La velocidad de las respuestas depende del equipo (ver [Tiempos](#tiempos)).

### Software

| Herramienta | Versión | Para qué |
| --- | --- | --- |
| Windows + PowerShell | 10 u 11 | Los comandos de este manual |
| Python | 3.10 o posterior (probado con 3.14) | El código del asistente |
| Ollama | Reciente, con el modelo `qwen2.5:3b` | El LLM local: interpreta la consulta y redacta la respuesta |
| Neo4j | 5.x (probado con 5.26): Neo4j Desktop local o AuraDB Free | La base de conocimiento, que es la que maneja la verdad |
| Git | Opcional | Solo si bajás el código con `git clone` |

### Puertos que usa

| Puerto | Servicio |
| --- | --- |
| 7687 | Neo4j (protocolo Bolt) |
| 7474 | Neo4j Browser, solo si querés mirar el grafo (opcional) |
| 11434 | Ollama |
| 8000 | La API del asistente (se puede cambiar con `--port`) |

---

## 2. Instalación

### 2.1 Obtener el código

Con el ZIP de la entrega, descomprimilo. Con Git:

```powershell
git clone <URL del repositorio>
```

Abrí PowerShell **en la carpeta raíz del proyecto**, la que tiene `requirements.txt`. Todos los comandos de este manual se corren desde ahí.

- **Con Git:** la raíz es la carpeta del repositorio clonado.
- **Con el ZIP:** la raíz es **`e_codigo_fuente/`**, dentro de la carpeta descomprimida. Tiene todo lo que hace falta para correr el sistema: el código, `requirements.txt`, `.env.example`, `cypher/`, `docs/cypher/` y `tests/`. Las demás carpetas del ZIP (`c_`, `f_`, `g_`, …) son para revisar cada ítem por separado, y desde ellas los comandos no andan. Por ejemplo, si corrés `python -m scripts.cargar_grafo` desde otra carpeta, termina con un error y no toca la base.

### 2.2 Python: entorno virtual y dependencias

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Instala solo lo que está en `requirements.txt`: `neo4j`, `langchain-core`, `langchain-ollama`, `requests`, `fastapi`, `uvicorn` y `httpx`. Si PowerShell dice que la ejecución de scripts está deshabilitada, corré esto y repetí la activación (solo vale para esa ventana):

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Si no tenés Python, instalalo desde python.org y marcá **Add python.exe to PATH**.

### 2.3 Ollama y el modelo

1. Instalá Ollama desde https://ollama.com/download.
2. Descargá el modelo (1,9 GB):

```powershell
ollama pull qwen2.5:3b
ollama list
```

`ollama list` tiene que mostrar `qwen2.5:3b`. Si da un error de conexión, abrí la aplicación Ollama o corré `ollama serve` en otra terminal.

> Opcional: `qwen2.5:7b` da respuestas algo mejores pero pide ~8 GB de RAM. Para usarlo, bajalo con `ollama pull qwen2.5:7b` y poné `OLLAMA_MODEL=qwen2.5:7b` en el `.env`. El proyecto está medido con `qwen2.5:3b`.

### 2.4 Neo4j

Hace falta una base **vacía y dedicada a este proyecto**: el paso 3 la **borra** antes de cargar el grafo.

**Con Neo4j Desktop (local):** creá una instancia nueva con una versión 5.x, elegí una contraseña, iniciala y dejá el puerto Bolt por defecto (7687). Los nombres de los menús cambian entre versiones de Desktop; lo que importa es tener la instancia corriendo y la contraseña a mano.

**Con AuraDB Free:** creá una instancia y guardá el usuario, la contraseña y la URI que te da Aura (empieza con `neo4j+s://`). Esa URI va en `NEO4J_URI`. No se probó el flujo completo con Aura; el grupo trabajó con Neo4j local.

### 2.5 El archivo `.env`

Copiá la plantilla y completá la contraseña de Neo4j:

```powershell
Copy-Item .env.example .env
notepad .env
```

| Variable | Qué es | Valor por defecto |
| --- | --- | --- |
| `NEO4J_URI` | Dónde está Neo4j | `bolt://localhost:7687` |
| `NEO4J_USER` | Usuario de Neo4j | `neo4j` |
| `NEO4J_PASSWORD` | **La contraseña que elegiste.** Obligatoria | (vacía) |
| `NEO4J_DATABASE` | Base dentro de Neo4j | `neo4j` |
| `OLLAMA_URL` | Dónde está Ollama | `http://localhost:11434` |
| `OLLAMA_MODEL` | Modelo de Ollama | `qwen2.5:3b` |
| `MAX_CARACTERES` | Largo máximo de una consulta | `1500` |
| `MAX_REGENERACIONES` | Veces que el explicador reintenta antes de usar la plantilla fija | `2` |
| `DIR_TRAZAS` | Carpeta donde se guarda la traza | `trazas` |

Escribí los valores sin comillas. **El `.env` no se sube nunca a Git** (está en `.gitignore`: el repositorio es público) y no se comparte.

El código **no lee el `.env` solo**: las variables se cargan en la ventana de PowerShell antes de lanzar cualquier comando. Es el primer paso del bloque de la sección 4.1.

---

## 3. Cargar y verificar el grafo

Con la terminal preparada como en la [sección 4.1](#41-cada-vez-que-abrís-una-terminal) y Neo4j iniciado:

```powershell
python -m scripts.cargar_grafo
```

**Borra todo lo que haya en esa base** y carga los scripts de `cypher/` en orden. Tiene que terminar así:

```text
Cargando el grafo en bolt://localhost:7687 ... (BORRA todo lo que haya en la base)
  00_esquema.cypher: 12 sentencias
  01_conocimiento.cypher: 16 sentencias
  02_instancias.cypher: 27 sentencias
  10_sm1.cypher: 7 sentencias
  15_evaluaciones.cypher: 1 sentencias
  20_sm2.cypher: 11 sentencias
  30_sm3.cypher: 9 sentencias
  40_sm4.cypher: 18 sentencias
Listo: 101 sentencias.
```

Después, la verificación:

```powershell
python -m scripts.verificar_grafo
```

Compara lo que devuelve el grafo con los 11 casos de prueba de la base (CP1 a CP11) y no escribe nada. Tiene que terminar con **`11/11 OK`**. Si algún caso falla, la última línea lista cuáles y el comando sale con código 1: volvé a cargar el grafo.

---

## 4. Usar el asistente

Hay dos formas de usarlo y hacen lo mismo: la **consola** (la más simple) y la **API**. Las dos pasan por el mismo camino: el router interpreta la consulta, el sistema consulta Neo4j con consultas Cypher fijas de solo lectura, y el explicador redacta la respuesta a partir de lo que devolvió el grafo.

### 4.1 Cada vez que abrís una terminal

Las variables de entorno y el entorno virtual valen **solo para la ventana donde los cargaste**. En cada ventana nueva, desde la carpeta raíz del proyecto:

```powershell
cd C:\ruta\al\proyecto
.venv\Scripts\Activate.ps1
Get-Content .env | Where-Object { $_ -match '^\s*[^#\s][^=]*=' } | ForEach-Object {
    $nombre, $valor = $_ -split '=', 2
    Set-Item -Path "Env:$($nombre.Trim())" -Value $valor.Trim()
}
```

Con eso quedan activos el entorno de Python y las variables del `.env`. Ollama y Neo4j tienen que estar corriendo.

### 4.2 La consola

Una sola consulta:

```powershell
python -m asistente.cli "Para req_01, ¿qué notebook me recomendás? ¿Cómo andan de RAM y de gráfica?"
```

Sale la respuesta y, debajo, una línea con el origen, el pedido y los submódulos consultados:

```text
<respuesta del asistente>

  [origen: llm · pedido: req_01 · submódulos: SM1, SM2, SM3, SM4]
```

Opciones (todas son de `asistente/cli.py`):

| Opción | Qué hace |
| --- | --- |
| `--traza` | Agrega debajo de la respuesta el plan, las consultas ejecutadas, la duración y el error si lo hubo (ver [sección 7](#7-ver-la-traza)) |
| `--pedido req_01` | Fija el pedido de la sesión, para no escribirlo en cada consulta |
| (sin texto) | Abre el modo conversación |

Modo conversación:

```powershell
python -m asistente.cli
```

```text
[sin pedido] > /pedido req_01
Pedido de la sesión: req_01

[req_01] > ¿Qué me recomendás?
```

Comandos del modo conversación: `/pedido req_01` fija el pedido y `/salir` termina (también `/exit`, `/q`, Ctrl+C o Ctrl+Z y Enter). Cualquier otra línea es una consulta. En la consola, el pedido de la sesión queda guardado mientras no salgas.

### 4.3 La API

```powershell
uvicorn asistente.api:app
```

Queda escuchando en `http://127.0.0.1:8000` (si el puerto está ocupado: `uvicorn asistente.api:app --port 8001`). Se corta con Ctrl+C. Es la entrada única del sistema y tiene dos operaciones:

| Operación | Para qué |
| --- | --- |
| `GET /salud` | Dice si Neo4j y Ollama (con el modelo descargado) responden. `ok: true` solo si ambos están bien |
| `POST /consultar` | Hace una consulta. Entrada: `texto` (obligatorio, hasta 1500 caracteres) y `requerimiento_id` (opcional, por ejemplo `req_01`) |

**Desde el navegador (lo más simple):** abrí `http://localhost:8000/docs`, elegí `POST /consultar`, **Try it out**, completá el cuerpo y **Execute**. Esa página carga sus componentes desde internet.

**Desde PowerShell.** Pegá una vez esta función y usala (los bytes en UTF-8 evitan que se rompan las tildes en Windows PowerShell 5.1):

```powershell
function Consultar($texto, $pedido) {
    $c = @{ texto = $texto }
    if ($pedido) { $c.requerimiento_id = $pedido }
    $bytes = [System.Text.Encoding]::UTF8.GetBytes(($c | ConvertTo-Json))
    $r = Invoke-WebRequest -Uri http://localhost:8000/consultar -Method Post -ContentType "application/json; charset=utf-8" -Body $bytes -UseBasicParsing
    [System.Text.Encoding]::UTF8.GetString($r.RawContentStream.ToArray()) | ConvertFrom-Json
}

$res = Consultar "Para req_01, ¿qué notebook me recomendás? ¿Cómo andan de RAM y de gráfica?" "req_01"
$res.respuesta
$res | Select-Object requerimiento_id, origen_respuesta, intento, submodulos_consultados
```

Para ver la salud:

```powershell
(Invoke-WebRequest http://localhost:8000/salud -UseBasicParsing).Content
```

La respuesta de `POST /consultar` trae estos campos:

| Campo | Qué es |
| --- | --- |
| `respuesta` | El texto para el asesor |
| `requerimiento_id` | El pedido sobre el que se respondió (`null` si la consulta no usó ninguno) |
| `submodulos_consultados` | Qué submódulos se consultaron (`SM1` a `SM4` y `GRUPO`) |
| `origen_respuesta` | De dónde salió la respuesta (ver [sección 6](#origen_respuesta-de-dónde-salió-el-texto)) |
| `intento` | Intento del explicador: `1` es a la primera, `2` o `3` indica que hubo que regenerar, `0` que no se llegó a explicar |
| `traza` | El registro completo de la consulta (ver [sección 7](#7-ver-la-traza)) |

> **Cada llamada a la API es independiente:** no recuerda el pedido de la anterior. Escribí el pedido en el texto (`req_01`) o mandá `requerimiento_id` en cada consulta.

### Tiempos

Cada consulta hace dos llamadas al modelo (una para interpretar y otra para redactar) y puede reintentar la redacción. Con `qwen2.5:3b`, en la máquina de de Coninck el plan solo tardó entre 10 y 50 s ([`PLAN_PG3.md`](plan/PLAN_PG3.md) §5), así que una consulta completa puede llevar **de varios segundos a más de un minuto**. La primera es la más lenta porque Ollama carga el modelo en memoria. El límite por llamada es de 120 s: pasado ese tiempo, la respuesta es el error del modelo (sección 8).

---

## 5. Consultas de ejemplo

Son los casos integrales de las pruebas E2E (de punta a punta) y el control de fuera de alcance. **Lo que decide si una respuesta está bien es lo que dice el grafo** (estados, grados, puestos, alertas), no la redacción exacta del modelo, que puede variar entre corridas y se limita a unas 150 palabras. Para cada consulta se indica qué tiene que aparecer.

Corré cada una desde la terminal preparada (sección 4.1):

```powershell
python -m asistente.cli "Para req_01, ¿qué notebook me recomendás? ¿Cómo andan de RAM y de gráfica?"
python -m asistente.cli "En req_01, ¿por qué la M quedó condicionada y la G indeterminada?"
python -m asistente.cli "En req_01, la E tiene casi el mismo puntaje que la B y la H, ¿por qué no la recomiendan?"
python -m asistente.cli "En req_01, ¿qué reglas se activaron para la A, de dónde sale cada dato y qué riesgo de RAM tiene?"
python -m asistente.cli "Para req_01, ¿cuáles son las mejores en movilidad y cómo queda el costo-beneficio?"
python -m asistente.cli "¿Cuál es la capital de Francia?"
```

| Caso | Qué muestra | Submódulos | Qué tiene que decir el grafo |
| --- | --- | --- | --- |
| **E2E-1** | Una recomendación completa que cruza cuatro submódulos | SM1, SM2, SM3 y SM4 | `Notebook_A` en el puesto 1, `Recomendada (Alta)`, grado 0,785. Después `Notebook_H` (puesto 2) y `Notebook_B` (puesto 3), ambas `Recomendada (Media)`. `Notebook_X` aparece aparte, como alternativa **fuera de presupuesto** (+5 %). `Notebook_M` es condicionada, `Notebook_G` indeterminada, `Notebook_E` y `Notebook_C` descartadas. La respuesta puede no nombrarlas todas: el ranking completo está en la traza |
| **E2E-2** | Un dato faltante que atraviesa módulos | SM2, SM3 y SM4 | `Notebook_M`: `Recomendada condicionada por falta de informacion`, grado entre 0,504 y 0,826, porque la ficha no informa la autonomía (REC-R15). `Notebook_G`: `Indeterminada: completar informacion`, riesgo de RAM entre 49,58 y 81,46, con las alertas REN-R10 y FZ-R7 |
| **E2E-5** | Un requisito excluyente que pesa más que el puntaje | SM2 y SM4 | `Notebook_E` (adecuación 0,81) está casi igual que `Notebook_B` (0,813) y `Notebook_H` (0,811), pero es `Descartada (excluyente incumplido)`: su CPU no soporta virtualización, que el perfil exige (REN-R1 y REC-R3) |
| **E2E-9** | Trazabilidad de una notebook | GRUPO, SM2 y SM4 | La traza de reglas de `Notebook_A` (18 reglas distintas de los cuatro submódulos, cada una con su fuerza), de dónde sale cada dato (14 de las 18 reglas tienen origen; GM-R3, INT-R11, REC-R4 y REC-R9 figuran como «no registrada»), la fuente del precio y de la autonomía, y el riesgo de RAM tal como lo devuelve el grafo |
| **E2E-10** | Búsqueda por movilidad más costo-beneficio | SM3 y SM4 | Notebooks ordenadas de mayor a menor adecuación de movilidad. Si una no tiene el dato (por ejemplo `Notebook_M`, sin autonomía informada) se dice que falta, **sin inventar un número**. El costo-beneficio sale del grafo: por ejemplo, `Notebook_B` tiene 1,161 |
| **E2E-8** (control) | Una pregunta que no es del dominio | Ninguno | `origen: fuera_de_alcance`, el mensaje fijo de alcance y **ninguna consulta al grafo** (en la traza, `consultas` queda vacía). Necesita igual Neo4j y Ollama levantados: el sistema lee el catálogo y el router (que usa el modelo) decide que no es del dominio |

Un control más, para ver cómo se lee un pedido sin perfil definido:

```powershell
python -m asistente.cli "Para req_02, ¿qué notebook me conviene?"
```

`req_02` tiene el perfil `indeterminado`: el sistema **no asume** ningún perfil, no evalúa ninguna notebook y repite la pregunta pendiente («¿Qué programas o actividades va a usar con la notebook?»).

Los submódulos de la columna son los que tiene que consultar el router; la línea `[origen: … · submódulos: …]` de la consola muestra los que realmente se consultaron. `SM1` aparece siempre que hay un pedido, porque el sistema lo agrega para llevar el perfil y el presupuesto en la evidencia.

### Para controlar una respuesta contra el grafo

Si querés comprobar lo que dijo el asistente por tu cuenta, abrí Neo4j Browser (`http://localhost:7474`, o el botón *Open* de Neo4j Desktop) y corré esta consulta de solo lectura, que tiene la misma forma que las de `scripts/verificar_grafo.py`:

```cypher
MATCH (:Requerimiento {id:'req_01'})-[:EVALUA]->(ev:Evaluacion)-[:SOBRE]->(n:Notebook)
RETURN n.modelo AS notebook, ev.estado AS estado, ev.grado_recomendacion AS grado,
       ev.grado_recomendacion_min AS grado_min, ev.grado_recomendacion_max AS grado_max
ORDER BY grado DESC
```

---

## 6. Cómo leer una respuesta

Una respuesta tiene cuatro partes: el **texto**, el **origen**, los **estados y rangos** que cita y la **advertencia** del final.

### `origen_respuesta`: de dónde salió el texto

En la consola aparece como `[origen: …]`; en la API es el campo `origen_respuesta`.

| Valor | Qué significa | Qué hacer |
| --- | --- | --- |
| `llm` | La redactó el modelo y el **verificador** la aprobó: cada cifra, notebook, regla y alerta que cita está en lo que devolvió el grafo | Nada: es el caso normal |
| `plantilla_fija` | El modelo no logró una redacción que pasara el verificador (se intenta 1 vez más 2 reintentos). Se muestra un texto armado por código con los datos del grafo | Es correcta pero seca (líneas como `SM4.recomendar:` y los datos). Podés reformular la consulta |
| `validacion` | La entrada no se pudo procesar y el asistente **pide una aclaración**: consulta vacía o muy larga, pedido o modelo que no existe, falta el pedido | Leé el mensaje: dice qué falta (sección 8) |
| `fuera_de_alcance` | La consulta no es del dominio. Mensaje fijo, sin tocar el grafo | Preguntá sobre notebooks, pedidos o reglas del sistema |
| `error` | Neo4j u Ollama no respondieron, o falló algo inesperado. Mensaje fijo | Sección 8; el detalle técnico está en la traza (`error`) |

### Estados de una notebook

Son siempre estos seis, escritos así (sin tildes, como están en el grafo). Los decide la base de conocimiento, no el modelo:

| Estado | Qué significa para el asesor | Ejemplo en `req_01` |
| --- | --- | --- |
| `Recomendada (Alta)` | Cumple lo que pide el perfil y su grado de recomendación es alto: opción firme | `Notebook_A`, grado 0,785 |
| `Recomendada (Media)` | Cumple, con un grado medio: es para considerar | `Notebook_H` y `Notebook_B` |
| `Recomendada condicionada por falta de informacion` | Podría recomendarse, pero a la ficha le falta un dato: el grado sale como **rango** y hay que completar el dato | `Notebook_M` (falta la autonomía) |
| `Indeterminada: completar informacion` | Falta un dato clave y **no se puede decidir** | `Notebook_G` (no se sabe si su RAM es ampliable) |
| `Descartada (excluyente incumplido)` | No cumple un requisito que el perfil exige, aunque su puntaje sea parecido al de las recomendadas | `Notebook_E` (su CPU no soporta virtualización) |
| `Descartada` | Su grado de recomendación quedó bajo | `Notebook_K` (8 GB de RAM contra 16 GB mínimos) |

Una notebook que se pasa un poco del presupuesto no se recomienda en primer lugar: aparece aparte, como **alternativa fuera de presupuesto**, con el porcentaje que se pasa.

### Rangos, «desconocida» e «indeterminado»

El sistema **no completa ni promedia** lo que no sabe:

- **Rango:** si falta un dato, el valor se informa como un intervalo, por ejemplo «el riesgo de RAM de la `Notebook_G` está entre 49,58 y 81,46 sobre 100». Son el peor y el mejor caso; no hay un número «del medio». El grado de `Notebook_M`, entre 0,504 y 0,826, se lee igual.
- **`desconocida`:** el dato no figura en la ficha (por ejemplo, si la RAM de la G es ampliable). No equivale a «no» ni a «sí».
- **`indeterminado`:** un pedido sin perfil definido (como `req_02`). No se elige un perfil por el comprador.

### Alertas y reglas

Los códigos como `REN-R10`, `FZ-R7` o `REC-R15` son las reglas de la base de conocimiento. El prefijo dice de qué submódulo vienen: `INT` (SM1, interpretación del pedido), `REN` y `FZ` (SM2, rendimiento: reglas crisp y difusas), `GM` (SM3, gráfica y movilidad) y `REC` (SM4, recomendación). Una **alerta** es un aviso del grafo sobre **una notebook concreta** («la ficha no informa si la RAM es ampliable»); no es lo mismo que una regla activada. Una alerta siempre se cita junto con su notebook.

### La advertencia del final

Toda respuesta que consulta el grafo cierra con este texto, copiado literal:

> Los parametros difusos y los umbrales del sistema estan sin validar por el tecnico: los grados y riesgos son una referencia, no una certeza.

Es una limitación real: los parámetros del modelo difuso (centros, sigmas y umbrales) todavía **no los validó un técnico**. Los grados y los riesgos sirven para ordenar y comparar, no como un dato cierto. Si el modelo se olvida de copiarla, la agrega el código.

Las respuestas de recomendación (SM4: recomendar, explicar una notebook, comparar y costo-beneficio) suman un aviso más, con la cuenta que sale del grafo:

> Los 9 parametros de recomendacion de SM4 todavia requieren validacion con el tecnico.

Son las 9 etiquetas difusas de SM4: adecuación global (baja, media y alta), excedente de presupuesto (dentro, levemente y muy) y grado de recomendación (descartar, considerar y recomendar). Si el técnico valida alguno, el número baja solo; con todos validados, el aviso desaparece.

---

## 7. Ver la traza

Cada consulta deja un registro que permite **reconstruir cómo se llegó a la respuesta**: qué entendió el modelo, qué se le preguntó a Neo4j, qué datos volvieron y qué se le pasó al explicador. Hay tres formas de verlo.

**1. En la consola, con `--traza`:**

```powershell
python -m asistente.cli --traza "Para req_01, ¿qué notebook me recomendás?"
```

Debajo de la respuesta imprime el plan (`plan:`), las observaciones de la validación, una línea por consulta ejecutada (nombre, milisegundos, cantidad de filas y parámetros), la duración y, si hubo, el `error:`.

**2. En la API:** es el campo `traza` de la respuesta (`$res.traza` con la función de la sección 4.3).

**3. En el archivo:** una línea JSON por consulta en `trazas\AAAA-MM-DD.jsonl`, dentro de la carpeta desde donde lanzaste el asistente (o la de `DIR_TRAZAS`). Está en `.gitignore`. Para ver la última consulta con todo el detalle:

```powershell
python -c "import json,sys; print(json.dumps(json.loads(open(sys.argv[1], encoding='utf-8').read().splitlines()[-1]), ensure_ascii=False, indent=2))" trazas\2026-11-11.jsonl
```

(Cambiá la fecha por la del archivo que haya en `trazas\`.)

| Campo de la traza | Qué tiene |
| --- | --- |
| `consulta_usuario` | El texto tal como lo escribiste |
| `plan` | Lo que entendió el router: pedido, intenciones elegidas y fragmentos del texto que las justifican |
| `validacion` | Observaciones de la validación del plan y, si hubo, la aclaración pedida |
| `consultas` | Por cada consulta al grafo: submódulo, nombre, el **Cypher ejecutado**, sus parámetros, las **filas que devolvió Neo4j** y los milisegundos |
| `evidencia` | Lo que recibió el explicador: es lo único que el modelo puede usar para redactar |
| `intentos` | Cada texto que escribió el modelo y los problemas que le encontró el verificador |
| `respuesta`, `origen_respuesta` | El texto final y de dónde salió |
| `duracion_ms`, `segundos` | Cuánto tardó cada paso (`plan`, `consultas`, `explicacion`) y en total |
| `error` | El detalle técnico si algo falló |

Con esto se contestan las cinco preguntas de trazabilidad de la consigna (§3.7): la **regla** (`[:ACTIVA]` en el grafo y la intención `GRUPO.traza_reglas`), la **fuente** (en `evidencia`, el `origen` de los parámetros y la fuente del precio y de la autonomía), la **evidencia** (`evidencia`), la **consulta** (`consultas`) y la **explicación** (`intentos` y `respuesta`). Más detalle en [`ARQUITECTURA.md`](ARQUITECTURA.md) §8.

---

## 8. Errores comunes

### Del asistente

| Lo que ves | Causa | Qué hacer |
| --- | --- | --- |
| `No pude consultar la base de conocimiento (Neo4j) en este momento…` (`origen: error`). Antes pueden salir líneas `Transaction failed and will be retried…` | Neo4j apagado, URI o puerto incorrectos, o contraseña mal cargada | 1) Iniciá Neo4j. 2) Corré `GET /salud` y mirá `neo4j.error`. 3) Revisá `NEO4J_URI` y `NEO4J_PASSWORD` **en esta ventana** (sección 4.1). En la traza, `error` empieza con el tipo de excepción: `ServiceUnavailable` es que no hay conexión, `AuthError` que la contraseña no es la correcta. Este error sale **incluso con una pregunta fuera de alcance**, porque el sistema lee el catálogo de Neo4j antes de interpretar la consulta |
| `No pude usar el modelo de lenguaje (Ollama) en este momento…` (`origen: error`) | Ollama apagado, **modelo sin descargar** o equipo tan lento que pasó el límite de 120 s | Corré `ollama list`: tiene que figurar el modelo de `OLLAMA_MODEL`. Si falta, `ollama pull qwen2.5:3b`. Si Ollama no responde, abrilo o corré `ollama serve`. `GET /salud` muestra `ollama.modelo_disponible`. Si fue por lentitud, volvé a intentar: la segunda vez el modelo ya está cargado |
| `¿Sobre qué pedido? Indicá el requerimiento (por ejemplo req_01) o fijalo con /pedido…` | **Pedido sin especificar.** El sistema nunca asume `req_01` | Escribí el pedido en la consulta, usá `--pedido req_01` o `/pedido req_01` en la consola, o mandá `requerimiento_id` en la API |
| `No existe el pedido req_99. Los pedidos cargados son: …` | Ese pedido no está en el grafo | Usá uno de los que lista el mensaje |
| `No encontré Notebook_Z en el catálogo. Modelos disponibles: …` | El modelo no existe | Usá un modelo de la lista (`Notebook_A`, `Notebook_G`…). Podés escribir «la G» |
| `¿De qué notebook? Indicá el modelo…` o `Para comparar necesito 2 o 3 modelos…` | La consulta pide algo sobre una notebook y no dice cuál | Nombrá el modelo o los modelos |
| `No entendí qué querés consultar. Por ejemplo: …` | El router no reconoció ninguna intención | Reformulá con una de las consultas de la sección 5 |
| `La consulta es muy larga…`, `No recibí ninguna consulta…` o `No pude entender la consulta: no tiene palabras…` | Entrada vacía, de más de 1500 caracteres o sin letras | Escribí una sola pregunta, más corta |
| `Cargar o aclarar un pedido nuevo todavía no está disponible…` | Registrar pedidos nuevos no está habilitado en esta versión | Consultá los pedidos que ya están cargados (`req_01`, `req_02`…) |
| La respuesta es una lista de datos con `Advertencia:` al final (`origen: plantilla_fija`) | El modelo no logró una redacción verificable | Es correcta, solo menos pulida. Probá reformular |
| Una respuesta nombra pocas notebooks | El texto del modelo se limita a unas 150 palabras | El detalle completo está en la traza (`evidencia`); pedí una notebook o un tema puntual |

### De la instalación

| Lo que ves | Causa | Qué hacer |
| --- | --- | --- |
| `Falta NEO4J_PASSWORD en el entorno (ver .env.example).` | No cargaste el `.env` en esta ventana | Corré el bloque de la sección 4.1 |
| Un traceback largo con `ServiceUnavailable` o `Couldn't connect to localhost:7687` en `cargar_grafo` o `verificar_grafo` | Neo4j apagado, o URI incorrecta | Iniciá Neo4j y revisá `NEO4J_URI` |
| Un traceback con `AuthError` o `Unauthorized` | La contraseña del `.env` no es la de la base | Corregí `NEO4J_PASSWORD` y volvé a cargar las variables |
| `verificar_grafo` da menos de `11/11 OK`, o el asistente no encuentra pedidos ni notebooks | El grafo no está cargado, o está a medias | Volvé a correr `python -m scripts.cargar_grafo` y luego `verificar_grafo` |
| `No module named 'asistente'` (o `scripts`) | Estás en otra carpeta | `cd` a la carpeta raíz del proyecto (la que tiene `requirements.txt`) |
| `No module named 'fastapi'` (o `neo4j`, `langchain_ollama`) | Falta activar el entorno virtual o instalar las dependencias | `.venv\Scripts\Activate.ps1` y `python -m pip install -r requirements.txt` |
| Al arrancar la API: `[Errno 10048] error while attempting to bind on address ('127.0.0.1', 8000)… solo se permite un uso de cada dirección de socket` | Hay otro programa usando el puerto 8000 | `uvicorn asistente.api:app --port 8001` (y usá ese puerto en las URL) |
| Las tildes salen rotas (`conexiÃ³n`) al llamar a la API desde PowerShell | Windows PowerShell 5.1 no interpreta bien el JSON en UTF-8 con `Invoke-RestMethod` | Usá la función `Consultar` de la sección 4.3, la consola o `/docs` |
| Al correr `python -m asistente.cli` con una tubería (`... \| python -m ...`) el primer renglón no se entiende | Windows PowerShell 5.1 le agrega una marca invisible (BOM) a lo que se envía por la tubería | No uses tuberías con la consola; escribí en el modo conversación |

---

## 9. Probar el sistema

No hace falta para usarlo, pero permite comprobar que todo funciona.

```powershell
python -m unittest
```

Sin Neo4j ni Ollama corre las pruebas que no los necesitan y **saltea** el resto (`s` en la salida). Al 13/11/2026 son 197 pruebas, con 29 salteadas. Pueden salir mensajes de conexión rechazada: son de una prueba que simula a propósito un Neo4j caído, no son un error. Con las variables del `.env` cargadas y el grafo en Neo4j, corren también las que consultan la base. Las que usan el modelo se activan aparte, y son lentas:

```powershell
$env:PG3_TEST_LLM = "1"
python -m unittest tests.test_router tests.test_explicador
```

Los resultados de los casos E2E, con la entrada, el plan, el Cypher, la evidencia y la respuesta de cada uno, van a [`docs/pruebas/`](pruebas/).

---

## 10. Dónde seguir

| Si querés… | Mirá |
| --- | --- |
| Entender cómo está armado el sistema | [`ARQUITECTURA.md`](ARQUITECTURA.md): componentes, flujo de una consulta y contrato de los submódulos |
| Saber qué técnicas y herramientas se pueden usar | [`RESTRICCIONES.md`](RESTRICCIONES.md) |
| Ver las decisiones del grupo | [`INCONSISTENCIAS_CONTEXTOS.md`](INCONSISTENCIAS_CONTEXTOS.md) (D-01 a D-13) |
| Ver los cambios y arreglos que se hicieron | [`CORRECCIONES.md`](CORRECCIONES.md) |
| Leer el resultado de las pruebas | [`pruebas/`](pruebas/) |
| Ver qué se hizo en cada sesión de trabajo | [`sesiones/`](sesiones/) |

---

## 11. Linux y macOS

El sistema es el mismo; cambian los comandos de la terminal. Python es `python3` en la mayoría de los sistemas.

| Qué | PowerShell (Windows) | Bash o zsh (Linux, macOS) |
| --- | --- | --- |
| Crear y activar el entorno | `python -m venv .venv` y `.venv\Scripts\Activate.ps1` | `python3 -m venv .venv` y `source .venv/bin/activate` |
| Copiar el `.env` | `Copy-Item .env.example .env` | `cp .env.example .env` |
| Cargar el `.env` en la terminal | El bloque de la sección 4.1 | `set -a; source .env; set +a` |
| Una variable puntual | `$env:PG3_TEST_LLM = "1"` | `export PG3_TEST_LLM=1` |
| Consultar la API | La función `Consultar` | `curl -s http://localhost:8000/consultar -H "Content-Type: application/json" -d '{"texto": "Para req_01, ¿qué notebook me recomendás?", "requerimiento_id": "req_01"}'` |
| Ver la última traza | El comando de la sección 7 | `tail -n 1 trazas/AAAA-MM-DD.jsonl \| python3 -m json.tool --no-ensure-ascii` |

El resto (`python -m scripts.cargar_grafo`, `python -m scripts.verificar_grafo`, `python -m asistente.cli …`, `uvicorn asistente.api:app`, `ollama pull qwen2.5:3b`) es idéntico. Ollama y Neo4j se instalan desde sus sitios para cada sistema.
