import dash
from dash import html, dcc, callback, Input, Output, ALL, State, dash_table, register_page, no_update, exceptions
import dash_bootstrap_components as dbc
import plotly.graph_objects as graph_objects
import pandas as pd
import copy
from pathlib import Path
import io
from plotly.subplots import make_subplots

import pages.modulos.calculation_projection as proyecciones
# Importar funciones para calculo de matricula proyectada
from pages.modulos.calculation_projection import (
    calcular_proyeccion_completa, 
    guardar_escenario_simulacion,
    guardar_escenario_corporativo,
    listar_escenarios_por_unidad,
    listar_todos_escenarios_agrupados,
    cargar_datos_escenario,
    eliminar_archivo_escenario,
    proyeccion_corporativa,
    asegurar_carpeta_escenarios,
    proyeccion_por_nivel,
    tasas_nuevos_alumnos,  
   )

from pages.modulos.slider_creation import crear_grupo_sliders 

register_page(
    __name__, 
    name="Proyección 8 Años",
    top_nav=True,
    path="/proyeccion",     
    )

UMBRAL_CRITICO = 600

# Diccionario de Unidades Educativas
ue_options = {
                'CORPORACIÓN': 'CORPORACIÓN',  # ← agregar primero
                'BÁSICA 1':'BÁSICA 1',
                'BÁSICA 2':'BÁSICA 2',
                'BÁSICA SAN FELIPE':'BÁSICA SF',
                'MEDIA LOS ANDES':'MEDIA LOS ANDES',
                'MEDIA SAN FELIPE':'MEDIA SAN FELIPE'}

# Lista de diccionarios para 'options' usando una lista por comprensión
ue_options_dropdown = [{'label': k, 'value': v} for k, v in ue_options.items()]

periodo_corporativo = {
                        '2027':2027,
                        '2028':2028,
                        '2029':2029,
                        '2030':2030,
                        '2031':2031,
                        '2032':2032,
                        '2033':2033,
                        '2034':2034,
                        '2035':2035,

}

p_corp_options_dropdown = [{'label': per, 'value': year} for per, year in periodo_corporativo.items()]

# Lista de Columnas optimizadas para el menú lateral angosto en la tabla de datos
columnas_verticales = [
    {"name": "Año", "id": "Anio", "editable": False},
    {"name": "Matrícula", "id": "Matricula", "type": "numeric", "editable": True}
]

    
# Menu Lateral
menu_lateral = dbc.Card([

    # Lista despegable de UNIDAD EDUCATIVA
    html.Div(
        children=[
            html.H6(
                [
                 html.I(className="fa-solid fa-school me-2"), 
                'Unidad Educativa '
                ],
                className="text-primary fw-bold mb-3"
              ),
              dcc.Dropdown(
                id='unidades_educativas', 
                options=ue_options_dropdown,
                value='BÁSICA 1',
                clearable=False,
                style={
                        'width': '100%',          # Ancho del dropdown
                        'backgroundColor': '#f0f0f0', # Color de fondo
                        'color': '#333333',      # Color del texto
                        'fontSize': '14px'       # Tamaño de la fuente
                      },
                
            ),
        ]),
    
    html.Br(),  
    
     # Título para Gestion de Escenarios, Input y Botones 
    html.H6(
            [
            html.I(className="fa-solid fa-folder-tree me-2"), # Icono de engranaje con margen derecho
            "Gestión de Escenarios"
            ],
            className="text-primary fw-bold mb-2" # Tus clases originales
        ),
    
    html.Hr(),
    
    # Campo para escribir el nombre del escenario a guardar
    dcc.Input(id="input-nombre-escenario", 
              type="text", 
              placeholder="Ej: Proyeccion 01 BAS1", 
              className="form-control mb-2",
              style={"fontSize": "14px"},
              ),
              
    
    # Dropdown para seleccionar qué escenario cargar
    dcc.Dropdown(id="dropdown-escenarios-guardados", 
                 placeholder="Seleccionar escenario para cargar...",
                 style={
                        'width': '100%',          # Ancho del dropdown
                        'backgroundColor': '#f0f0f0', # Color de fondo
                        'color': '#333333',      # Color del texto
                        'fontSize': '14px'       # Tamaño de la fuente
                      }, 
                 className="mb-3"),
    
    # Botones para escenarios, guardar, cargar, eliminar
    html.Div([
        dbc.Button(
            [
            html.I(className="bi bi-floppy me-2"), 
            "Guardar"
            ], 
            id="btn-guardar-escenario", 
            color="primary", size="sm", 
            className="me-2"
            ),
        dbc.Button(
            [
            html.I(className="bi bi-file-earmark-arrow-up me-2"), 
            "Cargar"
            ], 
            id="btn-cargar-escenario", 
            color="warning", 
            size="sm", 
            className="me-2"
            ),
        dbc.Button(
            [
            html.I(className="bi bi-file-earmark-x me-2"), 
            "Eliminar"
            ],  
            id="btn-eliminar-escenario", 
            color="danger", 
            size="sm"
            ),

            

    ], className="d-flex justify-content-start mb-3"),
    
    # Div con mensaje de alerta y modal para ventana emergente
    html.Div([
        # Mensaje de confirmación o alerta en pantalla (debajo de los botones)
        html.Div(id="mensaje-alerta-escenario", className="small text-muted mb-2"),

        # El bloque del Modal (permanece invisible hasta que se activa)
        dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle("Confirmar Acción"), close_button=False),
                dbc.ModalBody(
                        html.Div([
                            html.I(className="bi bi-exclamation-triangle-fill text-danger me-3 fs-3"),
                            html.Span("El escenario será eliminado definitivamente del sistema. ¿Deseas continuar?", className="fw-bold")
                         ], className="d-flex align-items-center p-3")
                     ),
                dbc.ModalFooter([
                        dbc.Button("Cancelar", id="btn-modal-cancelar", color="secondary", size="sm", className="me-2"),
                        dbc.Button("Aceptar", id="btn-modal-aceptar", color="danger", size="sm"),
                        ]),
            ],
            id="modal-confirmacion-eliminar",
            is_open=False,       
            centered=True,       
            backdrop="static",   
        ) # Cierre Modal

        ], id="contenedor-alertas-y-modal"), # Cierre mensaje alerta y modal
    

    # Boton exportar excel
    dbc.Button(
        [
            html.I(className="fas fa-file-excel me-2"), 
            "Exportar Proyección"
        ],
        id="btn-exportar-excel", 
        color="success",
        style={"fontSize": "14px"}, 
        className="mt-2"),
    dcc.Download(id="descarga-excel"),
    
    html.Br(),
    html.Br(),
    
    # Dropdown CORPORATIVO para elejir múltiples escenarios
    html.Div(
        id='contenedor-dropdown-corp',
        children=[
                        
            html.H6(
                [
                 html.I(className="fa-solid fa-chart-line me-2"), 
                'Escenarios por Unidad'
                ],
                className="text-primary fw-bold mb-2"
              ),
            
            html.Hr(),
            dcc.Dropdown(
                id='dropdown-escenarios-corp',
                placeholder="Seleccionar escenarios...",
                multi=True,  # ← selección múltiple
                className="mb-3",
                style={
                        'width': '100%',          # Ancho del dropdown
                        'backgroundColor': '#f0f0f0', # Color de fondo
                        'color': '#333333',      # Color del texto
                        'fontSize': '14px'       # Tamaño de la fuente
                      }, 
            )
        ],
        style={'display': 'none'}  # ← oculto por defecto
    ),
    
    # Gestion Escenarios: contenedor para slider de unidades educativas 
    # y tabla matricula inicial, se oculta si se elije CORPORACION
    html.Div( # incio contenedor
            id='contenedor-configuracion', # id contenedor"
            children=[ # inicio children contenedor
        # Contenedor despegable, Configuración escenarios
        html.Details([
            html.Summary(
                    [
                    # Icono de engranaje (ajustes) con un pequeño margen a la derecha
                    html.I(className="bi bi-gear-fill me-2"), 
                    "Configuración Escenarios"
                    ],  
                    
                    style={"cursor": "pointer", 
                                                        "fontWeight": "bold", 
                                                        "fontSize": "16px", 
                                                        "padding": "10px",
                                                        "color": "#ffffff", 
                                                        "backgroundColor": "#6E6E6E", 
                                                        "borderRadius": "5px", 
                                                        "marginBottom": "10px"}
                                                        ),
        
                
                    html.Hr(),
                    
                    # Pestañas para los 20 slider separados en 10 para retencion y 10 para captacion
                    dbc.Tabs([
                        # Pestaña 1: Alumnos nuevos
                        dbc.Tab(label="Alumnos Nuevos", tab_id="tab-sliders-retencion", label_style={'fontSize': '14px'},
                                children=[
                            html.Div([
                            # Slider alumnos nuevos
                                    html.Label("Nuevos Estudiantes: ", className="fw-bold text-secondary me-1", style={"fontSize": "14px"}),
                                    html.Hr(),
                                    # Crear slider con funcion crear_grupo_sliders para retencion
                                    html.Div(id='contenedor-captacion') # contenedor de slider segun unidad educativa elegida

                                ], className="pt-2")
                            ]),

                        # Pestaña 2: Retencion
                        dbc.Tab(label="Retención", tab_id="tab-sliders-nuevos", label_style={'fontSize': '14px'},
                                children=[
                            html.Div([
                            # Slider retencion
                                    html.Label(" Tasa de retencion (%):", className="fw-bold text-secondary me-1", style={"fontSize": "14px"}),
                                    html.Hr(),
                                    # Crear slider con funcion crear_grupo_sliders para retencion
                                    html.Div(id='contenedor-retencion') # contenedor de slider segun unidad educativa elegida

                                ], className="pt-2")
                            ]),
                    ], id="tabs-sliders-menu", active_tab="tab-sliders-retencion"), # fin 2 pestañas de sliders
                
                
        # Tabla para ver y modificar valores iniciales
        html.Label("Valores Iniciales Pre-kinder o 1° Medio:", style={'fontWeight': 'bold', "fontSize": "14px"}),
        # Tabla Vertical Interactiva
            dash_table.DataTable(
                id='tabla-matriculas-vertical',
                columns=columnas_verticales,
                editable=True,
                style_cell={
                    'textAlign': 'center', 
                    'padding': '6px',
                    'fontSize': '13px',
                    'fontFamily': 'sans-serif'
                },
                style_header={
                    'backgroundColor': '#f4f4f4', 
                    'fontWeight': 'bold',
                    'border': '1px solid #d6d6d6'
                },
                style_data={
                    'border': '1px solid #e0e0e0'
                }
            ),

        # Sección MODELOS MATEMÁTICOS para carga inicial PRE-KINDER o 1° MEDIOS
        html.Hr(),
        html.Label(
            "Modelos Carga Inicial de Estudiantes:", 
            style={'fontWeight': 'bold', "fontSize": "14px"}
        ),

        dbc.Tabs([
            # Pestaña 1: Modelo Lineal, 2 elementos 
            # 1. celdas de entrada, una para punto de partida P0
            # 2. celda para pendiente "p"
            dbc.Tab(label="Lineal", tab_id="tab-modelo-lineal", label_style={'fontSize': '13px'},
                children=[
                    html.Div([
                        # Población inicial P0
                        html.Label("Punto de partida (P0):", style={"fontSize": "13px", "fontWeight": "bold", "marginTop": "10px"}),
                        dcc.Input(
                            id="input-lineal-p0",
                            type="number",
                            placeholder="Matrícula 2026",
                            className="form-control mb-2",
                            style={"fontSize": "13px"}
                        ),
                        
                        # Pendiente
                        html.Label("Alumnos por año (pendiente):", style={"fontSize": "13px", "fontWeight": "bold"}),
                        html.Span(" positivo = alza, negativo = baja", style={"fontSize": "11px", "color": "#888888"}),
                        dcc.Input(
                            id="input-lineal-pendiente",
                            type="number",
                            value=5,  # default +5 alumnos por año
                            className="form-control mb-3",
                            style={"fontSize": "13px"}
                        ),
                        
                        # Botón cargar MODELO
                        dbc.Button(
                            [html.I(className="bi bi-calculator me-2"), "Cargar Modelo"],
                            id="btn-modelo-lineal",
                            color="primary",
                            size="sm",
                            className="mt-1"
                        ),
                        
                        # Mensaje resultado
                        html.Div(id="msg-modelo-lineal", className="small text-muted mt-2")
                        
                    ], className="pt-2 px-2")
                ]
            ),

            # Pestaña 2: Modelo Logístico, 4 elementos
            # 1. una casilla check para cambiar a modo DECRECIMIENTO
            # 2. una celda de entrada para P0 inicial
            # 3. una celda para "K", carga máxima (máximo o mínimo segun modelo)
            # 4. un slider para tasa crecimiento "r"
            dbc.Tab(label="Logístico", tab_id="tab-modelo-logistico", label_style={'fontSize': '13px'},
                children=[
                    html.Div([
                        
                        # Checkbox para elegir crecimiento o decrecimiento
                        dbc.Checklist(
                            id="check-decrecimiento",
                            options=[{"label": " Modo decrecimiento gradual", "value": "decrecer"}],
                            value=[],  # default: crecimiento
                            className="mb-2 mt-2",
                            style={"fontSize": "13px"}
                        ),
                        
                        # Población inicial P0
                        html.Label("Población inicial (P0):", style={"fontSize": "13px", "fontWeight": "bold"}),
                        dcc.Input(
                            id="input-logistico-p0",
                            type="number",
                            placeholder="Matrícula 2026",
                            className="form-control mb-2",
                            style={"fontSize": "13px"}
                        ),
                        
                        # Capacidad K (máxima o mínima según modo)
                        html.Label(id="label-k-logistico", children="Capacidad máxima (K):", 
                                style={"fontSize": "13px", "fontWeight": "bold"}),
                        dcc.Input(
                            id="input-logistico-k",
                            type="number",
                            className="form-control mb-2",
                            style={"fontSize": "13px"}
                        ),
                        
                        # Tasa de crecimiento r
                        html.Label("Tasa de crecimiento (r):", style={"fontSize": "13px", "fontWeight": "bold"}),
                        dcc.Slider(
                            id="slider-logistico-r",
                            min=0.05,
                            max=0.5,
                            step=0.05,
                            value=0.2,  # default
                            marks={i/100: str(i/100) for i in range(5, 55, 10)},
                            className="mb-3"
                        ),
                        
                        # Botón cargar MODELO
                        dbc.Button(
                            [html.I(className="bi bi-calculator me-2"), "Cargar Modelo"],
                            id="btn-modelo-logistico",
                            color="primary",
                            size="sm",
                            className="mt-1"
                        ),
                        
                        # Mensaje resultado
                        html.Div(id="msg-modelo-logistico", className="small text-muted mt-2")
                        
                    ], className="pt-2 px-2")
                ]
            ),

        ], id="tabs-modelos-carga", active_tab="tab-modelo-lineal"),



        


        
            ], open=False, style={"marginBottom": "15px"}), # Final menu despegable, escenarios unidades educativa

     
                     ] # final children contenedor Configuracion Escenarios, sliders y tabla matricula inicial

                 ), # Final contenedor configuracion escenarios, slider y tabla matricula inicial
            
    html.Br(), # salto de linea
        
    ], body=True, className="shadow-sm border-0", # fin menu lateral
    
 ) # fin dbc, Menu Lateral

