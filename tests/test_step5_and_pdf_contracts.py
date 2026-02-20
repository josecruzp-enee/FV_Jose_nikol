import copy
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from core.modelo import Datosproyecto
from core.orquestador import ejecutar_evaluacion
from ui import ingenieria_electrica as ie
from ui import resultados as ui_resultados


class TestStep5AndPdfContracts(unittest.TestCase):
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

    def test_paso5_core_se_ejecuta_una_sola_vez_si_reuso_res(self):
        ctx = SimpleNamespace(datos_proyecto=None, resultado_core=None)
        fake_datos = object()
        fake_res = {"electrico_nec": {"paq": {"dc": {}}}}

        with patch.object(ie, "_datosproyecto_desde_ctx", return_value=fake_datos), patch.object(
            ie, "ejecutar_evaluacion", return_value=fake_res
        ) as mock_eval:
            res = ie._ejecutar_core(ctx)
            pkg = ie._obtener_pkg_nec(ctx, res=res)

        self.assertEqual(fake_res, res)
        self.assertEqual({"dc": {}}, pkg)
        self.assertEqual(1, mock_eval.call_count)

    def test_contrato_orquestador_expone_electrico_y_electrico_ref(self):
        res = ejecutar_evaluacion(self._datos_minimos_validos())
        self.assertIn("electrico", res)
        self.assertIn("electrico_ref", res)
        self.assertEqual(res.get("electrico"), res.get("electrico_ref"))

    def test_datos_pdf_no_muta_datos_proyecto(self):
        dp = self._datos_minimos_validos()
        if hasattr(dp, "consumo_anual"):
            delattr(dp, "consumo_anual")

        ctx = SimpleNamespace(datos_proyecto=dp)
        before = copy.deepcopy(dp.__dict__)

        datos_pdf = ui_resultados._datos_pdf_from_ctx(ctx, {"consumo_anual": 12345.0})

        self.assertIn("consumo_anual", datos_pdf)
        self.assertEqual(before, dp.__dict__)
        self.assertFalse(hasattr(dp, "consumo_anual"))


if __name__ == "__main__":
    unittest.main()
