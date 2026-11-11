# Casos de uso integrados (consigna §3.4)

Cada caso involucra **al menos dos submódulos distintos** además de SM1, que el orquestador agrega siempre que hay un pedido. Los datos salen de las corridas reales de `scripts/correr_e2e.py`; el detalle de cada una está en `E2E-n.md`.

## Caso 1 · E2E-1

**Consulta:** «Para req_01, ¿qué notebook me recomendás? ¿Cómo andan de RAM y de gráfica?»

**Situación.** Un asesor atiende el pedido req_01 (presupuesto 1000 USD, perfil de virtualización) y quiere una recomendación, con el riesgo de RAM y la gráfica de las candidatas.

**Información usada.** Submódulos del plan: SM2, SM4 (más SM1 para el pedido). Intenciones: `SM4.recomendar`, `SM2.riesgo_ram`. Consultas Cypher ejecutadas: 6.

**Razonamiento.** SM4 ordena con REC-R8 (grado de recomendación y desempate por ampliabilidad de la RAM); SM2 calcula el riesgo de RAM con sus reglas difusas; SM3 aporta la gráfica y la movilidad. Las excluyentes (REC-R3) descartan a E y a C, y el dato faltante (REC-R15) deja a M condicionada.

**Resultado.** Al menos dos submódulos distintos pedidos en el plan (sin L1) → sí; Ranking: A puesto 1, H puesto 2, B puesto 3 → sí; Grado de A = 0,785 → sí; X queda fuera de presupuesto → sí; M condicionada, E y C descartadas, G indeterminada → sí.

**Explicación generada.**

> Te recomiendo la Notebook_A. La RAM es ampliable y el riesgo de que quede corta es bajo. La gráfica tiene un TGP de 60W, que no afecta el rendimiento.
> Los parametros difusos y los umbrales del sistema estan sin validar por el tecnico: los grados y riesgos son una referencia, no una certeza.

_Origen: llm · 15.456 s · [detalle](E2E-1.md)_

## Caso 2 · E2E-2

**Consulta:** «En req_01, ¿por qué la M quedó condicionada y la G indeterminada? ¿Qué riesgo de RAM tiene la G?»

**Situación.** El asesor ve en la lista a la M «condicionada» y a la G «indeterminada» y no entiende por qué.

**Información usada.** Submódulos del plan: SM2, SM4 (más SM1 para el pedido). Intenciones: `SM4.explicar_notebook`, `SM4.explicar_notebook`, `SM2.riesgo_ram`. Consultas Cypher ejecutadas: 4.

**Razonamiento.** M no informa la autonomía: REC-R15 deja su grado como rango en vez de inventar un valor. G no informa si la CPU soporta virtualización ni si la RAM es ampliable: el grafo no puede decidir y el estado es indeterminado. SM2 informa el riesgo de RAM de G como rango, por la misma falta de dato.

**Resultado.** Al menos dos submódulos distintos pedidos en el plan (sin L1) → sí; M condicionada, grado [0,504 ; 0,826], falta la autonomía → sí; G indeterminada con las alertas REN-R10 y FZ-R7 → sí; Riesgo de RAM de G como rango [49,58 ; 81,46] (SM2) → sí.

**Explicación generada.**

> La M quedó condicionada por falta de informacion sobre autonomia, la G es indeterminada por falta de informacion sobre si la CPU soporta virtualización. La G tiene riesgo alto de quedarse corta de RAM.
> Los parametros difusos y los umbrales del sistema estan sin validar por el tecnico: los grados y riesgos son una referencia, no una certeza.

_Origen: llm · 4.974 s · [detalle](E2E-2.md)_

## Caso 3 · E2E-5

**Consulta:** «En req_01, la E tiene casi el mismo puntaje que la B y la H, ¿por qué no la recomiendan? ¿Qué pasa con la virtualización?»

**Situación.** El asesor ve que la E puntúa igual que la B y la H y se pregunta por qué no entra en la recomendación.

**Información usada.** Submódulos del plan: SM2, SM4 (más SM1 para el pedido). Intenciones: `SM4.comparar`, `SM2.virtualizacion`. Consultas Cypher ejecutadas: 5.

**Razonamiento.** El puntaje no alcanza: la virtualización es un requisito excluyente del perfil (REC-R3) y la CPU de la E no la soporta, así que queda descartada aunque su adecuación global sea ≈ 0,81. SM2 confirma la virtualización por hardware.

