"""SM1 · Servicio: interpretación del pedido (L1) y alta o aclaración de un pedido nuevo (nivel 2, D-08).

L1 (interpretacion_pedido):
- Perfil indeterminado: estado_pedido = indeterminado, sin perfil asumido (CP10, E2E-3).
- Perfil con rango (D-09): se informa {"min","max"}; si es el dominante, queda provisional.

Pedido nuevo (registrar_pedido y aclarar_pedido, issues #12 a #14 y #20). Patrón sándwich de la PI4 de SM1:
el LLM ya extrajo el JSON (asistente/extractor.py, lo llama el orquestador); acá Python lo valida antes de
escribir nada:
- INT-R7: cada actividad y el presupuesto necesitan su cita literal en el texto; si no, se descartan.
- INT-R1: sin presupuesto, o fuera de (0 ; 20.000] USD, se repregunta y no se escribe.
- INT-R10: un presupuesto en pesos se convierte con COTIZACION_ARS_USD; si no está, se pide en USD.
- INT-R11: el perfil de cada actividad sale de su tipo (programar → VIRT si también virtualiza, si no DEV).
- Horas: cantidad × período en Python; si no, la expresión del léxico del grafo. El LLM no convierte.
Lo imprescindible que falta (uso, presupuesto, frecuencia) es una repregunta; lo deseable queda como
Pregunta pendiente en el grafo y no frena la respuesta.
"""
import re
import unicodedata

from asistente import config
from asistente.contrato import Aclaracion
from asistente.submodulos.comun import rango, redondear
from asistente.submodulos.sm1 import repositorio
from asistente.submodulos.sm1.esquemas import EvidenciaPedido, EvidenciaRegistro, PedidoValidado

PRESUPUESTO_MAXIMO_USD = 20000.0   # INT-R1 (PI4 de SM1)
PRIORIDADES = ["rendimiento", "grafica", "portabilidad", "autonomia", "precio"]

# INT-R11: perfil por el tipo de actividad (contexto de SM1, P7). 'estudiar' y 'otra' no definen perfil.
PERFIL_POR_TIPO = {"virtualizar": "VIRT", "jugar": "GAM", "disenar": "DIS", "editar_video": "VID3D",
                   "modelar_3d": "VID3D", "analizar_datos": "DATOS", "ofimatica": "OFI"}

# Una prioridad declarada necesita alguna de estas palabras en el texto (INT-R7 aplicado a la prioridad).
_PALABRAS_PRIORIDAD = {
    "rendimiento": ("rendimiento", "potente", "potencia", "rapida", "rapido", "veloz", "que rinda"),
    "grafica": ("grafica", "placa de video", "gpu", "graficos"),
    "portabilidad": ("liviana", "liviano", "portable", "portabilidad", "llevar", "la llevo", "transportar", "peso"),
    "autonomia": ("bateria", "autonomia", "que dure", "sin cargador", "enchufe"),
    "precio": ("barata", "barato", "economica", "economico", "precio", "ahorrar", "lo mas barato"),
}

_PROPOSITO = {"para", "quiero", "necesito", "busco", "uso"}
_STOP = {"la", "el", "los", "las", "a", "de", "en", "lo", "por", "para", "al"}
_RE_MONTO = re.compile(
    r"(?:(usd|u\$s|us\$)\s*(\d{1,3}(?:[.,]\d{3})+|\d+(?:[.,]\d+)?)\s*(mil|k)?)"
    r"|(?:(\d{1,3}(?:[.,]\d{3})+|\d+(?:[.,]\d+)?)\s*(mil|k)?\s*(?:de\s+)?"
    r"(usd|u\$s|us\$|dolares|dolar|verdes|pesos|ars|lucas))\b", re.IGNORECASE)
_RE_HORAS = re.compile(r"(\d+(?:[.,]\d+)?)\s*(?:h|hs|horas?)\b\s*(?:por|al|a la|cada|x)?\s*(dia|semana|mes)",
                       re.IGNORECASE)
_RE_HORAS_ADJ = re.compile(r"(\d+(?:[.,]\d+)?)\s*(?:h|hs|horas?)\s*(diarias|semanales|mensuales)", re.IGNORECASE)
_RE_MODELO = re.compile(r"\bnotebook[\s_-]*([a-z])\b", re.IGNORECASE)


