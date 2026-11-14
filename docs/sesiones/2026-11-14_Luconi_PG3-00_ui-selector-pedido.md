# Selector de pedido en la interfaz web · Luconi · 2026-11-14 · PG3-00

## En tres líneas
En `/ui`, si la consulta no nombraba un pedido y el campo «Pedido» quedaba vacío, el asistente respondía «¿Sobre qué pedido?». Ahora la página muestra los tres pedidos cargados (req_01, req_02 y req_03) con lo que pidió cada comprador, y req_01 queda elegido por defecto. Solo cambia `asistente/web/index.html`; la API y Swagger quedan igual.

## Qué cambió
| Archivo | Qué tiene ahora |
| --- | --- |
| [`asistente/web/index.html`](../../asistente/web/index.html) | Tres tarjetas para elegir el pedido (en lugar del campo de texto), un texto que explica que el asistente razona sobre pedidos ya cargados, y los ejemplos que nombran un pedido lo eligen solos |

## Cómo funciona (para alguien que no estuvo)
El grafo tiene tres pedidos de compra (`Requerimiento`) cargados en [`cypher/02_instancias.cypher`](../../cypher/02_instancias.cypher). Los grados, rankings y alertas de cada pedido se calculan con Cypher cuando se carga la base (bloques 9 y 10). Por eso el asistente no puede responder sobre un pedido que no existe: no hay `Evaluacion` para él. La página ahora siempre manda un `requerimiento_id` a `POST /consultar`, el que esté elegido. Si el texto nombra otro pedido, el router usa el del texto (como antes).

Ejemplo: «¿Qué notebook me recomendás para programar y jugar al Valorant?» con req_01 elegido responde el ranking de req_01 (programar, máquinas virtuales y Stardew Valley, 1000 USD). La tarjeta muestra ese texto para que quede claro sobre qué caso se razona.

## Decisiones y por qué
- **Selector en la página, no un pedido nuevo.** Crear un pedido a partir de la consulta (que el LLM extraiga presupuesto y actividades, se escriba en Neo4j y se recalculen SM1 a SM4) es el paso natural, pero toca los archivos de los cuatro, convierte la base en escritura durante la consulta y no se podía probar contra Neo4j antes de la defensa. Queda como trabajo futuro.
- **Descartado: elegir solo el pedido «más parecido».** Cambia el router y podría responder el caso de otra persona sin que se note.
- **Los textos de los pedidos están copiados en el HTML** solo para mostrarlos. Si cambia `02_instancias.cypher`, hay que actualizar la constante `PEDIDOS`.

## Cómo probarlo
```bash
uvicorn asistente.api:app      # abrir http://localhost:8000/ui
python -m unittest discover -s tests -t .
```
Escribir una pregunta sin nombrar pedido: tiene que responder sobre el pedido elegido, no pedir aclaración.

## Qué queda y dudas
- Probado con Chromium y un orquestador de prueba (el cuerpo enviado lleva `requerimiento_id`), no contra Neo4j y Ollama reales.
- Registrar pedidos nuevos desde la consulta: ver la decisión de arriba.
