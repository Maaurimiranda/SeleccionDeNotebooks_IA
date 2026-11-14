"""Extracción del pedido con el LLM (issue #12, D-08). Primer paso de una consulta libre.

Ollama lee el texto que escribió la persona y devuelve un JSON con las actividades, la frecuencia, los
juegos, el presupuesto y la prioridad, con la evidencia literal de cada dato. Es el mismo diseño de la
PI4 de SM1 (PROMPT_EXTRACCION), migrado al LLM común (LangChain + Ollama, salida estructurada).

El LLM solo copia lo que está escrito: la validación (INT-R1, INT-R7, INT-R10), las horas, los perfiles
y los grados los calculan Python y Neo4j (asistente/submodulos/sm1/).
"""
import json
from pathlib import Path

RUTA_PROMPT = Path(__file__).resolve().parent.parent / "prompts" / "extraccion.txt"

TIPOS_ACTIVIDAD = ["programar", "virtualizar", "jugar", "disenar", "editar_video", "modelar_3d",
                   "analizar_datos", "ofimatica", "estudiar", "otra"]
PRIORIDADES = ["rendimiento", "grafica", "portabilidad", "autonomia", "precio", "ninguna"]

_NULO_O = lambda esquema: {"anyOf": [esquema, {"type": "null"}]}  # noqa: E731

ESQUEMA_PEDIDO: dict = {
    "type": "object",
    "properties": {
        "es_pedido_notebook": {"type": "boolean"},
        "presupuesto": {
            "type": "object",
            "properties": {
                "monto": _NULO_O({"type": "number"}),
                "moneda": _NULO_O({"type": "string", "enum": ["USD", "ARS"]}),
                "evidencia": _NULO_O({"type": "string"}),
            },
            "required": ["monto", "moneda", "evidencia"],
        },
        "prioridad": {"type": "string", "enum": PRIORIDADES},
        "usa_monitor_externo": {"type": "boolean"},
        "notebook_consultada": _NULO_O({"type": "string"}),
        "actividades": {
            "type": "array",
            "maxItems": 6,
            "items": {
                "type": "object",
                "properties": {
                    "descripcion": {"type": "string"},
                    "tipo": {"type": "string", "enum": TIPOS_ACTIVIDAD},
                    "evidencia": {"type": "string"},
                    "expresion_frecuencia": _NULO_O({"type": "string"}),
                    "cantidad_horas": _NULO_O({"type": "number"}),
                    "periodo_horas": _NULO_O({"type": "string", "enum": ["dia", "semana", "mes"]}),
                    "juegos": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["descripcion", "tipo", "evidencia", "expresion_frecuencia", "cantidad_horas",
                             "periodo_horas", "juegos"],
            },
        },
    },
    "required": ["es_pedido_notebook", "presupuesto", "prioridad", "usa_monitor_externo",
                 "notebook_consultada", "actividades"],
}


def extraer(texto: str, llm, vocabulario: dict) -> dict:
    """Pide el JSON del pedido al LLM. `vocabulario` = {"expresiones": [...], "juegos": [...]} leído del grafo."""
    variables = {
        "tipos": json.dumps(TIPOS_ACTIVIDAD, ensure_ascii=False),
        "expresiones": json.dumps(vocabulario.get("expresiones") or [], ensure_ascii=False),
        "juegos": json.dumps(vocabulario.get("juegos") or [], ensure_ascii=False),
    }
    return llm.json(RUTA_PROMPT.read_text(encoding="utf-8"), f'Pedido: "{texto}"', ESQUEMA_PEDIDO,
                    variables=variables)
