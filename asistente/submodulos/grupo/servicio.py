"""GRUPO · Servicio: traza de reglas (L3) y parámetros sin validar (L4). Trazabilidad, consigna §3.7."""
from asistente.contrato import Aclaracion, SIN_VALIDAR
from asistente.submodulos.comun import redondear
from asistente.submodulos.grupo import repositorio
from asistente.submodulos.grupo.esquemas import EvidenciaParametros, EvidenciaTraza


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
    evidencia: EvidenciaTraza = {
        "requerimiento_id": p["requerimiento_id"], "notebook": p["modelo"], "reglas": reglas,
        "submodulos": sorted({r["submodulo"] for r in reglas if r.get("submodulo")}),
    }
    return [existe, c], evidencia


def parametros(grafo, p: dict) -> tuple[list, EvidenciaParametros]:
    c = repositorio.parametros(grafo)
    lista = [{"submodulo": f["submodulo"], "nombre": f["nombre"], "valor": redondear(f["valor"]),
              "estado_validacion": f["estado_validacion"], "tipo": f["tipo"]}
             for f in sorted(c["filas"], key=lambda f: (f["submodulo"] or "", f["tipo"], f["nombre"]))]
    evidencia: EvidenciaParametros = {
        "parametros": lista, "total": len(lista),
        "sin_validar": sum(1 for x in lista if x["estado_validacion"] == SIN_VALIDAR),
    }
    return [c], evidencia
