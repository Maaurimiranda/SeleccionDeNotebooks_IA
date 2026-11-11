"""PG3-11: corre los E2E con el orquestador real (Neo4j y Ollama) y documenta esperado contra obtenido.

    python -m scripts.correr_e2e                 # todos
    python -m scripts.correr_e2e E2E-1 E2E-9     # algunos

Escribe docs/pruebas/E2E-n.md, docs/pruebas/resultados_e2e.md, docs/pruebas/casos_de_uso.md y la traza JSONL en
docs/pruebas/trazas/. El aprobado de cada E2E lo decide lo que dice el grafo (la evidencia), no el texto del LLM.
"""
import json
import shutil
import sys
from datetime import date
from pathlib import Path

from asistente import explicador
from asistente.contrato import submodulo_de
from asistente.orquestador import INTENCION_PEDIDO, Orquestador

RAIZ = Path(__file__).resolve().parent.parent
DIR = RAIZ / "docs" / "pruebas"
DIR_TRAZAS = DIR / "trazas"


# ---------------------------------------------------------------- lectura de la evidencia
def _ev(t: dict) -> dict:
    return t.get("evidencia") or {}


def _filas_sm4(t: dict) -> dict[str, dict]:
    """notebook -> sus datos de SM4 (de cualquier intención: recomendar, explicar o comparar)."""
    filas: dict[str, dict] = {}
    for intencion, e in (_ev(t).get("SM4") or {}).items():
        lista = list(e.get("ranking") or []) + list(e.get("no_propuestas") or []) + list(e.get("notebooks") or [])
        if e.get("fuera_de_presupuesto"):
            lista.append(e["fuera_de_presupuesto"])
        for n in lista:
            filas.setdefault(n["notebook"], {}).update({k: v for k, v in n.items() if v is not None})
    return filas


def _estado(t, m):
    return _filas_sm4(t).get(m, {}).get("estado")


def _alertas(t, m) -> set:
    return {a["codigo"] for a in _filas_sm4(t).get(m, {}).get("alertas", [])}


def _riesgo_sm2(t, m):
    for n in ((_ev(t).get("SM2") or {}).get("riesgo_ram") or {}).get("notebooks", []):
        if n["notebook"] == m:
            return n["riesgo"], n["etiqueta"]
    return None, None


def _submodulos_pedidos(t) -> list[str]:
    """Submódulos distintos que pidió el plan, sin contar L1 (que el orquestador agrega siempre)."""
    return sorted({submodulo_de(c["intencion"]) for c in (t.get("plan") or {}).get("consultas", [])
                   if c["intencion"] != INTENCION_PEDIDO})


# ---------------------------------------------------------------- esperados: (descripción, función(traza) -> (ok, obtenido))
def _chk(descripcion, f):
    return descripcion, f


def _igual(valor, esperado, tol=0.0005):
    return abs(valor - esperado) <= tol if isinstance(valor, (int, float)) else False


def _e1():
    def ranking(t):
        r = ((_ev(t).get("SM4") or {}).get("recomendar") or {}).get("ranking", [])
        obt = [(x["puesto"], x["notebook"]) for x in r]
        return obt[:3] == [(1, "Notebook_A"), (2, "Notebook_H"), (3, "Notebook_B")], obt

    def grado_a(t):
        g = _filas_sm4(t).get("Notebook_A", {}).get("grado")
        return _igual(g, 0.785), g

    def fuera(t):
        f = ((_ev(t).get("SM4") or {}).get("recomendar") or {}).get("fuera_de_presupuesto") or {}
        return f.get("notebook") == "Notebook_X", f.get("notebook")

    def estados(t):
        obt = {m: _estado(t, m) for m in ("Notebook_M", "Notebook_E", "Notebook_G", "Notebook_C")}
        ok = (obt["Notebook_M"] == "Recomendada condicionada por falta de informacion"
              and obt["Notebook_E"] == "Descartada (excluyente incumplido)"
              and (obt["Notebook_C"] or "").startswith("Descartada")
              and obt["Notebook_G"] == "Indeterminada: completar informacion")
        return ok, obt

    return [_chk("Al menos dos submódulos distintos pedidos en el plan (sin L1)", lambda t: (len(_submodulos_pedidos(t)) >= 2, _submodulos_pedidos(t))),
            _chk("Ranking: A puesto 1, H puesto 2, B puesto 3", ranking),
            _chk("Grado de A = 0,785", grado_a),
            _chk("X queda fuera de presupuesto", fuera),
            _chk("M condicionada, E y C descartadas, G indeterminada", estados)]


