"""SM1 · Formas de parámetros y evidencia (TypedDict)."""
from typing import Any, TypedDict


class ParametrosInterpretacion(TypedDict):
    requerimiento_id: str


class PerfilPedido(TypedDict, total=False):
    perfil: str
    grado: Any                 # número o {"min","max"} si cruza 0,4 (D-09)
    impone_requisitos: bool
    en_frontera: bool


class EvidenciaPedido(TypedDict, total=False):
    requerimiento: str
    presupuesto: float
    prioridad: str
    perfiles: list[PerfilPedido]
    perfil_dominante: str      # código o "indeterminado"
    perfil_dominante_provisional: bool
    intensidad: Any
    intensidad_valor: Any
    preguntas_pendientes: list[str]
    estado_pedido: str         # interpretado | indeterminado
