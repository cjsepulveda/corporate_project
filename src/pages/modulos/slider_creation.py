
from dash import html, dcc
import dash_bootstrap_components as dbc

def crear_grupo_sliders(titulo_grupo, prefijo_id, tipo_slider='retencion', tasas_nivel=None):
    """
    Genera un grupo de sliders colapsados.
    tipo_slider puede ser: 'retencion' (porcentajes) o 'nuevos' (cantidades de alumnos).
    """
    sliders = []

    # Estructura limpia: la clave coincide exactamente con el prefijo_id que le pases
    niveles_corporacion = {
        'grupo-a': ['PRE-KINDER', 'KINDER'],
        'grupo-b': ['1BÁSICO', '2BÁSICO', '3BÁSICO', '4BÁSICO'],
        'grupo-c': ['5BÁSICO', '6BÁSICO', '7BÁSICO', '8BÁSICO'],
        'grupo-d':['1MEDIO','2MEDIO','3MEDIO','4MEDIO']
    }
        
    # Obtenemos la lista de cursos para este grupo específico
    cursos = niveles_corporacion[prefijo_id]

    # Iteramos directamente sobre los cursos obteniendo su índice (i) y su nombre (curso)
    for i, curso in enumerate(cursos, start=1):
        
        # CLAVE: El type del ID ahora incluye el tipo de slider para que el Callback no los mezcle
        id_diccionario = {"type": f"slider-{tipo_slider}", "id": f"{prefijo_id}-{i}"}
        
        #id_diccionario = {"type": "slider-dinamico", "id": f"{prefijo_id}-{i}"}
        
         # Configuramos las propiedades según el tipo
        if tipo_slider == 'retencion':
                min_val, max_val, val_defecto = 50, 100, 95
                marcas = {j: f"{j}%" for j in range(50, 101, 10)}
                clase = "slider-retencion"

        elif tipo_slider == 'nuevos': # 👈 Ahora es estricto para 'nuevos'
                
                #control prekinder
                if curso == "PRE-KINDER" or curso =="1MEDIO":
                     min_val, max_val, val_defecto = 0, 500, 0
                     marcas = {j: str(j) for j in range(0, 501, 50)}
                     clase = "slider-nuevos"
                else:
                    min_val, max_val, val_defecto = 0, 500, 10
                    marcas = {j: str(j) for j in range(0, 501, 50)}
                    clase = "slider-nuevos"

        else:
                # Si te equivocas al escribir el nombre en el layout, Python te avisará de inmediato
                raise ValueError(f"Error: El tipo_slider '{tipo_slider}' no es válido. Usa 'retencion' o 'nuevos'.")
        
        # bloquear solo el primer slider de cada grupo
        es_nivel_cero = (i == 1) and (curso =="PRE-KINDER" or curso =="1MEDIO")

        # Etiqueta de tasa solo para slider de nuevos
        etiqueta_tasa = None
        if tipo_slider == 'nuevos' and tasas_nivel:
            tasa = tasas_nivel.get(curso, 0.0)
            
            if tasa > 0:
                color_fondo = "#198754"  # verde
                simbolo = f"+{tasa*100:.1f}%"
                tooltip = "Tendencia al alza en alumnos nuevos"
            elif tasa < 0:
                color_fondo = "#dc3545"  # rojo
                simbolo = f"{tasa*100:.1f}%"
                tooltip = "Tendencia a la baja en alumnos nuevos"
            else:
                color_fondo = "#fd7e14"  # naranja
                simbolo = "0.0%"
                tooltip = "Tendencia estable en alumnos nuevos"

            # ← id único para vincular tooltip
            id_etiqueta = f"badge-tasa-{prefijo_id}-{i}"

            etiqueta_tasa = html.Span([
                html.Span(
                    simbolo,
                    id=id_etiqueta,
                    style={
                        "backgroundColor": color_fondo,
                        "color": "white",
                        "fontSize": "11px",
                        "fontWeight": "bold",
                        "padding": "2px 7px",
                        "borderRadius": "10px",
                        "marginLeft": "8px",
                        "verticalAlign": "middle",
                        "cursor": "pointer"
                    }
                ),
                dbc.Tooltip(
                    tooltip,
                    target=id_etiqueta,
                    placement="top"
                )
            ])

        sliders.append(
                html.Div([
                    html.Div([
                        html.Label(curso, style={"fontWeight": "bold", "fontSize": "14px"}),
                        etiqueta_tasa if etiqueta_tasa else html.Span()  # ← etiqueta al lado del nombre
                    ], style={"display": "flex", "alignItems": "center", "marginBottom": "5px"}),
                    dcc.Slider(
                        min=min_val, max=max_val, value=val_defecto, step=1,
                        id=id_diccionario,
                        marks=marcas,
                        className=clase,
                        disabled=es_nivel_cero
                    )
                ], style={"marginBottom": "20px", "opacity": "0.4" if es_nivel_cero else "1"})
            )
            
            
    return html.Details([
        html.Summary(titulo_grupo, style={"cursor": "pointer", 
                                          "fontWeight": "bold", 
                                          "fontSize": "14px", 
                                          "padding": "10px", 
                                          "color":"#333333",
                                          "backgroundColor": "#e6f0fa", 
                                          "borderRadius": "5px", 
                                          "marginBottom": "10px"}
                                          ),
        html.Div(sliders, style={"padding": "10px 15px"})
    ], open=False, style={"marginBottom": "15px"})