def _e2():
    def m(t):
        f = _filas_sm4(t).get("Notebook_M", {})
        g = f.get("grado") or {}
        ok = (f.get("estado") == "Recomendada condicionada por falta de informacion"
              and _igual(g.get("min"), 0.504) and _igual(g.get("max"), 0.826)
              and "autonomia" in (f.get("dato_faltante") or "").lower())
        return ok, {"estado": f.get("estado"), "grado": f.get("grado"), "dato_faltante": f.get("dato_faltante")}

    def g(t):
        f = _filas_sm4(t).get("Notebook_G", {})
        return (f.get("estado") == "Indeterminada: completar informacion" and {"REN-R10", "FZ-R7"} <= _alertas(t, "Notebook_G"),
                {"estado": f.get("estado"), "alertas": sorted(_alertas(t, "Notebook_G"))})

    def riesgo(t):
        r, etiqueta = _riesgo_sm2(t, "Notebook_G")
        ok = isinstance(r, dict) and _igual(r.get("min"), 49.58, 0.005) and _igual(r.get("max"), 81.46, 0.005)
        return ok, {"riesgo": r, "etiqueta": etiqueta}

    return [_chk("Al menos dos submódulos distintos pedidos en el plan (sin L1)", lambda t: (len(_submodulos_pedidos(t)) >= 2, _submodulos_pedidos(t))),
            _chk("M condicionada, grado [0,504 ; 0,826], falta la autonomía", m),
            _chk("G indeterminada con las alertas REN-R10 y FZ-R7", g),
            _chk("Riesgo de RAM de G como rango [49,58 ; 81,46] (SM2)", riesgo)]


def _e3():
    def indeterminado(t):
        l1 = [c for c in t["consultas"] if c.get("intencion") == INTENCION_PEDIDO]
        return bool(l1), [c.get("nombre") for c in l1]

    def sin_evaluaciones(t):
        sm4 = [c for c in t["consultas"] if c.get("sm") == "SM4" and c.get("filas")]
        return not sm4, f"{len(sm4)} consultas de SM4 con filas"

    return [_chk("Se consultó el pedido (L1) y el origen es una validación, no una recomendación",
                 lambda t: (t["origen_respuesta"] == "validacion" and indeterminado(t)[0], t["origen_respuesta"])),
            _chk("0 evaluaciones: ninguna consulta de SM4 devolvió filas", sin_evaluaciones),
            _chk("Pide responder la pregunta pendiente", lambda t: ("pregunta pendiente" in (t["respuesta"] or ""), (t["respuesta"] or "")[:100])),
            _chk("No asume un perfil (no aparece OFI)", lambda t: ("OFI" not in (t["respuesta"] or ""), "OFI" in (t["respuesta"] or "")))]


def _e5():
    def puntajes(t):
        f = _filas_sm4(t)
        obt = {m: f.get(m, {}).get("adecuacion_global") for m in ("Notebook_E", "Notebook_B", "Notebook_H")}
        ok = _igual(obt["Notebook_E"], 0.81) and _igual(obt["Notebook_B"], 0.813) and _igual(obt["Notebook_H"], 0.811)
        return ok, obt

    def descarte(t):
        e = _filas_sm4(t).get("Notebook_E", {})
        return (e.get("estado") == "Descartada (excluyente incumplido)" and e.get("regla") == "REC-R3",
                {"estado": e.get("estado"), "regla": e.get("regla"), "motivo": e.get("motivo")})

    return [_chk("Al menos dos submódulos distintos pedidos en el plan (sin L1)", lambda t: (len(_submodulos_pedidos(t)) >= 2, _submodulos_pedidos(t))),
            _chk("E ≈ 0,81, B = 0,813 y H = 0,811", puntajes),
            _chk("E Descartada (excluyente incumplido) por REC-R3", descarte),
            _chk("B y H siguen recomendadas", lambda t: (all((_estado(t, m) or "").startswith("Recomendada") for m in ("Notebook_B", "Notebook_H")),
                                                         {m: _estado(t, m) for m in ("Notebook_B", "Notebook_H")}))]


