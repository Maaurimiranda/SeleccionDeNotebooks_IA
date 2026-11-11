# 10. Trazabilidad del conocimiento

La consigna (§3.7) pide poder reconstruir, para una conclusión del sistema, cinco cosas: la fuente del conocimiento, la regla, la evidencia, la consulta y la explicación. Esta sección explica dónde queda cada una y lo demuestra con **un ejemplo real reconstruido de punta a punta**, el E2E-9, con sus límites a la vista.

## 10.1 Dónde queda cada eslabón

| Eslabón | Dónde se encuentra |
| --- | --- |
| **Fuente** | En el grafo: `Parametro.origen` (incluidos los `centros_y_sigmas_<variable>` que respaldan cada regla difusa), `EtiquetaDifusa.fuente`, `Juego.fuente`, `Notebook.fuente_precio` y `Bateria.fuente`, más las consultas pendientes al técnico (`ConsultaExperto`). El submódulo GRUPO las expone con `GRUPO.origen_reglas` y `GRUPO.origen_notebook`. Lo que el grafo no tiene sale como «no registrada», sin inventar nada |
| **Regla** | Cada regla es un nodo `Regla`, y cada activación, una relación `[:ACTIVA {fuerza}]`. La consulta `GRUPO.L3` las devuelve para una notebook en un pedido |
| **Evidencia** | La evidencia común que recibe el explicador, guardada completa en la traza |
| **Consulta** | El Cypher fijo con sus parámetros, las filas que devolvió y su duración, en la traza |
| **Explicación** | La respuesta final y cada intento del verificador con los problemas que encontró, en la traza |

La traza es una línea JSON por consulta del usuario. Las de los E2E están en `docs/pruebas/trazas/2026-11-11.jsonl`, y `docs/pruebas/E2E-n.md` las presenta paso a paso.

## 10.2 Ejemplo reconstruido: E2E-9

**Consulta del asesor:** «En req_01, ¿qué reglas se activaron para la A, de dónde sale cada dato y qué riesgo de RAM tiene?» (corrida del 11/11/2026, 4,3 s, detalle en `docs/pruebas/E2E-9.md`).

### Paso 1 · El plan del router

El LLM devolvió un plan con dos intenciones, y el orquestador agregó `SM1.interpretacion_pedido`:

```json
{"requerimiento_id": "req_01",
 "consultas": [
   {"intencion": "GRUPO.traza_reglas", "parametros": {"modelo": "Notebook_A"}},
   {"intencion": "SM2.riesgo_ram", "parametros": {"modelos": ["Notebook_A"]}}]}
```

La validación anotó una observación: descartó un fragmento por no ser literal (el texto dice «la A» y el plan escribió «Notebook_A»). El plan siguió siendo válido. Es el tipo de detalle que la traza deja ver y que una respuesta sola esconde.

### Paso 2 · Las consultas ejecutadas

Seis consultas Cypher fijas, todas de solo lectura: `SM1.L1` (el pedido), `GRUPO.existe_evaluacion`, `GRUPO.L3` (las reglas activadas, 20 filas), `GRUPO.origen_reglas` (19 filas), `GRUPO.origen_notebook` y `SM2.C2` (el riesgo de RAM, 1 fila, 12 ms). La L3, abreviada y con saltos de línea para el informe, es así:

```cypher
MATCH (c:Requerimiento {id:$requerimiento_id})-[:EVALUA]->(ev:Evaluacion)
      -[:SOBRE]->(n:Notebook {modelo:$modelo})
OPTIONAL MATCH (c)-[:INCLUYE]->(a:Actividad)
WITH c, ev, n, collect(a) AS acts
UNWIND [c, ev, n] + acts AS origen
OPTIONAL MATCH (origen)-[:TIENE_LECTURA*0..1]->(x)-[act:ACTIVA]->(q:Regla)
RETURN q.submodulo AS submodulo, q.id AS regla, q.tipo AS tipo, act.fuerza AS fuerza,
       q.estado_validacion AS validacion  // y el antecedente y el consecuente
```

Los parámetros son `{"requerimiento_id": "req_01", "modelo": "Notebook_A"}`. Las 20 filas que devuelve se agrupan en **18 reglas distintas de los cuatro submódulos**: 5 de SM1, 3 de SM2, 3 de SM3 y 7 de SM4. El texto exacto de cada consulta y sus primeras filas están en `docs/pruebas/E2E-9.md`.

### Paso 3 · La regla

Tomamos una de las tres reglas de SM2 que activó la A, la **FZ-R4** (difusa, Mamdani, `sin validar`):

> `MIN(S.justa, MAX(A.media, A.mucha))` → `riesgo_obsolescencia = bajo`

Es decir: si la RAM es justa para el perfil y la ampliabilidad es media o mucha, el riesgo es bajo. Para la A, con 16 GB de RAM mixta y ampliable, ρ = 1,0 (la RAM iguala al mínimo del perfil de virtualización) y un índice de ampliabilidad de 0,75, la FZ-R4 se activó con **fuerza 0,458**. La FZ-R2 y la FZ-R5 también, pero casi sin peso (0,044 cada una). La agregación y el centroide dan un riesgo de **23,02** sobre 100, etiqueta `bajo`.