# Callback que convierte el diccionario plano de matriculas iniciales 
# en 10 filas verticales para la tabla
@callback(
    Output('tabla-matriculas-vertical', 'data'),
    Input('unidades_educativas', 'value')
)
def cargar_valores_verticales(unidad_seleccionada):
    # Obtener el diccionario de años de la unidad actual {'2027': 24, '2028': 22, ...}
    
    # Si es Corporación, retornar tabla vacía
    if unidad_seleccionada == 'CORPORACIÓN':
        return []
    
    valores_anios = proyecciones.matriculas_iniciales_default[unidad_seleccionada]
    
    # Transformar a formato de lista de filas verticales
    filas_tabla = []
    for anio, valor in valores_anios.items():
        filas_tabla.append({"Anio": anio, "Matricula": valor})
        
    return filas_tabla

# Callback para crear slider segun la unidad educativa elegida y buscar escenarios en el output
@callback(
    [
        Output('contenedor-retencion', 'children'), # Primer Output (retencion)
        Output('contenedor-captacion', 'children')  # Segundo Output (captacion)
    ],
    Output('dropdown-escenarios-guardados', 'options'), # Nuevo para cargar escenarios de slider
    Output('dropdown-escenarios-corp', 'options'),  
    Output('contenedor-dropdown-corp', 'style'),          # ← nuevo, escenarios agrupados
    Output('contenedor-configuracion', 'style'),  # ← nuevo, contender slider (visible/oculto)
    Input('unidades_educativas', 'value'),  # Origen: la unidad educativa seleccionada
)
def actualizar_sliders(unidad_educativa):
    
    if unidad_educativa == 'CORPORACIÓN':  # ← agregar este bloque primero
        opciones_dropdown = listar_escenarios_por_unidad(unidad_educativa)
        escenarios_agrupados = listar_todos_escenarios_agrupados()  # ← cargar escenarios
        return [], [], opciones_dropdown, escenarios_agrupados, {'display': 'block'}, {'display': 'none'}  # ← mostrar dropdown
    
    # Condicional que define por completo cada grupo independiente
    if unidad_educativa in ['BÁSICA 1', 'BÁSICA 2', 'BÁSICA SF']:
        tasas = tasas_nuevos_alumnos.get(unidad_educativa, {})  # ← obtener tasas de la unidad
        
        # Grupo completamente definido de 3 sliders
        sliders_retencion = [
            crear_grupo_sliders("Prebásica", "grupo-a", tipo_slider='retencion'),
            crear_grupo_sliders("Primer Ciclo Básica", "grupo-b", tipo_slider='retencion'),
            crear_grupo_sliders("Segundo Ciclo Básica", "grupo-c", tipo_slider='retencion'),
          ]
        
        sliders_captacion =[
            crear_grupo_sliders("Prebásica", "grupo-a", tipo_slider='nuevos',tasas_nivel=tasas),
            crear_grupo_sliders("Primer Ciclo Básica",  "grupo-b", tipo_slider='nuevos',tasas_nivel=tasas),
            crear_grupo_sliders("Segundo Ciclo Básica",  "grupo-c", tipo_slider='nuevos',tasas_nivel=tasas),
          ]
    else:
        
        tasas = tasas_nuevos_alumnos.get(unidad_educativa, {})  # ← obtener tasas de la unidad
        
        sliders_retencion = [
            crear_grupo_sliders("Enseñanza Media", "grupo-d", tipo_slider='retencion'),
          ]
        
        sliders_captacion =[
            crear_grupo_sliders("Enseñanza Media", "grupo-d", tipo_slider='nuevos',tasas_nivel=tasas),
          ]
        
    # Un solo punto de retorno para la variable que contiene el grupo seleccionado

    # 🚀 AGREGADO: Buscamos dinámicamente qué escenarios existen en disco para esta unidad educativa
    opciones_dropdown = listar_escenarios_por_unidad(unidad_educativa)
    
    # Retornamos los tres elementos en el orden exacto de los Outputs de arriba
    return sliders_retencion, sliders_captacion, opciones_dropdown, [], {'display': 'none'}, {'display': 'block'}

