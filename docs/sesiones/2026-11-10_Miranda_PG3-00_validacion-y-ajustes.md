# Validación contra la consigna y ajustes del plan · Miranda · 2026-11-10 · PG3-00

## En tres líneas
- Se comparó `ConsignaPG3` con los 27 issues, el plan y la arquitectura, y otra vez después del PR #4 de de Coninck (PG3-00 a 09 en `main`). La cobertura formal está completa, pero había **brechas reales**.
- Se corrigieron en el plan: un issue nuevo (**PG3-05**), dos casos integrales más (E2E-9 y E2E-10), una **compuerta** para el pedido nuevo (PG3-21) y varias dependencias.
- No se tocó código. Se verificó que los 78 tests offline del PR #4 pasan; lo que necesita Neo4j u Ollama no se pudo correr.

## Qué cambió
| Archivo | Qué tiene ahora |
| --- | --- |
| [`docs/plan/PLAN_PG3.md`](../plan/PLAN_PG3.md) | Estado del 10/11, hitos con la compuerta, carga restante por persona (~25 h), dependencias, cobertura de la consigna y lista de issues con ✅ |
| [`docs/plan/issues/PG3-05.md`](../plan/issues/PG3-05.md) | **Nuevo:** conteos del grafo (lo que faltaba a PG3-02), fuente del conocimiento en la traza (lo que faltaba a PG3-04) y revisión del PR #4 |
| [`PG3-11`](../plan/issues/PG3-11.md) | E2E-9 y E2E-10, E2E-3 y E2E-8 como controles, 4 h, y la medición de tiempos |
| [`PG3-21`](../plan/issues/PG3-21.md) | Condicional con compuerta, 5 h, y el estado real del código (qué hay que tocar) |
| [`PG3-02`](../plan/issues/PG3-02.md), [`04`](../plan/issues/PG3-04.md), [`09`](../plan/issues/PG3-09.md), [`14`](../plan/issues/PG3-14.md), [`15`](../plan/issues/PG3-15.md), [`16`](../plan/issues/PG3-16.md), [`18`](../plan/issues/PG3-18.md) | Seguimientos, dependencias que faltaban y la regla del ítem l) |
| [`docs/ARQUITECTURA.md`](../ARQUITECTURA.md) | §8 (dónde está la fuente de verdad), §7 (los E2E) y §9 (PG3-21 condicional) |

## Qué se encontró (para alguien que no estuvo)
1. **Solo 3 de los 5 casos «integrales» cruzaban submódulos.** E2E-3 usa solo SM1 y E2E-8 no usa ninguno. La consigna pide ≥ 5 casos y ≥ 3 E2E que involucren varios submódulos. Se agregaron E2E-9 (traza de reglas + riesgo de RAM + explicación de A) y E2E-10 (movilidad + costo-beneficio). E2E-3 y E2E-8 quedan como controles.
2. **La fuente de una regla no existe en el grafo.** `GRUPO.traza_reglas` pide `q.fuente`, pero ninguna `:Regla` la tiene: los 20 valores del fixture con filas reales son `null`. El origen está en `Parametro.origen`, `EtiquetaDifusa.fuente`, `Notebook.fuente_precio` y `Bateria.fuente`. Sin arreglo, el ejemplo de trazabilidad (§3.7) quedaría sin fuente.
3. **El orquestador agrega siempre L1 (SM1).** Por eso `submodulos_consultados` incluye SM1 en cualquier consulta con pedido. No se cuenta como cruce: cada caso integral tiene que pedir ≥ 2 intenciones de submódulos distintos.
4. **No hay inferencia en vivo en el nivel 1.** Las reglas y el difuso corren al cargar el grafo. Solo PG3-21 la muestra.
5. **PG3-21 estaba agendado después del congelamiento** del jueves 22:00, que no deja entrar cambios de ese tamaño.
6. **PG3-05** no existe en el repositorio: el número se saltó al armar el plan y no hay rastro de por qué. Se usó para cerrar los puntos 2 y la tabla de conteos de PG3-02.
7. **Proceso:** el PR #4 se abrió y se unió por la misma persona, sin revisión, y cambió `contrato.py`, `CLAUDE.md` y D-05 (LangChain). Eso se revisa en PG3-05.

## Decisiones y por qué
- **Arquitectura B:** la misma de `ARQUITECTURA.md`, con PG3-21 condicional. Es lo más barato que permite demostrar inferencia en vivo sin poner en riesgo la entrega.
- **Compuerta, no fecha:** se decide cuando PG3-12 y PG3-13 estén en `main`, y termina a más tardar el jueves a las 13:00.
- **Sin fuentes inventadas:** lo que el grafo no tiene sale como «no registrada» y el informe lo cuenta como limitación.
- **SM3:** se acepta que la X aparezca con 0,74 al filtrar por `dedicada`. Sin filtro, el límite de 5 la deja afuera; se anotó en PG3-09.

## Qué pasa con lo ya hecho (PG3-00 a 09)
| Decisión | Efecto sobre lo hecho |
| --- | --- |
| Compuerta de PG3-21 | `contrato.py` ya declara `SM1.registrar_pedido` y `aclarar_pedido`, y `Grafo.escribir` ya existe: **sin cambios de contrato**. Sí hay que tocar `cypher/` (ningún archivo usa `$req` hoy), `cargar_grafo.py` (que no pasa parámetros) y el rechazo de nivel 2 en `router.validar` |
| Capas controlador → servicio → repositorio | Compatibles: el Cypher de escritura va en `sm1/repositorio.py` y `test_estructura.py` ya vigila que el servicio no tenga Cypher |
| LangChain como cliente | Compatible: `registrar_pedido` usa `LLM.json`. Revertirlo implicaría rehacer `llm.py`, `orquestador.py` y los tests; no se propone |
| PG3-05 | Cambia `grupo/repositorio.py` y `servicio.py` y obliga a regenerar `tests/fixtures/GRUPO.*`. No toca SM1, SM2 ni SM3 |
| E2E-9 y E2E-10 | Usan intenciones que ya existen; solo se suman consultas al CSV del router y se vuelve a medir el acierto |

Lo que **no** conviene cambiar a esta altura: `contrato.py`, la forma de los cinco paquetes o el stack del LLM, porque invalidaría los 78 tests y los fixtures.

## Cómo revisarlo
```bash
git diff --stat main -- docs/
```
Leer `PLAN_PG3.md` §2 (compuerta) y §8, y los issues PG3-05, PG3-11 y PG3-21.

## Qué queda y dudas
- **Miranda:** confirmar la arquitectura B y la excepción de `langchain-ollama` en `RESTRICCIONES.md` §8, y revisar `contrato.py` (PG3-05).
- **Sin verificar:** CP1–CP11 (11/11) y el 96 % de acierto del router son lo que reporta de Coninck; no se corrieron acá por falta de Neo4j y Ollama.
- **Riesgo:** el plan tarda entre 10 y 50 s con `qwen2.5:3b` en una máquina y el explicador suma otra llamada. Hay que medir en las demás antes del video.
- **Luconi** concentra SM4, el explicador y el PDF (9,5 h): conviene mirar su avance el miércoles al mediodía.
- Nada quedó commiteado: los cambios están en el árbol de trabajo.
