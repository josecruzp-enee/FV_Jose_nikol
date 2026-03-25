from __future__ import annotations

"""
ADAPTER PANELES
===============

Responsabilidad:
    Traducir el puerto (EntradaPaneles) hacia el motor real de cálculo.

Principios:
    ✔ No contiene lógica de negocio
    ✔ No reconstruye inversor
    ✔ No modifica datos
    ✔ Solo delega

Arquitectura:
    Core → PuertoPaneles → Adapter → ejecutar_paneles → motor strings
"""

from electrical.paneles.entrada_panel import EntradaPaneles
from electrical.paneles.orquestador_paneles import ejecutar_paneles
from electrical.paneles.resultado_paneles import ResultadoPaneles


class PanelesAdapter:
    """
    Implementación concreta del PuertoPaneles.
    """

    def ejecutar(self, entrada: EntradaPaneles) -> ResultadoPaneles:
        """
        Ejecuta el cálculo de paneles/strings.

        Parámetros:
            entrada: EntradaPaneles
                - panel
                - inversor
                - n_inversores
                - condiciones térmicas
                - n_paneles_total

        Retorna:
            ResultadoPaneles
        """

        # ==================================================
        # VALIDACIÓN BÁSICA (defensiva, no lógica de negocio)
        # ==================================================
        if entrada is None:
            raise ValueError("EntradaPaneles es None")

        if entrada.inversor is None:
            raise ValueError("EntradaPaneles sin inversor")

        if entrada.n_inversores is None:
            raise ValueError("EntradaPaneles sin n_inversores")

        if entrada.panel is None:
            raise ValueError("EntradaPaneles sin panel")

        # ==================================================
        # DEBUG (opcional pero útil en producción)
        # ==================================================
        print("\n🔌 [ADAPTER PANELES]")
        print(" - inversor kw_ac:", getattr(entrada.inversor, "kw_ac", None))
        print(" - n_inversores:", entrada.n_inversores)

        # ==================================================
        # DELEGACIÓN AL MOTOR REAL
        # ==================================================
        resultado = ejecutar_paneles(entrada)

        # ==================================================
        # VALIDACIÓN DE SALIDA
        # ==================================================
        if resultado is None:
            raise ValueError("ejecutar_paneles devolvió None")

        return resultado
