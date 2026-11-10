"""Carga el grafo canónico dividido por dueño (PG3-02, ARQUITECTURA §5).

Ejecuta cypher/NN_*.cypher en orden numérico, sentencia por sentencia. Una sentencia
termina en ';' al final de la línea; las líneas que empiezan con '//' se ignoran.
cypher/90_verificacion.cypher no se carga: son consultas (C1 escribe INCUMPLE y se
deja para la demostración) y las corre scripts/verificar_grafo.py.

Uso:  python -m scripts.cargar_grafo [--hasta 40]
      python -m scripts.cargar_grafo --canonico    (el canónico entero hasta el bloque 10, para PG3-05)

Las dos formas empiezan con el bloque 0 (limpieza): BORRAN la base antes de cargar.
"""
import argparse
import sys
from pathlib import Path

from neo4j import GraphDatabase

from asistente import config

DIR_CYPHER = Path(__file__).resolve().parent.parent / "cypher"
NO_SE_CARGAN = {"90_verificacion.cypher"}
CANONICO = DIR_CYPHER.parent / "docs" / "cypher" / "Grupo_2_PG2_U1_corregido.cypher"
INICIO_CONSULTAS = "// 11. CONSULTAS"   # del bloque 11 en adelante son consultas; C1 escribe INCUMPLE


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


def _ejecutar(s, nombre: str, lista: list, verbose: bool) -> int:
    for linea, texto in lista:
        try:
            s.run(texto).consume()
        except Exception as e:
            raise SystemExit(f"ERROR en {nombre}, línea {linea}: {type(e).__name__}: {e}")
    if verbose:
        print(f"  {nombre}: {len(lista)} sentencias")
    return len(lista)


def cargar(driver, hasta: int | None = None, verbose: bool = True) -> int:
    with driver.session(database=config.NEO4J_DATABASE) as s:
        return sum(_ejecutar(s, ruta.name, sentencias(ruta), verbose) for ruta in archivos(hasta))


def sentencias_canonico() -> list:
    """Las sentencias del canónico entero hasta el bloque 10 (del 11 en adelante son consultas)."""
    lineas = CANONICO.read_text(encoding="utf-8").splitlines()
    corte = next((n for n, linea in enumerate(lineas, start=1) if linea.startswith(INICIO_CONSULTAS)), None)
    if corte is None:
        raise SystemExit(f"No encontré la línea «{INICIO_CONSULTAS}…» en {CANONICO.name}: "
                         "no sé dónde terminan las cargas y empiezan las consultas.")
    return [(n, t) for n, t in sentencias(CANONICO) if n < corte]


def cargar_canonico(driver, verbose: bool = True) -> int:
    """El canónico entero hasta el bloque 10, para comparar sus conteos con los de cypher/ (PG3-05)."""
    with driver.session(database=config.NEO4J_DATABASE) as s:
        return _ejecutar(s, CANONICO.name, sentencias_canonico(), verbose)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--hasta", type=int, help="último prefijo numérico a cargar (por ejemplo 20)")
    ap.add_argument("--canonico", action="store_true", help="cargar el canónico entero en vez de cypher/")
    args = ap.parse_args()
    if not config.NEO4J_PASSWORD:
        sys.exit("Falta NEO4J_PASSWORD en el entorno (ver .env.example).")
    driver = GraphDatabase.driver(config.NEO4J_URI, auth=(config.NEO4J_USER, config.NEO4J_PASSWORD),
                                  notifications_min_severity="OFF")
    try:
        print(f"Cargando el grafo en {config.NEO4J_URI} ...")
        n = cargar_canonico(driver) if args.canonico else cargar(driver, args.hasta)
        print(f"Listo: {n} sentencias.")
    finally:
        driver.close()


if __name__ == "__main__":
    main()
