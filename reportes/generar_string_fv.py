# -*- coding: utf-8 -*-
from reportlab.lib.pagesizes import landscape, letter
from reportlab.platypus import SimpleDocTemplate
from reportlab.pdfgen import canvas
from reportlab.lib import colors


def generar_lamina_fv(strings, out_path):

    c = canvas.Canvas(out_path, pagesize=landscape(letter))

    width, height = landscape(letter)

    # =========================
    # TÍTULO
    # =========================
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(
        width / 2,
        height - 40,
        "CONFIGURACIÓN DEL GENERADOR FOTOVOLTAICO (TOPOLOGÍA REAL)"
    )

    # =========================
    # SECCIONES (líneas)
    # =========================
    c.setStrokeColor(colors.grey)
    c.setDash(3, 3)

    c.line(350, 100, 350, height - 80)
    c.line(500, 100, 500, height - 80)
    c.line(650, 100, 650, height - 80)

    c.setDash()

    # =========================
    # STRINGS
    # =========================
    y = height - 150

    for i, s in enumerate(strings):

        n = s.n_series

        c.setFont("Helvetica", 9)
        c.drawString(40, y + 10, f"STRING {i+1}")
        c.drawString(40, y - 5, f"{n} MÓDULOS")

        # paneles
        x = 120
        for j in range(n):
            c.setFillColorRGB(0.12, 0.18, 0.28)
            c.rect(x, y, 20, 40, fill=1)

            x += 25

        # cables
        c.setStrokeColor(colors.red)
        c.line(x, y + 25, 500, y + 25)

        c.setStrokeColor(colors.black)
        c.line(x, y + 10, 500, y + 10)

        # MPPT
        c.setStrokeColor(colors.black)
        c.rect(500, y + 15, 20, 20)

        c.setFillColor(colors.red)
        c.drawString(505, y + 20, "+")

        c.setFillColor(colors.black)
        c.drawString(505, y + 5, "-")

        # hacia inversor
        c.setStrokeColor(colors.red)
        c.line(520, y + 25, 650, y + 25)

        c.setStrokeColor(colors.black)
        c.line(520, y + 10, 650, y + 10)

        y -= 120

    # =========================
    # INVERSOR
    # =========================
    c.setStrokeColor(colors.black)
    c.setFillColorRGB(0.93, 0.93, 0.93)

    c.rect(650, height/2 - 100, 180, 200, fill=1)

    c.setFillColor(colors.black)
    c.drawCentredString(740, height/2, "INVERSOR 1")

    # =========================
    # FINAL
    # =========================
    c.save()

    return out_path