### Paso 4 · La fuente

Desde la regla se llega a su origen por el parámetro que la respalda (consulta `GRUPO.origen_reglas`):

| Eslabón de la cadena | Valor en el grafo |
| --- | --- |
| Regla | `FZ-R4`, consecuente `riesgo_obsolescencia` |
| Parámetro | `centros_y_sigmas_riesgo_obsolescencia` |
| Origen | «Decision de diseno del grupo (PI3)» |
| Estado de validación | `sin validar` |
| Consulta al técnico | `CE-riesgo_obsolescencia`, estado `pendiente` |

Los datos de la notebook, en cambio, sí tienen fuente externa (`GRUPO.origen_notebook`): el precio sale de «Mercado Libre Argentina y tiendas oficiales, 01/10/2026» y la autonomía, de «Notebookcheck / RTINGS».

### Paso 5 · La evidencia

El explicador no vio el grafo: recibió una evidencia común de **5434 caracteres** con el pedido (perfil dominante VIRT, grado 0,899; GAM 0,313), la traza de reglas con su origen, el riesgo de RAM de la A (23,02, `bajo`, con sus tres reglas) y la advertencia de que los parámetros están sin validar. Por el poco contexto del modelo, la lista de reglas se compactó: el LLM vio 12 de las 18 y la marca `_omitidas: 6`. La evidencia incluye además `reglas_sin_origen`: GM-R3, INT-R11, REC-R4 y REC-R9.

### Paso 6 · La explicación

El verificador aprobó la respuesta a la primera (origen `llm`):

> Para la A, se activaron las reglas FZ-R2, FZ-R4 y FZ-R5. Los datos vienen de la evaluación del grupo (PI3). La RAM tiene un riesgo de 23.02, que es bajo.
> Los parametros difusos y los umbrales del sistema estan sin validar por el tecnico: los grados y riesgos son una referencia, no una certeza.

Las cifras (23,02 y `bajo`) y las tres reglas citadas coinciden con la consulta `SM2.C2`. Pero la respuesta es **más pobre que su traza**: nombra 3 de las 18 reglas, resume el origen en una frase y no dice nada de las cuatro reglas sin origen ni de la fuente del precio y de la autonomía. Lo auditable es la traza, no el texto.

### Veredicto del E2E

El E2E-9 aprueba por lo que dice el grafo: la traza de la A tiene reglas de los 4 submódulos, 18 reglas, 14 con origen y 4 «no registrada» (GM-R3, INT-R11, REC-R4 y REC-R9); la notebook trae la fuente del precio y de la autonomía; y el riesgo de RAM es 23,02 `bajo`, tal cual lo da el grafo.

## 10.3 Cómo auditar una conclusión

Para una respuesta cualquiera, el camino es el inverso del ejemplo:

1. Se abre la traza de la consulta y se lee el **plan**: qué intenciones se pidieron y con qué parámetros.
2. Se leen las **consultas**: el Cypher, los parámetros y las filas devueltas. Cada cifra de la respuesta tiene que estar en esas filas.
3. Se mira la **evidencia** que recibió el explicador y los **intentos** del verificador: qué problemas encontró y cuántas veces regeneró.
4. Desde cada regla citada se sube a su **origen** con `GRUPO.origen_reglas`, y desde la notebook, a sus fuentes con `GRUPO.origen_notebook`.

Se puede repetir con la consola (`python -m asistente.cli --traza "..."`) o corriendo `python -m scripts.correr_e2e`, que reescribe `docs/pruebas/`.

## 10.4 Límites de la trazabilidad

Lo que el sistema **no** permite reconstruir hoy, dicho sin vueltas:

- **14 de las 18 reglas de la traza de la A tienen origen y 4 salen «no registrada»** (GM-R3, INT-R11, REC-R4 y REC-R9). El grafo canónico no guarda `fuente` en los nodos `Regla` y no tiene nodos de fuente.
- **El origen que se muestra es el de los parámetros, no el de la regla.** Se llega a él por el nombre del parámetro (`centros_y_sigmas_<variable>`) o porque el origen del parámetro menciona la regla. Es una cadena indirecta.
- **Ese origen es una decisión del grupo, no una cita.** Las seis entradas de origen de este ejemplo son «Decision de diseno del grupo (PI3)» o «Decision del grupo (REC-R5)», todas `sin validar`. El sistema puede decir que un parámetro lo decidió el grupo y que su validación está pendiente; **no puede** llevar de la regla a una ficha, a un manual o a la entrevista con el técnico. Los datos de catálogo (precio, autonomía) sí tienen fuente externa.
- **El texto de la respuesta no es evidencia.** Puede resumir mal o callar cosas, como en este ejemplo. La prueba es la traza.
- **Se reconstruyó un ejemplo, no todos.** La traza se guarda para cada consulta, pero la reconstrucción manual la hicimos para este caso. El E2E-9 se corrió una vez; el texto puede variar entre corridas, la evidencia no.
