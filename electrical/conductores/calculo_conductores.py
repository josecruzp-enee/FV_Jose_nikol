from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from .factores_nec import (
    ampacidad_ajustada_nec,
    AmpacidadResultado,
)
from .caida_voltaje import (
    caida_tension_pct,
    ajustar_calibre_por_vd,
    Conductor,
)
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

    tabla: List[Conductor] = list(
        tabla_base_conductores(material)
    )

    if not tabla:
        raise ValueError(
            f"No existe tabla de conductores para material {material}"
        )

    if i_diseno_a < 0:
        raise ValueError(
            "i_diseno_a no puede ser negativa"
        )

    if v_base_v <= 0:
        raise ValueError(
            "v_base_v debe ser mayor que cero"
        )

    if l_m < 0:
        raise ValueError(
            "l_m no puede ser negativa"
        )

    if vd_obj_pct <= 0:
        raise ValueError(
            "vd_obj_pct debe ser mayor que cero"
        )

    # ======================================================
    # 1. SELECCIÓN POR AMPACIDAD
    # ======================================================

    awg = tabla[-1].awg

    for conductor in tabla:

        amp_base = conductor.amp_a

        amp_res: AmpacidadResultado = (
            ampacidad_ajustada_nec(
                amp_base,
                t_amb_c,
                ccc,
                aplicar=aplicar_derating,
            )
        )

        if (
            i_diseno_a
            <= amp_res.ampacidad_ajustada
        ):
            awg = conductor.awg
            break

    # ======================================================
    # 2. VERIFICACIÓN Y AJUSTE POR CAÍDA DE VOLTAJE
    # ======================================================

    awg = ajustar_calibre_por_vd(
        tabla,
        awg=awg,
        i_a=i_diseno_a,
        v_v=v_base_v,
        l_m=l_m,
        vd_obj_pct=vd_obj_pct,
        n_hilos=n_hilos,
    )

    # ======================================================
    # 3. CONDUCTOR FINAL
    # ======================================================

    fila = next(
        conductor
        for conductor in tabla
        if conductor.awg == awg
    )

    amp_base = fila.amp_a
    resistencia = fila.r_ohm_km

    amp_res = ampacidad_ajustada_nec(
        amp_base,
        t_amb_c,
        ccc,
        aplicar=aplicar_derating,
    )

    vd_pct = caida_tension_pct(
        v=v_base_v,
        i=i_diseno_a,
        l_m=l_m,
        r_ohm_km=resistencia,
        n_hilos=n_hilos,
    )

    cumple_ampacidad = (
        amp_res.ampacidad_ajustada
        >= i_diseno_a
    )

    cumple_vd = (
        vd_pct
        <= vd_obj_pct
    )

    es_ultimo_calibre = (
        awg == tabla[-1].awg
    )

    return ResultadoConductor(
        nombre=nombre,
        i_diseno_a=i_diseno_a,
        v_base_v=v_base_v,
        l_m=l_m,
        calibre=awg,
        material=material,
        ampacidad_base_a=amp_base,
        ampacidad_ajustada_a=(
            amp_res.ampacidad_ajustada
        ),
        fac_temp=(
            amp_res.factor_temperatura
        ),
        fac_ccc=(
            amp_res.factor_ccc
        ),
        vd_pct=vd_pct,
        vd_obj_pct=vd_obj_pct,
        cumple_ampacidad=cumple_ampacidad,
        cumple_vd=cumple_vd,
        cumple=(
            cumple_ampacidad
            and cumple_vd
        ),
        r_ohm_km=resistencia,
        agotado_vd=(
            es_ultimo_calibre
            and not cumple_vd
        ),
    )


# ==========================================================
# RESULTADO AGRUPADO
# ==========================================================

@dataclass(frozen=True)
class TramosFV:
    dc_mppt: List[ResultadoConductor]
    ac_inversores: List[ResultadoConductor]
    ac_principal: ResultadoConductor

    # Tramo DC con mayor corriente de diseño.
    # El PDF debe leer este resultado sin recalcularlo.
    dc_mppt_critico: Optional[ResultadoConductor] = None


# ==========================================================
# DIMENSIONAMIENTO DC POR MPPT
# ==========================================================

def _dimensionar_tramos_mppt(
    *,
    corrientes: ResultadoCorrientes,
    vmp_dc: float,
    dist_dc_m: float,
    material_dc: str,
    vd_obj_dc_pct: float,
) -> List[ResultadoConductor]:

    tramos_mppt: List[ResultadoConductor] = []

    mppt_detalle = (
        getattr(
            corrientes,
            "mppt_detalle",
            [],
        )
        or []
    )

    for indice, mppt_corr in enumerate(
        mppt_detalle,
        start=1,
    ):

        tramo = tramo_conductor(
            nombre=f"DC_MPPT_{indice}",
            i_diseno_a=float(
                getattr(
                    mppt_corr,
                    "i_diseno_a",
                    0.0,
                )
                or 0.0
            ),
            v_base_v=vmp_dc,
            l_m=dist_dc_m,
            vd_obj_pct=vd_obj_dc_pct,
            material=material_dc,
            n_hilos=2,
        )

        tramos_mppt.append(tramo)

    return tramos_mppt


# ==========================================================
# IDENTIFICAR MPPT CRÍTICO
# ==========================================================