# ---------------------------------------------------------------------------
# L1
# ---------------------------------------------------------------------------
def interpretacion_pedido(grafo, p: dict) -> tuple[list, EvidenciaPedido]:
    c = repositorio.interpretacion(grafo, p["requerimiento_id"])
    if not c["filas"]:
        raise Aclaracion(f"No existe el pedido {p['requerimiento_id']}. Los pedidos cargados se ven con "
                         "«¿qué pedidos hay?» o en el manual.")
    f = c["filas"][0]
    perfiles = sorted((
        {"perfil": x["perfil"], "grado": rango(x["grado"], x.get("grado_min"), x.get("grado_max")),
         "impone_requisitos": x["impone_requisitos"], "en_frontera": x["en_frontera"]}
        for x in f["perfiles"]), key=lambda x: -(x["grado"] if isinstance(x["grado"], (int, float))
                                                 else (x["grado"] or {}).get("max") or 0))
    dominante = f["perfil_dominante"] or "indeterminado"
    indeterminado = dominante == "indeterminado"
    grado_dom = next((x["grado"] for x in perfiles if x["perfil"] == dominante), None)
    evidencia: EvidenciaPedido = {
        "requerimiento": f["requerimiento"],
        "presupuesto": redondear(f["presupuesto"]),
        "prioridad": f["prioridad"],
        "perfiles": perfiles,
        "perfil_dominante": dominante,
        "perfil_dominante_provisional": isinstance(grado_dom, dict),
        "intensidad": f["intensidad"],
        "intensidad_valor": redondear(f["intensidad_valor"]),
        "preguntas_pendientes": [q for q in f["preguntas_pendientes"] if q],
        "estado_pedido": "indeterminado" if indeterminado else "interpretado",
    }
    return [c], evidencia


# ---------------------------------------------------------------------------
# Utilidades de validación (puras: se prueban sin grafo ni LLM)
# ---------------------------------------------------------------------------
def sin_tildes(x: str) -> str:
    x = unicodedata.normalize("NFD", (x or "").lower())
    return "".join(c for c in x if unicodedata.category(c) != "Mn")


def limpio(x: str) -> str:
    x = unicodedata.normalize("NFD", (x or "").lower())
    x = "".join(c for c in x if unicodedata.category(c) != "Mn")
    return " ".join(re.sub(r"[^a-z0-9$ ]+", " ", x).split())


def contiene(texto: str, fragmento: str) -> bool:
    """INT-R7: la cita tiene que estar en el texto (sin distinguir mayúsculas, tildes ni signos)."""
    return bool(fragmento and limpio(fragmento)) and limpio(fragmento) in limpio(texto)


def contiene_expresion(texto: str, expresion: str) -> bool:
    """La expresión del léxico vale si sus palabras de contenido están en el texto
    («la necesito para» ↔ «Necesito una notebook para»; «a veces» ↔ «a veces»)."""
    palabras = set(limpio(texto).split())
    clave = [w for w in limpio(expresion).split() if w not in _STOP] or limpio(expresion).split()
    return bool(clave) and all(w in palabras for w in clave)


def horas_por_semana(cantidad, periodo) -> float | None:
    """Conversión aritmética en Python (no la hace el LLM)."""
    try:
        c = float(cantidad)
    except (TypeError, ValueError):
        return None
    factor = {"dia": 7.0, "semana": 1.0, "mes": 1 / 4.33}.get(periodo)
    if factor is None or c <= 0 or c > 168:
        return None
    return round(min(c * factor, 168.0), 2)


def _numero(s: str) -> float:
    if re.fullmatch(r"\d{1,3}(?:[.,]\d{3})+", s):
        return float(re.sub(r"[.,]", "", s))
    return float(s.replace(",", "."))


def _numero_en_texto(valor, texto: str) -> bool:
    if not isinstance(valor, (int, float)) or isinstance(valor, bool):
        return False
    t = limpio(texto).replace(" ", "")
    escritos = {f"{valor:g}", str(valor)}
    if float(valor).is_integer():
        v = int(valor)
        escritos |= {str(v), f"{v:,}".replace(",", "."), f"{v:,}"}
        if v % 1000 == 0:
            escritos |= {f"{v // 1000}mil", f"{v // 1000}k"}
    return any(limpio(e).replace(" ", "") in t for e in escritos)


def presupuesto_en_texto(texto: str) -> tuple[float, str, str] | None:
    """(monto, moneda, cita) del primer monto con moneda escrito en el texto, o None."""
    m = _RE_MONTO.search(sin_tildes(texto))
    if not m:
        return None
    if m.group(1):
        cifra, mil, moneda = m.group(2), m.group(3), m.group(1)
    else:
        cifra, mil, moneda = m.group(4), m.group(5), m.group(6)
    monto = _numero(cifra) * (1000 if mil else 1)
    moneda = "ARS" if moneda in ("pesos", "ars", "lucas") else "USD"
    if m.group(6) == "lucas":
        monto *= 1000
    return monto, moneda, m.group(0)


