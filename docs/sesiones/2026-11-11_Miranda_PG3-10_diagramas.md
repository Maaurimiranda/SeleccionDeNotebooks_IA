# Diagramas de arquitectura, secuencia y grafo · Miranda · 2026-11-11 · PG3-10

## En tres líneas
Se hicieron los tres diagramas del ítem **b) Diagramas** del ZIP (arquitectura, secuencia de una consulta y ontología del grafo), cada uno como `.drawio` editable y como `.png` en A4 apaisada, más un README con la función de cada componente. Están basados en el código y en `cypher/`, no en el borrador de `ARQUITECTURA.md`. Quedan listos para el informe (PG3-14) y el ZIP (PG3-18); falta la captura de Neo4j Browser, que es opcional.

## Qué cambió
| Archivo | Qué tiene ahora |
| --- | --- |
| [`docs/diagramas/arquitectura.drawio`](../diagramas/arquitectura.drawio) y [`.png`](../diagramas/arquitectura.png) | Los 7 elementos de la consigna §3.3 (usuario, interfaz, LLM, orquestación, base de conocimiento, módulos de razonamiento y fuentes), numerados y con color |
| [`docs/diagramas/secuencia_consulta.drawio`](../diagramas/secuencia_consulta.drawio) y [`.png`](../diagramas/secuencia_consulta.png) | Los 8 participantes de `ARQUITECTURA.md` §3 con el ejemplo E2E-1 sobre `req_01` |
| [`docs/diagramas/grafo.drawio`](../diagramas/grafo.drawio) y [`.png`](../diagramas/grafo.png) | 22 labels de Neo4j en cinco capas y sus relaciones, con una nota de lo que no se dibujó |
| [`docs/diagramas/README.md`](../diagramas/README.md) | La tabla «función de cada componente» (consigna §3.3), los pasos de la secuencia y la tabla de relaciones |

## Cómo funciona (para alguien que no estuvo)
**Qué pide la consigna.** La §3.3 pide un diagrama de la arquitectura con siete elementos y que se explique la función de cada componente. Cada elemento lleva un número y un color en el dibujo, y el README tiene una fila por componente con su archivo.

**Cómo se hicieron.** El issue pedía Diagrams.net (draw.io), que está en la lista verde de `RESTRICCIONES.md`. Esta sesión no tenía draw.io instalado, así que:

1. Se escribió un pequeño generador (fuera del repo) que a partir de una misma descripción de cajas y flechas produce **dos cosas**: el `.drawio` (XML de mxGraph, el formato nativo de diagrams.net) y el `.png` (dibujado con `matplotlib`, que está en la lista verde).
2. Se abrieron los tres `.drawio` en el visor de diagrams.net y se vio que se cargan y se dibujan igual que el PNG.
3. De ahora en adelante **el `.drawio` es la fuente**: se edita en diagrams.net y se reexporta el PNG desde ahí (pasos en el README de la carpeta).

**Qué se tomó del código.** Los nombres salen de `asistente/orquestador.py`, `router.py`, `explicador.py`, `llm.py`, `grafo.py`, `traza.py`, `api.py`, `cli.py` y los cinco paquetes de `asistente/submodulos/`. Un ejemplo: el orquestador llama a `grafo.catalogo()` y `grafo.pedidos()` antes de pedir el plan, y eso **no estaba** en el diagrama de `ARQUITECTURA.md` §3. Se agregó.

**El ejemplo de la secuencia.** La consulta es la de E2E-1 (`PG3-11`): «Para req_01, ¿qué notebook me recomendás? ¿Cómo andan de RAM y de gráfica?». El plan tiene tres intenciones (`SM4.recomendar`, `SM2.riesgo_ram`, `SM3.buscar`) y el orquestador suma `SM1.interpretacion_pedido`: son las cuatro vueltas del `loop`. Los resultados de cada vuelta (A con 0,785 en el puesto 1, G con riesgo de RAM [49,58 ; 81,46], etc.) salen de `tests/fixtures/`, que son filas reales del grafo.

**El grafo.** Las relaciones se comprobaron contra los patrones `(a)-[:REL]->(b)` de `cypher/*.cypher` con un script descartable: cada flecha dibujada existe con ese origen y destino. Por ejemplo, `SALIDA_PI2` va de `Notebook` a `Perfil` (adecuación de rendimiento y grado de pantalla por perfil) y `ACTIVA` va de `Evaluacion` y `Lectura` a `Regla`, con la `fuerza` como propiedad.

## Decisiones y por qué
| Decisión | Motivo | Alternativa descartada |
| --- | --- | --- |
| Escribir el XML de `.drawio` a mano (con un generador) | Es el formato editable que pide el issue y no hace falta instalar nada | Dibujar en draw.io: no estaba disponible en la sesión |
| PNG con `matplotlib` | Está en la lista verde y permite dibujar el mismo modelo | SVG a mano o Mermaid: no son editables en diagrams.net. Se dejó Mermaid solo donde ya estaba, en `ARQUITECTURA.md` |
| Lienzo A4 apaisado de 1169 × 827 px, PNG a 2922 × 2067 | La consigna pide que se lea bien en A4 apaisada: una fuente de 10 px sale de 7,2 pt en la hoja | PNG más chico: se pierde el texto de las cajas |
| El ejemplo usa un plan **esperado** y no una corrida | No se corrió Ollama en esta sesión; inventar una traza sería falso | Esperar a PG3-11 para usar la traza real |
| Se dibujan 22 labels y el resto va en una nota | Con todos los labels el diagrama no se lee en A4 | Un diagrama por capa: se pierde la vista general |
| No se tocó `ARQUITECTURA.md` | La tarea solo agrega `docs/diagramas/`; cambiar un documento común pide PR revisado | Reemplazar sus Mermaid por los PNG: conviene decidirlo aparte |

## Cómo probarlo
1. Abrir `docs/diagramas/arquitectura.drawio` en https://app.diagrams.net y comprobar que tiene 46 elementos y 13 flechas pegadas a las cajas.
2. Mirar los tres `.png` a pantalla completa o imprimir uno en A4 apaisada: todo el texto se lee.
3. Contar en `arquitectura.png` los 7 elementos de la consigna §3.3 (la leyenda de la izquierda los numera).
4. Si se edita un `.drawio`: **Archivo → Exportar como → PNG** (zoom 250 %) y reemplazar el `.png`.

## Qué queda y dudas
- **Verificado:** los tres `.drawio` son XML bien formado (ids únicos, padres y extremos de flecha existentes) y se abren y dibujan bien en el visor de diagrams.net; las relaciones del grafo coinciden con `cypher/`; la proporción de los PNG es la de una A4 apaisada (1,414).
- **No verificado:** que los `.drawio` abran en la **aplicación de escritorio** de draw.io (solo se probó el visor web); que los PNG **impresos** en papel se lean bien (se calculó el tamaño de fuente, no se imprimió); que el plan del ejemplo sea el que da `qwen2.5:3b` (cuando exista la traza de E2E-1 en `docs/pruebas/`, conviene comparar).
- **No hecho:** la captura de Neo4j Browser que sugiere el issue como complemento: pide el grafo cargado y credenciales, y no se tocó ninguna.
- **Para el grupo:** (1) el PNG actual no es una exportación de draw.io; si se prefiere que lo sea, alguien lo reexporta en 2 minutos. (2) Falta enlazar los diagramas desde `ARQUITECTURA.md` §2 y §3: se puede hacer en otro PR. (3) Si PG3-21 (pedido nuevo con escritura) entra, la flecha de SM1 a Neo4j pasa a ser también de escritura y hay que actualizar el dibujo.
