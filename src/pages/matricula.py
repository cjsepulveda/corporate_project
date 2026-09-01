import pathlib
from dash import dcc, html, Input, Output, callback, register_page
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import datetime
from datetime import timedelta
import dash_bootstrap_components as dbc
# Importamos la función de actualización desde el archivo secundario llamado 
# generador_mapa.py, que se encuentra en la carpeta modulos dentro de pages.
from pages.modulos.generador_mapa import actualizar_mapa_comunas 


register_page(
    __name__,
    name='Matrícula',
    top_nav=True,
    path='/matricula'
)

PATH = pathlib.Path(__file__).parent
DATA_PATH = PATH.joinpath("data").resolve()

# Caching de datos para evitar leer el Excel en cada importación del módulo.
# La lectura se hará solo la primera vez que se necesiten los datos.
_df01 = _df02 = _df03 = _df04 = _df05 = _df06 = _df07= None
_tabla_proyeccion = None


def load_data():
    """Carga los datos de Excel solo una vez por proceso."""
    global _df01, _df02, _df03, _df04, _df05, _df06, _df07, _df08
    # Si ya se cargaron los datos, no hacemos nada.
    if _df01 is not None:
        return

    workbook = DATA_PATH.joinpath('mat_2026.xlsx')
    _df01 = pd.read_excel(workbook, sheet_name='mat_2026')
    _df02 = pd.read_excel(workbook, sheet_name='proyeccion_2026')
    _df03 = pd.read_excel(workbook, sheet_name='genero')
    _df04 = pd.read_excel(workbook, sheet_name='mat_time')
    _df05 = pd.read_excel(workbook, sheet_name='origen_estudiantes')
    _df06 = pd.read_excel(workbook, sheet_name='origen_colegios')
    _df07 = pd.read_excel(workbook, sheet_name='com_est')
    _df08 = pd.read_excel(workbook, sheet_name='cantidad_cursos')

    # Convertir la columna de fechas solo una vez, al leer los datos.
    _df04['MATRICULA'] = pd.to_datetime(_df04['MATRICULA'], errors='coerce')


def get_tabla_proyeccion():
    """Devuelve la tabla de proyección, construida solo una vez."""
    global _tabla_proyeccion
    load_data()
    if _tabla_proyeccion is not None:
        return _tabla_proyeccion

    # Formatear el DataFrame de proyección y construir la tabla Dash una sola vez.
    df02_redondeado = _df02.round({'% CRECIMIENTO': 3, '% ALCANZADO PROYECCIÓN': 3})
    df02_redondeado['% CRECIMIENTO'] = df02_redondeado['% CRECIMIENTO'].map('{:.2%}'.format)
    df02_redondeado['% ALCANZADO PROYECCIÓN'] = df02_redondeado['% ALCANZADO PROYECCIÓN'].map('{:.2%}'.format)
    df02_nuevo = df02_redondeado.rename(columns={'% CRECIMIENTO': 'VARIACION PORCENTUAL SAE 2026 Y MATRÍCULA 2025'})

    _tabla_proyeccion = dbc.Table.from_dataframe(df02_nuevo,
                                               striped=True,
                                               bordered=True,
                                               hover=True,
                                               color='dark',
                                               className="align-middle",
                                               style={'width': '90%',
                                                      'margin': 'auto',
                                                      'textAlign': 'center'
                                                      })
    return _tabla_proyeccion


def calculate_origin(df_origen, unidad_edu=None):
    """Calcula los valores y la tabla de origen según la unidad educativa."""

    interno = df_origen['INTERNO'].sum()
    nuevo_sae = df_origen['NUEVO-SAE'].sum()
    anotate_lista = df_origen['ANOTATE-LISTA'].sum()
    categorias_origen = ['Interno', 'Nuevo SAE', 'Anotate Lista']
    valores_origen = [interno, nuevo_sae, anotate_lista]


    if unidad_edu == 'Corporacion':
        tabla_origen = df_origen.groupby('UE').sum().reset_index()
        tabla_origen = tabla_origen.drop(columns=['NIVEL'], errors='ignore')
        fila_extra_general = {'Origen': 'TOTAL', 'INTERNO': interno, 'NUEVO-SAE': nuevo_sae, 'ANOTATE-LISTA': anotate_lista}
        tabla_origen.rename(columns={'UE': 'Origen'}, inplace=True)


    else:
        tabla_origen = df_origen.copy()
        tabla_origen = tabla_origen.drop(columns=['UE'], errors='ignore')
        fila_extra_general = {'NIVEL': 'TOTAL', 'INTERNO': interno, 'NUEVO-SAE': nuevo_sae, 'ANOTATE-LISTA': anotate_lista}
        
    df_fila_extra_general = pd.DataFrame([fila_extra_general])
    tabla_origen= pd.concat([tabla_origen, df_fila_extra_general], ignore_index=True)
    tabla_origen['TOTAL NIVEL']=tabla_origen.select_dtypes(include='number').sum(axis=1)

    
    
    return categorias_origen, valores_origen, tabla_origen


