# reportes/bloques.py

from .resumen_ejecutivo import build_resumen_ejecutivo
from .analisis_energetico import build_analisis_energetico
from .analisis_financiero import build_analisis_financiero
from .analisis_operativo import build_analisis_operativo
from .ingenieria_electrica import (
    build_solucion_tecnica,
    build_layout_fv,
    build_operacion_fv,
    build_conclusiones,
    build_anexo_electrico,
)


# ==========================================================
# ÍNDICE MAESTRO DEL REPORTE PDF
# ==========================================================
# El orden de esta lista define el orden de aparición
# de los capítulos dentro del PDF.
#
# Reglas:
# - No cambiar nombres de funciones build_*.
# - No eliminar bloques sin revisar dependencias.
# - Para agregar una nueva sección, importar su build_* y
#   agregarla al final o en la posición deseada.
# ==========================================================
BLOQUES_REPORTE = [
    # 1. Resumen para decisión
    build_resumen_ejecutivo,

    # 2. Conclusiones y recomendación
    build_conclusiones,

    # 3. Análisis energético
    build_analisis_energetico,

    # 4. Evaluación económica
    build_analisis_financiero,

    # 5. Comportamiento mensual
    build_analisis_operativo,

    # 6. Solución técnica propuesta
    build_solucion_tecnica,

    # 7. Distribución física
    build_layout_fv,

    # 8. Operación y optimización
    build_operacion_fv,

    # 9. Respaldo técnico
    build_anexo_electrico,
]
