"""Regresión CP1–CP11 sobre el grafo cargado (PG3-02).

Compara lo que devuelve el grafo con los esperados de PG1/PG2 §9.4
(docs/contexto/Contexto_PG1_PG2_Grupo_para_PG3.md) e imprime una tabla
esperado / obtenido / OK. Solo lee: no corre C1 (que escribe INCUMPLE).

Uso:  python -m scripts.verificar_grafo      (sale con código 1 si algún CP falla)
"""
import sys

from neo4j import GraphDatabase, READ_ACCESS

from asistente import config

# Cada CP: (id, descripcion, cypher, funcion(filas) -> obtenido, esperado)
EV_REQ01 = """
MATCH (:Requerimiento {id:'req_01'})-[:EVALUA]->(ev:Evaluacion)-[:SOBRE]->(n:Notebook {modelo:$m})
OPTIONAL MATCH (:Recomendacion)-[p:PROPONE|PROPONE_FUERA_DE_PRESUPUESTO]->(n)
OPTIONAL MATCH (al:Alerta) WHERE EXISTS { MATCH (ev)-[:GENERA]->(al) } OR EXISTS { MATCH (n)-[:GENERA]->(al) }
RETURN ev.estado AS estado, ev.etiqueta_recomendacion AS etiqueta,
       ev.grado_recomendacion AS grado, ev.grado_recomendacion_min AS gmin, ev.grado_recomendacion_max AS gmax,
       ev.riesgo_valor AS riesgo, ev.riesgo_min AS rmin, ev.riesgo_max AS rmax, ev.riesgo_etiqueta AS retq,
       ev.adecuacion_global AS global, ev.excluyente_virtualizacion AS excl,
       n.adecuacion_movilidad AS mov, n.peso_kg AS peso,
       type(p) AS propuesta, p.orden AS orden,
       collect(DISTINCT al.regla_origen) AS alertas
"""


def _uno(filas):
    return filas[0] if filas else {}


def cp(id_, desc, cypher, params, obtener, esperado):
    return {"id": id_, "desc": desc, "cypher": cypher, "params": params, "obtener": obtener, "esperado": esperado}


