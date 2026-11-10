"""SM3 · Formas de parámetros y evidencia (TypedDict)."""
from typing import Any, TypedDict


class Filtros(TypedDict, total=False):
    dedicada: bool
    gama_min: int          # 1 a 5
    peso_max: float        # kg
    bateria_min: float     # h
    srgb_min: float        # %


class ParametrosBuscar(TypedDict, total=False):
    requerimiento_id: str
    orden: str             # grafica | movilidad | mixta
    filtros: Filtros


class ParametrosFicha(TypedDict):
    requerimiento_id: str
    modelo: str


class Regla(TypedDict, total=False):
    id: str
    fuerza: Any
    validacion: str


class Alerta(TypedDict):
    codigo: str
    texto: str
    notebook: str


class NotebookSM3(TypedDict, total=False):
    notebook: str
    precio_usd: Any
    gama_gpu: str
    gama_gpu_indice: int
    gpu_dedicada: bool
    grado_gpu: Any
    margen_gama: Any
    adecuacion_grafica: Any
    adecuacion_movilidad: Any          # None = no evaluable (falta la autonomía): se informa, no se completa
    movilidad_etiqueta: Any
    peso_kg: Any
    autonomia_h: Any
    autonomia_tipo_dato: str           # medida | estimada | desconocida
    srgb: Any
    reglas: list[Regla]
    alertas: list[Alerta]
    datos_faltantes: list[str]


class EvidenciaSM3(TypedDict, total=False):
    requerimiento_id: str
    perfil: str
    orden: str
    filtros: Filtros
    limite: int
    notebooks: list[NotebookSM3]
