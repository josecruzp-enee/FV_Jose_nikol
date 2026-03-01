from core.servicios.sizing import calcular_sizing_unificado
from core.servicios.finanzas import ejecutar_finanzas

from electrical.paneles.orquestador_paneles import ejecutar_paneles_desde_sizing
from electrical.energia.orquestador_energia import ejecutar_motor_energia
from electrical.energia.contrato import EnergiaInput
from electrical.nec.orquestador_nec import ejecutar_nec

from .puertos import (
    PuertoSizing,
    PuertoPaneles,
    PuertoEnergia,
    PuertoNEC,
    PuertoFinanzas,
)

from .orquestador_estudio import DependenciasEstudio


# -----------------------------
# ADAPTADORES
# -----------------------------

class SizingAdapter(PuertoSizing):
    def ejecutar(self, datos):
        return calcular_sizing_unificado(datos)


class PanelesAdapter(PuertoPaneles):
    def ejecutar(self, datos, sizing):
        return ejecutar_paneles_desde_sizing(datos, sizing)


class EnergiaAdapter(PuertoEnergia):
    def ejecutar(self, datos, sizing, strings):

        # -------------------------
        # 1. Potencias desde sizing
        # -------------------------
        pdc_instalada_kw = sizing.get("pdc_kw")
        pac_nominal_kw = sizing.get("pac_kw")

        # -------------------------
        # 2. Irradiancia mensual
        # -------------------------
        # Si tu modelo ya trae factores mensuales, los usamos.
        # Si no, deberías traer HSP base desde el módulo de energía.
        hsp_12m = getattr(datos, "factores_fv_12m", None)
        if not hsp_12m:
            raise ValueError("No se encontraron HSP/factores mensuales en Datosproyecto.")

        # -------------------------
        # 3. Días estándar por mes
        # -------------------------
        dias_mes = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

        # -------------------------
        # 4. Parámetros físicos desde sistema_fv
        # -------------------------
        sf = getattr(datos, "sistema_fv", {}) or {}

        factor_orientacion = sf.get("factor_orientacion", 1.0)
        perdidas_dc_pct = sf.get("perdidas_dc_pct", 3.0)
        perdidas_ac_pct = sf.get("perdidas_ac_pct", 2.0)
        sombras_pct = sf.get("sombras_pct", 0.0)
        permitir_curtailment = sf.get("permitir_curtailment", True)

        # -------------------------
        # 5. Construcción contrato
        # -------------------------
        inp = EnergiaInput(
            pdc_instalada_kw=pdc_instalada_kw,
            pac_nominal_kw=pac_nominal_kw,
            hsp_12m=hsp_12m,
            dias_mes=dias_mes,
            factor_orientacion=factor_orientacion,
            perdidas_dc_pct=perdidas_dc_pct,
            perdidas_ac_pct=perdidas_ac_pct,
            sombras_pct=sombras_pct,
            permitir_curtailment=permitir_curtailment,
        )

        return ejecutar_motor_energia(inp)


class NECAdapter(PuertoNEC):
    def ejecutar(self, datos, sizing, strings):
        return ejecutar_nec(datos, sizing, strings)


class FinanzasAdapter(PuertoFinanzas):
    def ejecutar(self, datos, sizing, energia):
        return ejecutar_finanzas(
            datos=datos,
            sizing=sizing,
            energia=energia,
        )


# -----------------------------
# FACTORY DE DEPENDENCIAS
# -----------------------------

def construir_dependencias() -> DependenciasEstudio:
    return DependenciasEstudio(
        sizing=SizingAdapter(),
        paneles=PanelesAdapter(),
        energia=EnergiaAdapter(),
        nec=NECAdapter(),
        finanzas=FinanzasAdapter(),
    )