CPS = [
    cp("CP1", "A cumple todo: Alta, 0,785, puesto 1", EV_REQ01, {"m": "Notebook_A"},
       lambda f: (_uno(f).get("estado"), _uno(f).get("grado"), _uno(f).get("orden")),
       ("Recomendada (Alta)", 0.785, 1)),
    cp("CP2", "E sin virtualizacion: descartada pese a 0,81", EV_REQ01, {"m": "Notebook_E"},
       lambda f: (_uno(f).get("estado"), _uno(f).get("excl")),
       ("Descartada (excluyente incumplido)", "no cumple")),
    cp("CP3", "X 5 % sobre presupuesto: alternativa, no primera", EV_REQ01, {"m": "Notebook_X"},
       lambda f: (_uno(f).get("grado"), _uno(f).get("propuesta")),
       (0.534, "PROPONE_FUERA_DE_PRESUPUESTO")),
    cp("CP4", "G: indeterminada, riesgo [49,58 ; 81,46], alertas REN-R10 y FZ-R7", EV_REQ01, {"m": "Notebook_G"},
       lambda f: (_uno(f).get("estado"), _uno(f).get("rmin"), _uno(f).get("rmax"),
                  sorted(a for a in _uno(f).get("alertas", []) if a in ("REN-R10", "FZ-R7", "REN-R13"))),
       ("Indeterminada: completar informacion", 49.58, 81.46, ["FZ-R7", "REN-R10"])),
    cp("CP5", "K con 8 GB y ranura libre: riesgo 49,55 medio", EV_REQ01, {"m": "Notebook_K"},
       lambda f: (_uno(f).get("riesgo"), _uno(f).get("retq")), (49.55, "medio")),
    cp("CP6", "C con 2,3 kg y 5 h: movilidad 0,231", EV_REQ01, {"m": "Notebook_C"},
       lambda f: (_uno(f).get("mov"),), (0.231,)),
    cp("CP7", "Desempate por ampliabilidad: A 1, H 2, B 3",
       "MATCH (:Recomendacion)-[p:PROPONE]->(n:Notebook) RETURN n.modelo AS m, p.orden AS o ORDER BY o", {},
       lambda f: tuple(r["m"] for r in f), ("Notebook_A", "Notebook_H", "Notebook_B")),
    cp("CP8", "47 etiquetas sin validar en 15 variables",
       "MATCH (e:EtiquetaDifusa) WHERE e.estado_validacion = 'sin validar' "
       "RETURN count(e) AS n, count(DISTINCT e.variable) AS v", {},
       lambda f: (_uno(f).get("n"), _uno(f).get("v")), (47, 15)),
    cp("CP9", "M sin autonomia: condicionada, grado [0,504 ; 0,826]", EV_REQ01, {"m": "Notebook_M"},
       lambda f: (_uno(f).get("estado"), _uno(f).get("gmin"), _uno(f).get("gmax")),
       ("Recomendada condicionada por falta de informacion", 0.504, 0.826)),
    cp("CP10", "req_02: perfil indeterminado, 0 evaluadas, pregunta pendiente",
       "MATCH (c:Requerimiento {id:'req_02'}) OPTIONAL MATCH (c)-[:EVALUA]->(ev:Evaluacion) "
       "OPTIONAL MATCH (c)-[:REQUIERE_ACLARACION]->(q:Pregunta) "
       "RETURN c.perfil_dominante AS p, count(DISTINCT ev) AS n, count(DISTINCT q) > 0 AS preg", {},
       lambda f: (_uno(f).get("p"), _uno(f).get("n"), _uno(f).get("preg")), ("indeterminado", 0, True)),
    cp("CP11", "K: Media 0,469 para req_03 y Descartada (a secas) para req_01",
       "MATCH (c:Requerimiento)-[:EVALUA]->(ev:Evaluacion)-[:SOBRE]->(:Notebook {modelo:'Notebook_K'}) "
       "RETURN c.id AS req, ev.estado AS estado, ev.grado_recomendacion AS grado ORDER BY req", {},
       lambda f: tuple((r["req"], r["estado"], r["grado"] if r["req"] == "req_03" else None) for r in f),
       (("req_01", "Descartada", None), ("req_03", "Recomendada (Media)", 0.469))),
]


def _aprox(a, b):
    if isinstance(a, float) or isinstance(b, float):
        try:
            return abs(float(a) - float(b)) < 0.0015
        except (TypeError, ValueError):
            return False
    if isinstance(a, (tuple, list)) and isinstance(b, (tuple, list)):
        return len(a) == len(b) and all(_aprox(x, y) for x, y in zip(a, b))
    return a == b


def verificar(driver) -> list[dict]:
    resultados = []
    with driver.session(database=config.NEO4J_DATABASE, default_access_mode=READ_ACCESS) as s:
        for c in CPS:
            filas = s.execute_read(lambda tx: [r.data() for r in tx.run(c["cypher"], **c["params"])])
            obtenido = c["obtener"](filas)
            resultados.append({"id": c["id"], "desc": c["desc"], "esperado": c["esperado"],
                               "obtenido": obtenido, "ok": _aprox(obtenido, c["esperado"])})
    return resultados


def main():
    driver = GraphDatabase.driver(config.NEO4J_URI, auth=(config.NEO4J_USER, config.NEO4J_PASSWORD),
                                  notifications_min_severity="OFF")
    try:
        res = verificar(driver)
    finally:
        driver.close()
    print("| CP | Caso | Esperado | Obtenido | OK |\n| --- | --- | --- | --- | --- |")
    for r in res:
        print(f"| {r['id']} | {r['desc']} | {r['esperado']} | {r['obtenido']} | {'OK' if r['ok'] else 'FALLA'} |")
    fallas = [r["id"] for r in res if not r["ok"]]
    print(f"\n{len(res) - len(fallas)}/{len(res)} OK" + (f" · fallan: {', '.join(fallas)}" if fallas else ""))
    sys.exit(1 if fallas else 0)


if __name__ == "__main__":
    main()
