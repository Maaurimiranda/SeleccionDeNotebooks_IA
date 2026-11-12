# 2. Resumen ejecutivo

**El problema.** Elegir una notebook obliga a traducir lo que el comprador necesita («programar, virtualizar y jugar a veces», «1000 USD») en requisitos de hardware y a compararlos contra fichas que suelen venir incompletas. Hoy lo resuelve un técnico por experiencia. Este trabajo vuelve ese criterio explícito, verificable y explicable para el **asesor de ventas**, que es quien usa el sistema.

**La solución.** Un único asistente con una sola entrada (API `POST /consultar` y consola) que responde en español. Cuatro submódulos comparten un grafo de conocimiento en Neo4j (343 nodos y 683 relaciones): SM1 interpreta el pedido, SM2 evalúa el riesgo de RAM y la virtualización, SM3 la gráfica y la movilidad, y SM4 recomienda con costo-beneficio. El razonamiento son 57 reglas (23 de ellas difusas, tipo Mamdani) escritas como consultas Cypher fijas.

**Cómo funciona.** El asesor escribe la consulta. Un router (LLM `qwen2.5:3b` local, temperatura 0) arma un plan JSON; Python lo valida; Neo4j ejecuta Cypher fijo de solo lectura; un explicador (LLM) redacta con esa evidencia y un verificador en Python revisa cifras, modelos y reglas antes de responder. Si no pasa, sale una plantilla fija.

**Principios.** Neo4j manda la verdad: el LLM interpreta y explica, pero no calcula, no decide ni escribe Cypher. La incertidumbre se conserva (rangos, `desconocida`, perfil indeterminado). Cada consulta deja una traza auditable.

**Ejemplo real (E2E-1, req_01: 1000 USD, perfil dominante virtualización con grado 0,899).** La A queda `Recomendada (Alta)` con grado 0,785, y la H y la B completan el podio por desempate de ampliabilidad. La X se ofrece aparte por pasarse del presupuesto. La E queda `Descartada (excluyente incumplido)` aunque puntúa ≈ 0,81, porque su CPU no soporta virtualización. La G queda `Indeterminada: completar informacion` y la M `Recomendada condicionada por falta de informacion` (grado [0,504 ; 0,826]).

| Medida (corridas del 11/11/2026) | Resultado |
| --- | --- |
| Regresión del grafo (CP1 a CP11) | 11 de 11 |
| Pruebas automáticas (`unittest`) | 193; offline (12/11) OK, con 29 salteadas que piden Neo4j u Ollama |
| E2E (5 integrales y 2 controles) | 7 de 7 aprueban; 4,3 a 7,1 s las que redacta el LLM (una máquina) |
| Router: intenciones / resultado final | 28 de 31 (90 %) / 30 de 31 (97 %) |
| Respuestas con explicación que salieron de la plantilla fija | 0 de 5 |

**Lo que falta, dicho sin vueltas.**
- Los parámetros difusos (centros, sigmas, mínimos de RAM) **no están validados por el técnico**: toda respuesta lo advierte.
- El asistente lee los resultados que el grafo ya calculó para 3 pedidos cargados: **no registra pedidos nuevos ni infiere en vivo**, y el nivel 2 (PG3-21 a 27) no está hecho.
- `qwen2.5:3b` redacta con torpezas que el verificador no siempre corta: en una respuesta (E2E-2) dio como riesgo de RAM de la G un número que era su adecuación global.
- Los tiempos de punta a punta se midieron en una sola máquina (en otra, el plan solo tardó de 10 a 50 s); el catálogo de prueba tiene 9 modelos.

**Grupo 2 · Comisión 5K09 · UTN FRM · Cátedra de Inteligencia Artificial.** Miranda, Mauricio · Olea, Facundo · de Coninck, Ramiro · Luconi, Martina · 13/11/2026.
