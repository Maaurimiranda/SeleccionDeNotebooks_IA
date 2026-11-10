"""Traza de cada consulta del usuario (D-07 §9, ARQUITECTURA §8).

Una línea JSON por consulta en DIR_TRAZAS/AAAA-MM-DD.jsonl.
"""
import json
from datetime import date, datetime
from pathlib import Path

from asistente import config


def nueva(texto: str) -> dict:
    return {
        "fecha": datetime.now().isoformat(timespec="seconds"),
        "consulta_usuario": texto,
        "plan": None,
        "validacion": {"observaciones": [], "aclaracion": None},
        "consultas": [],          # [{sm, intencion, nombre, cypher, parametros, filas, ms}]
        "evidencia": None,
        "intentos": [],           # [{texto, problemas}]
        "respuesta": None,
        "origen_respuesta": None,
        "duracion_ms": {},        # {plan, consultas, explicacion}
        "error": None,
        "segundos": None,
    }


def escribir(registro: dict, directorio: str | None = None) -> Path:
    carpeta = Path(directorio or config.DIR_TRAZAS)
    carpeta.mkdir(parents=True, exist_ok=True)
    ruta = carpeta / f"{date.today().isoformat()}.jsonl"
    with ruta.open("a", encoding="utf-8") as f:
        f.write(json.dumps(registro, ensure_ascii=False, default=str) + "\n")
    return ruta
