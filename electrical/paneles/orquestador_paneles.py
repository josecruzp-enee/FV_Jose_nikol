from __future__ import annotations
from typing import Dict, List, Optional

from electrical.modelos.paneles import PanelSpec
from electrical.modelos.inversor import InversorSpec

from .calculo_de_strings import calcular_strings_fv
from .validacion_strings import (
    validar_inversor,
    validar_panel,
    validar_parametros_generales,
)


# ================================
# MOTOR ORQUESTADO
# ================================

def ejecutar_calculo_strings(
    *,
    n_paneles_total: Optional[int],
    panel: PanelSpec,
    inversor: InversorSpec,
    t_min_c: float,
    dos_aguas: bool = False,
    objetivo_dc_ac: float | None = None,
    pdc_kw_objetivo: float | None = None,
    t_oper_c: float | None = None,
) -> Dict:

    errores: List[str] = []
    warnings: List[str] = []

    if n_paneles_total is None or n_paneles_total <= 0:
        return {"ok": False, "errores": ["n_paneles_total inválido"], "warnings": []}

    if not isinstance(panel, PanelSpec):
        raise TypeError("panel debe ser PanelSpec")

    if not isinstance(inversor, InversorSpec):
        raise TypeError("inversor debe ser InversorSpec")

    t_oper = float(t_oper_c) if t_oper_c is not None else 55.0

    e, w = validar_panel(panel)
    errores += e
    warnings += w

    e, w = validar_inversor(inversor)
    errores += e
    warnings += w

    e, w = validar_parametros_generales(n_paneles_total, t_min_c)
    errores += e
    warnings += w

    if errores:
        return {
            "ok": False,
            "errores": errores,
            "warnings": warnings,
        }

    resultado = calcular_strings_fv(
        n_paneles_total=n_paneles_total,
        panel=panel,
        inversor=inversor,
        t_min_c=float(t_min_c),
        dos_aguas=bool(dos_aguas),
        objetivo_dc_ac=objetivo_dc_ac,
        pdc_kw_objetivo=pdc_kw_objetivo,
        t_oper_c=t_oper,
    )

    resultado.setdefault("ok", False)
    resultado.setdefault("errores", [])
    resultado.setdefault("warnings", [])

    return resultado


# ================================
# ENTRADA DESDE CORE
# ================================

def ejecutar_paneles_desde_sizing(p, sizing):

    from electrical.catalogos.catalogos import get_panel, get_inversor

    equipos = getattr(p, "equipos", {}) or {}

    panel_id = equipos.get("panel_id")
    inversor_id = equipos.get("inversor_id")

    if not panel_id:
        raise ValueError("Panel no seleccionado")

    if not inversor_id:
        raise ValueError("Inversor no seleccionado")

    panel = get_panel(panel_id)
    inversor = get_inversor(inversor_id)

    return ejecutar_calculo_strings(
        n_paneles_total=sizing.n_paneles,
        panel=panel,
        inversor=inversor,
        t_min_c=float(getattr(p, "t_min_c", 10.0)),
        dos_aguas=bool(getattr(p, "dos_aguas", False)),
        pdc_kw_objetivo=sizing.pdc_kw,
    )
