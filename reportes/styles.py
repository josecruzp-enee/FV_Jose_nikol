# reportes/pdf/styles.py
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle


def pdf_palette():
    return {
        "PRIMARY": colors.HexColor("#0B2E4A"),
        "BORDER": colors.HexColor("#D7DCE3"),
        "SOFT": colors.HexColor("#F5F7FA"),

        # Estados financieros
        "OK": colors.HexColor("#1B7F3A"),      # Verde
        "WARN": colors.HexColor("#F9A825"),    # Amarillo
        "BAD": colors.HexColor("#C62828"),     # Rojo
    }


# Estilos que tus páginas pueden usar con confianza
_REQUIRED = ("H2b",)  # agrega aquí los que uses: "H1","H2","P","SMALL", etc.


def pdf_styles():
    styles = getSampleStyleSheet()

    # ===== Base (ajustes globales) =====
    body = styles["BodyText"]
    body.fontName = "Helvetica"
    body.fontSize = 10
    body.leading = 12

    # ===== Estilos propios del reporte =====
    # Nota: usamos add(ParagraphStyle) para que existan por nombre (H2b)
    if "H2b" not in styles.byName:
        base = styles["Heading2"] if "Heading2" in styles.byName else body
        styles.add(
            ParagraphStyle(
                name="H2b",
                parent=base,
                fontName="Helvetica-Bold",
                fontSize=11,
                leading=13,
                spaceBefore=6,
                spaceAfter=4,
                alignment=TA_LEFT,
                textColor=colors.black,
            )
        )

    _assert_required(styles)
    return styles


def _assert_required(styles):
    missing = [k for k in _REQUIRED if k not in styles.byName]
    if missing:
        raise KeyError(
            f"PDF styles missing: {missing}. Define them in reportes/pdf/styles.py"
        )
