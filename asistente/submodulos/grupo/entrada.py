"""GRUPO · Entrada (controlador del módulo)."""
from asistente.contrato import Aclaracion
from asistente.submodulos.grupo import servicio

_SERVICIOS = {
    "GRUPO.traza_reglas": servicio.traza_reglas,
    "GRUPO.parametros": servicio.parametros,
}


def ejecutar(intencion: str, parametros: dict, grafo) -> dict:
    if intencion not in _SERVICIOS:
        raise ValueError(f"GRUPO no atiende la intención {intencion!r}")
    p = dict(parametros)
    if intencion == "GRUPO.traza_reglas":
        if not p.get("requerimiento_id"):
            raise Aclaracion("¿Sobre qué pedido? Indicá el requerimiento, por ejemplo req_01.")
        if not p.get("modelo"):
            raise Aclaracion("¿De qué notebook querés ver las reglas? Por ejemplo, Notebook_A.")
    consultas, evidencia = _SERVICIOS[intencion](grafo, p)
    return {"consultas": consultas, "evidencia": evidencia}
