"""GRUPO · Formas de parámetros y evidencia (TypedDict)."""
from typing import Any, TypedDict


class ParametrosTraza(TypedDict):
    requerimiento_id: str
    modelo: str


class ReglaActivada(TypedDict, total=False):
    id: str
    submodulo: str
    tipo: str
    antecedente: str
    consecuente: str
    sobre: str          # Requerimiento | Actividad | Evaluacion | Notebook
    escenario: str      # peor | mejor (solo con dato faltante)
    fuerza: Any         # None = regla crisp (se activó sin grado)
    validacion: str
    fuente: str


class OrigenParametro(TypedDict, total=False):
    parametro: str
    origen: str
    validacion: str
    consulta_experto: str   # (:ConsultaExperto) que lo valida con el técnico
    estado_consulta: str    # pendiente | ...


class OrigenTraza(TypedDict):
    reglas: dict[str, list[OrigenParametro]]   # regla -> parámetros que la respaldan
    reglas_sin_origen: list[str]               # el grafo no tiene su origen: "no registrada"
    notebook: dict[str, str]                   # fuente_precio y fuente_autonomia


class EvidenciaTraza(TypedDict):
    requerimiento_id: str
    notebook: str
    reglas: list[ReglaActivada]
    submodulos: list[str]
    origen: OrigenTraza


class ParametroSistema(TypedDict, total=False):
    submodulo: str
    nombre: str
    valor: Any
    estado_validacion: str
    tipo: str           # etiqueta_difusa | parametro
    origen: str         # de dónde sale el valor, o "no registrada"


class EvidenciaParametros(TypedDict):
    parametros: list[ParametroSistema]
    total: int
    sin_validar: int
    sin_origen: int
