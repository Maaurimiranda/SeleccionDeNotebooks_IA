"""SM2 · Servicio: arma la evidencia a partir de las filas. No recalcula ni decide.

- El riesgo es un número, o {"min","max"} si la ampliabilidad es desconocida.
- `desconocida` viaja intacta.
- Las alertas llevan siempre su notebook (el verificador controla la atribución).
"""
from asistente.contrato import Aclaracion
from asistente.submodulos.comun import rango, redondear
from asistente.submodulos.sm2 import repositorio
from asistente.submodulos.sm2.esquemas import EvidenciaRiesgo, EvidenciaVirtualizacion


def _sin_evaluaciones(requerimiento_id: str, modelos):
    extra = f" para {', '.join(modelos)}" if modelos else ""
    return Aclaracion(f"El pedido {requerimiento_id} no tiene notebooks evaluadas{extra}. "
                      "Si el perfil quedó indeterminado, primero hay que responder la pregunta pendiente.")


def riesgo_ram(grafo, p: dict) -> tuple[list, EvidenciaRiesgo]:
    c = repositorio.riesgo_ram(grafo, p["requerimiento_id"], p.get("modelos"), p.get("etiqueta"), p.get("tipo_ram"))
    if not c["filas"]:
        raise _sin_evaluaciones(p["requerimiento_id"], p.get("modelos"))
    notebooks = []
    for f in c["filas"]:
        notebooks.append({
            "notebook": f["notebook"],
            "ram_gb": f["ram_gb"],
            "tipo_ram": f["tipo_ram"],
            "ampliabilidad": f["ampliabilidad"],
            "suficiencia_rho": redondear(f["suficiencia_rho"]),
            "indice_ampliabilidad": ("desconocida" if f["indice_ampliabilidad"] is None
                                     else redondear(f["indice_ampliabilidad"])),
            "riesgo": rango(f["riesgo_valor"], f["riesgo_min"], f["riesgo_max"]),
            "etiqueta": f["riesgo_etiqueta"],
            "reglas": sorted(({k: v for k, v in redondear(r).items() if v is not None} for r in f["reglas"]),
                             key=lambda r: (r["id"], r.get("escenario") or "")),
            "alertas": [{"codigo": a["codigo"], "texto": a["texto"], "notebook": f["notebook"]}
                        for a in f["alertas"]],
        })
    evidencia: EvidenciaRiesgo = {"requerimiento_id": p["requerimiento_id"], "perfil": c["filas"][0]["perfil"],
                                  "escala_riesgo": "0 a 100", "notebooks": notebooks}
    return [c], evidencia


def virtualizacion(grafo, p: dict) -> tuple[list, EvidenciaVirtualizacion]:
    c = repositorio.virtualizacion(grafo, p["requerimiento_id"], p.get("modelos"))
    if not c["filas"]:
        raise _sin_evaluaciones(p["requerimiento_id"], p.get("modelos"))
    evidencia: EvidenciaVirtualizacion = {
        "requerimiento_id": p["requerimiento_id"],
        "perfil": c["filas"][0]["perfil"],
        "excluyente": c["filas"][0]["excluyente"],
        "regla": "REN-R1 + REC-R3",
        "notebooks": [{"notebook": f["notebook"], "virtualizacion_cpu": f["virtualizacion_cpu"],
                       "resultado": f["resultado"], "estado": f["estado"]} for f in c["filas"]],
    }
    return [c], evidencia
