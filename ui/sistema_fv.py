"""
PASO 3 — SISTEMA FOTOVOLTAICO
FV Engine

Este módulo implementa el tercer paso del wizard de la interfaz
de usuario.

OBJETIVO
--------
Capturar los parámetros técnicos del sistema FV propuesto
que serán utilizados posteriormente por el motor del sistema
para realizar:

    dimensionamiento del sistema
    cálculo energético
    ingeniería eléctrica
    análisis financiero

Este módulo pertenece a la capa:

    UI / Presentation Layer


------------------------------------------------------------
FRONTERA DEL MÓDULO
------------------------------------------------------------

Entrada:

    WizardCtx (estado global del wizard)

Salida:

    ctx.sistema_fv actualizado


------------------------------------------------------------
DEPENDENCIAS PERMITIDAS
------------------------------------------------------------

streamlit
ui.state_helpers


------------------------------------------------------------
DEPENDENCIAS PROHIBIDAS
------------------------------------------------------------

Este módulo NO puede importar:

    electrical.*
    paneles.*
    energia.*
    nec.*
    finanzas.*

La UI no ejecuta cálculos técnicos.


------------------------------------------------------------
RESPONSABILIDADES DEL MÓDULO
------------------------------------------------------------

Este módulo se encarga de:

    1. Definir modo de dimensionamiento del sistema
    2. Capturar parámetros geométricos del arreglo FV
    3. Capturar condiciones de instalación
    4. Guardar configuración en ctx.sistema_fv
    5. Validar coherencia básica de los parámetros


------------------------------------------------------------
NO ES RESPONSABLE DE
------------------------------------------------------------

    cálculo de producción energética
    cálculo de strings
    cálculo eléctrico NEC
    cálculo financiero
    simulación solar

Estos cálculos pertenecen al motor FV.


------------------------------------------------------------
ENTRADA DEL MÓDULO
------------------------------------------------------------

ctx : WizardCtx

El módulo utiliza principalmente:

    ctx.sistema_fv


------------------------------------------------------------
ESTRUCTURA DE ctx.sistema_fv
------------------------------------------------------------

ctx.sistema_fv = {

    # modo de dimensionamiento
    "modo_dimensionado": str
        auto | manual

    "n_paneles_manual": int

    # geometría
    "inclinacion_deg": float
    "azimut_deg": float

    "tipo_superficie": str
        "Un plano"
        "Techo dos aguas"

    "azimut_a_deg": float
    "azimut_b_deg": float

    "reparto_pct_a": float

    # condiciones del sistema
    "sombras_pct": float
    "perdidas_sistema_pct": float
}


------------------------------------------------------------
VARIABLES INTERNAS IMPORTANTES
------------------------------------------------------------

sf : dict

Diccionario local que referencia:

    ctx.sistema_fv


_defaults_sistema_fv()

Define los valores iniciales del sistema FV.


------------------------------------------------------------
FUNCIONES DEL MÓDULO
------------------------------------------------------------


render(ctx)

Función principal del paso del wizard.

Responsabilidades:

    - cargar defaults
    - mostrar modo de dimensionamiento
    - capturar geometría del sistema FV
    - capturar condiciones de instalación

Entrada:

    ctx : WizardCtx

Salida:

    ctx.sistema_fv actualizado


------------------------------------------------------------


_render_modo_dimensionado(sf)

Captura el modo de dimensionamiento del sistema FV.

Opciones:

    Automático
    Manual (definir número de paneles)


Entrada:

    sf : dict


Salida:

    sf actualizado


------------------------------------------------------------


_render_geometria(sf)

Captura la geometría del sistema fotovoltaico.

Opciones de superficie:

    plano único
    techo dos aguas

Parámetros capturados:

    inclinación
    azimut
    reparto de paneles


Entrada:

    sf : dict


Salida:

    sf actualizado


------------------------------------------------------------


_render_condiciones(sf)

Captura condiciones de operación del sistema.

Parámetros:

    sombras
    pérdidas del sistema


Entrada:

    sf : dict


Salida:

    sf actualizado


------------------------------------------------------------


validar(ctx)

Realiza validaciones básicas de coherencia.

Validaciones:

    inclinación válida
    número de paneles válido (modo manual)


Entrada:

    ctx : WizardCtx


Salida:

    (bool, list[str])

    bool        → paso válido
    list[str]   → lista de errores


------------------------------------------------------------
SALIDA DEL MÓDULO
------------------------------------------------------------

El módulo actualiza:

    ctx.sistema_fv


Ejemplo:

ctx.sistema_fv = {

    "modo_dimensionado": "auto",

    "inclinacion_deg": 15,
    "azimut_deg": 180,

    "tipo_superficie": "Un plano (suelo/losa/estructura)",

    "sombras_pct": 5.0,
    "perdidas_sistema_pct": 15.0
}


------------------------------------------------------------
FLUJO DENTRO DEL WIZARD
------------------------------------------------------------

Paso 1

    datos_cliente

        ↓

Paso 2

    consumo_energetico

        ↓

Paso 3

    sistema_fv

        ↓

Paso 4

    selección equipos


Los parámetros capturados en este módulo serán utilizados por:

    core.orquestador_estudio

para ejecutar:

    dimensionamiento del sistema FV
    cálculo energético
    ingeniería eléctrica
    análisis financiero
"""