# Layaout General, Menu Lateral, 2 Tarjetas KPI, Gráfico y 2 Tablas con pestañas
layout = dbc.Container([
        
    # Layaout General, 1 fila, 2 columnas,
    dbc.Row([
        
        # 1° Columna para menu lateral
        dbc.Col(menu_lateral, width=4), 
        
        # 2° Columna para KPI, 1 Gráfico y 2 pestañas con tablas
        dbc.Col([                       
            # Tarjetas KPI
            html.Div(id="contenedor-kpis", className="mb-4"), # Tarjetas KPI
            
            # Diseño para gráfico unidad académica
            dbc.Card([
                dbc.CardHeader(html.Div([
                                        html.H6("Modelación Escenarios Matrículas: ", className="m-0 text-dark", style={"display": "inline"}),
                                        html.Span(id="variable-matricula", className="text-white fw-bold", style={"display": "inline", "marginLeft": "5px"}),
                                        html.Span(id="escenario-text", className="text-white fw-bold", style={"display": "inline", "marginLeft": "5px"})
                                        
                                        ], className="d-flex align-items-center"),
                                        style={"backgroundColor": "#020072"}
                ),
                dbc.CardBody(
                    dcc.Loading(
                        id="loading-grafico",
                        type="circle",
                        children=dcc.Graph(config={"displayModeBar": False}, id="grafico-dinamico-completo")
                    )
                )
            ], className="shadow-sm mt-3"), # 'mt-3' separa la tarjeta de la barra de pestañas

            html.Br(),
            # Diseño de dos tabs para las tablas
            dbc.Tabs([
                
                 # Pestaña 1: Resumen de Matrícula Total por Año real y proyectado
                dbc.Tab(label="Tabla de Proyecciones", tab_id="tab-ingreso", children=[
                    html.Div([
                        html.P("La siguiente tabla muestra la proyección según escenario simulado/cargado.", className="text-muted small"),
                        
                        # Tabla de resultados dinámica (No editable)
                        dash_table.DataTable(
                            id="tabla-datos-reales", # Mantenemos el ID original para no romper dependencias
                            columns=[
                                {"name": "Año Académico", "id": "Año"},
                                {"name": "Matrícula Proyectada (Alumnos)", "id": "Valor", "type": "numeric"},
                                {"name": "Estado del Dato", "id": "Tipo"}
                            ],
                            style_cell={"textAlign": "center", "padding": "8px", "fontFamily": "Roboto mono"},
                            style_header={"backgroundColor": "#f8f9fa", "fontWeight": "bold"},
                            style_table={"marginBottom": "1rem"},
                            # Agregamos estilo condicional simple para diferenciar visualmente el dato Real de la Proyección
                            style_data_conditional=[
                                {
                                    'if': {'column_id': 'Tipo', 'filter_query': '{Tipo} eq "Proyección"'},
                                    'color': '#ffae00',
                                    'fontWeight': 'bold'
                                },
                                {
                                    'if': {'column_id': 'Tipo', 'filter_query': '{Tipo} eq "Real"'},
                                    'color': '#af0000',
                                    'fontWeight': 'bold'
                                }
                            ]
                        ),
                    ], className="p-3")
                ]),

                # Pestaña 2: Desagregado por Niveles Educativos
                dbc.Tab(label="Tabla desagregada por Nivel o Unidad Educativa", tab_id="tab-matriz-desglose", children=[
                    html.Div([
                        html.P("La siguiente tabla muestra la proyección por nivel o unidad educativa.", className="text-muted small"),
                        dash_table.DataTable(
                            id="tabla-matriz-desglose-cursos", # 🚀 ID único para la segunda tabla
                            style_cell={"textAlign": "center", "padding": "6px", "fontFamily": "Roboto mono", "fontSize": "12px"},
                            style_header={"backgroundColor": "#f8f9fa", "fontWeight": "bold"},
                            style_table={"marginBottom": "1rem", "overflowX": "auto"}, # overflowX permite scroll horizontal si hay muchos años
                            # Destacamos visualmente la fila de TOTAL UNIDAD para diferenciarla de los cursos individuales
                            style_data_conditional=[
                                            {
                                                'if': {'filter_query': '{NIVEL} eq "TOTAL UNIDAD"'},
                                                'backgroundColor': '#e8f4fd',
                                                'color': '#0056b3',
                                                'fontWeight': 'bold',
                                            },
                                            {
                                                'if': {'filter_query': '{DIFERENCIA} < 0', 'column_id': 'DIFERENCIA'},
                                                'color': '#C0392B',
                                                'fontWeight': 'bold'
                                            },
                                            {
                                                'if': {'filter_query': '{DIFERENCIA} > 0', 'column_id': 'DIFERENCIA'},
                                                'color': '#198754',
                                                'fontWeight': 'bold'
                                            },
                                            {
                                                'if': {'filter_query': '{PORCENTAJE} contains "-"', 'column_id': 'PORCENTAJE'},
                                                'color': '#C0392B',
                                                'fontWeight': 'bold'
                                            },
                                            {
                                                'if': {'filter_query': '{PORCENTAJE} contains "+"', 'column_id': 'PORCENTAJE'},
                                                'color': '#198754',
                                                'fontWeight': 'bold'
                                            },
                                            {
                                                'if': {'filter_query': '{UNIDAD} eq "TOTAL CORPORACIÓN"'},
                                                'backgroundColor': '#2C3E50',
                                                'color': 'white',
                                                'fontWeight': 'bold'
                                            },
                                            {
                                                'if': {'filter_query': '{ESTADO_ESC} eq "Sin cargar"'},
                                                'backgroundColor': '#F5F5F5',
                                                'color': '#AAAAAA',
                                                'fontStyle': 'italic'
                                            },
                                        ]
                        ),
                    ], className="p-3"),

                    # Tarjeta para gráfico COMPARATIVO
                    dbc.Card([
                        dbc.CardHeader(html.Div([
                                                html.H6(" Grafico Comparativo 2026 - Proyección: ", className="m-0 text-dark", style={"display": "inline"}),
                                                html.Span(id="titulo-grafico-comp", className="text-white fw-bold", style={"display": "inline", "marginLeft": "5px"})
                                                ], className="d-flex align-items-center"),
                                                style={"backgroundColor":"#020072"}  # Otro color de fondo
                                        ),
                    # Contenedor del gráfico
                        dbc.CardBody(
                            [ 
                                
                                # Lista despegable de PERIODO para comparar
                                html.Div(
                                        children=[
                                            html.H6(
                                                [
                                                 html.I(className="fa-solid fa-calendar-days me-2"), 
                                                'Período'
                                                ],
                                                className="text-primary fw-bold mb-3"
                                              ),
                                              dcc.Dropdown(
                                                id='periodo-comparativo', 
                                                options=p_corp_options_dropdown,
                                                value=2027,
                                                clearable=False,
                                                style={
                                                        'width': '15%',          # Ancho del dropdown
                                                        'backgroundColor': '#f0f0f0', # Color de fondo
                                                        'color': '#333333',      # Color del texto
                                                        'fontSize': '12px'       # Tamaño de la fuente
                                                      },
                                                
                                            ),
                                        ]),

                                dcc.Loading(
                                    id="corp-loading-grafico",
                                    type="circle",
                                    children=dcc.Graph(config={"displayModeBar": False}, id="grafico-comparativo"),
                                ),
                            ],
                        ),
                        ], id="tarjeta-grafico-comparativo",className="shadow-sm mt-3"), # fin card




                ]),

            ], id="tabs-gestion", active_tab="tab-ingreso", className="shadow-sm bg-white rounded"), # fin dos pestañas para tablas
 # fin tabla configuracion

                


         ], width=8) # Fin columna diagrama general
    ])
], fluid=True) # Fin Layaout para leer en aap.py

# Callback para actualizar Gráfico y Generar Tarjetas KPI de Forma Simultánea
@callback(
    Output("grafico-dinamico-completo", "figure"),
    Output("contenedor-kpis", "children"), # Inyecta las tarjetas aquí
    Output("tabla-datos-reales", "data"), # 🚀 NUEVO OUTPUT AGREGADO AQUÍ
    Output("tabla-matriz-desglose-cursos", "data"),    # 🚀 NUEVO OUTPUT DATA
    Output("tabla-matriz-desglose-cursos", "columns"), # 🚀 NUEVO OUTPUT COLUMNS DINÁMICAS
    Output("variable-matricula", "children"), # nombre unidad educativa para el titulo de gráfico
    Output("grafico-comparativo", "figure"),
    Output("tarjeta-grafico-comparativo", "className"),

    Input({"type": "slider-retencion", "id": ALL}, "value"), # Lista de 10 porcentajes para retención
    Input({"type": "slider-nuevos", "id": ALL}, "value"),    # Lista de 10 cantidades de alumnos
    Input('unidades_educativas', 'value'), # unidad educativa elegida para filtrar excel
    Input('tabla-matriculas-vertical', 'data'), # Reacciona si el usuario edita la matrícula inicial
    Input('dropdown-escenarios-corp', 'value'),  # Escenarios corporativos
    Input('periodo-comparativo','value'), # dropdown periodo comporativo, solo para CORPORATIVO

)
def actualizar_interfaz_proyeccion(lista_retencion, lista_nuevos, unidad_edu, data_tabla_matriculas, escenarios_seleccionados, periodo_graf_comp):
    