def horas_en_texto(texto: str) -> float | None:
    """Horas por semana si el texto dice una cantidad con su período («3 horas por día», «10 hs semanales»)."""
    t = sin_tildes(texto)
    m = _RE_HORAS.search(t)
    if m:
        return horas_por_semana(_numero(m.group(1)), m.group(2))
    m = _RE_HORAS_ADJ.search(t)
    if m:
        periodo = {"diarias": "dia", "semanales": "semana", "mensuales": "mes"}[m.group(2)]
        return horas_por_semana(_numero(m.group(1)), periodo)
    return None


def _prioridad(valor: str | None, texto: str, obs: list[str]) -> str:
    if valor not in PRIORIDADES:
        return "ninguna"
    t = limpio(texto)
    if any(p in t for p in _PALABRAS_PRIORIDAD[valor]):
        return valor
    obs.append(f"prioridad «{valor}» descartada: el texto no la menciona (INT-R7)")
    return "ninguna"


def _juegos(nombres: list, texto_actividad: str, juegos_grafo: list[str], obs: list[str]) -> list[str]:
    """Solo los juegos que existen en el grafo (con su exigencia gráfica). Los demás se informan."""
    encontrados = [j for j in juegos_grafo if limpio(j) in limpio(texto_actividad)]
    for n in nombres or []:
        j = next((x for x in juegos_grafo if limpio(x) == limpio(n) or limpio(n) in limpio(x)
                  or limpio(x) in limpio(n)), None)
        if j:
            encontrados.append(j)
        elif n and limpio(n):
            obs.append(f"no tengo datos de exigencia gráfica de «{n}» en la base de conocimiento: "
                       "la intensidad gráfica se calcula solo con los juegos conocidos")
    return list(dict.fromkeys(encontrados))


def _perfil(tipo: str, hay_virtualizacion: bool) -> str | None:
    if tipo == "programar":
        return "VIRT" if hay_virtualizacion else "DEV"
    return PERFIL_POR_TIPO.get(tipo)


def _frecuencia(a: dict, texto: str, vocab: dict, obs: list[str]) -> tuple[str | None, float | None]:
    """(expresion del léxico, horas por semana) de una actividad. Nunca las inventa el LLM."""
    cita = a.get("evidencia") or ""
    horas = None
    if a.get("cantidad_horas") is not None and _numero_en_texto(a.get("cantidad_horas"), texto):
        horas = horas_por_semana(a.get("cantidad_horas"), a.get("periodo_horas"))
    if horas is None:
        horas = horas_en_texto(cita)
    if horas is not None:
        return None, horas
    expresiones = vocab.get("expresiones") or []
    e = a.get("expresion_frecuencia")
    if e in expresiones and (contiene_expresion(cita, e) or contiene_expresion(texto, e)):
        return e, None
    if e:
        obs.append(f"frecuencia «{e}» descartada: no está en el léxico o en el texto")
    candidatas = [x for x in expresiones if contiene_expresion(cita, x)]
    if candidatas:
        return max(candidatas, key=len), None
    # «una notebook para programar», «quiero programar»: el uso declarado como el propósito de la compra es
    # «la necesito para» (léxico del grafo; así se cargó req_01). Se avisa en las observaciones.
    t, c = limpio(texto), limpio(cita)
    pos = t.find(c)
    antes = set(t[:pos].split()[-3:] + c.split()) if pos >= 0 else set()   # la cita y las 3 palabras previas
    if "la necesito para" in expresiones and antes & _PROPOSITO:
        obs.append(f"«{cita}» se tomó como el uso principal («la necesito para», léxico): no dice con qué frecuencia")
        return "la necesito para", None
    return None, None


def _faltantes(datos: dict, sin_presupuesto: str | None) -> list[str]:
    preguntas = []
    if not datos["actividades"]:
        preguntas.append("¿Para qué vas a usar la notebook? Por ejemplo: programar, usar Docker o máquinas "
                         "virtuales, Office y navegador, diseño, edición de video o juegos (decime cuáles).")
    elif not any(a["horas"] is not None or a["expresion"] for a in datos["actividades"]):
        usos = " y ".join(a["descripcion"] for a in datos["actividades"])
        preguntas.append(f"¿Cuántas horas por semana la vas a usar para {usos}? También sirve «todos los días», "
                         "«a veces» o «principalmente».")
    if sin_presupuesto:
        preguntas.append(sin_presupuesto)
    return preguntas


