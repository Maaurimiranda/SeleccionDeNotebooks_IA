"""Contrato común del orquestador (ARQUITECTURA §4, D-06 y D-07).

Todo lo que comparten los submódulos, el router, el explicador y la API vive acá.
Se cambia solo con un PR aprobado por Miranda.
"""

# ---------------------------------------------------------------------------
# 1. Intenciones (D-07 §1, ARQUITECTURA §4.2)
# ---------------------------------------------------------------------------
# nombre -> obligatorios, opcionales, nivel. El submódulo es el prefijo del nombre.
INTENCIONES: dict[str, dict] = {
    "SM1.interpretacion_pedido": {"obligatorios": ["requerimiento_id"], "opcionales": [], "nivel": 1},
    "SM1.registrar_pedido": {"obligatorios": ["texto"], "opcionales": [], "nivel": 2},
    "SM1.aclarar_pedido": {"obligatorios": ["requerimiento_id", "respuesta"], "opcionales": [], "nivel": 2},
    "SM2.riesgo_ram": {"obligatorios": ["requerimiento_id"],
                       "opcionales": ["modelos", "etiqueta", "tipo_ram"], "nivel": 1},
    "SM2.virtualizacion": {"obligatorios": ["requerimiento_id"], "opcionales": ["modelos"], "nivel": 1},
    "SM3.buscar": {"obligatorios": ["requerimiento_id", "orden"], "opcionales": ["filtros"], "nivel": 1},
    "SM3.ficha": {"obligatorios": ["requerimiento_id", "modelo"], "opcionales": [], "nivel": 1},
    "SM4.recomendar": {"obligatorios": ["requerimiento_id"], "opcionales": [], "nivel": 1},
    "SM4.explicar_notebook": {"obligatorios": ["requerimiento_id", "modelo"], "opcionales": [], "nivel": 1},
    "SM4.comparar": {"obligatorios": ["requerimiento_id", "modelos"], "opcionales": [], "nivel": 1},
    "SM4.costo_beneficio": {"obligatorios": ["requerimiento_id"], "opcionales": [], "nivel": 1},
    "GRUPO.traza_reglas": {"obligatorios": ["requerimiento_id", "modelo"], "opcionales": [], "nivel": 1},
    "GRUPO.parametros": {"obligatorios": [], "opcionales": [], "nivel": 1},
}
INTENCIONES_NIVEL_1 = [k for k, v in INTENCIONES.items() if v["nivel"] == 1]
SUBMODULOS = ["SM1", "SM2", "SM3", "SM4", "GRUPO"]

# Valores cerrados de algunos parámetros
ORDENES_SM3 = ["grafica", "movilidad", "mixta"]
ETIQUETAS_RIESGO = ["bajo", "medio", "alto"]
TIPOS_RAM = ["ampliable", "soldada", "mixta", "desconocida"]
FILTROS_SM3 = ["dedicada", "gama_min", "peso_max", "bateria_min", "srgb_min"]


def submodulo_de(intencion: str) -> str:
    return intencion.split(".", 1)[0]


# ---------------------------------------------------------------------------
# 2. Esquema del plan del router (D-07 §2, ARQUITECTURA §4.3)
# ---------------------------------------------------------------------------
# Se pasa a Ollama como salida estructurada (format = esquema). Con qwen2.5:3b
# ayuda que todo esté cerrado: enum de intenciones, maxItems y sin propiedades extra.
_NULO_O = lambda esquema: {"anyOf": [esquema, {"type": "null"}]}  # noqa: E731

