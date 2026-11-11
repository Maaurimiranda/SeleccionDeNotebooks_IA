"""Dibuja las dos figuras del informe (sección 4) con matplotlib.

Uso (desde la raíz del repo):  python docs/informe/figuras.py
Escribe docs/informe/figuras/arquitectura.png y docs/informe/figuras/flujo.png.
Las cifras de la figura 2 son las del E2E-9 (docs/pruebas/E2E-9.md).
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

SALIDA = Path(__file__).resolve().parent / "figuras"

# Un color por quién decide: Python valida, el LLM interpreta y explica, Neo4j razona.
PY = ("#DCE6F2", "#2F5D8C")
LLM = ("#FCE5CD", "#C26A1B")
NEO = ("#D9EAD3", "#38761D")
GRIS = ("#EEEEEE", "#666666")
FONDO = ("#FAFAFA", "#9A9A9A")


def caja(ax, x, y, w, h, texto, col, fs=6.6, negrita=False, ls="-", radio=1.2):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={radio}",
                                fc=col[0], ec=col[1], lw=0.9, ls=ls))
    if texto:
        ax.text(x + w / 2, y + h / 2, texto, ha="center", va="center", fontsize=fs,
                fontweight="bold" if negrita else "normal", color="#222222", linespacing=1.25)


def flecha(ax, p, q, col="#333333", ls="-", doble=False, lw=0.9):
    ax.annotate("", xy=q, xytext=p,
                arrowprops=dict(arrowstyle="<|-|>" if doble else "-|>", color=col, lw=lw, ls=ls,
                                shrinkA=0, shrinkB=0, mutation_scale=7))


def arquitectura():
    fig, ax = plt.subplots(figsize=(7.4, 5.6))
    ax.set_xlim(0, 100)
    ax.set_ylim(-15, 66)
    ax.axis("off")

    # Leyenda de colores
    for i, (col, txt) in enumerate([(LLM, "LLM: interpreta y explica"), (PY, "Python: valida y coordina"),
                                    (NEO, "Neo4j: guarda la verdad (reglas y difuso)")]):
        x = 1 + i * 29
        ax.add_patch(FancyBboxPatch((x, 62), 2.4, 2.4, boxstyle="round,pad=0,rounding_size=0.4",
                                    fc=col[0], ec=col[1], lw=0.9))
        ax.text(x + 3.6, 63.2, txt, fontsize=6.4, va="center")

    # Usuario e interfaz
    caja(ax, 1, 40, 14, 12, "Usuario\n(asesor\nde ventas)", GRIS, negrita=True)
    caja(ax, 1, 21, 14, 14, "Interfaz\nAPI FastAPI\nPOST /consultar\nConsola (CLI)", GRIS, fs=6.2)
    flecha(ax, (8, 40), (8, 35))

    # Orquestación
    caja(ax, 18, 0.5, 26, 58, "", FONDO, ls="--", radio=2)
    ax.text(31, 55.2, "Orquestación (Python)", ha="center", fontsize=6.6, fontweight="bold", color="#555555")
    caja(ax, 20, 41, 22, 11, "Router\nprompt maestro\n→ plan JSON", PY, negrita=False)
    caja(ax, 20, 20, 22, 14, "Orquestador\nvalida el plan, despacha\ny arma la evidencia\ncomún", PY)
    caja(ax, 20, 3.5, 22, 12, "Explicador\n+ verificador\n+ plantilla fija", PY)
    flecha(ax, (15, 28), (20, 28))
    flecha(ax, (31, 34), (31, 41), doble=True)
    flecha(ax, (31, 20), (31, 15.5), doble=True)

    # Modelo de lenguaje
    caja(ax, 47, 38, 13, 16, "Modelo de\nlenguaje\nOllama local\nqwen2.5:3b\ntemperatura 0", LLM, fs=6.2)
    flecha(ax, (42, 46.5), (47, 46.5), col=LLM[1], ls="--", doble=True)
    ax.plot([42, 53.5], [9.5, 9.5], color=LLM[1], ls="--", lw=0.9)
    flecha(ax, (53.5, 9.5), (53.5, 38), col=LLM[1], ls="--", doble=True)

    # Módulos de razonamiento
    caja(ax, 63, 0.5, 24, 58, "", FONDO, ls="--", radio=2)
    ax.text(75, 56, "Módulos de\nrazonamiento", ha="center", va="center", fontsize=6.4, fontweight="bold", color="#555555")
    mods = ["SM1 · Interpretación\ndel pedido", "SM2 · Riesgo de RAM\ny virtualización", "SM3 · Gráfica\ny movilidad",
            "SM4 · Recomendación\ny costo-beneficio", "GRUPO · traza de\nreglas y parámetros"]
    ys = [41.5, 32, 22.5, 13, 3.5]
    for y, m in zip(ys, mods):
        caja(ax, 64.5, y, 21, 8, m, PY, fs=5.9)
        flecha(ax, (85.5, y + 4), (89, y + 4))
    flecha(ax, (42, 27), (63, 27))
    ax.text(47.7, 28.0, "Cypher\nfijo", ha="center", va="bottom", fontsize=5.6, color="#444444")

    # Neo4j
    caja(ax, 89, 0.5, 11, 58, "Neo4j\n\nbase de\nconocimiento\n\ngrafo\ncanónico\n\n343 nodos\n683\nrelaciones\n\nsolo\nlectura",
         NEO, fs=5.8, radio=2)

    # Traza
    caja(ax, 1, 3.5, 14, 9, "Traza JSONL\n(una por consulta)", GRIS, fs=6.0)
    flecha(ax, (20, 21), (15, 10), col="#666666", ls=":")

    # Fuentes
    caja(ax, 1, -13, 98.5, 8.5,
         "Fuentes de información: apuntes y guía de la cátedra · requisitos oficiales (Docker, Adobe, DaVinci, PyTorch, Steam)\n"
         "fichas (Intel ARK, AMD, NVIDIA, Lenovo PSREF) · Notebookcheck y RTINGS · entrevista a un técnico · Mercado Libre y tiendas oficiales",
         GRIS, fs=5.8)
    flecha(ax, (95, -4.5), (95, 0.5), col="#38761D", ls="--")
    ax.text(93.6, -2.3, "se cargan al grafo\ncon cypher/*.cypher", ha="right", va="center", fontsize=5.6, color="#38761D")

    fig.savefig(SALIDA / "arquitectura.png", dpi=220, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def flujo():
    pasos = [
        ("Consulta\ndel asesor", "", GRIS),
        ("Router\n(LLM)\nplan JSON", "2,6 s", LLM),
        ("Validación\n(Python)\nintención,\nmodelo, pedido", "", PY),
        ("Cypher fijo\n(Neo4j,\nsolo lectura)", "0,08 s", NEO),
        ("Explicador\n(LLM)\nredacta con la\nevidencia", "1,6 s", LLM),
        ("Verificador\n(Python)\ncifras,\nmodelos, reglas", "pasó al\nintento 1", PY),
        ("Respuesta\n+ traza", "", GRIS),
    ]
    fig, ax = plt.subplots(figsize=(7.4, 2.3))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 30)
    ax.axis("off")
    w, gap = 11.9, 2.55
    for i, (txt, tiempo, col) in enumerate(pasos):
        x = 0.5 + i * (w + gap)
        caja(ax, x, 9, w, 17, txt, col, fs=6.0)
        if tiempo:
            ax.text(x + w / 2, 5.2, tiempo, ha="center", va="center", fontsize=6.4, fontweight="bold", color=col[1])
        if i:
            flecha(ax, (x - gap, 17.5), (x, 17.5))
    ax.text(50, 0.4, "Tiempos del E2E-9: plan 2,6 s · consultas 0,08 s · explicación 1,6 s · total 4,3 s (una máquina)",
            ha="center", fontsize=6.2, color="#444444")
    fig.savefig(SALIDA / "flujo.png", dpi=220, bbox_inches="tight", facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    SALIDA.mkdir(exist_ok=True)
    arquitectura()
    flujo()
    print("figuras escritas en", SALIDA)