# Sección Corporacion
    if unidad_edu == 'CORPORACIÓN':
        titulo_grafico_unidad_educativa = unidad_edu

        # Construir diccionario de escenarios seleccionados
        escenarios_corp = {}
        if escenarios_seleccionados:
            for ruta in escenarios_seleccionados:
                datos = cargar_datos_escenario(ruta)
                if datos:
                    unidad = datos["unidad_educativa"]
                    escenarios_corp[unidad] = datos

        # Si no hay escenarios seleccionados, usar df corporativo default
        if not escenarios_corp:
            df_corporacion, totales_por_unidad = proyecciones.proyeccion_corporativa(
                proyecciones.matriculas_iniciales_default
            )

        else:
            df_corporacion, totales_por_unidad = proyecciones.proyeccion_corporativa(
                proyecciones.matriculas_iniciales_default,
                escenarios_corp = escenarios_corp
            )

                                
        """Cálculo y diseño tarjetas KPI CORPORACIÓN"""
        # region KPI       
        # 1. Determinar nivel matrícula critica de unidad educativa, promedio años 2024, 2025 y 2026
        df_real_solo = df_corporacion[df_corporacion["Tipo"] == "Real"]      
        promedio = df_real_solo.loc[df_real_solo['PERIODO'].isin([2024, 2025, 2026]),'MATRICULA'].mean().round().astype(int)
        
        # 1.1 Matrícula año 2026
        valor_2026 = df_corporacion[df_corporacion["PERIODO"] == 2026]["MATRICULA"].values[0]

        # 2. Matricula Máxima
        fila_max = df_corporacion.loc[df_corporacion["MATRICULA"].idxmax()]
        max_valor = fila_max["MATRICULA"]
        max_anio = fila_max["PERIODO"]

        # 3. Estado de Alerta (¿Cae abajo de promedio en algún año proyectado?)
        df_proy_solo = df_corporacion[df_corporacion["Tipo"] == "Proyección"]
        quiebra_limite = (df_proy_solo["MATRICULA"] < valor_2026 * 0.9).any()
        
        # 4. Cálculo matricula año 2035 para mensaje de alerta específico
        valor_2035 = df_corporacion[df_corporacion["PERIODO"] == 2035]["MATRICULA"].values[0]
        
        # 5. Cálculo porcentaje matricula 20235 sobre matricula 2026

        porcentaje_matricula = valor_2035/valor_2026 - 1   

        if quiebra_limite:
            
            if valor_2035 < valor_2026 * 0.8:
                    kpi_alerta_texto = f"Baja Crítica {porcentaje_matricula:.1%}"
                    kpi_alerta_color = "danger"
            else:    
                    kpi_alerta_texto = f"Baja {porcentaje_matricula:.1%}"
                    kpi_alerta_color = "warning"
            
        else:
                             
            kpi_alerta_texto = f"Estable {'a la baja' if valor_2035 < valor_2026 * 1 else 
                                          
                                          'al alza' if valor_2035 < valor_2026 * 1.1 else 'alza sostenida'
                                          } {porcentaje_matricula:.1%}"
            kpi_alerta_color = "success"
            
        # DEFINIR TU VARIABLE O CONDICIÓN
        # Ejemplo: si el valor es mayor a 50000 es exitoso, si no, es una alerta.

        valor_condicion = valor_2035

        if valor_condicion > valor_2026 * 0.9:
            kpi_bg_1 = "bg-success"  # Fondo verde muy suave
        else:
            
            if valor_condicion < valor_2026 * 0.8:

                kpi_bg_1 = "bg-danger"   # Fondo rojo muy suave
            
            else:
                kpi_bg_1 = "bg-warning"   # Fondo rojo muy suave



        # CONSTRUCCIÓN VISUAL DE LAS TARJETAS KPI (Bootstrap)
        kpis_layout = dbc.Row([
            # 1. Primera Columna 
            dbc.Col(dbc.Card([
                dbc.CardBody([
                    dbc.Row([ # Fila con dos columnas una texto y otra numérica
                        # Columna de texto
                        dbc.Col([
                                html.H6("Última Matrícula", className="text-muted card-subtitle small"),
                                html.Span(f"Año Académico: 2026", className="text-secondary small"),
                                
                        ],
                        width=8,
                        className="d-flex flex-column justify-content-center"
                        ), # Cierre columna Texto

                        # Columna Numérica
                        dbc.Col([
                                html.H6(f"{valor_2026:,}", className="text-white fw-bold my-1 fs-2"),
                        ],
                        width=4,
                        className="d-flex flex-column justify-content-center bg-primary text-white py-3 px-1 text-center rounded"
                        ), # Cierre columna numérica
                    ],
                    className="h-100 g-0" # Alinea verticalmente y quita márgenes (gutters)
                    ) # Cierre de la fila
                ]) # Cierre cuerpo tarjeta
            ],className="border-start border-primary border-2 shadow-sm h-100"), width=5), # Cierre borde tarjeta numero 1
            
            # 2. Segunda Columna 
            dbc.Col(dbc.Card([
                dbc.CardBody([
                    dbc.Row([ # Filas con dos columnas, una de texto y otra numérica
                        # Columna de texto
                        dbc.Col([
                                html.H6("Estado matrícula al 2035", className="text-muted card-subtitle small"),
                                html.H6(kpi_alerta_texto, className=f"text-{kpi_alerta_color} fw-bold my-0 me-2"),
                            ],
                        width=8,
                        className="d-flex flex-column justify-content-center"
                        ), # Cierre columna Texto
                        # Columna numérica
                        dbc.Col([
                                html.Span(f"{valor_2035:,} ", className="text-white fw-bold fs-2"),
                        ],
                        width=4,
                        className= f"{kpi_bg_1} d-flex flex-column justify-content-center text-white py-3 px-1 text-center rounded"
                        ), # Cierre columna numérica
                    ],
                    className="h-100 g-0" # Alinea verticalmente y quita márgenes (gutters)
                    ) # Cierre de la fila
                ]) # Cierre cuerpo segunda tarjeta          
            ], className=f"border-start border-{kpi_alerta_color} border-2 shadow-sm h-100"), width=6), # Cierre borde segunda tarjeta
                    

        ], className="g-3", style={"marginTop": "5px"}) # Cierre fila con dos tarjetas

        # endregion


        """Sección Gráfico Corporativo"""
        # region GRAFICO CORPORATIVO
        # CALCULAR RANGO DINÁMICO SEGÚN LOS DATOS ACTUALES DE ESTA ESCUELA
        # Buscamos el valor máximo y mínimo dentro del DataFrame generado
        valor_maximo_corp = int(df_corporacion["MATRICULA"].max())
        valor_minimo_corp = int(df_corporacion["MATRICULA"].min())

        # Dejamos un 25% de holgura hacia arriba y hacia abajo para que la línea respire
        techo_eje_y_corp = int(valor_maximo_corp * 1.15)
        piso_eje_y_corp = max(0, int(valor_minimo_corp * 0.85))

        
        # Gráfico corporativo con valores default
        corp_graph = graph_objects.Figure()
        df_reales_corp = df_corporacion[df_corporacion["Tipo"] == "Real"]
        df_proy_corp = df_corporacion[df_corporacion["Tipo"] == "Proyección"]
        
        corp_graph.add_trace(graph_objects.Scatter(
            x=df_reales_corp["PERIODO"], y=df_reales_corp["MATRICULA"], name="Datos Reales",
            mode="lines+markers",
            marker=dict(color="#af0000", size=8),
            line=dict(color="#4B4B4B", width=2)
        ))
        
        punto_conexion_corp = df_reales_corp.tail(1)
        df_proy_conectado_corp = pd.concat([punto_conexion_corp, df_proy_corp])
        
        corp_graph.add_trace(graph_objects.Scatter(
            x=df_proy_conectado_corp["PERIODO"], y=df_proy_conectado_corp["MATRICULA"], name="Proyección",
            mode="lines+markers",
            marker=dict(color="#1d1d1d", size=8),
            line=dict(color="#ffae00", width=2)
        ))
        
        corp_graph.update_layout(
            hovermode="x unified", plot_bgcolor="white", height=260,
            margin=dict(l=40, r=30, t=10, b=10),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            font_family='Roboto mono',
        )
        corp_graph.update_xaxes(showgrid=True, gridcolor="#EAEAEA")
        corp_graph.update_yaxes(showgrid=True, 
                                gridcolor="#EAEAEA",
                                range=[piso_eje_y_corp, techo_eje_y_corp],
                                )

        # endregion

        # Preparar datos para la tabla
        df_tabla_corp = df_corporacion.rename(columns={
                                                "PERIODO": "Año",
                                                "MATRICULA": "Valor"
                                             })
        tabla_corp_data = df_tabla_corp.to_dict(orient="records")

        # Tabla comparativa por unidad educativa
        # region Tabla comparativa
        columnas_corp = [
            {"name": "Unidad Educativa", "id": "UNIDAD"},
            {"name": "Matrícula 2026", "id": "MAT_2026", "type": "numeric"},
            {"name": "Matrícula 2035", "id": "MAT_2035", "type": "numeric"},
            {"name": "Diferencia", "id": "DIFERENCIA", "type": "numeric"},
            {"name": "Variación %", "id": "PORCENTAJE"},
            {"name": "Estado Escenario", "id":"ESTADO_ESC"}
        ]

        # Bloque construccion, TABLA COMPARATIVA
        if not escenarios_seleccionados:
            tabla_comp_data = []
            graph_tabla_comp_data = graph_objects.Figure()
            tarjeta_grafico_comparativo = "d-none"

        else:
            filas = []
            total_2026 = 0
            total_2035 = 0
            tarjeta_grafico_comparativo = "shadow-sm mt-3 d-block" 
            
            for unidad_nombre, valores in totales_por_unidad.items():
                val_2026 = valores['2026']
                val_2035 = valores['2035']
                es_default = valores.get('default', False)

                

                if es_default:

                    diferencia = val_2035 - val_2026
                    porcentaje = (diferencia / val_2026 * 100) if val_2026 != 0 else 0
                    
                    filas.append({
                        "UNIDAD": unidad_nombre,
                        "MAT_2026": val_2026,
                        "MAT_2035": val_2035,
                        "DIFERENCIA": diferencia,
                        "PORCENTAJE": f"{porcentaje:+.1f}%",
                        "ESTADO_ESC": "Sin cargar"
                    })
                else:
                    diferencia = val_2035 - val_2026
                    porcentaje = (diferencia / val_2026 * 100) if val_2026 != 0 else 0
                
                    filas.append({
                        "UNIDAD": unidad_nombre,
                        "MAT_2026": val_2026,
                        "MAT_2035": val_2035,
                        "DIFERENCIA": diferencia,
                        "PORCENTAJE": f"{porcentaje:+.1f}%",
                        "ESTADO_ESC": "Cargado"
                    })
                
                total_2026 += val_2026
                total_2035 += val_2035

            # Fila total solo con unidades con escenario
            dif_total = total_2035 - total_2026
            pct_total = (dif_total / total_2026 * 100) if total_2026 != 0 else 0
            filas.append({
                "UNIDAD": "TOTAL CORPORACIÓN",
                "MAT_2026": total_2026,
                "MAT_2035": total_2035,
                "DIFERENCIA": dif_total,
                "PORCENTAJE": f"{pct_total:+.1f}%"
            })
            
            tabla_comp_data = filas # Tabla comparativa para la segunda pestaña en CORPORACION
            # endregion 

            # Creación gráfico Comparativo 2026 con proyecciones si hay escenarios elegidos
            
            # region Preparar datos para FILTRAR escenarios corporativos segun año 1 y año 2
            # Extraer clave tabla_proyeccion de cada unidad educativa
            clave_extraer = "tabla_proyeccion"

            # Crear nuevo diccionario solo con clave principal y tabla de proyeccion
            nuevo_diccionario = {
                clave_principal: sub_diccionario[clave_extraer]
                for clave_principal, sub_diccionario in escenarios_corp.items()
                if clave_extraer in sub_diccionario
            }

            # Clave "Tipo" sera eliminada del diccionario
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

            periodo_comparar = periodo_graf_comp

            # Crear nuevo DataFrame filtrando solo las columnas deseadas
            columnas_seleccionadas = ['UNIDAD_ACADEMICA', 2026, periodo_comparar]
            df_nuevo_comparativo = df_ancho_grafico_comparativo[columnas_seleccionadas]
            

           

            total_mat_year_01 = df_nuevo_comparativo[2026].sum()
            total_mat_year_02 = df_nuevo_comparativo[periodo_comparar].sum()
            fila_total_comparativa = {'UNIDAD_ACADEMICA': 'CORPORACION', 2026: total_mat_year_01, periodo_comparar: total_mat_year_02}
            df_total_comparativa = pd.DataFrame([fila_total_comparativa])

            df_final_comparativo = pd.concat([df_nuevo_comparativo, df_total_comparativa], ignore_index=True)
            df_final_comparativo['% Variación'] = (df_final_comparativo[periodo_comparar]-df_final_comparativo[2026])/df_final_comparativo[2026]

            df_final_comparativo['Diferencia']=df_final_comparativo[periodo_comparar]-df_final_comparativo[2026]

            print (df_final_comparativo)

            # endregion

            # Definicion de variables, ejes colores para gráfico comparativo
            
            x_df_tabla_comp_data = df_final_comparativo["UNIDAD_ACADEMICA"]
            categorias_tabla_comp_data= [2026, periodo_comparar]
            colores_tabla_comp_data= ["#305199","#FFB922"]

            valor_max = df_final_comparativo['% Variación'].max()
            valor_min = df_final_comparativo['% Variación'].min()
            delta_valor_max = valor_max + 0.05
            delta_valor_min = valor_min - 0.05          

            # region Grafico comparativo
            graph_tabla_comp_data = make_subplots ( specs = [[{ "secondary_y" :  True }]])

            for data_value, color in zip(categorias_tabla_comp_data, colores_tabla_comp_data):
            
                    graph_tabla_comp_data.add_trace(
                        graph_objects.Bar(
                                    x=x_df_tabla_comp_data, 
                                    y=df_final_comparativo[data_value],
                                    marker_color = color,
                                    name=data_value,
                                    ),
                                    secondary_y=False,
                                    )
            graph_tabla_comp_data.add_trace(
                    graph_objects.Scatter(
                                x=x_df_tabla_comp_data,
                                y=df_final_comparativo["% Variación"],
                                name="% Variación",
                                customdata=df_final_comparativo["Diferencia"],
                                mode="lines+markers",
                                line=dict(color="#5F5F5F", width=3),
                                marker=dict(color = "#ffffff", size = 12, 
                                                    line=dict(width = 2,
                                                    color = "#BB0000")),
                                
                                ),
                        secondary_y=True,
                        )
            
            graph_tabla_comp_data.update_layout(
                                        hoverlabel_font=dict(family='Roboto mono', weight='bold', size=14, color='black'),
                                        font_family='Roboto mono',
                                        template="simple_white",
                                        margin=dict(l=40, r=30, t=10, b=10),
                                        hovermode="x unified",
                                        yaxis2=dict(
                                            title="Porcentaje Variación",
                                            tickformat=".0%",
                                            range=[delta_valor_min, delta_valor_max],
                                            overlaying="y",
                                            side="right"
                                            ),
                                        legend=dict(
                                            orientation = "h",
                                            x=0.15,          # Posición horizontal (0 = izquierda, 1 = derecha)
                                            y=1.1,          # Posición vertical (0 = abajo, 1 = arriba)
                                            xanchor="left",
                                            yanchor="top"
                                            )
                                        )

            graph_tabla_comp_data.update_xaxes(tickfont_weight='normal', 
                                             tickfont_size=10, 
                                             showgrid=False,
                                             ticks="", 
                                             showline=False,
                                             title_text="",
                                             tickfont=dict(color='gray'),
                                             )
            
            graph_tabla_comp_data.update_yaxes(tickfont_weight='normal', 
                                             showgrid=False, 
                                             tickfont_size=12,
                                             showline=True, 
                                             linecolor="gray",
                                             title_text="",
                                             tickfont=dict(color='gray'),
                                             )

            

           # endregion

            

            
        # Retornamos valores vacíos para los outputs que no aplican
        return (corp_graph, 
                kpis_layout, 
                tabla_corp_data, 
                tabla_comp_data, 
                columnas_corp, 
                titulo_grafico_unidad_educativa,
                graph_tabla_comp_data, # gráfico comparativo CORPORACION
                tarjeta_grafico_comparativo, # TARJETA gráfico comparativo.
                )


