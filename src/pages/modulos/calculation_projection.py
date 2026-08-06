import os
from pathlib import Path
import json
import pandas as pd
import copy

# 1. Obtiene la ruta de este archivo script (calculos_proyeccion.py)
ruta_actual = Path(__file__).resolve()

# 2. Sube un nivel a la carpeta 'pages' (.parent) y entra a 'data/archivo.xlsx'
data_corp_projection_path = ruta_actual.parent.parent / "data" / "data_corp_projection.xlsx"

# NOTA: Dejamos la ruta original aquí por trazabilidad, pero abajo generamos la ruta específica por unidad.
json_data_web_path = ruta_actual.parent.parent / "data" / "data_web_user.json"

matriculas_iniciales_default = {
        'BÁSICA 1':         {'2027':24,'2028':22, '2029':21, '2030':20,'2031':20,
                            '2032':19,'2033':18,'2034':18,'2035':17},

        'BÁSICA 2':         {'2027':40,'2028':39, '2029':38, '2030':37,'2031':36,
                            '2032':32,'2033':30,'2034':29,'2035':28},

        'BÁSICA SF':        {'2027':36,'2028':35, '2029':34, '2030':33,'2031':30,
                            '2032':30,'2033':28,'2034':28,'2035':26},

        'MEDIA LOS ANDES':  {'2027':400,'2028':380, '2029':350, '2030':340,'2031':330,
                            '2032':300,'2033':300,'2034':300,'2035':290},

        'MEDIA SAN FELIPE': {'2027':257,'2028':250, '2029':240, '2030':240,'2031':240,
                            '2032':200,'2033':200,'2034':190,'2035':190},   
     }

# Capacidad máxima por unidad educativa (K para modelo logístico)
capacidad_maxima_default = {
    'BÁSICA 1':         {'K_max': 120, 'K_min': 100},  # PRE-KINDER
    'BÁSICA 2':         {'K_max': 120, 'K_min': 100},  # PRE-KINDER
    'BÁSICA SF':        {'K_max': 160, 'K_min': 100},  # PRE-KINDER
    'MEDIA LOS ANDES':  {'K_max': 480, 'K_min': 100},  # 1° MEDIO
    'MEDIA SAN FELIPE': {'K_max': 280, 'K_min': 100},  # 1° MEDIO
}




tasas_nuevos_alumnos = {
    'BÁSICA 1': {
        'PRE-KINDER': 0.000,
        'KINDER': -0.040,
        '1BÁSICO': -0.060,
        '2BÁSICO': 0.000,
        '3BÁSICO': 0.015,
        '4BÁSICO': -0.025,
        '5BÁSICO': -0.035,
        '6BÁSICO': -0.060,
        '7BÁSICO': 0.015,
        '8BÁSICO': -0.015,
    },
    'BÁSICA 2': {
        'PRE-KINDER': 0.000,
        'KINDER': -0.040,
        '1BÁSICO': -0.060,
        '2BÁSICO': 0.000,
        '3BÁSICO': 0.015,
        '4BÁSICO': -0.025,
        '5BÁSICO': -0.035,
        '6BÁSICO': -0.060,
        '7BÁSICO': 0.015,
        '8BÁSICO': -0.015,
    },
    'BÁSICA SF': {
        'PRE-KINDER': 0.000,
        'KINDER':  0.000,
        '1BÁSICO': 0.000,
        '2BÁSICO': 0.000,
        '3BÁSICO': 0.015,
        '4BÁSICO': -0.025,
        '5BÁSICO': -0.035,
        '6BÁSICO': 0.000,
        '7BÁSICO': 0.015,
        '8BÁSICO': -0.015,
    },
    'MEDIA LOS ANDES': {
        '1MEDIO': 0.000,
        '2MEDIO': -0.060,
        '3MEDIO': -0.080,
        '4MEDIO': 0.000,
    },
    'MEDIA SAN FELIPE': {
        '1MEDIO': -0.022,
        '2MEDIO': 0.017,
        '3MEDIO': 0.0,
        '4MEDIO': -0.013,
    },
}


