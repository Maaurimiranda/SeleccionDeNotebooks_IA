"""Router (PG3-06): prompt maestro -> plan JSON -> validación en Python.

El LLM solo propone el plan (intenciones del enum). Python lo valida antes de tocar
el grafo (A10: «desconfiar del cumplimiento del LLM»). Nunca se asume req_01.
"""
import re
import unicodedata
from pathlib import Path

from asistente.contrato import (Aclaracion, EJEMPLO_REFORMULACION, ESQUEMA_PLAN, FILTROS_SM3, FueraDeAlcance,
                                INTENCIONES, submodulo_de)

RUTA_PROMPT = Path(__file__).resolve().parent.parent / "prompts" / "maestro.txt"
MAX_CONSULTAS = 3

_RE_PEDIDO = re.compile(r"\breq[\s_-]?0*(\d{1,3})\b", re.IGNORECASE)
_RE_MODELO_LARGO = re.compile(r"\bnotebook[\s_-]*([a-z])\b", re.IGNORECASE)
_RE_MODELO_CORTO = re.compile(r"\b(?:la|el|de la|y la|y)\s+([A-Z])\b")
# Palabras que muestran que la consulta es del dominio (guarda contra un fuera_de_alcance falso)
_DOMINIO = ("notebook", "req", "pedido", "ram", "gpu", "grafica", "bateria", "autonomia", "peso", "liviana",
            "recomend", "compar", "precio", "costo", "virtualiz", "regla", "parametro", "perfil", "comprador",
            "pantalla", "ficha", "modelo", "presupuesto", "conviene", "descart", "indetermin", "movilidad")


