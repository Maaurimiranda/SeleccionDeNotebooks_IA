"""D-03 / PG3-25: la propuesta provisional de SALIDA_PI2 (scripts/proponer_salida_pi2.py)."""
import re
import unittest

from scripts import proponer_salida_pi2 as p

NB = {"modelo": "Notebook_K", "gama": "media", "ram": 8, "ampliabilidad": "ampliable", "max_gb": 32,
      "ranuras": 1, "ssd": 512, "tipo_alm": "SSD", "srgb": 60, "hz": 60, "pantalla_virt": 0.9}
REQ_DEV = {"gama_cpu": "media", "ram_gb": (16, 32), "ssd_gb": 1024}


class TestMetodo(unittest.TestCase):
    def test_rendimiento_sp6_con_ren_r7(self):
        # CPU 1,0 · RAM 8 < 16 ampliable -> 0,5 (REN-R7) · SSD 512 = M/2 -> 0,4
        self.assertEqual(p.rendimiento(NB, REQ_DEV), round(0.35 + 0.40 * 0.5 + 0.25 * 0.4, 2))

    def test_ampliabilidad_desconocida_no_aplica_ren_r7(self):
        g = {**NB, "ampliabilidad": "desconocida", "max_gb": None, "ranuras": None}
        self.assertEqual(p.grado_ram(g, 16, 32), 0.0)

    def test_pantalla_por_perfil(self):
        self.assertEqual(p.pantalla(NB, "DEV"), (0.9, "igual"))
        self.assertEqual(p.pantalla(NB, "DIS"), (round(60 / 95, 2), "srgb"))
        self.assertEqual(p.pantalla({**NB, "hz": 144}, "GAM"), (1.0, "hz"))


class TestArchivoCargado(unittest.TestCase):
    def setUp(self):
        self.texto = p.CYPHER.read_text(encoding="utf-8")
        self.filas = re.findall(r"m:'(Notebook_\w)', p:'(\w+)', rend:([\d.]+), pant:([\d.]+)", self.texto)

    def test_53_pares_sin_virt_ni_k_ofi(self):
        self.assertEqual(len(self.filas), 53)
        pares = {(m, perfil) for m, perfil, _, _ in self.filas}
        self.assertEqual(len(pares), 53)
        self.assertNotIn(("Notebook_K", "OFI"), pares)
        self.assertFalse(any(perfil == "VIRT" for _, perfil in pares))

    def test_valores_en_rango_y_marcados_sin_validar(self):
        for _, _, rend, pant in self.filas:
            self.assertTrue(0 <= float(rend) <= 1 and 0 <= float(pant) <= 1)
        self.assertIn("s.validacion = 'sin validar'", self.texto)
        self.assertIn("sin validar por SM2", self.texto)


if __name__ == "__main__":
    unittest.main()
