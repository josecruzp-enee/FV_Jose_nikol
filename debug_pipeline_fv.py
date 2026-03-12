import pprint
import inspect

from core.aplicacion.dependencias import construir_dependencias
from core.aplicacion.orquestador_estudio import ejecutar_estudio
from core.dominio.modelo import Datosproyecto


MAX_DEPTH = 1000


def dump(title, obj, depth=3):
    print("\n" + "=" * 80)
    print(title)
    print("-" * 80)
    try:
        pprint.pprint(obj, depth=depth)
    except Exception as e:
        print("Error printing:", e)
    print("=" * 80)


def trace_function(fn, name):

    def wrapper(*args, **kwargs):

        print("\n")
        print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        print("ENTER:", name)
        print("ARGS:")
        dump("args", args)
        dump("kwargs", kwargs)

        result = fn(*args, **kwargs)

        print("EXIT:", name)
        dump("result", result)

        print("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<")

        return result

    return wrapper


def instrument_dependencies(deps):

    # envolver cada puerto para trazado

    deps.sizing.ejecutar = trace_function(
        deps.sizing.ejecutar, "sizing"
    )

    deps.paneles.ejecutar = trace_function(
        deps.paneles.ejecutar, "paneles"
    )

    deps.energia.ejecutar = trace_function(
        deps.energia.ejecutar, "energia"
    )

    deps.nec.ejecutar = trace_function(
        deps.nec.ejecutar, "nec"
    )

    deps.finanzas.ejecutar = trace_function(
        deps.finanzas.ejecutar, "finanzas"
    )

    return deps


def construir_datos_demo():

    return Datosproyecto(

        cliente="DEBUG",
        ubicacion="TEST",

        consumo_12m=[500]*12,

        # producción base Honduras aprox
        prod_base_kwh_kwp_mes=[
            140,145,150,148,140,135,
            132,134,130,128,135,138
        ],

        # factores mensuales FV
        factores_fv_12m=[
            1,1,1,1,1,1,1,1,1,1,1,1
        ],

        cobertura_objetivo=1.0,

        # costos
        costo_usd_kwp=900,

        # financiero
        tcambio=24.5,
        tasa_anual=0.12,
        plazo_anios=10,
        porcentaje_financiado=0.7
    )
def main():

    print("\n\n========== DEBUG PIPELINE FV ENGINE ==========\n")

    deps = construir_dependencias()

    deps = instrument_dependencies(deps)

    datos = construir_datos_demo()

    dump("INPUT DATOSPROYECTO", datos)

    resultado = ejecutar_estudio(datos, deps)

    dump("RESULTADO FINAL", resultado)

    print("\n========== FIN DEBUG ==========\n")


if __name__ == "__main__":
    main()
