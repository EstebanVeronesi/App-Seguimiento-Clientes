# pages/logout.py
import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
from flask_login import logout_user
import flask

dash.register_page(__name__, path='/logout', title="Cerrar Sesión", name="Cerrar Sesión")

def layout():
    # Usamos el request de Flask para asegurarnos de que esto solo
    # se ejecute una vez cuando se carga la página.
    if flask.request.method == 'GET':
        logout_user()

    return dbc.Container([
        dbc.Row(dbc.Col(
            dbc.Card([
                dbc.CardBody([
                    html.H4("Has cerrado sesión"),
                    html.P("Serás redirigido a la página de inicio."),
                    # Redirige al login y refresca la página
                    dcc.Location(pathname="/login", id="redirect-to-login-after-logout", refresh=True)
                ])
            ]),
            width=10, md=6, lg=4
        ), justify="center", className="mt-5")
    ], fluid=True)