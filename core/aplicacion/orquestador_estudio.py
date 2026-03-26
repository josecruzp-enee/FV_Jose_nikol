from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from core.dominio.contrato import ResultadoProyecto

from core.aplicacion.puertos import (
    PuertoSizing,
    PuertoPaneles,
    PuertoElectrical,
    PuertoEnergia,
    PuertoFinanzas,
)

from electrical.paneles.entrada_panel import EntradaPaneles
from electrical.paneles.consolidacion_strings import consolidar_strings

strings_global = consolidar_strings(resultado_paneles)

# ==========================================================
# DEPENDENCIAS
# ==========================================================
@dataclass
class DependenciasEstudio:
    sizing: PuertoSizing
    paneles: PuertoPaneles
    energia: PuertoEnergia
    electrical: Optional[PuertoElectrical]
    finanzas: Optional[PuertoFinanzas] = None


# ==========================================================
# ORQUESTADOR PRINCIPAL
# ==========================================================
def ejecutar_estudio(datos: Any, deps: DependenciasEstudio):

    try:
        # --------------------------------------------------
        # 1. SIZING
        # --------------------------------------------------
        sizing = _ejecutar_sizing(datos, deps)

        if not getattr(sizing, "ok", True):
            return ResultadoProyecto(
                sizing=sizing,
                strings=None,
                energia=None,
                electrical=None,
                financiero=None
            )

        # --------------------------------------------------
        # 2. PANELES (🔥 MULTIZONA READY)
        # --------------------------------------------------
        from core.aplicacion.helpers_zonas import extraer_zonas
        from core.aplicacion.builder_paneles import (
            construir_entrada_paneles,
            construir_entrada_panel_desde_zona,
        )

        zonas = extraer_zonas(datos)

        # =========================
        # CASO LEGACY (1 zona)
        # =========================
        if len(zonas) == 1:

            entrada_paneles = construir_entrada_paneles(
                datos,
                sizing,
                deps.catalogos,  # 🔥 nuevo
            )

            paneles = _ejecutar_paneles(entrada_paneles, deps)

            if not paneles.ok:
                return ResultadoProyecto(
                    sizing=sizing,
                    strings=paneles,
                    energia=None,
                    electrical=None,
                    financiero=None
                )

        # =========================
        # CASO MULTIZONA
        # =========================
        else:

            resultados_zonas = []

            for z in zonas:

                entrada = construir_entrada_panel_desde_zona(
                    z,
                    sizing,
                    deps.catalogos,  # 🔥 desacoplado
                )

                res = _ejecutar_paneles(entrada, deps)

                if not getattr(res, "ok", True):
                    return ResultadoProyecto(
                        sizing=sizing,
                        strings=res,
                        energia=None,
                        electrical=None,
                        financiero=None
                    )

                resultados_zonas.append(res)

            # ⚠️ IMPORTANTE:
            # aún NO consolidamos (eso viene en el paso 2)
            paneles = resultados_zonas

        # --------------------------------------------------
        # 3. ENERGÍA
        # --------------------------------------------------
        energia = _ejecutar_energia(datos, sizing, paneles, deps)

        if not getattr(energia, "ok", True):
            return ResultadoProyecto(
                sizing=sizing,
                strings=paneles,
                energia=energia,
                electrical=None,
                financiero=None
            )

        # --------------------------------------------------
        # 4. ELECTRICAL
        # --------------------------------------------------
        electrico = _ejecutar_electrical(datos, sizing, paneles, deps)

        # --------------------------------------------------
        # 5. FINANZAS
        # --------------------------------------------------
        financiero = _ejecutar_finanzas(datos, sizing, energia, deps)

        # --------------------------------------------------
        # RESULTADO FINAL
        # --------------------------------------------------
        return ResultadoProyecto(
            sizing=sizing,
            strings=paneles,
            energia=energia,
            electrical=electrico,
            financiero=financiero,
        )

    except Exception:
        import traceback
        print(traceback.format_exc())
        raise

# ==========================================================
# FUNCIONES INTERNAS
# ==========================================================

def _ejecutar_sizing(datos, deps):
    sizing = deps.sizing.ejecutar(datos)

    if sizing is None:
        raise ValueError("Sizing devolvió None")

    return sizing


def _construir_entrada_paneles(datos, sizing):

    from electrical.catalogos.catalogos import get_panel
    from electrical.paneles.entrada_panel import EntradaPaneles

    equipos = getattr(datos, "equipos", {}) or {}

    panel_id = equipos.get("panel_id")

    if not panel_id:
        raise ValueError("panel_id no definido en datos.equipos")

    panel = get_panel(panel_id)

    if panel is None:
        raise ValueError(f"Panel no encontrado en catálogo: {panel_id}")

    inversor = sizing.inversor

    # ------------------------------------------------------
    # 🔥 OBTENER MODO (CLAVE)
    # ------------------------------------------------------
    modo = None

    # caso objeto
    if hasattr(datos, "modo_dimensionado"):
        modo = getattr(datos, "modo_dimensionado")

    # caso dict (por si acaso)
    elif isinstance(datos, dict):
        modo = datos.get("modo_dimensionado")

    # fallback seguro
    if not modo:
        modo = "manual"

    # normalizar
    modo = str(modo).strip().lower()

    # ------------------------------------------------------
    # CREAR ENTRADA
    # ------------------------------------------------------
    return EntradaPaneles(
        panel=panel,
        inversor=inversor,
        modo=modo,  # 🔥 ESTE ERA EL ERROR
        n_inversores=getattr(sizing, "n_inversores", 1),
        n_paneles_total=sizing.n_paneles,
    )

def _ejecutar_paneles(entrada_paneles, deps):

    resultado = deps.paneles.ejecutar(entrada_paneles)

    if resultado is None:
        raise ValueError("Paneles devolvió None")

    return resultado


def _ejecutar_energia(datos, sizing, paneles, deps):

    energia = deps.energia.ejecutar(datos, sizing, paneles)

    if energia is None:
        raise ValueError("Energía devolvió None")

    return energia


def _ejecutar_electrical(datos, sizing, paneles, deps):

    if not deps.electrical:
        print("⚠ No hay módulo electrical")
        return None

    print("🔥 LLAMANDO ELECTRICAL")

    resultado = deps.electrical.ejecutar(
        datos=datos,
        paneles=paneles,
        sizing=sizing,
    )

    print("⚡ RESULTADO ELECTRICAL:", resultado)

    return resultado


def _ejecutar_finanzas(datos, sizing, energia, deps):

    if not deps.finanzas:
        return None

    return deps.finanzas.ejecutar(datos, sizing, energia)
