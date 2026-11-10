"""Ayudas compartidas por los paquetes de submódulos (no es un submódulo).

- `leer_consulta`: ejecuta un Cypher fijo y devuelve el registro `Consulta` de la traza.
- `redondear` y `rango`: reglas de la evidencia de ARQUITECTURA §4.1.
"""
from typing import Any, TypedDict


class Consulta(TypedDict):
    nombre: str          # "SM2.C2"
    cypher: str
    parametros: dict
    filas: list[dict]


def leer_consulta(grafo, sm: str, nombre: str, cypher: str, parametros: dict) -> Consulta:
    filas = grafo.leer(cypher, parametros)
    return {"nombre": f"{sm}.{nombre}", "cypher": cypher.strip(), "parametros": dict(parametros), "filas": filas}


def redondear(x: Any, nd: int = 3) -> Any:
    """Números como los devuelve el grafo, redondeados a 3 decimales. Lo demás, intacto."""
    if isinstance(x, bool) or x is None:
        return x
    if isinstance(x, float):
        return round(x, nd)
    if isinstance(x, list):
        return [redondear(v, nd) for v in x]
    if isinstance(x, dict):
        return {k: redondear(v, nd) for k, v in x.items()}
    return x


def rango(valor: Any, minimo: Any, maximo: Any) -> Any:
    """Un valor puntual, o {"min","max"} si el grafo lo dejó como rango. Nunca promedia."""
    if valor is not None:
        return redondear(valor)
    if minimo is None and maximo is None:
        return None
    return {"min": redondear(minimo), "max": redondear(maximo)}
