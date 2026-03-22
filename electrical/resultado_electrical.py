from __future__ import annotations
from dataclasses import dataclass
from typing import List

from electrical.paneles.resultado_paneles import ResultadoPaneles
from electrical.conductores.resultado_corrientes import ResultadoCorrientes
from electrical.conductores.resultado_conductores import ResultadoConductores
from electrical.protecciones.resultado_protecciones import ResultadoProtecciones


@dataclass(frozen=True)
class ResultadoElectrico:
    """
    Resultado consolidado del sistema eléctrico FV.
    Este objeto es INMUTABLE y SOLO debe construirse desde el orquestador.
    """

    ok: bool

    paneles: ResultadoPaneles
    corrientes: ResultadoCorrientes
    conductores: ResultadoConductores
    protecciones: ResultadoProtecciones

    errores: List[str]
    warnings: List[str]

    # =========================
    # 🔧 CONSTRUCTOR OFICIAL
    # =========================
    @staticmethod
    def build(
        paneles: ResultadoPaneles,
        corrientes: ResultadoCorrientes,
        conductores: ResultadoConductores,
        protecciones: ResultadoProtecciones,
    ) -> "ResultadoElectrico":
        """
        Construye el resultado consolidado a partir de subresultados.
        Este es el ÚNICO punto válido de creación.
        """

        # 🔴 Consolidación de errores
        errores = (
            (paneles.errores if paneles else [])
            + (corrientes.errores if corrientes else [])
            + (conductores.errores if conductores else [])
            + (protecciones.errores if protecciones else [])
        )

        # 🟡 Consolidación de warnings
        warnings = (
            (paneles.warnings if paneles else [])
            + (corrientes.warnings if corrientes else [])
            + (conductores.warnings if conductores else [])
            + (protecciones.warnings if protecciones else [])
        )

        # ✅ Estado global
        ok = (
            paneles.ok
            and corrientes.ok
            and conductores.ok
            and protecciones.ok
        )

        return ResultadoElectrico(
            ok=ok,
            paneles=paneles,
            corrientes=corrientes,
            conductores=conductores,
            protecciones=protecciones,
            errores=errores,
            warnings=warnings,
        )

    # =========================
    # 📊 PROPIEDADES ÚTILES
    # =========================
    @property
    def hay_errores(self) -> bool:
        return len(self.errores) > 0

    @property
    def hay_warnings(self) -> bool:
        return len(self.warnings) > 0

    @property
    def resumen(self) -> str:
        if self.ok:
            return "Sistema eléctrico válido"
        return f"Sistema con errores: {len(self.errores)} encontrados"
