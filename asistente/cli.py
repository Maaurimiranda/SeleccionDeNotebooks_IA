"""Consola del asistente. Capa de controlador alternativa a la API.

Uso:
  python -m asistente.cli                       # bucle interactivo
  python -m asistente.cli "¿Qué me recomendás para req_01?"   # una sola consulta
  python -m asistente.cli --traza ...           # muestra la traza de cada respuesta
Comandos del bucle: /pedido req_01 · /salir
"""
import argparse
import json

from asistente.orquestador import Orquestador
from asistente.router import normalizar_pedido


def mostrar(res: dict, con_traza: bool):
    print(f"\n{res['respuesta']}\n")
    print(f"  [origen: {res['origen_respuesta']} · pedido: {res['requerimiento_id'] or '-'} · "
          f"submódulos: {', '.join(res['submodulos_consultados']) or '-'}]")
    if con_traza:
        t = res["traza"]
        print("  plan:", json.dumps(t["plan"], ensure_ascii=False))
        if t["validacion"]["observaciones"]:
            print("  observaciones:", "; ".join(t["validacion"]["observaciones"]))
        for c in t["consultas"]:
            print(f"  consulta {c.get('nombre')} ({c.get('ms', '-')} ms): {len(c.get('filas', []))} filas, "
                  f"parámetros {json.dumps(c.get('parametros', {}), ensure_ascii=False)}")
        print(f"  duración: {t['duracion_ms']} · total {t['segundos']} s")
        if t["error"]:
            print("  error:", t["error"])


def main():
    ap = argparse.ArgumentParser(description="Consola del asistente de selección de notebooks")
    ap.add_argument("texto", nargs="*", help="consulta única (sin esto, abre el bucle)")
    ap.add_argument("--traza", action="store_true", help="muestra la traza de cada respuesta")
    ap.add_argument("--pedido", help="pedido inicial de la sesión (por ejemplo req_01)")
    args = ap.parse_args()

    orq = Orquestador()
    sesion = {"requerimiento_id": normalizar_pedido(args.pedido)} if args.pedido else {}
    if args.texto:
        mostrar(orq.consultar(" ".join(args.texto), sesion=sesion), args.traza)
        return
    print("Asistente de notebooks · /pedido req_01 fija el pedido · /salir termina")
    while True:
        try:
            linea = input(f"\n[{sesion.get('requerimiento_id') or 'sin pedido'}] > ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not linea:
            continue
        if linea in ("/salir", "/exit", "/q"):
            break
        if linea.startswith("/pedido"):
            req = normalizar_pedido(linea.removeprefix("/pedido"))
            if req:
                sesion["requerimiento_id"] = req
                print(f"Pedido de la sesión: {req}")
            else:
                print("Uso: /pedido req_01")
            continue
        mostrar(orq.consultar(linea, sesion=sesion), args.traza)


if __name__ == "__main__":
    main()
