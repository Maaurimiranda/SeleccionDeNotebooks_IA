"""Arma el informe final en PDF a partir de las secciones .md de docs/informe/.

Uso (desde la raíz del repo):  python docs/informe/armar_pdf.py
Escribe:
  docs/informe/Grupo_2_PG3_Informe.pdf         informe completo: portada, índice, las 12 secciones y anexos
  docs/presentacion/resumen_ejecutivo.pdf      la sección 2 en una página (ítem l de la consigna §4)

Herramientas: mistune (Markdown a HTML) y PyMuPDF (HTML a PDF con fitz.Story). No son parte del asistente
ni están en requirements.txt: solo sirven para armar el PDF. Las figuras salen de docs/informe/figuras.py.
Si MuPDF recorta algo (una columna que no entra, por ejemplo), el script se detiene y lo dice.
"""
import html as html_lib
import io
import re
import unicodedata
from pathlib import Path

import fitz
import mistune

INFORME = Path(__file__).resolve().parent
DOCS = INFORME.parent
PDF_INFORME = INFORME / "Grupo_2_PG3_Informe.pdf"
PDF_RESUMEN = DOCS / "presentacion" / "resumen_ejecutivo.pdf"

A4 = fitz.paper_rect("a4")
CUERPO = A4 + (62, 62, -62, -66)
AZUL = (0.12, 0.23, 0.37)
GRIS = (0.4, 0.4, 0.4)
CABECERA = "Asistente experto para la selección de notebooks · Grupo 2 · UTN FRM"

# Cada entrada es una sección del informe: los archivos que la forman, en orden.
SECCIONES = [
    ["02_resumen.md"],
    ["03_problema.md"],
    ["04_arquitectura.md"],
    ["05_base_conocimiento.md", "05_sm1.md", "05_sm2.md", "05_sm3.md", "05_sm4.md"],
    ["06_integracion_llm.md"],
    ["07_casos_de_uso.md"],
    ["08_pruebas.md"],
    ["09_evaluacion.md"],
    ["10_trazabilidad.md"],
    ["11_reflexion_metodologia.md", "11_conclusiones.md"],
    ["12_referencias.md"],
]

NOTA_CORRECCIONES = (
    "*Este registro se redactó el 10/11/2026 y algunos pasajes quedaron desactualizados: dice que SM4, el explicador "
    "y el verificador siguen como stub, que los E2E no se ejecutaron y cita la medición del router de ese día (24 de 25). "
    "Ya están hechos. Las cifras vigentes (router 28 de 31 y 30 de 31, los 7 E2E) están en las secciones 6 y 8.*\n\n")

# Anexos: (archivo relativo a docs/, nota previa). El que no existe se saltea.
ANEXOS = [
    ("CORRECCIONES.md", NOTA_CORRECCIONES),
    ("MANUAL_DE_USO.md", ""),
    ("pruebas/casos_de_uso.md", ""),
    ("pruebas/funcionales.md", ""),
]


def css(base=9.4):
    return f"""
body {{ font-family: sans-serif; font-size: {base}pt; line-height: 1.28; color: #1b1b1b; }}
h1 {{ font-size: 18pt; color: #1F3A5F; margin: 0 0 8pt 0; padding-bottom: 3pt; border-bottom: 1.5pt solid #1F3A5F; }}
h2 {{ font-size: 12.5pt; color: #1F3A5F; margin: 12pt 0 4pt 0; }}
h3 {{ font-size: 10.4pt; color: #2d4f7c; margin: 9pt 0 3pt 0; }}
p {{ margin: 0 0 5pt 0; }}
ul, ol {{ margin: 0 0 5pt 0; }}
li {{ margin: 0 0 2pt 0; }}
table {{ border-collapse: collapse; width: 100%; margin: 4pt 0 7pt 0; }}
th {{ color: #1F3A5F; font-size: {base - 1.1}pt; text-align: left; border: 0.6pt solid #b8c0cc; border-bottom: 1.4pt solid #1F3A5F; padding: 2.5pt 3.5pt; }}
td {{ font-size: {base - 1.1}pt; border: 0.6pt solid #b8c0cc; padding: 2.5pt 3.5pt; vertical-align: top; }}
code {{ font-family: monospace; font-size: {base - 1.2}pt; background-color: #EEF1F5; }}
pre {{ font-family: monospace; font-size: 6.9pt; white-space: pre-wrap; padding: 4pt; margin: 3pt 0 6pt 0; border: 0.5pt solid #c9d0d9; border-left: 2.5pt solid #1F3A5F; }}
pre code {{ background-color: #ffffff; font-size: 6.9pt; }}
blockquote {{ margin: 3pt 0 6pt 8pt; padding-left: 7pt; border-left: 2pt solid #9AA5B1; color: #333333; }}
img {{ margin: 3pt 0; }}
.anexo td, .anexo th {{ font-size: 7.4pt; padding: 2pt 3pt; }}
.portada p {{ text-align: center; margin: 0 0 9pt 0; }}
.portada h1 {{ text-align: center; font-size: 25pt; border-bottom: none; margin: 40pt 24pt 10pt 24pt; }}
.portada h2 {{ text-align: center; font-size: 17pt; color: #2d4f7c; margin: 10pt 0 6pt 0; }}
.portada table {{ width: 80%; margin: 26pt 0 22pt 40pt; }}
.portada td, .portada th {{ font-size: 10.5pt; padding: 5pt 7pt; }}
.toc td {{ border: none; padding: 1.2pt 3pt; font-size: 9.2pt; }}
.toc1 td {{ font-weight: bold; padding-top: 5pt; }}
"""
# Nota: no se usa background-color en tablas ni en <pre>. MuPDF repite esos fondos como tiras en las páginas siguientes.