def obtener_ruta_json_dinamica(uni_edu):
    """
    Toma la carpeta 'data' original del proyecto y construye una ruta
    de archivo única reemplazando espacios por guiones bajos.
    Ejemplo: .../data/datos_web_BÁSICA_1.json
    """
    nombre_limpio = str(uni_edu).replace(" ", "_")
    carpeta_data = data_corp_projection_path.parent
    return carpeta_data / f"datos_web_{nombre_limpio}.json"

def cargar_datos_consolidados(uni_edu):
    """
    Une el Excel maestro de Power Query con las ediciones hechas en la web.
    El Excel manda, pero la web puede actualizar o agregar nuevos años.
    """
    # 1. Leer datos base desde tu archivo Excel
    if data_corp_projection_path.exists():
        
        # filtrar el archivo excel según la unidad académica y luego eliminar la columna UNIDAD_ACADEMICA
                
        df_excel = pd.read_excel(data_corp_projection_path, sheet_name="data_mat_proj")
        df_excel_filtrado =  df_excel.query("UNIDAD_ACADEMICA == @uni_edu").copy()
        df_filtrado_final = df_excel_filtrado.drop(columns=['UNIDAD_ACADEMICA'])
        # Convertimos a diccionario string-int para procesarlo igual: {'2024': 2400, '2025': 2520}
        datos_finales = dict(zip(df_filtrado_final['PERIODO'].astype(str), df_filtrado_final['MATRICULA'].astype(int)))
    else:
        # Respaldo por si el Excel no está en la carpeta
        datos_finales = {"2024": 664, "2025": 652, "2026": 635}

    return datos_finales

def calcular_proyeccion_completa(lista_retencion, lista_nuevos, unidad_educativa, data_diccionario):
    """Genera el DataFrame usando el Excel mapeado como historial base."""
    #  Aquí cargamos datos excel
    reales_dict = cargar_datos_consolidados(unidad_educativa) 
    
    anios = [str(a) for a in range(2020, 2036)]
    registros = []
    
    # Identificar cuál es el último año real disponible (venga de Excel)
    if reales_dict:
        ultimo_anio_real = max([int(k) for k in reales_dict.keys()])
    else:
        ultimo_anio_real = 2026
    # Identificar cuál es el último año real disponible (venga de Excel o Web)
    #ultimo_anio_real = max([int(k) for k in reales_dict.keys()])

    #valor_actual = reales_dict[str(ultimo_anio_real)]

    # 2. Generar la proyección (esto te devuelve un DataFrame con columnas PERIODO y MATRICULA)
     # PASO CLAVE: Pasamos las dos listas al motor por niveles
     # Ajustamos la recepción de las dos variables desde el motor por nivel
    df_proj_corp, df_matriz_desglose = proyeccion_por_nivel(lista_retencion, lista_nuevos, unidad_educativa, data_diccionario)
    
    for anio in anios:
        anio_int = int(anio)
        
        if anio_int <= ultimo_anio_real:
            # Si el año existe en nuestros registros combinados, es un dato histórico real
            val = reales_dict.get(anio, None)
            registros.append({"Año": anio, "Valor": val, "Tipo": "Real"})
        else:
            # OPTIMIZACIÓN: Buscamos directamente el año en el DataFrame sin usar un ciclo 'for'
            fila_anio = df_proj_corp[df_proj_corp['PERIODO'] == anio]
            
            if not fila_anio.empty:
                # Extraemos el valor numérico de la matrícula de esa fila específica
                valor_actual = int(fila_anio['MATRICULA'].values[0])
                registros.append({"Año": anio, "Valor": valor_actual, "Tipo": "Proyección"})

           
            
    
    return pd.DataFrame(registros), str(ultimo_anio_real), df_matriz_desglose


