"""SM1 · Servicio: arma la clave `pedido` de la evidencia común. No asume perfiles.

- Perfil indeterminado: estado_pedido = indeterminado, sin perfil asumido (CP10, E2E-3).
- Perfil con rango (D-09): se informa {"min","max"}; si es el dominante, queda provisional.
"""
from asistente.contrato import Aclaracion
from asistente.submodulos.comun import rango, redondear
from asistente.submodulos.sm1 import repositorio
from asistente.submodulos.sm1.esquemas import EvidenciaPedido


def interpretacion_pedido(grafo, p: dict) -> tuple[list, EvidenciaPedido]:
    c = repositorio.interpretacion(grafo, p["requerimiento_id"])
    if not c["filas"]:
        raise Aclaracion(f"No existe el pedido {p['requerimiento_id']}. Los pedidos cargados se ven con "
                         "«¿qué pedidos hay?» o en el manual.")
    f = c["filas"][0]
    perfiles = sorted((
        {"perfil": x["perfil"], "grado": rango(x["grado"], x.get("grado_min"), x.get("grado_max")),
         "impone_requisitos": x["impone_requisitos"], "en_frontera": x["en_frontera"]}
        for x in f["perfiles"]), key=lambda x: -(x["grado"] if isinstance(x["grado"], (int, float))
                                                 else (x["grado"] or {}).get("max") or 0))
    dominante = f["perfil_dominante"] or "indeterminado"
    indeterminado = dominante == "indeterminado"
    grado_dom = next((x["grado"] for x in perfiles if x["perfil"] == dominante), None)
    evidencia: EvidenciaPedido = {
        "requerimiento": f["requerimiento"],
        "presupuesto": redondear(f["presupuesto"]),
        "prioridad": f["prioridad"],
        "perfiles": perfiles,
        "perfil_dominante": dominante,
        "perfil_dominante_provisional": isinstance(grado_dom, dict),
        "intensidad": f["intensidad"],
        "intensidad_valor": redondear(f["intensidad_valor"]),
        "preguntas_pendientes": [q for q in f["preguntas_pendientes"] if q],
        "estado_pedido": "indeterminado" if indeterminado else "interpretado",
    }
    return [c], evidencia
