MODELO_REPORTE = {

    # =========================
    # SISTEMA FV
    # =========================
    "sistema": {
        "potencia_dc": "resultado_proyecto.sizing.kwp_dc",
        "potencia_ac": "resultado_proyecto.sizing.kw_ac",
        "dc_ac_ratio": "resultado_proyecto.sizing.dc_ac_ratio",
    },

    # =========================
    # PANEL
    # =========================
    "panel": {
        "pmax": "resultado_proyecto.paneles.panel.pmax_w",
        "vmp": "resultado_proyecto.paneles.panel.vmp_v",
        "voc": "resultado_proyecto.paneles.panel.voc_v",
    },

    # =========================
    # STRINGS
    # =========================
    "strings": {
        "fuente": "resultado_proyecto.paneles.strings",
        "estructura": [
            "mppt",
            "n_series",
            "vmp_string_v",
            "voc_frio_string_v",
            "imp_string_a",
            "isc_string_a"
        ]
    },

    # =========================
    # ELÉCTRICO
    # =========================
    "electrico": {
        "corrientes": "resultado_proyecto.electrical.corrientes",
        "protecciones": "resultado_proyecto.electrical.protecciones",
        "conductores": "resultado_proyecto.electrical.conductores",
    }

}
