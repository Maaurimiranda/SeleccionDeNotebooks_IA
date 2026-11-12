"""SM4 · Servicio: arma la evidencia a partir de las filas. No recalcula ni decide.

- Grado y adecuación global: un número, o {"min","max"} si el grafo los dejó como rango (REC-R15). Nunca un promedio.
- Los estados, los motivos y las reglas viajan como los devuelve el grafo (literales de D-06, sin tildes).
- Las alertas llevan siempre su notebook (el verificador controla la atribución).
- Toda respuesta lleva `validacion_parametros` (Q8): cuántos de los parámetros de recomendación siguen sin validar
  con el técnico, con un aviso que el explicador exige copiar literal (devolución docente de PI4).
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


def _no_figura(f: dict) -> dict:
    """La notebook, con por qué no figura en el ranking y qué regla lo decidió (solo si el grafo lo informa)."""
    nb = _notebook(f)
    for clave in ("motivo", "regla", "dato_faltante"):
        if f.get(clave) is not None:
            nb[clave] = f[clave]
    return nb


def _con_empates(items: list[dict], filas: list[dict], contra: list[dict] | None = None) -> list[dict]:
    """`empata_con`: las de su misma franja de REC-R8, que calculó el grafo, entre todas las del ranking (`contra`).
    Solo para las que tienen puesto. Si su grado es un rango, la franja se calculó con el peor caso."""
    contra = filas if contra is None else contra
    for nb, f in zip(items, filas):
        if f["franja_empate"] is not None:
            nb["empata_con"] = [o["notebook"] for o in contra
                                if o["notebook"] != f["notebook"] and o["franja_empate"] == f["franja_empate"]]
            if isinstance(nb["grado"], dict):
                nb["franja_con_peor_caso"] = True
    return items


def aviso_parametros(parametros: int, sin_validar: int) -> str | None:
    """El aviso que acompaña toda respuesta de SM4 mientras quede algún parámetro sin validar. Sin tildes (D-06)."""
    if not sin_validar:
        return None
    cuantos = f"Los {sin_validar}" if sin_validar == parametros else f"{sin_validar} de los {parametros}"
    return f"{cuantos} parametros de recomendacion de SM4 todavia requieren validacion con el tecnico."


def _con_validacion(grafo, consultas: list, evidencia: dict) -> tuple[list, dict]:
    """Agrega Q8 a las consultas y `validacion_parametros` a la evidencia (las cuentas son las del grafo)."""
    c8 = repositorio.parametros_sm4(grafo)
    if c8["filas"]:
        f = c8["filas"][0]
        validacion = {"parametros": f["parametros"], "sin_validar": f["sin_validar"], "nombres": sorted(f["nombres"])}
        aviso = aviso_parametros(f["parametros"], f["sin_validar"])
        if aviso:
            validacion["aviso_validacion"] = aviso
        evidencia["validacion_parametros"] = validacion
    return consultas + [c8], evidencia


def _desempate(c: dict):
    return redondear(c["filas"][0]) if c["filas"] else None


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
        "no_propuestas": [_no_figura(f) for f in c2["filas"]],
        "sin_alternativa": c3["filas"][0]["motivo"] if c3["filas"] else None,
        "criterio_desempate": _desempate(c6b),
    }
    return _con_validacion(grafo, [c1, c2, c3, c6b], evidencia)


def explicar_notebook(grafo, p: dict) -> tuple[list, EvidenciaExplicar]:
    c = repositorio.explicar(grafo, p["requerimiento_id"], p["modelo"])
    if not c["filas"]:
        raise Aclaracion(f"La {p['modelo']} no está evaluada en el pedido {p['requerimiento_id']}.")
    f = c["filas"][0]
    nb = _no_figura(f)
    nb.update({"en_la_recomendacion": f["en_la_recomendacion"], "pesos": redondear(f["pesos"]),
               "cumple": f["cumple"], "no_cumple": f["no_cumple"], "falta_verificar": f["falta_verificar"]})
    evidencia: EvidenciaExplicar = {"requerimiento_id": p["requerimiento_id"], "perfil": f["perfil"],
                                    "presupuesto_usd": redondear(f["presupuesto_usd"]), "notebooks": [nb]}
    return _con_validacion(grafo, [c], evidencia)


def comparar(grafo, p: dict) -> tuple[list, EvidenciaComparar]:
    c = repositorio.comparar(grafo, p["requerimiento_id"], p["modelos"])
    faltan = [m for m in p["modelos"] if m not in {f["notebook"] for f in c["filas"]}]
    if faltan:
        raise Aclaracion(f"No están evaluadas en el pedido {p['requerimiento_id']}: {', '.join(faltan)}.")
    c6b, c1 = repositorio.criterio_desempate(grafo), repositorio.ranking(grafo, p["requerimiento_id"])
    notebooks = [{**_no_figura(f), "en_la_recomendacion": f["en_la_recomendacion"]} for f in c["filas"]]
    dentro = [f for f in c1["filas"] if not f["fuera_de_presupuesto"]]   # empata con cualquiera del ranking, no solo con las comparadas
    evidencia: EvidenciaComparar = {"requerimiento_id": p["requerimiento_id"],
                                    "notebooks": _con_empates(notebooks, c["filas"], dentro),
                                    "criterio_desempate": _desempate(c6b)}
    return _con_validacion(grafo, [c, c6b, c1], evidencia)


def costo_beneficio(grafo, p: dict) -> tuple[list, EvidenciaCostoBeneficio]:
    req = p["requerimiento_id"]
    c = repositorio.costo_beneficio(grafo, req)
    if not c["filas"]:
        # Q7 solo trae las recomendadas: sin ninguna, el pedido puede estar evaluado igual (REC-R10)
        c2, c3 = repositorio.no_propuestas(grafo, req), repositorio.sin_alternativa(grafo, req)
        if not c2["filas"]:
            raise _sin_evaluaciones(req)
        motivo = c3["filas"][0]["motivo"] if c3["filas"] else "Ninguna notebook evaluada quedó recomendada"
        return _con_validacion(grafo, [c, c2, c3],
                               {"requerimiento_id": req, "regla": None, "notebooks": [], "sin_alternativa": motivo})
    r = c["filas"][0]
    evidencia: EvidenciaCostoBeneficio = {
        "requerimiento_id": req,
        "regla": {"id": r["regla"], "enunciado": r["enunciado"], "validacion": r["validacion"]},
        "notebooks": [{"posicion": i, **_notebook(f)} for i, f in enumerate(c["filas"], 1)],
    }
    return _con_validacion(grafo, [c], evidencia)