def build_evolution_df(df_time, unidad_edu=None):
    """Crea el DataFrame de evolución de matrícula por fecha."""
    if unidad_edu and unidad_edu != 'Corporacion':
        df_filtered = df_time.query("UE == @unidad_edu").copy()
    else:
        df_filtered = df_time

    df_agg = df_filtered.groupby('MATRICULA').sum().reset_index()
    df_agg = df_agg.drop(columns=['UE'], errors='ignore')
    df_agg['accumulated'] = df_agg['ESTUDIANTES'].cumsum()
    return df_agg


def get_gender_counts(df_genero, unidad_edu=None):
    """Devuelve los conteos de género para la unidad educativa o la corporación."""
    if unidad_edu and unidad_edu != 'Corporacion':
        df_filtered = df_genero.query("`UNIDAD ACADÉMICA` == @unidad_edu")
    else:
        df_filtered = df_genero

    df_grouped = df_filtered.groupby('Sexo').sum().reset_index()
    df_grouped = df_grouped.drop(columns=['UNIDAD ACADÉMICA'], errors='ignore')
    df_dict = df_grouped.set_index('Sexo')['RECUENTO'].to_dict()
    return df_dict.get('F', 0), df_dict.get('M', 0)


def build_summary_df(df_source, unidad_edu=None):
    """Construye el DataFrame de resumen con fila GENERAL y calcula % Meta."""

    if unidad_edu and unidad_edu != 'Corporacion':
        df_filtered = df_source.query("UNI_EDU == @unidad_edu")
        df_clean = df_filtered.drop(columns=['UNI_EDU', '% META'], errors='ignore')
        graph_x_axes = 'NIVEL'
        color_bar = 'NIVEL'
        etiqueta = 'Niveles'
        total_label = 'GENERAL'
        label_col = 'NIVEL'
    else:
        df_filtered = df_source.groupby('UNI_EDU').sum().reset_index()
        df_clean = df_filtered.drop(columns=['NIVEL', '% META'], errors='ignore')
        graph_x_axes = 'UNI_EDU'
        color_bar = 'UNI_EDU'

        colors = ['#FF5733', '#33FF57', '#3357FF', '#F3FF33', '#FF33F3']

        etiqueta = 'Unidades Educativas'
        total_label = 'GENERAL'
        label_col = 'UNI_EDU'

    total_SAE_2026 = df_clean['SAE_2026'].sum()
    total_MAT_2026 = df_clean['MAT_2026'].sum()
    fila_total = {label_col: total_label, 'SAE_2026': total_SAE_2026, 'MAT_2026': total_MAT_2026}
    df_total = pd.DataFrame([fila_total])
    df_result = pd.concat([df_clean, df_total], ignore_index=True)
    df_result['% Meta'] = (df_result['MAT_2026'] / df_result['SAE_2026']) * 100

    return df_result, graph_x_axes, color_bar, etiqueta


def get_origin_school(df_institution, unidad_edu=None):
    """Construye el DataFrame para el colegio de origen de los estudiantes."""

    if unidad_edu and unidad_edu != 'Corporacion':
       df_filtered_institution= df_institution[(df_institution['ESTUDIANTES'] >= 10) & (df_institution['UE'] == unidad_edu)]
    else:
        df_filtered_institution = df_institution[df_institution['ESTUDIANTES'] >= 10]     
        
    return df_filtered_institution

