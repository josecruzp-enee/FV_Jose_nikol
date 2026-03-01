from dataclasses import asdict, is_dataclass
from typing import Any

from core.servicios.sizing import calcular_sizing_unificado
from core.servicios.paneles import ejecutar_paneles_desde_sizing
from core.servicios.energia import ejecutar_energia_desde_sizing
from core.servicios.nec import ejecutar_nec_desde_sizing
from core.servicios.finanzas import ejecutar_finanzas_desde_sizing


# ==========================================================
# Helper seguro: convierte dataclass → dict
# ==========================================================

def _to_dict_safe(obj: Any) -> Any:
    if is_dataclass(obj):
        return asdict(obj)
    return obj


# ==========================================================
# Adaptadores de puertos (infraestructura legacy)
# ==========================================================

class PuertoSizingImpl:
    def ejecutar(self, datos):
        resultado = calcular_sizing_unificado(datos)
        return _to_dict_safe(resultado)


class PuertoPanelesImpl:
    def ejecutar(self, datos, sizing_raw):
        resultado = ejecutar_paneles_desde_sizing(datos, sizing_raw)
        return _to_dict_safe(resultado)


class PuertoEnergiaImpl:
    def ejecutar(self, datos, sizing_raw, strings_raw):
        resultado = ejecutar_energia_desde_sizing(datos, sizing_raw, strings_raw)
        return _to_dict_safe(resultado)


class PuertoNECImpl:
    def ejecutar(self, datos, sizing_raw, strings_raw):
        resultado = ejecutar_nec_desde_sizing(datos, sizing_raw, strings_raw)
        return _to_dict_safe(resultado)


class PuertoFinanzasImpl:
    def ejecutar(self, datos, sizing_raw, energia_raw):
        resultado = ejecutar_finanzas_desde_sizing(datos, sizing_raw, energia_raw)
        return _to_dict_safe(resultado)
