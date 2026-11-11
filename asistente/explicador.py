"""Explicador común (PG3-13, D-07 §5 y §6): una sola explicación para cualquier combinación de submódulos.

El LLM redacta con `prompts/explicacion.txt`; el verificador comprueba cada respuesta contra la evidencia
(cifras, modelos, reglas, atribución de alertas, rangos, estados, perfil indeterminado, advertencia y largo).
Si falla `MAX_REGENERACIONES` veces, sale la plantilla fija, armada en código solo con la evidencia (REC-R11).
La exactitud la garantiza el verificador, no que el modelo obedezca.
"""
import json
import re
import unicodedata
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from pathlib import Path

from asistente.contrato import ESTADOS

MAX_REGENERACIONES = 2
MAX_PALABRAS = 180             # D-07 §5, para la respuesta del LLM
MAX_PALABRAS_PLANTILLA = 250   # la plantilla es el último recurso: completa, pero acotada
MAX_FILAS_PLANTILLA = 5        # filas de una lista que muestra la plantilla
MAX_FILAS_PROMPT = 12          # filas de una lista que ve el LLM (qwen2.5:3b tiene poco contexto)
PERFILES = ("OFI", "DEV", "VIRT", "DIS", "VID3D", "GAM", "DATOS")
NOMBRES_DE_PERFIL = ("oficina", "ofimática", "ofimatica", "gamer", "gaming", "programación", "programacion",
                     "diseño", "diseno", "virtualización", "virtualizacion", "ciencia de datos")
RUTA_PROMPT = Path(__file__).resolve().parent.parent / "prompts" / "explicacion.txt"