def _e8():
    return [_chk("Origen fuera_de_alcance", lambda t: (t["origen_respuesta"] == "fuera_de_alcance", t["origen_respuesta"])),
            _chk("Ninguna consulta al grafo (consultas = [])", lambda t: (t["consultas"] == [], len(t["consultas"])))]


def _e9():
    def traza_a(t):
        g = ((_ev(t).get("GRUPO") or {}).get("traza_reglas")) or {}
        ids = {r["id"] for r in g.get("reglas", [])}
        o = g.get("origen") or {}
        ok = (g.get("submodulos") == ["SM1", "SM2", "SM3", "SM4"] and len(ids) == 18 and len(o.get("reglas", {})) == 14
              and set(o.get("reglas_sin_origen", [])) == {"GM-R3", "INT-R11", "REC-R4", "REC-R9"})
        return ok, {"submodulos": g.get("submodulos"), "reglas": len(ids), "con_origen": len(o.get("reglas", {})),
                    "sin_origen": o.get("reglas_sin_origen")}

    def fuentes(t):
        n = (((_ev(t).get("GRUPO") or {}).get("traza_reglas") or {}).get("origen") or {}).get("notebook") or {}
        ok = bool(n.get("fuente_precio")) and n.get("fuente_precio") != "no registrada" and bool(n.get("fuente_autonomia"))
        return ok, n

    def riesgo(t):
        r, etiqueta = _riesgo_sm2(t, "Notebook_A")
        return r is not None, {"riesgo": r, "etiqueta": etiqueta}

    return [_chk("Al menos dos submódulos distintos pedidos en el plan (sin L1)", lambda t: (len(_submodulos_pedidos(t)) >= 2, _submodulos_pedidos(t))),
            _chk("Traza de A: reglas de los 4 submódulos, 18 reglas, 14 con origen y 4 «no registrada»", traza_a),
            _chk("La notebook trae la fuente del precio y de la autonomía", fuentes),
            _chk("Riesgo de RAM de A, tal cual lo da el grafo (SM2)", riesgo)]


def _e10():
    def movilidad(t):
        b = ((_ev(t).get("SM3") or {}).get("buscar")) or {}
        valores = [n.get("adecuacion_movilidad") for n in b.get("notebooks", [])]
        con = [v for v in valores if v is not None]
        ok = b.get("orden") == "movilidad" and con == sorted(con, reverse=True) and valores[:len(con)] == con
        return ok, {"orden": b.get("orden"), "filtros": b.get("filtros"), "adecuacion_movilidad": valores}

    def cb(t):
        n = ((_ev(t).get("SM4") or {}).get("costo_beneficio") or {}).get("notebooks", [])
        obt = [(x["notebook"], x["indice_costo_beneficio"]) for x in n[:2]]
        return obt == [("Notebook_B", 1.161), ("Notebook_A", 0.907)], obt

    return [_chk("Al menos dos submódulos distintos pedidos en el plan (sin L1)", lambda t: (len(_submodulos_pedidos(t)) >= 2, _submodulos_pedidos(t))),
            _chk("SM3: orden por movilidad descendente, con los datos faltantes al final y sin números inventados", movilidad),
            _chk("SM4: costo-beneficio de Q7 (B 1,161; A 0,907)", cb)]