def validar_pedido(texto: str, ext: dict, vocab: dict) -> tuple[PedidoValidado, list[str], str | None]:
    """Devuelve (pedido validado, preguntas imprescindibles, motivo si el presupuesto no sirve).

    No escribe nada: es la capa de validación del sándwich (PI4 de SM1).
    """
    ext = ext if isinstance(ext, dict) else {}
    obs: list[str] = []

    # Presupuesto (INT-R7, INT-R1, INT-R10): manda el monto escrito en el texto
    escrito = presupuesto_en_texto(texto)
    pres = ext.get("presupuesto") or {}
    monto, moneda = (escrito[0], escrito[1]) if escrito else (None, None)
    if monto is None and pres.get("monto") is not None:
        if _numero_en_texto(pres.get("monto"), texto) and pres.get("moneda") in ("USD", "ARS"):
            monto, moneda = float(pres["monto"]), pres["moneda"]
        else:
            obs.append(f"presupuesto {pres.get('monto')} descartado: no figura en el texto con su moneda (INT-R7)")
    motivo = None
    usd = None
    if monto is None:
        motivo = "¿Cuál es tu presupuesto? Indicalo en dólares, por ejemplo «tengo 900 USD»."
    elif moneda == "ARS":
        if config.COTIZACION_ARS_USD:
            usd = round(monto / config.COTIZACION_ARS_USD, 2)
            obs.append(f"presupuesto de {monto:g} ARS convertido a {usd:g} USD con la cotización "
                       f"configurada ({config.COTIZACION_ARS_USD:g} pesos por dólar, INT-R10)")
        else:
            motivo = (f"No tengo cargada la cotización del dólar para convertir {monto:g} pesos (INT-R10). "
                      "¿Me decís el presupuesto en dólares?")
    else:
        usd = monto
    if usd is not None and not 0 < usd <= PRESUPUESTO_MAXIMO_USD:
        motivo = f"El presupuesto de {usd:g} USD no parece válido (INT-R1). ¿Cuánto podés invertir, en dólares?"
        usd = None

    # Actividades (INT-R7, INT-R11)
    crudas = [a for a in ext.get("actividades") or [] if isinstance(a, dict)]
    validas = []
    for a in crudas:
        if not contiene(texto, a.get("evidencia") or ""):
            obs.append(f"actividad «{a.get('descripcion')}» descartada: su cita no está en el texto (INT-R7)")
            continue
        validas.append(a)
    hay_virtualizacion = any(a.get("tipo") == "virtualizar" for a in validas)
    actividades, sin_dedicacion = [], []
    juegos_grafo = vocab.get("juegos") or []
    for a in validas:
        perfil = _perfil(a.get("tipo"), hay_virtualizacion)
        if perfil is None:
            obs.append(f"«{a.get('evidencia')}» no define un perfil de uso (INT-R11): no se usa para inferir")
            continue
        expresion, horas = _frecuencia(a, texto, vocab, obs)
        juegos = _juegos(a.get("juegos") or [], a.get("evidencia") or "", juegos_grafo, obs) \
            if a.get("tipo") == "jugar" else []
        actividad = {"id": f"A{len(actividades) + 1}", "descripcion": (a.get("descripcion") or a.get("tipo")).strip(),
                     "tipo": a.get("tipo"), "perfil": perfil, "fragmento": a["evidencia"].strip(),
                     "expresion": expresion, "horas": horas, "juegos": juegos}
        if expresion is None and horas is None:
            sin_dedicacion.append(actividad["descripcion"])
        actividades.append(actividad)

    # Juegos del grafo nombrados en el texto sin una actividad «jugar» (el LLM la omitió)
    if not any(a["tipo"] == "jugar" for a in actividades):
        nombrados = [j for j in juegos_grafo if limpio(j) in limpio(texto)]
        if nombrados:
            obs.append(f"se nombra {', '.join(nombrados)} pero no se reconoció la actividad de jugar")

    # Consulta puntual: el modelo escrito en el texto y existente en el catálogo
    notebook = None
    for m in _RE_MODELO.findall(texto):
        candidato = f"Notebook_{m.upper()}"
        if candidato in (vocab.get("catalogo") or []):
            notebook = candidato
            break

    preguntas_deseables = [f"¿Cuántas horas por semana vas a dedicar a {d}?" for d in sin_dedicacion] \
        if len(sin_dedicacion) < len(actividades) else []
    datos: PedidoValidado = {
        "presupuesto_usd": usd, "moneda_original": moneda or "USD",
        "prioridad": _prioridad(ext.get("prioridad"), texto, obs),
        "usa_monitor_externo": bool(ext.get("usa_monitor_externo")) and "monitor" in limpio(texto),
        "notebook_consultada": notebook, "actividades": actividades,
        "preguntas": preguntas_deseables, "observaciones": obs,
    }
    return datos, _faltantes(datos, None), motivo


