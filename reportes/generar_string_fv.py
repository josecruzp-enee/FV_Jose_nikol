# -*- coding: utf-8 -*-
from reportlab.platypus import SimpleDocTemplate, Spacer, Table
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.graphics.shapes import Drawing, Rect, Line, String, Image


def generar_lamina_fv(pdf_path,
                      panel_img=None,
                      mc4_img=None,
                      inversor_img=None):

    doc = SimpleDocTemplate(pdf_path, pagesize=landscape(letter))
    elements = []

    # =========================
    # DIBUJO BASE
    # =========================
    d = Drawing(1000, 420)

    # ---- TÍTULO
    d.add(String(300, 390,
        "CONFIGURACIÓN DEL GENERADOR FOTOVOLTAICO (TOPOLOGÍA REAL)",
        fontSize=14))

    # ---- LÍNEAS DE SECCIÓN
    for x in [350, 550, 750]:
        d.add(Line(x, 40, x, 360, strokeColor=colors.lightblue, strokeDashArray=[4,3]))

    # ---- ENCABEZADOS
    d.add(String(120, 350, "STRING FV\n(MÓDULOS EN SERIE)", fontSize=9))
    d.add(String(420, 350, "SALIDA DC", fontSize=9))
    d.add(String(620, 350, "ENTRADA MPPT", fontSize=9))
    d.add(String(820, 350, "INVERSOR", fontSize=9))

    # =========================
    # FUNCIÓN STRING
    # =========================
    def dibujar_string(x, y, n, label):

        d.add(String(x-80, y+10, label, fontSize=9))

        for i in range(n):

            px = x + i * 22

            # panel (imagen o fallback)
            if panel_img:
                d.add(Image(px, y, 18, 30, panel_img))
            else:
                d.add(Rect(px, y, 18, 30,
                           fillColor=colors.HexColor("#1e293b")))

            # conexión
            if i < n-1:
                d.add(Line(px+18, y+15, px+22, y+15))

        x_end = x + n * 22

        # cables
        d.add(Line(x_end, y+20, x_end+100, y+20,
                   strokeColor=colors.red, strokeWidth=2))

        d.add(Line(x_end, y+10, x_end+100, y+10,
                   strokeColor=colors.black, strokeWidth=2))

        # MC4 (si existe)
        if mc4_img:
            d.add(Image(x_end+40, y+12, 30, 10, mc4_img))

        return x_end + 100

    # =========================
    # STRINGS
    # =========================
    x_salida_1 = dibujar_string(80, 260, 10, "STRING 1\n10 módulos")
    x_salida_2 = dibujar_string(80, 120, 8, "STRING 2\n8 módulos")

    # =========================
    # MPPT
    # =========================
    def dibujar_mppt(x, y, label):

        d.add(String(x, y+40, label, fontSize=9))

        # +
        d.add(Rect(x, y+15, 20, 20, strokeColor=colors.red))
        d.add(String(x+7, y+20, "+"))

        # -
        d.add(Rect(x, y-5, 20, 20, strokeColor=colors.black))
        d.add(String(x+7, y, "-"))

        return x + 20

    x_mppt = 550

    dibujar_mppt(x_mppt, 260, "MPPT 1")
    dibujar_mppt(x_mppt, 120, "MPPT 2")

    # =========================
    # INVERSOR
    # =========================
    inv_x = 780
    inv_y = 120

    if inversor_img:
        d.add(Image(inv_x, inv_y, 180, 180, inversor_img))
    else:
        d.add(Rect(inv_x, inv_y, 180, 180,
                   fillColor=colors.lightgrey))
        d.add(String(inv_x+40, inv_y+140, "INVERSOR 1"))

    # conexiones
    def conectar(y):

        d.add(Line(x_mppt+20, y+25, inv_x, y+25,
                   strokeColor=colors.red, strokeWidth=2))

        d.add(Line(x_mppt+20, y+5, inv_x, y+5,
                   strokeColor=colors.black, strokeWidth=2))

        d.add(Rect(inv_x-5, y+23, 6, 6, fillColor=colors.red))
        d.add(Rect(inv_x-5, y+3, 6, 6, fillColor=colors.black))

    conectar(260)
    conectar(120)

    elements.append(d)

    elements.append(Spacer(1, 20))

    # =========================
    # TABLA
    # =========================
    data = [
        ["MPPT", "N° STRINGS", "MÓDULOS", "TOTAL"],
        ["MPPT 1", "1", "10", "10"],
        ["MPPT 2", "1", "8", "8"]
    ]

    table = Table(data)
    table.setStyle([
        ("GRID", (0,0), (-1,-1), 1, colors.black),
        ("BACKGROUND", (0,0), (-1,0), colors.lightgrey)
    ])

    elements.append(table)

    # =========================
    # GENERAR PDF
    # =========================
    doc.build(elements)


# =========================
# EJECUCIÓN
# =========================
if __name__ == "__main__":
    generar_lamina_fv(
        "lamina_fv_final.pdf",
        panel_img=None,       # 👉 pon ruta PNG si tienes
        mc4_img=None,
        inversor_img=None
    )