def proyeccion_por_nivel(lista_retencion, lista_nuevos, unidad_educativa, diccionario_matriculas=None):

    """
    Motor analítico por niveles de enseñanza básica de Chile.
    lista_retencion: 10 porcentajes desde Pre-Kinder hasta 8° Básico.
    lista_nuevos: 10 cantidades de alumnos nuevos desde Pre-Kinder hasta 8° Básico.
    """
    if diccionario_matriculas is None:
        diccionario_matriculas = matriculas_iniciales_default
        
    # Obtener los datos específicos de la unidad seleccionada
    valores_inicales_uni_acad = diccionario_matriculas.get(unidad_educativa, {})


    # Data frame Original
    df_nivel = pd.read_excel(data_corp_projection_path, sheet_name="data_proj")

    # Data frame filtrado segun Unidad académica
    df_nivel_filtrado = df_nivel.query("UNIDAD_ACADEMICA == @unidad_educativa").copy()

    # Asegurar que las columnas de años sean string de inmediato
    df_nivel_filtrado.columns = df_nivel_filtrado.columns.astype(str)
    
    # 1. OPTIMIZACIÓN: Vectorizar tasas de sliders antes de los ciclos for
    tasas_decimales = [r / 100 if r > 1 else r for r in lista_retencion]

    # Obtener tasas para esta unidad educativa
    tasas_unidad = tasas_nuevos_alumnos.get(unidad_educativa, {})
    niveles_unidad = list(df_nivel_filtrado['NIVEL'])



    # Inicializar columnas del horizonte de proyección
    for year in range(2027, 2036):
        df_nivel_filtrado[str(year)] = 0.0

    # Determinar el total de niveles reales que tiene este establecimiento
    total_niveles = len(df_nivel_filtrado)

    # Control de seguridad: Si Dash mandó menos sliders de las filas que tiene el Excel, cortamos el error
    if len(tasas_decimales) < total_niveles:
        raise ValueError(f"Error de consistencia: El Excel tiene {total_niveles} cursos, pero se recibieron {len(tasas_decimales)} sliders.")

    # 2. CORRECCIÓN: Ciclo dinámico basado en la estructura real del colegio
    for periodo in range(2027, 2036):
        j = df_nivel_filtrado.columns.get_loc(str(periodo)) 
        j_anterior = df_nivel_filtrado.columns.get_loc(str(periodo - 1)) 
        estudiantes_carga_inicial = valores_inicales_uni_acad[str(periodo)]

        anios_transcurridos = periodo - 2027

        for nivel in range(total_niveles):
            tasa_ret_nivel = tasas_decimales[nivel]
            nombre_nivel = niveles_unidad[nivel]
        
            tasa_crecimiento = tasas_unidad.get(nombre_nivel, 0.0)


            alumnos_nuevos_base = lista_nuevos[nivel]

            # Tasa aplicada con guardia de seguridad contra negativos
            alumnos_nuevos_nivel = max(0, int(round(
                    alumnos_nuevos_base * ((1 + tasa_crecimiento) ** anios_transcurridos), 0
                )))

            if nivel == 0:
                # Pre-Kinder o 1° Medio en colegios de pura Media
                # Reemplazamos la búsqueda de '2026' fija por la columna inmediatamente anterior dinámicamente
                df_nivel_filtrado.iloc[nivel, j] =  estudiantes_carga_inicial + alumnos_nuevos_nivel
            else:
                # Flujo de cohorte tradicional (alumnos del año pasado en curso inferior * tasa de retención)
                alumnos_que_pasan = df_nivel_filtrado.iloc[nivel - 1, j_anterior] * tasa_ret_nivel
                total_calculado = alumnos_que_pasan + alumnos_nuevos_nivel
                df_nivel_filtrado.iloc[nivel, j] = int(round(total_calculado, 0))
    
    # --- PROCESAMIENTO DE TOTALES Y PIVOT (Tu sección final limpia) ---
    columnas_proyeccion = [str(y) for y in range(2027, 2036)]
    df_nivel_filtrado[columnas_proyeccion] = df_nivel_filtrado[columnas_proyeccion].astype(int)

    totales_años = df_nivel_filtrado.sum(numeric_only=True)
    
    fila_total = {
        'UNIDAD_ACADEMICA': df_nivel_filtrado['UNIDAD_ACADEMICA'].iloc[0],
        'NIVEL': 'TOTAL UNIDAD'
    }
    for col, suma in totales_años.items():
        fila_total[col] = suma

    df_total_fila = pd.DataFrame([fila_total])
    df_nivel_filtrado = pd.concat([df_nivel_filtrado, df_total_fila], ignore_index=True)

    columnas_años = [str(y) for y in range(2026, 2036)]
    df_nivel_filtrado[columnas_años] = df_nivel_filtrado[columnas_años].astype(int)

     # 🚀 PASO CLAVE: Guardamos una copia limpia de la matriz completa por niveles antes de filtrarla
    df_matriz_desglose = df_nivel_filtrado.drop(columns=['UNIDAD_ACADEMICA']).copy()

    df_totales_proyectados = df_nivel_filtrado.iloc[[-1]]
    df_totales_proyectados = df_totales_proyectados.drop(columns=['UNIDAD_ACADEMICA', 'NIVEL'])
    df_totales_proyectados = df_totales_proyectados.melt(var_name='PERIODO', value_name='MATRICULA')
    df_totales_proyectados = df_totales_proyectados[df_totales_proyectados['PERIODO'] != '2026']
    # el data frame final está forma por dos columnas una llamada PERIODO y otra MATRICULA, parte desde 2027
    
    
    
    return df_totales_proyectados, df_matriz_desglose


