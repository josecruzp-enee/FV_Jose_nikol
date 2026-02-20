import unittest

from core.modelo import Datosproyecto
from core.orquestador import ejecutar_evaluacion


class TestHappyPathCore(unittest.TestCase):
    def _datos_minimos_validos(self) -> Datosproyecto:
        p = Datosproyecto(
            cliente="Cliente Test",
            ubicacion="Tegucigalpa",
            consumo_12m=[1000.0] * 12,
            tarifa_energia=4.998,
            cargos_fijos=325.38,
            prod_base_kwh_kwp_mes=145.0,
            factores_fv_12m=[1.0] * 12,
            cobertura_objetivo=0.64,
            costo_usd_kwp=1200.0,
            tcambio=27.0,
            tasa_anual=0.08,
            plazo_anios=10,
            porcentaje_financiado=1.0,
            om_anual_pct=0.01,
        )
        p.sistema_fv = {}
        p.equipos = {
            "panel_id": "panel_550w",
            "inversor_id": "inv_5kw_2mppt",
            "sobredimension_dc_ac": 1.2,
            "tension_sistema": "2F+N_120/240",
        }
        p.electrico = {}
        return p

    def test_ejecutar_evaluacion_happy_path(self):
        resultado = ejecutar_evaluacion(self._datos_minimos_validos())

        for key in [
            "params_fv",
            "sizing",
            "cuota_mensual",
            "tabla_12m",
            "evaluacion",
            "decision",
            "ahorro_anual_L",
            "payback_simple_anios",
            "electrico",
            "electrico_nec",
            "finanzas_lp",
        ]:
            self.assertIn(key, resultado)

        self.assertEqual(12, len(resultado["tabla_12m"]))

        electrico_nec = resultado.get("electrico_nec") or {}
        self.assertIn("paq", electrico_nec)
        self.assertIsInstance(electrico_nec.get("paq"), dict)


if __name__ == "__main__":
    unittest.main()
