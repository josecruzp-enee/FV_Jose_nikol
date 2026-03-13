from pathlib import Path
from reportlab.platypus import Paragraph, Spacer, Image


# ==========================================================
# Insertar layout de paneles en el PDF
# ==========================================================

def insertar_layout_paneles(story, paths, styles, content_w):

    if not paths or not isinstance(paths, dict):
        layout = None
    else:
        layout = paths.get("layout_paneles")

    # ------------------------------------------------------
    # Verificar existencia del archivo
    # ------------------------------------------------------

    if layout and Path(layout).exists():

        story.append(Spacer(1, 12))

        try:

            img = Image(str(layout))

            # Ajustar tamaño manteniendo proporción
            img.drawWidth = content_w
            img.drawHeight = img.imageHeight * (content_w / img.imageWidth)

            img.hAlign = "CENTER"

            story.append(img)

        except Exception:

            story.append(
                Paragraph("No se pudo cargar el layout de paneles.", styles["BodyText"])
            )

    else:

        story.append(
            Paragraph("Layout de paneles no disponible.", styles["BodyText"])
        )

    story.append(Spacer(1, 12))
