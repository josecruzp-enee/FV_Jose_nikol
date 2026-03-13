from __future__ import annotations

from core.aplicacion.orquestador_estudio import DependenciasEstudio

from core.servicios.sizing import calcular_sizing_unificado
from electrical.paneles.orquestador_paneles import ejecutar_paneles
from electrical.energia.orquestador_energia import ejecutar_motor_energia
from electrical.nec.orquestador_nec import ejecutar_nec
from core.servicios.finanzas import ejecutar_finanzas

from electrical.paneles.entrada_panel import EntradaPaneles


class PanelesAdapter:

    def ejecutar(self, datos, sizing):

        entrada = EntradaPaneles(

            panel=sizing.panel,

            inversor=sizing.inversor,

            n_paneles_total=sizing.n_paneles,

            n_inversores=sizing.n_inversores,

            t_min_c=datos.sistema_fv.get("t_min_c", 10),

            t_oper_c=datos.sistema_fv.get("t_oper_c", 45),

            dos_aguas=datos.sistema_fv.get("dos_aguas", False),

            objetivo_dc_ac=datos.sistema_fv.get("dc_ac_ratio", 1.2),

            pdc_kw_objetivo=sizing.pdc_kw

        )

        return ejecutar_paneles(entrada)

class SizingAdapter:
    def ejecutar(self, datos):
        return calcular_sizing_unificado(datos)


class EnergiaAdapter:
    def ejecutar(self, datos, sizing, strings):
        return ejecutar_motor_energia(datos, sizing, strings)


class NECAdapter:
    def ejecutar(self, datos, sizing, strings):
        # Ajuste importante: si tu ejecutar_nec espera (entrada_nec, sizing, strings)
        # entonces aquí deberías construir 'entrada_nec'. Si tu versión ya acepta
        # (datos, sizing, strings), esto funciona tal cual.
        return ejecutar_nec(datos, sizing, strings)


class FinanzasAdapter:
    def ejecutar(self, datos, sizing, energia):
        return ejecutar_finanzas(datos, sizing, energia)


def construir_dependencias():
    return DependenciasEstudio(
        sizing=SizingAdapter(),
        paneles=PanelesAdapter(),
        energia=EnergiaAdapter(),
        nec=NECAdapter(),
        finanzas=FinanzasAdapter(),
    )
