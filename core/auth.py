# core/auth.py
from flask_login import UserMixin
from core.db import get_db_connection, release_db_connection
from core.password import check_password
from psycopg2.extras import DictCursor

class User(UserMixin):
    """Clase de Usuario para Flask-Login."""
    def __init__(self, dni, nombre, email, rol, zona=None): # <-- Añadir rol al constructor
        self.id = dni
        self.dni = dni
        self.nombre = nombre
        self.email = email
        self.rol = rol # <-- Guardar el rol
        self.zona = zona

    @staticmethod
    def get(user_id, pool):
        """Carga un usuario desde la DB por su ID (DNI), incluyendo el rol."""
        conn = None
        try:
            conn = pool.getconn()
            with conn.cursor(cursor_factory=DictCursor) as cur:
                # --- OBTENER ROL ---
                cur.execute("SELECT dni, nombre, email, rol, zona FROM users WHERE dni = %s", (user_id,))
                # ------------------
                user_data = cur.fetchone()
                if user_data:
                    return User(
                        dni=user_data['dni'],
                        nombre=user_data['nombre'],
                        email=user_data['email'],
                        rol=user_data['rol'], # <-- Pasar rol
                        zona=user_data['zona']
                    )
            return None
        except Exception as e:
            print(f"Error en User.get: {e}")
            return None
        finally:
            if conn:
                pool.putconn(conn)

    @staticmethod
    def authenticate(email, password, pool):
        """Autentica un usuario, incluyendo el rol."""
        conn = None
        try:
            conn = pool.getconn()
            with conn.cursor(cursor_factory=DictCursor) as cur:
                # --- OBTENER ROL ---
                cur.execute("SELECT dni, nombre, email, password_hash, rol, zona FROM users WHERE email = %s", (email,))
                # ------------------
                user_data = cur.fetchone()
                if not user_data: return None
                
                if check_password(password, user_data['password_hash']):
                    return User(
                        dni=user_data['dni'],
                        nombre=user_data['nombre'],
                        email=user_data['email'],
                        rol=user_data['rol'], # <-- Pasar rol
                        zona=user_data['zona']
                    )
            return None
        except Exception as e:
            print(f"Error en User.authenticate: {e}")
            return None
        finally:
            if conn:
                pool.putconn(conn)