from panel.potencia_panel import *

entrada = PotenciaPanelInput(

    irradiancia_poa_wm2=900,
    temperatura_celda_c=52,

    pmax_stc_w=550,
    vmp_stc_v=41.5,
    voc_stc_v=49.5,

    coef_pmax_pct_per_c=-0.004,
    coef_voc_pct_per_c=-0.0028,
    coef_vmp_pct_per_c=-0.003
)

resultado = calcular_potencia_panel(entrada)

print(resultado)
