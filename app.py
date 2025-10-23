# app.py
import os
import dash
import flask
from flask import session, request, redirect, url_for # Asegurar importaciones
import dash_bootstrap_components as dbc
from dash import dcc, Input, Output, html, State
from flask_login import LoginManager, current_user, login_required
from dotenv import load_dotenv
from core.auth import User
from core.db import init_db_pool
from core import google_auth
import traceback # Importar traceback

google_fonts = "https://fonts.googleapis.com/css2?family=Lato:wght@400;700&display=swap"

load_dotenv()

server = flask.Flask(__name__)
server.config.update(
    SECRET_KEY=os.getenv("FLASK_SECRET_KEY", "un-valor-secreto-por-defecto-cambiar"), # Cambiar default si es necesario
    DB_POOL=init_db_pool()
)

# --- DEBUG: Imprimir la SECRET_KEY cargada ---
print(f"DEBUG: Flask SECRET_KEY cargada: {server.config.get('SECRET_KEY')}")
# ----------------------------------------------

login_manager = LoginManager()
login_manager.init_app(server)
login_manager.login_view = "/login"
login_manager.session_protection = "strong"
@login_manager.user_loader
def load_user(user_id):
    # --- DEBUG: Ver quién se está cargando ---
    print(f"DEBUG: user_loader llamado para user_id: {user_id}")
    # -----------------------------------------
    pool = server.config["DB_POOL"]
    user = User.get(user_id, pool)
    # --- DEBUG: Ver resultado de User.get ---
    print(f"DEBUG: User.get devolvió: {'Usuario encontrado' if user else 'None'}")
    # ---------------------------------------
    return user

app = dash.Dash(
    __name__,
    server=server,
    use_pages=True,
    external_stylesheets=[dbc.themes.BOOTSTRAP, google_fonts],
    suppress_callback_exceptions=True,
    meta_tags=[{'name': 'viewport', 'content': 'width=device-width, initial-scale=1'}]
)
app.title = "Seguimiento de Clientes"

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='navbar-container'),
    dbc.Container(
        html.Div(id='page-container-wrapper', children=dash.page_container),
        fluid=False,
        className="mt-4"
    )
])

# --- RUTA FLASK: Callback de OAuth (con más prints) ---
@server.route('/oauth2callback')
@login_required # Este decorador podría ser la causa del logout si la sesión se pierde ANTES
def oauth2callback():
    print(f"DEBUG: Entrando a /oauth2callback. Usuario actual: {current_user.id if current_user.is_authenticated else 'Anónimo'}")
    state = session.get('google_oauth_state')
    print(f"DEBUG: State en sesión: {state}")
    print(f"DEBUG: State recibido: {request.args.get('state')}")

    if not state or state != request.args.get('state'):
        print("ERROR: State de OAuth no coincide o falta. Redirigiendo a home.")
        home_path = dash.page_registry.get('pages.home', {}).get('path', '/')
        return redirect(home_path)

    flow = google_auth.get_google_auth_flow()
    if not flow:
         print("ERROR: No se pudo crear el flow de Google Auth. Redirigiendo a home.")
         home_path = dash.page_registry.get('pages.home', {}).get('path', '/')
         return redirect(home_path)

    try:
        auth_response = request.url
        print(f"DEBUG: authorization_response URL: {auth_response}")
        # Considerar HTTPS en producción si es necesario
        # if not auth_response.startswith('https://') and 'localhost' not in auth_response:
        #      auth_response = auth_response.replace('http://', 'https://', 1)

        flow.fetch_token(authorization_response=auth_response)
        credentials = flow.credentials
        print("DEBUG: Token obtenido de Google.")

        if not current_user or not hasattr(current_user, 'dni'):
             print("ERROR: No se pudo obtener DNI del usuario actual para guardar credenciales. Redirigiendo a login.")
             login_path = dash.page_registry.get('pages.login', {}).get('path', '/login')
             return redirect(login_path)

        print(f"DEBUG: Intentando guardar credenciales para DNI: {current_user.dni}")
        save_success = google_auth.save_google_credentials(current_user.dni, credentials)
        print(f"DEBUG: Resultado de guardar credenciales: {save_success}")

        session.pop('google_oauth_state', None)
        print("DEBUG: Autorización de Google completada exitosamente. Redirigiendo a nueva-interaccion.")
        interaction_path = dash.page_registry.get('pages.02_interaccion', {}).get('path', '/nueva-interaccion')
        return redirect(interaction_path)

    except Exception as e:
        print(f"ERROR: Excepción durante el callback de OAuth: {e}")
        traceback.print_exc() # Imprimir el traceback completo
        home_path = dash.page_registry.get('pages.home', {}).get('path', '/')
        return redirect(home_path)
