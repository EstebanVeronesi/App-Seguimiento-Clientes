# app.py
import os
import dash
import flask
import dash_bootstrap_components as dbc
from dash import dcc, Input, Output, html, State # Asegurarse de que 'html' esté importado
from flask_login import LoginManager, current_user
from dotenv import load_dotenv
from core.auth import User
from core.db import init_db_pool

# --- FUENTE DE GOOGLE (Solo Lato) ---
google_fonts = "https://fonts.googleapis.com/css2?family=Lato:wght@400;700&display=swap"
# ---------------------------------------

# Cargar variables de entorno
load_dotenv()

# Iniciar servidor Flask
server = flask.Flask(__name__)
server.config.update(
    SECRET_KEY=os.getenv("FLASK_SECRET_KEY", "un-valor-secreto-por-defecto"),
    DB_POOL=init_db_pool()
)

# Configurar Flask-Login
login_manager = LoginManager()
login_manager.init_app(server)
login_manager.login_view = "/login" # Ruta a la que redirige si no está autenticado
login_manager.session_protection = "strong"
@login_manager.user_loader
def load_user(user_id):
    pool = server.config["DB_POOL"]
    return User.get(user_id, pool)

# Iniciar aplicación Dash
app = dash.Dash(
    __name__,
    server=server,
    use_pages=True,
    external_stylesheets=[dbc.themes.BOOTSTRAP, google_fonts],
    suppress_callback_exceptions=True,
    meta_tags=[{'name': 'viewport', 'content': 'width=device-width, initial-scale=1'}]
)
app.title = "Seguimiento de Clientes"

# --- Layout Principal (Ajustado para Header personalizado) ---
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    # El Header (logo, links) se renderizará aquí
    html.Div(id='navbar-container'),
    # El Contenido de la Página (Dashboards, Forms) se renderizará aquí
    dbc.Container(
        html.Div(id='page-container-wrapper', children=dash.page_container),
        fluid=False, # Centrado
        className="mt-4"
    )
])


# --- CALLBACK DE NAVBAR Y CONTENIDO (ACTUALIZADO) ---
@app.callback(
    Output('navbar-container', 'children'), # Controla el Header
    Output('page-container-wrapper', 'style'), # Controla la visibilidad del contenido
    Input('url', 'pathname')
)
def update_navbar_and_page_visibility(pathname):
    """
    Actualiza el header según el rol y gestiona la visibilidad.
    """
    
    if pathname == '/login':
        return None, {'display': 'block'} # Sin header en login

    if not current_user.is_authenticated and pathname != '/login':
         return None, {'display': 'none'} # Ocultar contenido fantasma

    # --- SI ESTAMOS AUTENTICADOS ---
    # --- CORRECCIÓN: Añadir '/nueva-interaccion' al gerente ---
    roles_paginas = {
        'gerente': ['/dashboard-gerencia', '/sincronizar-clientes', '/nueva-interaccion'],
        'vendedor': ['/dashboard-vendedor', '/nueva-interaccion']
    }
    # --------------------------------------------------------
    
    paginas_permitidas = roles_paginas.get(current_user.rol, [])

    paginas_a_mostrar = [
        page for page in dash.page_registry.values()
        if page['path'] in paginas_permitidas
    ]
    # Ordenar (usando 'name' como fallback seguro)
    paginas_a_mostrar.sort(key=lambda page: (page.get('order', float('inf')), page.get('name', '')))

    links_principales = [
        dbc.NavLink(page.get('name', 'Link?'), href=page['relative_path'], active="exact")
        for page in paginas_a_mostrar
    ]
    
    # Añadir link de Cerrar Sesión
    links_principales.append(dbc.NavLink("Cerrar Sesión", href="/logout", className="nav-link-logout"))


    # --- Construir el Header Personalizado con Toggler ---
    header = html.Header(
        dbc.Navbar(
            dbc.Container(
                [
                    html.Img(
                        src=app.get_asset_url('logo-frigorifico-la-morena.webp'),
                        className="header-logo"
                    ),
                    dbc.NavbarToggler(id="navbar-toggler", n_clicks=0),
                    dbc.Collapse(
                        dbc.Nav(
                            links_principales,
                            className="header-nav ms-auto",
                            navbar=True,
                        ),
                        id="navbar-collapse",
                        is_open=False,
                        navbar=True,
                    ),
                ],
                fluid=False,
            ),
            className="app-header",
            color=None,
            dark=False,
        ),
        className="app-header-wrapper"
    )
    # --- Fin Header Personalizado ---
    
    return header, {'display': 'block'}


# --- CALLBACK: Para abrir/cerrar el menú hamburguesa ---
@app.callback(
    Output("navbar-collapse", "is_open"),
    [Input("navbar-toggler", "n_clicks")],
    [State("navbar-collapse", "is_open")],
    prevent_initial_call=True,
)
def toggle_navbar_collapse(n, is_open):
    if n:
        return not is_open
    return is_open
# -------------------------------------------------------------

# --- Punto de entrada (en index.py) ---
# if __name__ == "__main__":
#     app.run(debug=True, host="0.0.0.0", port=3000)