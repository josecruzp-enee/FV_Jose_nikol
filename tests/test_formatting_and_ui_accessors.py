import unittest

from core.rutas import money_L as core_money_L
from core.result_accessors import get_capex_L, get_kwp_dc, get_n_paneles
from reportes.pdf_utils import money_L as pdf_money_L
from ui import resultados as ui_resultados


class TestFormattingAndUIAccessors(unittest.TestCase):
    def test_money_L_consistency_core_vs_pdf(self):
        v = 12345.678
        self.assertEqual(core_money_L(v), pdf_money_L(v))
        self.assertEqual(core_money_L(v, dec=0), pdf_money_L(v, dec=0))

    def test_ui_wrappers_delegate_accessors(self):
        sizing = {"kwp_dc": "5.5", "capex_L": "120000", "n_paneles": "10"}
        res = {"sizing": sizing}

        self.assertEqual(get_kwp_dc(res), ui_resultados._kwp_dc_from_sizing(sizing))
        self.assertEqual(get_capex_L(res), ui_resultados._capex_L_from_sizing(sizing))
        self.assertEqual(get_n_paneles(res), ui_resultados._n_paneles_from_sizing(sizing))


if __name__ == "__main__":
    unittest.main()