_MODELO = re.compile(r"Notebook_[A-Z]\b")
_REGLA = re.compile(r"\b[A-Z]{2,4}-RD?\d+\b")
_IDENTIFICADOR = re.compile(r"Notebook_[A-Z]\b|\breq_\d+\b|\b[A-Z]{1,5}(?:-[A-Za-z0-9_]+)+\b")
_NUMERO = re.compile(r"(?<![\w.,])\d{1,15}(?:[.,]\d{1,15})?")   # acotado: un número de 40 dígitos no tumba el verificador
_PARTIR_POR_MODELO = re.compile(r"(Notebook_[A-Z]\b)")


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
    o es un grado (0 a 1) escrito como porcentaje, o es «1.200» con punto de miles para 1200."""
    d = max(0, -n.as_tuple().exponent)
    miles = d == 3 and n >= 1   # tres decimales exactos: puede ser un punto de miles
    try:
        return any(_redondear(e, d) == n or (0 <= e <= 1 and _redondear(e * 100, d) == n) or (miles and e == n * 1000)
                   for e in nums)
    except InvalidOperation:   # una cifra que no se puede redondear no está respaldada
        return False


def _segmentos(oracion: str) -> list[tuple[str | None, str]]:
    """Parte la oración en tramos: cada uno es de la notebook nombrada justo antes (el primero, de ninguna)."""
    partes = _PARTIR_POR_MODELO.split(oracion)
    return [(None, partes[0])] + [(partes[i], partes[i + 1]) for i in range(1, len(partes) - 1, 2)]


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


def _numeros_por_modelo(evidencia) -> tuple[dict[str, set[Decimal]], set[Decimal]]:
    """Números de cada notebook (los de sus dicts y textos) y números que no son de ninguna (pedido, umbrales)."""
    por_modelo: dict[str, set[Decimal]] = {}
    sin_modelo: set[Decimal] = set()
    for d, modelo in _recorrer(evidencia):
        destino = por_modelo.setdefault(modelo, set()) if modelo else sin_modelo
        for v in d.values():
            for hoja in (v if isinstance(v, list) else [v]):
                if isinstance(hoja, bool):
                    continue
                if isinstance(hoja, (int, float)):
                    destino.add(Decimal(str(hoja)))
                elif isinstance(hoja, str):
                    destino.update(_numeros(hoja))
    return por_modelo, sin_modelo


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
def _recomendables(evidencia) -> set[str] | None:
    """Notebooks que la evidencia deja recomendar: las del ranking (`puesto`) o, sin ranking, las de estado
    `Recomendada*` dentro del presupuesto. None si la evidencia no dice nada (p. ej., solo SM2)."""
    clasificadas = {d["notebook"] for d, _ in _recorrer(evidencia) if d.get("notebook") and "puesto" in d}
    if clasificadas:
        return clasificadas
    _, por_modelo = _estados_por_modelo(evidencia)
    if not por_modelo:
        return None
    fuera = {m for d, m in _recorrer(evidencia) if m and (d.get("excedente_presupuesto_pct") or 0) > 0}
    return {m for m, es in por_modelo.items() if any(e.startswith("Recomendada") for e in es)} - fuera


_VERBO_RECOMENDAR = re.compile(r"recomiend|recomend|conviene|aconsej|mejor opcion|primer lugar|primera opcion|elegi|elegir")
_NEGACION = re.compile(r"\b(?:no|nunca|ni)\b")


def verificar(respuesta: str, evidencia: dict, max_palabras: int = MAX_PALABRAS) -> list[str]:
    """Problemas de la respuesta contra la evidencia (lista vacía = pasa). Controles (a) a (h) de D-07 §6.
    Lo que se dice de cada notebook se atribuye por tramos: cada tramo es de la notebook nombrada antes."""
    problemas: list[str] = []
    volcado = json.dumps(evidencia, ensure_ascii=False)
    oraciones = _oraciones(respuesta)
    tramos = [t for o in oraciones for t in _segmentos(o)]

    # (a) cada número está en la evidencia (con tolerancia de redondeo) y es un dato de la notebook de su tramo
    nums = _numeros_de_la_evidencia(evidencia)
    por_modelo, sin_modelo = _numeros_por_modelo(evidencia)
    for n in dict.fromkeys(_numeros(respuesta)):
        if not _respaldado(n, nums):
            problemas.append(f"(a) la cifra {n} no está en la evidencia")
    for m, texto in tramos:
        if m in por_modelo:
            for n in dict.fromkeys(_numeros(texto)):
                if _respaldado(n, nums) and not _respaldado(n, por_modelo[m] | sin_modelo):
                    problemas.append(f"(a) la cifra {n} no es un dato de {m}")

    # (b) los modelos y las reglas citados existen en la evidencia (id completo, no una subcadena de otro)
    for m in dict.fromkeys(re.findall(r"\bNotebo\w*", respuesta)):
        if m not in ("Notebook", "Notebooks") and not (_MODELO.fullmatch(m) and m in volcado):
            problemas.append(f"(b) el modelo «{m}» no está en la evidencia")
    ids_en_evidencia = set(_REGLA.findall(volcado))
    for r in dict.fromkeys(_REGLA.findall(respuesta)):
        if r not in ids_en_evidencia:
            problemas.append(f"(b) la regla {r} no está en la evidencia")

    # (c) cada alerta está atribuida a su notebook, y una alerta no se presenta como regla activada (ni al revés)
    alertas = _alertas(evidencia)
    reglas = {d["id"] for d, _ in _recorrer(evidencia) if isinstance(d.get("id"), str)}
    for m, texto in tramos:
        if _NEGACION.search(_sin_tildes(texto)):
            continue
        for codigo in dict.fromkeys(_REGLA.findall(texto)):
            duenos = alertas.get(codigo)
            if m and duenos and m not in duenos:
                problemas.append(f"(c) la alerta {codigo} es de {', '.join(sorted(duenos))}, no de {m}")
    for o in oraciones:
        o_sin = _sin_tildes(o)
        for codigo in dict.fromkeys(_REGLA.findall(o)):
            tras_regla = re.search(r"(?:\breglas?|activ\w*)[^.;,]{0,20}" + re.escape(codigo.lower()), o_sin)
            if codigo in alertas and codigo not in reglas and tras_regla:
                problemas.append(f"(c) {codigo} es una alerta, no una regla activada")
            elif codigo in reglas and codigo not in alertas and "alerta" in o_sin:
                problemas.append(f"(c) {codigo} es una regla, no una alerta")

    # (d) largo
    palabras = len(respuesta.split())
    if not palabras:
        problemas.append("(d) la respuesta está vacía")
    elif palabras > max_palabras:
        problemas.append(f"(d) tiene {palabras} palabras y el máximo es {max_palabras}")

    # (e) advertencia
    advertencia = evidencia.get("advertencia")
    if advertencia and _espacios(advertencia) not in _espacios(respuesta):
        problemas.append("(e) falta la advertencia, copiada literal")

    # (f) un rango se dice como rango: ni un valor intermedio ni un solo extremo
    for modelo, lo, hi in _rangos(evidencia):
        propios = por_modelo.get(modelo, set()) | sin_modelo if modelo else nums  # otro dato de la notebook no es un promedio
        for o in oraciones:
            if modelo:
                texto = " ".join(t for m, t in _segmentos(o) if m == modelo)
                if not texto:
                    continue
            else:
                texto = o
            en_o = _numeros(texto)
            adentro = [n for n in en_o if lo < n < hi and not _respaldado(n, propios)]
            tiene_lo, tiene_hi = (any(_respaldado(n, {x}) for n in en_o) for x in (lo, hi))
            if adentro:
                problemas.append(f"(f) da {adentro[0]} dentro del rango [{lo} ; {hi}]{' de ' + modelo if modelo else ''}: "
                                 "tiene que decir el rango entero")
            elif tiene_lo != tiene_hi:
                problemas.append(f"(f) da un solo extremo del rango [{lo} ; {hi}]{' de ' + modelo if modelo else ''}")

    # (g) un pedido indeterminado no se completa con un perfil (repetir la pregunta pendiente sí se puede)
    pedido = evidencia.get("pedido") or {}
    if pedido.get("perfil_dominante") == "indeterminado" or pedido.get("estado_pedido") == "indeterminado":
        preguntas = _espacios(" ".join(pedido.get("preguntas_pendientes") or []))
        for o in oraciones:
            if "?" in o or (preguntas and _espacios(o).strip(" .:") in preguntas):
                continue
            o_sin = _sin_tildes(o)
            asumido = [p for p in PERFILES if re.search(rf"\b{p}\b", o)]
            asumido += [p for p in NOMBRES_DE_PERFIL if p in o_sin]
            if asumido:
                problemas.append(f"(g) el pedido está indeterminado y la respuesta nombra el perfil {asumido[0]}")
                break

    # (h) los estados, comparados sin tildes, son los de cada notebook; solo se recomienda lo que la evidencia recomienda
    globales, estados = _estados_por_modelo(evidencia)
    for m, texto in tramos:
        for estado in _estados_en(texto):
            if not _respalda(estado, globales):
                problemas.append(f"(h) el estado «{estado}» no está en la evidencia")
            elif m and estados.get(m) and not _respalda(estado, estados[m]):
                problemas.append(f"(h) {m} no está «{estado}»: la evidencia dice «{'», «'.join(sorted(estados[m]))}»")
    recomendables = _recomendables(evidencia)
    if recomendables is not None:
        for o in oraciones:
            modelos = set(_MODELO.findall(o))
            sin_estados = _sin_tildes(o)
            for e in _estados_en(o):
                sin_estados = sin_estados.replace(_sin_tildes(e), " ")
            if len(modelos) == 1 and _VERBO_RECOMENDAR.search(sin_estados) and not _NEGACION.search(sin_estados):
                m = next(iter(modelos))
                if m not in recomendables:
                    problemas.append(f"(h) recomienda {m}, que la evidencia no recomienda")
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
    return ", ".join(f"{k.replace('_', ' ')} {_valor(v)}" for k, v in d.items()
                     if k not in salvo and (v is None or _es_rango(v) or isinstance(v, (str, int, float, bool))))


def _fila(d: dict) -> str:
    """Una notebook en una línea: sus datos, las listas de texto (cumple, no cumple, falta verificar) y sus alertas."""
    partes = [_escalares(d, salvo=("notebook",))]
    for k, v in d.items():
        if isinstance(v, list) and v and all(isinstance(x, str) for x in v):
            partes.append(f"{k.replace('_', ' ')}: {'; '.join(v)}")
    alertas = [f"{a['codigo']} ({a.get('texto', '')})" for a in d.get("alertas") or []]
    if alertas:
        partes.append("alertas: " + "; ".join(alertas))
    return (f"- {d['notebook']}: " if d.get("notebook") else "- ") + "; ".join(p for p in partes if p)


def _lineas_de(nombre: str, ev: dict) -> list[str]:
    lineas = [f"{nombre}:"]
    resumen = _escalares({k: v for k, v in ev.items() if v is not None}, salvo=("requerimiento_id",))
    if resumen:
        lineas.append(resumen + ".")
    for clave, valor in ev.items():
        etiqueta = clave.replace("_", " ")
        if isinstance(valor, dict) and clave not in ("origen", "pesos") and not _es_rango(valor):
            if valor.get("notebook"):
                lineas.append(f"{etiqueta}: " + _fila(valor)[2:])
            elif _escalares(valor):
                lineas.append(f"{etiqueta}: {_escalares(valor)}.")
        elif isinstance(valor, list) and valor and all(isinstance(x, dict) for x in valor):
            if clave == "reglas":
                ids = list(dict.fromkeys(r["id"] for r in valor if "id" in r))
                lineas.append(f"Reglas activadas: {', '.join(ids[:12])}{' y otras (ver la traza)' if len(ids) > 12 else ''}.")
            elif clave != "parametros":
                lineas.extend(_fila(x) for x in valor[:MAX_FILAS_PLANTILLA])
                if len(valor) > MAX_FILAS_PLANTILLA:
                    lineas.append("(Hay más filas: están en la traza de la consulta.)")
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
            lineas.append(f"Pedido {pedido.get('requerimiento')}: perfil {pedido.get('perfil_dominante')}"
                          f"{' (provisional)' if pedido.get('perfil_dominante_provisional') else ''}, "
                          f"presupuesto {_valor(pedido.get('presupuesto'))}, prioridad {pedido.get('prioridad')}.")
    for sm in ("SM4", "SM2", "SM3", "SM1", "GRUPO"):  # lo más importante primero: el recorte es por líneas, desde el final
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
    if respuesta.strip() and advertencia and _espacios(advertencia) not in _espacios(respuesta):
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
