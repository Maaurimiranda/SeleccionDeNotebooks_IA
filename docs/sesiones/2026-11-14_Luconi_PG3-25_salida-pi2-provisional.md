# SALIDA_PI2 provisional para los otros 6 perfiles · Luconi · 2026-11-14 · PG3-25

## En tres líneas
Un pedido de programación (perfil DEV), de diseño (DIS) o de juegos (GAM) no tenía ranking, porque solo había datos de rendimiento y pantalla (`SALIDA_PI2`) para VIRT y para K–OFI (D-03). Esta rama carga 53 pares provisionales, calculados con un método explícito y marcados `'sin validar'`, para que cualquier pedido evalúe el catálogo. **Miranda (rendimiento, SM2) y de Coninck (pantalla, SM3) tienen que revisarlos** y reemplazarlos por los valores de sus reglas de PI2 cuando los tengan.

## Qué cambió
| Archivo | Qué tiene ahora |
| --- | --- |
| [`scripts/proponer_salida_pi2.py`](../../scripts/proponer_salida_pi2.py) | Nuevo. Lee del grafo la ficha de cada notebook y los requisitos de cada perfil, aplica el método de abajo y escribe el `.cypher` y la planilla. |
| [`cypher/03_salida_pi2_provisional.cypher`](../../cypher/03_salida_pi2_provisional.cypher) | Nuevo, generado. Una sentencia con los 53 pares (OFI, DEV, DIS, VID3D, GAM y DATOS × 9 notebooks, menos K–OFI). Cada relación lleva `origen`, `origen_rendimiento`, `origen_pantalla` y `validacion: 'sin validar'`. Va en un archivo aparte (como `50_validacion_tecnico`) para que 01 a 40 sigan iguales al canónico. |
| [`docs/cypher/salida_pi2.csv`](../../cypher/salida_pi2.csv) | La planilla de D-03: los 53 pares pasan de `pendiente` a `provisional`, con su origen. |
| `tests/test_salida_pi2_provisional.py`, `test_pedido_nuevo.py`, `test_contar_grafo.py`, `test_armar_zip.py` | Tests del método y del archivo, el pedido DEV de Fam contra Neo4j real, y los conteos que suman un archivo y una sentencia. |

## El método (para que se pueda revisar)
**Rendimiento** (SM2, [Contexto SM2 §6.3](../contexto/Contexto_SM2_Miranda_para_PG3.md), con los requisitos del grafo canónico y el alcance de D-02):
- **CPU:** brecha de gama contra la mínima del perfil (REN-R3): misma gama o mejor 1,0; un nivel abajo 0,6; dos niveles 0,2. Núcleos y carga sostenida quedan fuera (D-02).
- **RAM** (M = mínimo, R = recomendado): ≥ R 1,0; entre M y R 0,7; entre M/2 y M, lineal hasta 0,7; ≤ M/2, 0. REN-R7: si está por debajo de M y se puede ampliar hasta M, al menos 0,5. Sin el +0,1 de REN-R9, que está retirada. Con ampliabilidad desconocida (G) no se aplica REN-R7.
- **SSD:** ≥ M 1,0; entre M/2 y M 0,4; menos, 0. El canónico no guarda un SSD recomendado.
- **Rendimiento** = 0,35·CPU + 0,40·RAM + 0,25·SSD (SP6).

**Pantalla** (SM3):
- OFI, DEV y DATOS no exigen nada de la pantalla, igual que VIRT: se usa el grado de VIRT de esa notebook. Es lo mismo que ya hacía el supuesto K–OFI (0,90).
- DIS y VID3D: min(1, sRGB / 95), porque 95 % sRGB es el umbral de diseño de SM3.
- GAM: min(1, Hz / 144).

**Lo que este método no reproduce:** aplicado a VIRT da A 0,88 (cargado 0,90), C 0,88 (0,95), K 0,80 (0,50) y G 0,46 (0,55). No distingue dentro de la gama alta ni castiga el canal simple de K. Por eso no se tocaron los 9 pares de VIRT ni K–OFI, y por eso los valores nuevos son provisionales.

## Qué cambia en los resultados
- `req_01` y `req_03` no cambian: usan VIRT y K–OFI. Los 242 tests pasan (5 salteados por Ollama).
- El pedido de Fam («Soy programadora… IDEs y bases de datos… Valorant los fines de semana. Tengo 1000 dólares») queda DEV 0,899 + GAM 0,388 y ahora recomienda Notebook_A, Notebook_E y Notebook_H (las tres «Recomendada (Media)»).
- `docs/pruebas/conteos_grafo.md` compara el canónico con `cypher/`: ahora `SALIDA_PI2` da 10 contra 63. Es la diferencia esperada por este archivo.

## Cómo probarlo
```powershell
python -m scripts.cargar_grafo          # carga también 03_salida_pi2_provisional.cypher
python -m unittest                      # 242 OK, 5 salteadas
python -m scripts.proponer_salida_pi2   # solo si cambia la ficha o el método: regenera el .cypher y la planilla
```

## Qué queda y dudas
- **Miranda:** confirmar o reemplazar el rendimiento de los 53 pares, y K–OFI.
- **de Coninck:** confirmar o reemplazar la pantalla, sobre todo GAM (60 Hz da 0,42) y DIS/VID3D.
- Cuando estén los valores de PI2, se cargan en el bloque 8 de `02_instancias` (como dice PG3-25) y se borra `03_salida_pi2_provisional.cypher`.
