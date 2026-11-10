"""Explicador común (PG3-13, D-07 §5 y §6): una sola explicación para cualquier combinación de submódulos.

El LLM redacta con `prompts/explicacion.txt`; el verificador comprueba cada respuesta contra la evidencia
(cifras, modelos, reglas, atribución de alertas, rangos, estados, perfil indeterminado, advertencia y largo).
Si falla `MAX_REGENERACIONES` veces, sale la plantilla fija, armada en código solo con la evidencia (REC-R11).
La exactitud la garantiza el verificador, no que el modelo obedezca.
"""
import json
import re
import unicodedata
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

from asistente.contrato import ESTADOS

MAX_REGENERACIONES = 2
MAX_PALABRAS = 180             # D-07 §5, para la respuesta del LLM
MAX_PALABRAS_PLANTILLA = 250   # la plantilla es el último recurso: completa, pero acotada
MAX_FILAS_PROMPT = 12          # filas de una lista que ve el LLM (qwen2.5:3b tiene poco contexto)
PERFILES = ("OFI", "DEV", "VIRT", "DIS", "VID3D", "GAM", "DATOS")
NOMBRES_DE_PERFIL = ("oficina", "ofimática", "ofimatica", "gamer", "gaming", "programación", "programacion",
                     "diseño", "diseno", "virtualización", "virtualizacion", "ciencia de datos")
RUTA_PROMPT = Path(__file__).resolve().parent.parent / "prompts" / "explicacion.txt"

_MODELO = re.compile(r"Notebook_[A-Z]\b")
_REGLA = re.compile(r"\b[A-Z]{2,4}-R\d+\b")
_IDENTIFICADOR = re.compile(r"Notebook_[A-Z]\b|\breq_\d+\b|\b[A-Z]{1,5}(?:-[A-Za-z0-9_]+)+\b")
_NUMERO = re.compile(r"(?<![\w.,])\d+(?:[.,]\d+)?")


