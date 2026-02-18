# app.py
from __future__ import annotations

import sys
from pathlib import Path
import streamlit as st

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ui.router import PasoWizard, render_wizard
from ui import datos_cliente, consumo_energetico, sistema_fv, seleccion_equipos
from core import ingenieria_electrica
from ui import resultados

def main() -> None:
    st.set_page_config(page_title="FV Engine", layout="wide")
    st.title("FV Engine — Wizard profesional")

    pasos = [
        PasoWizard(1, "Datos cliente", datos_cliente.render, datos_cliente.validar, requiere=[]),
        PasoWizard(2, "Consumo energético", consumo_energetico.render, consumo_energetico.validar, requiere=[1]),
        PasoWizard(3, "Sistema FV", sistema_fv.render, sistema_fv.validar, requiere=[1, 2]),
        PasoWizard(4, "Selección de equipos", seleccion_equipos.render, seleccion_equipos.validar, requiere=[1, 2, 3]),
        PasoWizard(5, "Ingeniería eléctrica", ingenieria_electrica.render, ingenieria_electrica.validar, requiere=[1, 2, 3, 4]),
        PasoWizard(6, "Resultados", resultados.render, resultados.validar, requiere=[1, 2, 3, 4, 5]),
    ]

    render_wizard(pasos)

if __name__ == "__main__":
    main()
