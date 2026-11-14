"""Inferencia bajo demanda para un pedido (D-08, issues #15 a #19).

Los archivos de inferencia de cypher/ (10, 15, 20, 30 y 40) aceptan el parámetro `$req`:
- `req = None` (lo que hace scripts/cargar_grafo.py): corre para todos los pedidos, como siempre;
- `req = "req_101"`: las sentencias que parten de un `Requerimiento` corren solo para ese pedido.

Las sentencias que no parten de un pedido (fuzificación de juegos, actividades, notebooks y
evaluaciones) siguen corriendo sobre todo el grafo. Son idempotentes (solo `MERGE` y `SET` con los
mismos valores), así que volver a correrlas no cambia los pedidos que ya estaban: lo controla
tests/test_inferencia.py contra un Neo4j real.

Este módulo es el único que conoce el separador de sentencias: lo usan cargar_grafo.py y SM1.
"""
import re
import time
from pathlib import Path

DIR_CYPHER = Path(__file__).resolve().parent.parent / "cypher"
ARCHIVOS_INFERENCIA = ["10_sm1.cypher", "15_evaluaciones.cypher", "20_sm2.cypher", "30_sm3.cypher",
                       "40_sm4.cypher"]

# El filtro que se agregó a los archivos, con la forma exacta en que aparece.
FILTRO_REQ = "($req IS NULL OR c.id = $req)"


def sentencias(ruta: Path) -> list[tuple[int, str]]:
    """Devuelve [(linea_inicial, texto)] de las sentencias del archivo.

    Una sentencia termina en ';' al final de la línea; las líneas que empiezan con '//' se ignoran.
    """
    resultado, actual, inicio = [], [], None
    for n, linea in enumerate(ruta.read_text(encoding="utf-8").splitlines(), start=1):
        if not actual and (not linea.strip() or linea.strip().startswith("//")):
            continue
        if linea.strip().startswith("//"):
            continue
        if inicio is None:
            inicio = n
        actual.append(linea)
        if linea.rstrip().endswith(";"):
            texto = "\n".join(actual).rstrip().rstrip(";")
            resultado.append((inicio, texto))
            actual, inicio = [], None
    if actual:
        resultado.append((inicio, "\n".join(actual)))
    return resultado


def sin_filtro_req(texto: str) -> str:
    """La sentencia como estaba en el canónico de PG2, sin el filtro por `$req` (para scripts/contar_grafo.py)."""
    f = re.escape(FILTRO_REQ)
    texto = re.sub(r"\nWHERE " + f + r"\n  AND ", "\nWHERE ", texto)   # WHERE propio en la línea siguiente
    texto = re.sub(r" WHERE " + f + r" AND ", " WHERE ", texto)        # WHERE en la misma línea
    texto = re.sub(r"\nWHERE " + f + r"(?=\n|$)", "", texto)          # el filtro era el único WHERE
    return texto


def sentencias_inferencia() -> list[tuple[str, int, str]]:
    """[(archivo, linea, texto)] de los archivos de inferencia, en orden."""
    return [(nombre, linea, texto) for nombre in ARCHIVOS_INFERENCIA
            for linea, texto in sentencias(DIR_CYPHER / nombre)]


def inferir(grafo, req: str) -> dict:
    """Recalcula SM1 → SM2 → SM3 → SM4 para el pedido `req`, en una sola transacción de escritura.

    Devuelve {"requerimiento_id", "sentencias", "ms"}. Si una sentencia falla, no queda nada a medias
    (la transacción se deshace) y se lanza ErrorGrafo con el archivo y la línea.
    """
    if not req:
        raise ValueError("inferir() necesita un pedido: la inferencia de todos los pedidos la hace cargar_grafo")
    lista = sentencias_inferencia()
    t0 = time.perf_counter()
    grafo.escribir_lote([(f"{a}:{l}", t) for a, l, t in lista], {"req": req})
    return {"requerimiento_id": req, "sentencias": len(lista), "ms": int((time.perf_counter() - t0) * 1000)}
