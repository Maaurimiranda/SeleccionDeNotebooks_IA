"""PG3-01: grafo.leer no puede escribir (READ_ACCESS)."""
import unittest

from asistente.contrato import ErrorGrafo
from tests.comun import grafo_real, requiere_neo4j


@requiere_neo4j
class TestGrafoSoloLectura(unittest.TestCase):
    def test_create_falla_en_leer(self):
        g = grafo_real()
        with self.assertRaises(ErrorGrafo):
            g.leer("CREATE (:PruebaEscritura {x: 1})")
        self.assertEqual(g.leer("MATCH (n:PruebaEscritura) RETURN count(n) AS n")[0]["n"], 0)

    def test_catalogo_y_pedidos(self):
        g = grafo_real()
        self.assertEqual(len(g.catalogo()), 9)
        # los precargados; los pedidos creados desde consultas (req_101 en adelante, origen 'consulta') pueden
        # quedar de usar la web o la consola y no son parte del grafo cargado (se borran con scripts.limpiar_pedidos)
        nuevos = {f["id"] for f in g.leer("MATCH (c:Requerimiento {origen:'consulta'}) RETURN c.id AS id")}
        self.assertEqual([p for p in g.pedidos() if p not in nuevos], ["req_01", "req_02", "req_03"])


if __name__ == "__main__":
    unittest.main()
