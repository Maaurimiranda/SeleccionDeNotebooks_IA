"""Propuesta provisional de SALIDA_PI2 para los 6 perfiles que faltan (D-03, PG3-25).

Sin estos datos, un pedido cuyo perfil dominante no es VIRT (por ejemplo DEV) no evalúa ninguna notebook y
no tiene ranking. La decisión del grupo (D-03) es que SM2 y SM3 completen la planilla con sus reglas de PI2.
Mientras tanto, este script la completa con un método explícito y deja cada valor marcado 'sin validar':

Rendimiento (SM2, Contexto SM2 §6.3, con los requisitos del grafo canónico y el alcance de D-02):
  - CPU: brecha de gama contra la gama mínima del perfil (REN-R3): 0 niveles 1,0; 1 nivel 0,6; 2 niveles 0,2.
    Núcleos y carga sostenida (REN-R4, REN-R8) están fuera del prototipo.
  - RAM (M = mínimo, R = recomendado del perfil): >= R 1,0; M <= RAM < R 0,7; M/2 < RAM < M lineal hasta 0,7;
    <= M/2 0. REN-R7: por debajo del mínimo y ampliable hasta M, al menos 0,5. REN-R9 está retirada (sin +0,1).
    Con ampliabilidad desconocida no se aplica REN-R7 (no se supone que se pueda ampliar).
  - SSD (el canónico solo guarda el mínimo M; el recomendado está fuera del prototipo): >= M 1,0;
    M/2 <= SSD < M 0,4; < M/2 0.
  - Rendimiento = 0,35·CPU + 0,40·RAM + 0,25·SSD (SP6), con 2 decimales.

Pantalla (SM3):
  - OFI, DEV y DATOS no exigen nada de la pantalla, igual que VIRT: se usa el grado de VIRT de esa notebook
    (es lo que ya hace el supuesto K–OFI, 0,90).
  - DIS y VID3D: fidelidad de color, min(1, sRGB / 95) (sRGB >= 95 % es el umbral de diseño de SM3).
  - GAM: tasa de refresco, min(1, Hz / 144).

K–OFI no se toca: es el supuesto del grupo para CP11. Los nueve pares de VIRT tampoco.

Uso (con la base cargada):  python -m scripts.proponer_salida_pi2
Escribe cypher/03_salida_pi2_provisional.cypher y actualiza docs/cypher/salida_pi2.csv.
"""
import csv
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CYPHER = RAIZ / "cypher" / "03_salida_pi2_provisional.cypher"
PLANILLA = RAIZ / "docs" / "cypher" / "salida_pi2.csv"

PERFILES = ["OFI", "DEV", "DIS", "VID3D", "GAM", "DATOS"]
GAMAS = {"entrada": 0, "media": 1, "alta": 2}
BRECHA = {0: 1.0, 1: 0.6, 2: 0.2}
PESOS = {"cpu": 0.35, "ram": 0.40, "ssd": 0.25}
SRGB_DISENO, HZ_JUEGOS = 95, 144
ORIGEN_REND = "Propuesta provisional SP6 (Contexto SM2 6.3), sin validar por SM2"
ORIGEN_PANT = {
    "igual": "Propuesta provisional: igual que VIRT (el perfil no exige pantalla), sin validar por SM3",
    "srgb": "Propuesta provisional: min(1, sRGB/95), sin validar por SM3",
    "hz": "Propuesta provisional: min(1, Hz/144), sin validar por SM3",
}

CATALOGO = """
MATCH (n:Notebook)-[:POSEE]->(cpu:CPU), (n)-[:POSEE]->(r:RAM), (n)-[:POSEE]->(a:Almacenamiento),
      (n)-[:POSEE]->(p:Pantalla), (n)-[v:SALIDA_PI2]->(:Perfil {codigo:'VIRT'})
RETURN n.modelo AS modelo, cpu.gama AS gama, r.ram_gb AS ram, r.ampliabilidad AS ampliabilidad,
       r.max_gb AS max_gb, r.ranuras_libres AS ranuras, a.capacidad_gb AS ssd, a.tipo AS tipo_alm,
       p.srgb AS srgb, p.refresco_hz AS hz, v.grado_pantalla AS pantalla_virt
ORDER BY modelo
"""
REQUISITOS = """
MATCH (p:Perfil)-[:EXIGE]->(q:Requisito) WHERE q.criterio IN ['gama_cpu', 'ram_gb', 'ssd_gb']
RETURN p.codigo AS perfil, q.criterio AS criterio, q.valor_texto AS texto, q.valor_min AS minimo,
       q.valor_rec AS rec
ORDER BY perfil, criterio
"""


def grado_cpu(gama: str, minima: str) -> float:
    return BRECHA.get(max(0, GAMAS[minima] - GAMAS[gama]), 0.0)


def grado_ram(n: dict, m: int, r: int) -> float:
    ram = n["ram"]
    if ram >= r:
        g = 1.0
    elif ram >= m:
        g = 0.7
    elif ram > m / 2:
        g = (ram - m / 2) / (m / 2) * 0.7
    else:
        g = 0.0
    ampliable_hasta_m = (n["ampliabilidad"] == "ampliable" and (n["max_gb"] or 0) >= m and (n["ranuras"] or 0) >= 1)
    if ram < m and ampliable_hasta_m:  # REN-R7
        g = max(g, 0.5)
    return g


