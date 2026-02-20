import copy
import unittest

from core.result_accessors import (
    get_capex_L,
    get_consumo_anual,
    get_electrico_nec,
    get_electrico_nec_pkg,
    get_kwp_dc,
    get_n_paneles,
    get_sizing,
    get_strings,
    get_tabla_12m,
)


class TestResultAccessors(unittest.TestCase):
    def test_res_parcial_no_revienta_y_tipos(self):
        res = {}
        self.assertIsInstance(get_sizing(res), dict)
        self.assertIsInstance(get_kwp_dc(res), float)
        self.assertIsInstance(get_capex_L(res), float)
        self.assertIsInstance(get_n_paneles(res), int)
        self.assertIsInstance(get_tabla_12m(res), list)
        self.assertIsInstance(get_consumo_anual(res), float)
        self.assertIsInstance(get_electrico_nec(res), dict)
        self.assertIsInstance(get_electrico_nec_pkg(res), dict)
        self.assertIsInstance(get_strings(res), list)

    def test_no_muta_res(self):
        res = {
            "sizing": {"kwp_dc": 4.2, "capex_L": 1000, "n_paneles": 8, "cfg_strings": {"strings": [{"mppt": 1}]}},
            "tabla_12m": [{"consumo_kwh": 100}],
            "electrico_nec": {"paq": {"dc": {"config_strings": {"n_strings": 1}}}},
        }
        before = copy.deepcopy(res)
        _ = get_sizing(res)
        _ = get_kwp_dc(res)
        _ = get_capex_L(res)
        _ = get_n_paneles(res)
        _ = get_tabla_12m(res)
        _ = get_consumo_anual(res)
        _ = get_electrico_nec(res)
        _ = get_electrico_nec_pkg(res)
        _ = get_strings(res)
        self.assertEqual(before, res)

    def test_caso_tipico(self):
        res = {
            "sizing": {
                "pdc_kw": 5.5,
                "capex": 250000,
                "cfg_strings": {"n_paneles": 10, "strings": [{"mppt": 1, "n_series": 5}]},
            },
            "tabla_12m": [{"consumo_kwh": 1000} for _ in range(12)],
            "electrico_nec": {"ok": True, "paq": {"dc": {"config_strings": {"n_strings": 2, "modulos_por_string": 5}}}},
        }
        self.assertAlmostEqual(5.5, get_kwp_dc(res))
        self.assertAlmostEqual(250000.0, get_capex_L(res))
        self.assertEqual(10, get_n_paneles(res))
        self.assertEqual(12, len(get_tabla_12m(res)))
        self.assertGreater(get_consumo_anual(res), 0)
        self.assertIn("paq", get_electrico_nec(res))
        self.assertIsInstance(get_electrico_nec_pkg(res), dict)
        self.assertEqual(1, len(get_strings(res)))


if __name__ == "__main__":
    unittest.main()
