# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


# ==========================================================
# MODELO DE ENTRADA
# ==========================================================

@dataclass
class EntradaBateria:
    """
    Entrada única para recomendación, simulación y evaluación
    económica del sistema de baterías.

    No depende de Datosproyecto ni de EnergiaResultado.
    """

    # ======================================================
    # PERFILES ENERGÉTICOS
    # ======================================================

    demanda_24h_kwh: Dict[int, float] | List[float]

    # Puede contener 24 o 8760 valores.
    fv_horaria_kwh: List[float]

    consumo_12m_kwh: List[float]
    energia_fv_util_12m_kwh: List[float]

    # Generación total antes de limitarla por autoconsumo.
    energia_fv_generada_12m_kwh: List[float] = field(
        default_factory=list
    )

    # ======================================================
    # CONFIGURACIÓN TÉCNICA
    # ======================================================

    usar_bateria: bool = False

    factor_aprovechamiento: float = 0.80

    capacidades_comerciales_kwh: List[float] = field(
        default_factory=lambda: [
            5.0,
            10.0,
            15.0,
            20.0,
            25.0,
            40.0,
            50.0,
            
            70.0,
            
            100.0
        ]
    )

    soc_inicial_pct: float = 20.0
    soc_min_pct: float = 20.0
    soc_max_pct: float = 100.0

    eficiencia_ida_vuelta: float = 0.90
    vida_util_bateria_anios: int = 10

    # ======================================================
    # COSTOS
    # ======================================================

    costo_bateria_usd_kwh: float = 200.0
    tipo_cambio_l_usd: float = 26.61

    capex_fv_l: float = 0.0
    tarifa_compra_l_kwh: float = 0.0
    tarifa_inyeccion_l_kwh: float = 2.72
    cargos_fijos_l_mes: float = 0.0
    om_anual_pct: float = 0.0

    # ======================================================
    # FINANCIAMIENTO
    # ======================================================

    modo_financiamiento: str = "contado"
    tasa_anual: float = 0.0
    plazo_anios: int = 0
    porcentaje_financiado: float = 0.0

    # ======================================================
    # PROPIEDADES CALCULADAS
    # ======================================================

    @property
    def consumo_anual_kwh(self) -> float:
        return sum(
            max(0.0, float(valor or 0.0))
            for valor in self.consumo_12m_kwh
        )

    @property
    def costo_bateria_l_kwh(self) -> float:
        return (
            max(0.0, float(self.costo_bateria_usd_kwh))
            * max(0.0, float(self.tipo_cambio_l_usd))
        )

    # ======================================================
    # VALIDACIÓN
    # ======================================================

    def validar(self) -> List[str]:
        errores: List[str] = []

        _validar_perfiles(self, errores)
        _validar_configuracion_tecnica(self, errores)
        _validar_costos(self, errores)
        _validar_financiamiento(self, errores)
        _validar_capacidades_comerciales(self, errores)

        return errores


# ==========================================================
# VALIDACIÓN DE PERFILES
# ==========================================================

def _validar_perfiles(
    entrada: EntradaBateria,
    errores: List[str],
) -> None:

    if not entrada.demanda_24h_kwh:
        errores.append(
            "No se recibió el perfil horario de demanda."
        )

    if not entrada.fv_horaria_kwh:
        errores.append(
            "No se recibió el perfil horario fotovoltaico."
        )

    _validar_longitud_mensual(
        valores=entrada.consumo_12m_kwh,
        nombre="consumo_12m_kwh",
        errores=errores,
    )

    _validar_longitud_mensual(
        valores=entrada.energia_fv_util_12m_kwh,
        nombre="energia_fv_util_12m_kwh",
        errores=errores,
    )

    if entrada.energia_fv_generada_12m_kwh:
        _validar_longitud_mensual(
            valores=entrada.energia_fv_generada_12m_kwh,
            nombre="energia_fv_generada_12m_kwh",
            errores=errores,
        )

    if entrada.consumo_anual_kwh <= 0:
        errores.append(
            "El consumo anual debe ser mayor que cero."
        )


def _validar_longitud_mensual(
    *,
    valores: List[float],
    nombre: str,
    errores: List[str],
) -> None:

    if len(valores) != 12:
        errores.append(
            f"{nombre} debe contener 12 valores."
        )


# ==========================================================
# VALIDACIÓN TÉCNICA
# ==========================================================

