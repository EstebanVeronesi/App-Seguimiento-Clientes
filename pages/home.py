# pages/home.py
import dash
from dash import dcc

# Registrar esta página como la raíz '/'
dash.register_page(__name__, path='/', title="Inicio")

# El layout simplemente redirige a la página de login
def layout():
    return dcc.Location(pathname="/login", id="redirect-to-login")