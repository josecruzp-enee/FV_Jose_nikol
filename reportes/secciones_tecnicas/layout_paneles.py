from pathlib import Path
from reportlab.platypus import Paragraph, Spacer, Image, PageBreak


# ==========================================================
# Insertar layout de paneles en el PDF
# ==========================================================

def insertar_layout_paneles(story, paths, styles, content_w, safe_image=None):

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

            # ==================================================
            # 🔥 USAR safe_image SI EXISTE
            # ==================================================
            if safe_image:
                img = safe_image(str(layout), max_w=content_w, max_h=600)

            else:
                img = Image(str(layout))

                # 🔥 ESCALADO SEGURO (CLAVE PARA EVITAR ERROR)
                max_w = content_w
                max_h = 600  # menor que el frame (≈636)

                w = img.imageWidth
                h = img.imageHeight

                scale = min(max_w / w, max_h / h)

                img.drawWidth = w * scale
                img.drawHeight = h * scale

            img.hAlign = "CENTER"

            # ==================================================
            # 🔥 FORZAR NUEVA PÁGINA (MEJOR PRESENTACIÓN)
            # ==================================================
            story.append(PageBreak())

            story.append(
                Paragraph("Layout de paneles fotovoltaicos", styles["Heading2"])
            )
            story.append(Spacer(1, 6))

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
