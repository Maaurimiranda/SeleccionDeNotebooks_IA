# 5. Base de conocimiento en Neo4j

**Fuente:** el grafo canónico de PG2 corregido (`docs/cypher/Grupo_2_PG2_U1_corregido.cypher`, decisión D-01), dividido en PG3 en un archivo por dueño sin cambiar su contenido.

## Ontología

| Capa | Labels | Para qué |
| --- | --- | --- |
| Esquema | `Frame` | Una clase por concepto de la red semántica de PG1 |
| Conocimiento | `Perfil`, `Requisito`, `VariableDifusa`, `EtiquetaDifusa`, `Regla` (`ReglaDifusa`, `ReglaCrisp`), `Parametro`, `ExpresionFrecuencia`, `GamaGPU`, `ConsultaExperto` | Perfiles de uso y sus requisitos, 15 variables y 47 etiquetas difusas, 57 reglas, parámetros, léxico de frecuencia y agenda de validación con el técnico |
| Instancias | `Comprador`, `Requerimiento`, `Actividad`, `Juego`, `Notebook`, `CPU`, `RAM`, `Almacenamiento`, `GPU`, `Pantalla`, `Bateria` | Pedidos y catálogo |
| Inferencia | `Evaluacion`, `Lectura`, `Alerta`, `Pregunta`, `Recomendacion` | Resultados por pedido × notebook, escenarios peor/mejor con dato faltante, alertas y recomendación |

Relaciones principales: `FORMULA`, `INCLUYE`, `PERTENECE`, `TIENE_PERFIL_DOMINANTE`, `EXIGE`, `POSEE`, `EVALUA` y `SOBRE` (pedido → evaluación → notebook), `TIENE_LECTURA`, `PERTENECE_A` (pertenencia difusa), `ACTIVA {fuerza}` (traza de cada regla), `GENERA` (alertas), `REQUIERE_ACLARACION`, `PROPONE` y `PROPONE_FUERA_DE_PRESUPUESTO`.

Todo resultado que depende del pedido vive en la `(:Evaluacion)` de ese pedido × notebook (corrección de PG2): dos compradores pueden evaluar la misma notebook sin pisarse (caso CP11, Notebook_K en `req_01` y `req_03`).

## Conteos (grafo cargado)

343 nodos y 683 relaciones. La carga dividida da **los mismos conteos** por label (28) y por tipo de relación (29) que el canónico entero: 57 de 57 iguales.

## Cómo se carga y de quién es cada archivo

`python -m scripts.cargar_grafo` ejecuta `cypher/NN_*.cypher` en orden numérico, sentencia por sentencia; si una falla, informa el archivo y la línea. `python -m scripts.verificar_grafo` corre la regresión CP1–CP11 contra los esperados de PG1/PG2 §9.4: **11 de 11 OK**.

| Archivo | Contenido | Dueño |
| --- | --- | --- |
| `00_esquema.cypher` | Limpieza, índices y frames | Miranda |
| `01_conocimiento.cypher` | Perfiles, variables difusas, reglas, parámetros, léxico y gamas | Miranda |
| `02_instancias.cypher` | Compradores, pedidos y catálogo | Miranda |
| `10_sm1.cypher` | Fuzificación e inferencia de SM1 | Olea |
| `15_evaluaciones.cypher` | Una `Evaluacion` por pedido × notebook | Miranda |
| `20_sm2.cypher` | Riesgo de obsolescencia de la RAM | Miranda |
| `30_sm3.cypher` | Movilidad y grado de GPU | de Coninck |
| `40_sm4.cypher` | Filtro de excluyentes y recomendación | Luconi |
| `90_verificacion.cypher` | Consultas C1–C3 y CP1–CP11 (no se cargan) | Miranda |

Arreglos de D-06 aplicados en PG3: los parámetros, el léxico y las gamas pasan de `'provisional'` a `'sin validar'` (hoy no queda ningún nodo `'provisional'`), y la prioridad `grafica` suma su incremento al peso gráfico (REC-R5), como dice el enunciado de la regla.
