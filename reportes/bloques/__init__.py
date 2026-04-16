from .resumen_ejecutivo import build_resumen_ejecutivo
from .analisis_energetico import build_analisis_energetico

# 🔴 temporales
from ..page_3 import build_page_3
from ..page_4 import build_page_4
from ..page_5 import build_page_5


BLOQUES_REPORTE = [
    build_resumen_ejecutivo,
    build_analisis_energetico,
    build_page_3,
    build_page_4,
    build_page_5,
]
