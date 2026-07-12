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
#   agregarla en la posición deseada.
# ==========================================================

BLOQUES_REPORTE = [

    # 1. Reporte ejecutivo
    build_resumen_ejecutivo,

    # 2. Conclusiones
    build_conclusiones,

    # 3. Evaluación financiera
    build_analisis_financiero,

    # 4. Impacto económico
    build_analisis_operativo,

    # 5. Análisis energético
    build_analisis_energetico,

    # 6. Solución técnica
    build_solucion_tecnica,

    # 7. Layout FV
    build_layout_fv,

    # 8. Operación FV
    build_operacion_fv,

    # 9. Anexo técnico
    build_anexo_electrico,
]
