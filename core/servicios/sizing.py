from __future__ import annotations

"""
Servicio de sizing FV (REFORMADO + MULTI-ZONA + CONTROL DE MODO)
"""

from typing import Any, Dict, Optional, List
from math import ceil

from core.dominio.modelo import Datosproyecto
from core.dominio.contrato import ResultadoSizing, MesEnergia

from core.servicios.consumo import consumo_anual_kwh

from electrical.catalogos import get_panel, get_inversor
from electrical.inversor.orquestador_inversor import ejecutar_inversor_desde_sizing
from electrical.paneles.dimensionado_paneles import dimensionar_paneles


# ==========================================================
# HELPERS
# ==========================================================

def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, float(x)))


def _leer_equipos(p):
    """
    Soporta dict (legacy) y dataclass Equipos (nuevo)
    PERO SIEMPRE devuelve objeto con atributos
    """

    eq = getattr(p, "equipos", None)

    if eq is None:
        raise ValueError("p.equipos no definido")

    # -----------------------------
    # NUEVO: DATACLASS / OBJETO
    # -----------------------------
    if hasattr(eq, "panel_id") and hasattr(eq, "inversor_id"):
        return eq

    # -----------------------------
    # LEGACY: DICT → convertir a objeto
    # -----------------------------
    if isinstance(eq, dict):
        panel_id = eq.get("panel_id")
        inversor_id = eq.get("inversor_id")

        if not panel_id or not inversor_id:
            raise ValueError("Datos incompletos en p.equipos")

        return type("EquiposTmp", (), {
            "panel_id": panel_id,
            "inversor_id": inversor_id,
        })()

    raise ValueError("Formato inválido en p.equipos")


def _panel_id(eq) -> str:
    pid = str(getattr(eq, "panel_id", "")).strip()

    if not pid:
        raise ValueError("panel_id no definido en equipos")

    return pid


def _inv_id(eq) -> Optional[str]:
    v = getattr(eq, "inversor_id", None)

    if v is None:
        return None

    v = str(v).strip()
    return v if v else None


# ==========================================================
# PANEL + CONFIG
# ==========================================================

def _leer_panel_y_config(p: Datosproyecto):

    eq = _leer_equipos(p)

    panel = get_panel(_panel_id(eq))

    if panel is None:
        raise ValueError("Panel no encontrado en catálogo")

    panel_w = float(getattr(panel, "pmax_w", 0.0))

    if panel_w <= 0:
        raise ValueError("Potencia de panel inválida")

    dc_ac_obj = _clamp(
        float(getattr(eq, "sobredimension_dc_ac", 1.20)),
        1.0,
        2.0,
    )

    return panel, dc_ac_obj, eq


# ==========================================================
# CONSUMO
# ==========================================================

def _leer_consumo(p: Datosproyecto):

    consumo_12m = list(getattr(p, "consumo_12m", []) or [])

    if len(consumo_12m) != 12:
        raise ValueError("consumo_12m debe tener 12 valores")

    consumo_12m = [float(x or 0.0) for x in consumo_12m]

    consumo_anual = consumo_anual_kwh(consumo_12m)

    return consumo_anual
# ==========================================================
# SIZING INPUT
# ==========================================================

def _leer_sizing_input(p: Datosproyecto):

    sf = getattr(p, "sistema_fv", {}) or {}

    # 🔥 SI ES MULTIZONA → NO USAR sizing_input
    if sf.get("usar_zonas"):
        return None, None

    si = sf.get("sizing_input", {}) or {}

    modo = str(si.get("modo", "consumo")).strip().lower()
    valor = si.get("valor", None)

    if valor is None:
        raise ValueError("sizing_input sin valor")

    return modo, valor
    # ======================================================
    # MODELO LEGACY (FALLBACK)
    # ======================================================
    si = sf.get("sizing_input", {}) or {}

    modo = str(si.get("modo", "consumo")).strip().lower()
    valor = si.get("valor", None)

    if valor is None:
        raise ValueError("sizing_input sin valor")

    return modo, valor

# ==========================================================
# GENERADOR FV (MODO NORMAL)
# ==========================================================

def _dimensionar_generador(panel, modo, valor, consumo_anual):

    energia_por_kwp_anual = 1500.0

    if modo == "consumo":
        cobertura = _clamp(float(valor) / 100.0, 0.1, 2.0)
        kwp_obj = (consumo_anual * cobertura) / energia_por_kwp_anual

    elif modo == "area":
        area = float(valor)
        area_util = area * 0.75
        kwp_obj = area_util / 5.0

    elif modo == "potencia":
        kwp_obj = float(valor)

    elif modo == "manual":

        n_paneles = int(valor)

        if n_paneles <= 0:
            raise ValueError("Número de paneles inválido")

        pdc_kw = (n_paneles * panel.pmax_w) / 1000
        return n_paneles, pdc_kw

    else:
        raise ValueError(f"Modo inválido: {modo}")

    n_paneles = int(ceil((kwp_obj * 1000) / panel.pmax_w))
    pdc_kw = (n_paneles * panel.pmax_w) / 1000

    return n_paneles, pdc_kw


# ==========================================================
# MULTI-ZONA
# ==========================================================

