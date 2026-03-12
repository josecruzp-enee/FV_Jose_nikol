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

    # ejemplo mínimo de proyecto

    return Datosproyecto(
        cliente="DEBUG",
        ubicacion="TEST",
        consumo_12m=[500]*12,
        tarifa_energia=5.0,
        cargos_fijos=100
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
