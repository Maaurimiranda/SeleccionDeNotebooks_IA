"""PG3-17: exporta el grafo y arma los datos de ejemplo (consigna §4, ítems i y j).

    python -m scripts.exportar_grafo

Escribe, con Cypher estándar y el driver (sin APOC, RESTRICCIONES §5):
- datos/export/nodos.csv y relaciones.csv  (ítem i)
- datos/salida_pi2.csv, datos/consultas_ejemplo.csv y datos/traza_ejemplo.jsonl  (ítem j)
"""
import csv
import json
from pathlib import Path

from asistente.grafo import Grafo

RAIZ = Path(__file__).resolve().parent.parent
DATOS = RAIZ / "datos"

NODOS = "MATCH (n) RETURN elementId(n) AS id, labels(n) AS labels, properties(n) AS props ORDER BY id"
RELACIONES = ("MATCH (a)-[r]->(b) RETURN elementId(a) AS origen, type(r) AS tipo, elementId(b) AS destino, "
              "properties(r) AS props ORDER BY origen, tipo, destino")
SALIDA_PI2 = """
MATCH (c:Requerimiento)-[:EVALUA]->(ev:Evaluacion)-[:SOBRE]->(n:Notebook)
RETURN c.id AS requerimiento, n.modelo AS notebook, ev.estado AS estado,
       ev.grado_recomendacion AS grado, ev.grado_recomendacion_min AS grado_min, ev.grado_recomendacion_max AS grado_max,
       ev.adecuacion_global AS adecuacion_global, ev.excedente_presupuesto AS excedente_presupuesto_pct,
       ev.indice_costo_beneficio AS indice_costo_beneficio
ORDER BY requerimiento, notebook
"""


def _json(x) -> str:
    return json.dumps(x, ensure_ascii=False, sort_keys=True, default=str)


def _escribir(ruta: Path, columnas: list[str], filas: list[list]):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with ruta.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(columnas)
        w.writerows(filas)
    print(f"  {ruta.relative_to(RAIZ)} ({len(filas)} filas)")


def main():
    from scripts.correr_e2e import CASOS
    g = Grafo()
    try:
        _escribir(DATOS / "export" / "nodos.csv", ["id", "labels", "propiedades"],
                  [[f["id"], "|".join(f["labels"]), _json(f["props"])] for f in g.leer(NODOS)])
        _escribir(DATOS / "export" / "relaciones.csv", ["origen", "tipo", "destino", "propiedades"],
                  [[f["origen"], f["tipo"], f["destino"], _json(f["props"])] for f in g.leer(RELACIONES)])
        cols = ["requerimiento", "notebook", "estado", "grado", "grado_min", "grado_max", "adecuacion_global",
                "excedente_presupuesto_pct", "indice_costo_beneficio"]
        _escribir(DATOS / "salida_pi2.csv", cols, [[f[c] for c in cols] for f in g.leer(SALIDA_PI2)])
    finally:
        g.cerrar()
    _escribir(DATOS / "consultas_ejemplo.csv", ["id", "tipo", "consulta", "esperado"],
              [[c["id"], c["tipo"], c["texto"], " | ".join(d for d, _ in c["esperado"]())] for c in CASOS])
    trazas = sorted((RAIZ / "docs" / "pruebas" / "trazas").glob("*.jsonl"))
    if trazas:
        lineas = trazas[-1].read_text(encoding="utf-8").splitlines()
        (DATOS / "traza_ejemplo.jsonl").write_text("\n".join(lineas[:1]) + "\n", encoding="utf-8")
        print("  datos/traza_ejemplo.jsonl (1 traza)")
    else:
        print("  Sin trazas en docs/pruebas/trazas: corré antes `python -m scripts.correr_e2e`.")


if __name__ == "__main__":
    main()
