"""Acceso a Neo4j (ARQUITECTURA §4.5). Repositorio común del sistema.

`leer` abre la sesión en READ_ACCESS dentro de una transacción de lectura: una
consulta del asistente no puede escribir en el grafo (A11, principio 5).
"""
from neo4j import GraphDatabase, READ_ACCESS, WRITE_ACCESS

from asistente import config
from asistente.contrato import ErrorGrafo


class Grafo:
    def __init__(self, uri: str | None = None, usuario: str | None = None,
                 clave: str | None = None, base: str | None = None):
        self.uri = uri or config.NEO4J_URI
        self.usuario = usuario or config.NEO4J_USER
        self.clave = clave if clave is not None else config.NEO4J_PASSWORD
        self.base = base or config.NEO4J_DATABASE
        self._driver = None
        self._catalogo: list[str] | None = None
        self._pedidos: list[str] | None = None

    # El driver se crea recién en la primera consulta: así la API levanta aunque
    # Neo4j esté apagado, y /salud lo informa.
    def _drv(self):
        if self._driver is None:
            try:
                # Tiempos cortos: si Neo4j está apagado, el usuario recibe el error fijo en
                # segundos y no después de ~30 s de reintentos del driver.
                self._driver = GraphDatabase.driver(self.uri, auth=(self.usuario, self.clave),
                                                    notifications_min_severity="OFF",
                                                    connection_timeout=5, max_transaction_retry_time=2)
            except Exception as e:
                raise ErrorGrafo(f"No se pudo crear el driver de Neo4j ({type(e).__name__}): {e}") from e
        return self._driver

    def _correr(self, modo, cypher: str, parametros: dict | None) -> list[dict]:
        def trabajo(tx):
            return [r.data() for r in tx.run(cypher, **(parametros or {}))]
        try:
            with self._drv().session(database=self.base, default_access_mode=modo) as s:
                if modo == READ_ACCESS:
                    return s.execute_read(trabajo)
                return s.execute_write(trabajo)
        except ErrorGrafo:
            raise
        except Exception as e:  # ServiceUnavailable, AuthError, CypherSyntaxError, escritura en lectura...
            raise ErrorGrafo(f"No se pudo consultar Neo4j ({type(e).__name__}): {e}") from e

    def leer(self, cypher: str, parametros: dict | None = None) -> list[dict]:
        return self._correr(READ_ACCESS, cypher, parametros)

    def escribir(self, cypher: str, parametros: dict | None = None) -> list[dict]:
        """Solo para SM1.registrar_pedido y SM1.aclarar_pedido (nivel 2, D-08)."""
        self._catalogo = self._pedidos = None
        return self._correr(WRITE_ACCESS, cypher, parametros)

    def catalogo(self) -> list[str]:
        if self._catalogo is None:
            self._catalogo = [f["v"] for f in self.leer("MATCH (n:Notebook) RETURN n.modelo AS v ORDER BY v")]
        return self._catalogo

    def pedidos(self) -> list[str]:
        if self._pedidos is None:
            self._pedidos = [f["v"] for f in self.leer("MATCH (c:Requerimiento) RETURN c.id AS v ORDER BY v")]
        return self._pedidos

    def salud(self) -> dict:
        try:
            n = self.leer("MATCH (n:Notebook) RETURN count(n) AS n")[0]["n"]
            return {"ok": True, "uri": self.uri, "notebooks": n}
        except ErrorGrafo as e:
            return {"ok": False, "uri": self.uri, "error": str(e)}

    def cerrar(self):
        if self._driver is not None:
            self._driver.close()
            self._driver = None
