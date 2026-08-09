import pandas as pd

escenarios_corp = {'BÁSICA 1': 
                   {'nombre_escenario': 'P01_BAS01_opt', 
                    'unidad_educativa': 'BÁSICA 1', 
                    'valores_retencion': [95, 87, 80, 92, 80, 85, 90, 90, 85, 90], 
                    'valores_nuevos': [0, 20, 20, 8, 15, 13, 12, 19, 13, 17], 
                    'valores_tabla_inicial': {'2027': 30, '2028': 33, '2029': 36, '2030': 39, '2031': 42, '2032': 46, '2033': 50, '2034': 55, '2035': 60}, 
                    'tabla_proyeccion': [{'Año': '2020', 'Valor': 901, 'Tipo': 'Real'}, 
                                         {'Año': '2021', 'Valor': 863, 'Tipo': 'Real'}, 
                                         {'Año': '2022', 'Valor': 819, 'Tipo': 'Real'}, 
                                         {'Año': '2023', 'Valor': 746, 'Tipo': 'Real'}, 
                                         {'Año': '2024', 'Valor': 645, 'Tipo': 'Real'}, 
                                         {'Año': '2025', 'Valor': 648, 'Tipo': 'Real'}, 
                                         {'Año': '2026', 'Valor': 639, 'Tipo': 'Real'}, 
                                         {'Año': '2027', 'Valor': 640, 'Tipo': 'Proyección'}, 
                                         {'Año': '2028', 'Valor': 654, 'Tipo': 'Proyección'}, 
                                         {'Año': '2029', 'Valor': 636, 'Tipo': 'Proyección'}, 
                                         {'Año': '2030', 'Valor': 636, 'Tipo': 'Proyección'}, 
                                         {'Año': '2031', 'Valor': 639, 'Tipo': 'Proyección'}, 
                                         {'Año': '2032', 'Valor': 642, 'Tipo': 'Proyección'}, 
                                         {'Año': '2033', 'Valor': 653, 'Tipo': 'Proyección'}, 
                                         {'Año': '2034', 'Valor': 661, 'Tipo': 'Proyección'}, 
                                         {'Año': '2035', 'Valor': 674, 'Tipo': 'Proyección'}]}, 
                    'BÁSICA 2': 
                    {'nombre_escenario': 'P01_BAS02_opt', 
                     'unidad_educativa': 'BÁSICA 2', 'valores_retencion': [95, 87, 84, 95, 81, 91, 88, 92, 89, 88], 
                     'valores_nuevos': [0, 9, 19, 7, 11, 13, 18, 14, 24, 20], 'valores_tabla_inicial': {'2027': 46, '2028': 48, '2029': 49, '2030': 51, '2031': 53, '2032': 54, '2033': 56, '2034': 58, '2035': 60}, 'tabla_proyeccion': [{'Año': '2020', 'Valor': 750, 'Tipo': 'Real'}, {'Año': '2021', 'Valor': 755, 'Tipo': 'Real'}, {'Año': '2022', 'Valor': 705, 'Tipo': 'Real'}, {'Año': '2023', 'Valor': 653, 'Tipo': 'Real'}, {'Año': '2024', 'Valor': 656, 'Tipo': 'Real'}, {'Año': '2025', 'Valor': 650, 'Tipo': 'Real'}, {'Año': '2026', 'Valor': 674, 'Tipo': 'Real'}, {'Año': '2027', 'Valor': 700, 'Tipo': 'Proyección'}, {'Año': '2028', 'Valor': 715, 'Tipo': 'Proyección'}, {'Año': '2029', 'Valor': 712, 'Tipo': 'Proyección'}, {'Año': '2030', 'Valor': 707, 'Tipo': 'Proyección'}, {'Año': '2031', 'Valor': 707, 'Tipo': 'Proyección'}, {'Año': '2032', 'Valor': 705, 'Tipo': 'Proyección'}, {'Año': '2033', 'Valor': 713, 'Tipo': 'Proyección'}, {'Año': '2034', 'Valor': 709, 'Tipo': 'Proyección'}, {'Año': '2035', 'Valor': 713, 'Tipo': 'Proyección'}]}, 'BÁSICA SF': {'nombre_escenario': 'P02_BAS_SF_opt', 'unidad_educativa': 'BÁSICA SF', 'valores_retencion': [95, 89, 92, 86, 87, 90, 90, 91, 89, 88], 'valores_nuevos': [0, 12, 28, 14, 12, 16, 30, 19, 25, 38], 'valores_tabla_inicial': {'2027': 44, '2028': 48, '2029': 52, '2030': 55, '2031': 58, '2032': 60, '2033': 62, '2034': 64, '2035': 65}, 'tabla_proyeccion': [{'Año': '2020', 'Valor': 1305, 'Tipo': 'Real'}, {'Año': '2021', 'Valor': 1260, 'Tipo': 'Real'}, {'Año': '2022', 'Valor': 1140, 'Tipo': 'Real'}, {'Año': '2023', 'Valor': 1117, 'Tipo': 'Real'}, {'Año': '2024', 'Valor': 1024, 'Tipo': 'Real'}, {'Año': '2025', 'Valor': 1006, 'Tipo': 'Real'}, {'Año': '2026', 'Valor': 983, 'Tipo': 'Real'}, {'Año': '2027', 'Valor': 983, 'Tipo': 'Proyección'}, {'Año': '2028', 'Valor': 989, 'Tipo': 'Proyección'}, {'Año': '2029', 'Valor': 978, 'Tipo': 'Proyección'}, {'Año': '2030', 'Valor': 957, 'Tipo': 'Proyección'}, {'Año': '2031', 'Valor': 955, 'Tipo': 'Proyección'}, {'Año': '2032', 'Valor': 960, 'Tipo': 'Proyección'}, {'Año': '2033', 'Valor': 962, 'Tipo': 'Proyección'}, {'Año': '2034', 'Valor': 972, 'Tipo': 'Proyección'}, {'Año': '2035', 'Valor': 988, 'Tipo': 'Proyección'}]}, 'MEDIA LOS ANDES': {'nombre_escenario': 'P03_MEDIA_LA_optimista', 'unidad_educativa': 'MEDIA LOS ANDES', 'valores_retencion': [95, 84, 90, 94], 'valores_nuevos': [0, 48, 29, 8], 'valores_tabla_inicial': {'2027': 393, '2028': 382, '2029': 413, '2030': 401, '2031': 392, '2032': 388, '2033': 374, '2034': 379, '2035': 367}, 'tabla_proyeccion': [{'Año': '2020', 'Valor': 1177, 'Tipo': 'Real'}, {'Año': '2021', 'Valor': 1206, 'Tipo': 'Real'}, {'Año': '2022', 'Valor': 1184, 'Tipo': 'Real'}, {'Año': '2023', 'Valor': 1016, 'Tipo': 'Real'}, {'Año': '2024', 'Valor': 1058, 'Tipo': 'Real'}, {'Año': '2025', 'Valor': 1125, 'Tipo': 'Real'}, {'Año': '2026', 'Valor': 1285, 'Tipo': 'Real'}, {'Año': '2027', 'Valor': 1427, 'Tipo': 'Proyección'}, {'Año': '2028', 'Valor': 1470, 'Tipo': 'Proyección'}, {'Año': '2029', 'Valor': 1511, 'Tipo': 'Proyección'}, {'Año': '2030', 'Valor': 1486, 'Tipo': 'Proyección'}, {'Año': '2031', 'Valor': 1472, 'Tipo': 'Proyección'}, {'Año': '2032', 'Valor': 1463, 'Tipo': 'Proyección'}, {'Año': '2033', 'Valor': 1422, 'Tipo': 'Proyección'}, {'Año': '2034', 'Valor': 1396, 'Tipo': 'Proyección'}, {'Año': '2035', 'Valor': 1367, 'Tipo': 'Proyección'}]}, 'MEDIA SAN FELIPE': {'nombre_escenario': 'P03_MEDIA_SF_opt', 'unidad_educativa': 'MEDIA SAN FELIPE', 'valores_retencion': [95, 88, 95, 92], 'valores_nuevos': [0, 41, 47, 10], 'valores_tabla_inicial': {'2027': 250, '2028': 244, '2029': 238, '2030': 233, '2031': 228, '2032': 224, '2033': 221, '2034': 218, '2035': 216}, 'tabla_proyeccion': [{'Año': '2020', 'Valor': 875, 'Tipo': 'Real'}, {'Año': '2021', 'Valor': 866, 'Tipo': 'Real'}, {'Año': '2022', 'Valor': 849, 'Tipo': 'Real'}, {'Año': '2023', 'Valor': 807, 'Tipo': 'Real'}, {'Año': '2024', 'Valor': 802, 'Tipo': 'Real'}, {'Año': '2025', 'Valor': 859, 'Tipo': 'Real'}, {'Año': '2026', 'Valor': 922, 'Tipo': 'Real'}, {'Año': '2027', 'Valor': 1009, 'Tipo': 'Proyección'}, {'Año': '2028', 'Valor': 1052, 'Tipo': 'Proyección'}, {'Año': '2029', 'Valor': 1080, 'Tipo': 'Proyección'}, {'Año': '2030', 'Valor': 1058, 'Tipo': 'Proyección'}, {'Año': '2031', 'Valor': 1040, 'Tipo': 'Proyección'}, {'Año': '2032', 'Valor': 1026, 'Tipo': 'Proyección'}, {'Año': '2033', 'Valor': 1014, 'Tipo': 'Proyección'}, {'Año': '2034', 'Valor': 1003, 'Tipo': 'Proyección'}, {'Año': '2035', 'Valor': 994, 'Tipo': 'Proyección'}]}}

