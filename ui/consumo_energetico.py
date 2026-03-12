"""
PASO 2 — CONSUMO ENERGÉTICO
FV Engine

Este módulo implementa el segundo paso del wizard de la interfaz de usuario.

OBJETIVO
--------
Capturar y validar el consumo energético del usuario durante los últimos
12 meses junto con los parámetros de facturación eléctrica.

Este módulo pertenece a la capa:

    UI / Presentation Layer


FRONTERA DEL MÓDULO
-------------------

Entrada:
    WizardCtx (estado global del wizard)

Salida:
    ctx.consumo actualizado


DEPENDENCIAS PERMITIDAS
-----------------------

streamlit
pandas
core.servicios.analisis_cobertura


DEPENDENCIAS PROHIBIDAS
-----------------------

Este módulo NO puede importar:

    electrical.*
    paneles.*
    nec.*
    finanzas.*

La UI no realiza cálculos eléctricos ni dimensionamiento.


RESPONSABILIDADES
-----------------

Este módulo se encarga de:

    1. Capturar consumo mensual (12 meses)
    2. Capturar tarifa eléctrica
    3. Capturar cargos fijos
    4. Validar datos ingresados
    5. Mostrar métricas de consumo
    6. Ejecutar análisis exploratorio de cobertura FV
    7. Mostrar gráfica Demanda vs Generación FV


NO ES RESPONSABLE DE

    dimensionamiento FV
    cálculo de strings
    cálculo energético real
    cálculo NEC
    cálculos financieros

Estos cálculos pertenecen al motor FV.


ENTRADA DEL MÓDULO
------------------

ctx : WizardCtx

El módulo utiliza principalmente:

ctx.consumo


ESTRUCTURA DE ctx.consumo
-------------------------

ctx.consumo = {

    "kwh_12m": list[float],      # consumo mensual (12 valores)

    "cargos_fijos_L_mes": float, # cargo fijo factura

    "tarifa_energia_L_kwh": float, # tarifa variable energía

    "fuente": str                # manual | recibo | csv
}


VARIABLES INTERNAS IMPORTANTES
------------------------------

_MESES : list[str]

Lista de meses usada para:

    UI
    tablas
    gráficos


kwh : list[float]

Vector temporal usado para capturar el consumo mensual.


total : float

Consumo total anual.


prom : float

Consumo promedio mensual.


energia_mensual_fv : list[float]

Vector temporal usado únicamente para visualización
de la gráfica Demanda vs FV.


FUNCIONES DEL MÓDULO
--------------------


render(ctx)

    Función principal del paso del wizard.

    Responsabilidades:

        - renderizar inputs de consumo
        - capturar valores
        - actualizar ctx.consumo
        - mostrar métricas
        - ejecutar análisis de cobertura
        - mostrar gráfica comparativa

    Entrada:

        ctx : WizardCtx

    Salida:

        ctx.consumo actualizado



render_analisis_cobertura(ctx)

    Ejecuta un análisis exploratorio de diferentes
    tamaños de sistema FV.

    Utiliza:

        core.servicios.analisis_cobertura


    Entrada:

        consumo_anual
        tarifa_energia

    Salida:

        tabla de escenarios FV



render_demanda_vs_fv(ctx, energia_mensual_kwh)

    Muestra una gráfica comparando:

        demanda mensual
        generación FV estimada


    Entrada:

        ctx
        energia_mensual_kwh


    Salida:

        gráfico streamlit



validar(ctx)

    Valida los datos ingresados por el usuario.

    Validaciones:

        1. Deben existir 12 meses
        2. No se permiten valores negativos
        3. Al menos un mes debe tener consumo > 0


    Entrada:

        ctx : WizardCtx

    Salida:

        (bool, list[str])

        bool        → paso válido
        list[str]   → lista de errores



SALIDA DEL MÓDULO
-----------------

El módulo actualiza:

ctx.consumo


Ejemplo:

ctx.consumo = {

    "kwh_12m": [
        820, 790, 860, 910, 950, 980,
        1020, 1000, 940, 890, 860, 830
    ],

    "cargos_fijos_L_mes": 250.0,

    "tarifa_energia_L_kwh": 6.75,

    "fuente": "manual"
}


FLUJO DENTRO DEL WIZARD
-----------------------

Paso 1

    datos_cliente

        ↓

Paso 2

    consumo_energetico

        ↓

Paso 3

    dimensionamiento FV


El consumo capturado en este módulo es utilizado por:

    core.orquestador_estudio

para calcular:

    sizing
    producción energética
    dimensionamiento eléctrico
    análisis financiero
"""
