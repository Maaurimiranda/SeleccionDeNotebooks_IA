"""Explicador (STUB de PG3-01). Luconi lo completa en PG3-13 con el prompt común,
el verificador y la plantilla fija definitiva (D-07 §5 y §6).

Por ahora `explicar` usa una plantilla mínima armada solo con la evidencia:
no llama al LLM, así que no puede inventar nada.
"""


def _linea(clave: str, valor) -> str:
    if isinstance(valor, dict):
        return f"- {clave}: " + ", ".join(f"{k}={v}" for k, v in valor.items() if v not in (None, [], {}))
    return f"- {clave}: {valor}"


def plantilla_fija(evidencia: dict) -> str:
    partes = []
    pedido = evidencia.get("pedido")
    if pedido:
        if pedido.get("estado_pedido") == "indeterminado":
            partes.append(f"Pedido {pedido['requerimiento']}: perfil indeterminado. Pregunta pendiente: "
                          + " ".join(pedido.get("preguntas_pendientes") or []))
        else:
            partes.append(f"Pedido {pedido['requerimiento']}: perfil {pedido['perfil_dominante']}, "
                          f"presupuesto {pedido['presupuesto']} USD, prioridad {pedido['prioridad']}.")
    for sm in ("SM1", "SM2", "SM3", "SM4", "GRUPO"):
        for intencion, ev in (evidencia.get(sm) or {}).items():
            partes.append(f"[{sm}.{intencion}]")
            if "notebooks" in ev:
                for nb in ev["notebooks"]:
                    datos = {k: v for k, v in nb.items() if k not in ("reglas", "alertas", "notebook")}
                    partes.append(_linea(nb["notebook"], datos))
                    for a in nb.get("alertas") or []:
                        partes.append(f"  alerta {a['codigo']} ({a['notebook']}): {a['texto']}")
            elif "reglas" in ev:
                for r in ev["reglas"]:
                    f = "" if r.get("fuerza") is None else f" fuerza {r['fuerza']}"
                    partes.append(f"- {r['id']} ({r.get('submodulo')}){f}")
            elif "parametros" in ev:
                partes.append(f"- {ev['sin_validar']} de {ev['total']} parametros sin validar")
            else:
                partes.extend(_linea(k, v) for k, v in ev.items() if k != "requerimiento_id")
    if evidencia.get("advertencia"):
        partes.append(f"Advertencia: {evidencia['advertencia']}")
    return "\n".join(partes)


def verificar(respuesta: str, evidencia: dict) -> list[str]:
    """STUB: el verificador real (cifras, modelos, reglas y atribución de alertas) es de PG3-13."""
    return []


def explicar(texto: str, evidencia: dict, llm) -> dict:
    return {"respuesta": plantilla_fija(evidencia), "origen_respuesta": "plantilla_fija", "intentos": []}
