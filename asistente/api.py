"""API única (D-07 §11): POST /consultar y GET /salud. Capa de controlador del sistema.

Documentación OpenAPI en /docs. Lanzar con:  uvicorn asistente.api:app
Interfaz web en /ui: un HTML estático (asistente/web/index.html) que llama a los mismos POST /consultar y
GET /salud. No agrega endpoints a la API: sus rutas no aparecen en Swagger.
"""
import json
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Literal

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from asistente import config

DESCRIPCION = (
    "Asistente experto para elegir notebooks (Grupo 2, UTN FRM, PG3). El LLM interpreta la consulta y "
    "redacta; las cifras, reglas y estados salen de Neo4j. Cada respuesta trae su traza completa. "
    "Una consulta libre («quiero programar y jugar, tengo 900 USD») registra un pedido nuevo: Ollama extrae "
    "usos, juegos y presupuesto, y Neo4j corre las reglas y el difuso para ese pedido. "
    "Hay una interfaz web en [/ui](/ui) que usa este mismo endpoint.")

RAIZ = Path(__file__).resolve().parent.parent
PAGINA_UI = Path(__file__).resolve().parent / "web" / "index.html"
TRAZA_EJEMPLO = RAIZ / "datos" / "traza_ejemplo.jsonl"


class ConsultaEntrada(BaseModel):
    texto: str = Field(
        ..., description=f"Consulta en lenguaje natural. Máximo {config.MAX_CARACTERES} caracteres: si se pasa, "
                         "la respuesta es una aclaración (origen_respuesta = 'validacion'), sin recortar.",
        examples=["Quiero una notebook para programar y usar Docker, y a veces jugar al Fortnite. Tengo 900 dólares."])
    requerimiento_id: str | None = Field(
        None, description="Pedido de la sesión (req_01, req_02...). Si el texto nombra otro, manda el del texto. "
                          "Vacío y con una consulta que describe una necesidad, se registra un pedido nuevo.",
        examples=[None])
    sesion_id: str | None = Field(
        None, description="Conversación: devolvé el `sesion_id` de la respuesta anterior para seguir con el mismo "
                          "pedido (contestar una repregunta o preguntar algo más). Vacío: conversación nueva.")


class ConsultaSalida(BaseModel):
    respuesta: str = Field(..., description="Texto para el asesor.")
    requerimiento_id: str | None = Field(None, description="Pedido sobre el que se respondió.")
    submodulos_consultados: list[str] = Field(default_factory=list, examples=[["SM1", "SM2", "SM4"]])
    origen_respuesta: Literal["llm", "plantilla_fija", "validacion", "fuera_de_alcance", "error"] = Field(
        ..., description="De dónde salió la respuesta (D-07 §9).")
    intento: int = Field(0, description="Número de intento del explicador (0 si no se llegó a explicar).")
    traza: dict[str, Any] = Field(..., description="Plan, validación, consultas Cypher con filas, evidencia, "
                                                   "intentos y duración de cada paso.")
    sesion_id: str = Field(..., description="Identificador de la conversación, para la próxima consulta.")
    pedido_nuevo: bool = Field(False, description="True si esta consulta registró un pedido nuevo en Neo4j.")
    repregunta: str | None = Field(None, description="Lo que falta para registrar el pedido (presupuesto, usos u "
                                                     "horas). Se contesta en la próxima consulta con el mismo sesion_id.")
    pedido: dict[str, Any] | None = Field(None, description="Lo que se entendió del pedido nuevo o de la aclaración: "
                                                            "presupuesto, prioridad y actividades con su cita.")


class SaludSalida(BaseModel):
    ok: bool = Field(..., description="True si Neo4j y Ollama (con el modelo) están disponibles.")
    neo4j: dict[str, Any]
    ollama: dict[str, Any]
    modelo: str | None = Field(None, examples=["qwen2.5:3b"])


class Sesiones:
    """Conversaciones en memoria (pedido de la sesión, repregunta en curso). Vencen tras `vida_s` sin uso."""

    def __init__(self, vida_s: int = 2 * 3600, maximo: int = 1000):
        self.vida_s, self.maximo = vida_s, maximo
        self._datos: dict[str, tuple[float, dict]] = {}
        self._candado = threading.Lock()

    def obtener(self, sesion_id: str | None) -> tuple[str, dict]:
        ahora = time.time()
        with self._candado:
            for k in [k for k, (t, _) in self._datos.items() if ahora - t > self.vida_s]:
                del self._datos[k]
            if sesion_id and sesion_id in self._datos:
                sesion = self._datos[sesion_id][1]
            else:
                sesion_id, sesion = sesion_id or uuid.uuid4().hex, {}
                if len(self._datos) >= self.maximo:
                    del self._datos[min(self._datos, key=lambda k: self._datos[k][0])]
            self._datos[sesion_id] = (ahora, sesion)
            return sesion_id, sesion


def crear_app(orquestador=None) -> FastAPI:
    app = FastAPI(title="Asistente de selección de notebooks · Grupo 2", version="1.0", description=DESCRIPCION)
    estado: dict = {"orq": orquestador}
    sesiones = Sesiones()

    def orq():
        if estado["orq"] is None:
            from asistente.orquestador import Orquestador
            estado["orq"] = Orquestador()
        return estado["orq"]

    @app.post("/consultar", response_model=ConsultaSalida, summary="Hacer una consulta al asistente")
    def consultar(entrada: ConsultaEntrada) -> ConsultaSalida:
        sesion_id, sesion = sesiones.obtener(entrada.sesion_id)
        return ConsultaSalida(**orq().consultar(entrada.texto, entrada.requerimiento_id, sesion=sesion),
                              sesion_id=sesion_id)

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
                "intento": len(t.get("intentos") or []), "traza": t, "sesion_id": "ejemplo",
                "pedido_nuevo": bool(t.get("escritura")), "repregunta": t.get("repregunta"), "pedido": None}

    return app


app = crear_app()