# ---------------------------------------------------------------- utilidades
def _sin_tildes(t: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", t) if unicodedata.category(c) != "Mn").lower()


def _espacios(t: str) -> str:
    return " ".join(_sin_tildes(t).split())


def _oraciones(t: str) -> list[str]:
    """Parte en oraciones y líneas sin cortar los decimales (el punto de «0.785» no lleva espacio)."""
    return [s for s in re.split(r"(?<=[.!?])\s+|\n+", t) if s.strip()]


def _numeros(texto: str) -> list[Decimal]:
    """Números de un texto, con coma o punto decimal, sin los que forman parte de un identificador."""
    return [Decimal(n.replace(",", ".")) for n in _NUMERO.findall(_IDENTIFICADOR.sub(" ", texto))]


def _redondear(x: Decimal, decimales: int) -> Decimal:
    return x.quantize(Decimal(1).scaleb(-decimales), rounding=ROUND_HALF_UP)


def _es_rango(v) -> bool:
    return (isinstance(v, dict) and set(v) == {"min", "max"}
            and all(isinstance(v[k], (int, float)) and not isinstance(v[k], bool) for k in v))


def _numeros_de_la_evidencia(evidencia) -> set[Decimal]:
    nums: set[Decimal] = set()

    def rec(x):
        if isinstance(x, bool):
            return
        if isinstance(x, (int, float)):
            nums.add(Decimal(str(x)))
        elif isinstance(x, str):
            nums.update(_numeros(x))
        elif isinstance(x, dict):
            for v in x.values():
                rec(v)
        elif isinstance(x, (list, tuple)):
            for v in x:
                rec(v)

    rec(evidencia)
    return nums


def _respaldado(n: Decimal, nums: set[Decimal]) -> bool:
    """n está en la evidencia, o es ese número redondeado a los decimales con que se escribió,
    o es un grado (0 a 1) escrito como porcentaje."""
    d = max(0, -n.as_tuple().exponent)
    return any(_redondear(e, d) == n or (0 <= e <= 1 and _redondear(e * 100, d) == n) for e in nums)


def _recorrer(x, contexto=None):
    """Genera (dict, modelo) por cada dict de la evidencia; `modelo` es el del dict `notebook`/`modelo` más cercano."""
    if isinstance(x, dict):
        modelo = x.get("notebook") if isinstance(x.get("notebook"), str) else x.get("modelo")
        modelo = modelo if isinstance(modelo, str) else contexto
        yield x, modelo
        for v in x.values():
            yield from _recorrer(v, modelo)
    elif isinstance(x, (list, tuple)):
        for v in x:
            yield from _recorrer(v, contexto)


def _alertas(evidencia) -> dict[str, set[str]]:
    """código de alerta -> notebooks que la tienen."""
    por_codigo: dict[str, set[str]] = {}
    for d, _ in _recorrer(evidencia):
        modelo = d.get("notebook") or d.get("modelo")
        if isinstance(d.get("codigo"), str) and isinstance(modelo, str):
            por_codigo.setdefault(d["codigo"], set()).add(modelo)
    return por_codigo


def _rangos(evidencia) -> list[tuple[str | None, Decimal, Decimal]]:
    salida = []
    for d, modelo in _recorrer(evidencia):
        for v in d.values():
            if _es_rango(v) and v["min"] < v["max"]:
                salida.append((modelo, Decimal(str(v["min"])), Decimal(str(v["max"]))))
    return salida


_ESTADOS_NORM = {_sin_tildes(e): e for e in ESTADOS}
_ORDEN_ESTADOS = sorted(_ESTADOS_NORM, key=len, reverse=True)  # «Descartada (excluyente…)» antes que «Descartada»


def _estados_en(texto: str) -> set[str]:
    t, hallados = _sin_tildes(texto), set()
    for norm in _ORDEN_ESTADOS:
        if norm in t:
            hallados.add(_ESTADOS_NORM[norm])
            t = t.replace(norm, " ")
    return hallados


def _respalda(estado: str, permitidos: set[str]) -> bool:
    """«Descartada» alcanza si la evidencia dice «Descartada (excluyente incumplido)»; al revés, no."""
    return any(p == estado or p.startswith(estado + " ") for p in permitidos)


def _estados_por_modelo(evidencia) -> tuple[set[str], dict[str, set[str]]]:
    globales: set[str] = set()
    por_modelo: dict[str, set[str]] = {}
    for d, modelo in _recorrer(evidencia):
        for v in d.values():
            if isinstance(v, str) and _sin_tildes(v) in _ESTADOS_NORM:
                globales.add(_ESTADOS_NORM[_sin_tildes(v)])
                if modelo:
                    por_modelo.setdefault(modelo, set()).add(_ESTADOS_NORM[_sin_tildes(v)])
    return globales, por_modelo


# ---------------------------------------------------------------- verificador
def verificar(respuesta: str, evidencia: dict, max_palabras: int = MAX_PALABRAS) -> list[str]:
    """Problemas de la respuesta contra la evidencia (lista vacía = pasa). Controles (a) a (h) de D-07 §6."""
    problemas: list[str] = []
    volcado = json.dumps(evidencia, ensure_ascii=False)
    oraciones = _oraciones(respuesta)

    # (a) cada número está en la evidencia (con tolerancia de redondeo)
    nums = _numeros_de_la_evidencia(evidencia)
    for n in dict.fromkeys(_numeros(respuesta)):
        if not _respaldado(n, nums):
            problemas.append(f"(a) la cifra {n} no está en la evidencia")

    # (b) los modelos y las reglas citados existen en la evidencia
    for m in dict.fromkeys(re.findall(r"\bNotebo\w*", respuesta)):
        if m not in ("Notebook", "Notebooks") and not (_MODELO.fullmatch(m) and m in volcado):
            problemas.append(f"(b) el modelo «{m}» no está en la evidencia")
    for r in dict.fromkeys(_REGLA.findall(respuesta)):
        if r not in volcado:
            problemas.append(f"(b) la regla {r} no está en la evidencia")

    # (c) cada alerta está atribuida a su notebook
    alertas = _alertas(evidencia)
    for o in oraciones:
        modelos = set(_MODELO.findall(o))
        for codigo in dict.fromkeys(_REGLA.findall(o)):
            duenos = alertas.get(codigo)
            if duenos and any(m not in duenos for m in modelos):
                problemas.append(f"(c) la alerta {codigo} es de {', '.join(sorted(duenos))}, "
                                 f"no de {', '.join(sorted(modelos - duenos))}")

    # (d) largo
    palabras = len(respuesta.split())
    if palabras > max_palabras:
        problemas.append(f"(d) tiene {palabras} palabras y el máximo es {max_palabras}")

    # (e) advertencia
    advertencia = evidencia.get("advertencia")
    if advertencia and _espacios(advertencia) not in _espacios(respuesta):
        problemas.append("(e) falta la advertencia, copiada literal")

    # (f) un rango se dice como rango: ni un valor intermedio ni un solo extremo
    for modelo, lo, hi in _rangos(evidencia):
        for o in oraciones:
            if modelo and modelo not in o:
                continue
            en_o = _numeros(o)
            adentro = [n for n in en_o if lo < n < hi and not _respaldado(n, {lo, hi})]
            tiene_lo, tiene_hi = (any(_respaldado(n, {x}) for n in en_o) for x in (lo, hi))
            if adentro:
                problemas.append(f"(f) da {adentro[0]} dentro del rango [{lo} ; {hi}]{' de ' + modelo if modelo else ''}: "
                                 "tiene que decir el rango entero")
            elif tiene_lo != tiene_hi:
                problemas.append(f"(f) da un solo extremo del rango [{lo} ; {hi}]{' de ' + modelo if modelo else ''}")

    # (g) un pedido indeterminado no se completa con un perfil
    pedido = evidencia.get("pedido") or {}
    if pedido.get("perfil_dominante") == "indeterminado" or pedido.get("estado_pedido") == "indeterminado":
        for o in oraciones:
            asumido = [p for p in PERFILES if re.search(rf"\b{p}\b", o)]
            asumido += [p for p in NOMBRES_DE_PERFIL
                        if "perfil" in o.lower() and p in o.lower() and "indeterminado" not in o.lower()]
            if asumido:
                problemas.append(f"(g) el pedido está indeterminado y la respuesta nombra el perfil {asumido[0]}")
                break

    # (h) los estados, comparados sin tildes, son los que dice la evidencia
    globales, por_modelo = _estados_por_modelo(evidencia)
    for o in oraciones:
        modelos = set(_MODELO.findall(o))
        for estado in _estados_en(o):
            if not _respalda(estado, globales):
                problemas.append(f"(h) el estado «{estado}» no está en la evidencia")
            elif len(modelos) == 1:
                m = next(iter(modelos))
                if por_modelo.get(m) and not _respalda(estado, por_modelo[m]):
                    problemas.append(f"(h) {m} no está «{estado}»: la evidencia dice «{'», «'.join(sorted(por_modelo[m]))}»")
    return list(dict.fromkeys(problemas))


# ---------------------------------------------------------------- plantilla fija
def _valor(v) -> str:
    if _es_rango(v):
        return f"[{v['min']} ; {v['max']}]"
    if v is None:
        return "sin dato"
    if isinstance(v, bool):
        return "sí" if v else "no"
    return str(v)


def _escalares(d: dict, salvo=()) -> str:
    return ", ".join(f"{k} {_valor(v)}" for k, v in d.items()
                     if k not in salvo and (v is None or _es_rango(v) or isinstance(v, (str, int, float, bool))))


def _fila(d: dict) -> str:
    texto = f"- {d['notebook']}: " if d.get("notebook") else "- "
    texto += _escalares(d, salvo=("notebook",))
    alertas = [f"{a['codigo']} ({a.get('texto', '')})" for a in d.get("alertas") or []]
    return texto + ("; alertas: " + "; ".join(alertas) if alertas else "")


def _lineas_de(nombre: str, ev: dict) -> list[str]:
    lineas = [f"{nombre}:"]
    resumen = _escalares(ev, salvo=("requerimiento_id",))
    if resumen:
        lineas.append(resumen + ".")
    for clave, valor in ev.items():
        if not isinstance(valor, list) or not valor or not all(isinstance(x, dict) for x in valor):
            continue
        if clave == "reglas":
            ids = list(dict.fromkeys(r["id"] for r in valor if "id" in r))
            lineas.append(f"Reglas activadas: {', '.join(ids[:12])}.")
        elif clave != "parametros":
            lineas.extend(_fila(x) for x in valor)
    return lineas


def plantilla_fija(evidencia: dict) -> str:
    """Respuesta determinista (REC-R11), con lo que haya en la evidencia. Recorta por líneas, nunca por datos."""
    lineas: list[str] = []
    pedido = evidencia.get("pedido")
    if pedido:
        if pedido.get("estado_pedido") == "indeterminado" or pedido.get("perfil_dominante") == "indeterminado":
            falta = " ".join(pedido.get("preguntas_pendientes") or [])
            lineas.append(f"Pedido {pedido.get('requerimiento')}: perfil indeterminado, no se asume ninguno. "
                          f"Presupuesto {_valor(pedido.get('presupuesto'))}. Falta: {falta}")
        else:
            lineas.append(f"Pedido {pedido.get('requerimiento')}: perfil {pedido.get('perfil_dominante')}, "
                          f"presupuesto {_valor(pedido.get('presupuesto'))}, prioridad {pedido.get('prioridad')}.")
    for sm in ("SM1", "SM2", "SM3", "SM4", "GRUPO"):
        for intencion, ev in (evidencia.get(sm) or {}).items():
            lineas.extend(_lineas_de(f"{sm}.{intencion}", ev))
    cierre = [f"Advertencia: {evidencia['advertencia']}"] if evidencia.get("advertencia") else []
    reserva = sum(len(x.split()) for x in cierre) + 12
    salida, usadas = [], 0
    for i, linea in enumerate(lineas):
        usadas += len(linea.split())
        if usadas > MAX_PALABRAS_PLANTILLA - reserva:
            salida.append("(Hay más líneas de detalle: están en la traza de la consulta.)")
            break
        salida.append(linea)
    return "\n".join(salida + cierre)


# ---------------------------------------------------------------- explicación con el LLM
def _origen_agrupado(o):
    """GRUPO.traza_reglas: reglas que comparten el mismo parámetro y origen se muestran juntas."""
    if not (isinstance(o, dict) and isinstance(o.get("reglas"), dict)):
        return o
    grupos: dict[str, dict] = {}
    for regla, filas in o["reglas"].items():
        for f in filas:
            grupos.setdefault(json.dumps(f, sort_keys=True), {**f, "reglas": []})["reglas"].append(regla)
    return {**o, "reglas": list(grupos.values())}


def _compactar(x):
    """La evidencia que ve el LLM: las listas largas se acortan y las reglas repetidas (escenarios peor y mejor) se juntan.
    El verificador usa la evidencia completa."""
    if isinstance(x, dict):
        return {k: _compactar(_origen_agrupado(v) if k == "origen" else v) for k, v in x.items()}
    if isinstance(x, list):
        if x and all(isinstance(f, dict) and "id" in f and "fuerza" in f for f in x):
            por_id: dict[str, dict] = {}
            for f in x:
                e = por_id.setdefault(f["id"], {**f, "fuerza": []})
                if f["fuerza"] not in e["fuerza"]:
                    e["fuerza"].append(f["fuerza"])
                e.pop("escenario", None)
            x = [{**e, "fuerza": e["fuerza"][0] if len(e["fuerza"]) == 1 else e["fuerza"]} for e in por_id.values()]
        corta = [_compactar(f) for f in x[:MAX_FILAS_PROMPT]]
        return corta + [{"_omitidas": len(x) - MAX_FILAS_PROMPT}] if len(x) > MAX_FILAS_PROMPT else corta
    return x


def _correcciones(anterior: str, problemas: list[str]) -> str:
    return ("\nTU RESPUESTA ANTERIOR TUVO ESTOS PROBLEMAS. Corregilos y escribí la respuesta completa de nuevo:\n"
            + "\n".join(f"- {p}" for p in problemas) + f"\nRespuesta anterior:\n{anterior}\n")


def _con_advertencia(respuesta: str, evidencia: dict) -> str:
    """El modelo chico suele omitir la advertencia: si falta, la agrega el código, literal."""
    advertencia = evidencia.get("advertencia")
    if advertencia and _espacios(advertencia) not in _espacios(respuesta):
        return f"{respuesta}\n{advertencia}"
    return respuesta


def explicar(texto: str, evidencia: dict, llm) -> dict:
    """Genera, verifica y regenera hasta `MAX_REGENERACIONES` veces; si no pasa, plantilla fija.
    Devuelve {"respuesta", "origen_respuesta": "llm"|"plantilla_fija", "intentos": [{"texto", "problemas"}]}."""
    sistema = RUTA_PROMPT.read_text(encoding="utf-8")
    visible = json.dumps(_compactar(evidencia), ensure_ascii=False, separators=(",", ":"))
    intentos, correcciones = [], ""
    for _ in range(1 + MAX_REGENERACIONES):
        respuesta = _con_advertencia(
            llm.texto(sistema, texto, {"evidencia": visible, "correcciones": correcciones}), evidencia)
        problemas = verificar(respuesta, evidencia)
        intentos.append({"texto": respuesta, "problemas": problemas})
        if not problemas:
            return {"respuesta": respuesta, "origen_respuesta": "llm", "intentos": intentos}
        correcciones = _correcciones(respuesta, problemas)
    return {"respuesta": plantilla_fija(evidencia), "origen_respuesta": "plantilla_fija", "intentos": intentos}
