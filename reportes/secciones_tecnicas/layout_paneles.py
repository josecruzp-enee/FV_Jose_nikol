from pathlib import Path
from reportlab.platypus import Paragraph, Spacer, Image


def insertar_layout_paneles(story, paths, styles, content_w):

    layout = (paths or {}).get("layout_paneles")

    if layout and Path(str(layout)).exists():

        story.append(Spacer(1, 10))

        img = Image(str(layout), width=content_w, height=content_w * 0.45)
        img.hAlign = "CENTER"

        story.append(img)
        story.append(Spacer(1, 10))

    else:

        story.append(
            Paragraph("Layout de paneles no disponible.", styles["BodyText"])
        )
        story.append(Spacer(1, 10))