**Resultado.** Al menos dos submódulos distintos pedidos en el plan (sin L1) → sí; E ≈ 0,81, B = 0,813 y H = 0,811 → sí; E Descartada (excluyente incumplido) por REC-R3 → sí; B y H siguen recomendadas → sí.

**Explicación generada.**

> La E no la recomiendan porque no soporta virtualización por hardware, requisito excluyente para el perfil VIRT. La virtualización CPU de B y H es soportada, pero la E no cumple.
> Los parametros difusos y los umbrales del sistema estan sin validar por el tecnico: los grados y riesgos son una referencia, no una certeza.

_Origen: llm · 4.023 s · [detalle](E2E-5.md)_

## Caso 4 · E2E-9

**Consulta:** «En req_01, ¿qué reglas se activaron para la A, de dónde sale cada dato y qué riesgo de RAM tiene?»

**Situación.** Un auditor pide reconstruir cómo llegó el sistema al resultado de la A: reglas, fuente de los datos y riesgo de RAM (consigna §3.7).

**Información usada.** Submódulos del plan: GRUPO, SM2 (más SM1 para el pedido). Intenciones: `GRUPO.traza_reglas`, `SM2.riesgo_ram`. Consultas Cypher ejecutadas: 6.

**Razonamiento.** GRUPO.traza_reglas devuelve las 18 reglas activadas de los cuatro submódulos con su fuerza y, para 14 de ellas, los parámetros que las respaldan. Las 4 restantes salen «no registrada»: el grafo no guarda su fuente. SM2 informa el riesgo de RAM de la A.

**Resultado.** Al menos dos submódulos distintos pedidos en el plan (sin L1) → sí; Traza de A: reglas de los 4 submódulos, 18 reglas, 14 con origen y 4 «no registrada» → sí; La notebook trae la fuente del precio y de la autonomía → sí; Riesgo de RAM de A, tal cual lo da el grafo (SM2) → sí.

**Explicación generada.**

> Para la A, se activaron las reglas FZ-R2, FZ-R4 y FZ-R5. Los datos vienen de la evaluación del grupo (PI3). La RAM tiene un riesgo de 23.02, que es bajo.
> Los parametros difusos y los umbrales del sistema estan sin validar por el tecnico: los grados y riesgos son una referencia, no una certeza.

_Origen: llm · 4.262 s · [detalle](E2E-9.md)_

## Caso 5 · E2E-10

**Consulta:** «Para req_01, ¿cuáles son las mejores en movilidad y cómo queda el costo-beneficio?»

**Situación.** El asesor quiere las más portables del pedido y cuál rinde más por su precio.

**Información usada.** Submódulos del plan: SM3, SM4 (más SM1 para el pedido). Intenciones: `SM4.costo_beneficio`, `SM3.buscar`. Consultas Cypher ejecutadas: 3.

**Razonamiento.** SM3 ordena por la adecuación de movilidad (peso y autonomía) y deja los datos faltantes al final; SM4 ordena por el índice costo-beneficio de REC-R9 (adecuación global sobre precio).

**Resultado.** Al menos dos submódulos distintos pedidos en el plan (sin L1) → sí; SM3: orden por movilidad descendente, con los datos faltantes al final y sin números inventados → sí; SM4: costo-beneficio de Q7 (B 1,161; A 0,907) → sí.

**Explicación generada.**

> Vos te conviene la Notebook_A, está recomendada (Alta) en movilidad. El costo-beneficio está en 0.907.
> Los parametros difusos y los umbrales del sistema estan sin validar por el tecnico: los grados y riesgos son una referencia, no una certeza.

_Origen: llm · 4.142 s · [detalle](E2E-10.md)_

## Controles

No cuentan como casos integrales: no cruzan información entre submódulos.

- **E2E-3** · «Para req_02, ¿qué notebook me conviene?» → APRUEBA. El asesor pregunta por req_02, un pedido al que todavía le falta una respuesta del comprador. El perfil de req_02 es indeterminado y no tiene evaluaciones: el sistema no completa un perfil (no asume oficina), pide responder la pregunta pendiente y no recomienda. ([detalle](E2E-3.md))
- **E2E-8** · «¿Cuál es la capital de Francia?» → APRUEBA. Una pregunta que no tiene que ver con notebooks. El router la marca fuera de alcance y el sistema responde con un mensaje fijo, sin ejecutar ninguna consulta de submódulo ni llamar al explicador. ([detalle](E2E-8.md))