ESQUEMA_PLAN: dict = {
    "type": "object",
    "properties": {
        "requerimiento_id": _NULO_O({"type": "string"}),
        "consultas": {
            "type": "array",
            "maxItems": 3,
            "items": {
                "type": "object",
                "properties": {
                    "intencion": {"type": "string", "enum": list(INTENCIONES)},
                    "parametros": {
                        "type": "object",
                        "properties": {
                            "modelo": {"type": "string"},
                            "modelos": {"type": "array", "items": {"type": "string"}},
                            "orden": {"type": "string", "enum": ORDENES_SM3},
                            "etiqueta": {"type": "string", "enum": ETIQUETAS_RIESGO},
                            "tipo_ram": {"type": "string", "enum": TIPOS_RAM},
                            "filtros": {
                                "type": "object",
                                "properties": {
                                    "dedicada": {"type": "boolean"},
                                    "gama_min": {"type": "integer"},
                                    "peso_max": {"type": "number"},
                                    "bateria_min": {"type": "number"},
                                    "srgb_min": {"type": "number"},
                                },
                            },
                        },
                    },
                },
                "required": ["intencion", "parametros"],
            },
        },
        "evidencia": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"dato": {"type": "string"}, "fragmento": {"type": "string"}},
                "required": ["dato", "fragmento"],
            },
        },
        "fuera_de_alcance": {"type": "boolean"},
        "aclaracion": _NULO_O({"type": "string"}),
    },
    "required": ["requerimiento_id", "consultas", "evidencia", "fuera_de_alcance", "aclaracion"],
}

# ---------------------------------------------------------------------------
# 3. Excepciones (el orquestador las traduce a origen_respuesta)
# ---------------------------------------------------------------------------


class Aclaracion(Exception):
    """Falta o sobra un dato: se le pide al usuario que aclare. -> 'validacion'."""

    def __init__(self, mensaje: str):
        super().__init__(mensaje)
        self.mensaje = mensaje


class FueraDeAlcance(Exception):
    """La consulta no es del dominio. -> 'fuera_de_alcance', sin tocar el grafo."""


class ErrorGrafo(Exception):
    """Neo4j no respondió o la consulta falló. -> 'error'."""


class ErrorLLM(Exception):
    """Ollama no respondió o no cumplió el formato. -> 'error'."""


# ---------------------------------------------------------------------------
# 4. Literales (D-06), sin tildes como en el grafo
# ---------------------------------------------------------------------------
ESTADOS = [
    "Recomendada (Alta)",
    "Recomendada (Media)",
    "Recomendada condicionada por falta de informacion",
    "Indeterminada: completar informacion",
    "Descartada (excluyente incumplido)",
    "Descartada",
]
SIN_VALIDAR = "sin validar"
ESCENARIOS = ["peor", "mejor"]
ORIGENES_RESPUESTA = ["llm", "plantilla_fija", "validacion", "fuera_de_alcance", "error"]

# ---------------------------------------------------------------------------
# 5. Textos fijos
# ---------------------------------------------------------------------------
ADVERTENCIA = ("Los parametros difusos y los umbrales del sistema estan sin validar por el tecnico: "
               "los grados y riesgos son una referencia, no una certeza.")

MENSAJE_ALCANCE = (
    "Esa consulta esta fuera de lo que puedo responder. Soy el asistente para elegir notebooks: "
    "puedo interpretar un pedido, evaluar el riesgo de quedarse corto de RAM, la virtualizacion, "
    "buscar por grafica o movilidad, mostrar la ficha de un modelo, recomendar, comparar y "
    "mostrar las reglas y parametros que usa el sistema.")

MENSAJE_ERROR_GRAFO = ("No pude consultar la base de conocimiento (Neo4j) en este momento. "
                       "Revisá que este levantada y volve a intentar.")
MENSAJE_ERROR_LLM = ("No pude usar el modelo de lenguaje (Ollama) en este momento. "
                     "Revisá que este levantado y que el modelo este descargado.")
MENSAJE_ERROR = "Ocurrio un error inesperado al procesar la consulta. Quedo registrado en la traza."

EJEMPLO_REFORMULACION = ("Por ejemplo: «¿Qué me recomendás para req_01?», «¿Qué riesgo de RAM tiene "
                         "la Notebook_G en req_01?» o «Buscá las más livianas para req_01».")
