"""SM4 · Servicio (STUB de PG3-01): devuelve tests/fixtures/SM4.<intencion>.json.

Cumple la firma del contrato para que el orquestador corra de punta a punta.
"""
import json
from pathlib import Path

DIR_FIXTURES = Path(__file__).resolve().parents[3] / "tests" / "fixtures"


def desde_fixture(intencion: str, p: dict) -> tuple[list, dict]:
    datos = json.loads((DIR_FIXTURES / f"{intencion}.json").read_text(encoding="utf-8"))
    evidencia = dict(datos["evidencia"])
    evidencia["requerimiento_id"] = p.get("requerimiento_id")
    return list(datos["consultas"]), evidencia