# region FILTRAR escenarios corporativos segun año 1 y año 2
# Extraer clave tabla_proyeccion de cada unidad educativa
clave_extraer = "tabla_proyeccion"

# Crear nuevo diccionario solo con clave principal y tabla de proyeccion
nuevo_diccionario = {
    clave_principal: sub_diccionario[clave_extraer]
    for clave_principal, sub_diccionario in escenarios_corp.items()
    if clave_extraer in sub_diccionario
}

# Calve Tipo sera eliminada del diccionario
clave_borrar = "Tipo"

# Crear nuevo diccionario con clave principal eliminando clave Tipo
datos_limpios = {
    clave_principal: [
        {key_dict: value_dict for key_dict, value_dict in sub_dict.items() if key_dict != clave_borrar}
        for sub_dict in lista_dict
    ]
    for clave_principal, lista_dict in nuevo_diccionario.items()
}

# Crear una lista de diccionario, cada diccionario tendra UNIDAD_ACADEMICA; Año y Valor
filas_grafico_comparativo = []
for principal, lista_sub in datos_limpios.items():
    for sub in lista_sub:
        filas_grafico_comparativo.append({
            'UNIDAD_ACADEMICA': principal,
            'Año': int(sub['Año']),  # Convertir el año a número
            'Valor': sub['Valor']
        })