CASOS = [
    {"id": "E2E-1", "tipo": "integral", "texto": "Para req_01, ¿qué notebook me recomendás? ¿Cómo andan de RAM y de gráfica?",
     "esperado": _e1,
     "situacion": "Un asesor atiende el pedido req_01 (presupuesto 1000 USD, perfil de virtualización) y quiere una recomendación, con el riesgo de RAM y la gráfica de las candidatas.",
     "razonamiento": "SM4 ordena con REC-R8 (grado de recomendación y desempate por ampliabilidad de la RAM); SM2 calcula el riesgo de RAM con sus reglas difusas; SM3 aporta la gráfica y la movilidad. Las excluyentes (REC-R3) descartan a E y a C, y el dato faltante (REC-R15) deja a M condicionada."},
    {"id": "E2E-2", "tipo": "integral", "texto": "En req_01, ¿por qué la M quedó condicionada y la G indeterminada? ¿Qué riesgo de RAM tiene la G?",
     "esperado": _e2,
     "situacion": "El asesor ve en la lista a la M «condicionada» y a la G «indeterminada» y no entiende por qué.",
     "razonamiento": "M no informa la autonomía: REC-R15 deja su grado como rango en vez de inventar un valor. G no informa si la CPU soporta virtualización ni si la RAM es ampliable: el grafo no puede decidir y el estado es indeterminado. SM2 informa el riesgo de RAM de G como rango, por la misma falta de dato."},
    {"id": "E2E-3", "tipo": "control", "texto": "Para req_02, ¿qué notebook me conviene?",
     "esperado": _e3,
     "situacion": "El asesor pregunta por req_02, un pedido al que todavía le falta una respuesta del comprador.",
     "razonamiento": "El perfil de req_02 es indeterminado y no tiene evaluaciones: el sistema no completa un perfil (no asume oficina), pide responder la pregunta pendiente y no recomienda."},
    {"id": "E2E-5", "tipo": "integral", "texto": "En req_01, la E tiene casi el mismo puntaje que la B y la H, ¿por qué no la recomiendan? ¿Qué pasa con la virtualización?",
     "esperado": _e5,
     "situacion": "El asesor ve que la E puntúa igual que la B y la H y se pregunta por qué no entra en la recomendación.",
     "razonamiento": "El puntaje no alcanza: la virtualización es un requisito excluyente del perfil (REC-R3) y la CPU de la E no la soporta, así que queda descartada aunque su adecuación global sea ≈ 0,81. SM2 confirma la virtualización por hardware."},
    {"id": "E2E-8", "tipo": "control", "texto": "¿Cuál es la capital de Francia?",
     "esperado": _e8,
     "situacion": "Una pregunta que no tiene que ver con notebooks.",
     "razonamiento": "El router la marca fuera de alcance y el sistema responde con un mensaje fijo, sin consultar el grafo ni el explicador."},
    {"id": "E2E-9", "tipo": "integral", "texto": "En req_01, ¿qué reglas se activaron para la A, de dónde sale cada dato y qué riesgo de RAM tiene?",
     "esperado": _e9,
     "situacion": "Un auditor pide reconstruir cómo llegó el sistema al resultado de la A: reglas, fuente de los datos y riesgo de RAM (consigna §3.7).",
     "razonamiento": "GRUPO.traza_reglas devuelve las 18 reglas activadas de los cuatro submódulos con su fuerza y, para 14 de ellas, los parámetros que las respaldan. Las 4 restantes salen «no registrada»: el grafo no guarda su fuente. SM2 informa el riesgo de RAM de la A."},
    {"id": "E2E-10", "tipo": "integral", "texto": "Para req_01, ¿cuáles son las mejores en movilidad y cómo queda el costo-beneficio?",
     "esperado": _e10,
     "situacion": "El asesor quiere las más portables del pedido y cuál rinde más por su precio.",
     "razonamiento": "SM3 ordena por la adecuación de movilidad (peso y autonomía) y deja los datos faltantes al final; SM4 ordena por el índice costo-beneficio de REC-R9 (adecuación global sobre precio)."},
]


# ---------------------------------------------------------------- corrida y documentos
def _json(x, n=None):
    s = json.dumps(x, ensure_ascii=False, indent=1, default=str)
    return s if n is None or len(s) <= n else s[:n] + "\n... (recortado)"


def _correr(caso: dict, orq: Orquestador) -> dict:
    r = orq.consultar(caso["texto"])
    t = r["traza"]
    resultados = []
    for descripcion, f in caso["esperado"]():
        try:
            ok, obtenido = f(t)
        except Exception as e:  # un esperado que no se puede evaluar es un fallo, no un cuelgue
            ok, obtenido = False, f"{type(e).__name__}: {e}"
        resultados.append({"esperado": descripcion, "ok": bool(ok), "obtenido": obtenido})
    return {"caso": caso, "respuesta": r, "traza": t, "resultados": resultados, "ok": all(x["ok"] for x in resultados)}