def origin_city_student(df_city, unidad_edu=None):
    """Construye el DataFrame para la ciudad de origen de los estudiantes."""

    if unidad_edu and unidad_edu != 'Corporacion':
        df_filtered_city = df_city.query("UE == @unidad_edu").copy()
        df_grouped_city = df_filtered_city.sort_values('Estudiantes', ascending=False).reset_index(drop=True)
        
        total_estudiantes_comuna = df_filtered_city['Estudiantes'].sum()
        fila_total = {'UE': 'General', 'Comuna': 'Todas', 'Estudiantes': total_estudiantes_comuna}
        df_total = pd.DataFrame([fila_total])
        df_grouped_city = pd.concat([df_grouped_city, df_total], ignore_index=True)
        df_grouped_city.rename(columns={'UE': 'Origen'}, inplace=True)

    else:
        df_filtered_city = df_city.groupby('Comuna').sum().reset_index()
        df_filtered_city_corp=df_filtered_city.drop(columns=['UE'], errors='ignore')
        #agegar una columna nueva al inicio del data frame llamada Origen con el valor 'Corporación' para todas las filas
        df_filtered_city_corp.insert(0, 'Origen', 'Corporación')
        df_grouped_city = df_filtered_city_corp.sort_values('Estudiantes', ascending=False).reset_index(drop=True)
        
        total_estudiantes_comuna = df_city['Estudiantes'].sum()
        fila_total = {'Origen': 'General', 'Comuna': 'Todas', 'Estudiantes': total_estudiantes_comuna}
        df_total = pd.DataFrame([fila_total])
        df_grouped_city = pd.concat([df_grouped_city, df_total], ignore_index=True)
    

    return df_grouped_city



def cantidad_cursos_colegio(df_cursos, unidad_edu=None):
    """Construye el DataFrame para la cantidad de cursos por colegio."""

    if unidad_edu and unidad_edu != 'Corporacion':
        df_cantidad_cursos = df_cursos.query("UE == @unidad_edu").copy()
        
        # ordenar los valores de nivel básica segun el siguiente orden: 
        # PRE-KINDER, KINDER, 1BÁSICO, 2BÁSICO, 3BÁSICO, 4BÁSICO, 5BÁSICO, 6BÁSICO, 7BÁSICO, 8BÁSICO 
        # y los valores de nivel media segun el siguiente orden: 1MEDIO, 2MEDIO, 3MEDIO, 4MEDIO

        orden_basica = ['PRE-KINDER', 'KINDER', '1BÁSICO', '2BÁSICO', '3BÁSICO', '4BÁSICO', '5BÁSICO', '6BÁSICO', '7BÁSICO', '8BÁSICO']
        orden_media = ['1MEDIO', '2MEDIO', '3MEDIO', '4MEDIO']
        df_cantidad_cursos['NIVEL'] = pd.Categorical(df_cantidad_cursos['NIVEL'], categories=orden_basica + orden_media, ordered=True)
        df_cantidad_cursos = df_cantidad_cursos.sort_values('NIVEL').reset_index(drop=True)
          
        # Agregar fila total al final del dataframe, 
        # con el total de cursos para la unidad educativa seleccionada, 
        # y con el valor "General" en la columna UE, y "Todos" en la columna Cursos.
        total_cursos = df_cantidad_cursos['CURSOS'].sum()
        fila_total = {'UE': 'General', 'NIVEL': 'Todos', 'CURSOS': total_cursos}

        # Convertir la fila total en un DataFrame y concatenarla al DataFrame original
        df_total = pd.DataFrame([fila_total])
        df_cantidad_cursos = pd.concat([df_cantidad_cursos, df_total], ignore_index=True)

        # Renombrar columnas para que tengan un nombre más legible 
        # en la tabla de cantidad de cursos por colegio.
        df_cantidad_cursos.rename(columns={'UE': 'UNIDAD EDUCATIVA'}, inplace=True)
        df_cantidad_cursos.rename(columns={'CURSOS': 'N° de CURSOS'}, inplace=True)

    else:
        df_filtered_cursos = df_cursos.groupby('NIVEL').sum().reset_index()

        df_filtered_cursos_corp=df_filtered_cursos.drop(columns=['UE'], errors='ignore')

        # Agegar una columna nueva al inicio del data frame llamada Origen 
        # con el valor 'Corporación' para todas las filas
        df_filtered_cursos_corp.insert(0, 'Origen', 'Corporación')
        
        # Creamos el DataFrame final para la cantidad de cursos por colegio, 
        # con la columna Origen, y renombramos la columna NIVEL a GRADO 
        # para que sea más legible en la tabla de cantidad de cursos por colegio.
        df_cantidad_cursos = df_filtered_cursos_corp
        
        df_cantidad_cursos.rename(columns={'NIVEL': 'GRADO'}, inplace=True)

        # Agregar una columna nueva despues de origen llamada nivel con dos
        # valores, uno para basica y otro para media, 
        # segun corresponda, para luego usar esa columna 
        # como filtro en la tabla de cantidad de cursos por colegio.
        df_cantidad_cursos['NIVEL'] = df_cantidad_cursos['GRADO'].apply(lambda x: 
                                                                        'BÁSICA' if x in ['PRE-KINDER', 'KINDER', '1BÁSICO', '2BÁSICO', 
                                                                                          '3BÁSICO','4BÁSICO','5BÁSICO','6BÁSICO','7BÁSICO','8BÁSICO'] else 'MEDIA')
        # Cambiar de posición la columna NIVEL para que quede después de ORIGEN
        cols = df_cantidad_cursos.columns.tolist() # Obtener la lista de columnas
        cols = cols[:1] + cols[-1:] + cols[1:-1] # Reordenar la lista de columnas para mover 'NIVEL' después de 'Origen'
        df_cantidad_cursos = df_cantidad_cursos[cols] # Reordenar el DataFrame con la nueva lista de columnas

        # Ordenar data frame por la columna NIVEL
        df_cantidad_cursos = df_cantidad_cursos.sort_values('NIVEL', ascending=True).reset_index(drop=True)

        # Ordenar los valores de nivel básica segun el siguiente orden: 
        # PRE-KINDER, KINDER, 1BÁSICO, 2BÁSICO, 3BÁSICO, 4BÁSICO, 5BÁSICO, 6BÁSICO, 7BÁSICO, 8BÁSICO ylos valores de
        # nivel media segun el siguiente orden: 1MEDIO, 2MEDIO, 3MEDIO, 4MEDIO
        orden_basica = ['PRE-KINDER', 'KINDER', '1BÁSICO', '2BÁSICO', '3BÁSICO', '4BÁSICO', '5BÁSICO', '6BÁSICO', '7BÁSICO', '8BÁSICO']
        orden_media = ['1MEDIO', '2MEDIO', '3MEDIO', '4MEDIO']
        df_cantidad_cursos['GRADO'] = pd.Categorical(df_cantidad_cursos['GRADO'], categories=orden_basica + orden_media, ordered=True)
        df_cantidad_cursos = df_cantidad_cursos.sort_values('GRADO').reset_index(drop=True)

        # Agregar fila total al final del dataframe, 
        # con el total de cursos para la unidad educativa seleccionada, 
        # y con el valor "General" en la columna UE, y "Todos" en la columna Cursos.  
        total_cursos = df_cursos['CURSOS'].sum()
        fila_total = {'Origen': 'General', 'NIVEL': 'Todos', 'GRADO': 'Todos', 'CURSOS': total_cursos}
        df_total = pd.DataFrame([fila_total])
        df_cantidad_cursos = pd.concat([df_cantidad_cursos, df_total], ignore_index=True)
        df_cantidad_cursos.rename(columns={'CURSOS': 'N° de CURSOS'}, inplace=True)

    
    return df_cantidad_cursos