def proyeccion_corporativa(diccionario_matriculas=None, 
                           unidad_activa=None, 
                           lista_retencion_activa=None, 
                           lista_nuevos_activa=None,
                           escenarios_corp=None):
    """
    backend para calcular proyección de toda la corporacion
    Incluye 5 unidades educativas
    Período 2027 - 2035.
    """

    if diccionario_matriculas is None:
        diccionario_matriculas = matriculas_iniciales_default
        

    lista_data_corp=[]
    
    # Diccionario de unidades educativas
    ue_corp = ['BÁSICA 1','BÁSICA 2','BÁSICA SF','MEDIA LOS ANDES','MEDIA SAN FELIPE']
    
    # Data frame Original, la hoja data_proj ya biene con el año 2026
    df_nivel_corp = pd.read_excel(data_corp_projection_path, sheet_name="data_proj")
    
    # Asegurar que las columnas de años sean string de inmediato
    df_nivel_corp.columns = df_nivel_corp.columns.astype(str)
   
    
   

    for unidad in ue_corp: 
    
        # Después — usa sliders reales solo para la unidad activa
        if escenarios_corp and unidad in escenarios_corp:
            # Usar escenario guardado para esta unidad
            datos_escenario = escenarios_corp[unidad]
            lista_retencion_corp = datos_escenario["valores_retencion"]
            lista_nuevos_corp = datos_escenario["valores_nuevos"]
            # ← usar valores_tabla_inicial del escenario
            
            if "valores_tabla_inicial" in datos_escenario:
        
                diccionario_matriculas = copy.deepcopy(diccionario_matriculas)  # ← copia profunda
                # Solo copiar años 2027-2035, ignorar 2036 si existe
                diccionario_matriculas[unidad] = {
                    k: v for k, v in datos_escenario["valores_tabla_inicial"].items()
                    if k in [str(y) for y in range(2027, 2036)]
                }

    

        elif unidad == unidad_activa and lista_retencion_activa and lista_nuevos_activa:
            lista_retencion_corp = lista_retencion_activa
            lista_nuevos_corp = lista_nuevos_activa

        elif unidad in ['BÁSICA 1','BÁSICA 2','BÁSICA SF']:
            lista_retencion_corp = [95, 95, 95, 95, 95, 95, 95, 95, 95, 95]
            lista_nuevos_corp = [10, 10, 10, 10, 10, 10, 10, 10, 10, 10]
            
        else:
            lista_retencion_corp = [95, 95, 95, 95]
            lista_nuevos_corp = [10, 10, 10, 10]

        

        # Data frame filtrado segun Unidad académica
        df_nivel_filtrado_corp = df_nivel_corp.query("UNIDAD_ACADEMICA == @unidad").copy()

        if df_nivel_filtrado_corp.empty:
            continue
        
        
        # 1. OPTIMIZACIÓN: Vectorizar tasas de sliders antes de los ciclos for
        tasas_decimales = [r / 100 if r > 1 else r for r in lista_retencion_corp]
        
        # Matricula inicial extraida del diccionario, segun unidad educativa ciclo for
         #matricula_inicial_uni_edu = matriculas_iniciales[unidad]
        
        # Obtener los datos específicos de la unidad seleccionada
        matricula_inicial_uni_edu = diccionario_matriculas.get(unidad, {})


        # Inicializar columnas del horizonte de proyección
        for year in range(2027, 2036):
            df_nivel_filtrado_corp[str(year)] = 0.0

        # Determinar el total de niveles reales que tiene este establecimiento
        total_niveles = len(df_nivel_filtrado_corp)

        # Control de seguridad: Si Dash mandó menos sliders de las filas que tiene el Excel, cortamos el error
        if len(tasas_decimales) < total_niveles:
            raise ValueError(f"Error de consistencia: El Excel tiene {total_niveles} cursos, pero se recibieron {len(tasas_decimales)} sliders.")

        # Obtener tasas para esta unidad educativa
        tasas_unidad = tasas_nuevos_alumnos.get(unidad, {})
        niveles_unidad = list(df_nivel_filtrado_corp['NIVEL'])

        # 2. CORRECCIÓN: Ciclo dinámico basado en la estructura real del colegio
        for periodo in range(2027, 2036):
            j = df_nivel_filtrado_corp.columns.get_loc(str(periodo)) 
            j_anterior = df_nivel_filtrado_corp.columns.get_loc(str(periodo - 1)) 
            estudiantes_carga_inicial = matricula_inicial_uni_edu[str(periodo)]

            anios_transcurridos = periodo - 2027  # ← igual que en proyeccion_por_nivel

            for nivel in range(total_niveles):
                tasa_ret_nivel = tasas_decimales[nivel]
                nombre_nivel = niveles_unidad[nivel]  # ← nuevo
        
                # Obtener tasa de crecimiento para este nivel
                tasa_crecimiento = tasas_unidad.get(nombre_nivel, 0.0)  # ← nuevo

                # Alumnos nuevos con tasa aplicada — igual que proyeccion_por_nivel
                alumnos_nuevos_base = lista_nuevos_corp[nivel]
                alumnos_nuevos_nivel = max(0, int(round(
                        alumnos_nuevos_base * ((1 + tasa_crecimiento) ** anios_transcurridos), 0
                    )))  # ← nuevo

            
                if nivel == 0:
                    # Pre-Kinder o 1° Medio 
                    # Carga especial de estudiantes segun diccionario llamado matriculas_iniciales
                    df_nivel_filtrado_corp.iloc[nivel, j] =  estudiantes_carga_inicial + alumnos_nuevos_nivel
                else:
                    # Flujo de cohorte tradicional (alumnos del año pasado en curso inferior * tasa de retención)
                    alumnos_que_pasan = df_nivel_filtrado_corp.iloc[nivel - 1, j_anterior] * tasa_ret_nivel
                    total_calculado = alumnos_que_pasan + alumnos_nuevos_nivel
                    df_nivel_filtrado_corp.iloc[nivel, j] = int(round(total_calculado, 0))
        
        # --- PROCESAMIENTO DE TOTALES Y PIVOT (Tu sección final limpia) ---
        columnas_proyeccion = [str(y) for y in range(2027, 2036)]
        df_nivel_filtrado_corp[columnas_proyeccion] = df_nivel_filtrado_corp[columnas_proyeccion].astype(int)

        totales_años = df_nivel_filtrado_corp.sum(numeric_only=True)
        
        fila_total = {
            'UNIDAD_ACADEMICA': df_nivel_filtrado_corp['UNIDAD_ACADEMICA'].iloc[0],
            'NIVEL': 'TOTAL UNIDAD'
        }
        for col, suma in totales_años.items():
            fila_total[col] = suma

        df_total_fila = pd.DataFrame([fila_total])
        df_nivel_filtrado_corp = pd.concat([df_nivel_filtrado_corp, df_total_fila], ignore_index=True)

        # Columnas totales final, el excel ya biene con una columna 2026
        columnas_años = [str(y) for y in range(2026, 2036)]
        df_nivel_filtrado_corp[columnas_años] = df_nivel_filtrado_corp[columnas_años].astype(int)

        # Data frame formado solo por la última fila de la unidad académica con los totales por año
        # desde 2026 hasta 2035
        df_totales_proyectados_uni_edu = df_nivel_filtrado_corp.iloc[[-1]]

        # Data frame agregado como lista a la lista llamada lista_data_corp
        lista_data_corp.append(df_totales_proyectados_uni_edu)

    # 1.1 Unir los data frame de cada unidad educativa almacenados como lista
    df_totales_proyectados_corp = pd.concat(lista_data_corp, ignore_index=True)

    # 1.2 Eliminamos columnas de texto para poder operar matemáticamente
    df_totales_proyectados_corp = df_totales_proyectados_corp.drop(columns=['UNIDAD_ACADEMICA', 'NIVEL'])

    # 1.3. Sumamos todas las filas para consolidar la corporación en una única fila
    df_consolidado_fila = df_totales_proyectados_corp.sum(numeric_only=True).to_frame().T

     # 1.4. Aplicamos el melt (pivotear) para transponer los años a filas
    df_final_corp = df_consolidado_fila.melt(var_name='PERIODO', value_name='MATRICULA')
    
    # 1.5. Filtramos para quitar el año 2026 y asegurar tipos de datos correctos
    df_final_corp = df_final_corp[df_final_corp['PERIODO'] != '2026'].reset_index(drop=True)
    df_final_corp['MATRICULA'] = df_final_corp['MATRICULA'].astype(int)

    # el data frame final está forma por dos columnas una llamada PERIODO y otra MATRICULA, 
    # parte desde 2027 y llega hasta 2035

    # Agregar una columna al dataframe llamada Tipo, con el valor Proyectado
    df_final_corp["Tipo"]="Proyección"


    # Tomar el dataframe de excel sumar las filas del mismo año y genera un data frame histórico
    # de la corporacion
    # Data frame Original, la hoja data_mat_proj tiene matriculas históricas
    # desde 2024 hasta 2026 de cada unidad académica
    df_historicos_corp = pd.read_excel(data_corp_projection_path, sheet_name="data_mat_proj")

    # Eliminar columna UNIDAD ACADEMICA
    df_filtrado_historico_corp = df_historicos_corp.drop(columns=['UNIDAD_ACADEMICA'])

    # Sumar matrícula por año para tener el total de la corporación por año
    df_suma_historico_corp = df_filtrado_historico_corp.groupby('PERIODO')['MATRICULA'].sum().reset_index()

    # Agregar una columna llamada Tipo con el valor "Real"
    df_suma_historico_corp["Tipo"] = "Real"


    # Unir los dataframe: df_suma_historico_corp con df_final_corp
    df_completo_corp = pd.concat([df_suma_historico_corp, df_final_corp], ignore_index=True)

    # Convertir la columna 'periodo' a entero (int)
    df_completo_corp["PERIODO"] = df_completo_corp["PERIODO"].astype(int)
    
    # Ordenar por la columna 'PERIODO' de menor a mayor
    df_completo_corp = df_completo_corp.sort_values(by="PERIODO", ascending=True)

    # Reiniciar el índice final para que quede limpio
    df_completo_corp = df_completo_corp.reset_index(drop=True)

    # Construir diccionario de totales por unidad para tabla comparativa
    totales_por_unidad = {}
    for df_unidad in lista_data_corp:

        unidad_nombre = df_unidad['UNIDAD_ACADEMICA'].iloc[0]

        

        if escenarios_corp and unidad_nombre in escenarios_corp:

            totales_por_unidad[unidad_nombre] = {
            '2026': int(df_unidad['2026'].iloc[0]),
            '2035': int(df_unidad['2035'].iloc[0]),
            'default': False # tiene escenario
            }
        else:
            totales_por_unidad[unidad_nombre] = {
                        '2026': int(df_unidad['2026'].iloc[0]),
                        '2035': int(df_unidad['2035'].iloc[0]),
                        'default': True # no tiene escenario
            }

    

    return df_completo_corp, totales_por_unidad  # devuelve dataframe corporativo y totales por unidad


