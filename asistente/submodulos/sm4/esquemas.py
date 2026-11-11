"""SM4 · Formas de parámetros y evidencia (TypedDict)."""
from typing import Any, TypedDict


class ParametrosSM4(TypedDict, total=False):
    requerimiento_id: str
    modelo: str            # SM4.explicar_notebook
    modelos: list[str]     # SM4.comparar: 2 o 3


class Alerta(TypedDict):
    codigo: str            # regla que la produjo (REC-R13, GM-R8...)
    texto: str
    notebook: str


class NotebookSM4(TypedDict, total=False):
    notebook: str
    estado: str                        # literales de D-06
    grado: Any                         # número o {"min", "max"} (REC-R15): nunca un promedio
    precio_usd: Any
    adecuacion_global: Any             # número o {"min", "max"}
    excedente_presupuesto_pct: Any
    indice_costo_beneficio: Any
    indice_con_peor_caso: bool         # True si la adecuación es un rango: el índice usa su mínimo
    ampliabilidad_ram: str             # alta | media | baja | desconocida
    alertas: list[Alerta]
    # solo si corresponde
    puesto: int
    empata_con: list[str]              # notebooks en la misma franja de REC-R8
    franja_con_peor_caso: bool         # True si el grado es un rango: la franja usa su mínimo
    en_la_recomendacion: str
    motivo: str                        # por qué no figura en el ranking
    regla: str
    dato_faltante: str
    posicion: int                      # SM4.costo_beneficio
    pesos: dict                        # SM4.explicar_notebook
    cumple: list[str]
    no_cumple: list[str]
    falta_verificar: list[str]


class CriterioDesempate(TypedDict, total=False):
    regla: str
    enunciado: str
    margen_empate: Any
    validacion: str
    validacion_margen: str


class EvidenciaRecomendar(TypedDict, total=False):
    requerimiento_id: str
    ranking: list[NotebookSM4]                  # hasta 3, dentro del presupuesto
    fuera_de_presupuesto: Any                   # NotebookSM4 o None (máximo una)
    no_propuestas: list[NotebookSM4]            # evaluadas que no figuran, con motivo y regla
    sin_alternativa: Any                        # motivo (REC-R10) o None
    criterio_desempate: Any                     # CriterioDesempate o None


class EvidenciaExplicar(TypedDict, total=False):
    requerimiento_id: str
    perfil: str
    presupuesto_usd: Any
    notebooks: list[NotebookSM4]                # una sola


class EvidenciaComparar(TypedDict, total=False):
    requerimiento_id: str
    notebooks: list[NotebookSM4]
    criterio_desempate: Any


class ReglaCostoBeneficio(TypedDict, total=False):
    id: str
    enunciado: str
    validacion: str


class EvidenciaCostoBeneficio(TypedDict, total=False):
    requerimiento_id: str
    regla: ReglaCostoBeneficio | None           # None si ninguna notebook quedó recomendada
    notebooks: list[NotebookSM4]                # de mayor a menor índice
    sin_alternativa: str                        # solo si no hay recomendadas: el motivo de REC-R10