# Seccion Unidades Educativa individuales
    else: 
        tarjeta_grafico_comparativo = "d-none"
        # Sección para actualizar matriculas iniciales

        # PASO 1: Clonar el diccionario completo primero 
        # (usando tu variable 'matriculas_iniciales_deafault')
        diccionario_completo_actualizado = copy.deepcopy(proyecciones.matriculas_iniciales_default)

        titulo_grafico_unidad_educativa = unidad_edu

        # 1. Validación inicial por si la tabla viene vacía en el primer renderizado
        if not data_tabla_matriculas:
            # Si está vacía, puedes usar el diccionario default directamente para no romper el flujo
            valores_modificados = proyecciones.matriculas_iniciales_default.get(unidad_edu, {})
        else:
            # 2. Reconstruir el diccionario desde la tabla vertical
            valores_modificados = {}
            for fila in data_tabla_matriculas:
                anio = str(fila["Anio"])
                valor_matricula = int(fila["Matricula"]) if fila["Matricula"] is not None else 0
                valores_modificados[anio] = valor_matricula

        # Reemplazamos solo los datos de la unidad modificada dentro del diccionario completo
        diccionario_completo_actualizado[unidad_edu] = valores_modificados

        # Control de seguridad para que Dash no intente calcular con listas vacías
        if not lista_retencion or not lista_nuevos:
            raise dash.exceptions.PreventUpdate
        
       
        # Data frame para la unidad educativa seleccionada
        df, ultimo_anio_real_str, df_matriz_desglose = calcular_proyeccion_completa(lista_retencion, lista_nuevos, unidad_edu, diccionario_completo_actualizado)
        

       
       
       # region TARJETAS KPI

       # 1. Determinar nivel matrícula critica de unidad educativa, promedio años 2024, 2025 y 2026
        df_real_solo = df[df["Tipo"] == "Real"]      
        promedio = df_real_solo.loc[df_real_solo['Año'].isin(['2024', '2025', '2026']),'Valor'].mean().round().astype(int)
        
        # 1.1 Matrícula año 2026
        valor_2026 = df[df["Año"] == "2026"]["Valor"].values[0]

        # 2. Matricula Máxima
        fila_max = df.loc[df["Valor"].idxmax()]
        max_valor = fila_max["Valor"]
        max_anio = fila_max["Año"]

        # 3. Cálculo matricula año 2035 para mensaje de alerta específico
        valor_2035 = df[df["Año"] == "2035"]["Valor"].values[0]

        # 4. Estado de Alerta (¿Cae abajo de promedio en algún año proyectado?)
        df_proy_solo = df[df["Tipo"] == "Proyección"]
        #quiebra_limite = (df_proy_solo["Valor"] < valor_2026 * 0.9).any()
        quiebra_limite = valor_2035 < valor_2026 * 0.9 # nuevo quiebra límite
        
        
        # 5. Cálculo porcentaje matricula 20235 sobre matricula 2026

        porcentaje_matricula = valor_2035/valor_2026 - 1   

        if quiebra_limite:
            
            if valor_2035 < valor_2026 * 0.8:
                    kpi_alerta_texto = f"Baja Crítica {porcentaje_matricula:.1%}"
                    kpi_alerta_color = "danger"
            else:    
                    kpi_alerta_texto = f"Baja {porcentaje_matricula:.1%}"
                    kpi_alerta_color = "warning"
            
        else:
            
                 
            kpi_alerta_texto = f"Estable {'a la baja' if valor_2035 < valor_2026 * 1 else 
                                          
                                          'al alza' if valor_2035 < valor_2026 * 1.1 else 'alza sostenida'
                                          } {porcentaje_matricula:.1%}"
            kpi_alerta_color = "success"

        
            
        
        # DEFINIR TU VARIABLE O CONDICIÓN
        # Ejemplo: si el valor es mayor a 50000 es exitoso, si no, es una alerta.

        valor_condicion = valor_2035

        if valor_condicion > valor_2026 * 0.9:
            kpi_bg_1 = "bg-success"  # Fondo verde muy suave
        else:
            
            if valor_condicion < valor_2026 * 0.8:

                kpi_bg_1 = "bg-danger"   # Fondo rojo muy suave
            
            else:
                kpi_bg_1 = "bg-warning"   # Fondo rojo muy suave



     # CONSTRUCCIÓN VISUAL DE LAS TARJETAS KPI (Bootstrap)
        kpis_layout = dbc.Row([
            # 1. Primera Columna 
            dbc.Col(dbc.Card([
                dbc.CardBody([
                    dbc.Row([ # Fila con dos columnas una texto y otra numérica
                        # Columna de texto
                        dbc.Col([
                                html.H6("Última Matrícula", className="text-muted card-subtitle small"),
                                html.Span(f"Año Académico: 2026", className="text-secondary small"),
                                
                        ],
                        width=8,
                        className="d-flex flex-column justify-content-center"
                        ), # Cierre columna Texto

                        # Columna Numérica
                        dbc.Col([
                                html.H6(f"{valor_2026:,}", className="text-white fw-bold my-1 fs-2"),
                        ],
                        width=4,
                        className="d-flex flex-column justify-content-center bg-primary text-white py-3 px-1 text-center rounded"
                        ), # Cierre columna numérica
                    ],
                    className="h-100 g-0" # Alinea verticalmente y quita márgenes (gutters)
                    ) # Cierre de la fila
                ]) # Cierre cuerpo tarjeta
            ],className="border-start border-primary border-2 shadow-sm h-100"), width=5), # Cierre borde tarjeta numero 1
            
            # 2. Segunda Columna 
            dbc.Col(dbc.Card([
                dbc.CardBody([
                    dbc.Row([ # Filas con dos columnas, una de texto y otra numérica
                        # Columna de texto
                        dbc.Col([
                                html.H6("Estado matrícula al 2035", className="text-muted card-subtitle small"),
                                html.H6(kpi_alerta_texto, className=f"text-{kpi_alerta_color} fw-bold my-0 me-2"),
                            ],
                        width=8,
                        className="d-flex flex-column justify-content-center"
                        ), # Cierre columna Texto
                        # Columna numérica
                        dbc.Col([
                                html.Span(f"{valor_2035:,} ", className="text-white fw-bold fs-2"),
                        ],
                        width=4,
                        className= f"{kpi_bg_1} d-flex flex-column justify-content-center text-white py-3 px-1 text-center rounded"
                        ), # Cierre columna numérica
                    ],
                    className="h-100 g-0" # Alinea verticalmente y quita márgenes (gutters)
                    ) # Cierre de la fila
                ]) # Cierre cuerpo segunda tarjeta          
            ], className=f"border-start border-{kpi_alerta_color} border-2 shadow-sm h-100"), width=6), # Cierre borde segunda tarjeta
                    

        ], className="g-3", style={"marginTop": "5px"}) # Cierre fila con dos tarjetas
        
     # endregion
        

        # region GRAFICO unidades educativas
        # 1. CALCULAR RANGO DINÁMICO SEGÚN LOS DATOS ACTUALES DE ESTA ESCUELA
        # Buscamos el valor máximo y mínimo dentro del DataFrame generado
        valor_maximo = int(df["Valor"].max())
        valor_minimo = int(df["Valor"].min())
        
        # Dejamos un 25% de holgura hacia arriba y hacia abajo para que la línea respire
        techo_eje_y = int(valor_maximo * 1.25)
        piso_eje_y = max(0, int(valor_minimo * 0.75)) # El 'max' evita que baje de 0 alumnos si hay valores muy chicos

        # Grafico para unidad educativa seleccionada
        unidad_edu_graph = graph_objects.Figure()
        
        df_reales = df[df["Tipo"] == "Real"]
        df_proy = df[df["Tipo"] == "Proyección"]
        
        unidad_edu_graph.add_trace(graph_objects.Scatter(
            x=df_reales["Año"], y=df_reales["Valor"], name="Datos Reales",
            mode="lines+markers", 
            marker=dict(color= "#af0000", size=8),
            line=dict(color="#4B4B4B", width=2)
        ))
        
        punto_conexion = df_reales.tail(1)
        df_proy_conectado = pd.concat([punto_conexion, df_proy])
        
        unidad_edu_graph.add_trace(graph_objects.Scatter(
            x=df_proy_conectado["Año"], y=df_proy_conectado["Valor"], name="Proyección",
            mode="lines+markers",
            marker=dict(color= "#1d1d1d", size=8), 
            line=dict(color="#ffae00", width=2)
        ))
        
        unidad_edu_graph.update_layout(
            hovermode="x unified", plot_bgcolor="white", height=260,
            margin=dict(l=40, r=30, t=10, b=10),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            hoverlabel_font=dict(family='Roboto mono', weight='bold', size=14, color='black'),
            font_family='Roboto mono',
        )
        unidad_edu_graph.update_xaxes(showgrid=True, gridcolor="#EAEAEA")
        
        # CORRECCIÓN DEL EJE Y: Reemplazamos los números fijos por tus variables dinámicas
        unidad_edu_graph.update_yaxes(
                        showgrid=True, 
                        gridcolor="#EAEAEA",
                        range=[piso_eje_y, techo_eje_y]
                        )
        # endregion        

        # 1. Datos para tabla resumen por año
        tabla_consolidada_data = df.to_dict(orient="records") 

        
        # 2. Preparación para la Tabla 2 (Matricula por nivel y año)
        # Creamos las columnas dinámicamente basándonos en las columnas reales que trae el DataFrame
        columnas_matriz = [{"name": "Curso / Nivel", "id": "NIVEL"}] + [
            {"name": col, "id": col} for col in df_matriz_desglose.columns if col != "NIVEL"
        ]

        # Sólo datos, Lista de diccionarios, cada diccionario es un nivel con años y matrícula
        tabla_matriz_data = df_matriz_desglose.to_dict(orient="records") 


        # Retornamos los cinco elementos alineados con la cabecera
        return (
            unidad_edu_graph, # Gráfico unidad educativa
            kpis_layout, # Tarjetas con valores
            tabla_consolidada_data, # Tabla con el resumen por año de la matrícula
            tabla_matriz_data,  # Las filas con los datos desagregados por nivel y año
            columnas_matriz, # Los nombres de las columnas de cada año
            titulo_grafico_unidad_educativa, # título del gráfico
            dash.no_update, # no actualizar grafico compartivo seccion CORPORACION
            tarjeta_grafico_comparativo, # no mostrar grafico compartivo
           )

