"""SM1 · Entrada (controlador del módulo).

- `SM1.interpretacion_pedido`: L1 de un pedido cargado (lectura).
- `SM1.registrar_pedido` y `SM1.aclarar_pedido` (nivel 2, D-08): las únicas intenciones que escriben en el grafo.
  Reciben el texto y el JSON que ya extrajo el LLM (`pedido`, lo agrega el orquestador con asistente/extractor.py).
"""
from asistente.contrato import Aclaracion
from asistente.submodulos.sm1 import servicio

_SERVICIOS = {
    "SM1.interpretacion_pedido": servicio.interpretacion_pedido,
    "SM1.registrar_pedido": servicio.registrar_pedido,
    "SM1.aclarar_pedido": servicio.aclarar_pedido,
}


def ejecutar(intencion: str, parametros: dict, grafo) -> dict:
    if intencion not in _SERVICIOS:
        raise Aclaracion(f"SM1 no conoce la intención {intencion}.")
    if intencion == "SM1.registrar_pedido":
        if not (parametros.get("texto") or "").strip():
            raise Aclaracion("Contame para qué vas a usar la notebook y cuánto querés gastar.")
    elif not parametros.get("requerimiento_id"):
        raise Aclaracion("¿Sobre qué pedido? Indicá el requerimiento, por ejemplo req_01.")
    elif intencion == "SM1.aclarar_pedido" and not (parametros.get("respuesta") or "").strip():
        raise Aclaracion("No recibí la respuesta a la pregunta pendiente.")
    consultas, evidencia = _SERVICIOS[intencion](grafo, dict(parametros))
    return {"consultas": consultas, "evidencia": evidencia}
