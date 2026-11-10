"""PG3-05: la comparación de conteos del grafo (scripts/contar_grafo.py)."""
import unittest

from scripts.contar_grafo import comparar, diferencias_sentencias

BASE = {"nodos": {"Notebook": 9, "Regla": 31}, "relaciones": {"EVALUA": 27},
        "total_nodos": 40, "total_relaciones": 27}


class TestCompararConteos(unittest.TestCase):
    def test_iguales(self):
        tabla, igual = comparar(BASE, dict(BASE))
        self.assertTrue(igual)
        self.assertNotIn("**NO**", tabla)

    def test_una_diferencia_se_marca(self):
        otro = {**BASE, "nodos": {"Notebook": 9, "Regla": 30}, "total_nodos": 39}
        tabla, igual = comparar(BASE, otro)
        self.assertFalse(igual)
        self.assertIn("| label | Regla | 31 | 30 | **NO** |", tabla)

    def test_un_label_que_falta_cuenta_cero(self):
        otro = {**BASE, "relaciones": {}}
        tabla, igual = comparar(BASE, otro)
        self.assertFalse(igual)
        self.assertIn("| relación | EVALUA | 27 | 0 | **NO** |", tabla)


class TestCorteDelCanonico(unittest.TestCase):
    def test_cypher_es_el_canonico_salvo_los_arreglos_de_d06(self):
        """PG3-02: cortar el canónico no cambió el contenido. D-06 cambió 3 sentencias ('provisional' a
        'sin validar') y una más (REC-R5, que ahora suma la prioridad `grafica`)."""
        total_c, total_d, solo_c, solo_d = diferencias_sentencias()
        self.assertEqual(total_c, total_d)
        resto = [t for t in solo_c if t.replace("'provisional'", "'sin validar'") not in solo_d]
        self.assertEqual(len(resto), 1, "solo debe quedar la sentencia de REC-R5")
        self.assertIn("P_INCREMENTO_PRIORIDAD", resto[0])


if __name__ == "__main__":
    unittest.main()
