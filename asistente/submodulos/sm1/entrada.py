"""SM1 · Entrada (controlador del módulo). registrar_pedido y aclarar_pedido son nivel 2 (PG3-21)."""
from asistente.contrato import Aclaracion
from asistente.submodulos.sm1 import servicio

_SERVICIOS = {
    "SM1.interpretacion_pedido": servicio.interpretacion_pedido,
}


def ejecutar(intencion: str, parametros: dict, grafo) -> dict:
    if intencion not in _SERVICIOS:
        raise Aclaracion("Registrar o aclarar un pedido nuevo todavía no está disponible. "
                         "Podés consultar los pedidos cargados (req_01, req_02, req_03).")
    if not parametros.get("requerimiento_id"):
        raise Aclaracion("¿Sobre qué pedido? Indicá el requerimiento, por ejemplo req_01.")
    consultas, evidencia = _SERVICIOS[intencion](grafo, dict(parametros))
    return {"consultas": consultas, "evidencia": evidencia}
