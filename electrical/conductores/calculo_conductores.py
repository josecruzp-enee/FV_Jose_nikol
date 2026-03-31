from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .factores_nec import ampacidad_ajustada_nec, AmpacidadResultado
from .caida_voltaje import caida_tension_pct, ajustar_calibre_por_vd, Conductor
from .tablas_conductores import tabla_base_conductores
from .corrientes import ResultadoCorrientes


# ==========================================================
# RESULTADO
# ==========================================================

@dataclass(frozen=True)
class ResultadoConductor:

    nombre: str

    i_diseno_a: float
    v_base_v: float
    l_m: float

    calibre: str
    material: str

    ampacidad_base_a: float
    ampacidad_ajustada_a: float

    fac_temp: float
    fac_ccc: float

    vd_pct: float
    vd_obj_pct: float

    cumple_ampacidad: bool
    cumple_vd: bool
    cumple: bool

    r_ohm_km: float
    agotado_vd: bool


# ==========================================================
# MOTOR BASE
# ==========================================================

def tramo_conductor(
    *,
    nombre: str,
    i_diseno_a: float,
    v_base_v: float,
    l_m: float,
    vd_obj_pct: float,
    material: str = "Cu",
    n_hilos: int = 2,
    t_amb_c: float = 30.0,
    ccc: int = 2,
    aplicar_derating: bool = True,
) -> ResultadoConductor:

    tabla: List[Conductor] = list(tabla_base_conductores(material))

    # 1. Ampacidad
    for t in tabla:

        amp_base = t.amp_a

        amp_res: AmpacidadResultado = ampacidad_ajustada_nec(
            amp_base,
            t_amb_c,
            ccc,
            aplicar=aplicar_derating,
        )

        if i_diseno_a <= amp_res.ampacidad_ajustada:
            awg = t.awg
            break
    else:
        awg = tabla[-1].awg

    # 2. VD
    awg = ajustar_calibre_por_vd(
        tabla,
        awg=awg,
        i_a=i_diseno_a,
        v_v=v_base_v,
        l_m=l_m,
        vd_obj_pct=vd_obj_pct,
        n_hilos=n_hilos,
    )

    # 3. Resultado
    fila = next(t for t in tabla if t.awg == awg)

    amp_base = fila.amp_a
    r = fila.r_ohm_km

    amp_res = ampacidad_ajustada_nec(
        amp_base,
        t_amb_c,
        ccc,
        aplicar=aplicar_derating,
    )

    vd = caida_tension_pct(
        v=v_base_v,
        i=i_diseno_a,
        l_m=l_m,
        r_ohm_km=r,
        n_hilos=n_hilos,
    )

    cumple_amp = amp_res.ampacidad_ajustada >= i_diseno_a
    cumple_vd = vd <= vd_obj_pct

    return ResultadoConductor(
        nombre=nombre,
        i_diseno_a=i_diseno_a,
        v_base_v=v_base_v,
        l_m=l_m,
        calibre=awg,
        material=material,
        ampacidad_base_a=amp_base,
        ampacidad_ajustada_a=amp_res.ampacidad_ajustada,
        fac_temp=amp_res.factor_temperatura,
        fac_ccc=amp_res.factor_ccc,
        vd_pct=vd,
        vd_obj_pct=vd_obj_pct,
        cumple_ampacidad=cumple_amp,
        cumple_vd=cumple_vd,
        cumple=(cumple_amp and cumple_vd),
        r_ohm_km=r,
        agotado_vd=(awg == tabla[-1].awg and not cumple_vd),
    )


# ==========================================================
# RESULTADO AGRUPADO (SIN DC GLOBAL)
# ==========================================================

@dataclass(frozen=True)
class TramosFV:

    dc_mppt: List[ResultadoConductor]  # 🔥 cada MPPT su cable
    ac: ResultadoConductor


# ==========================================================
# ORQUESTADOR FV (CORRECTO)
# ==========================================================

def dimensionar_tramos_fv(
    *,
    corrientes: ResultadoCorrientes,
    vmp_dc: float,
    vac: float,
    dist_dc_m: float,
    dist_ac_m: float,
    material_dc: str = "Cu",
    material_ac: str = "Cu",
    vd_obj_dc_pct: float = 2.0,
    vd_obj_ac_pct: float = 2.0,
    fases: int = 1,
) -> TramosFV:

    # ==================================================
    # DC POR MPPT (🔥 CORRECTO)
    # ==================================================
    tramos_mppt = []

    for i, mppt_corr in enumerate(getattr(corrientes, "mppt_detalle", [])):

        tramo = tramo_conductor(
            nombre=f"DC_MPPT_{i+1}",
            i_diseno_a=mppt_corr.i_diseno_a,
            v_base_v=vmp_dc if vmp_dc > 0 else 1.0,
            l_m=dist_dc_m,
            vd_obj_pct=vd_obj_dc_pct,
            material=material_dc,
            n_hilos=2,
        )

        tramos_mppt.append(tramo)

    # ==================================================
    # AC
    # ==================================================
    n_hilos_ac = 3 if fases == 3 else 2

    tramo_ac = tramo_conductor(
        nombre="AC_INV_A_TABLERO",
        i_diseno_a=corrientes.ac.i_diseno_a,
        v_base_v=vac if vac > 0 else 1.0,
        l_m=dist_ac_m,
        vd_obj_pct=vd_obj_ac_pct,
        material=material_ac,
        n_hilos=n_hilos_ac,
    )

    # ==================================================
    # RESULTADO FINAL
    # ==================================================
    return TramosFV(
        dc_mppt=tramos_mppt,
        ac=tramo_ac,
    )
