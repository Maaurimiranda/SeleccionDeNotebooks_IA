"""Cuenta nodos por label y relaciones por tipo, y compara dos conteos (PG3-05, criterio de PG3-02).

Sirve para probar que los archivos de cypher/ dan el mismo grafo que el canónico entero.

Sin Neo4j (y sin tocar la base): python -m scripts.contar_grafo --sentencias
compara las sentencias del canónico (hasta el bloque 10) con las de cypher/, una por una. Si el
corte está bien hecho, solo difieren los arreglos de D-06. Es la prueba más fuerte: un conteo no
detecta que cambie el contenido de una propiedad.

Con Neo4j (borra la base dos veces):
  1. python -m scripts.cargar_grafo --canonico   (borra y carga el canónico hasta el bloque 10)
  2. python -m scripts.contar_grafo --guardar docs/pruebas/conteos_canonico.json
  3. python -m scripts.cargar_grafo              (borra y carga cypher/)
  4. python -m scripts.contar_grafo --guardar docs/pruebas/conteos_dividido.json
  5. python -m scripts.contar_grafo --comparar docs/pruebas/conteos_canonico.json docs/pruebas/conteos_dividido.json

`--comparar` imprime la tabla en Markdown (va a docs/pruebas/conteos_grafo.md) y sale con 1 si algo difiere.
"""
import argparse
import json
import sys
from collections import Counter
from pathlib import Path

NODOS = "MATCH (n) UNWIND labels(n) AS clave RETURN clave, count(*) AS n"
RELACIONES = "MATCH ()-[r]->() RETURN type(r) AS clave, count(*) AS n"


def contar(grafo) -> dict:
    """Conteos del grafo cargado. Un nodo con dos labels cuenta una vez por cada label."""
    return {
        "nodos": {f["clave"]: f["n"] for f in grafo.leer(NODOS)},
        "relaciones": {f["clave"]: f["n"] for f in grafo.leer(RELACIONES)},
        "total_nodos": grafo.leer("MATCH (n) RETURN count(n) AS n")[0]["n"],
        "total_relaciones": grafo.leer("MATCH ()-[r]->() RETURN count(r) AS n")[0]["n"],
    }


def comparar(a: dict, b: dict) -> tuple[str, bool]:
    """Tabla en Markdown con los dos conteos y si coinciden. Devuelve (tabla, todo_igual)."""
    filas = [("Total", "nodos", a["total_nodos"], b["total_nodos"]),
             ("Total", "relaciones", a["total_relaciones"], b["total_relaciones"])]
    for seccion, titulo in (("nodos", "label"), ("relaciones", "relación")):
        for clave in sorted(set(a[seccion]) | set(b[seccion])):
            filas.append((titulo, clave, a[seccion].get(clave, 0), b[seccion].get(clave, 0)))
    lineas = ["| Qué | Clave | Canónico | Dividido | OK |", "| --- | --- | ---: | ---: | --- |"]
    lineas += [f"| {q} | {k} | {x} | {y} | {'sí' if x == y else '**NO**'} |" for q, k, x, y in filas]
    return "\n".join(lineas), all(x == y for _, _, x, y in filas)


def _normalizar(texto: str) -> str:
    return " ".join(texto.split())


def diferencias_sentencias() -> tuple[int, int, list[str], list[str]]:
    """(total canónico, total dividido, solo en el canónico, solo en cypher/), con espacios normalizados."""
    from scripts.cargar_grafo import archivos, sentencias, sentencias_canonico
    canonico = Counter(_normalizar(t) for _, t in sentencias_canonico())
    dividido = Counter(_normalizar(t) for ruta in archivos() for _, t in sentencias(ruta))
    return (sum(canonico.values()), sum(dividido.values()),
            list((canonico - dividido).elements()), list((dividido - canonico).elements()))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--sentencias", action="store_true", help="compara las sentencias, sin Neo4j")
    g.add_argument("--guardar", metavar="ARCHIVO.json", help="cuenta el grafo cargado y guarda el resultado")
    g.add_argument("--comparar", nargs=2, metavar=("CANONICO.json", "DIVIDIDO.json"))
    args = ap.parse_args()
    if args.sentencias:
        total_c, total_d, solo_c, solo_d = diferencias_sentencias()
        print(f"Canónico (hasta el bloque 10): {total_c} sentencias. cypher/: {total_d} sentencias.")
        for titulo, lista in (("Solo en el canónico", solo_c), ("Solo en cypher/", solo_d)):
            print(f"\n{titulo}: {len(lista)}")
            for t in lista:
                print(f"  - {t[:110]}{'…' if len(t) > 110 else ''}")
        return
    if args.comparar:
        a, b = (json.loads(Path(r).read_text(encoding="utf-8")) for r in args.comparar)
        tabla, igual = comparar(a, b)
        print(tabla)
        sys.exit(0 if igual else 1)
    from asistente import config
    from asistente.contrato import ErrorGrafo
    from asistente.grafo import Grafo
    if not config.NEO4J_PASSWORD:
        sys.exit("Falta NEO4J_PASSWORD en el entorno (ver .env.example).")
    grafo = Grafo()
    try:
        datos = contar(grafo)
    except ErrorGrafo as e:
        sys.exit(f"No pude contar el grafo: {e}")
    finally:
        grafo.cerrar()
    Path(args.guardar).parent.mkdir(parents=True, exist_ok=True)
    Path(args.guardar).write_text(json.dumps(datos, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{datos['total_nodos']} nodos y {datos['total_relaciones']} relaciones -> {args.guardar}")


if __name__ == "__main__":
    main()