def _dimensionar_por_zonas(panel, zonas):

    total_paneles = 0
    total_pdc = 0

    for i, z in enumerate(zonas):

        modo = str(z.get("modo", "")).strip().lower()

        # ==================================================
        # NORMALIZAR ACENTOS
        # ==================================================
        modo = modo.replace("á", "a")

        # ==================================================
        # MODO ÁREA
        # ==================================================
        if modo == "area":

            area = z.get("area")

            if area is None:
                raise ValueError(f"Zona {i+1}: área no definida")

            area = float(area)

            if area <= 0:
                raise ValueError(f"Zona {i+1}: área inválida")

            area_util = area * 0.75
            kwp_obj = area_util / 5.0

            from electrical.paneles.entrada_panel import EntradaPaneles

            entrada = EntradaPaneles(
                panel=panel,
                inversor=None,
                modo="area",
                pdc_kw_objetivo=kwp_obj,
                t_min_c=10,
                t_oper_c=50,
            )

            res = dimensionar_paneles(entrada)

            if not res.ok:
                raise ValueError(f"Zona {i+1}: {res.errores}")

            total_paneles += res.n_paneles
            total_pdc += res.pdc_kw

        # ==================================================
        # MODO PANELES
        # ==================================================
        elif modo == "paneles":

            n_paneles = z.get("n_paneles")

            if n_paneles is None:
                raise ValueError(f"Zona {i+1}: n_paneles no definido")

            n_paneles = int(n_paneles)

            if n_paneles <= 0:
                raise ValueError(f"Zona {i+1}: número de paneles inválido")

            pdc_kw = (n_paneles * panel.pmax_w) / 1000

            total_paneles += n_paneles
            total_pdc += pdc_kw

        # ==================================================
        # ERROR
        # ==================================================
        else:
            raise ValueError(f"Zona {i+1}: modo inválido ({modo})")

    if total_paneles <= 0:
        raise ValueError("No se pudo dimensionar ninguna zona")

    return total_paneles, total_pdc
# ==========================================================
# INVERSOR
# ==========================================================

def _seleccionar_inversor(pdc, dc_ac_obj, eq):

    resultado = ejecutar_inversor_desde_sizing(
        pdc_kw=pdc,
        dc_ac_obj=dc_ac_obj,
        inversor_id_forzado=_inv_id(eq),
    )

    inv_id = resultado["inversor_id"]
    inv = get_inversor(inv_id)

    kw_ac = float(resultado.get("kw_ac", 0))
    n_inv = int(resultado.get("n_inversores", 1))

    if kw_ac <= 0:
        raise ValueError("kw_ac inválido")

    pac_total = float(resultado.get("kw_ac_total", kw_ac * n_inv))

    dc_ac_ratio = pdc / pac_total

    if not (0.9 <= dc_ac_ratio <= 1.6):
        print(f"⚠ DC/AC fuera de rango recomendado: {dc_ac_ratio:.2f}")

    return inv, kw_ac, n_inv, pac_total, resultado.get("sugerencias", [])


# ==========================================================
# API PRINCIPAL
# ==========================================================

def calcular_sizing_unificado(p: Datosproyecto) -> ResultadoSizing:

    # ======================================================
    # 1. PANEL + CONFIG
    # ======================================================
    panel, dc_ac_obj, eq = _leer_panel_y_config(p)

    # ======================================================
    # 2. CONSUMO
    # ======================================================
    consumo_anual = _leer_consumo(p)

    # ======================================================
    # 3. SISTEMA FV
    # ======================================================
    sf = getattr(p, "sistema_fv", {}) or {}

    # 🔥 fuente única de verdad
    usar_zonas = sf.get("usar_zonas", False)

    # ======================================================
    # 4. FLUJO DE DIMENSIONAMIENTO
    # ======================================================
    if usar_zonas:

        zonas = sf.get("zonas", [])

        if not zonas:
            raise ValueError("Multizona activado pero sin zonas")

        n_paneles, pdc = _dimensionar_por_zonas(
            panel,
            zonas
        )

    else:

        modo, valor = _leer_sizing_input(p)

        # 🔥 protección
        if modo == "multizona":
            raise ValueError("Estado inconsistente: multizona sin usar_zonas")

        n_paneles, pdc = _dimensionar_generador(
            panel,
            modo,
            valor,
            consumo_anual
        )

    # ======================================================
    # 5. INVERSOR
    # ======================================================
    inv, kw_ac, n_inv, pac_total, sugerencias = _seleccionar_inversor(
        pdc,
        dc_ac_obj,
        eq
    )

    # ======================================================
    # 6. DERIVADOS
    # ======================================================
    paneles_por_inversor = ceil(n_paneles / n_inv)

    dc_ac_ratio = pdc / pac_total

    energia_12m: List[MesEnergia] = []

    # ======================================================
    # 7. RESULTADO
    # ======================================================
    return ResultadoSizing(
        n_paneles=n_paneles,
        kwp_dc=round(pdc, 3),
        pdc_kw=round(pdc, 3),

        kw_ac=pac_total,
        kw_ac_total=pac_total,
        n_inversores=n_inv,
        paneles_por_inversor=paneles_por_inversor,

        inversor=inv,
        panel=panel,
        dc_ac_ratio=round(dc_ac_ratio, 3),

        energia_12m=energia_12m,
    )
