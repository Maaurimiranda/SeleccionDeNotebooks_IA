"""GRUPO · Servicio: traza de reglas (L3) y parámetros sin validar (L4). Trazabilidad, consigna §3.7."""
from asistente.contrato import Aclaracion, SIN_VALIDAR
from asistente.submodulos.comun import redondear
from asistente.submodulos.grupo import repositorio
from asistente.submodulos.grupo.esquemas import EvidenciaParametros, EvidenciaTraza

NO_REGISTRADA = "no registrada"   # lo que el grafo no tiene no se inventa (consigna §3.7)
_CAMPOS_ORIGEN = ("parametro", "origen", "validacion", "consulta_experto", "estado_consulta")


def _origen_de_reglas(filas: list[dict], ids: list[str]) -> tuple[dict, list[str]]:
    """Agrupa las filas de origen_reglas: {regla: [parámetro...]} y las reglas sin ningún origen."""
    por_regla: dict[str, list] = {i: [] for i in ids}
    for f in filas:
        if f["parametro"] is None:
            continue
        item = {k: f[k] for k in _CAMPOS_ORIGEN if f.get(k) is not None}
        if item not in por_regla.setdefault(f["regla"], []):
            por_regla[f["regla"]].append(item)
    return {i: p for i, p in por_regla.items() if p}, sorted(i for i, p in por_regla.items() if not p)


def traza_reglas(grafo, p: dict) -> tuple[list, EvidenciaTraza]:
    existe = repositorio.existe_evaluacion(grafo, p["requerimiento_id"], p["modelo"])
    if not existe["filas"] or existe["filas"][0]["evaluaciones"] == 0:
        raise Aclaracion(f"La {p['modelo']} no tiene evaluación en el pedido {p['requerimiento_id']}: "
                         "no hay reglas que mostrar para ese par.")
    c = repositorio.traza(grafo, p["requerimiento_id"], p["modelo"])
    reglas = []
    for f in c["filas"]:
        r = {"id": f["regla"], "submodulo": f["submodulo"], "tipo": f["tipo"], "antecedente": f["antecedente"],
             "consecuente": f["consecuente"], "sobre": f["sobre"], "escenario": f["escenario"],
             "fuerza": redondear(f["fuerza"]), "validacion": f["validacion"], "fuente": f["fuente"]}
        reglas.append({k: v for k, v in r.items() if v is not None or k == "fuerza"})
    ids = sorted({r["id"] for r in reglas})
    c_reglas = repositorio.origen_reglas(grafo, ids)
    c_nb = repositorio.origen_notebook(grafo, p["modelo"])
    con_origen, sin_origen = _origen_de_reglas(c_reglas["filas"], ids)
    nb = c_nb["filas"][0] if c_nb["filas"] else {}
    evidencia: EvidenciaTraza = {
        "requerimiento_id": p["requerimiento_id"], "notebook": p["modelo"], "reglas": reglas,
        "submodulos": sorted({r["submodulo"] for r in reglas if r.get("submodulo")}),
        "origen": {
            "reglas": con_origen, "reglas_sin_origen": sin_origen,
            "notebook": {"fuente_precio": nb.get("fuente_precio") or NO_REGISTRADA,
                         "fuente_autonomia": nb.get("fuente_autonomia") or NO_REGISTRADA},
        },
    }
    return [existe, c, c_reglas, c_nb], evidencia


def parametros(grafo, p: dict) -> tuple[list, EvidenciaParametros]:
    c = repositorio.parametros(grafo)
    c_origen = repositorio.origen_parametros(grafo)
    origen = {f["nombre"]: f["origen"] for f in c_origen["filas"] if f["origen"]}
    lista = [{"submodulo": f["submodulo"], "nombre": f["nombre"], "valor": redondear(f["valor"]),
              "estado_validacion": f["estado_validacion"], "tipo": f["tipo"],
              "origen": origen.get(f["nombre"], NO_REGISTRADA)}
             for f in sorted(c["filas"], key=lambda f: (f["submodulo"] or "", f["tipo"], f["nombre"]))]
    evidencia: EvidenciaParametros = {
        "parametros": lista, "total": len(lista),
        "sin_validar": sum(1 for x in lista if x["estado_validacion"] == SIN_VALIDAR),
        "sin_origen": sum(1 for x in lista if x["origen"] == NO_REGISTRADA),
    }
    return [c, c_origen], evidencia
