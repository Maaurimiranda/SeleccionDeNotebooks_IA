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

## 2. Con Neo4j: conteos por label y por tipo de relación

**Pendiente de correr** (necesita una base propia, y borra su contenido dos veces):

```bash
python -m scripts.cargar_grafo --canonico
python -m scripts.contar_grafo --guardar docs/pruebas/conteos_canonico.json
python -m scripts.cargar_grafo
python -m scripts.contar_grafo --guardar docs/pruebas/conteos_dividido.json
python -m scripts.contar_grafo --comparar docs/pruebas/conteos_canonico.json docs/pruebas/conteos_dividido.json
```

La tabla que imprime el último comando va debajo de este párrafo.
