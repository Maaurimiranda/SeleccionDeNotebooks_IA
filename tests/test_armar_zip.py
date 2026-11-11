"""PG3-17: el escaneo de credenciales de scripts/armar_zip.py no deja pasar contraseñas ni las muestra."""
import tempfile
import unittest
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


if __name__ == "__main__":
    unittest.main()
