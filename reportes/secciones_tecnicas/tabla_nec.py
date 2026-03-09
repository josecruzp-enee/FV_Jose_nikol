from reportlab.platypus import Table, TableStyle


def crear_tabla_nec_profesional(paq, pal, content_w):

    corr = paq.get("corrientes", {})
    ocpd = paq.get("ocpd", {})
    cond = paq.get("conductores", {})

    def fmt_corriente(v):
        try:
            return f"{float(v):.2f} A"
        except:
            return "-"

    data = [

        ["Circuito", "I nominal", "I diseño", "Protección", "Conductor"],

        [
            "String",
            fmt_corriente(corr.get("string", {}).get("i_nominal")),
            fmt_corriente(corr.get("string", {}).get("i_diseno")),
            ocpd.get("string", {}).get("proteccion", "-"),
            cond.get("string", {}).get("calibre", "-"),
        ],

        [
            "MPPT",
            fmt_corriente(corr.get("mppt", {}).get("i_nominal")),
            fmt_corriente(corr.get("mppt", {}).get("i_diseno")),
            ocpd.get("mppt", {}).get("proteccion", "-"),
            cond.get("mppt", {}).get("calibre", "-"),
        ],

        [
            "DC Inversor",
            fmt_corriente(corr.get("dc_inversor", {}).get("i_nominal")),
            fmt_corriente(corr.get("dc_inversor", {}).get("i_diseno")),
            ocpd.get("dc_inversor", {}).get("proteccion", "-"),
            cond.get("dc_inversor", {}).get("calibre", "-"),
        ],

        [
            "AC salida",
            fmt_corriente(corr.get("ac_salida", {}).get("i_nominal")),
            fmt_corriente(corr.get("ac_salida", {}).get("i_diseno")),
            ocpd.get("ac_salida", {}).get("proteccion", "-"),
            cond.get("ac_salida", {}).get("calibre", "-"),
        ],
    ]

    colw = [
        content_w * 0.20,
        content_w * 0.20,
        content_w * 0.20,
        content_w * 0.20,
        content_w * 0.20,
    ]

    tabla = Table(data, colWidths=colw)

    tabla.setStyle(TableStyle([

        ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
        ("BACKGROUND",(0,0),(-1,0),pal["SOFT"]),
        ("TEXTCOLOR",(0,0),(-1,0),pal["PRIMARY"]),

        ("ALIGN",(1,1),(-1,-1),"RIGHT"),

        ("GRID",(0,0),(-1,-1),0.3,pal["BORDER"]),
        ("FONTSIZE",(0,0),(-1,-1),9),

        ("VALIGN",(0,0),(-1,-1),"MIDDLE")

    ]))

    return tabla
