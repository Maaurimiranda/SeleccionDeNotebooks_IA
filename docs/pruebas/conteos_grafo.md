# Conteos del grafo: canónico entero contra los archivos de `cypher/` (PG3-02 y PG3-05)

**Pregunta:** ¿cortar `docs/cypher/Grupo_2_PG2_U1_corregido.cypher` en `cypher/00_…90_*.cypher` cambió el grafo?

## 1. Sin Neo4j: comparación de sentencias (hecha el 10/11/2026)

```bash
python -m scripts.contar_grafo --sentencias
```

| | Sentencias |
| --- | ---: |
| Canónico, del bloque 0 al 10 (del 11 en adelante son consultas) | 101 |
| `cypher/`, sin `90_verificacion.cypher` | 101 |

Se compara cada sentencia con los espacios normalizados. **Difieren exactamente 4**, y son los arreglos de D-06 que se hicieron a propósito en `cypher/`:

| Sentencia | Qué cambió |
| --- | --- |
| Parámetros del bloque 5 (`umbral_exigencia`…) | `'provisional'` pasó a `'sin validar'` |
| Léxico de frecuencia (bloque 6) | `'provisional'` pasó a `'sin validar'` |
| Gamas de GPU (bloque 6) | `'provisional'` pasó a `'sin validar'` |
| REC-R5 (`P_INCREMENTO_PRIORIDAD`, bloque 10.f) | la prioridad `grafica` suma a `peso_grafica` |

Las otras 97 sentencias son **idénticas**. Lo controla `tests/test_contar_grafo.py`. Como las propiedades no cambian ni el número de nodos ni el de relaciones, los conteos tienen que coincidir.

## 2. Con Neo4j: conteos por label y por tipo de relación (hecho el 10/11/2026)

Neo4j 5.26.0 (enterprise), una instancia local nueva de Neo4j Desktop y la base vacía. Se cargó primero el canónico entero (bloques 0 al 10) y se contó; después se cargó `cypher/` y se contó de nuevo.

```bash
python -m scripts.cargar_grafo --canonico
python -m scripts.contar_grafo --guardar docs/pruebas/conteos_canonico.json
python -m scripts.cargar_grafo
python -m scripts.contar_grafo --guardar docs/pruebas/conteos_dividido.json
python -m scripts.contar_grafo --comparar docs/pruebas/conteos_canonico.json docs/pruebas/conteos_dividido.json
```

**Resultado: coinciden todas las filas.** Los dos grafos tienen 343 nodos y 683 relaciones. Un nodo con dos labels (por ejemplo, `Regla` y `ReglaDifusa`) cuenta una vez por cada label.

| Qué | Clave | Canónico | Dividido | OK |
| --- | --- | ---: | ---: | --- |
| Total | nodos | 343 | 343 | sí |
| Total | relaciones | 683 | 683 | sí |
| label | Actividad | 4 | 4 | sí |
| label | Alerta | 8 | 8 | sí |
| label | Almacenamiento | 9 | 9 | sí |
| label | Bateria | 9 | 9 | sí |
| label | CPU | 9 | 9 | sí |
| label | Comprador | 3 | 3 | sí |
| label | ConsultaExperto | 16 | 16 | sí |
| label | EtiquetaDifusa | 47 | 47 | sí |
| label | Evaluacion | 10 | 10 | sí |
| label | ExpresionFrecuencia | 14 | 14 | sí |
| label | Frame | 17 | 17 | sí |
| label | GPU | 9 | 9 | sí |
| label | GamaGPU | 5 | 5 | sí |
| label | Juego | 3 | 3 | sí |
| label | Lectura | 4 | 4 | sí |
| label | Notebook | 9 | 9 | sí |
| label | Pantalla | 9 | 9 | sí |
| label | Parametro | 30 | 30 | sí |
| label | Perfil | 7 | 7 | sí |
| label | Pregunta | 1 | 1 | sí |
| label | RAM | 9 | 9 | sí |
| label | Recomendacion | 1 | 1 | sí |
| label | Regla | 57 | 57 | sí |
| label | ReglaCrisp | 27 | 27 | sí |
| label | ReglaDifusa | 23 | 23 | sí |
| label | Requerimiento | 3 | 3 | sí |
| label | Requisito | 35 | 35 | sí |
| label | VariableDifusa | 15 | 15 | sí |
| relación | ACTIVA | 159 | 159 | sí |
| relación | APUNTA_A | 4 | 4 | sí |
| relación | CONSULTA_POR | 1 | 1 | sí |
| relación | ES_DE_GAMA | 9 | 9 | sí |
| relación | EVALUA | 10 | 10 | sí |
| relación | EXIGE | 35 | 35 | sí |
| relación | EXPRESADA_COMO | 4 | 4 | sí |
| relación | FORMULA | 3 | 3 | sí |
| relación | GENERA | 8 | 8 | sí |
| relación | INCLUYE | 4 | 4 | sí |
| relación | INSTANCIA_DE | 7 | 7 | sí |
| relación | PERTENECE | 3 | 3 | sí |
| relación | PERTENECE_A | 221 | 221 | sí |
| relación | POSEE | 54 | 54 | sí |
| relación | POSEE_SLOT | 6 | 6 | sí |
| relación | PRODUCIDA_POR | 8 | 8 | sí |
| relación | PROPONE | 3 | 3 | sí |
| relación | PROPONE_FUERA_DE_PRESUPUESTO | 1 | 1 | sí |
| relación | RECIBE | 1 | 1 | sí |
| relación | RECOMIENDA_GAMA | 3 | 3 | sí |
| relación | REQUIERE_ACLARACION | 1 | 1 | sí |
| relación | SALIDA_PI2 | 10 | 10 | sí |
| relación | SE_PARAMETRIZA_CON | 47 | 47 | sí |
| relación | SOBRE | 10 | 10 | sí |
| relación | TIENE_ETIQUETA | 47 | 47 | sí |
| relación | TIENE_LECTURA | 4 | 4 | sí |
| relación | TIENE_PERFIL_DOMINANTE | 2 | 2 | sí |
| relación | USA | 1 | 1 | sí |
| relación | VALIDA | 17 | 17 | sí |

Los conteos crudos están en [`conteos_canonico.json`](conteos_canonico.json) y [`conteos_dividido.json`](conteos_dividido.json).
