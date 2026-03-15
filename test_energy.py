from energy.orquestador_energia import ejecutar_motor_energia
from energy.contrato import EnergiaInput


entrada = EnergiaInput(

    # potencia sistema
    pdc_instalada_kw = 5.0,
    pac_nominal_kw = 4.5,

    # modo
    modo_simulacion = "mensual",

    # recurso solar
    hsp_12m = [
        5.5,5.7,6.0,6.2,6.3,6.1,
        5.8,5.7,5.6,5.4,5.2,5.1
    ],

    dias_mes = [
        31,28,31,30,31,30,
        31,31,30,31,30,31
    ],

    # orientación
    azimut_deg = 180,
    hemisferio = "norte",

    # pérdidas
    perdidas_dc_pct = 2,
    perdidas_ac_pct = 1.5,
    sombras_pct = 2
)


resultado = ejecutar_motor_energia(entrada)

print("\nRESULTADO DEL MOTOR\n")

print("OK:", resultado.ok)
print("Producción anual:", resultado.energia_util_anual, "kWh")

print("\nProducción mensual:")

for i,e in enumerate(resultado.energia_util_12m,1):
    print(f"Mes {i}: {round(e,2)} kWh")
