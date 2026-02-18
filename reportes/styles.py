# reportes/pdf/styles.py
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet


def pdf_palette():
    return {
        "PRIMARY": colors.HexColor("#0B2E4A"),
        "BORDER": colors.HexColor("#D7DCE3"),
        "SOFT": colors.HexColor("#F5F7FA"),
        "OK": colors.HexColor("#1B7F3A"),
    }


def pdf_styles():
    styles = getSampleStyleSheet()

    styles["BodyText"].fontName = "Helvetica"
    styles["BodyText"].fontSize = 10
    styles["BodyText"].leading = 12

    return styles