def _obtener_tramo_mppt_critico(
    tramos_mppt: List[ResultadoConductor],
) -> Optional[ResultadoConductor]:
    """
    Identifica el tramo MPPT con mayor corriente de diseño.

    Esta decisión pertenece al motor eléctrico. El reporte
    solamente debe presentar el resultado obtenido.
    """

    if not tramos_mppt:
        return None

    return max(
        tramos_mppt,
        key=lambda tramo: tramo.i_diseno_a,
    )


# ==========================================================
# DIMENSIONAMIENTO AC POR INVERSOR
# ==========================================================

def _dimensionar_tramos_ac_inversores(
    *,
    corrientes: ResultadoCorrientes,
    vac: float,
    dist_ac_m: float,
    material_ac: str,
    vd_obj_ac_pct: float,
    n_hilos_ac: int,
) -> List[ResultadoConductor]:

    tramos_ac: List[ResultadoConductor] = []

    inversores_detalle = (
        getattr(
            corrientes,
            "inversores_detalle",
            [],
        )
        or []
    )

    for indice, inv_corr in enumerate(
        inversores_detalle,
        start=1,
    ):

        tramo = tramo_conductor(
            nombre=(
                f"AC_INV_{indice}_A_TABLERO"
            ),
            i_diseno_a=float(
                getattr(
                    inv_corr,
                    "i_diseno_a",
                    0.0,
                )
                or 0.0
            ),
            v_base_v=vac,
            l_m=dist_ac_m,
            vd_obj_pct=vd_obj_ac_pct,
            material=material_ac,
            n_hilos=n_hilos_ac,
        )

        tramos_ac.append(tramo)

    return tramos_ac


# ==========================================================
# DIMENSIONAMIENTO AC PRINCIPAL
# ==========================================================

def _dimensionar_tramo_ac_principal(
    *,
    corrientes: ResultadoCorrientes,
    vac: float,
    dist_ac_m: float,
    material_ac: str,
    vd_obj_ac_pct: float,
    n_hilos_ac: int,
) -> ResultadoConductor:

    ac_total = getattr(
        corrientes,
        "ac_total",
        None,
    )

    if ac_total is None:
        ac_total = getattr(
            corrientes,
            "ac",
            None,
        )

    if ac_total is None:
        raise ValueError(
            "No existe corriente AC total"
        )

    return tramo_conductor(
        nombre="AC_TABLERO_A_INTERCONEXION",
        i_diseno_a=float(
            getattr(
                ac_total,
                "i_diseno_a",
                0.0,
            )
            or 0.0
        ),
        v_base_v=vac,
        l_m=dist_ac_m,
        vd_obj_pct=vd_obj_ac_pct,
        material=material_ac,
        n_hilos=n_hilos_ac,
    )


# ==========================================================
# ORQUESTADOR FV
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

    if corrientes is None:
        raise ValueError(
            "corrientes no está disponible"
        )

    if vmp_dc <= 0:
        raise ValueError(
            "vmp_dc debe ser mayor que cero"
        )

    if vac <= 0:
        raise ValueError(
            "vac debe ser mayor que cero"
        )

    if dist_dc_m < 0:
        raise ValueError(
            "dist_dc_m no puede ser negativa"
        )

    if dist_ac_m < 0:
        raise ValueError(
            "dist_ac_m no puede ser negativa"
        )

    if fases not in (1, 3):
        raise ValueError(
            "fases debe ser 1 o 3"
        )

    # ======================================================
    # DC POR MPPT
    # ======================================================

    tramos_mppt = _dimensionar_tramos_mppt(
        corrientes=corrientes,
        vmp_dc=vmp_dc,
        dist_dc_m=dist_dc_m,
        material_dc=material_dc,
        vd_obj_dc_pct=vd_obj_dc_pct,
    )

    # Esta selección se realiza dentro del motor eléctrico.
    tramo_mppt_critico = (
        _obtener_tramo_mppt_critico(
            tramos_mppt
        )
    )

    # ======================================================
    # AC
    # ======================================================
    # Se conserva temporalmente la lógica existente.
    # La formulación trifásica de caída de tensión deberá
    # corregirse posteriormente en caida_voltaje.py.
    # ======================================================

    n_hilos_ac = (
        3
        if fases == 3
        else 2
    )

    tramos_ac_inversores = (
        _dimensionar_tramos_ac_inversores(
            corrientes=corrientes,
            vac=vac,
            dist_ac_m=dist_ac_m,
            material_ac=material_ac,
            vd_obj_ac_pct=vd_obj_ac_pct,
            n_hilos_ac=n_hilos_ac,
        )
    )

    tramo_ac_principal = (
        _dimensionar_tramo_ac_principal(
            corrientes=corrientes,
            vac=vac,
            dist_ac_m=dist_ac_m,
            material_ac=material_ac,
            vd_obj_ac_pct=vd_obj_ac_pct,
            n_hilos_ac=n_hilos_ac,
        )
    )

    # ======================================================
    # RESULTADO FINAL
    # ======================================================

    return TramosFV(
        dc_mppt=tramos_mppt,
        ac_inversores=tramos_ac_inversores,
        ac_principal=tramo_ac_principal,
        dc_mppt_critico=tramo_mppt_critico,
    )
