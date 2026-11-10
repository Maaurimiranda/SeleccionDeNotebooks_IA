"""SM4 · Entrada (controlador del módulo). STUB hasta PG3-12."""
from asistente.contrato import Aclaracion
from asistente.submodulos.sm4 import servicio

INTENCIONES = ("SM4.recomendar", "SM4.explicar_notebook", "SM4.comparar", "SM4.costo_beneficio")


def ejecutar(intencion: str, parametros: dict, grafo) -> dict:
    if intencion not in INTENCIONES:
        raise ValueError(f"SM4 no atiende la intención {intencion!r}")
    if not parametros.get("requerimiento_id"):
        raise Aclaracion("¿Sobre qué pedido? Indicá el requerimiento, por ejemplo req_01.")
    consultas, evidencia = servicio.desde_fixture(intencion, dict(parametros))
    return {"consultas": consultas, "evidencia": evidencia}
