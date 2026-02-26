"""
Dominio conductores — FV Engine

API pública del módulo:
- Dimensionamiento de conductores
- Cálculo de caída de tensión
- Acceso controlado al motor NEC

Regla arquitectónica:
Otros módulos NO deben importar archivos internos.
Siempre importar desde:
    electrical.conductores
"""

# Motor principal
from .calculo_conductores import tramo_conductor

# Utilidad física (permitida externamente)
from .modelo_tramo import caida_tension_pct

__all__ = [
    "tramo_conductor",
    "caida_tension_pct",
]
