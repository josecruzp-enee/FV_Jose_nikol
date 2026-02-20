# electrical/cables.py
from __future__ import annotations

from typing import Any, Dict, List, Optional
import math

from electrical.modelos import ParametrosCableado


# ==========================================================
# Tablas (referenciales)
# ==========================================================

# Ampacidad CU 75°C (simplificada)
AMP_CU_75C = {"14": 20, "12": 25, "10": 35, "8": 50, "6": 65, "4": 85, "3": 100, "2": 115, "1": 130, "1/0": 150}

# PV wire referencial
AMP_PV_90C = {"14": 25, "12": 30, "10": 40, "8": 55, "6": 75}

# R ohm/km Cu
R_OHM_KM_CU = {"14": 8.286, "12": 5.211, "10": 3.277, "8": 2.061, "6": 1.296, "4": 0.815, "3": 0.647, "2": 0.513, "1": 0.407, "1/0": 0.323}

GAUGES_CU = ["14", "12", "10", "8", "6", "4", "3", "2", "1", "1/0"]
GAUGES_PV = ["14", "12", "10", "8", "6"]