# Ruta de tu archivo
ruta_archivo = DATA_PATH.joinpath('mat_2026.xlsx')

# Obtener la hora de última modificación (timestamp Unix)
timestamp_mod = os.path.getmtime(ruta_archivo)

# Convertir a objeto datetime
fecha_mod = datetime.datetime.fromtimestamp(timestamp_mod)

# Ajustar Zona Horaria
fecha_menos_3h = fecha_mod + timedelta(hours=-4)

# Formatear como string legible (ej: '2025-12-11 10:30:00')
fecha_actualizada_menos_tres = fecha_menos_3h.strftime('%Y-%m-%d %H:%M:%S')


# Diccionario de Unidades Educativas
ue_options = {
                'CORPORACIÓN': 'Corporacion',
                'BÁSICA 1':'BÁSICA 1',
                'BÁSICA 2':'BÁSICA 2',
                'BÁSICA SAN FELIPE':'BÁSICA SF',
                'MEDIA LOS ANDES':'MEDIA LOS ANDES',
                'MEDIA SAN FELIPE':'MEDIA SAN FELIPE'}

# Lista de diccionarios para 'options' usando una lista por comprensión
ue_options_dropdown = [{'label': k, 'value': v} for k, v in ue_options.items()]

# Inicio aplicacion Dash
#app = Dash(__name__)
# server=app.server