# Callback para DESCARGAR el archivo Excel vinculando los componentes reales
@callback(
    Output("descarga-excel", "data"),
    Input("btn-exportar-excel", "n_clicks"),
    State({"type": "slider-retencion", "id": ALL}, "value"),
    State({"type": "slider-nuevos", "id": ALL}, "value"),
    State('unidades_educativas', 'value'),
    State('tabla-matriculas-vertical', 'data'),
    State('dropdown-escenarios-corp', 'value'),
    prevent_initial_call=True
)
def exportar_a_excel(n_clicks, lista_retencion, lista_nuevos, unidad_edu, tabla_matriculas_iniciales, escenarios_select):
    

    if unidad_edu == "CORPORACIÓN":
        if not n_clicks :
                return dash.no_update

        # Construir diccionario de escenarios seleccionados
        escenarios_corp = {}
        if escenarios_select:
            for ruta in escenarios_select:
                datos = cargar_datos_escenario(ruta)
                if datos:
                    unidad = datos["unidad_educativa"]
                    escenarios_corp[unidad] = datos

        # Si no hay escenarios seleccionados, usar df corporativo default
        # Extrae 1° data frame "df_proyeccion"
        if not escenarios_corp:
            df_proyeccion, totales_por_unidad = proyecciones.proyeccion_corporativa(
                proyecciones.matriculas_iniciales_default
            )
        else:
            df_proyeccion, totales_por_unidad = proyecciones.proyeccion_corporativa(
                proyecciones.matriculas_iniciales_default,
                escenarios_corp = escenarios_corp
            )

        # Extraer 2° dataframe "df_desagregado"
        df_resumen_corporativo = pd.DataFrame.from_dict(totales_por_unidad, orient="index")
        df_reset_index = df_resumen_corporativo.reset_index(names="UNIDAD EDUCATIVA")
        df_reset_index["Diferencia"] = df_reset_index["2035"] - df_reset_index["2026"]
        df_reset_index["% Variación"] =df_reset_index["Diferencia"]/df_reset_index["2026"]
        df_reset_index_drop = df_reset_index.drop(columns='default')
        fila_total = {
                'UNIDAD EDUCATIVA': 'TOTAL CORPORACIÓN',
                '2026': df_reset_index_drop['2026'].sum(),
                '2035': df_reset_index_drop['2035'].sum(),
                'Diferencia': df_reset_index_drop['Diferencia'].sum(),
                '% Variación': df_reset_index_drop['% Variación'].mean(),
             }

        df_desagregado = pd.concat([df_reset_index_drop, pd.DataFrame([fila_total])], ignore_index=True)
        
              

    else:
        if not n_clicks or not lista_retencion or not lista_nuevos:
                return dash.no_update

        # Copia diccionario de matrículas iniciales
        diccionario_completo_actualizado = copy.deepcopy(proyecciones.matriculas_iniciales_default)
        # 1. Validación inicial por si la tabla de matriculas iniciales 
        # viene vacía en el primer renderizado
        if not tabla_matriculas_iniciales:
            # Si está vacía, se usa el diccionario default directamente para no romper el flujo
            valores_modificados = proyecciones.matriculas_iniciales_default.get(unidad_edu, {})
        else:
            # 2. Reconstruir el diccionario desde la tabla vertical
            valores_modificados = {}
            for fila in tabla_matriculas_iniciales:
                anio = str(fila["Anio"])
                valor_matricula = int(fila["Matricula"]) if fila["Matricula"] is not None else 0
                valores_modificados[anio] = valor_matricula

        # Reemplazamos solo los datos de la unidad modificada
        # dentro del diccionario de matriculas iniciales
        # este nuevo diccionario se utiliza para la proyeccion completa
        diccionario_completo_actualizado[unidad_edu] = valores_modificados
        
        # Calcular proyeccion completa con datos cargados en pantalla
        # sean default al inicio de la aplicación
        # o datos cargados de un escenario
        # se carga con datos de tabla actualizada "diccionario_completo_actualizado"

        # 1° Data frame, df_proyeccion unidad educativa
        df_proyeccion, _, _ = calcular_proyeccion_completa(
            lista_retencion, 
            lista_nuevos, 
            unidad_edu, 
            diccionario_completo_actualizado
            )

        # Extraer diccionario con desagregado por nivel y convertirlo en data frama df_desagregado
        # 2° Data frame, df_desagregado
        _, df_desagregado = proyeccion_por_nivel(
            lista_retencion, 
            lista_nuevos, 
            unidad_edu, 
            diccionario_completo_actualizado)

    # ENVIO DE EXCEL con varias hojas
    # Crear un buffer en memoria con módulo "io" para almacenar hojas
    output = io.BytesIO()

    # Renombrar columnas data frame proyeccion
    df_proyeccion_rename = df_proyeccion.rename(columns={"Año": "Año Académico", "Valor": "Matrícula (Alumnos)", "Tipo": "Estado del Dato"})

    # Agregar multiples hojas con ExcelWriter utilizando buffer "output"
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df_proyeccion_rename.to_excel(writer, sheet_name="DATA_GENERAL", index=False)
        df_desagregado.to_excel(writer, sheet_name="DATA_DESAGREGADO", index=False)

    # Enviar data utilizando send_bytes
    send_excel = dcc.send_bytes(output.getvalue(), "Reporte_Proyeccion_Matriculas.xlsx") 
    
    return send_excel

