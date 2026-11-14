"""Router (PG3-06): prompt maestro -> plan JSON -> validación en Python.

El LLM solo propone el plan (intenciones del enum). Python lo valida antes de tocar
el grafo (A10: «desconfiar del cumplimiento del LLM»). Nunca se asume req_01.

Consultas libres (D-08, issue #21): si la consulta describe una necesidad (usos, presupuesto) y no hay
pedido escrito ni de sesión, el plan empieza con `SM1.registrar_pedido` y, si no pide otra cosa, sigue con
`SM4.recomendar` sobre el pedido nuevo. Así responde a cualquier persona, no solo a req_01..req_03.
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
            "pantalla", "ficha", "modelo", "presupuesto", "conviene", "descart", "indetermin", "movilidad",
            "computadora", "compu", "laptop", "portatil")
# Palabras que muestran que la consulta describe una necesidad: con ellas, sin pedido, se registra uno nuevo.
_NECESIDAD = ("programar", "programacion", "codigo", "docker", "maquina virtual", "maquinas virtuales", "virtualiz",
              "jugar", "juego", "gamer", "gaming", "office", "word", "excel", "navegar", "navegador", "facu",
              "estudiar", "universidad", "disen", "photoshop", "figma", "editar", "edicion", "video",
              "render", "3d", "blender", "datos", "machine learning", "trabajar", "trabajo", "usar", "uso",
              "dolares", "usd", "u$s", "pesos", "presupuesto", "tengo", "gastar", "necesito", "quiero", "busco")
_RE_MONTO = re.compile(r"\d+\s*(?:mil\s*)?(?:usd|u\$s|dolares|dolar|pesos|verdes|lucas)|\b(?:usd|u\$s)\s*\d", re.IGNORECASE)
ESCRITURA = ("SM1.registrar_pedido", "SM1.aclarar_pedido")
# Señales literales de una intención (PG3-00, corrida con Ollama real): con varias preguntas en una consulta,
# qwen2.5:3b suele planificar solo la primera. Si el texto pide algo con estas palabras y el plan no lo trae,
# Python lo agrega. Son frases inequívocas: el CSV del router controla que ninguna agregue lo que no se pidió.
_SENALES = (
    ("SM4.costo_beneficio", re.compile(r"costo[\s-]*beneficio|por su precio|rinde mas")),
    ("SM2.riesgo_ram", re.compile(r"\bde ram\b")),
    ("SM3.buscar", re.compile(r"\bmovilidad\b|\b(?:de|mejor) grafica\b")),
    ("GRUPO.traza_reglas", re.compile(r"\bque reglas\b|\breglas se activaron\b")),
)


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
    return any(p in t for p in _DOMINIO) or bool(_RE_PEDIDO.search(texto)) or parece_pedido(texto)


def parece_pedido(texto: str) -> bool:
    """La consulta describe una necesidad (un uso o un presupuesto), no una pregunta sobre un pedido cargado."""
    t = _sin_tildes(texto)
    if pedidos_en_texto(texto):
        return False
    return bool(_RE_MONTO.search(t)) or sum(p in t for p in _NECESIDAD) >= 2


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
    escritura: dict | None = None
    for c in plan.get("consultas") or []:
        if not isinstance(c, dict):
            continue
        intencion = c.get("intencion") or ""
        if c.get("sm") and "." not in intencion:
            intencion = f"{c['sm']}.{intencion}"
        if intencion not in INTENCIONES:
            obs.append(f"intención inválida descartada: {intencion!r}")
            continue
        if intencion in ESCRITURA:
            escritura = escritura or _validar_escritura(intencion, texto, escritos, sesion, obs)
            continue
        parametros = _validar_parametros(intencion, c.get("parametros") or {}, catalogo, modelos_texto, obs, texto)
        clave = (intencion, repr(sorted(parametros.items())))
        if clave in vistas:
            continue
        vistas.add(clave)
        consultas.append({"intencion": intencion, "parametros": parametros})

    _completar_por_senales(consultas, texto, modelos_texto, obs)
    if len(consultas) > MAX_CONSULTAS:
        obs.append(f"se recortó el plan a {MAX_CONSULTAS} consultas")
        consultas = consultas[:MAX_CONSULTAS]

    # 5. Pedido nuevo: sin pedido escrito ni de sesión, una consulta que describe una necesidad se registra
    necesita_pedido = not consultas or any("requerimiento_id" in INTENCIONES[c["intencion"]]["obligatorios"]
                                           for c in consultas)
    if escritura is None and requerimiento_id is None and necesita_pedido and parece_pedido(texto):
        escritura = {"intencion": "SM1.registrar_pedido", "parametros": {"texto": texto}}
        obs.append("la consulta describe una necesidad y no hay pedido: se registra uno nuevo (D-08)")
    if escritura is not None:
        if escritura["intencion"] == "SM1.aclarar_pedido":
            requerimiento_id = escritura["parametros"].pop("requerimiento_id")
        if not consultas:
            consultas = [{"intencion": "SM4.recomendar", "parametros": {}}]
        return {"requerimiento_id": requerimiento_id if escritura["intencion"] == "SM1.aclarar_pedido" else None,
                "consultas": [escritura] + consultas, "evidencia": evidencia, "observaciones": obs}

    if not consultas:
        if not es_del_dominio(texto):
            raise FueraDeAlcance()
        raise Aclaracion("No entendí qué querés consultar. " + EJEMPLO_REFORMULACION)

    # 6. Pedido obligatorio
    if requerimiento_id is None and any("requerimiento_id" in INTENCIONES[c["intencion"]]["obligatorios"]
                                        for c in consultas):
        raise Aclaracion("¿Sobre qué pedido? Indicá el requerimiento (por ejemplo req_01) o fijalo con "
                         f"/pedido. Pedidos cargados: {', '.join(pedidos)}.")

    return {"requerimiento_id": requerimiento_id, "consultas": consultas, "evidencia": evidencia,
            "observaciones": obs}


def senales(texto: str) -> list[str]:
    """Intenciones que el texto pide con una frase inequívoca (ver _SENALES)."""
    t = _sin_tildes(texto)
    return [i for i, patron in _SENALES if patron.search(t)]


def _completar_por_senales(consultas: list[dict], texto: str, modelos_texto: list[str], obs: list[str]) -> None:
    pedidas = {c["intencion"] for c in consultas}
    t = _sin_tildes(texto)
    for intencion in senales(texto):
        if intencion in pedidas or len(consultas) >= MAX_CONSULTAS:
            continue
        if intencion == "SM3.buscar":
            mov, graf = "movilidad" in t, "grafica" in t
            parametros = {"orden": "mixta" if mov and graf else "movilidad" if mov else "grafica"}
        elif intencion == "GRUPO.traza_reglas":
            if len(modelos_texto) != 1:
                continue
            parametros = {"modelo": modelos_texto[0]}
        elif intencion == "SM2.riesgo_ram" and modelos_texto:
            parametros = {"modelos": modelos_texto[:3]}
        else:
            parametros = {}
        consultas.append({"intencion": intencion, "parametros": parametros})
        obs.append(f"{intencion} agregada: el texto la pide y el plan del LLM no la traía")


def _validar_escritura(intencion: str, texto: str, escritos: list[str], sesion: dict, obs: list[str]) -> dict | None:
    """Las dos intenciones que escriben (D-08). Los parámetros los arma Python con el texto del usuario:
    el LLM no elige qué se guarda."""
    if intencion == "SM1.registrar_pedido":
        if escritos:
            obs.append(f"SM1.registrar_pedido descartado: el usuario nombró {escritos[0]}")
            return None
        if not parece_pedido(texto):
            obs.append("SM1.registrar_pedido descartado: la consulta no describe usos ni presupuesto")
            return None
        return {"intencion": intencion, "parametros": {"texto": texto}}
    req = escritos[0] if escritos else sesion.get("requerimiento_id")
    if not req:
        obs.append("SM1.aclarar_pedido descartado: no hay pedido que aclarar")
        return None
    return {"intencion": intencion, "parametros": {"requerimiento_id": req, "respuesta": texto}}


_PALABRAS_NUMERO = {n: w for n, w in enumerate(
    "cero uno dos tres cuatro cinco seis siete ocho nueve diez once doce trece catorce quince dieciseis "
    "diecisiete dieciocho diecinueve veinte".split())}


def _filtro_en_texto(valor, texto: str) -> bool:
    """Un filtro de SM3 vale solo si el usuario lo dijo: su número aparece en el texto (con punto o coma)
    o, si es un sí/no, la palabra «dedicada». Un modelo chico copia los filtros del ejemplo del prompt."""
    if isinstance(valor, bool):
        return "dedicad" in texto.lower()
    if not isinstance(valor, (int, float)):   # un valor que no es número no se puede respaldar
        return False
    escritos = {str(valor), f"{valor:g}"}
    if valor >= 1000 and float(valor).is_integer():
        escritos.add(f"{int(valor):,}".replace(",", "."))     # «2.500 gramos» para 2500
    escritos |= {e.replace(".", ",") for e in escritos}
    if any(re.search(r"(?<![\d.,])" + re.escape(e) + r"(?!\d)", texto) for e in escritos):
        return True
    return float(valor).is_integer() and _PALABRAS_NUMERO.get(int(valor)) in re.findall(r"[a-z]+", _sin_tildes(texto))


def _validar_parametros(intencion: str, crudos: dict, catalogo: list[str], modelos_texto: list[str],
                        obs: list[str], texto: str = "") -> dict:
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
            inventados = [k for k, v in p["filtros"].items() if not _filtro_en_texto(v, texto)]
            if inventados:
                obs.append(f"Se descartaron filtros que el texto no pide: {', '.join(inventados)}")
                p["filtros"] = {k: v for k, v in p["filtros"].items() if k not in inventados}
            if not p["filtros"]:
                p.pop("filtros")
    return p


def sm_de(consulta: dict) -> str:
    return submodulo_de(consulta["intencion"])
