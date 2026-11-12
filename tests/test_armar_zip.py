"""PG3-17: el escaneo de credenciales de scripts/armar_zip.py no deja pasar contraseñas ni las muestra."""
import contextlib
import io
import tempfile
import unittest
import zipfile
from pathlib import Path

from scripts import armar_zip


class TestCredenciales(unittest.TestCase):
    def hallazgos(self, nombre: str, texto: str) -> list[str]:
        with tempfile.TemporaryDirectory(dir=armar_zip.RAIZ) as d:
            ruta = Path(d) / nombre
            ruta.write_text(texto, encoding="utf-8")
            return armar_zip.credenciales([ruta])

    def test_detecta_las_formas_comunes(self):
        for linea in ('NEO4J_PASSWORD="mi clave larga"', "export NEO4J_PASSWORD=Abc12345 # prod", "password: x1y2z3",
                      "set NEO4J_PASSWORD=zzzz", "NEO4J_PASSWORD=tu_clave_real99", "NEO4J_PASSWORD=$ecret99"):
            with self.subTest(linea):
                self.assertEqual(len(self.hallazgos("a.md", linea)), 1)

    def test_los_placeholders_pasan(self):
        for linea in ("NEO4J_PASSWORD=", "NEO4J_PASSWORD=<tu clave>", "NEO4J_PASSWORD=${NEO4J_PASSWORD}", "NEO4J_PASSWORD=..."):
            with self.subTest(linea):
                self.assertEqual(self.hallazgos("a.md", linea), [])

    def test_en_python_solo_cuenta_la_cadena_literal(self):
        literal = "NEO4J_" + "PASSWORD = " + chr(34) + "Abc12345" + chr(34)   # armado, para que este archivo no se marque a sí mismo
        self.assertEqual(len(self.hallazgos("a.py", literal)), 1)
        self.assertEqual(self.hallazgos("a.py", 'x = os.getenv("NEO4J_PASSWORD", "")\npassword = os.environ["P"]'), [])

    def test_el_aviso_no_muestra_el_valor(self):
        self.assertNotIn("Abc12345", " ".join(self.hallazgos("a.md", "NEO4J_PASSWORD=Abc12345")))


class TestCodigoFuenteEjecutable(unittest.TestCase):
    """e_codigo_fuente/ tiene que andar sola: el manual dice que con el ZIP los comandos se corren desde ahí."""

    def test_e_codigo_fuente_tiene_cypher_tests_y_configuracion(self):
        with tempfile.TemporaryDirectory() as d:
            zip_ = Path(d) / "entrega.zip"
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(armar_zip.main(["--salida", str(zip_)]), 0)
            destino = Path(d) / "descomprimido"
            with zipfile.ZipFile(zip_) as z:
                z.extractall(destino)
            e = destino / "e_codigo_fuente"
            esperados = sorted(p.name for p in (armar_zip.RAIZ / "cypher").glob("*.cypher"))
            self.assertEqual(len(esperados), 9)
            self.assertEqual(sorted(p.name for p in (e / "cypher").glob("*.cypher")), esperados)
            self.assertTrue((e / "docs" / "cypher" / "Grupo_2_PG2_U1_corregido.cypher").is_file())
            self.assertTrue((e / "tests" / "__init__.py").is_file())
            self.assertTrue(any((e / "tests").glob("test_*.py")))
            for f in ("requirements.txt", ".env.example", "asistente/contrato.py", "scripts/cargar_grafo.py",
                      "prompts/maestro.txt"):
                with self.subTest(f):
                    self.assertTrue((e / f).is_file())
            self.assertFalse((e / ".env").exists())
            self.assertIn("e_codigo_fuente/", (destino / "LEEME.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