# Callback para GUARDAR escenario de una unidad educativa específica
@callback(
    Output("mensaje-alerta-escenario", "children"),
    # CORRECCIÓN: Agregamos allow_duplicate=True para permitir que este callback actualice las opciones
    Output("dropdown-escenarios-guardados", "options", allow_duplicate=True), # Actualiza la lista desplegable al guardar
    Input("btn-guardar-escenario", "n_clicks"),
    State("unidades_educativas", "value"),
    State("input-nombre-escenario", "value"),
    State({"type": "slider-retencion", "id": ALL}, "value"),
    State({"type": "slider-nuevos", "id": ALL}, "value"),
    State('tabla-matriculas-vertical', 'data'),
    State('dropdown-escenarios-corp', 'value'),  # ← agregar
    prevent_initial_call=True # Esto es obligatorio si usas allow_duplicate
)
def ejecutar_guardado_escenario(
                        n_clicks, 
                        unidad_edu, 
                        nombre_escenario, 
                        lista_ret, 
                        lista_nuevos, 
                        data_tabla, 
                        escenarios_seleccionados
                        ):
    if not n_clicks:
        raise dash.exceptions.PreventUpdate
        
    if not nombre_escenario or str(nombre_escenario).strip() == "":
        opciones_actuales = listar_escenarios_por_unidad(unidad_edu)
        return "Por favor, ingresa un nombre para el escenario.", opciones_actuales

    # Guardar escenario corporativo
    if unidad_edu == 'CORPORACIÓN':
        # Construir diccionario de receta
        escenarios_por_unidad = {}
        ue_corp = ['BÁSICA 1', 'BÁSICA 2', 'BÁSICA SF', 'MEDIA LOS ANDES', 'MEDIA SAN FELIPE']
        
        for unidad in ue_corp:
            escenarios_por_unidad[unidad] = "default"  # valor inicial
        
        if escenarios_seleccionados:
            for ruta in escenarios_seleccionados:
                datos = cargar_datos_escenario(ruta)
                if datos:
                    escenarios_por_unidad[datos["unidad_educativa"]] = ruta
        
        # Calcular df corporativo para guardar
        df_corp, _ = proyecciones.proyeccion_corporativa(
            proyecciones.matriculas_iniciales_default,
            escenarios_corp={datos["unidad_educativa"]: cargar_datos_escenario(ruta) 
                           for ruta in (escenarios_seleccionados or []) 
                           if cargar_datos_escenario(ruta)}
        )
        
        exito, mensaje = guardar_escenario_corporativo(
            nombre_escenario.strip(), 
            escenarios_por_unidad, 
            df_corp
        )
        
    # Guardar escenario de unidad educativa
    else:

         # Reconstruir diccionario con valores de la tabla
        diccionario_actualizado = copy.deepcopy(proyecciones.matriculas_iniciales_default)
        valores_tabla = {str(fila["Anio"]): fila["Matricula"] for fila in data_tabla}
        diccionario_actualizado[unidad_edu] = valores_tabla


        df, _, _ = calcular_proyeccion_completa(
            lista_ret, lista_nuevos, unidad_edu,
            diccionario_actualizado
        )
        #valores_tabla = {str(fila["Anio"]): fila["Matricula"] for fila in data_tabla}
        exito, mensaje = guardar_escenario_simulacion(
            unidad_edu, nombre_escenario.strip(), lista_ret, lista_nuevos, df, valores_tabla
        )

    nuevas_opciones = listar_escenarios_por_unidad(unidad_edu)

    return mensaje, nuevas_opciones

# Callback para CARGAR un escenario en los Sliders
@callback(
    Output({"type": "slider-retencion", "id": ALL}, "value"),
    Output({"type": "slider-nuevos", "id": ALL}, "value"),
    Output('tabla-matriculas-vertical', 'data', allow_duplicate=True),  # ← nuevo
    Output('dropdown-escenarios-corp', 'value', allow_duplicate=True),  # ← nuevo, corporativo
    Input("btn-cargar-escenario", "n_clicks"),
    State("dropdown-escenarios-guardados", "value"),
    State({"type": "slider-retencion", "id": ALL}, "value"),  # ← para mantener valores actuales
    State({"type": "slider-nuevos", "id": ALL}, "value"),     # ← para mantener valores actuales
    prevent_initial_call=True
)
def ejecutar_carga_en_sliders(n_clicks, ruta_archivo_escenario, sliders_ret_actuales, sliders_nuevos_actuales):

    if not n_clicks or not ruta_archivo_escenario:
        raise dash.exceptions.PreventUpdate
        
    datos_escenario = cargar_datos_escenario(ruta_archivo_escenario)
    
    if datos_escenario is None:
        raise dash.exceptions.PreventUpdate
    
    # Detectar tipo de escenario
    if datos_escenario.get("tipo") == "corporativo":
        # Cargar escenario corporativo — restaurar dropdown múltiple
        escenarios_por_unidad = datos_escenario.get("escenarios_por_unidad", {})
        carpeta = str(asegurar_carpeta_escenarios())

        # Reconstruir rutas completas desde el nombre del archivo
        rutas_seleccionadas = [
        str(Path(carpeta) / nombre_archivo)
        for nombre_archivo in escenarios_por_unidad.values()
        if nombre_archivo != "default"
       ]

        return sliders_ret_actuales, sliders_nuevos_actuales, dash.no_update, rutas_seleccionadas
    
    else:
        # Cargar escenario de unidad educativa — comportamiento original
        valores_retencion_guardados = datos_escenario.get("valores_retencion", [])
        valores_nuevos_guardados = datos_escenario.get("valores_nuevos", [])
        valores_tabla = datos_escenario.get("valores_tabla_inicial", {})
        filas_tabla = [{"Anio": anio, "Matricula": valor} for anio, valor in valores_tabla.items()]
        
        return valores_retencion_guardados, valores_nuevos_guardados, filas_tabla, dash.no_update

