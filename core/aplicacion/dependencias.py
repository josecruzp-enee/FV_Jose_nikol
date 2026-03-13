"""
MÓDULO: ADAPTADORES DEL ESTUDIO FV

Este módulo implementa los adaptadores concretos de los puertos
definidos por el orquestador del estudio FV.

Forma parte de la capa de infraestructura dentro del patrón
Ports & Adapters utilizado por FV Engine.

---------------------------------------------------------------------

ARQUITECTURA

UI
↓
core.orquestador_estudio
↓
PUERTOS (interfaces)
↓
ADAPTADORES (este módulo)
↓
DOMINIOS

    sizing
    paneles
    energia
    nec
    finanzas

---------------------------------------------------------------------

RESPONSABILIDAD

Implementar los puertos definidos por el orquestador del estudio
y conectar cada dominio con su motor correspondiente.

Cada adaptador traduce la entrada del sistema hacia el formato
esperado por el dominio.

Este módulo NO contiene lógica de cálculo de ingeniería.

---------------------------------------------------------------------

ADAPTADORES IMPLEMENTADOS

SizingAdapter
    Ejecuta el motor de dimensionamiento del sistema FV.

PanelesAdapter
    Ejecuta el cálculo de configuración de strings.

EnergiaAdapter
    Ejecuta el motor de simulación energética anual.

NECAdapter
    Ejecuta el cálculo de ingeniería eléctrica NEC.

FinanzasAdapter
    Ejecuta el análisis financiero del proyecto.

---------------------------------------------------------------------

FUNCIÓN PRINCIPAL DEL MÓDULO

construir_dependencias() -> DependenciasEstudio

Construye la estructura de dependencias que será utilizada por
el orquestador del estudio.

---------------------------------------------------------------------

ENTRADAS

Cada adaptador recibe según el dominio:

    datos   : DatosProyecto
    sizing  : ResultadoSizing
    strings : ResultadoPaneles
    energia : ResultadoEnergia

---------------------------------------------------------------------

SALIDAS

Cada adaptador devuelve el resultado del dominio correspondiente:

    sizing   → ResultadoSizing
    paneles  → ResultadoPaneles
    energia  → ResultadoEnergia
    nec      → ResultadoNEC
    finanzas → ResultadoFinanzas

---------------------------------------------------------------------

REGLA ARQUITECTÓNICA

Este módulo NO realiza cálculos físicos ni eléctricos.

Su único propósito es conectar los puertos definidos por el core
con las implementaciones concretas de los dominios.
"""

from core.servicios.sizing import calcular_sizing_unificado
from core.servicios.finanzas import ejecutar_finanzas

from electrical.paneles.orquestador_paneles import ejecutar_paneles
from electrical.energia.orquestador_energia import ejecutar_motor_energia
from electrical.energia.contrato import EnergiaInput
from electrical.nec.orquestador_nec import ejecutar_nec
from electrical.energia.irradiancia import hsp_12m_base

from .puertos import (
    PuertoSizing,
    PuertoPaneles,
    PuertoEnergia,
    PuertoNEC,
    PuertoFinanzas,
)

from .orquestador_estudio import DependenciasEstudio


# ==========================================================
# ADAPTADOR: SIZING
# ==========================================================

class SizingAdapter(PuertoSizing):

    def ejecutar(self, datos):
        """
        Ejecuta el motor de dimensionamiento FV.
        """
        return calcular_sizing_unificado(datos)


# ==========================================================
# ADAPTADOR: PANELES
# ==========================================================

# ==========================================================
# ADAPTADOR: PANELES
# ==========================================================

from electrical.paneles.entrada_panel import EntradaPaneles
from electrical.catalogos import get_panel, get_inversor


class PanelesAdapter(PuertoPaneles):

    def ejecutar(self, datos, sizing):
        """
        Ejecuta el cálculo de configuración del generador FV.
        """

        eq = getattr(datos, "equipos", {}) or {}

        panel = get_panel(eq.get("panel_id"))
        inversor = get_inversor(eq.get("inversor_id"))

        if panel is None:
            raise ValueError("Panel no encontrado en catálogo")

        if inversor is None:
            raise ValueError("Inversor no encontrado en catálogo")

        entrada = EntradaPaneles(
            panel=panel,
            inversor=inversor,
            n_paneles_total=sizing.n_paneles,
            n_inversores=sizing.n_inversores,
            t_min_c=10,
            t_oper_c=50,
        )

        return ejecutar_paneles(entrada)