# Diagrama de la aplicación y layout, con callback para actualizar gráficos según unidad educativa seleccionada en dropdown
def layout():    
    
    layout = html.Div(
        children=[
    
    # Marco para lista despegable UNIDAD EDUCATIVA y Fecha Actualización
        html.Div(children=[
    
    # Fecha Actualización
    html.Div(
            children=[
            html.Div("Última actualización", style={'textAlign': 'center', 'color': 'white', 'fontSize': '14px'}),
            html.Div(f"Fecha: {fecha_actualizada_menos_tres}", style={'fontSize': '18px', 'fontWeight': 'bold', 'textAlign': 'center','color': 'white'})
        ],
    ),

    # Lista despegable de UNIDAD EDUCATIVA
    html.Div(
        children=[
            html.Div(children='Unidad Educativa', className='menu-title'),
            dcc.Dropdown(
                id='unidades_educativas', 
                options=ue_options_dropdown,
                value='Corporacion',
                clearable=False,
                className='dropdown'
            ),
        ]),

    ],
    className="menu",
    ),

    
    # Marcos para los gráficos y tablas (dcc.Graph estan incorporados en la función update_charts)

        # Contenedor del gráfico de matrícula por unidad educativa o nivel, con tarjetas de género.
        html.Div(id='grafico_matricula' , className="grafico_and_card"),

        # Contenedor de la tabla de cantidad de cursos por colegio
        html.Div(id='tabla_cursos' , className="tabla_cursos_contenedor"),
        
        # Contenedor del gráfico de evolución matricula por fecha.
        html.Div(id='grafico_evolucion' , className="grafico-evolucion"),

        # Contenedor del gráfico de torta y tabla con el origen de estudiantes matriculados,
        html.Div(id='grafico_origen' , className="grafico-origen-contenedor"),
   
        # Contenedor del mapa (se inicializa vacío, el callback lo dibuja)
        html.Div(id='mapa_comunas', className="contenedor-mapa-comunas-tabla"),

        # Contenedor del gráfico de barras horizontales con los colegios de origen 
        # de los estudiantes matriculados,
        # con filtro por unidad educativa, mostrando solo los colegios que aportan 10 o más
        html.Div(id='grafico_colegios' , className="grafico-evolucion"),

        # Contenedor de la tabla de proyección, con el mismo filtro de unidad educativa,
        # para que se actualice junto al gráfico de matrícula por unidad educativa o nivel.
        html.Div(get_tabla_proyeccion(), id='tabla_matricula' , className="wrapper"),
       
       
       
        ])

    return layout

# callback para filtrar gráfico segun unidad educativa
@callback(
        Output('grafico_matricula', 'children'),
        Output('grafico_evolucion', 'children'),
        Output('grafico_origen', 'children'),
        Output('mapa_comunas', 'children'),
        Output('tabla_cursos', 'children'),
        Output('grafico_colegios','children'),
        [Input('unidades_educativas', 'value'),
         ]
        )

