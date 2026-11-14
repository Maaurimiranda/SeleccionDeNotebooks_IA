# Resumen ejecutivo

**El problema.** Elegir una notebook obliga a traducir lo que el comprador necesita («programar, virtualizar y jugar a veces», «1000 USD») en requisitos de hardware y a compararlos contra fichas que suelen venir incompletas. Hoy lo resuelve un técnico por experiencia. Este trabajo vuelve ese criterio explícito, verificable y explicable para el **asesor de ventas**, que es quien usa el sistema.

**La solución.** Un único asistente con una sola entrada (API `POST /consultar`, web en `/ui` y consola) que responde en español. Cuatro submódulos comparten un grafo de conocimiento en Neo4j (343 nodos y 683 relaciones): SM1 interpreta el pedido, SM2 evalúa el riesgo de RAM y la virtualización, SM3 la gráfica y la movilidad, y SM4 recomienda con costo-beneficio. El razonamiento son 57 reglas (23 de ellas difusas, tipo Mamdani) cargadas en el grafo y consultadas con Cypher fijo.

**Cómo funciona.** El asesor escribe la consulta. Un router (LLM `qwen2.5:3b` local, temperatura 0) arma un plan JSON y Python lo valida. Si la consulta describe un pedido nuevo («soy diseñadora, uso Photoshop todos los días, tengo 1000 USD»), el LLM extrae un JSON con usos, juegos y presupuesto; Python lo valida contra el texto, y Neo4j guarda el pedido y corre las reglas solo para él. Después, Neo4j ejecuta Cypher fijo de solo lectura; un explicador (LLM) redacta con esa evidencia y un verificador en Python revisa cifras, modelos, reglas y estados antes de responder. Si no pasa, sale una plantilla fija.

**Principios.** Neo4j maneja la verdad: el LLM interpreta y explica, pero no calcula, no decide ni escribe Cypher. La incertidumbre se conserva (rangos, `desconocida`, perfil indeterminado). Cada consulta deja una traza auditable.

**Ejemplo real (E2E-1, req_01: 1000 USD, perfil dominante virtualización con grado 0,899).** La A queda `Recomendada (Alta)` con grado 0,785, y la H y la B completan el podio por desempate de ampliabilidad. La X se ofrece aparte por pasarse del presupuesto. La E queda `Descartada (excluyente incumplido)` aunque puntúa ≈ 0,81, porque su CPU no soporta virtualización. La G queda `Indeterminada: completar informacion` y la M `Recomendada condicionada por falta de informacion` (grado [0,504 ; 0,826]).

| Medida | Resultado |
| --- | --- |
| Regresión del grafo (CP1 a CP11) | 11 de 11 |
| Pruebas automáticas (`unittest`, con Neo4j, 14/11) | 244 OK, 5 salteadas porque piden Ollama |
| E2E (5 integrales y 2 controles, 11/11) | 7 de 7 aprueban; 4,3 a 7,1 s las que redacta el LLM (una máquina) |
| Router: intenciones / resultado final (37 consultas) | 34 de 37 (92 %) / 37 de 37 (100 %) |
| Respuestas con explicación que salieron de la plantilla fija | 0 de 5 |

**Limitaciones vigentes.**
- **Validación con el técnico, parcial.** Respondió las 16 consultas el 14/11/2026 y confirmó 7 de las 15 variables difusas (21 de 47 etiquetas). Para 6 variables propuso otros valores y para 3 pidió cambios de regla; esas 9 propuestas no se aplicaron, para no mover los resultados. El resto de los parámetros sigue sin validar, y toda respuesta lo advierte.
- **Pedido nuevo con datos provisionales.** Desde el 14/11 el asistente registra pedidos escritos en lenguaje libre, corre la inferencia en vivo para cada uno y los rankea cualquiera sea su perfil. Para seis de los siete perfiles, los datos de rendimiento de las notebooks son provisionales y están marcados como sin validar.
- **Redacción del modelo chico.** `qwen2.5:3b` redacta con torpezas que el verificador no siempre corta: en E2E-2 dio como riesgo de RAM de la G un número que era su adecuación global.
- **Alcance de la medición.** Los tiempos se midieron en una sola máquina y el catálogo de prueba tiene 9 modelos.

**Grupo 2 · Comisión 5K09 · UTN FRM · Cátedra de Inteligencia Artificial.** Miranda, Mauricio · Olea, Facundo · de Coninck, Ramiro · Luconi, Martina · 14/11/2026.
