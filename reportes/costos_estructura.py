import pandas as pd

archivo = "Estructura_datos.xlsx"
precios = pd.read_excel(archivo, sheet_name="Materiales")

# diccionario de precios
dict_precios = dict(zip(precios["CODIGO"], precios["Costo Unitario"]))

CUADRILLA = 1250

resultados = []

xls = pd.ExcelFile(archivo)

for hoja in xls.sheet_names:

    if hoja in ["Materiales", "indice", "Internos", "conectores"]:
        continue

    df = pd.read_excel(xls, sheet_name=hoja)

    if "COD. ENEE" not in df.columns:
        continue

    total_material = 0

    for _, row in df.iterrows():

        codigo = row["COD. ENEE"]
        cantidad = row["34.5"] if "34.5" in df.columns else 0

        precio = dict_precios.get(codigo, 0)

        total_material += cantidad * precio

    equipos = total_material * 0.20
    mo = CUADRILLA * 0.25
    utilidad = (total_material + equipos + mo) * 0.15
    total = total_material + equipos + mo + utilidad

    resultados.append({
        "Estructura": hoja,
        "Material": total_material,
        "Equipos": equipos,
        "MO": mo,
        "Utilidad": utilidad,
        "TOTAL": total
    })

df_final = pd.DataFrame(resultados)
df_final.to_excel("costos_estructuras.xlsx", index=False)

print(df_final)