# función para trazar grafico de matricula
def update_charts(unidad_edu):
    
    # Asegura que los datos de Excel estén cargados antes de generar los gráficos.
    load_data()
    if unidad_edu == 'Corporacion':
        origen_df = _df05
    else:
        origen_df = _df05.query("UE == @unidad_edu")

    # Creamos un diccionario inverso para obtener la etiqueta legible 
    # a partir del valor seleccionado en el dropdown
    inverse_dict = {v: k for k, v in ue_options.items()}

    # Extraer la etiqueta legible para el gráfico a partir del valor seleccionado en el dropdown
    label_graph = inverse_dict.get(unidad_edu) 

    """# Llamadas a las funciones def con sus respectivos filtros según la unidad educativa seleccionada,
    # para obtener los datos necesarios para cada gráfico.
    # Cada función tiene sus propios valores return, que se asignan a variables locales 
    # para luego construir cada gráfico."""
   
    # Funcion para dataframe de matrícula por unidad educativa o nivel, con fila adicional GENERAL
    # y calculo de % Meta alcanzada.
    select_nivel_subject, graph_x_axes, color_bar, etiqueta = build_summary_df(_df01, unidad_edu)

    # Función para dataframe de evolución de matrícula por fecha, 
    # con acumulado de estudiantes matriculados,
    df_time_agrupado = build_evolution_df(_df04, unidad_edu)
    
    # Función para calcular el origen de los estudiantes matriculados
    # INTERNO, NUEVO-SAE, ANOTATE LISTA, con filtro por unidad educativa,
    categorias_origen, valores_origen, tabla_origen = calculate_origin(origen_df, unidad_edu)

    # Función para obtener el conteo de estudiantes por género, con filtro por unidad educativa,
    masculino_count, femenino_count = get_gender_counts(_df03, unidad_edu)

    # Función para obtener el DataFrame filtrado para el gráfico de barras horizontales 
    # del colegio de origen de los estudiantes matriculados.
    df_filtered_institution = get_origin_school(_df06, unidad_edu)

    # Función para obtener el DataFrame filtrado para el gráfico de mapa 
    # de las comunas de origen de los estudiantes matriculados,
    df_grouped_city = origin_city_student(_df07, unidad_edu)

    # funcion para obtener la cantidad de cursos por colegio, con filtro por unidad educativa
    df_cantidad_cursos = cantidad_cursos_colegio(_df08, unidad_edu)


    # Color específico para la barra del gráfico de matrícula por unidad educativa o nivel,
    # para que se destaque del resto de barras, y se mantenga el mismo color tanto 
    # para la barra de la unidad educativa o nivel seleccionado, 
    # como para la barra total GENERAL, que siempre se muestra al final del gráfico.
    color_03='blue'

    # Gráfico de matriculados por unidad educativa o nivel, con filtro por unidad educativa, 
    # con barra de colores diferenciada por unidad educativa o nivel, 
    # y con porcentaje de meta alcanzada en el tooltip.
    trace01 = px.bar(select_nivel_subject, x=graph_x_axes, y='MAT_2026', 
                     title=f'Matrícula 2026 - {label_graph}',
                     width=1020, height=380,
                     labels={graph_x_axes: '','MAT_2026':''},
                     color=color_bar,
                     color_discrete_map= {'GENERAL':color_03},
                     color_discrete_sequence=px.colors.qualitative.T10,
                     template="simple_white",
                     custom_data=['SAE_2026','% Meta'],
                     text_auto=True,
                     
            )
    
    trace01.add_layout_image(                                 
                            source= "assets/logo_corp.png",
                            xref="paper", yref="paper",
                            x=0.9, 
                            y=1.15,
                            sizex=0.2, sizey=0.2,
                            xanchor="left", yanchor="bottom",                                
                            )

    trace01.update_traces(hovertemplate=
                          '<b>SAE 2026: </b>%{customdata[0]}</b><br>'+
                          '<b>Mat 2026: </b>%{y:f}<br>'+
                          '<b>% Meta  : </b>%{customdata[1]:.1f} %</b><br>',
                          textfont_size=16, textangle=0, textposition="outside", cliponaxis=False,
                          textfont=dict(weight="bold"),
                          width=0.5,
                          )

    
    trace01.update_yaxes(tickfont_weight='normal', showgrid=True, tickfont_size=15,showline=False, ticks="",
                         tickfont=dict(color='gray'))
    
    trace01.update_xaxes(tickfont_weight='bold', tickfont_size=12, showline=False, ticks="")

    trace01.update_layout(
                         hoverlabel_font=dict(family='Roboto mono', weight='bold', size=15, color='white'),
                         font_family='Roboto mono',
                         title_font_weight='bold',
                         title_font_size=20,
                         title_xanchor='left',
                         xaxis_type='category',
                         showlegend=False,
                         
                         )
    
    # Gráfico de evolución matricula por fecha, filtrado por unidad educativa, 
    # con acumulado de estudiantes matriculados en el eje y, y fecha de matrícula en el eje x.
    trace02 = px.line(df_time_agrupado, x='MATRICULA', y='accumulated', 
                      title=f'Matrícula 2026 - {label_graph}',
                      width=1280, height=500,
                      template="simple_white",
                      )
            
    trace02.update_traces(mode="markers+lines",
                          hovertemplate=
                           '<b>Matriculados: </b>%{y}</b>',
                          marker=dict(color=' #e74040'),
                          line=dict(width=2, color='#555555'),
                    )
    
    trace02.update_yaxes(tickfont_weight='normal', 
                         showgrid=True, 
                         tickfont_size=15,
                         showline=False, 
                         ticks="",
                         title_text="",
                         tickfont=dict(color='gray'))
    
    trace02.update_xaxes(tickfont_weight='bold', 
                         tickfont_size=12, 
                         showgrid=True, 
                         showline=True,
                         title_text="",
                         tickfont=dict(color='gray'))
    
    trace02.update_layout(
                         hoverlabel_font=dict(family='Roboto mono', weight='bold', size=14, color='black'),
                         font_family='Roboto mono',
                         title_font_weight='bold',
                         title_font_size=20,
                         title_xanchor='left',
                         showlegend=False,
                         hovermode="x unified",
                         
                         )
    
    # Gráfico de torta con el origen de los estudiantes matriculados: Interno, Nuevo SAE y Anotate Lista,
    # con filtro por unidad educativa.
    trace03=px.pie(values=valores_origen, names=categorias_origen, 
                         title=f'Origen Matrícula 2026 - {label_graph}',
                         labels={'names':'Origen','values':'Cantidad'},
                         width=650, height=490,
                         hole=0.4, 
                         template="simple_white", 
                         color_discrete_sequence=px.colors.qualitative.D3)
    
    trace03.update_traces(
                            textinfo='percent',
                            textfont=dict(
                            color='white',  
                            size=20,
                            weight='bold',
                        ),
                        )
    
    trace03.update_layout(
                         hoverlabel_font=dict(family='Roboto mono', weight='bold', size=15, color='white'),
                         font_family='Roboto mono',
                         title_font_weight='bold',
                         title_font_size=20,
                         title_xanchor='left',
                         autosize=False,
                         )
    
    if df_filtered_institution.empty:
        # Crear una figura vacía con el mensaje de alerta cuando 
        # no hay datos para mostrar en el gráfico de barras horizontales 
        # del origen de los estudiantes matriculados por colegio, 
        
        trace04 = go.Figure()
        trace04.update_layout(
                title='Origen Estudiantes, Matrícula 2026 (colegios que aportan 10 o más estudiantes)',
                title_font=dict(size=20, color="black", family="Roboto mono"),
                title_font_weight='bold',
                title_xanchor='left',
                width=1280, height=550,
                template="simple_white",
                xaxis={"visible": False},
                yaxis={"visible": False},
                annotations=[
                        {
                            "text": "No hay colegios externos que aporten 10 o más estudiantes para esta unidad educativa",
                             "x": 1.5,
                             "y": 0.5,
                            "yref": "paper",
                            "showarrow": False,
                            "font": {"size": 20, "color": "gray"},
                        }
                ],
    )
    else:    
    
        # Gráfico de barras horizontales con los colegios de origen de los estudiantes matriculados, 
        # con filtro por unidad educativa, mostrando solo los colegios que aportan 10 o más estudiantes.
        trace04 = px.bar(df_filtered_institution, x='ESTUDIANTES', y='PROCEDENCIA',
                     facet_col="UE", 
                     orientation='h', 
                     title='Origen Estudiantes, Matrícula 2026 (colegios que aportan 10 o más estudiantes)',
                     width=1280, height=550,
                     labels={'UE': 'Unidad Académica'},
                     color='UE',
                     color_discrete_sequence=px.colors.qualitative.G10,
                     template="plotly",
                     text_auto=True,
                     
                )
    
        trace04.update_yaxes(title_text="",
                         tickfont_weight='normal',
                         tickfont_size=14,
                         tickfont=dict(color='gray'),
                         
                         )
    
        trace04.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1], font=dict(size=14, color='black')))
    
        trace04.update_layout(
                         hoverlabel_font=dict(family='Roboto mono', weight='bold', size=12, color='white'),
                         title_font=dict(size=20, color="black", family="Roboto mono"),
                         title_font_weight='bold',
                         title_xanchor='left',
                         margin=dict(t=100),
                         yaxis_autorange='reversed',
                         )

        trace04.update_traces(
                           width=0.8,
                           textangle=0,  
                           textfont=dict(
                           color='white',
                           size=20,
                           family="Roboto mono",
                           weight='bold',
                           ),
                        )

    # Div con gráfico de matricula por unidad educativa o nivel, con tarjetas de genero.

    new_trace01 = [dcc.Graph(figure=trace01, config={"displayModeBar": False}, className="graph_bar"),
                   html.Div(children=[
                            html.Div("Matrícula por género", style={'textAlign': 'left', 'color': 'gray', 'fontSize': '14px'}),

                            html.Div(children=[
                                     html.Div(
                                         html.I(className="fa-solid fa-child"), className="bloque-azul"),
                                     html.Div(f"{masculino_count}", className="bloque-gris"),
                                     
                            ],
                                className="contenedor-icono-texto"),
                             
                             html.Div(children=[
                                     html.Div(
                                         html.I(className="fa-solid fa-child-dress"), className="bloque-azul"),
                                     html.Div(f"{femenino_count}", className="bloque-gris"),
                                     
                            ],
                                className="contenedor-icono-texto"),
                            
                            ],
                       
                       className="card_contenedor")]
    
    # Div con gráfico de matricula por fecha filtrado según unidad educativa.

    newtrace02 = [dcc.Graph(figure=trace02, config={"displayModeBar": False}, className="graph_line")]
    
    # Tabla con el origen de los estuidantes, Interno, sae nuevo y anotate lista, 
    # para colocar al lado del gráfico de torta del origen de estudiantes matriculados. 
    # La función calculate_origin ya devuelve la tabla con el filtro aplicado 
    # según la unidad educativa seleccionada, por lo que aquí solo construimos la tabla Dash 
    # a partir del DataFrame filtrado que nos devuelve la función externa."
    tabla_origen_global= dbc.Table.from_dataframe(tabla_origen, 
                                                  striped=True, 
                                                  bordered=True, 
                                                  hover=True,
                                                  #color='light',                                               size='sm',
                                                  style={'width': '100%',
                                                      'margin': 'auto', 
                                                      'textAlign': 'center',
                                                      "fontSize": "14px",  
                                                      },
                                                  className="tabla-personalizada" # Agrega esta clase
                                                      )

    # Gráfico de torta y tabla con el origen de estudiantes matriculados, 
    # para colocar debajo del gráfico de evolución matricula por fecha
    newtrace03 = [dcc.Graph(figure=trace03, config={"displayModeBar": False}, className="graph_pie"),
                   html.Div(children=[
                            html.Div("Origen de Estudiantes Matriculados", style={'textAlign': 'center', 'color': 'gray', 'fontSize': '14px'}),
                            html.Div(tabla_origen_global),
                            ],
                            className="tabla_origen_contenedor"),
                    ]
    # Div para el gráfico de barras horizontales con los colegios de origen 
    # de los estudiantes matriculados, 
    # con filtro por unidad educativa, mostrando solo los colegios 
    # que aportan 10 o más estudiantes, para colocar debajo del gráfico de evolución matricula por fecha.

    newtrace04 = [dcc.Graph(figure=trace04, config={"displayModeBar": False}, className="graph_bar")]

    # Grafico con mapa de las comunas de origen de los estudiantes matriculados, 
    # con filtro por unidad educativa
    # La función actualizar_mapa_comunas se encarga de generar el mapa filtrado 
    # según la unidad educativa seleccionada, utilizando el DataFrame df_grouped_city 
    # que ya tiene aplicado el filtro correspondiente. 
    # Le pasamos el DataFrame filtrado y el label para que el título del mapa también 
    # se actualice según la unidad educativa seleccionada.
    # Le enviamos los datos filtrados a la función externa para generar el nuevo mapa
    trace05 = actualizar_mapa_comunas(df_grouped_city,label_graph)

    # Tabla comuna estudiantes para colocar al lado del mapa de las comunas, 
    # con el mismo filtro de unidad educativa, para que se actualice junto al mapa. 
    # La función externa solo devuelve el mapa, la tabla la construimos aquí mismo.
    tabla_comuna_estudiantes= dbc.Table.from_dataframe(df_grouped_city, 
                                               striped=True, 
                                               bordered=True, 
                                               hover=True,
                                               #color='light',
                                               size='sm',
                                               style={'width': '100%',
                                                      'margin': 'auto', 
                                                      'textAlign': 'center',
                                                      "fontSize": "14px",  
                                                      },
                                               className="tabla-personalizada" # Agrega esta clase
                                                      )
    # Div contenedor del mapa y la tabla de la cantidad de estudiantes por comuna, 
    # ambos con el mismo filtro de unidad educativa, para que se actualicen juntos.
    newtrace05= [dcc.Graph(figure=trace05, className="mapa_comunas_estudiantes"),
                 html.Div(children=[
                            html.Div("Comuna Estudiantes Matriculados", style={'textAlign': 'center', 'color': 'gray', 'fontSize': '14px'}),
                            html.Div(tabla_comuna_estudiantes),
                            ],
                            className="tabla_comuna_contenedor"),
                    ]
    
    tabla_cantidad_cursos= dbc.Table.from_dataframe(df_cantidad_cursos, 
                                               striped=True, 
                                               bordered=True, 
                                               hover=True,
                                               #color='light',
                                               size='sm',
                                               style={'width': '100%',
                                                      'margin': 'auto', 
                                                      'textAlign': 'center',
                                                      "fontSize": "14px",  
                                                      },
                                               className="tabla-personalizada" # Agrega esta clase
                                                      )
     
       
    

    return new_trace01, newtrace02, newtrace03, newtrace05, tabla_cantidad_cursos, newtrace04

# cargar en servidor
# if __name__ == '__main__':
#   app.run_server(debug=True)