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


# --- Pedido nuevo (nivel 2, D-08, issues #12 a #14 y #20) -------------------------------------
class ActividadPedido(TypedDict, total=False):
    id: str                    # A1, A2... (en el grafo: <req>_A1)
    descripcion: str
    tipo: str                  # TIPOS_ACTIVIDAD de asistente/extractor.py
    perfil: str                # INT-R11: perfil por el tipo de actividad
    fragmento: str             # cita literal del texto (INT-R7)
    expresion: str | None      # del léxico ExpresionFrecuencia
    horas: float | None        # horas por semana declaradas
    juegos: list[str]          # solo los que existen en el grafo


class PedidoValidado(TypedDict, total=False):
    presupuesto_usd: float
    moneda_original: str
    prioridad: str
    usa_monitor_externo: bool
    notebook_consultada: str | None
    actividades: list[ActividadPedido]
    preguntas: list[str]       # deseables que faltan: quedan como Pregunta pendiente
    observaciones: list[str]   # lo que se descartó o no se reconoció


class EvidenciaRegistro(TypedDict, total=False):
    requerimiento_id: str
    pedido_nuevo: bool         # True en registrar, False en aclarar
    entendido: dict            # presupuesto, prioridad, actividades con su cita, juegos
    observaciones: list[str]
    inferencia_ms: int
