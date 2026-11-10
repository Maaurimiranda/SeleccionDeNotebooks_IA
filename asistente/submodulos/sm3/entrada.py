"""SM3 · Entrada (controlador del módulo): valida orden y rangos de los filtros, y despacha."""
from asistente.contrato import Aclaracion, ORDENES_SM3
from asistente.submodulos.sm3 import servicio

RANGO_PESO_KG = (0.5, 5.0)
RANGO_BATERIA_H = (0.0, 30.0)     # (mín excluido, máx incluido]
RANGO_GAMA = (1, 5)
RANGO_SRGB = (0, 100)

_SERVICIOS = {
    "SM3.buscar": servicio.buscar,
    "SM3.ficha": servicio.ficha,
}


def validar_rangos(filtros: dict) -> list[str]:
    """Guardas deterministas: devuelve los valores imposibles."""
    problemas = []
    peso, bat, gama, srgb = (filtros.get(k) for k in ("peso_max", "bateria_min", "gama_min", "srgb_min"))
    if peso is not None and not RANGO_PESO_KG[0] <= peso <= RANGO_PESO_KG[1]:
        problemas.append(f"un peso máximo de {peso:g} kg (las notebooks pesan entre "
                         f"{RANGO_PESO_KG[0]:g} y {RANGO_PESO_KG[1]:g} kg)")
    if bat is not None and not RANGO_BATERIA_H[0] < bat <= RANGO_BATERIA_H[1]:
        problemas.append(f"una batería de al menos {bat:g} h (el máximo realista es {RANGO_BATERIA_H[1]:g} h)")
    if gama is not None and not RANGO_GAMA[0] <= gama <= RANGO_GAMA[1]:
        problemas.append(f"una gama de GPU {gama} (la escala va de 1 a 5)")
    if srgb is not None and not RANGO_SRGB[0] <= srgb <= RANGO_SRGB[1]:
        problemas.append(f"un sRGB de {srgb:g} % (va de 0 a 100)")
    return problemas


def ejecutar(intencion: str, parametros: dict, grafo) -> dict:
    if intencion not in _SERVICIOS:
        raise ValueError(f"SM3 no atiende la intención {intencion!r}")
    p = dict(parametros)
    if not p.get("requerimiento_id"):
        raise Aclaracion("¿Sobre qué pedido? Indicá el requerimiento, por ejemplo req_01.")
    if intencion == "SM3.buscar":
        p["orden"] = p.get("orden") or "mixta"
        if p["orden"] not in ORDENES_SM3:
            raise Aclaracion(f"Puedo ordenar por {', '.join(ORDENES_SM3)}.")
        filtros = {k: v for k, v in (p.get("filtros") or {}).items() if v is not None}
        problemas = validar_rangos(filtros)
        if problemas:
            raise Aclaracion("No puedo buscar con " + " y ".join(problemas) + ". ¿Podés revisar el valor?")
        p["filtros"] = filtros
    elif not p.get("modelo"):
        raise Aclaracion("¿De qué notebook querés la ficha? Por ejemplo, Notebook_X.")
    consultas, evidencia = _SERVICIOS[intencion](grafo, p)
    return {"consultas": consultas, "evidencia": evidencia}
