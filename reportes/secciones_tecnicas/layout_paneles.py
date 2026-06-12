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

    ✔ Usa safe_image si existe
    ✔ Escala la imagen correctamente
    ✔ Presentación limpia
    ✔ Texto dinámico según tipo de montaje
    ✔ No rompe si falla la carga de imagen
    """

    layout = paths.get("layout_paneles") if isinstance(paths, dict) else None
    sf = sistema_fv or {}

    tipo_montaje = sf.get("tipo_montaje", "Terraza / cubierta plana")
    orientacion_panel = sf.get("orientacion_panel", "Vertical (Portrait)")

    if tipo_montaje == "Techo a dos aguas":
        descripcion = (
            "Distribución del arreglo fotovoltaico sobre cubierta inclinada. "
            "Configuración a dos aguas con división en cumbrera."
        )
    elif tipo_montaje == "Suelo":
        descripcion = (
            "Distribución preliminar del arreglo fotovoltaico en sistema sobre suelo. "
            "La separación y orientación deberán verificarse en el diseño definitivo."
        )
    else:
        descripcion = (
            "Distribución preliminar del arreglo fotovoltaico sobre terraza o cubierta plana."
        )

    descripcion += f" Orientación de panel: {orientacion_panel}."

    if layout and Path(layout).exists():

        story.append(PageBreak())

        story.append(
            Paragraph("Layout de paneles fotovoltaicos", styles["Heading2"])
        )
        story.append(Spacer(1, 6))

        story.append(
            Paragraph(descripcion, styles["BodyText"])
        )
        story.append(Spacer(1, 10))

        try:
            if safe_image:
                img = safe_image(str(layout), max_w=content_w, max_h=750)
                if not img:
                    img = Image(str(layout))
            else:
                img = Image(str(layout))

            max_w = content_w
            max_h = 750

            w = img.imageWidth
            h = img.imageHeight

            scale = min(max_w / w, max_h / h)

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
