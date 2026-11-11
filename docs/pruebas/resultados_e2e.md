# Resultados de los E2E

Corrida del 2026-11-11 con el orquestador real (Neo4j y `qwen2.5:3b`). Tiempos medidos en **una** máquina: falta repetirlos en otra (PG3-11, punto 3).

| E2E | Tipo | Submódulos del plan | Origen | Intentos | Tiempo (s) | Esperados | Veredicto |
| --- | --- | --- | --- | --- | --- | --- | --- |
| [E2E-1](E2E-1.md) | integral | SM2, SM4 | llm | 1 | 7.091 | 5/5 | APRUEBA |
| [E2E-2](E2E-2.md) | integral | SM2, SM4 | llm | 1 | 5.087 | 4/4 | APRUEBA |
| [E2E-3](E2E-3.md) | control | SM4 | validacion | 0 | 1.308 | 4/4 | APRUEBA |
| [E2E-5](E2E-5.md) | integral | SM2, SM4 | llm | 1 | 4.515 | 4/4 | APRUEBA |
| [E2E-8](E2E-8.md) | control | — | fuera_de_alcance | 0 | 0.69 | 2/2 | APRUEBA |
| [E2E-9](E2E-9.md) | integral | GRUPO, SM2 | llm | 1 | 4.332 | 4/4 | APRUEBA |
| [E2E-10](E2E-10.md) | integral | SM3, SM4 | llm | 1 | 4.281 | 3/3 | APRUEBA |

**Tasa de plantilla fija:** 0 de 5 respuestas con explicación salieron de la plantilla (0%); el resto las redactó el LLM y las aprobó el verificador.