def _validar_configuracion_tecnica(
    entrada: EntradaBateria,
    errores: List[str],
) -> None:

    _validar_factor_unitario(
        valor=entrada.factor_aprovechamiento,
        nombre="factor_aprovechamiento",
        errores=errores,
        permitir_cero=False,
    )

    _validar_factor_unitario(
        valor=entrada.eficiencia_ida_vuelta,
        nombre="eficiencia_ida_vuelta",
        errores=errores,
        permitir_cero=False,
    )

    _validar_soc(entrada, errores)


def _validar_factor_unitario(
    *,
    valor: float,
    nombre: str,
    errores: List[str],
    permitir_cero: bool,
) -> None:

    limite_inferior_valido = (
        valor >= 0.0
        if permitir_cero
        else valor > 0.0
    )

    if not limite_inferior_valido or valor > 1.0:
        errores.append(
            f"{nombre} debe estar entre 0 y 1."
        )


def _validar_soc(
    entrada: EntradaBateria,
    errores: List[str],
) -> None:

    _validar_porcentaje(
        entrada.soc_min_pct,
        "soc_min_pct",
        errores,
    )

    _validar_porcentaje(
        entrada.soc_max_pct,
        "soc_max_pct",
        errores,
    )

    if entrada.soc_max_pct <= entrada.soc_min_pct:
        errores.append(
            "soc_max_pct debe ser mayor que soc_min_pct."
        )

    if not (
        entrada.soc_min_pct
        <= entrada.soc_inicial_pct
        <= entrada.soc_max_pct
    ):
        errores.append(
            "soc_inicial_pct debe estar dentro de los "
            "límites mínimo y máximo."
        )


def _validar_porcentaje(
    valor: float,
    nombre: str,
    errores: List[str],
) -> None:

    if not 0.0 <= valor <= 100.0:
        errores.append(
            f"{nombre} debe estar entre 0 y 100."
        )


# ==========================================================
# VALIDACIÓN ECONÓMICA
# ==========================================================

def _validar_costos(
    entrada: EntradaBateria,
    errores: List[str],
) -> None:

    if entrada.costo_bateria_usd_kwh < 0:
        errores.append(
            "El costo de batería no puede ser negativo."
        )

    if entrada.tipo_cambio_l_usd <= 0:
        errores.append(
            "El tipo de cambio debe ser mayor que cero."
        )

    if entrada.tarifa_compra_l_kwh < 0:
        errores.append(
            "La tarifa de compra no puede ser negativa."
        )

    if entrada.tarifa_inyeccion_l_kwh < 0:
        errores.append(
            "La tarifa de inyección no puede ser negativa."
        )


def _validar_financiamiento(
    entrada: EntradaBateria,
    errores: List[str],
) -> None:

    _validar_factor_unitario(
        valor=entrada.porcentaje_financiado,
        nombre="porcentaje_financiado",
        errores=errores,
        permitir_cero=True,
    )

    es_financiado = (
        entrada.modo_financiamiento != "contado"
        and entrada.porcentaje_financiado > 0
    )

    if es_financiado and entrada.plazo_anios <= 0:
        errores.append(
            "El plazo debe ser mayor que cero para un "
            "proyecto financiado."
        )


def _validar_capacidades_comerciales(
    entrada: EntradaBateria,
    errores: List[str],
) -> None:

    capacidades_validas = [
        float(capacidad)
        for capacidad in entrada.capacidades_comerciales_kwh
        if float(capacidad or 0.0) > 0
    ]

    if entrada.usar_bateria and not capacidades_validas:
        errores.append(
            "No existen capacidades comerciales válidas."
        )


# ==========================================================
# CONVERSORES SEGUROS
# ==========================================================

def _leer_float(
    objeto: Any,
    atributo: str,
    valor_defecto: float = 0.0,
) -> float:

    valor = getattr(
        objeto,
        atributo,
        valor_defecto,
    )

    return float(
        valor
        if valor is not None
        else valor_defecto
    )


def _leer_int(
    objeto: Any,
    atributo: str,
    valor_defecto: int = 0,
) -> int:

    valor = getattr(
        objeto,
        atributo,
        valor_defecto,
    )

    return int(
        valor
        if valor is not None
        else valor_defecto
    )


def _leer_texto(
    objeto: Any,
    atributo: str,
    valor_defecto: str,
) -> str:

    valor = getattr(
        objeto,
        atributo,
        valor_defecto,
    )

    return str(
        valor
        if valor not in (None, "")
        else valor_defecto
    )


