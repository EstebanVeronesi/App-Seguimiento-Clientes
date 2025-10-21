# core/db.py
import os
import psycopg2
from psycopg2.extras import DictCursor # <-- Importante para que devuelva diccionarios
from psycopg2.pool import ThreadedConnectionPool # <-- El pool de V2
from dotenv import load_dotenv

load_dotenv()

# Variable global para el pool
db_pool = None

def init_db_pool():
    """Inicializa el pool de conexiones (usando psycopg2)."""
    global db_pool
    if db_pool is None:
        # El formato de conn_info es un string de 'key=value'
        conn_info = f"dbname='{os.getenv('DB_DATABASE')}' \
                     user='{os.getenv('DB_USER')}' \
                     password='{os.getenv('DB_PASSWORD')}' \
                     host='{os.getenv('DB_HOST')}' \
                     port='{os.getenv('DB_PORT')}'"
        try:
            # Usamos ThreadedConnectionPool
            db_pool = ThreadedConnectionPool(
                minconn=2,
                maxconn=10,
                dsn=conn_info
            )
            
            # Prueba de conexión
            conn = db_pool.getconn()
            # ¡Importante! Usamos DictCursor aquí para que devuelva dicts
            cur = conn.cursor(cursor_factory=DictCursor) 
            cur.execute("SELECT NOW()")
            print("Pool de conexiones (psycopg2) inicializado con éxito.")
            cur.close()
            db_pool.putconn(conn)
            
        except Exception as e:
            print(f"Error fatal al inicializar el pool de (psycopg2): {e}")
            db_pool = None
            
    return db_pool

def get_db_connection():
    """Obtiene una conexión del pool (psycopg2)."""
    global db_pool
    if db_pool is None:
        init_db_pool()
    
    if db_pool:
        # Esto obtiene una conexión del pool
        conn = db_pool.getconn()
        return conn
    else:
        raise Exception("El pool de la base de datos no está disponible.")

def release_db_connection(conn):
    """Devuelve una conexión al pool (psycopg2)."""
    if db_pool:
        # Esto devuelve la conexión al pool
        db_pool.putconn(conn)