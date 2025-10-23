# pages/authorize_google.py
import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
from flask_login import current_user
from core import google_auth # Importar nuestro módulo

dash.register_page(__name__, path='/authorize-google', title="Autorizar Google Calendar")

# Este layout es simple, solo muestra un botón para iniciar el flujo
# o un mensaje si ya está autorizado (o si hay error).
def layout():
    if not current_user.is_authenticated:
        return dcc.Location(pathname="/login", id="redirect-login-auth-google")

    # Verificar si ya tiene credenciales (simplificado, podríamos chequear validez)
    creds_json = google_auth.load_google_credentials(current_user.dni)
    authorization_url = None
    error_message = None

    if not creds_json:
        flow = google_auth.get_google_auth_flow()
        if flow:
            # Generar la URL a la que el usuario debe ir
            authorization_url, state = flow.authorization_url(
                access_type='offline', # Necesario para obtener refresh_token
                prompt='consent'       # Fuerza a mostrar la pantalla de consentimiento
            )
            # Guardar el 'state' en la sesión de Flask para verificarlo en el callback
            # Necesitas importar 'session' de Flask en app.py si no lo has hecho
            from flask import session
            session['google_oauth_state'] = state
        else:
            error_message = "Error al configurar la autorización con Google. Verifica el archivo client_secret.json."

    return dbc.Container([
        html.H2("Conectar con Google Calendar"),
        html.Hr(),
        dbc.Row(dbc.Col(
            dbc.Card(dbc.CardBody([
                html.P("Para crear eventos automáticamente en tu calendario, necesitas autorizar esta aplicación."),
                html.Br(),
                # Mostrar botón o mensaje
                dbc.Button("Autorizar Acceso a Google Calendar", href=authorization_url, external_link=True, color="primary") if authorization_url else None,
                dbc.Alert("Ya has autorizado la aplicación.", color="success") if creds_json else None,
                dbc.Alert(f"Error: {error_message}", color="danger") if error_message else None,
            ]))
        , width=10, md=8, lg=6), justify="center", className="mt-4")
    ])