def tablas_anchas_a_fichas(md: str, min_cols: int = 8) -> str:
    """Una tabla de 8 o más columnas no entra en una página vertical y MuPDF recorta las últimas. Cada fila pasa a
    una ficha: título con las tres primeras columnas y la última, y una viñeta por cada columna del medio."""
    lineas, salida, i = md.split("\n"), [], 0
    celdas = lambda l: [c.strip() for c in re.split(r"(?<!\\)\|", l.strip())[1:-1]]
    while i < len(lineas):
        if lineas[i].startswith("|") and i + 1 < len(lineas) and re.match(r"^\|(\s*:?-+:?\s*\|)+\s*$", lineas[i + 1]) \
                and len(celdas(lineas[i])) >= min_cols:
            cab, i = celdas(lineas[i]), i + 2
            while i < len(lineas) and lineas[i].startswith("|"):
                c = celdas(lineas[i])
                salida.append("**" + " · ".join(c[:3] + [c[-1]]) + "**\n")
                salida += [f"- **{cab[k]}:** {c[k]}" for k in range(3, len(cab) - 1)]
                salida.append("")
                i += 1
        else:
            salida.append(lineas[i])
            i += 1
    return "\n".join(salida)


def md_a_html(md: str, anexo: bool = False) -> str:
    # Los vínculos relativos apuntan a archivos del repo y no sirven en un PDF: se deja solo el texto.
    md = re.sub(r"(?<!!)\[([^\]]+)\]\((?!https?://)[^)]*\)", r"\1", md)
    if anexo:
        md = tablas_anchas_a_fichas(md)
    html = mistune.create_markdown(plugins=["table"])(md)
    html = html.replace("<img ", '<img width="470" ')
    if anexo:
        # Las rutas largas no se parten solas: se les da dónde cortar.
        html = re.sub(r"(<code>)([^<]*)(</code>)",
                      lambda m: m.group(1) + re.sub(r"([/_.-])", r"\1<wbr>", m.group(2)) + m.group(3), html)
        html = f'<div class="anexo">{html}</div>'
    return html


def render(html: str, estilo: str, where: fitz.Rect, mediabox=A4):
    """HTML a PDF en memoria. Devuelve (documento, titulos), con los títulos como (nivel, texto, página 0-based)."""
    story = fitz.Story(html=html, user_css=estilo, archive=fitz.Archive(str(INFORME)))
    buf = io.BytesIO()
    w = fitz.DocumentWriter(buf)
    titulos, pno, mas = [], 0, 1
    while mas:
        dev = w.begin_page(mediabox)
        mas, _ = story.place(where)
        story.element_positions(
            lambda e: titulos.append((e.heading, e.text, e.pno)) if e.heading and e.open_close & 1 else None,
            {"pno": pno})
        story.draw(dev)
        w.end_page()
        pno += 1
    w.close()
    # El texto que informa Story pierde el espacio donde el título cortó la línea: se usa el del HTML.
    textos = [html_lib.unescape(re.sub(r"<[^>]+>", "", t)) for t, _ in re.findall(r"<h[1-6]>(.*?)</h([1-6])>", html, re.S)]
    if len(textos) == len(titulos):
        titulos = [(n, t, p) for (n, _, p), t in zip(titulos, textos)]
    return fitz.open("pdf", buf.getvalue()), titulos


