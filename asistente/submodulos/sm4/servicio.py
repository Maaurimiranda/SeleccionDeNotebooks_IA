"""SM4 · Servicio: arma la evidencia a partir de las filas. No recalcula ni decide.

- Grado y adecuación global: un número, o {"min","max"} si el grafo los dejó como rango (REC-R15). Nunca un promedio.
- Los estados, los motivos y las reglas viajan como los devuelve el grafo (literales de D-06, sin tildes).
- Las alertas llevan siempre su notebook (el verificador controla la atribución).
"""
from asistente.contrato import Aclaracion
from asistente.submodulos.comun import rango, redondear
from asistente.submodulos.sm4 import repositorio
from asistente.submodulos.sm4.esquemas import (EvidenciaComparar, EvidenciaCostoBeneficio, EvidenciaExplicar,
                                               EvidenciaRecomendar)


def _sin_evaluaciones(requerimiento_id: str) -> Aclaracion:
    return Aclaracion(f"El pedido {requerimiento_id} no tiene notebooks evaluadas que recomendar. "
                      "Si el perfil quedó indeterminado, primero hay que responder la pregunta pendiente.")


def _notebook(f: dict) -> dict:
    """Los campos que comparten todas las intenciones."""
    nb = {
        "notebook": f["notebook"],
        "estado": f["estado"],
        "grado": rango(f["grado_recomendacion"], f["grado_recomendacion_min"], f["grado_recomendacion_max"]),
        "precio_usd": redondear(f["precio_usd"]),
        "adecuacion_global": rango(f["adecuacion_global"], f["adecuacion_global_min"], f["adecuacion_global_max"]),
        "excedente_presupuesto_pct": redondear(f["excedente_presupuesto_pct"]),
        "indice_costo_beneficio": redondear(f["indice_costo_beneficio"]),
        "ampliabilidad_ram": f["ampliabilidad_ram"],
    }
    if isinstance(nb["adecuacion_global"], dict):
        nb["indice_con_peor_caso"] = True      # el grafo lo calcula con la adecuación mínima
    nb["alertas"] = [{"codigo": a["codigo"], "texto": a["texto"], "notebook": f["notebook"]}
                     for a in sorted(f["alertas"], key=lambda a: (a["codigo"] or "", a["texto"] or ""))]
    return nb


def _con_motivo(nb: dict, f: dict) -> dict:
    """Por qué no figura en el ranking y qué regla lo decidió (solo si el grafo lo informa)."""
    for clave in ("motivo", "regla", "dato_faltante"):
        if f.get(clave) is not None:
            nb[clave] = f[clave]
    return nb


def _con_empates(items: list[dict], filas: list[dict]) -> list[dict]:
    """`empata_con`: las de su misma franja de REC-R8, que calculó el grafo. Solo para las que tienen puesto."""
    for nb, f in zip(items, filas):
        if f["franja_empate"] is not None:
            nb["empata_con"] = [o["notebook"] for o in filas if o is not f and o["franja_empate"] == f["franja_empate"]]
    return items


def _desempate(c: dict):
    return {k: redondear(v) for k, v in c["filas"][0].items()} if c["filas"] else None


def recomendar(grafo, p: dict) -> tuple[list, EvidenciaRecomendar]:
    req = p["requerimiento_id"]
    c1, c2 = repositorio.ranking(grafo, req), repositorio.no_propuestas(grafo, req)
    if not c1["filas"] and not c2["filas"]:
        raise _sin_evaluaciones(req)
    c3, c6b = repositorio.sin_alternativa(grafo, req), repositorio.criterio_desempate(grafo)
    dentro = [f for f in c1["filas"] if not f["fuera_de_presupuesto"]]
    fuera = [f for f in c1["filas"] if f["fuera_de_presupuesto"]]
    evidencia: EvidenciaRecomendar = {
        "requerimiento_id": req,
        "ranking": _con_empates([{"puesto": f["puesto"], **_notebook(f)} for f in dentro], dentro),
        "fuera_de_presupuesto": _notebook(fuera[0]) if fuera else None,
        "no_propuestas": [_con_motivo(_notebook(f), f) for f in c2["filas"]],
        "sin_alternativa": c3["filas"][0]["motivo"] if c3["filas"] else None,
        "criterio_desempate": _desempate(c6b),
    }
    return [c1, c2, c3, c6b], evidencia


def explicar_notebook(grafo, p: dict) -> tuple[list, EvidenciaExplicar]:
    c = repositorio.explicar(grafo, p["requerimiento_id"], p["modelo"])
    if not c["filas"]:
        raise Aclaracion(f"La {p['modelo']} no está evaluada en el pedido {p['requerimiento_id']}.")
    f = c["filas"][0]
    nb = _con_motivo(_notebook(f), f)
    nb.update({"en_la_recomendacion": f["en_la_recomendacion"], "pesos": redondear(f["pesos"]),
               "cumple": f["cumple"], "no_cumple": f["no_cumple"], "falta_verificar": f["falta_verificar"]})
    evidencia: EvidenciaExplicar = {"requerimiento_id": p["requerimiento_id"], "perfil": f["perfil"],
                                    "presupuesto_usd": redondear(f["presupuesto_usd"]), "notebooks": [nb]}
    return [c], evidencia


def comparar(grafo, p: dict) -> tuple[list, EvidenciaComparar]:
    c = repositorio.comparar(grafo, p["requerimiento_id"], p["modelos"])
    faltan = [m for m in p["modelos"] if m not in {f["notebook"] for f in c["filas"]}]
    if faltan:
        raise Aclaracion(f"No están evaluadas en el pedido {p['requerimiento_id']}: {', '.join(faltan)}.")
    c6b = repositorio.criterio_desempate(grafo)
    notebooks = [_con_motivo({**_notebook(f), "en_la_recomendacion": f["en_la_recomendacion"]}, f) for f in c["filas"]]
    evidencia: EvidenciaComparar = {"requerimiento_id": p["requerimiento_id"],
                                    "notebooks": _con_empates(notebooks, c["filas"]),
                                    "criterio_desempate": _desempate(c6b)}
    return [c, c6b], evidencia


def costo_beneficio(grafo, p: dict) -> tuple[list, EvidenciaCostoBeneficio]:
    c = repositorio.costo_beneficio(grafo, p["requerimiento_id"])
    if not c["filas"]:
        raise _sin_evaluaciones(p["requerimiento_id"])
    r = c["filas"][0]
    evidencia: EvidenciaCostoBeneficio = {
        "requerimiento_id": p["requerimiento_id"],
        "regla": {"id": r["regla"], "enunciado": r["enunciado"], "validacion": r["validacion"]},
        "notebooks": [{"posicion": i, **_notebook(f)} for i, f in enumerate(c["filas"], 1)],
    }
    return [c], evidencia
