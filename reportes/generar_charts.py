# reportes/generar_charts.py
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

import matplotlib.pyplot as plt


def generar_charts(tabla_12m: List[Dict[str, Any]], out_dir: Optional[str] = None) -> Dict[str, str]:
    """
    Genera 3 PNG:
      - fv_chart_energia.png (factura_base vs pago_enee)
      - fv_chart_neto.png (ahorro)
      - fv_chart_generacion.png (fv_kwh)
    """
    base = Path(out_dir) if out_dir else Path("salidas/charts")
    base.mkdir(parents=True, exist_ok=True)

    meses = [str(r.get("mes", i + 1)) for i, r in enumerate(tabla_12m)]
    factura_base = [float(r.get("factura_base_L", 0.0)) for r in tabla_12m]
    pago_enee = [float(r.get("pago_enee_L", 0.0)) for r in tabla_12m]
    ahorro = [float(r.get("ahorro_L", 0.0)) for r in tabla_12m]
    fv_kwh = [float(r.get("fv_kwh", 0.0)) for r in tabla_12m]

    # 1) Energia (L)
    p1 = base / "fv_chart_energia.png"
    plt.figure()
    plt.plot(meses, factura_base, marker="o")
    plt.plot(meses, pago_enee, marker="o")
    plt.xticks(rotation=90)
    plt.tight_layout()
    plt.savefig(p1, dpi=160)
    plt.close()

    # 2) Flujo neto (ahorro)
    p2 = base / "fv_chart_neto.png"
    plt.figure()
    plt.bar(meses, ahorro)
    plt.xticks(rotation=90)
    plt.tight_layout()
    plt.savefig(p2, dpi=160)
    plt.close()

    # 3) Generacion FV util
    p3 = base / "fv_chart_generacion.png"
    plt.figure()
    plt.plot(meses, fv_kwh, marker="o")
    plt.xticks(rotation=90)
    plt.tight_layout()
    plt.savefig(p3, dpi=160)
    plt.close()

    return {"chart_energia": str(p1), "chart_neto": str(p2), "chart_generacion": str(p3)}


