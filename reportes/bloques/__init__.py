# reportes/bloques.py

from .resumen_ejecutivo import build_resumen_ejecutivo
from .analisis_energetico import build_analisis_energetico
from .analisis_financiero import build_analisis_financiero
from .analisis_operativo import build_analisis_operativo
from .ingenieria_electrica import build_ingenieria_electrica


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
    # 1. Resumen inicial para toma de decisión
    build_resumen_ejecutivo,

    # 2. Producción, consumo, cobertura y balance energético
    build_analisis_energetico,

    # 3. CAPEX, modalidad de pago, financiamiento y retorno
    build_analisis_financiero,

    # 4. Factura residual y comportamiento económico mensual
    build_analisis_operativo,

    # 5. Solución FV, conclusiones y anexo técnico eléctrico
    build_ingenieria_electrica,
]
