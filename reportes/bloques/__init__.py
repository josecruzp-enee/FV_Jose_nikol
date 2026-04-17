from .resumen_ejecutivo import build_resumen_ejecutivo
from .analisis_energetico import build_analisis_energetico
from .analisis_financiero import build_analisis_financiero
from .analisis_operativo import build_analisis_operativo
from .ingenieria_electrica import build_bloque_ingenieria  

BLOQUES_REPORTE = [
    build_resumen_ejecutivo,
    build_analisis_energetico,
    build_analisis_financiero,
    build_analisis_operativo,
    build_bloque_ingenieria,  
]
