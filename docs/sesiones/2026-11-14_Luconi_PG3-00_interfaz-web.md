# Interfaz web en /ui · Luconi · 2026-11-14 · PG3-00

## En tres líneas
Se agregó una página web en `http://localhost:8000/ui`, servida por la misma API, para mostrar en la defensa la consulta, las recomendaciones con sus grados y el razonamiento paso a paso. Swagger sigue en `/docs` igual que antes: la página usa el mismo `POST /consultar` y sus rutas no aparecen en el esquema OpenAPI. Está terminada y probada con un orquestador de prueba; falta probarla con Neo4j y Ollama reales.

## Qué cambió
| Archivo | Qué tiene ahora |
| --- | --- |
| [`asistente/web/index.html`](../../asistente/web/index.html) | La página entera: HTML, CSS y JavaScript del navegador en un solo archivo, sin build ni librerías externas |
| [`asistente/api.py`](../../asistente/api.py) | Dos rutas nuevas fuera de Swagger (`include_in_schema=False`): `GET /ui` devuelve la página y `GET /ui/ejemplo` devuelve la traza grabada con la forma de `/consultar`. La descripción de Swagger enlaza a `/ui` |
| [`tests/test_api.py`](../../tests/test_api.py) | Dos pruebas: `/ui` responde HTML y no está en `/openapi.json`; `/ui/ejemplo` tiene las mismas claves que `/consultar` |
| [`docs/RESTRICCIONES.md`](../RESTRICCIONES.md) §8 | Excepción propuesta para la página estática, pendiente de aprobación en el PR |
| [`README.md`](../../README.md) | Cómo abrir la interfaz |

## Cómo funciona (para alguien que no estuvo)
La página no calcula nada. Manda el texto a `POST /consultar` (igual que Swagger) y dibuja lo que vuelve:

1. **Respuesta** del asistente, con el origen (`llm`, `plantilla_fija`, `validacion`, `fuera_de_alcance`, `error`) y la advertencia de parámetros «sin validar».
2. **Cómo entendió el pedido (SM1)**: presupuesto, prioridad y la pertenencia difusa a cada perfil como barra (por ejemplo, req_01: VIRT 0,899 y GAM 0,313).
3. **Recomendaciones (SM4)**: el ranking en tarjetas (Notebook_A puesto 1 con grado 0,785), la alternativa fuera de presupuesto (Notebook_X, +5 %) y la tabla de no propuestas con la regla que las sacó (Notebook_E, `REC-R3`). Un grado que es rango, como el `[0,504 ; 0,826]` de la M, se dibuja como un tramo rayado: la incertidumbre no se promedia.
4. **Riesgo de RAM (SM2)**: el riesgo de 0 a 100 con las reglas difusas `FZ-R1..R5` que dispararon y su fuerza.
5. **Más evidencia**: cualquier otra intención (SM3, GRUPO, etc.) se muestra tal cual, como tabla o lista.
6. **Razonamiento paso a paso**: la traza en cinco pasos (plan del router, validación, cada consulta Cypher con sus filas y su tiempo, intentos del explicador aceptados o rechazados, respuesta final) y un botón para descargar la traza en JSON.

Arriba a la derecha hay dos indicadores que llaman a `GET /salud` (Neo4j y Ollama) y un enlace a Swagger.

## Decisiones y por qué
- **HTML estático sin frameworks**: RESTRICCIONES pone en rojo React, Vue, Streamlit y Gradio. Una página que solo llama a la API no agrega dependencias ni lógica, y no necesita `npm` ni build. Igual se registró en §8 para que el grupo la apruebe.
- **Rutas fuera del esquema** (`include_in_schema=False`): así `/openapi.json` sigue teniendo solo `/consultar` y `/salud` (lo verifica `test_openapi_documenta_los_dos_endpoints_con_ejemplos`).
- **Ejemplo grabado** (`/ui/ejemplo`): si en la defensa Ollama tarda o se cae, se puede mostrar la traza real de `datos/traza_ejemplo.jsonl`. La página aclara con un aviso que no es una consulta en vivo.
- **Sin recursos externos**: la página no carga nada de internet (ni fuentes ni CDN), así que anda sin conexión. Swagger, en cambio, baja su JS de un CDN.
- **Paleta** de la presentación de la defensa: berenjena `#241530`, frambuesa `#D6336C` y menta `#2FB397`.

## Cómo probarlo
```bash
uvicorn asistente.api:app
# abrir http://localhost:8000/ui  (Swagger sigue en http://localhost:8000/docs)
python -m unittest tests.test_api      # 6 pruebas, OK
```
Sin Neo4j ni Ollama, el botón «Ver ejemplo grabado» igual muestra todo.

## Qué queda y dudas
- No se probó contra Neo4j y Ollama reales (se probó con un orquestador que devuelve la traza de ejemplo, con Chromium).
- Las vistas propias son para `SM4.recomendar` y `SM2.riesgo_ram`; el resto de las intenciones se ve con el render genérico. Si alguna se usa mucho en la defensa, conviene darle vista propia.
- La excepción de §8 queda aprobada cuando Miranda apruebe el PR.
