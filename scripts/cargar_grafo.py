"""Carga el grafo canónico dividido por dueño (PG3-02, ARQUITECTURA §5).

Ejecuta cypher/NN_*.cypher en orden numérico, sentencia por sentencia. Una sentencia
termina en ';' al final de la línea; las líneas que empiezan con '//' se ignoran.
cypher/90_verificacion.cypher no se carga: son consultas (C1 escribe INCUMPLE y se
deja para la demostración) y las corre scripts/verificar_grafo.py.

Uso:  python -m scripts.cargar_grafo [--hasta 40]
"""
import argparse
import sys
from pathlib import Path

from neo4j import GraphDatabase

from asistente import config

DIR_CYPHER = Path(__file__).resolve().parent.parent / "cypher"
NO_SE_CARGAN = {"90_verificacion.cypher"}


def sentencias(ruta: Path):
    """Devuelve [(linea_inicial, texto)] de las sentencias del archivo."""
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


def archivos(hasta: int | None = None):
    for ruta in sorted(DIR_CYPHER.glob("[0-9][0-9]_*.cypher")):
        if ruta.name in NO_SE_CARGAN:
            continue
        if hasta is not None and int(ruta.name[:2]) > hasta:
            continue
        yield ruta


def cargar(driver, hasta: int | None = None, verbose: bool = True) -> int:
    total = 0
    with driver.session(database=config.NEO4J_DATABASE) as s:
        for ruta in archivos(hasta):
            lista = sentencias(ruta)
            for linea, texto in lista:
                try:
                    s.run(texto).consume()
                except Exception as e:
                    raise SystemExit(f"ERROR en {ruta.name}, línea {linea}: {type(e).__name__}: {e}")
            total += len(lista)
            if verbose:
                print(f"  {ruta.name}: {len(lista)} sentencias")
    return total


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--hasta", type=int, help="último prefijo numérico a cargar (por ejemplo 20)")
    args = ap.parse_args()
    if not config.NEO4J_PASSWORD:
        sys.exit("Falta NEO4J_PASSWORD en el entorno (ver .env.example).")
    driver = GraphDatabase.driver(config.NEO4J_URI, auth=(config.NEO4J_USER, config.NEO4J_PASSWORD),
                                  notifications_min_severity="OFF")
    try:
        print(f"Cargando el grafo en {config.NEO4J_URI} ...")
        n = cargar(driver, args.hasta)
        print(f"Listo: {n} sentencias.")
    finally:
        driver.close()


if __name__ == "__main__":
    main()
