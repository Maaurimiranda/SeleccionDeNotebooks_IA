"""API única (D-07 §11): POST /consultar y GET /salud. Capa de controlador del sistema.

Documentación OpenAPI en /docs. Lanzar con:  uvicorn asistente.api:app
Interfaz web en /ui: un HTML estático (asistente/web/index.html) que llama a los mismos POST /consultar y
GET /salud. No agrega endpoints a la API: sus rutas no aparecen en Swagger.
"""
import json
from pathlib import Path
from typing import Any, Literal

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from asistente import config

DESCRIPCION = (
    "Asistente experto para elegir notebooks (Grupo 2, UTN FRM, PG3). El LLM interpreta la consulta y "
    "redacta; las cifras, reglas y estados salen de Neo4j. Cada respuesta trae su traza completa. "
    "Hay una interfaz web en [/ui](/ui) que usa este mismo endpoint.")

RAIZ = Path(__file__).resolve().parent.parent
PAGINA_UI = Path(__file__).resolve().parent / "web" / "index.html"
TRAZA_EJEMPLO = RAIZ / "datos" / "traza_ejemplo.jsonl"


class ConsultaEntrada(BaseModel):
    texto: str = Field(
        ..., description=f"Consulta en lenguaje natural. Máximo {config.MAX_CARACTERES} caracteres: si se pasa, "
                         "la respuesta es una aclaración (origen_respuesta = 'validacion'), sin recortar.",
        examples=["¿Por qué la G quedó indeterminada y qué riesgo de RAM tiene en req_01?"])
    requerimiento_id: str | None = Field(
        None, description="Pedido de la sesión (req_01, req_02...). Si el texto nombra otro, manda el del texto.",
        examples=["req_01"])


class ConsultaSalida(BaseModel):
    respuesta: str = Field(..., description="Texto para el asesor.")
    requerimiento_id: str | None = Field(None, description="Pedido sobre el que se respondió.")
    submodulos_consultados: list[str] = Field(default_factory=list, examples=[["SM1", "SM2", "SM4"]])
    origen_respuesta: Literal["llm", "plantilla_fija", "validacion", "fuera_de_alcance", "error"] = Field(
        ..., description="De dónde salió la respuesta (D-07 §9).")
    intento: int = Field(0, description="Número de intento del explicador (0 si no se llegó a explicar).")
    traza: dict[str, Any] = Field(..., description="Plan, validación, consultas Cypher con filas, evidencia, "
                                                   "intentos y duración de cada paso.")


class SaludSalida(BaseModel):
    ok: bool = Field(..., description="True si Neo4j y Ollama (con el modelo) están disponibles.")
    neo4j: dict[str, Any]
    ollama: dict[str, Any]
    modelo: str | None = Field(None, examples=["qwen2.5:3b"])


def crear_app(orquestador=None) -> FastAPI:
    app = FastAPI(title="Asistente de selección de notebooks · Grupo 2", version="1.0", description=DESCRIPCION)
    estado: dict = {"orq": orquestador}

    def orq():
        if estado["orq"] is None:
            from asistente.orquestador import Orquestador
            estado["orq"] = Orquestador()
        return estado["orq"]

    @app.post("/consultar", response_model=ConsultaSalida, summary="Hacer una consulta al asistente")
    def consultar(entrada: ConsultaEntrada) -> ConsultaSalida:
        return ConsultaSalida(**orq().consultar(entrada.texto, entrada.requerimiento_id, sesion={}))

    @app.get("/salud", response_model=SaludSalida, summary="Estado de Neo4j, de Ollama y del modelo")
    def salud() -> SaludSalida:
        return SaludSalida(**orq().salud())

    # Interfaz web: fuera del esquema OpenAPI, así Swagger (/docs) queda igual.
    @app.get("/ui", include_in_schema=False)
    def ui() -> FileResponse:
        return FileResponse(PAGINA_UI, media_type="text/html")

    @app.get("/ui/ejemplo", include_in_schema=False)
    def ui_ejemplo() -> dict:
        """Última traza grabada en datos/traza_ejemplo.jsonl, con la forma de POST /consultar (respaldo para la defensa)."""
        if not TRAZA_EJEMPLO.exists():
            raise HTTPException(404, "No está datos/traza_ejemplo.jsonl")
        lineas = [l for l in TRAZA_EJEMPLO.read_text(encoding="utf-8").splitlines() if l.strip()]
        t = json.loads(lineas[-1])
        submodulos = list(dict.fromkeys(c["sm"] for c in t.get("consultas", []) if c.get("sm")))
        return {"respuesta": t.get("respuesta") or "", "requerimiento_id": (t.get("plan") or {}).get("requerimiento_id"),
                "submodulos_consultados": submodulos, "origen_respuesta": t.get("origen_respuesta") or "error",
                "intento": len(t.get("intentos") or []), "traza": t}

    return app


app = crear_app()
