from reportlab.platypus import Table, TableStyle


def crear_tabla_diseno_nec(paq, pal, content_w):

    ocpd = paq.get("ocpd", {})
    conductores = paq.get("conductores", {}).get("circuitos", [])

    i_dc = None
    i_ac = None

    for c in conductores:

        if c.get("nombre") == "DC":
            i_dc = c.get("i_diseno_a")

        if c.get("nombre") == "AC":
            i_ac = c.get("i_diseno_a")

    breaker = ocpd.get("breaker_ac", {}).get("tamano_a")

    data = [

        ["Parámetro", "Valor"],

        ["Corriente DC diseño", f"{(i_dc or 0):.2f} A"],

        ["Corriente AC diseño", f"{(i_ac or 0):.2f} A"],

        ["Breaker AC requerido", f"{breaker or 0} A"],
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