# Funciones especializadas en gestionar escenarios
def asegurar_carpeta_escenarios():

    """Usa disco persistente en Render, carpeta local en desarrollo."""
    ruta_render = Path("/opt/render/project/src/pages/data/escenarios")

    if ruta_render.exists():
        return ruta_render  # ← estamos en Render
    else:

        """Crea la subcarpeta de escenarios si no existe."""
        ruta_local = data_corp_projection_path.parent / "escenarios"
        ruta_local.mkdir(parents=True, exist_ok=True)

    return ruta_local

def guardar_escenario_simulacion(unidad_edu, nombre_escenario, lista_ret, lista_nuevos, df_resultado, valores_tabla):
    """Guarda el escenario completo en un archivo JSON estructurado."""
    if not nombre_escenario:
        return False, "Por favor, ingresa un nombre válido para el escenario."
        
    carpeta = asegurar_carpeta_escenarios()
    # Limpiamos el nombre para que sea un nombre de archivo válido
    nombre_archivo = f"{unidad_edu}_{nombre_escenario}.json".replace(" ", "_")
    ruta_final = carpeta / nombre_archivo
    
    # Convertimos el DataFrame a un formato de lista de diccionarios para JSON
    tabla_datos = df_resultado.to_dict(orient="records")
    
    escenario_dict = {
        "nombre_escenario": nombre_escenario,
        "unidad_educativa": unidad_edu,
        "valores_retencion": lista_ret,
        "valores_nuevos": lista_nuevos,
        "valores_tabla_inicial": valores_tabla,  # ← nuevo campo
        "tabla_proyeccion": tabla_datos
    }
    
    with open(ruta_final, "w", encoding="utf-8") as f:
        json.dump(escenario_dict, f, indent=4, ensure_ascii=False)
        
    return True, f"Escenario '{nombre_escenario}' guardado con éxito."

