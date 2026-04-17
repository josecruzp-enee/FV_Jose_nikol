from pathlib import Path
from reportlab.platypus import Paragraph, Spacer, Image, PageBreak


def insertar_layout_paneles(story, paths, styles, content_w, safe_image=None):
    """
    Inserta el layout de paneles en una nueva página del PDF.

    ✔ Usa safe_image si existe
    ✔ Escala la imagen correctamente
    ✔ Presentación limpia (título + descripción)
    ✔ No rompe si falla la carga de imagen
    """

    layout = paths.get("layout_paneles") if isinstance(paths, dict) else None

    if layout and Path(layout).exists():

        # ==================================================
        # 🔥 NUEVA PÁGINA
        # ==================================================
        story.append(PageBreak())

        # ==================================================
        # TÍTULO
        # ==================================================
        story.append(
            Paragraph("Layout de paneles fotovoltaicos", styles["Heading2"])
        )
        story.append(Spacer(1, 6))

        # ==================================================
        # DESCRIPCIÓN
        # ==================================================
        story.append(
            Paragraph(
                "Distribución del arreglo fotovoltaico sobre la cubierta. "
                "Configuración a dos aguas con división en cumbrera.",
                styles["BodyText"]
            )
        )
        story.append(Spacer(1, 10))

        try:

            # ==================================================
            # 🔥 CARGA DE IMAGEN
            # ==================================================
            if safe_image:
                img = safe_image(str(layout), max_w=content_w, max_h=750)
                if not img:
                    img = Image(str(layout))
            else:
                img = Image(str(layout))

            # ==================================================
            # 🔥 ESCALADO SEGURO
            # ==================================================
            max_w = content_w
            max_h = 750

            w = img.imageWidth
            h = img.imageHeight

            scale = min(max_w / w, max_h / h)

            img.drawWidth = w * scale
            img.drawHeight = h * scale

            img.hAlign = "CENTER"

            # ==================================================
            # INSERTAR
            # ==================================================
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
