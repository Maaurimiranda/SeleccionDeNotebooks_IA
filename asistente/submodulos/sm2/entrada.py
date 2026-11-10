"""SM2 · Entrada (controlador del módulo): valida parámetros y despacha la intención."""
from asistente.contrato import Aclaracion, ETIQUETAS_RIESGO, TIPOS_RAM
from asistente.submodulos.sm2 import servicio

_SERVICIOS = {
    "SM2.riesgo_ram": servicio.riesgo_ram,
    "SM2.virtualizacion": servicio.virtualizacion,
}


def ejecutar(intencion: str, parametros: dict, grafo) -> dict:
    """Devuelve {"consultas": [Consulta, ...], "evidencia": dict}. Lanza Aclaracion si faltan datos."""
    if intencion not in _SERVICIOS:
        raise ValueError(f"SM2 no atiende la intención {intencion!r}")
    p = dict(parametros)
    if not p.get("requerimiento_id"):
        raise Aclaracion("¿Sobre qué pedido? Indicá el requerimiento, por ejemplo req_01.")
    p["modelos"] = p.get("modelos") or None
    if p.get("etiqueta") not in (None, *ETIQUETAS_RIESGO):
        raise Aclaracion(f"La etiqueta de riesgo tiene que ser {', '.join(ETIQUETAS_RIESGO)}.")
    if p.get("tipo_ram") not in (None, *TIPOS_RAM):
        raise Aclaracion(f"El tipo de RAM tiene que ser {', '.join(TIPOS_RAM)}.")
    consultas, evidencia = _SERVICIOS[intencion](grafo, p)
    return {"consultas": consultas, "evidencia": evidencia}