FIGURA = re.compile(r"(<h[23]>(?:(?!</h).)*</h[23]>\s*)?(<p>)(<img )", re.S)


def render_seguro(html: str, estilo: str, where: fitz.Rect):
    """Como render, pero si una figura no entra en el resto de la página y MuPDF la aplasta, la pasa a la página
    siguiente (junto con su título, si lo tiene) en lugar de dejarla ilegible."""
    for _ in range(6):
        doc, titulos = render(html, estilo, where)
        info = [i for pagina in doc for i in pagina.get_image_info()]
        coincidencias = list(FIGURA.finditer(html))
        # MuPDF achica la figura entera (con su proporción) para que entre: se nota porque queda más angosta que 470 pt
        k = next((k for k, i in enumerate(info) if k < len(coincidencias) and i["bbox"][2] - i["bbox"][0] < 0.9 * 470), None)
        if k is None:
            return doc, titulos
        m = coincidencias[k]
        salto = ' style="page-break-before:always"'
        if m.group(1):
            html = html[:m.start()] + m.group(1).replace(">", f"{salto}>", 1) + m.group(2) + m.group(3) + html[m.end():]
        else:
            html = html[:m.start()] + "<p" + salto + ">" + m.group(3) + html[m.end():]
    raise SystemExit("no se pudo acomodar una figura")


def verificar_texto(doc: fitz.Document, html: str, nombre: str):
    """MuPDF recorta en silencio lo que no entra (por ejemplo, las últimas columnas de una tabla ancha).
    Se comprueba que cada palabra del HTML (de 5 letras o más) esté en el texto del PDF."""
    def palabras(t):
        # NFKC deshace las ligaduras («fi», «fl») que el PDF guarda como un solo carácter
        return set(re.findall(r"[a-z0-9áéíóúñü]{5,}", unicodedata.normalize("NFKC", html_lib.unescape(t)).lower()))
    esperadas = palabras(re.sub(r"<[^>]+>", " ", html))
    halladas = palabras(" ".join(pagina.get_text() for pagina in doc))
    faltan = sorted(esperadas - halladas)
    if faltan:
        raise SystemExit(f"{nombre}: faltan {len(faltan)} palabras en el PDF (¿una tabla ancha recortada?): {faltan[:12]}")


def en_una_pagina(html: str, where: fitz.Rect, tamanos=(9.4, 9.2, 9.0, 8.8, 8.6, 8.4, 8.2, 8.0, 7.8)):
    for t in tamanos:
        doc, titulos = render(html, css(t), where)
        if doc.page_count == 1:
            return doc, titulos, t
    raise SystemExit("el texto no entra en una página ni con la letra más chica")


def leer(ruta: Path) -> str:
    return ruta.read_text(encoding="utf-8")


def seccion_md(archivos: list[str]) -> str:
    """Une los archivos de una sección. Los que siguen al primero son subsecciones: su título baja un nivel."""
    partes = []
    for i, nombre in enumerate(archivos):
        txt = leer(INFORME / nombre).strip()
        if i:
            txt = re.sub(r"^# ", "## ", txt, count=1)
        partes.append(txt)
    return "\n\n".join(partes)


def pie(doc: fitz.Document):
    """Cabecera y número de página en todas las páginas menos la portada."""
    for i, page in enumerate(doc):
        if i == 0:
            continue
        w, h = page.rect.width, page.rect.height
        page.draw_line((62, 44), (w - 62, 44), color=(0.7, 0.72, 0.76), width=0.5)
        page.insert_text((62, 38), CABECERA, fontsize=7.5, fontname="helv", color=GRIS)
        n = str(i + 1)
        page.insert_text(((w - fitz.get_text_length(n, "helv", 8.5)) / 2, h - 30), n, fontsize=8.5, fontname="helv", color=GRIS)


