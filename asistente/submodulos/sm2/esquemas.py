"""SM2 · Formas de parámetros y evidencia (TypedDict, biblioteca estándar)."""
from typing import Any, TypedDict


class ParametrosRiesgo(TypedDict, total=False):
    requerimiento_id: str
    modelos: list[str]
    etiqueta: str        # bajo | medio | alto
    tipo_ram: str        # ampliable | soldada | mixta | desconocida


class ParametrosVirtualizacion(TypedDict, total=False):
    requerimiento_id: str
    modelos: list[str]


class Regla(TypedDict, total=False):
    id: str
    fuerza: float
    escenario: str       # peor | mejor (solo con dato faltante)
    validacion: str


class Alerta(TypedDict):
    codigo: str
    texto: str
    notebook: str


class RiesgoNotebook(TypedDict, total=False):
    notebook: str
    ram_gb: Any
    tipo_ram: str
    ampliabilidad: str
    suficiencia_rho: float
    indice_ampliabilidad: Any          # número o "desconocida"
    riesgo: Any                        # número o {"min","max"}
    etiqueta: str
    reglas: list[Regla]
    alertas: list[Alerta]


class EvidenciaRiesgo(TypedDict):
    requerimiento_id: str
    perfil: str
    escala_riesgo: str
    notebooks: list[RiesgoNotebook]


class VirtualizacionNotebook(TypedDict):
    notebook: str
    virtualizacion_cpu: str
    resultado: str          # cumple | no cumple | falta informacion | no aplica
    estado: str             # literal D-06 de la evaluación


class EvidenciaVirtualizacion(TypedDict):
    requerimiento_id: str
    perfil: str
    excluyente: bool
    regla: str
    notebooks: list[VirtualizacionNotebook]
