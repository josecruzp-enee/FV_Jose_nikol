from reportlab.platypus import Table, TableStyle


def crear_tabla_corrientes(corr, pal, content_w):

    panel = corr.get("panel", {})
    string = corr.get("string", {})
    mppt = corr.get("mppt", {})
    dc_total = corr.get("dc_inversor", {})   # ← nombre correcto
    ac = corr.get("ac_salida", {})           # ← nombre correcto

    data = [

        ["Nivel eléctrico", "Corriente (A)"],

        ["Panel", f"{panel.get('i_nominal',0):.2f}"],

        ["String", f"{string.get('i_nominal',0):.2f}"],

        ["MPPT", f"{mppt.get('i_nominal',0):.2f}"],

        ["Entrada inversor DC", f"{dc_total.get('i_nominal',0):.2f}"],

        ["Salida inversor AC", f"{ac.get('i_nominal',0):.2f}"],
    ]

    colw = [content_w * 0.6, content_w * 0.4]

    tabla = Table(data, colWidths=colw)

    tabla.setStyle(TableStyle([
        ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
        ("BACKGROUND",(0,0),(-1,0),pal["SOFT"]),
        ("TEXTCOLOR",(0,0),(-1,0),pal["PRIMARY"]),
        ("ALIGN",(1,1),(-1,-1),"RIGHT"),
        ("GRID",(0,0),(-1,-1),0.3,pal["BORDER"]),
        ("FONTSIZE",(0,0),(-1,-1),10),
    ]))

    return tabla
