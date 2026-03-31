from __future__ import annotations

from electrical.paneles.resultado_paneles import ResultadoPaneles

from electrical.conductores.corrientes import (
    calcular_corrientes,
    CorrientesInput,
)

from electrical.conductores.calculo_conductores import (
    dimensionar_tramos_fv as calcular_conductores,
)

from electrical.conductores.resultado_conductores import ResultadoConductores

from electrical.protecciones.protecciones import (
    calcular_protecciones,
    EntradaProtecciones,
)

from electrical.resultado_electrical import ResultadoElectrico

# 🔥 VALIDADOR
from electrical.validacion_fv import validar_sistema_fv


# ==========================================================
# ORQUESTADOR ELECTRICAL
# ==========================================================
def ejecutar_paneles(entrada: EntradaPaneles) -> ResultadoPaneles:

    errores: List[str] = []
    warnings: List[str] = []

    panel = entrada.panel
    inversor = entrada.inversor

    # ------------------------------------------------------
    # VALIDACIÓN
    # ------------------------------------------------------
    for val in (
        validar_panel(panel),
        validar_inversor(inversor),
    ):
        errores += val.errores
        warnings += val.warnings

    if errores:
        return _resultado_error(panel, errores, warnings)

    # ======================================================
    # 🔥 MULTIZONA (ROBUSTO)
    # ======================================================
    if entrada.zonas:

        strings: List[StringFV] = []

        for i, zona in enumerate(entrada.zonas):

            # 🔍 DEBUG
            warnings.append(f"DEBUG ZONA {i+1}: {zona}")

            valor = zona.get("n_paneles")

            if valor is None:
                warnings.append(f"Zona {i+1} sin n_paneles")
                continue

            try:
                n = int(valor)
            except Exception:
                warnings.append(f"Zona {i+1} inválida")
                continue

            if n <= 0:
                warnings.append(f"Zona {i+1} <= 0")
                continue

            strings.append(
                StringFV(
                    mppt=i + 1,
                    n_series=n,
                    vmp_string_v=panel.vmp_v * n,
                    voc_frio_string_v=panel.voc_v * n,
                    imp_string_a=panel.imp_a,
                    isc_string_a=panel.isc_a,
                )
            )

        # ❌ si todas las zonas fallaron
        if not strings:
            return _resultado_error(panel, ["No hay zonas válidas"], warnings)

        # --------------------------------------------------
        # ARRAY
        # --------------------------------------------------
        n_paneles_total = sum(s.n_series for s in strings)
        pdc_kw = (n_paneles_total * panel.pmax_w) / 1000

        array = ArrayFV(
            potencia_dc_w=pdc_kw * 1000,
            vdc_nom=max(s.vmp_string_v for s in strings),
            idc_nom=panel.imp_a * len(strings),
            isc_total=panel.isc_a * len(strings),
            voc_frio_array_v=max(s.voc_frio_string_v for s in strings),
            n_strings_total=len(strings),
            n_paneles_total=n_paneles_total,
            strings_por_mppt=1,
            n_mppt=inversor.n_mppt,
            p_panel_w=panel.pmax_w,
        )

        meta = PanelesMeta(
            n_paneles_total=n_paneles_total,
            pdc_kw=pdc_kw,
            n_inversores=entrada.n_inversores,
        )

        return ResultadoPaneles(
            ok=True,
            panel=panel,
            topologia="multizona",
            array=array,
            recomendacion=None,
            strings=strings,
            warnings=warnings,
            errores=[],
            meta=meta,
        )

    # ======================================================
    # NORMAL (auto / manual)
    # ======================================================
    n_paneles, pdc_kw, err = _resolver_dimensionado(entrada, panel)

    if err:
        return _resultado_error(panel, err, warnings)

    strings_res = calcular_strings_fv(
        n_paneles_total=n_paneles,
        panel=panel,
        inversor=inversor,
        n_inversores=entrada.n_inversores,
        t_min_c=entrada.t_min_c,
        t_oper_c=entrada.t_oper_c,
        modo=entrada.modo,
    )

    if not strings_res.ok:
        return _resultado_error(panel, strings_res.errores, warnings)

    # ------------------------------------------------------
    # ARRAY
    # ------------------------------------------------------
    array = _armar_array(
        panel,
        inversor,
        strings_res,
        n_paneles,
        pdc_kw,
        _strings_por_mppt_real(strings_res),
        entrada.n_inversores,
    )

    # ------------------------------------------------------
    # STRINGS
    # ------------------------------------------------------
    strings = _mapear_strings(strings_res)

    # ------------------------------------------------------
    # META
    # ------------------------------------------------------
    meta = PanelesMeta(
        n_paneles_total=n_paneles,
        pdc_kw=pdc_kw,
        n_inversores=entrada.n_inversores,
    )

    return ResultadoPaneles(
        ok=True,
        panel=panel,
        topologia="string",
        array=array,
        recomendacion=strings_res.recomendacion,
        strings=strings,
        warnings=warnings,
        errores=[],
        meta=meta,
    )
