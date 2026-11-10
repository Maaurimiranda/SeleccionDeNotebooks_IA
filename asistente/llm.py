"""Cliente único del LLM (D-05): LangChain + Ollama, temperatura 0.

- `json`: cadena ChatPromptTemplate | ChatOllama.with_structured_output(esquema),
  que devuelve un dict ya validado contra el esquema (salida estructurada de Ollama).
- `texto`: cadena ChatPromptTemplate | ChatOllama | StrOutputParser.
- `salud`: GET /api/tags con requests.

Prompts como plantilla: si se pasa `variables`, `sistema` se trata como plantilla
de ChatPromptTemplate ({variable}; las llaves literales se escriben {{ y }}).
Sin `variables`, el texto va tal cual (no se interpretan llaves).
Este archivo y el orquestador son los únicos que importan LangChain.
"""
import requests
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama

from asistente import config
from asistente.contrato import ErrorLLM


def _prompt(sistema: str, usuario: str, variables: dict | None):
    """Devuelve (plantilla, entradas) para invocar la cadena."""
    if variables is None:
        plantilla = ChatPromptTemplate.from_messages([("system", "{__sistema}"), ("human", "{__usuario}")])
        return plantilla, {"__sistema": sistema, "__usuario": usuario}
    plantilla = ChatPromptTemplate.from_messages([("system", sistema), ("human", "{__usuario}")])
    return plantilla, {**variables, "__usuario": usuario}


class LLM:
    def __init__(self, modelo: str | None = None, url: str | None = None, timeout: float = 120):
        self.modelo = modelo or config.OLLAMA_MODEL
        self.url = url or config.OLLAMA_URL
        self.timeout = timeout

    def _chat(self) -> ChatOllama:
        # Un solo cliente reutilizado: evita abrir una conexión nueva (y dejarla colgada) en cada llamada.
        if getattr(self, "_cliente", None) is None:
            self._cliente = ChatOllama(model=self.modelo, base_url=self.url, temperature=0,
                                       client_kwargs={"timeout": self.timeout})
        return self._cliente

    def json(self, sistema: str, usuario: str, esquema: dict, variables: dict | None = None) -> dict:
        plantilla, entradas = _prompt(sistema, usuario, variables)
        cadena = plantilla | self._chat().with_structured_output(esquema, method="json_schema")
        try:
            salida = cadena.invoke(entradas)
        except Exception as e:  # conexión, modelo inexistente, JSON inválido...
            raise ErrorLLM(f"El LLM no devolvió un JSON válido ({type(e).__name__}): {e}") from e
        if not isinstance(salida, dict):
            raise ErrorLLM(f"El LLM devolvió {type(salida).__name__} en lugar de un objeto JSON")
        return salida

    def texto(self, sistema: str, usuario: str, variables: dict | None = None) -> str:
        plantilla, entradas = _prompt(sistema, usuario, variables)
        cadena = plantilla | self._chat() | StrOutputParser()
        try:
            return cadena.invoke(entradas).strip()
        except Exception as e:
            raise ErrorLLM(f"El LLM no respondió ({type(e).__name__}): {e}") from e

    def salud(self) -> dict:
        try:
            r = requests.get(f"{self.url}/api/tags", timeout=5)
            r.raise_for_status()
            modelos = [m.get("name") for m in r.json().get("models", [])]
            return {"ok": self.modelo in modelos, "url": self.url, "modelo": self.modelo,
                    "modelo_disponible": self.modelo in modelos}
        except Exception as e:
            return {"ok": False, "url": self.url, "modelo": self.modelo, "error": f"{type(e).__name__}: {e}"}
