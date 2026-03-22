from __future__ import annotations

from core.dominio.modelo import Datosproyecto
from core.dominio.contrato import ResultadoSizing

from electrical.paneles.resultado_paneles import ResultadoPaneles
from electrical.conductores.corrientes import (
    calcular_corrientes,
    CorrientesInput,
)
from electrical.protecciones.calculo_protecciones import (
    calcular_protecciones,
    EntradaProtecciones,
)


# ==========================================================
# NEC / CORRIENTES + PROTECCIONES
# ==========================================================

class PuertoNEC:

    def ejecutar(
        self,
        datos: Datosproyecto,
        sizing: ResultadoSizing,
        paneles: ResultadoPaneles,
    ):

        # ==================================================
        # VALIDACIÓN
        # ==================================================

        if not paneles.ok:
            raise ValueError("ResultadoPaneles inválido")

        if not paneles.strings:
            raise ValueError("No existen strings en ResultadoPaneles")

        # ==================================================
        # VOLTAJE DC (PARCHE CLAVE)
        # ==================================================

        vdc = paneles.strings[0].vmp_string_v

        # ==================================================
        # CORRIENTES (NEC)
        # ==================================================

        corrientes = calcular_corrientes(
            CorrientesInput(
                paneles=paneles,
                kw_ac=sizing.pac_nominal_kw,
                vac=datos.vac,
                fases=getattr(datos, "fases", 1),
                fp=getattr(datos, "fp", 1.0),
            )
        )

        # ==================================================
        # PROTECCIONES
        # ==================================================

        protecciones = calcular_protecciones(
            EntradaProtecciones(
                corrientes=corrientes
            )
        )

        return protecciones
