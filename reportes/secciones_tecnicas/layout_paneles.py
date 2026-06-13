from pathlib import Path
from reportlab.platypus import Paragraph, Spacer, Image, PageBreak


def insertar_layout_paneles(
    story,
    paths,
    styles,
    content_w,
    safe_image=None,
    sistema_fv=None,
):
    """
    Inserta el layout de paneles en una nueva página del PDF.

    La tabla preliminar conserva los datos técnicos.
    La imagen se usa como representación gráfica limpia.
    """

    layout = paths.get("layout_paneles") if isinstance(paths, dict) else None
    sf = sistema_fv or {}

    tipo_montaje = (
        sf.get("tipo_montaje")
        or paths.get("tipo_montaje")
        or "Terraza / cubierta plana"
    )

    orientacion_panel = (
        sf.get("orientacion_panel")
        or paths.get("orientacion_panel")
        or "Vertical (Portrait)"
    )

    if tipo_montaje == "Techo a dos aguas":
        descripcion = (
            "Distribución gráfica preliminar del arreglo fotovoltaico sobre "
            "cubierta inclinada a dos aguas. La cumbrera se muestra como "
            "referencia geométrica."
        )
    elif tipo_montaje == "Suelo":
        descripcion = (
            "Distribución gráfica preliminar del arreglo fotovoltaico sobre suelo. "
            "La separación entre filas, sombras y obstáculos deberán verificarse "
            "en el diseño definitivo."
        )
    else:
        descripcion = (
            "Distribución gráfica preliminar del arreglo fotovoltaico sobre "
            "terraza o cubierta plana."
        )

    descripcion += f" Orientación de panel: {orientacion_panel}."

    if layout and Path(str(layout)).exists():

        story.append(PageBreak())
        story.append(Paragraph("Layout de paneles fotovoltaicos", styles["Heading2"]))
        story.append(Spacer(1, 6))
        story.append(Paragraph(descripcion, styles["BodyText"]))
        story.append(Spacer(1, 10))

        try:
            max_w = content_w*0.88
            max_h = 500

            if safe_image:
                img = safe_image(str(layout), max_w=max_w, max_h=max_h)
            else:
                img = None

            if not img:
                img = Image(str(layout))

                w = img.imageWidth
                h = img.imageHeight

                scale = min(max_w / w, max_h / h, 1.0)

                img.drawWidth = w * scale
                img.drawHeight = h * scale

            img.hAlign = "CENTER"
            story.append(img)

        except Exception:
            story.append(
                Paragraph(
                    "No se pudo cargar el layout de paneles.",
                    styles["BodyText"]
                )
            )

    else:
        story.append(
            Paragraph(
                "Layout de paneles no disponible.",
                styles["BodyText"]
            )
        )

    story.append(Spacer(1, 12))
