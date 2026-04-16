# reportes/mapa_modelo_electrico.py

MAPA_ELECTRICO = {

    # =========================================
    # STRINGS
    # =========================================
    "strings": {

        "fuente": "resultado.paneles.strings",
        "descripcion": "Configuración de strings del generador fotovoltaico",

        "variables": {

            "mppt": {
                "ruta": "paneles.strings[].mppt",
                "tipo": "int",
                "unidad": None,
                "descripcion": "Identificador del MPPT del inversor",
                "origen": "ResultadoPaneles.StringFV",
                "uso": "Distribución de strings por MPPT en reporte",
                "nivel": "detalle",
                "obligatorio": True
            },

            "n_series": {
                "ruta": "paneles.strings[].n_series",
                "tipo": "int",
                "unidad": "modulos",
                "descripcion": "Número de módulos conectados en serie en el string",
                "origen": "ResultadoPaneles.StringFV",
                "uso": "Configuración eléctrica del generador FV",
                "nivel": "detalle",
                "obligatorio": True
            },

            "vmp_string_v": {
                "ruta": "paneles.strings[].vmp_string_v",
                "tipo": "float",
                "unidad": "V",
                "descripcion": "Voltaje de operación del string (Vmp)",
                "origen": "calculo_strings",
                "uso": "Validación contra rango MPPT del inversor",
                "nivel": "detalle",
                "obligatorio": True
            },

            "voc_frio_string_v": {
                "ruta": "paneles.strings[].voc_frio_string_v",
                "tipo": "float",
                "unidad": "V",
                "descripcion": "Voltaje máximo del string en condición de temperatura mínima",
                "origen": "calculo_termico",
                "uso": "Verificación contra Vdc máximo del inversor",
                "nivel": "detalle",
                "obligatorio": True
            },

            "imp_string_a": {
                "ruta": "paneles.strings[].imp_string_a",
                "tipo": "float",
                "unidad": "A",
                "descripcion": "Corriente de operación del string (Imp)",
                "origen": "panel",
                "uso": "Dimensionamiento de conductores DC",
                "nivel": "detalle",
                "obligatorio": True
            },

            "isc_string_a": {
                "ruta": "paneles.strings[].isc_string_a",
                "tipo": "float",
                "unidad": "A",
                "descripcion": "Corriente de cortocircuito del string (Isc)",
                "origen": "panel",
                "uso": "Selección de protecciones DC",
                "nivel": "detalle",
                "obligatorio": True
            },
        }
    },

    # =========================================
    # RESUMEN ARRAY FV
    # =========================================
    "array": {

        "fuente": "resultado.paneles.array",
        "descripcion": "Parámetros globales del arreglo FV",

        "variables": {

            "n_strings_total": {
                "ruta": "paneles.array.n_strings_total",
                "tipo": "int",
                "unidad": "strings",
                "descripcion": "Número total de strings del sistema",
                "origen": "ResultadoPaneles.ArrayFV",
                "uso": "Resumen del generador FV",
                "nivel": "resumen",
                "obligatorio": True
            },

            "strings_por_mppt": {
                "ruta": "paneles.array.strings_por_mppt",
                "tipo": "int",
                "unidad": "strings",
                "descripcion": "Cantidad de strings conectados por MPPT",
                "origen": "ResultadoPaneles.ArrayFV",
                "uso": "Distribución del sistema en el inversor",
                "nivel": "resumen",
                "obligatorio": True
            },

            "vdc_nom": {
                "ruta": "paneles.array.vdc_nom",
                "tipo": "float",
                "unidad": "V",
                "descripcion": "Voltaje DC nominal del arreglo",
                "origen": "calculo_strings",
                "uso": "Base para dimensionamiento eléctrico",
                "nivel": "resumen",
                "obligatorio": True
            },

            "voc_frio_array_v": {
                "ruta": "paneles.array.voc_frio_array_v",
                "tipo": "float",
                "unidad": "V",
                "descripcion": "Voltaje máximo del arreglo en frío",
                "origen": "calculo_termico",
                "uso": "Verificación de seguridad del sistema",
                "nivel": "resumen",
                "obligatorio": True
            },
        }
    },

    # =========================================
    # CORRIENTES
    # =========================================
    "corrientes": {

        "fuente": "resultado.corrientes",
        "descripcion": "Corrientes calculadas del sistema FV",

        "variables": {

            "panel_i_operacion": {
                "ruta": "corrientes.panel.i_operacion_a",
                "tipo": "float",
                "unidad": "A",
                "descripcion": "Corriente de operación a nivel de panel",
                "origen": "calcular_corrientes",
                "uso": "Base de cálculos eléctricos",
                "nivel": "detalle",
                "obligatorio": True
            },

            "string_i_operacion": {
                "ruta": "corrientes.string.i_operacion_a",
                "tipo": "float",
                "unidad": "A",
                "descripcion": "Corriente de operación del string",
                "origen": "calcular_corrientes",
                "uso": "Dimensionamiento DC",
                "nivel": "detalle",
                "obligatorio": True
            },

            "ac_i_operacion": {
                "ruta": "corrientes.ac.i_operacion_a",
                "tipo": "float",
                "unidad": "A",
                "descripcion": "Corriente en el lado AC del inversor",
                "origen": "calcular_corrientes",
                "uso": "Selección de protecciones AC",
                "nivel": "resumen",
                "obligatorio": True
            },
        }
    },

    # =========================================
    # CONDUCTORES
    # =========================================
    "conductores": {

        "fuente": "resultado.conductores.tramos.dc_mppt",
        "descripcion": "Dimensionamiento de conductores del sistema",

        "variables": {

            "nombre": {
                "ruta": "conductores.tramos.dc_mppt[].nombre",
                "tipo": "str",
                "unidad": None,
                "descripcion": "Identificador del tramo",
                "origen": "dimensionar_tramos_fv",
                "uso": "Referencia en reporte",
                "nivel": "detalle",
                "obligatorio": True
            },

            "calibre": {
                "ruta": "conductores.tramos.dc_mppt[].calibre",
                "tipo": "str",
                "unidad": "AWG/mm2",
                "descripcion": "Calibre del conductor seleccionado",
                "origen": "dimensionar_tramos_fv",
                "uso": "Reporte técnico",
                "nivel": "detalle",
                "obligatorio": True
            },

            "material": {
                "ruta": "conductores.tramos.dc_mppt[].material",
                "tipo": "str",
                "unidad": None,
                "descripcion": "Material del conductor (Cu/Al)",
                "origen": "dimensionar_tramos_fv",
                "uso": "Especificación técnica",
                "nivel": "detalle",
                "obligatorio": True
            },

            "i_diseno_a": {
                "ruta": "conductores.tramos.dc_mppt[].i_diseno_a",
                "tipo": "float",
                "unidad": "A",
                "descripcion": "Corriente de diseño del tramo",
                "origen": "calcular_corrientes",
                "uso": "Verificación de ampacidad",
                "nivel": "detalle",
                "obligatorio": True
            },

            "vd_pct": {
                "ruta": "conductores.tramos.dc_mppt[].vd_pct",
                "tipo": "float",
                "unidad": "%",
                "descripcion": "Caída de voltaje porcentual",
                "origen": "dimensionamiento",
                "uso": "Validación normativa",
                "nivel": "detalle",
                "obligatorio": True
            },

            "cumple": {
                "ruta": "conductores.tramos.dc_mppt[].cumple",
                "tipo": "bool",
                "unidad": None,
                "descripcion": "Indica si el tramo cumple criterios eléctricos",
                "origen": "dimensionamiento",
                "uso": "Conclusión técnica",
                "nivel": "resumen",
                "obligatorio": True
            },
        }
    },

    # =========================================
    # PROTECCIONES
    # =========================================
    "protecciones": {

        "fuente": "resultado.protecciones",
        "descripcion": "Protecciones eléctricas del sistema FV",

        "variables": {

            "breaker_ac": {
                "ruta": "protecciones.ocpd_ac.tamano_a",
                "tipo": "float",
                "unidad": "A",
                "descripcion": "Capacidad del breaker AC",
                "origen": "calcular_protecciones",
                "uso": "Protección del inversor",
                "nivel": "resumen",
                "obligatorio": True
            },

            "ocpd_dc": {
                "ruta": "protecciones.ocpd_dc_array.tamano_a",
                "tipo": "float",
                "unidad": "A",
                "descripcion": "Protección en el lado DC",
                "origen": "calcular_protecciones",
                "uso": "Seguridad del sistema FV",
                "nivel": "resumen",
                "obligatorio": True
            },

            "fusible": {
                "ruta": "protecciones.fusible_string.requerido",
                "tipo": "bool",
                "unidad": None,
                "descripcion": "Indica si se requiere fusible en strings",
                "origen": "criterio_normativo",
                "uso": "Diseño eléctrico",
                "nivel": "resumen",
                "obligatorio": True
            },
        }
    }
}