# ==========================================================
# ADAPTADOR: ENERGÍA
# ==========================================================

class EnergiaAdapter(PuertoEnergia):

    def ejecutar(self, datos, sizing, strings):
        """
        Ejecuta el motor de simulación energética anual.
        """

        pdc_instalada_kw = sizing.pdc_kw
        pac_nominal_kw = sizing.kw_ac

        hsp_12m = hsp_12m_base()

        if not hsp_12m:
            raise ValueError(
                "No se encontraron factores mensuales (HSP) en Datosproyecto."
            )

        dias_mes = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

        sf = getattr(datos, "sistema_fv", {}) or {}

        inp = EnergiaInput(
            pdc_instalada_kw=pdc_instalada_kw,
            pac_nominal_kw=pac_nominal_kw,
            hsp_12m=hsp_12m,
            dias_mes=dias_mes,
            factor_orientacion=sf.get("factor_orientacion", 1.0),
            perdidas_dc_pct=sf.get("perdidas_dc_pct", 3.0),
            perdidas_ac_pct=sf.get("perdidas_ac_pct", 2.0),
            sombras_pct=sf.get("sombras_pct", 0.0),
            permitir_curtailment=sf.get("permitir_curtailment", True),
        )

        return ejecutar_motor_energia(inp)


# ==========================================================
# ADAPTADOR: NEC
# ==========================================================

class NECAdapter(PuertoNEC):

    def ejecutar(self, datos, sizing, strings):
        """
        Ejecuta el cálculo de ingeniería eléctrica NEC.
        """

        sf = getattr(datos, "sistema_fv", {}) or {}

        vdc_nom = sf.get("vdc_nom", 600)
        vac_ll = sf.get("vac_ll", 480)
        vac_ln = sf.get("vac_ln", None)
        fases = sf.get("fases", 3)
        fp = sf.get("fp", 1.0)

        strings_list = strings.get("strings", [])

        if strings_list:

            s0 = strings_list[0]

            imp_string = s0.get("imp_a", 0)
            isc_string = s0.get("isc_a", 0)
            strings_por_mppt = s0.get("n_paralelo", 1)

        else:

            imp_string = 0
            isc_string = 0
            strings_por_mppt = 1

        n_strings_total = strings.get("recomendacion", {}).get(
            "n_strings_total", 0
        )

        # ======================================================
        # ENTRADA PARA ORQUESTADOR NEC
        # ======================================================

        entrada_nec = {

            "electrico": {
                "vac_ll": vac_ll,
                "vac_ln": vac_ln,
                "fases": fases,
                "fp": fp,
            },

            "potencia_dc_kw": sizing.pdc_kw,
            "potencia_ac_kw": sizing.kw_ac,

            "vdc_nom": vdc_nom,

            "strings": {
                "imp_string_a": imp_string,
                "isc_string_a": isc_string,
                "strings_por_mppt": strings_por_mppt,
                "n_strings_total": n_strings_total,
            },

            "inversor": {
                "kw_ac": sizing.kw_ac,
                "v_ac_nom_v": vac_ll,
                "fases": fases,
                "fp": fp,
            },
        }

        return ejecutar_nec(entrada_nec, sizing, strings)


# ==========================================================
# ADAPTADOR: FINANZAS
# ==========================================================

class FinanzasAdapter(PuertoFinanzas):

    def ejecutar(self, datos, sizing, energia):
        """
        Ejecuta el motor financiero del proyecto.
        """

        return ejecutar_finanzas(
            datos=datos,
            sizing=sizing,
            energia=energia,
        )


# ==========================================================
# FACTORY DE DEPENDENCIAS
# ==========================================================

def construir_dependencias() -> DependenciasEstudio:
    """
    Construye la estructura completa de dependencias del estudio.

    Esta función es utilizada por el orquestador principal
    del sistema FV para inyectar los motores de cada dominio.
    """

    return DependenciasEstudio(
        sizing=SizingAdapter(),
        paneles=PanelesAdapter(),
        energia=EnergiaAdapter(),
        nec=NECAdapter(),
        finanzas=FinanzasAdapter(),
    )
