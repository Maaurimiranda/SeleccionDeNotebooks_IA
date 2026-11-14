# Pedido de programación sin ranking · Luconi · 2026-11-14 · PG3-00

## En tres líneas
Fam pidió «Soy programadora y necesito una notebook para abrir IDEs y bases de datos al mismo tiempo, y jugar al Valorant los fines de semana. Tengo 1000 dólares». El pedido se registró bien (perfil dominante DEV, programación, más GAM, juegos), pero no salió ningún ranking, y el LLM igual escribió «Te recomiendo la Notebook X». Esta rama arregla el verificador para que frene esa invención y hace que SM4 diga con claridad por qué no hay ranking. **No carga datos nuevos:** que haya ranking para DEV es una decisión del grupo.

## Qué cambió
| Archivo | Qué tiene ahora |
| --- | --- |
| [`asistente/explicador.py`](../../asistente/explicador.py) | `verificar` normaliza «Notebook X» o «notebook-X» a `Notebook_X` antes de los controles. Antes, un modelo escrito con espacio no se reconocía como modelo y pasaban los controles (b) (el modelo tiene que estar en la evidencia) y (h) (solo se recomienda lo que la evidencia recomienda). |
| [`asistente/submodulos/sm4/repositorio.py`](../../asistente/submodulos/sm4/repositorio.py) | Consulta nueva `Q0_COBERTURA`: el perfil dominante del pedido y los perfiles que tienen `SALIDA_PI2`. Solo se usa cuando el pedido no tiene evaluaciones. |
| [`asistente/submodulos/sm4/servicio.py`](../../asistente/submodulos/sm4/servicio.py) | `_sin_evaluaciones` arma el mensaje con esos datos: «su perfil dominante es DEV (programación), y la base de conocimiento solo tiene los datos de rendimiento de las notebooks (SALIDA_PI2) para OFI (oficina), VIRT (virtualización). No recomiendo ninguna notebook hasta que se carguen esos datos.» Si el perfil quedó indeterminado, pide responder la pregunta pendiente. |
| `tests/test_explicador.py`, `tests/test_sm4.py` | Un test del modelo con espacio y uno del mensaje nuevo. `Q0_COBERTURA` no lleva `ORDER BY` (devuelve una fila); los perfiles se ordenan en Python. |

### Segunda vuelta: el plural de E2E-9
Fam corrió los tests con Ollama real. En E2E-9, `qwen2.5:3b` escribió «Notebooks_G» y «Notebooks_A», en plural. El control (b) los rechazó tres veces y la respuesta cayó en la plantilla fija. Ahora `normalizar_modelos` (en `explicador.py`) escribe `Notebook_X` cuando el LLM pone «Notebooks_X», «Notebook X» o «notebook-X», y se aplica a la respuesta antes de verificarla, así que el usuario también ve el nombre bien escrito. El control (b) no se afloja: «Notebooks_Z» sigue rechazada, porque Notebook_Z no está en la evidencia.

## Por qué no hay ranking (para alguien que no estuvo)
SM4 rankea las `(:Evaluacion)` que crea [`cypher/15_evaluaciones.cypher`](../../cypher/15_evaluaciones.cypher). Ese archivo crea una evaluación solo si existe `(:Notebook)-[:SALIDA_PI2]->(:Perfil)` para el perfil dominante del pedido. `SALIDA_PI2` es la salida de PI2 (adecuación de rendimiento y grado de pantalla de cada notebook para cada perfil). Hoy está cargada para VIRT (9 notebooks) y para OFI (solo `Notebook_K`, supuesto del grupo para CP11). Un pedido DEV, GAM o DIS queda registrado, pero sin evaluaciones (D-03, D-11).

## Decisiones y por qué
- **No se inventan datos de rendimiento.** Cargar `SALIDA_PI2` para DEV y los otros perfiles es trabajo de SM2/PI2 (Miranda). Queda como decisión del grupo.
- **El verificador normaliza en vez de sumar otro patrón.** Así los controles (b) y (h), que ya existían, cubren el caso sin duplicar la lógica.

## Cómo probarlo
```powershell
python -m unittest      # 240 OK, 5 salteadas
python -m asistente.cli --traza "Soy programadora y necesito una notebook para abrir IDEs y bases de datos al mismo tiempo, y jugar al Valorant los fines de semana. Tengo 1000 dólares."
```
Tiene que registrar el pedido con perfil DEV y responder que no hay notebooks evaluadas, sin nombrar ninguna notebook.

## Qué queda y dudas
- Decidir si se carga `SALIDA_PI2` provisional (`'sin validar'`) para DEV, GAM, DIS y el resto, o si se deja así hasta que SM2 lo defina.
- Solo se tocaron archivos de Luconi (`explicador.py` y SM4). La decisión sobre los datos es de Miranda (SM2).