def _md_e2e(c: dict) -> str:
    caso, t, r = c["caso"], c["traza"], c["respuesta"]
    L = [f"# {caso['id']} · {caso['tipo']}", "", f"**Fecha:** {t['fecha']} · **Veredicto:** {'APRUEBA' if c['ok'] else 'FALLA'} · "
         f"**Tiempo de punta a punta:** {t['segundos']} s (plan {t['duracion_ms'].get('plan', 0)} ms, consultas "
         f"{t['duracion_ms'].get('consultas', 0)} ms, explicación {t['duracion_ms'].get('explicacion', 0)} ms)", "",
         "## 1. Entrada", "", f"> {caso['texto']}", "", "## 2. Plan del router (JSON extraído)", "", "```json", _json(t["plan"]), "```", ""]
    if t["validacion"]["observaciones"]:
        L += ["Observaciones de la validación: " + "; ".join(t["validacion"]["observaciones"]), ""]
    L += [f"Submódulos consultados: {', '.join(r['submodulos_consultados']) or 'ninguno'} (SM1 lo agrega el orquestador siempre que hay pedido)", "",
          "## 3. Consultas Cypher (plantillas fijas) y sus valores", ""]
    if not t["consultas"]:
        L += ["Ninguna: el sistema no consultó el grafo.", ""]
    for q in t["consultas"]:
        L += [f"### {q.get('nombre') or q.get('intencion')} · parámetros `{json.dumps(q.get('parametros'), ensure_ascii=False)}` · "
              f"{len(q.get('filas') or [])} filas" + (f" · {q['ms']} ms" if q.get("ms") is not None else ""), "",
              "<details><summary>Cypher y primeras filas</summary>", "", "```cypher", (q.get("cypher") or "").strip(), "```", "",
              "```json", _json((q.get("filas") or [])[:3], 2500), "```", "", "</details>", ""]
    if t["evidencia"]:
        vista = json.dumps(explicador._compactar(t["evidencia"]), ensure_ascii=False, separators=(",", ":"))
        L += ["## 4. Datos enviados al LLM (evidencia común compactada)", "", f"{len(vista)} caracteres.", "",
              "<details><summary>Ver evidencia</summary>", "", "```json", vista[:6000] + (" ... (recortado)" if len(vista) > 6000 else ""), "```", "", "</details>", ""]
    L += ["## 5. Intentos del verificador", ""]
    if t["intentos"]:
        for i, it in enumerate(t["intentos"], 1):
            L.append(f"- Intento {i}: {'pasa' if not it['problemas'] else 'rechazado: ' + '; '.join(it['problemas'])}")
    else:
        L.append("- No hubo explicación con el LLM.")
    L += ["", f"**Origen de la respuesta:** `{r['origen_respuesta']}`", "", "## 6. Respuesta final", ""]
    L += ["> " + linea for linea in (r["respuesta"] or "").splitlines()] + ["", "## 7. Esperado contra obtenido (lo decide el grafo)", "",
          "| Esperado | Obtenido | OK |", "| --- | --- | --- |"]
    for x in c["resultados"]:
        obtenido = json.dumps(x["obtenido"], ensure_ascii=False, default=str).replace("|", "\\|")
        L.append(f"| {x['esperado']} | `{obtenido[:220]}` | {'sí' if x['ok'] else '**NO**'} |")
    L += ["", f"**Veredicto: {'APRUEBA' if c['ok'] else 'FALLA'}.** La explicación en lenguaje natural la genera el LLM y no decide el veredicto."]
    return "\n".join(L) + "\n"


