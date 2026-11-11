# Correcciones del re-review · Miranda · 2026-11-11 · PG3-00

## En tres líneas
Se cerraron los hallazgos abiertos de la primera revisión de código de PG3-11, 13 y 17, y se hizo una segunda revisión sobre esas mismas correcciones. Quedaron arreglados los falsos negativos del escaneo de credenciales del ZIP, varios falsos positivos del verificador del explicador y el test de E2E que corría el modelo 13 veces. Suite offline: 182 pruebas, OK (29 salteadas porque no había Neo4j ni Ollama).

## Qué cambió
| Archivo | Qué tiene ahora |
| --- | --- |
| [`tests/test_e2e.py`](../../tests/test_e2e.py) | Corre cada caso E2E una sola vez (`setUpClass`) y se saltea si el grafo está vacío |
| [`asistente/explicador.py`](../../asistente/explicador.py) | «1.000» se lee como 1000 si la evidencia lo tiene; «1.000.000» no se lee como 1000; la alerta nombrada antes de la notebook también se atribuye; «recomendación» y «alertas» ya no disparan los controles (h) y (c) |
| [`asistente/router.py`](../../asistente/router.py) | Un filtro de SM3 vale si el texto lo dice en palabras («ocho horas») o con punto de miles («2.500 gramos») |
| [`scripts/armar_zip.py`](../../scripts/armar_zip.py) | Escanea también `.py`; detecta valores entre comillas con espacios, comentarios al final, estilo YAML y `set` de Windows; solo acepta como placeholder lo vacío, `<...>`, `...`, `changeme`, `xxx` y `${VAR}`; el aviso ya no imprime el valor; el LEEME dice dónde va el enlace del video |
| [`scripts/correr_e2e.py`](../../scripts/correr_e2e.py) | Un id de E2E que no existe es un error (antes salía con 0) |
| [`tests/test_armar_zip.py`](../../tests/test_armar_zip.py) | Nuevo: prueba el escaneo de credenciales |
| [`docs/CORRECCIONES.md`](../CORRECCIONES.md) | Ya no dice que SM4 y el explicador son stub |

## Cómo funciona (para alguien que no estuvo)
El **verificador** del explicador compara cada cifra, notebook y regla de la respuesta del modelo contra la evidencia que salió de Neo4j. Si algo no cuadra, se pide otra redacción y, tras dos intentos, se usa una plantilla fija. Un falso positivo no es grave (cae a la plantilla), pero gasta tiempo; un falso negativo deja pasar un dato inventado. Por eso las correcciones apuntan a que no rechace frases correctas («la recomendación», «no tiene alertas») sin dejar pasar las incorrectas («La alerta REC-R9 aparece en Notebook_B» cuando REC-R9 es de la A).

El **escaneo de credenciales** del ZIP corre antes de armarlo y, si encuentra una contraseña o una URI de Aura, no lo arma. Como el repo es público, es la última barrera.

## Decisiones y por qué
- **El `.py` se escanea solo por cadenas literales** asignadas a algo con `PASSWORD`, `SECRET`, `TOKEN` o `API_KEY`; el código que lee el entorno (`os.getenv`) no se marca. Alternativa descartada: aplicar el mismo regex que a `.md`, que marcaría todo el código.
- **El test de `armar_zip` arma la cadena de prueba por partes** para no marcarse a sí mismo al escanear `tests/`.

## Cómo probarlo
```bash
python -m unittest discover -s tests -t .      # 182 tests, OK
python -m scripts.armar_zip --verificar        # «Sin credenciales»
```

## Qué queda y dudas
- No se arreglaron: el `?` que exime a toda la oración en el control (g); la fusión de intenciones repetidas en el orquestador (dos `SM3.buscar` con filtros distintos); que la advertencia `franja_con_peor_caso` de SM4 no se marque en las notebooks de grado exacto que empatan con una de rango.
- No se pudo correr con Neo4j ni Ollama (estaban apagados): falta E2E-1 desde el ZIP descomprimido y actualizar los «171 tests» del informe y de `docs/pruebas/funcionales.md` (hoy son 182). El PDF del informe no se rehízo.
