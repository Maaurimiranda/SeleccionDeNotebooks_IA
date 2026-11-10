"""SM4 · Entrada (controlador del módulo): valida parámetros y despacha cada intención."""
from asistente.contrato import Aclaracion
from asistente.submodulos.sm4 import servicio

MODELOS_COMPARAR = (2, 3)

_SERVICIOS = {
    "SM4.recomendar": servicio.recomendar,
    "SM4.explicar_notebook": servicio.explicar_notebook,
    "SM4.comparar": servicio.comparar,
    "SM4.costo_beneficio": servicio.costo_beneficio,
}


def ejecutar(intencion: str, parametros: dict, grafo) -> dict:
    """Devuelve {"consultas": [Consulta, ...], "evidencia": dict}. Lanza Aclaracion si faltan datos."""
    if intencion not in _SERVICIOS:
        raise ValueError(f"SM4 no atiende la intención {intencion!r}")
    p = dict(parametros)
    if not p.get("requerimiento_id"):
        raise Aclaracion("¿Sobre qué pedido? Indicá el requerimiento, por ejemplo req_01.")
    if intencion == "SM4.explicar_notebook" and not p.get("modelo"):
        raise Aclaracion("¿De qué notebook querés la explicación? Por ejemplo, Notebook_M.")
    if intencion == "SM4.comparar":
        modelos = p.get("modelos") or []
        modelos = list(dict.fromkeys([modelos] if isinstance(modelos, str) else modelos))
        if not MODELOS_COMPARAR[0] <= len(modelos) <= MODELOS_COMPARAR[1]:
            raise Aclaracion("Para comparar necesito 2 o 3 notebooks distintas, por ejemplo «compará la A y la H».")
        p["modelos"] = modelos
    consultas, evidencia = _SERVICIOS[intencion](grafo, p)
    return {"consultas": consultas, "evidencia": evidencia}