# --- FIN RUTA ---


# --- Callback NAVBAR ---
@app.callback(
    Output('navbar-container', 'children'),
    Output('page-container-wrapper', 'style'),
    Input('url', 'pathname')
)
def update_navbar_and_page_visibility(pathname):
    # --- DEBUG: Ver estado de autenticación al inicio del callback ---
    print(f"DEBUG Navbar Callback - Path: {pathname}, Autenticado: {current_user.is_authenticated}")
    # -------------------------------------------------------------

    if pathname == '/login':
        return None, {'display': 'block'}

    # Si NO está autenticado (y no es login), NO mostrar navbar ni contenido
    if not current_user.is_authenticated and pathname != '/login':
         print("DEBUG Navbar: Usuario no autenticado detectado fuera de /login.")
         return None, {'display': 'none'}

    # Si LLEGAMOS AQUÍ, el usuario DEBERÍA estar autenticado
    roles_paginas = {
        'gerente': ['/dashboard-gerencia', '/sincronizar-clientes', '/nueva-interaccion', '/dashboard-vendedor'],
        'vendedor': ['/dashboard-vendedor', '/nueva-interaccion']
    }
    # Asegurarse de que current_user.rol existe si está autenticado
    user_rol = getattr(current_user, 'rol', None)
    paginas_permitidas = roles_paginas.get(user_rol, []) if user_rol else []

    paginas_disponibles = [page for page in dash.page_registry.values()]
    paginas_a_mostrar = [
        page for page in paginas_disponibles
        if page['path'] in paginas_permitidas
    ]
    paginas_a_mostrar.sort(key=lambda page: (page.get('order', float('inf')), page.get('name', '')))

    links_principales = [
        dbc.NavLink(page.get('name', 'Link?'), href=page['relative_path'], active="exact")
        for page in paginas_a_mostrar
    ]

    try:
        auth_page_info = dash.page_registry.get('pages.authorize_google')
        if auth_page_info:
            # --- DEBUG: Verificar DNI antes de cargar credenciales ---
            user_dni = getattr(current_user, 'dni', None)
            print(f"DEBUG Navbar: Verificando creds para DNI: {user_dni}")
            # ------------------------------------------------------
            if user_dni: # Solo intentar cargar si tenemos DNI
                creds_json = google_auth.load_google_credentials(user_dni)
                if not creds_json:
                    links_principales.append(dbc.NavLink("Conectar Google Calendar", href=auth_page_info['relative_path']))
                else:
                    links_principales.append(dbc.NavItem(html.Span("📅 Conectado", className="nav-link disabled")))
            else:
                 print("WARN Navbar: No se pudo obtener DNI para verificar credenciales de Google.")
    except Exception as e:
         print(f"ERROR al verificar credenciales o página de autorización en Navbar: {e}")

    links_principales.append(dbc.NavLink("Cerrar Sesión", href="/logout", className="nav-link-logout"))

    header = html.Header( # ... (resto del header sin cambios) ...
         dbc.Navbar(
            dbc.Container(
                [
                    html.Img(src=app.get_asset_url('logo-frigorifico-la-morena.webp'), className="header-logo"),
                    dbc.NavbarToggler(id="navbar-toggler", n_clicks=0),
                    dbc.Collapse(
                        dbc.Nav(links_principales, className="header-nav ms-auto", navbar=True),
                        id="navbar-collapse", is_open=False, navbar=True,
                    ),
                ], fluid=False,
            ), className="app-header", color=None, dark=False,
        ), className="app-header-wrapper"
    )
    return header, {'display': 'block'}


@app.callback(
    Output("navbar-collapse", "is_open"),
    [Input("navbar-toggler", "n_clicks")],
    [State("navbar-collapse", "is_open")],
    prevent_initial_call=True,
)
def toggle_navbar_collapse(n, is_open):
    if n: return not is_open
    return is_open