# Callback para abrir el Modal, lo Cierra con "Cancelar" y limpia/muestra errores
@callback(
    Output("modal-confirmacion-eliminar", "is_open"),
    Output("mensaje-alerta-escenario", "children", allow_duplicate=True),
    Input("btn-eliminar-escenario", "n_clicks"),
    Input("btn-modal-cancelar", "n_clicks"),
    State("dropdown-escenarios-guardados", "value"),
    prevent_initial_call=True
)
def controlar_visibilidad_modal(click_eliminar, click_cancelar, ruta_archivo_escenario):
    # Identificamos cuál de los dos botones disparó este callback
    ctx = dash.callback_context
    if not ctx.triggered:
        raise exceptions.PreventUpdate
        
    id_disparador = ctx.triggered[0]["prop_id"].split(".")[0]

    # CASO A: El usuario presionó el botón "Eliminar" principal
    if id_disparador == "btn-eliminar-escenario":
        # Validación: Si no hay escenario, no abrimos el modal y mostramos error
        if not ruta_archivo_escenario:
            mensaje_error = html.Span([
                html.I(className="bi bi-exclamation-triangle-fill me-2 text-danger"),
                "Por favor, selecciona un escenario antes de intentar eliminar."
            ])
            return False, mensaje_error
            
        # Si hay escenario seleccionado: Abrimos el modal (True) y LIMPIAMOS el texto viejo (None)
        return True, None

    # CASO B: El usuario presionó "Cancelar" dentro del Modal
    if id_disparador == "btn-modal-cancelar":
        # Cerramos el modal (False) y no alteramos los mensajes de la pantalla
        return False, no_update

    raise exceptions.PreventUpdate

# Callback para ELIMINAR un escenario en los Sliders, con ventana emergente de seguridad
@callback(
    Output("mensaje-alerta-escenario", "children", allow_duplicate=True),
    Output("dropdown-escenarios-guardados", "options", allow_duplicate=True),
    Output("dropdown-escenarios-guardados", "value"), # Resetea el selector visual a vacío
    
    Output("modal-confirmacion-eliminar", "is_open", allow_duplicate=True), # Cerramos el modal tras borrar
    Input("btn-modal-aceptar", "n_clicks"),
    
    State("unidades_educativas", "value"),
    State("dropdown-escenarios-guardados", "value"),
    prevent_initial_call=True
)
def ejecutar_eliminacion_escenario(click_aceptar, unidad_edu, ruta_archivo_escenario):
    if not click_aceptar or not ruta_archivo_escenario:
        raise dash.exceptions.PreventUpdate
        
    # 1. Borramos el archivo del disco
    _, mensaje = eliminar_archivo_escenario(ruta_archivo_escenario)
    
    # 2. Listamos nuevamente los escenarios vigentes de esta escuela
    nuevas_opciones = listar_escenarios_por_unidad(unidad_edu)
    
    # 3. Retornamos el mensaje, las nuevas opciones y limpiamos la selección
    return mensaje, nuevas_opciones, None, False


# Callback limpia el texto del gráfico de inmediato si cambia el dropdown de unidades educativas
@callback(
    Output('escenario-text', 'children', allow_duplicate=True),
    Input('unidades_educativas', 'value'),
    prevent_initial_call=True # Evita que borre cosas al cargar la página
)
def limpiar_texto_al_cambiar(valor_dropdown):
    # No importa qué elija el usuario, devolvemos un texto vacío ("") 
    # para asegurar que el label anterior desaparezca de la pantalla
    return ""

# Callback para extraer el nombre del escenario elegido
@callback(
    Output("escenario-text", "children"),
    Input("btn-cargar-escenario", "n_clicks"),
    State("dropdown-escenarios-guardados", "value"),
    State("dropdown-escenarios-guardados", "options"),
    prevent_initial_call=True 
 )
def nombre_escenario(n_clicks, value_escenarios,options_escenarios):

    if not n_clicks or not value_escenarios or not options_escenarios:
            raise dash.exceptions.PreventUpdate

    for option in options_escenarios:
        if option["value"] == value_escenarios:
            return  f", escenario: {option['label']}"
       
    return ""


""" Funciones de Modelado Para matrículas"""

# Callback Modelo Lineal
@callback(
    Output('tabla-matriculas-vertical', 'data', allow_duplicate=True),
    Output('msg-modelo-lineal', 'children'),
    Input('btn-modelo-lineal', 'n_clicks'),
    State('input-lineal-p0', 'value'),
    State('input-lineal-pendiente', 'value'),
    State('unidades_educativas', 'value'),
    prevent_initial_call=True
)
def aplicar_modelo_lineal(n_clicks, p0, pendiente, unidad_edu):
    if not n_clicks:
        raise dash.exceptions.PreventUpdate
    
    # Validaciones
    if p0 is None or pendiente is None:
        return dash.no_update, "Ingresa P0 y la pendiente antes de cargar."
    
    if unidad_edu == 'CORPORACIÓN':
        return dash.no_update, "Selecciona una unidad educativa primero."
    
    # Calcular proyección lineal
    resultado = proyecciones.modelo_lineal(p0, pendiente)
    
    # Convertir a formato de tabla
    filas_tabla = [{"Anio": anio, "Matricula": valor} for anio, valor in resultado.items()]
    
    return filas_tabla, f"Modelo lineal cargado — P0: {p0}, pendiente: {pendiente:+.0f} alumnos/año"

# Callback Modelo Logístico
@callback(
    Output('tabla-matriculas-vertical', 'data', allow_duplicate=True),
    Output('msg-modelo-logistico', 'children'),
    Output('label-k-logistico', 'children'),  # ← cambia el label según modo
    Input('btn-modelo-logistico', 'n_clicks'),
    Input('check-decrecimiento', 'value'),     # ← reacciona al checkbox
    State('input-logistico-p0', 'value'),
    State('input-logistico-k', 'value'),
    State('slider-logistico-r', 'value'),
    State('unidades_educativas', 'value'),
    prevent_initial_call=True
)
def aplicar_modelo_logistico(n_clicks, modo_decrecer, p0, k, r, unidad_edu):
    
    ctx = dash.callback_context
    trigger = ctx.triggered[0]['prop_id'].split('.')[0]
    
    # Si el trigger es el checkbox, solo actualizar el label
    if trigger == 'check-decrecimiento':
        if 'decrecer' in (modo_decrecer or []):
            return dash.no_update, dash.no_update, "Límite inferior (K mín):"
        else:
            return dash.no_update, dash.no_update, "Capacidad máxima (K máx):"
    
    # Si el trigger es el botón
    if not n_clicks:
        raise dash.exceptions.PreventUpdate
    
    # Validaciones
    if p0 is None or k is None:
        return dash.no_update, "Ingresa P0 y K antes de cargar.", dash.no_update
    
    if unidad_edu == 'CORPORACIÓN':
        return dash.no_update, "Selecciona una unidad educativa primero.", dash.no_update
    
    # Calcular según modo
    if 'decrecer' in (modo_decrecer or []):
        resultado = proyecciones.modelo_logistico_decrecimiento(p0, k, r)
        msg = f"Decrecimiento gradual — P0: {p0}, K mín: {k}, r: {r}"
    else:
        resultado = proyecciones.modelo_logistico_crecimiento(p0, k, r)
        msg = f"Crecimiento logístico — P0: {p0}, K máx: {k}, r: {r}"
    
    # Convertir a formato de tabla
    filas_tabla = [{"Anio": anio, "Matricula": valor} for anio, valor in resultado.items()]
    
    return filas_tabla, msg, dash.no_update

# Callback para cargar K default según unidad educativa
@callback(
    Output('input-logistico-k', 'value'),
    Output('input-lineal-p0', 'value'),
    Output('input-logistico-p0', 'value'),
    Input('unidades_educativas', 'value')
)
def cargar_defaults_modelos(unidad_edu):
    if unidad_edu == 'CORPORACIÓN' or unidad_edu is None:
        return dash.no_update, dash.no_update, dash.no_update
    
    # K default según unidad
    k_default = proyecciones.capacidad_maxima_default.get(unidad_edu, {}).get('K_max', 100)
    
    # P0 default: matrícula 2026 desde datos históricos
    # datos_reales = proyecciones.cargar_datos_consolidados(unidad_edu)
    p0_default= proyecciones.matriculas_iniciales_default.get(unidad_edu, {}).get('2027',100)
    # p0_default = datos_reales.get('2026', 0)
    
    return k_default, p0_default, p0_default