def _md_casos(corridas: list[dict]) -> str:
    L = ["# Casos de uso integrados (consigna §3.4)", "",
         "Cada caso involucra **al menos dos submódulos distintos** además de SM1, que el orquestador agrega siempre que hay un pedido. "
         "Los datos salen de las corridas reales de `scripts/correr_e2e.py`; el detalle de cada una está en `E2E-n.md`.", ""]
    por_id = {c["caso"]["id"]: c for c in corridas}
    for i, caso in enumerate([k for k in CASOS if k["tipo"] == "integral"], 1):
        c = por_id.get(caso["id"])
        if not c:
            continue
        t = c["traza"]
        L += [f"## Caso {i} · {caso['id']}", "", f"**Consulta:** «{caso['texto']}»", "", f"**Situación.** {caso['situacion']}", "",
              f"**Información usada.** Submódulos del plan: {', '.join(_submodulos_pedidos(t)) or 'ninguno'} (más SM1 para el pedido). Intenciones: "
              + ", ".join(f"`{q['intencion']}`" for q in (t['plan'] or {}).get("consultas", [])) + ". "
              f"Consultas Cypher ejecutadas: {len(t['consultas'])}.", "", f"**Razonamiento.** {caso['razonamiento']}", "",
              "**Resultado.** " + ("; ".join(f"{x['esperado']} → {'sí' if x['ok'] else 'NO'}" for x in c["resultados"])) + ".", "",
              "**Explicación generada.**", ""]
        L += ["> " + linea for linea in (c["respuesta"]["respuesta"] or "").splitlines()]
        L += ["", f"_Origen: {c['respuesta']['origen_respuesta']} · {t['segundos']} s · [detalle]({caso['id']}.md)_", ""]
    L += ["## Controles", "", "No cuentan como casos integrales: no cruzan información entre submódulos.", ""]
    for caso in [k for k in CASOS if k["tipo"] == "control"]:
        c = por_id.get(caso["id"])
        if c:
            L += [f"- **{caso['id']}** · «{caso['texto']}» → {'APRUEBA' if c['ok'] else 'FALLA'}. {caso['situacion']} {caso['razonamiento']} ([detalle]({caso['id']}.md))"]
    return "\n".join(L) + "\n"


def _md_resultados(corridas: list[dict]) -> str:
    L = ["# Resultados de los E2E", "", f"Corrida del {date.today().isoformat()} con el orquestador real (Neo4j y `qwen2.5:3b`). "
         "Tiempos medidos en **una** máquina: falta repetirlos en otra (PG3-11, punto 3).", "",
         "| E2E | Tipo | Submódulos del plan | Origen | Intentos | Tiempo (s) | Esperados | Veredicto |", "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for c in corridas:
        t = c["traza"]
        L.append(f"| [{c['caso']['id']}]({c['caso']['id']}.md) | {c['caso']['tipo']} | {', '.join(_submodulos_pedidos(t)) or '—'} | "
                 f"{c['respuesta']['origen_respuesta']} | {len(t['intentos'])} | {t['segundos']} | "
                 f"{sum(x['ok'] for x in c['resultados'])}/{len(c['resultados'])} | {'APRUEBA' if c['ok'] else '**FALLA**'} |")
    llm = [c for c in corridas if c["respuesta"]["origen_respuesta"] in ("llm", "plantilla_fija")]
    if llm:
        n_llm = sum(c["respuesta"]["origen_respuesta"] == "llm" for c in llm)
        L += ["", f"**Tasa de plantilla fija:** {len(llm) - n_llm} de {len(llm)} respuestas con explicación salieron de la plantilla "
              f"({(len(llm) - n_llm) / len(llm):.0%}); el resto las redactó el LLM y las aprobó el verificador."]
    return "\n".join(L) + "\n"


def main(ids: list[str]) -> int:
    from asistente.config import DIR_TRAZAS as _  # noqa: F401  (falla temprano si falta la configuración)
    DIR.mkdir(parents=True, exist_ok=True)
    shutil.rmtree(DIR_TRAZAS, ignore_errors=True)
    orq = Orquestador(dir_trazas=str(DIR_TRAZAS))
    salud = orq.salud()
    if not salud["ok"]:
        print("Neo4j u Ollama no están disponibles:", json.dumps(salud, ensure_ascii=False, default=str))
        return 2
    corridas = []
    for caso in CASOS:
        if ids and caso["id"] not in ids:
            continue
        c = _correr(caso, orq)
        corridas.append(c)
        (DIR / f"{caso['id']}.md").write_text(_md_e2e(c), encoding="utf-8")
        print(f"{caso['id']}: {'APRUEBA' if c['ok'] else 'FALLA'} · {c['traza']['segundos']} s · {c['respuesta']['origen_respuesta']}")
        for x in c["resultados"]:
            if not x["ok"]:
                print(f"   NO: {x['esperado']} -> {x['obtenido']}")
    if not ids:
        (DIR / "resultados_e2e.md").write_text(_md_resultados(corridas), encoding="utf-8")
        (DIR / "casos_de_uso.md").write_text(_md_casos(corridas), encoding="utf-8")
    return 0 if all(c["ok"] for c in corridas) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
