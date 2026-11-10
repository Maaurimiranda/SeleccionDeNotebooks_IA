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


class EvidenciaTraza(TypedDict):
    requerimiento_id: str
    notebook: str
    reglas: list[ReglaActivada]
    submodulos: list[str]


class ParametroSistema(TypedDict, total=False):
    submodulo: str
    nombre: str
    valor: Any
    estado_validacion: str
    tipo: str           # etiqueta_difusa | parametro


class EvidenciaParametros(TypedDict):
    parametros: list[ParametroSistema]
    total: int
    sin_validar: int
