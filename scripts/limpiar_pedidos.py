"""Borra los pedidos creados desde consultas libres (D-08): los `Requerimiento` con origen 'consulta'
(req_101 en adelante) y todo lo que cuelga de ellos (actividades, evaluaciones, lecturas, alertas,
recomendación, preguntas y comprador). Nunca toca req_01..req_03.

Uso:  python -m scripts.limpiar_pedidos            (todos los pedidos creados desde consultas)
      python -m scripts.limpiar_pedidos req_101    (solo ese)
"""
import sys

from asistente import config
from asistente.grafo import Grafo
from asistente.submodulos.sm1 import repositorio


def main(args: list[str]) -> int:
    if not config.NEO4J_PASSWORD:
        print("Falta NEO4J_PASSWORD en el entorno (ver .env.example).")
        return 2
    grafo = Grafo()
    try:
        antes = [p for p in grafo.pedidos()]
        n = repositorio.borrar_pedidos_consulta(grafo, args[0] if args else None)
        print(f"Pedidos borrados: {n}. Quedan: {', '.join(Grafo().pedidos()) or 'ninguno'} (antes: {len(antes)}).")
    finally:
        grafo.cerrar()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
