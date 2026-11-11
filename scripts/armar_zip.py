"""PG3-17: arma Grupo_2_PG3_ProyectoFinal.zip con los ítems a-l de la consigna §4.

    python -m scripts.armar_zip            # arma dist/Grupo_2_PG3_ProyectoFinal.zip
    python -m scripts.armar_zip --verificar   # solo busca credenciales y lista lo que falta

Una carpeta por ítem y un LEEME.md que dice qué archivos hay en cada una y qué falta. Excluye .env, .venv, trazas,
__pycache__, .git y .claude. Si encuentra una credencial, no arma el ZIP.
"""
import re
import sys
import zipfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SALIDA = RAIZ / "dist" / "Grupo_2_PG3_ProyectoFinal.zip"
EXCLUIDOS = {".env", ".venv", "venv", "trazas", "__pycache__", ".git", ".claude", "dist", ".pytest_cache"}

# ítem -> (carpeta, descripción, [rutas o globs relativos a la raíz])
ITEMS = [
    ("a", "a_informe", "Informe ejecutivo final (PDF) y sus secciones", ["docs/informe", "docs/Informe*.pdf"]),
    ("b", "b_diagramas", "Diagramas", ["docs/diagramas", "docs/informe/diagramas"]),
    ("c", "c_casos_de_prueba", "Casos de prueba, E2E y pruebas funcionales", ["docs/pruebas", "tests"]),
    ("d", "d_manual_de_uso", "Manual de uso", ["docs/MANUAL_DE_USO.md", "README.md"]),
    ("e", "e_codigo_fuente", "Código fuente y requirements.txt", ["asistente", "scripts", "prompts", "requirements.txt"]),
    ("f", "f_scripts_cypher", "Scripts Cypher", ["cypher", "docs/cypher"]),
    ("g", "g_configuracion", "Archivos de configuración", [".env.example"]),
    ("h", "h_recursos", "Recursos complementarios (arquitectura, decisiones, contextos, notas de sesión)",
     ["docs/ARQUITECTURA.md", "docs/RESTRICCIONES.md", "docs/INCONSISTENCIAS_CONTEXTOS.md", "docs/CORRECCIONES.md",
      "docs/contexto", "docs/sesiones", "docs/fuentes", "docs/plan", "CLAUDE.md"]),
    ("i", "i_exportacion_neo4j", "Exportación de Neo4j", ["datos/export"]),
    ("j", "j_datos_de_ejemplo", "Datos de ejemplo", ["datos/consultas_ejemplo.csv", "datos/salida_pi2.csv", "datos/traza_ejemplo.jsonl"]),
    ("k", "k_video", "Video demostrativo o presentación", ["docs/video"]),
    ("l", "l_infografia", "Infografía o resumen ejecutivo", ["docs/infografia", "docs/presentacion", "docs/informe/02_resumen*"]),
]

_PLACEHOLDER = re.compile(r"^(?:|…|\.\.\.|<[^>]*>|tu_[\w-]*|cambiar\w*|changeme|xxx+|\$\{?\w+\}?)$", re.IGNORECASE)
_CLAVE = re.compile(r"(?im)^[ 	]*(?:export[ 	]+)?\w*(?:PASSWORD|PASSWD|SECRET|TOKEN|API_KEY)\w*[ 	]*=[ 	]*(\S*)[ 	]*$")
_AURA = re.compile(r"neo4j\+s://[a-z0-9]{8}", re.IGNORECASE)
_TEXTO = {".md", ".txt", ".csv", ".json", ".jsonl", ".cypher", ".example", ".env", ".toml", ".yml", ".yaml", ".cfg", ".ini"}


def _archivos(carpeta: Path):
    for p in sorted(carpeta.rglob("*")):
        if p.is_file() and not (EXCLUIDOS & set(p.relative_to(RAIZ).parts)) and p.suffix != ".pyc":
            yield p