def grado_ssd(n: dict, m: int) -> float:
    g = 1.0 if n["ssd"] >= m else 0.4 if n["ssd"] >= m / 2 else 0.0
    return g * 0.3 if n["tipo_alm"] == "HDD" else g  # REN-R5


def rendimiento(n: dict, req: dict) -> float:
    g = (PESOS["cpu"] * grado_cpu(n["gama"], req["gama_cpu"]) + PESOS["ram"] * grado_ram(n, *req["ram_gb"])
         + PESOS["ssd"] * grado_ssd(n, req["ssd_gb"]))
    return round(g, 2)


def pantalla(n: dict, perfil: str) -> tuple[float, str]:
    if perfil in ("DIS", "VID3D"):
        return round(min(1.0, n["srgb"] / SRGB_DISENO), 2), "srgb"
    if perfil == "GAM":
        return round(min(1.0, n["hz"] / HZ_JUEGOS), 2), "hz"
    return n["pantalla_virt"], "igual"


def requisitos(filas: list[dict]) -> dict:
    req: dict = {}
    for f in filas:
        r = req.setdefault(f["perfil"], {})
        r[f["criterio"]] = (f["texto"] if f["criterio"] == "gama_cpu" else
                            (f["minimo"], f["rec"]) if f["criterio"] == "ram_gb" else f["minimo"])
    return req


def proponer(catalogo: list[dict], req: dict) -> list[dict]:
    filas = []
    for perfil in PERFILES:
        for n in catalogo:
            if (n["modelo"], perfil) == ("Notebook_K", "OFI"):
                continue  # supuesto del grupo para CP11, se deja como está
            pant, metodo = pantalla(n, perfil)
            filas.append({"modelo": n["modelo"], "perfil": perfil, "rend": rendimiento(n, req[perfil]),
                          "pant": pant, "metodo_pantalla": metodo})
    return filas


def cypher(filas: list[dict]) -> str:
    lineas = [f"  {{m:'{f['modelo']}', p:'{f['perfil']}', rend:{f['rend']:.2f}, pant:{f['pant']:.2f}, "
              f"op:'{f['metodo_pantalla']}'}}" for f in filas]
    return f"""// =====================================================================
// cypher/03_salida_pi2_provisional.cypher
// SALIDA_PI2 provisional de OFI, DEV, DIS, VID3D, GAM y DATOS (D-03, PG3-25).
// Generado por: python -m scripts.proponer_salida_pi2 (el metodo esta en ese script).
// Duenio de los datos: Miranda (rendimiento, SM2) y de Coninck (pantalla, SM3).
// Todos los valores son 'sin validar': se reemplazan cuando SM2 y SM3 carguen
// los de sus reglas de PI2. No toca los 9 pares de VIRT ni el supuesto K-OFI,
// asi que req_01 y req_03 no cambian.
// Va en un archivo aparte para que 01 a 40 sigan iguales al canonico de PG2.
// =====================================================================

UNWIND [
{(','+chr(10)).join(lineas)}
] AS x
MATCH (n:Notebook {{modelo:x.m}}), (p:Perfil {{codigo:x.p}})
MERGE (n)-[s:SALIDA_PI2]->(p)
SET s.adecuacion_rendimiento = x.rend, s.grado_pantalla = x.pant,
    s.origen = 'Propuesta provisional del grupo, sin validar por SM2 y SM3',
    s.origen_rendimiento = '{ORIGEN_REND}',
    s.origen_pantalla = CASE x.op
      WHEN 'srgb' THEN '{ORIGEN_PANT["srgb"]}'
      WHEN 'hz'   THEN '{ORIGEN_PANT["hz"]}'
      ELSE '{ORIGEN_PANT["igual"]}' END,
    s.validacion = 'sin validar';
"""


def actualizar_planilla(filas: list[dict]) -> None:
    with PLANILLA.open(encoding="utf-8", newline="") as fh:
        actuales = list(csv.DictReader(fh))
    nuevas = {(f["modelo"], f["perfil"]): f for f in filas}
    for a in actuales:
        f = nuevas.get((a["modelo"], a["perfil"]))
        if f and a["estado"] == "pendiente":
            a.update(adecuacion_rendimiento=f["rend"], grado_pantalla=f["pant"], origen_rendimiento=ORIGEN_REND,
                     origen_pantalla=ORIGEN_PANT[f["metodo_pantalla"]], estado="provisional")
    with PLANILLA.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(actuales[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(actuales)


def main() -> None:
    from asistente.grafo import Grafo
    g = Grafo()
    filas = proponer(g.leer(CATALOGO), requisitos(g.leer(REQUISITOS)))
    CYPHER.write_text(cypher(filas), encoding="utf-8")
    actualizar_planilla(filas)
    print(f"{len(filas)} pares escritos en {CYPHER.relative_to(RAIZ)} y {PLANILLA.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