def _entendido(datos: dict) -> dict:
    return {
        "presupuesto_usd": datos.get("presupuesto_usd"), "moneda_original": datos.get("moneda_original"),
        "prioridad": datos.get("prioridad"), "notebook_consultada": datos.get("notebook_consultada"),
        "actividades": [{"descripcion": a["descripcion"], "perfil": a["perfil"], "cita": a["fragmento"],
                         "frecuencia": a["expresion"], "horas_semana": a["horas"], "juegos": a["juegos"]}
                        for a in datos.get("actividades") or []],
        "preguntas_pendientes": datos.get("preguntas") or [],
    }


def _repregunta(preguntas: list[str]) -> Aclaracion:
    if len(preguntas) == 1:
        return Aclaracion("Para armar tu pedido me falta un dato. " + preguntas[0])
    return Aclaracion("Para armar tu pedido me faltan algunos datos:\n" + "\n".join(f"- {p}" for p in preguntas))


# ---------------------------------------------------------------------------
# Pedido nuevo
# ---------------------------------------------------------------------------
def registrar_pedido(grafo, p: dict) -> tuple[list, EvidenciaRegistro]:
    """Valida el JSON extraído, da de alta el pedido y corre la inferencia para ese pedido (D-08)."""
    texto, ext = p["texto"], p.get("pedido") or {}
    vocab = repositorio.vocabulario(grafo)
    datos, faltan, motivo = validar_pedido(texto, ext, vocab)
    if ext.get("es_pedido_notebook") is False and not datos["actividades"] and datos["presupuesto_usd"] is None:
        raise Aclaracion("No entendí un pedido de notebook. Contame para qué la vas a usar y cuánto querés gastar, "
                         "por ejemplo: «quiero programar y usar Docker, tengo 900 USD».")
    if motivo:
        faltan.append(motivo)
    if faltan:
        raise _repregunta(faltan)
    c = repositorio.registrar(grafo, datos, texto)
    req = c["filas"][0]["requerimiento_id"]
    evidencia: EvidenciaRegistro = {"requerimiento_id": req, "pedido_nuevo": True, "entendido": _entendido(datos),
                                    "observaciones": datos["observaciones"]}
    return [c], evidencia


def aclarar_pedido(grafo, p: dict) -> tuple[list, EvidenciaRegistro]:
    """Completa el MISMO pedido con la respuesta, marca sus preguntas como respondidas y lo vuelve a inferir."""
    req, texto, ext = p["requerimiento_id"], p["respuesta"], p.get("pedido") or {}
    actual = repositorio.pedido(grafo, req)
    if not actual["filas"]:
        raise Aclaracion(f"No existe el pedido {req}.")
    fila = actual["filas"][0]
    previas = [a for a in fila["actividades"] if a]
    pendientes = [q for q in fila["preguntas"] or [] if q]
    vocab = repositorio.vocabulario(grafo)
    datos, _, motivo = validar_pedido(texto, ext, vocab)

    # Las actividades nuevas siguen la numeración de las que ya tiene el pedido
    for i, a in enumerate(datos["actividades"], start=len(previas) + 1):
        a["id"] = f"A{i}"
    # Una cantidad de horas o una frecuencia suelta completa las actividades que no tenían dedicación
    sin_horas = [a["id"] for a in previas if a.get("dedicacion_origen") == "desconocida"]
    horas = horas_en_texto(texto)
    if horas is None and sin_horas and not datos["actividades"]:
        e = next((x for x in sorted(vocab.get("expresiones") or [], key=len, reverse=True)
                  if contiene_expresion(texto, x)), None)
        horas = (vocab.get("horas_expresion") or {}).get(e) if e else None
    cambia = bool(datos["actividades"]) or datos["presupuesto_usd"] is not None or (horas is not None and sin_horas)
    if not cambia:
        if motivo and presupuesto_en_texto(texto):
            raise Aclaracion(motivo)
        detalle = (" Lo que falta es: " + " ".join(pendientes)) if pendientes else ""
        raise Aclaracion(f"No encontré en tu respuesta un dato nuevo para el pedido {req}.{detalle}")
    c = repositorio.aclarar(grafo, req, datos, texto, sin_horas, horas)
    entendido = _entendido(datos)
    if horas is not None and sin_horas:
        entendido["horas_semana_completadas"] = horas
    evidencia: EvidenciaRegistro = {"requerimiento_id": req, "pedido_nuevo": False, "entendido": entendido,
                                    "observaciones": datos["observaciones"]}
    return [c], evidencia
