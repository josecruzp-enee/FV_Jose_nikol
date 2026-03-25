from __future__ import annotations

from electrical.paneles.resultado_paneles import ResultadoPaneles

from electrical.paneles.string_auto import calcular_strings_fv  # 🔥 NUEVO

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


# ==========================================================
# ORQUESTADOR ELECTRICAL
# ==========================================================

def ejecutar_electrical(*args, **kwargs) -> ResultadoElectrico:

    # ======================================================
    # NORMALIZADOR DE ENTRADA
    # ======================================================
    if args:
        if len(args) == 2:
            datos, paneles = args
            kwargs["datos"] = datos
            kwargs["paneles"] = paneles

    paneles = kwargs.get("paneles")
    datos = kwargs.get("datos")
    sizing = kwargs.get("sizing")

    try:

        print("\n⚡ [ELECTRICAL] INICIO")

        # ==================================================
        # VALIDACIONES BASE
        # ==================================================
        if not paneles or not paneles.ok:
            return ResultadoElectrico.build(
                paneles=paneles,
                corrientes=_corrientes_error("Paneles inválidos"),
                conductores=_conductores_error("Paneles inválidos"),
                protecciones=_protecciones_error("Paneles inválidos"),
            )

        if not sizing:
            raise ValueError("Falta sizing en electrical")

        # ==================================================
        # 🔥 STRINGS AUTOMÁTICO (NUEVO)
        # ==================================================
        panel_obj = getattr(paneles, "panel", None) or getattr(paneles, "panel_spec", None)

        if panel_obj is None:
            raise ValueError("No se pudo obtener panel desde ResultadoPaneles")

        strings = calcular_strings_fv(
            n_paneles_total=sizing.n_paneles,
            panel=panel_obj,
            inversor=sizing.inversor,
            t_min_c=10
        )

        print("DEBUG STRINGS:", strings)

        if not strings["ok"]:
            raise ValueError(strings.get("error", "Error en cálculo de strings"))

        # Inyectar strings
        paneles.strings = strings

        # Actualizar array si existe
        if hasattr(paneles, "array"):
            paneles.array.n_strings_total = strings["n_strings"]

        # ==================================================
        # PARAMETROS ELECTRICOS
        # ==================================================
        inst = getattr(datos, "electrico", None) or getattr(datos, "instalacion_electrica", None)

        if inst is None:
            raise ValueError("No existe instalacion_electrica en datos")

        if isinstance(inst, dict):
            vac = inst.get("vac")
            fases = inst.get("fases", 1)
            fp = inst.get("fp", 1.0)
            dist_dc_m = inst.get("dist_dc_m")
            dist_ac_m = inst.get("dist_ac_m")
        else:
            vac = getattr(inst, "vac", None)
            fases = getattr(inst, "fases", 1)
            fp = getattr(inst, "fp", 1.0)
            dist_dc_m = getattr(inst, "dist_dc_m", None)
            dist_ac_m = getattr(inst, "dist_ac_m", None)

        print("DEBUG INSTALACION:")
        print(" - vac:", vac)
        print(" - fases:", fases)
        print(" - fp:", fp)
        print(" - dist_dc_m:", dist_dc_m)
        print(" - dist_ac_m:", dist_ac_m)

        if vac is None:
            raise ValueError("Falta 'vac' en instalacion_electrica")

        if dist_dc_m is None or dist_ac_m is None:
            raise ValueError("Faltan distancias en instalacion_electrica")

        # ==================================================
        # CORRIENTES
        # ==================================================
        corrientes_input = CorrientesInput(
            paneles=paneles,
            kw_ac=sizing.kw_ac,
            vac=vac,
            fases=fases,
            fp=fp,
        )

        corrientes = calcular_corrientes(corrientes_input)

        print("DEBUG CORRIENTES:", corrientes)

        if not corrientes.ok:
            return ResultadoElectrico.build(
                paneles=paneles,
                corrientes=corrientes,
                conductores=_conductores_error("Corrientes inválidas"),
                protecciones=_protecciones_error("Corrientes inválidas"),
            )

        # ==================================================
        # CONDUCTORES
        # ==================================================
        tramos = calcular_conductores(
            corrientes=corrientes,
            vmp_dc=paneles.array.vdc_nom,
            vac=vac,
            dist_dc_m=dist_dc_m,
            dist_ac_m=dist_ac_m,
            fases=fases,
        )

        conductores = ResultadoConductores.build(tramos)

        print("DEBUG CONDUCTORES:", conductores)

        if not conductores.ok:
            return ResultadoElectrico.build(
                paneles=paneles,
                corrientes=corrientes,
                conductores=conductores,
                protecciones=_protecciones_error("Conductores inválidos"),
            )

        # ==================================================
        # PROTECCIONES
        # ==================================================
        entrada_prot = EntradaProtecciones(
            corrientes=corrientes,
            n_strings=paneles.array.n_strings_total,
        )

        protecciones = calcular_protecciones(entrada_prot)

        print("DEBUG PROTECCIONES:", protecciones)

        # ==================================================
        # RESULTADO FINAL
        # ==================================================
        print("⚡ [ELECTRICAL] OK")

        return ResultadoElectrico.build(
            paneles=paneles,
            corrientes=corrientes,
            conductores=conductores,
            protecciones=protecciones,
        )

    except Exception as e:

        print("🔥 ERROR ELECTRICAL:", str(e))

        return ResultadoElectrico.build(
            paneles=paneles,
            corrientes=_corrientes_error(str(e)),
            conductores=_conductores_error(str(e)),
            protecciones=_protecciones_error(str(e)),
        )


# ==================================================
# HELPERS DE ERROR
# ==================================================

def _corrientes_error(msg: str):
    from electrical.conductores.resultado_corriente import ResultadoCorrientes
    return ResultadoCorrientes.error(msg)


def _conductores_error(msg: str):
    from electrical.conductores.resultado_conductores import ResultadoConductores
    return ResultadoConductores.error(msg)


def _protecciones_error(msg: str):
    from electrical.protecciones.resultado_protecciones import ResultadoProtecciones
    return ResultadoProtecciones.error(msg)