def listar_escenarios_por_unidad(unidad_edu):
    """Busca todos los JSON guardados que correspondan a la unidad educativa actual."""
    carpeta = asegurar_carpeta_escenarios()
    archivos = carpeta.glob(f"{unidad_edu.replace(' ', '_')}_*.json")
    
    opciones = []
    for archivo in archivos:
        with open(archivo, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Guardamos la ruta del archivo como valor y el nombre del escenario como etiqueta
            opciones.append({"label": data["nombre_escenario"], "value": str(archivo)})

    return opciones

def cargar_datos_escenario(ruta_archivo):
    """Lee el archivo JSON seleccionado y devuelve sus parámetros."""
    if not os.path.exists(ruta_archivo):
        return None
    with open(ruta_archivo, "r", encoding="utf-8") as f:
        return json.load(f)

def eliminar_archivo_escenario(ruta_archivo):
    """Borra físicamente el archivo JSON del escenario seleccionado."""
    if not ruta_archivo or not os.path.exists(ruta_archivo):
        return False, "⚠️ El archivo del escenario no existe o ya fue eliminado."
    
    try:
        os.remove(ruta_archivo)
        return True, "🗑️ Escenario eliminado con éxito del sistema."
    except Exception as e:
        return False, f"❌ Error al intentar eliminar el archivo: {str(e)}"

def listar_todos_escenarios_agrupados():
    """Devuelve todos los escenarios guardados agrupados por unidad educativa para un dropdown múltiple."""
    carpeta = asegurar_carpeta_escenarios()
    ue_corp = ['BÁSICA 1', 'BÁSICA 2', 'BÁSICA SF', 'MEDIA LOS ANDES', 'MEDIA SAN FELIPE']
    
    grupos = []
    for unidad in ue_corp:
        archivos = carpeta.glob(f"{unidad.replace(' ', '_')}_*.json")
        opciones_unidad = []
        
        for archivo in archivos:
            with open(archivo, "r", encoding="utf-8") as f:
                data = json.load(f)
                opciones_unidad.append({
                    "label": data["nombre_escenario"],
                    "value": str(archivo)
                })
        
        if opciones_unidad:  # Solo agregar el grupo si tiene escenarios
            grupos.append({
                "label": unidad,
                "value": unidad,
                "disabled": True  # Título del grupo no seleccionable
            })
            grupos.extend(opciones_unidad)
    
    return grupos

def guardar_escenario_corporativo(nombre_escenario, escenarios_por_unidad, df_resultado):
    """Guarda la receta de escenarios corporativos y el DataFrame resultado."""

    if not nombre_escenario:
        return False, "Por favor, ingresa un nombre válido para el escenario."
    
    carpeta = asegurar_carpeta_escenarios()
    nombre_archivo = f"CORPORACIÓN_{nombre_escenario}.json".replace(" ", "_")
    ruta_final = carpeta / nombre_archivo
    
    tabla_datos = df_resultado.to_dict(orient="records")
    
   # Guardar solo nombre de archivo en vez de ruta absoluta
    escenarios_por_unidad_relativo = {}
    for unidad, ruta in escenarios_por_unidad.items():
        if ruta == "default":
            escenarios_por_unidad_relativo[unidad] = "default"
        else:
            escenarios_por_unidad_relativo[unidad] = Path(ruta).name
    
    escenario_dict = {
        "nombre_escenario": nombre_escenario,
        "tipo": "corporativo",
        "escenarios_por_unidad": escenarios_por_unidad_relativo,
        "tabla_proyeccion": tabla_datos
    }
    
    with open(ruta_final, "w", encoding="utf-8") as f:
        json.dump(escenario_dict, f, indent=4, ensure_ascii=False)
    
    return True, f"Escenario corporativo '{nombre_escenario}' guardado con éxito."

# Funciones para carga inicial de estudiantes lineal y logística
def modelo_lineal(p0, pendiente):
    """
    Calcula la proyección lineal de matrícula inicial desde 2027 hasta 2035.
    p0: matrícula inicial año 2026
    pendiente: alumnos que se agregan o restan por año (puede ser negativo)
    Retorna diccionario {año: valor}
    """
    resultado = {}
    for i, anio in enumerate(range(2027, 2036), start=1):
        # Fórmula lineal: P0 + pendiente * años transcurridos
        valor = int(round(p0 + pendiente * i, 0))
        # Guardia: nunca menos de 0 alumnos
        resultado[str(anio)] = max(0, valor)
        
    return resultado

def modelo_logistico_crecimiento(p0, k_max, r):
    """
    Calcula proyección logística de crecimiento desde 2027 hasta 2035.
    p0: población inicial (matrícula 2026)
    k_max: capacidad máxima de estudiantes
    r: tasa de crecimiento [0.05 - 0.5]
    Fórmula: K / (1 + ((K - P0) / P0) * e^(-r*t))
    Retorna diccionario {año: valor}
    """
    import math
    resultado = {}
    for i, anio in enumerate(range(2027, 2036), start=1):
        # t = años transcurridos desde 2026
        denominador = 1 + ((k_max - p0) / p0) * math.exp(-r * i)
        valor = int(round(k_max / denominador, 0))
        resultado[str(anio)] = max(0, valor)
    return resultado

def modelo_logistico_decrecimiento(p0, k_min, r):
    """
    Calcula proyección logística de decrecimiento desde 2027 hasta 2035.
    p0: población inicial (matrícula 2026)
    k_min: límite inferior de estudiantes (mínimo viable)
    r: tasa de decrecimiento [0.05 - 0.5]
    Fórmula: K + (P0 - K) * 2 / (1 + e^(r*t))
    Retorna diccionario {año: valor}
    """
    import math
    resultado = {}
    for i, anio in enumerate(range(2027, 2036), start=1):
        # t = años transcurridos desde 2026
        valor = int(round(k_min + (p0 - k_min) * 2 / (1 + math.exp(r * i)), 0))
        # Guardia: nunca menos que k_min
        resultado[str(anio)] = max(k_min, valor)
    return resultado