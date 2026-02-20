from reportlab.platypus import SimpleDocTemplate
from reportlab.lib.pagesizes import letter

from .styles import pdf_palette, pdf_styles
from .page_1 import build_page_1
from .page_2 import build_page_2
from .page_3 import build_page_3
from .page_4 import build_page_4
from .page_5 import build_page_5


def _compat_resultado_plano(resultado_proyecto: dict) -> dict:
    """
    Muchas páginas legacy esperan llaves planas (sizing, tabla_12m, etc.).
    Este adaptador las reconstruye desde ResultadoProyecto SIN recalcular.
    """
    if not isinstance(resultado_proyecto, dict):
        return {}

    # Si ya viene plano (legacy), lo devolvemos tal cual
    if "sizing" in resultado_proyecto and "tabla_12m" in resultado_proyecto:
        return resultado_proyecto

    tecnico = (resultado_proyecto.get("tecnico") or {})
    energetico = (resultado_proyecto.get("energetico") or {})
    financiero = (resultado_proyecto.get("financiero") or {})

    # Si el orquestador incluyó _compat, úsalo como base (cero riesgo)
    base = (resultado_proyecto.get("_compat") or {})
    out = dict(base)

    # Asegurar llaves planas importantes
    out.setdefault("params_fv", tecnico.get("params_fv"))
    out.setdefault("sizing", tecnico.get("sizing"))
    out.setdefault("electrico_ref", tecnico.get("electrico_ref"))
    out.setdefault("electrico_nec", tecnico.get("electrico_nec"))

    out.setdefault("tabla_12m", energetico.get("tabla_12m"))

    out.setdefault("cuota_mensual", financiero.get("cuota_mensual"))
    out.setdefault("evaluacion", financiero.get("evaluacion"))
    out.setdefault("decision", financiero.get("decision"))
    out.setdefault("ahorro_anual_L", financiero.get("ahorro_anual_L"))
    out.setdefault("payback_simple_anios", financiero.get("payback_simple_anios"))
    out.setdefault("finanzas_lp", financiero.get("finanzas_lp"))

    return out


def generar_pdf_profesional(resultado_proyecto, datos, paths):
    """
    `resultado_proyecto` debe ser el objeto único del orquestador (ResultadoProyecto).
    `datos` = Datosproyecto (o equivalente) para datos del cliente/inputs.
    """
    pal = pdf_palette()
    styles = pdf_styles()

    doc = SimpleDocTemplate(
        str(paths["pdf_path"]),
        pagesize=letter
    )

    story = []
    content_w = doc.width

    # ✅ Compat: tus páginas actuales pueden seguir esperando dict plano
    resultado = _compat_resultado_plano(resultado_proyecto)

    story += build_page_1(resultado, datos, paths, pal, styles, content_w)
    story += build_page_2(resultado, datos, paths, pal, styles, content_w)
    story += build_page_3(resultado, datos, paths, pal, styles, content_w)
    story += build_page_4(resultado, datos, paths, pal, styles, content_w)
    story += build_page_5(resultado, datos, paths, pal, styles, content_w)

    doc.build(story)
    return paths["pdf_path"]
