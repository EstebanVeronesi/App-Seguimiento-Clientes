# pages/login.py
import dash
from dash import dcc, html, callback, Input, Output, State, no_update, ctx
import dash_bootstrap_components as dbc
import flask
# Asegúrate de importar current_user también si aún no lo tienes
from flask_login import login_user, current_user
from core.auth import User

dash.register_page(__name__, path='/login', title="Login")

# Layout simple de login (sin cambios)
layout = dbc.Container([
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
    ), justify="center", className="mt-5")
])

# Callback para ocultar alerta (sin cambios)
@callback(
    Output('login-alert', 'is_open', allow_duplicate=True),
    Input('login-email', 'value'),
    Input('login-password', 'value'),
    prevent_initial_call=True
)
def hide_alert_on_input(email, password):
    return False

# --- CALLBACK DE LOGIN CORREGIDO CON REDIRECCIÓN POR ROL ---
@callback(
    Output('url', 'pathname'), # Output para la ruta
    Output('login-alert', 'is_open'),
    Output('url', 'refresh'), # Output para el refresh
    Input('login-button', 'n_clicks'),
    State('login-email', 'value'),
    State('login-password', 'value'),
    prevent_initial_call=True
)
def handle_login(n_clicks, email, password):
    # No hacer nada si no hay clicks (previene ejecución inicial)
    # Aunque prevent_initial_call=True lo hace, es una doble seguridad
    triggered_id = ctx.triggered_id
    if not triggered_id or triggered_id == '.':
         return no_update, False, False

    # Validar campos vacíos
    if not email or not password:
        return no_update, True, False # Mostrar alerta, no refrescar

    pool = flask.current_app.config["DB_POOL"]
    user = User.authenticate(email, password, pool)

    if user:
        login_user(user, remember=True) # Iniciar sesión
        # --- REDIRECCIÓN BASADA EN ROL ---
        if user.rol == 'gerente':
            target_path = '/dashboard-gerencia'
            print(f"DEBUG: Login Gerente OK. Redirigiendo a {target_path}...")
        elif user.rol == 'vendedor':
            target_path = '/dashboard-vendedor'
            print(f"DEBUG: Login Vendedor OK. Redirigiendo a {target_path}...")
        else:
            # Rol desconocido o no asignado, redirigir a login por seguridad
            print(f"WARN: Rol desconocido '{user.rol}' para {user.email}. Redirigiendo a /login.")
            target_path = '/login' # O a una página de error/home si prefieres

        # Devolver ruta, ocultar alerta, FORZAR REFRESH
        return target_path, False, True
        # ----------------------------------
    else:
        # Error de autenticación
        print(f"DEBUG: Login FALLIDO para email {email}.")
        return no_update, True, False # Mostrar alerta, no refrescar