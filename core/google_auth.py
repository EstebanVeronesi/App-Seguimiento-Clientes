# core/google_auth.py
import os
import json
from flask import current_app, url_for, request, session, redirect
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from flask_login import current_user

# --- Configuración ---
# El archivo descargado de Google Cloud Console
CLIENT_SECRETS_FILE = "client_secret.json"
# Los permisos que solicitará tu aplicación
SCOPES = ['https://www.googleapis.com/auth/calendar.events']
# La ruta DENTRO de tu aplicación donde Google redirigirá después de la autorización
# Debe coincidir EXACTAMENTE con una de las URIs de redirección en Google Cloud Console
REDIRECT_URI = 'http://localhost:3000/oauth2callback' # ¡Ajusta si es necesario!

# --- Funciones de Autenticación ---

def get_google_auth_flow():
    """Crea y configura el objeto Flow de OAuth."""
    try:
        flow = Flow.from_client_secrets_file(
            CLIENT_SECRETS_FILE,
            scopes=SCOPES,
            redirect_uri=REDIRECT_URI
        )
        return flow
    except FileNotFoundError:
        print(f"ERROR CRÍTICO: No se encontró el archivo '{CLIENT_SECRETS_FILE}'. Descárgalo de Google Cloud Console.")
        return None
    except Exception as e:
        print(f"Error al crear el flow de Google Auth: {e}")
        return None

def build_calendar_service(credentials_json_string):
    """Construye el servicio de Calendar API a partir de credenciales guardadas."""
    if not credentials_json_string:
        return None
    try:
        creds_data = json.loads(credentials_json_string)
        # Asegurarse de que los campos necesarios estén presentes
        if not all(k in creds_data for k in ["token", "refresh_token", "client_id", "client_secret", "scopes"]):
             print("WARN: Faltan campos en las credenciales guardadas.")
             return None

        credentials = Credentials(**creds_data)

        # Refrescar si es necesario (la librería maneja esto si el refresh_token está presente)
        # No es necesario llamar a refresh() explícitamente aquí si se usa build()
        # if credentials.expired and credentials.refresh_token:
        #     credentials.refresh(Request()) # Request necesitaría importarse de google.auth.transport.requests

        service = build('calendar', 'v3', credentials=credentials)
        return service
    except json.JSONDecodeError:
        print("Error: No se pudo decodificar el JSON de credenciales de Google.")
        return None
    except Exception as e:
        print(f"Error construyendo el servicio de Calendar: {e}")
        return None

def save_google_credentials(dni, credentials):
    """Guarda las credenciales (como JSON) en la base de datos para el usuario."""
    pool = current_app.config.get("DB_POOL")
    conn = None
    if not pool:
        print("Error: No se pudo obtener el pool de DB para guardar credenciales.")
        return False
    try:
        # Convertir credenciales a formato serializable (diccionario -> JSON string)
        creds_data = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes
        }
        creds_json = json.dumps(creds_data)

        conn = pool.getconn()
        with conn.cursor() as cur:
            cur.execute("UPDATE users SET google_creds_json = %s WHERE dni = %s", (creds_json, dni))
            conn.commit()
            print(f"Credenciales de Google guardadas para usuario DNI {dni}")
            return True
    except Exception as e:
        if conn: conn.rollback()
        print(f"Error al guardar credenciales de Google para DNI {dni}: {e}")
        return False
    finally:
        if conn: pool.putconn(conn)

def load_google_credentials(dni):
    """Carga las credenciales (como string JSON) desde la base de datos."""
    pool = current_app.config.get("DB_POOL")
    conn = None
    if not pool:
        print("Error: No se pudo obtener el pool de DB para cargar credenciales.")
        return None
    try:
        conn = pool.getconn()
        with conn.cursor() as cur:
            cur.execute("SELECT google_creds_json FROM users WHERE dni = %s", (dni,))
            result = cur.fetchone()
            if result and result[0]:
                return result[0] # Devuelve el string JSON
            else:
                return None
    except Exception as e:
        print(f"Error al cargar credenciales de Google para DNI {dni}: {e}")
        return None
    finally:
        if conn: pool.putconn(conn)

# --- Funciones para interactuar con Calendar ---

def create_calendar_event(service, event_data):
    """Crea un evento usando el servicio de Calendar API."""
    try:
        event = service.events().insert(calendarId='primary', body=event_data).execute()
        print(f"Evento de Google Calendar creado: {event.get('htmlLink')}")
        return event
    except HttpError as error:
        print(f'Error al crear evento en Google Calendar: {error}')
        # Podrías querer levantar una excepción aquí para manejarla en el servicio
        raise error
    except Exception as e:
        print(f"Error inesperado al crear evento: {e}")
        raise e