# Crear un DataFrame inicial con tres columnas, cada diccionario es una fila
df_largo_grafico_comparativo = pd.DataFrame(filas_grafico_comparativo)

# Transformar (pivotear) para que los años sean columnas
df_ancho_grafico_comparativo = df_largo_grafico_comparativo.pivot(index='UNIDAD_ACADEMICA', columns='Año', values='Valor').reset_index()
df_ancho_grafico_comparativo.columns.name = None # eliminar nombre de la columna index


# Crear nuevo DataFrame filtrando solo las columnas deseadas
columnas_seleccionadas = ['UNIDAD_ACADEMICA', 2026, 2027]
df_nuevo_comparativo = df_ancho_grafico_comparativo[columnas_seleccionadas]

total_mat_year_01 = df_nuevo_comparativo[2026].sum()
total_mat_year_02 = df_nuevo_comparativo[2027].sum()
fila_total_comparativa = {'UNIDAD_ACADEMICA': 'CORPORACION', 2026: total_mat_year_01, 2027: total_mat_year_02}
df_total_comparativa = pd.DataFrame([fila_total_comparativa])

df_final_comparativo = pd.concat([df_nuevo_comparativo, df_total_comparativa], ignore_index=True)
df_final_comparativo['% Variación'] = (df_final_comparativo[2027]-df_final_comparativo[2026])/df_final_comparativo[2026]

print(df_final_comparativo)

# endregion