def armar_informe():
    estilo = css()

    # Portada
    portada, _ = render(f'<div class="portada"><div style="height:120pt"></div>{md_a_html(leer(INFORME / "01_portada.md"))}</div>',
                        estilo, A4 + (62, 62, -62, -62))
    if portada.page_count != 1:
        raise SystemExit("la portada no entra en una página")

    # Secciones y anexos: cada una arranca en página nueva
    bloques = []  # (documento, titulos, es_anexo)
    for archivos in SECCIONES:
        html = md_a_html(seccion_md(archivos))
        if archivos[0] == "02_resumen.md":
            doc, tit, _ = en_una_pagina(html, CUERPO)
        else:
            doc, tit = render_seguro(html, estilo, CUERPO)
        verificar_texto(doc, html, archivos[0])
        bloques.append((doc, tit, False))
    letra = iter("ABCDEFG")
    for rel, nota in ANEXOS:
        ruta = DOCS / rel
        if not ruta.exists():
            continue
        txt = leer(ruta).strip()
        txt = re.sub(r"^# ", f"# Anexo {next(letra)} · ", txt, count=1)
        txt = txt.replace(" · Asistente experto para la selección de notebooks", "", 1)
        primera, _, resto = txt.partition("\n")
        html = md_a_html(f"{primera}\n\n{nota}{resto}", anexo=True)
        doc, tit = render_seguro(html, estilo, CUERPO)
        verificar_texto(doc, html, rel)
        bloques.append((doc, tit, True))

    # Índice: se arma dos veces porque el largo del índice corre los números de página
    def indice(desplazamiento: int):
        filas, pagina = ['<tr class="toc1"><td>1. Portada institucional</td><td style="text-align:right;width:28pt">1</td></tr>'], desplazamiento
        for doc, tit, es_anexo in bloques:
            for nivel, texto, p in tit:
                if nivel == 1 or (nivel == 2 and not es_anexo):
                    cls = "toc1" if nivel == 1 else "toc2"
                    sangria = "" if nivel == 1 else ' style="padding-left:16pt"'
                    filas.append(f'<tr class="{cls}"><td{sangria}>{mistune.escape(texto)}</td>'
                                 f'<td style="text-align:right;width:28pt">{pagina + p + 1}</td></tr>')
            pagina += doc.page_count
        return '<div class="toc"><h1>Índice</h1><table>' + "".join(filas) + "</table></div>"

    idx_doc, _ = render(indice(1), estilo, CUERPO)
    idx_doc, _ = render(indice(1 + idx_doc.page_count), estilo, CUERPO)

    # Ensamblado
    out = fitz.open()
    out.insert_pdf(portada)
    out.insert_pdf(idx_doc)
    marcadores = [[1, "Portada", 1], [1, "Índice", 2]]
    pagina = 1 + idx_doc.page_count
    for doc, tit, es_anexo in bloques:
        out.insert_pdf(doc)
        for nivel, texto, p in tit:
            if nivel == 1 or (nivel == 2 and not es_anexo):
                marcadores.append([nivel, texto[:90], pagina + p + 1])
        pagina += doc.page_count
    out.set_toc(marcadores)
    out.set_metadata({"title": "Asistente experto para la selección de notebooks · Informe ejecutivo final",
                      "author": "Grupo 2 · Comisión 5K09 · UTN FRM", "subject": "PG3 · Cátedra de Inteligencia Artificial"})
    pie(out)
    # Franja de color en la portada
    p0 = out[0]
    p0.draw_rect(fitz.Rect(0, 0, A4.width, 16), fill=AZUL, color=None)
    p0.draw_rect(fitz.Rect(0, A4.height - 16, A4.width, A4.height), fill=AZUL, color=None)
    out.save(PDF_INFORME, garbage=3, deflate=True)
    print(f"{PDF_INFORME}: {out.page_count} páginas")


def armar_resumen():
    where = A4 + (44, 52, -44, -44)
    html = md_a_html(leer(INFORME / "02_resumen.md"))
    doc, _, tam = en_una_pagina(html, where, tamanos=(9.2, 9.0, 8.8, 8.6, 8.4, 8.2, 8.0, 7.8, 7.6))
    verificar_texto(doc, html, "resumen_ejecutivo")
    page = doc[0]
    page.draw_rect(fitz.Rect(0, 0, A4.width, 14), fill=AZUL, color=None)
    page.insert_text((44, 32), CABECERA, fontsize=7.5, fontname="helv", color=GRIS)
    pie_txt = "Resumen ejecutivo · Informe final PG3 · 13/11/2026"
    page.insert_text(((A4.width - fitz.get_text_length(pie_txt, "helv", 7.5)) / 2, 826), pie_txt, fontsize=7.5,
                     fontname="helv", color=GRIS)
    doc.set_metadata({"title": "Resumen ejecutivo · Asistente experto para la selección de notebooks",
                      "author": "Grupo 2 · Comisión 5K09 · UTN FRM"})
    PDF_RESUMEN.parent.mkdir(exist_ok=True)
    doc.save(PDF_RESUMEN, garbage=3, deflate=True)
    print(f"{PDF_RESUMEN}: 1 página, letra {tam} pt")


if __name__ == "__main__":
    armar_informe()
    armar_resumen()
