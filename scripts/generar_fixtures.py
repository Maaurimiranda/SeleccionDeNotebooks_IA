"""Regenera tests/fixtures/ con filas REALES del grafo cargado (PG3-01, 03, 04, 07, 09).

Cada fixture tiene la forma {"parametros", "consultas", "evidencia"}: la salida de
ejecutar() para esos parámetros. Los tests offline la usan con un Grafo falso.
SM4 no se regenera hasta PG3-12 (su servicio es un stub).

Uso:  python -m scripts.generar_fixtures
"""
import json
from pathlib import Path

from asistente.grafo import Grafo
from asistente.submodulos import grupo, sm1, sm2, sm3

DIR = Path(__file__).resolve().parent.parent / "tests" / "fixtures"

CASOS = [
    ("SM1.interpretacion_pedido", sm1, {"requerimiento_id": "req_01"}, "SM1.interpretacion_pedido"),
    ("SM1.interpretacion_pedido", sm1, {"requerimiento_id": "req_02"}, "SM1.interpretacion_pedido.req_02"),
    ("SM2.riesgo_ram", sm2, {"requerimiento_id": "req_01", "modelos": ["Notebook_G"]}, "SM2.riesgo_ram"),
    ("SM2.riesgo_ram", sm2, {"requerimiento_id": "req_01"}, "SM2.riesgo_ram.todas"),
    ("SM2.virtualizacion", sm2, {"requerimiento_id": "req_01"}, "SM2.virtualizacion"),
    ("SM3.buscar", sm3, {"requerimiento_id": "req_01", "orden": "grafica", "filtros": {"dedicada": True}},
     "SM3.buscar"),
    ("SM3.buscar", sm3, {"requerimiento_id": "req_01", "orden": "grafica"}, "SM3.buscar.sin_filtros"),
    ("SM3.ficha", sm3, {"requerimiento_id": "req_01", "modelo": "Notebook_M"}, "SM3.ficha"),
    ("GRUPO.traza_reglas", grupo, {"requerimiento_id": "req_01", "modelo": "Notebook_A"}, "GRUPO.traza_reglas"),
    ("GRUPO.parametros", grupo, {}, "GRUPO.parametros"),
]


def main():
    g = Grafo()
    DIR.mkdir(parents=True, exist_ok=True)
    try:
        for intencion, modulo, parametros, archivo in CASOS:
            salida = modulo.ejecutar(intencion, parametros, g)
            datos = {"intencion": intencion, "parametros": parametros, **salida}
            (DIR / f"{archivo}.json").write_text(json.dumps(datos, ensure_ascii=False, indent=1, default=str) + "\n",
                                                 encoding="utf-8")
            print(f"  {archivo}.json")
    finally:
        g.cerrar()


if __name__ == "__main__":
    main()
