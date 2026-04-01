# ==========================================================
# DEBUG REAL DEL PIPELINE FV ENGINE
# ==========================================================

from pprint import pprint
from dataclasses import asdict, is_dataclass

from core.aplicacion.dependencias import construir_dependencias
from core.aplicacion.orquestador_estudio import ejecutar_estudio
from core.aplicacion.builder_paneles import construir_entrada_paneles

from core.dominio.modelo import Datosproyecto


# ==========================================================
# UTIL
# ==========================================================

def dump(obj, titulo):
    print("\n" + "="*70)
    print(f"🔎 {titulo}")
    print("="*70)

    if obj is None:
        print("❌ None")
        return

    if is_dataclass(obj):
        pprint(asdict(obj))
    elif isinstance(obj, dict):
        pprint(obj)
    else:
        print(obj)


# ==========================================================
# DATOS CONTROLADOS
# ==========================================================

def datos_debug():

    p = Datosproyecto(
        cliente="debug",
        ubicacion="debug",
        lat=15.8,
        lon=-87.2,

        consumo_12m=[10000]*12,
        tarifa_energia=5,
        cargos_fijos=0,

        prod_base_kwh_kwp_mes=[120]*12,
        factores_fv_12m=[1]*12,

        cobertura_objetivo=1.0,
        costo_usd_kwp=1000,
        tcambio=24.5,

        tasa_anual=0.1,
        plazo_anios=10,
        porcentaje_financiado=0.0
    )

    # 🔥 EQUIPOS
    p.equipos = {
        "panel_id": "canadian_450",
        "inversor_id": "inv_5kw_2mppt"
    }

    # 🔥 SISTEMA FV (CLAVE PARA MULTIZONA)
    p.sistema_fv = {
        "modo": "multizona",
        "zonas": [
            {
                "nombre": "Zona 1",
                "modo": "paneles",
                "n_paneles": 10,
                "azimut": 180,
                "inclinacion": 15
            }
        ]
    }

    # 🔥 ELÉCTRICO (ESTO TE ROMPÍA TODO)
    p.electrico = {
        "vac": 240,
        "fases": 1,
        "fp": 1.0,
        "dist_dc_m": 15,
        "dist_ac_m": 25
    }

    return p


# ==========================================================
# DEBUG POR CAPAS
# ==========================================================

def debug_pipeline():

    print("\n🚀 DEBUG PROFUNDO FV ENGINE\n")

    datos = datos_debug()
    deps = construir_dependencias()

    dump(datos, "INPUT DATOSPROYECTO")

    # ======================================================
    # 1. SIZING
    # ======================================================
    sizing = deps.sizing.ejecutar(datos)
    dump(sizing, "1. SIZING")

    # ======================================================
    # 2. BUILDER PANELES (🔥 AQUÍ MUEREN MUCHAS COSAS)
    # ======================================================
    entrada_paneles = construir_entrada_paneles(datos, sizing)
    dump(entrada_paneles, "2. ENTRADA PANELES")

    # ======================================================
    # 3. PANELES (MULTIZONA)
    # ======================================================
    paneles = deps.paneles.ejecutar(entrada_paneles)
    dump(paneles, "3. RESULTADO PANELES")

    # ======================================================
    # 4. ENERGÍA
    # ======================================================
    energia = deps.energia.ejecutar(datos, sizing, paneles)
    dump(energia, "4. ENERGÍA")

    # ======================================================
    # 5. ELÉCTRICO (🔥 CRÍTICO EN TU CASO)
    # ======================================================
    electrical = deps.electrical.ejecutar(
        datos=datos,
        paneles=paneles,
        sizing=sizing
    )
    dump(electrical, "5. ELÉCTRICO")

    # ======================================================
    # 6. FINANZAS
    # ======================================================
    finanzas = deps.finanzas.ejecutar(datos, sizing, energia)
    dump(finanzas, "6. FINANZAS")

    print("\n✅ DEBUG COMPLETO\n")


# ==========================================================
# MAIN
# ==========================================================

if __name__ == "__main__":
    debug_pipeline()
