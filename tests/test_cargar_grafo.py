"""PG3-17: scripts/cargar_grafo.py no borra la base si no encuentra qué cargar (por ejemplo, desde una carpeta sin cypher/)."""
import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts import cargar_grafo


class TestSinArchivosNoBorra(unittest.TestCase):
    def correr(self, argv: list[str], dir_cypher: Path) -> tuple[mock.Mock, SystemExit]:
        """Corre main() con cypher/ apuntando a dir_cypher y un driver falso; devuelve el driver y la salida."""
        driver = mock.Mock()
        with mock.patch.object(cargar_grafo, "DIR_CYPHER", dir_cypher), \
             mock.patch.object(cargar_grafo, "CANONICO", dir_cypher.parent / "docs" / "cypher" / "no_existe.cypher"), \
             mock.patch.object(cargar_grafo.config, "NEO4J_PASSWORD", "clave-de-prueba"), \
             mock.patch.object(cargar_grafo.GraphDatabase, "driver", driver), \
             mock.patch("sys.argv", ["cargar_grafo", *argv]), \
             contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(SystemExit) as ctx:
                cargar_grafo.main()
        return driver, ctx.exception

    def test_sin_cypher_sale_con_error_sin_conectarse(self):
        with tempfile.TemporaryDirectory() as d:
            for argv, carpeta in (([], Path(d) / "cypher"), ([], Path(d)), (["--canonico"], Path(d) / "cypher")):
                with self.subTest(argv=argv, carpeta=carpeta.name):
                    driver, salida = self.correr(argv, carpeta)
                    driver.assert_not_called()   # sin driver no hay sesión, y sin sesión no se borra nada
                    self.assertNotIn(salida.code, (0, None))
                    self.assertIn("No se tocó la base", str(salida.code))

    def test_hasta_que_no_deja_ningun_archivo_tambien_frena(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "10_sm1.cypher").write_text("RETURN 1;\n", encoding="utf-8")
            driver, salida = self.correr(["--hasta", "5"], Path(d))
            driver.assert_not_called()
            self.assertIn("No se tocó la base", str(salida.code))

    def test_con_los_archivos_del_proyecto_no_frena(self):
        lista = cargar_grafo.comprobar_archivos()
        self.assertEqual([p.name for p in lista][:1], ["00_esquema.cypher"])
        self.assertNotIn("90_verificacion.cypher", [p.name for p in lista])


if __name__ == "__main__":
    unittest.main()
