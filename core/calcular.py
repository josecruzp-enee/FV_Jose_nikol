# calcular.py
from __future__ import annotations

from .modelo import modelo
from .rutas import preparar_salida
from .orquestador import ejecutar_evaluacion

from reportes.charts import generar_charts
from reportes.layout_paneles import generar_layout_paneles
from reportes.pdf.builder import generar_pdf_profesional


def main():
    datos = Datosproyecto(
        cliente="Cliente ejemplo",
        ubicacion="Honduras",
        consumo_12m=[1500,1800,2100,2200,2400,2300,900,950,1100,1200,1900,1700],
        tarifa_energia=4.998,
        cargos_fijos=325.38,
        prod_base_kwh_kwp_mes=145,
        factores_fv_12m=[0.95,0.97,1.02,1.05,1.08,1.05,0.98,1.00,1.03,1.04,1.00,0.93],
        cobertura_objetivo=0.64,
        costo_usd_kwp=1200,
        tcambio=27.0,
        tasa_anual=0.08,
        plazo_anios=10,
        porcentaje_financiado=1.0,
        om_anual_pct=0.01,
    )

    paths = preparar_salida("salidas")
    resultado = ejecutar_evaluacion(datos)

    generar_charts(resultado["tabla_12m"], paths)
    generar_layout_paneles(
        n_paneles=int(resultado["sizing"]["n_paneles"]),
        out_path=paths["layout_paneles"],
        max_cols=7,
        dos_aguas=True,
        gap_cumbrera_m=0.35
    )

    pdf = generar_pdf_profesional(resultado, datos, paths)
    print("✅ PDF:", pdf)


if __name__ == "__main__":
    main()
