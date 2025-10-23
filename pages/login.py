# pages/login.py
import dash
from dash import dcc, html, callback, Input, Output, State, no_update, ctx
import dash_bootstrap_components as dbc
import flask
from flask_login import login_user, current_user
from core.auth import User
# from app import app # No es necesario

dash.register_page(__name__, path='/login', title="Login")

# --- Header simple solo con el logo (MODIFICADO: Estructura y clases) ---
login_header = html.Header(
    dbc.Navbar(
        # --- MODIFICACIÓN: Container fluid, sin Row/Col interno ---
        dbc.Container(
            html.Img(
                src="/assets/logo-frigorifico-la-morena.webp",
                # Aplicamos clases directamente a la imagen para centrarla
                className="header-logo login-header-logo "
            ),
            fluid=True # <-- Ocupa todo el ancho
        ),
        # --- FIN MODIFICACIÓN ---
        color="light",
        className="app-header login-navbar-padding" # Clase para padding extra
    )
)
# --- FIN HEADER ---

# --- Layout Card Login (sin cambios) ---
login_card_layout = dbc.Container([
    dbc.Row(dbc.Col(
        dbc.Card([
            dbc.CardHeader(html.H4("Iniciar Sesión")),
            dbc.CardBody([
                dbc.Alert("Email o contraseña inválidos", color="danger", id="login-alert", is_open=False),
                dbc.Form([
                    dbc.Label("Email", html_for="login-email"),
                    dbc.Input(type="email", id="login-email", placeholder="tu@email.com"),
                ], className="mb-3"),
                dbc.Form([
                    dbc.Label("Contraseña", html_for="login-password"),
                    dbc.Input(type="password", id="login-password", placeholder="Contraseña"),
                ], className="mb-3"),
                dbc.Button("Ingresar", color="primary", id="login-button", n_clicks=0, className="w-100"),
            ])
        ]),
        width=10, md=6, lg=4
    ), justify="center")
])

# --- Layout Final Combinado ---
layout = html.Div([
    login_header,
    login_card_layout
])

# --- Callbacks (Sin cambios) ---
@callback(
    Output('login-alert', 'is_open', allow_duplicate=True),
    Input('login-email', 'value'),
    Input('login-password', 'value'),
    prevent_initial_call=True
)
def hide_alert_on_input(email, password):
    return False

@callback(
    Output('url', 'pathname'),
    Output('login-alert', 'is_open'),
    Output('login-alert', 'children'),
    Output('url', 'refresh'),
    Input('login-button', 'n_clicks'),
    State('login-email', 'value'),
    State('login-password', 'value'),
    prevent_initial_call=True
)
def handle_login(n_clicks, email, password):
    triggered_id = ctx.triggered_id
    if not n_clicks or n_clicks == 0:
        return no_update, False, no_update, False
    error_message = "Email o contraseña inválidos"
    if not email or not password:
        error_message = "Debe ingresar Email y Contraseña."
        return no_update, True, error_message, False
    pool = flask.current_app.config["DB_POOL"]
    user = User.authenticate(email, password, pool)
    if user:
        login_user(user, remember=True)
        if user.rol == 'gerente': target_path = '/dashboard-gerencia'
        elif user.rol == 'vendedor': target_path = '/dashboard-vendedor'
        else: target_path = '/login'
        return target_path, False, no_update, True
    else:
        return no_update, True, error_message, False