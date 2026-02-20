import math
import unittest

from electrical.calculos_regulacion import tramo_ac_1f_ref, tramo_dc_ref
from electrical.ingenieria_nec_2023 import calcular_paquete_electrico_nec
from electrical.modelos import ParametrosCableado
from electrical.paquete_electrico import calcular_paquete_electrico_ref
from electrical.tramos_base import caida_tension_pct, elegir_calibre


class TestTramosBase(unittest.TestCase):
    def test_caida_tension_pct_no_nan(self):
        vd = caida_tension_pct(v=240.0, i=20.0, l_m=15.0, r_ohm_km=3.277, n_hilos=2)
        self.assertTrue(math.isfinite(vd))
        self.assertGreaterEqual(vd, 0.0)

    def test_monotonicidad_basica(self):
        vd_short = caida_tension_pct(v=240.0, i=20.0, l_m=10.0, r_ohm_km=3.277, n_hilos=2)
        vd_long = caida_tension_pct(v=240.0, i=20.0, l_m=20.0, r_ohm_km=3.277, n_hilos=2)
        self.assertGreater(vd_long, vd_short)

    def test_elegir_calibre_retorna_valido(self):
        awg = elegir_calibre(v=240.0, i=20.0, i_diseno_a=25.0, l_m=20.0, vd_obj_pct=2.0, tipo="CU", n_hilos=2)
        self.assertIsInstance(awg, str)
        self.assertTrue(len(awg) > 0)

    def test_regresion_keys_paquetes_ref_vs_nec(self):
        ref = calcular_paquete_electrico_ref(
            params=ParametrosCableado(
                vac=240.0,
                dist_dc_m=10.0,
                dist_ac_m=15.0,
                vdrop_obj_dc_pct=2.0,
                vdrop_obj_ac_pct=2.0,
                incluye_neutro_ac=False,
                otros_ccc=0,
            ),
            vmp_string_v=410.0,
            imp_a=13.2,
            isc_a=14.1,
            iac_estimado_a=25.0,
            fases_ac=1,
            n_strings=2,
            isc_mod_a=14.1,
            has_combiner=False,
        )

        nec = calcular_paquete_electrico_nec({
            "n_strings": 2,
            "n_modulos_serie": 7,
            "vmp_string_v": 290.5,
            "voc_frio_string_v": 361.053,
            "imp_mod_a": 13.25,
            "isc_mod_a": 14.1,
            "p_ac_w": 5000.0,
            "v_ac": 240.0,
            "fases": 1,
            "tension_sistema": "2F+N_120/240",
            "L_dc_string_m": 10.0,
            "L_ac_m": 15.0,
            "vd_max_dc_pct": 2.0,
            "vd_max_ac_pct": 2.0,
            "temp_amb_c": 30.0,
            "pf_ac": 1.0,
            "otros_ccc": 0,
            "incluye_neutro_ac": False,
        })

        self.assertTrue({"dc", "ac", "ocpd", "canalizacion"}.issubset(set(ref.keys())))
        self.assertTrue({"dc", "ac", "ocpd", "canalizacion"}.issubset(set(nec.keys())))


if __name__ == "__main__":
    unittest.main()