def _sin_tildes(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn").lower()


def planificar(texto: str, sesion: dict, llm, catalogo: list[str] | None = None,
               pedidos: list[str] | None = None) -> dict:
    """Pide el plan al LLM con el prompt maestro (salida estructurada contra ESQUEMA_PLAN)."""
    plantilla = RUTA_PROMPT.read_text(encoding="utf-8")
    variables = {
        "catalogo": ", ".join(catalogo or []) or "(no disponible)",
        "pedidos": ", ".join(pedidos or []) or "(no disponible)",
        "pedido_sesion": (sesion or {}).get("requerimiento_id") or "ninguno",
    }
    return llm.json(plantilla, f'Consulta: "{texto}"', ESQUEMA_PLAN, variables=variables)


# ---------------------------------------------------------------------------
# Normalizaciones
# ---------------------------------------------------------------------------
def normalizar_pedido(valor) -> str | None:
    if not valor:
        return None
    m = _RE_PEDIDO.search(str(valor))
    return f"req_{int(m.group(1)):02d}" if m else None


def normalizar_modelo(valor) -> str | None:
    if not valor:
        return None
    v = str(valor).strip()
    m = _RE_MODELO_LARGO.search(v)
    if m:
        return f"Notebook_{m.group(1).upper()}"
    if re.fullmatch(r"(?:la\s+|el\s+)?[A-Za-z]", v, re.IGNORECASE):
        return f"Notebook_{v[-1].upper()}"
    return v


def pedidos_en_texto(texto: str) -> list[str]:
    return list(dict.fromkeys(f"req_{int(m):02d}" for m in _RE_PEDIDO.findall(texto)))


def modelos_en_texto(texto: str) -> list[str]:
    largos = [f"Notebook_{m.upper()}" for m in _RE_MODELO_LARGO.findall(texto)]
    cortos = [f"Notebook_{m}" for m in _RE_MODELO_CORTO.findall(texto)]
    return list(dict.fromkeys(largos + cortos))


def es_del_dominio(texto: str) -> bool:
    t = _sin_tildes(texto)
    return any(p in t for p in _DOMINIO) or bool(_RE_PEDIDO.search(texto))


def _fragmento_literal(fragmento: str, texto: str) -> bool:
    return bool(fragmento) and _sin_tildes(fragmento).strip() in _sin_tildes(texto)


# ---------------------------------------------------------------------------
# Validación del plan
# ---------------------------------------------------------------------------
def validar(plan: dict, texto: str, sesion: dict, catalogo: list[str], pedidos: list[str]) -> dict:
    """Devuelve {"requerimiento_id", "consultas": [{"intencion","parametros"}], "evidencia", "observaciones"}.

    Lanza FueraDeAlcance o Aclaracion. Nunca deja pasar una intención o un modelo inventado.
    """
    plan = plan if isinstance(plan, dict) else {}
    sesion = sesion or {}
    obs: list[str] = []

    # 1. Fuera de alcance: se respeta, salvo que el texto sea claramente del dominio
    if plan.get("fuera_de_alcance") and not es_del_dominio(texto):
        raise FueraDeAlcance()
    if plan.get("fuera_de_alcance"):
        obs.append("el LLM marcó fuera_de_alcance, pero la consulta es del dominio: se ignora la marca")

    # 2. Evidencia: solo fragmentos literales
    evidencia = []
    for e in plan.get("evidencia") or []:
        if isinstance(e, dict) and _fragmento_literal(e.get("fragmento", ""), texto):
            evidencia.append({"dato": e.get("dato"), "fragmento": e.get("fragmento")})
        else:
            obs.append(f"fragmento descartado por no ser literal: {e!r}")

    # 3. Pedido: el que escribió el usuario, o el de la sesión. Nunca el que "completa" el LLM.
    escritos = pedidos_en_texto(texto)
    for r in escritos:
        if r not in pedidos:
            raise Aclaracion(f"No existe el pedido {r}. Los pedidos cargados son: {', '.join(pedidos)}.")
    del_plan = normalizar_pedido(plan.get("requerimiento_id"))
    if escritos:
        requerimiento_id = escritos[0]
        if del_plan and del_plan != requerimiento_id:
            obs.append(f"el LLM propuso {del_plan}, pero el usuario escribió {requerimiento_id}")
    elif sesion.get("requerimiento_id"):
        requerimiento_id = sesion["requerimiento_id"]
        if del_plan and del_plan != requerimiento_id:
            obs.append(f"el LLM propuso {del_plan}, que no está en el texto: se usa el de la sesión")
    else:
        requerimiento_id = None
        if del_plan:
            obs.append(f"el LLM propuso {del_plan}, que no está en el texto ni en la sesión: se descarta")

    # 4. Consultas
    inexistentes = [f"Notebook_{m.upper()}" for m in _RE_MODELO_LARGO.findall(texto)
                    if f"Notebook_{m.upper()}" not in catalogo]
    if inexistentes:
        raise Aclaracion(f"No encontré {', '.join(inexistentes)} en el catálogo. Modelos disponibles: "
                         f"{', '.join(catalogo)}.")
    modelos_texto = [m for m in modelos_en_texto(texto) if m in catalogo]
    consultas, vistas = [], set()
    pendientes_nivel_2 = False
    for c in plan.get("consultas") or []:
        if not isinstance(c, dict):
            continue
        intencion = c.get("intencion") or ""
        if c.get("sm") and "." not in intencion:
            intencion = f"{c['sm']}.{intencion}"
        if intencion not in INTENCIONES:
            obs.append(f"intención inválida descartada: {intencion!r}")
            continue
        if INTENCIONES[intencion]["nivel"] != 1:
            pendientes_nivel_2 = True
            obs.append(f"{intencion} es de nivel 2 y todavía no está disponible")
            continue
        parametros = _validar_parametros(intencion, c.get("parametros") or {}, catalogo, modelos_texto, obs)
        clave = (intencion, repr(sorted(parametros.items())))
        if clave in vistas:
            continue
        vistas.add(clave)
        consultas.append({"intencion": intencion, "parametros": parametros})

    if len(consultas) > MAX_CONSULTAS:
        obs.append(f"se recortó el plan a {MAX_CONSULTAS} consultas")
        consultas = consultas[:MAX_CONSULTAS]

    if not consultas:
        if pendientes_nivel_2:
            raise Aclaracion("Cargar o aclarar un pedido nuevo todavía no está disponible. Podés consultar los "
                             f"pedidos cargados ({', '.join(pedidos)}).")
        if not es_del_dominio(texto):
            raise FueraDeAlcance()
        raise Aclaracion("No entendí qué querés consultar. " + EJEMPLO_REFORMULACION)

    # 5. Pedido obligatorio
    if requerimiento_id is None and any("requerimiento_id" in INTENCIONES[c["intencion"]]["obligatorios"]
                                        for c in consultas):
        raise Aclaracion("¿Sobre qué pedido? Indicá el requerimiento (por ejemplo req_01) o fijalo con "
                         f"/pedido. Pedidos cargados: {', '.join(pedidos)}.")

    return {"requerimiento_id": requerimiento_id, "consultas": consultas, "evidencia": evidencia,
            "observaciones": obs}


def _validar_parametros(intencion: str, crudos: dict, catalogo: list[str], modelos_texto: list[str],
                        obs: list[str]) -> dict:
    permitidos = set(INTENCIONES[intencion]["obligatorios"]) | set(INTENCIONES[intencion]["opcionales"])
    p = {k: v for k, v in crudos.items() if k in permitidos and k != "requerimiento_id" and v not in (None, "", [])}
    descartados = set(crudos) - set(p) - {"requerimiento_id"}
    if descartados:
        obs.append(f"{intencion}: parámetros ignorados {sorted(descartados)}")

    def chequear(modelo: str) -> str:
        m = normalizar_modelo(modelo)
        if m not in catalogo:
            raise Aclaracion(f"No encontré el modelo {modelo!r} en el catálogo. Modelos disponibles: "
                             f"{', '.join(catalogo)}.")
        return m

    if "modelo" in permitidos:
        if p.get("modelo"):
            p["modelo"] = chequear(p["modelo"])
        elif len(modelos_texto) == 1:
            p["modelo"] = modelos_texto[0]
            obs.append(f"{intencion}: modelo tomado del texto ({modelos_texto[0]})")
        else:
            raise Aclaracion("¿De qué notebook? Indicá el modelo, por ejemplo Notebook_G.")
    if "modelos" in permitidos:
        lista = p.get("modelos") or []
        lista = [lista] if isinstance(lista, str) else lista
        lista = list(dict.fromkeys(chequear(m) for m in lista))
        if intencion == "SM4.comparar":
            if len(lista) < 2 and len(modelos_texto) >= 2:
                lista = modelos_texto[:3]
            if not 2 <= len(lista) <= 3:
                raise Aclaracion("Para comparar necesito 2 o 3 modelos, por ejemplo «compará la A y la H».")
        if lista:
            p["modelos"] = lista
        else:
            p.pop("modelos", None)
    if intencion == "SM3.buscar":
        p["orden"] = p.get("orden") or "mixta"
        if isinstance(p.get("filtros"), dict):
            p["filtros"] = {k: v for k, v in p["filtros"].items() if k in FILTROS_SM3 and v is not None}
            if not p["filtros"]:
                p.pop("filtros")
    return p


def sm_de(consulta: dict) -> str:
    return submodulo_de(consulta["intencion"])