def _expandir(patron: str) -> list[Path]:
    base = RAIZ / patron
    if base.is_dir():
        return list(_archivos(base))
    if base.is_file():
        return [base]
    return [p for p in sorted(RAIZ.glob(patron)) if p.is_file()]


def credenciales(rutas: list[Path]) -> list[str]:
    """Líneas con una contraseña o una URI de Aura que no sean un placeholder."""
    halladas = []
    for p in rutas:
        if p.suffix not in _TEXTO and p.name != ".env.example":
            continue
        try:
            texto = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for m in _CLAVE.finditer(texto):
            if not _PLACEHOLDER.match(m.group(1).strip("'\"")):
                halladas.append(f"{p.relative_to(RAIZ)}: {m.group(0).strip()[:40]}")
        for m in _AURA.finditer(texto):
            halladas.append(f"{p.relative_to(RAIZ)}: URI de Aura {m.group(0)}…")
    return halladas


def _clave_del_entorno() -> str:
    """La contraseña real (del entorno o de .env), para buscarla tal cual en todo lo que va al ZIP."""
    import os
    clave = os.getenv("NEO4J_PASSWORD", "")
    env = RAIZ / ".env"
    if not clave and env.is_file():
        m = re.search(r"(?m)^\s*NEO4J_PASSWORD\s*=\s*(\S+)", env.read_text(encoding="utf-8", errors="ignore"))
        clave = m.group(1).strip("'\"") if m else ""
    return clave if len(clave) >= 4 else ""


def contienen_la_clave(rutas: list[Path]) -> list[str]:
    clave = _clave_del_entorno().encode()
    return [str(p.relative_to(RAIZ)) for p in rutas if clave and clave in p.read_bytes()] if clave else []


def main(argv: list[str]) -> int:
    contenido: dict[str, list[Path]] = {}
    for letra, carpeta, _, patrones in ITEMS:
        vistos: dict[Path, None] = {}
        for patron in patrones:
            for p in _expandir(patron):
                vistos[p] = None
        contenido[letra] = list(vistos)
    todos = [p for ps in contenido.values() for p in ps]
    malas = credenciales(todos) + [f"{r}: contiene la contraseña de NEO4J_PASSWORD" for r in contienen_la_clave(todos)]
    if malas:
        print("Se encontraron posibles credenciales; no se arma el ZIP:\n  " + "\n  ".join(malas))
        return 1
    faltan = [f"{letra}) {desc}" for letra, _, desc, _ in ITEMS if not contenido[letra]]
    print(f"{len(todos)} archivos en {sum(bool(v) for v in contenido.values())} de {len(ITEMS)} ítems. Sin credenciales.")
    if faltan:
        print("Faltan (se marcan «pendiente» en el LEEME.md):\n  " + "\n  ".join(faltan))
    if "--verificar" in argv:
        return 0
    leeme = ["# Grupo 2 · PG3 · Asistente experto para la selección de notebooks", "",
             "Proyecto final de PG3 (UTN FRM). Este ZIP tiene una carpeta por ítem de la consigna §4. "
             "Para reproducirlo: `e_codigo_fuente/` y `d_manual_de_uso/` (cómo instalarlo y correrlo), `f_scripts_cypher/` (cargar el grafo) y `g_configuracion/` (variables de entorno).", "",
             "| Ítem | Carpeta | Contenido | Estado |", "| --- | --- | --- | --- |"]
    for letra, carpeta, desc, _ in ITEMS:
        n = len(contenido[letra])
        leeme.append(f"| {letra}) | `{carpeta}/` | {desc} | {f'{n} archivos' if n else '**pendiente** (ver el enlace o el aviso del grupo)'} |")
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(SALIDA, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("LEEME.md", "\n".join(leeme) + "\n")
        for letra, carpeta, _, patrones in ITEMS:
            for p in contenido[letra]:
                z.write(p, f"{carpeta}/{p.relative_to(RAIZ).as_posix()}")
    print(f"Listo: {SALIDA.relative_to(RAIZ)} ({SALIDA.stat().st_size / 1e6:.1f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
