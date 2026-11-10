"""SM4 · Formas de parámetros y evidencia (TypedDict). La completa Luconi en PG3-12."""
from typing import Any, TypedDict


class ParametrosSM4(TypedDict, total=False):
    requerimiento_id: str
    modelo: str
    modelos: list[str]


class EvidenciaSM4(TypedDict, total=False):
    requerimiento_id: str
    stub: bool
    datos: Any
