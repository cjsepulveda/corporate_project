from dash import html, register_page  #, callback # If you need callbacks, import it here.

register_page(
    __name__,
    name='HOME',
    top_nav=True,
    path='/'
)

image_path = 'assets/logo_nuevo.png'

def layout():
    layout = html.Div([
        
        html.Br(), 
        html.Img(src=image_path,
                 style={
                    "width": "20%",      # Ocupará la mitad del ancho de la pantalla o del Div
                    "height": "auto"     # Mantiene la proporción original para que no se deforme
                    }
                   ),
        
        html.Br(),
        html.Br(),
        html.P(
            [
                "Análisis de Datos, elija una opción del menu"
            ], className='home'
        )
    ])
    return layout