def _leer_lista(
    objeto: Any,
    atributo: str,
) -> List[float]:

    valores = getattr(
        objeto,
        atributo,
        [],
    )

    return list(
        valores
        if valores is not None
        else []
    )


# ==========================================================
# EXTRACCIÓN DE PERFILES
# ==========================================================

def _obtener_consumo_12m(datos) -> List[float]:
    return _leer_lista(
        datos,
        "consumo_12m",
    )


def _obtener_energia_util_12m(energia) -> List[float]:
    return _leer_lista(
        energia,
        "energia_util_12m",
    )


def _obtener_energia_generada_12m(
    energia,
    energia_util_12m: List[float],
) -> List[float]:

    atributos = (
        "energia_generada_12m",
        "energia_bruta_12m",
        "energia_fv_12m",
        "produccion_12m",
    )

    for atributo in atributos:
        valores = getattr(
            energia,
            atributo,
            None,
        )

        if valores:
            return list(valores)

    return list(energia_util_12m)


def _obtener_demanda_24h(datos):
    return (
        getattr(
            datos,
            "consumo_horario_24h_kwh",
            {},
        )
        or {}
    )


def _obtener_fv_horaria(energia) -> List[float]:
    return list(
        getattr(
            energia,
            "energia_horaria_kwh",
            [],
        )
        or []
    )


# ==========================================================
# CÁLCULOS ECONÓMICOS
# ==========================================================

def _calcular_capex_fv_l(
    *,
    sizing,
    datos,
    tipo_cambio: float,
) -> float:

    potencia_fv_kwp = _leer_float(
        sizing,
        "pdc_kw",
        0.0,
    )

    costo_usd_kwp = _leer_float(
        datos,
        "costo_usd_kwp",
        0.0,
    )

    return (
        potencia_fv_kwp
        * costo_usd_kwp
        * tipo_cambio
    )


# ==========================================================
# CONSTRUCTOR PRINCIPAL
# ==========================================================

def construir_entrada_bateria(
    *,
    datos,
    sizing,
    energia,
) -> EntradaBateria:

    
    consumo_12m = _obtener_consumo_12m(
        datos
    )

    energia_util_12m = _obtener_energia_util_12m(
        energia
    )

    energia_generada_12m = _obtener_energia_generada_12m(
        energia,
        energia_util_12m,
    )

    tipo_cambio = _leer_float(
        datos,
        "tcambio",
        26.61,
    )

    capex_fv_l = _calcular_capex_fv_l(
        sizing=sizing,
        datos=datos,
        tipo_cambio=tipo_cambio,
    )

    return EntradaBateria(
        demanda_24h_kwh=_obtener_demanda_24h(
            datos
        ),
        fv_horaria_kwh=_obtener_fv_horaria(
            energia
        ),
        consumo_12m_kwh=consumo_12m,
        energia_fv_util_12m_kwh=energia_util_12m,
        energia_fv_generada_12m_kwh=energia_generada_12m,
        usar_bateria=bool(
            (
                getattr(datos, "sistema_fv", {})
                .get("bateria", {})
                .get("usar_bateria", False)
            )
        ),
        
        costo_bateria_usd_kwh=_leer_float(
            datos,
            "costo_bateria_usd_kwh",
            250.0,
        ),
        tipo_cambio_l_usd=tipo_cambio,
        capex_fv_l=capex_fv_l,
        tarifa_compra_l_kwh=_leer_float(
            datos,
            "tarifa_energia",
            0.0,
        ),
        tarifa_inyeccion_l_kwh=_leer_float(
            datos,
            "tarifa_inyeccion_l_kwh",
            2.72,
        ),
        cargos_fijos_l_mes=_leer_float(
            datos,
            "cargos_fijos",
            0.0,
        ),
        om_anual_pct=_leer_float(
            datos,
            "om_anual_pct",
            0.0,
        ),
        modo_financiamiento=_leer_texto(
            datos,
            "modo_financiamiento",
            "contado",
        ),
        tasa_anual=_leer_float(
            datos,
            "tasa_anual",
            0.0,
        ),
        plazo_anios=_leer_int(
            datos,
            "plazo_anios",
            0,
        ),
        porcentaje_financiado=_leer_float(
            datos,
            "porcentaje_financiado",
            0.0,
        ),
    )
