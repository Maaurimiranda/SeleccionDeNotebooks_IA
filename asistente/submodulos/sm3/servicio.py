"""SM3 · Servicio: búsqueda por gráfica/movilidad/mixta y ficha de un modelo.

La movilidad en null no se completa: se informa como dato faltante (la autonomía).
"""
from asistente.contrato import Aclaracion
from asistente.submodulos.comun import redondear
from asistente.submodulos.sm3 import repositorio
from asistente.submodulos.sm3.esquemas import EvidenciaSM3

_CLAVES = ("notebook", "precio_usd", "gama_gpu", "gama_gpu_indice", "gpu_dedicada", "grado_gpu", "margen_gama",
           "adecuacion_grafica", "adecuacion_movilidad", "movilidad_etiqueta", "peso_kg", "autonomia_h",
           "autonomia_tipo_dato", "srgb")
_EXTRA_FICHA = ("autonomia_medida_h", "autonomia_declarada_h", "fuente_bateria", "resolucion", "refresco_hz",
                "vram_gb", "fuente_precio")


def _notebook(f: dict, extra=()) -> dict:
    nb = {k: redondear(f.get(k)) for k in (*_CLAVES, *extra)}
    nb["reglas"] = sorted((redondear(r) for r in f["reglas"]), key=lambda r: -(r.get("fuerza") or 0))
    nb["alertas"] = [{"codigo": a["codigo"], "texto": a["texto"], "notebook": f["notebook"]} for a in f["alertas"]]
    faltan = []
    if f.get("adecuacion_movilidad") is None:
        faltan.append("autonomia (la adecuacion de movilidad no se puede evaluar)")
    if f.get("autonomia_tipo_dato") == "estimada":
        faltan.append("autonomia medida (la que hay es estimada)")
    nb["datos_faltantes"] = faltan
    return nb


def buscar(grafo, p: dict) -> tuple[list, EvidenciaSM3]:
    c = repositorio.buscar(grafo, p["requerimiento_id"], p["orden"], p.get("filtros") or {})
    if not c["filas"]:
        raise Aclaracion(f"No hay notebooks evaluadas en {p['requerimiento_id']} que cumplan esos filtros. "
                         "Probá con filtros menos exigentes.")
    evidencia: EvidenciaSM3 = {
        "requerimiento_id": p["requerimiento_id"], "perfil": c["filas"][0]["perfil"], "orden": p["orden"],
        "filtros": {k: v for k, v in (p.get("filtros") or {}).items() if v is not None},
        "limite": repositorio.LIMITE_RESULTADOS, "notebooks": [_notebook(f) for f in c["filas"]],
    }
    return [c], evidencia


def ficha(grafo, p: dict) -> tuple[list, EvidenciaSM3]:
    c = repositorio.ficha(grafo, p["requerimiento_id"], p["modelo"])
    if not c["filas"]:
        raise Aclaracion(f"La {p['modelo']} no está evaluada en el pedido {p['requerimiento_id']}.")
    evidencia: EvidenciaSM3 = {"requerimiento_id": p["requerimiento_id"], "perfil": c["filas"][0]["perfil"],
                               "notebooks": [_notebook(c["filas"][0], _EXTRA_FICHA)]}
    return [c], evidencia
