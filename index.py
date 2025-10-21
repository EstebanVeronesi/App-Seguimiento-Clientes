# index.py
from app import app, server

# Este es el punto de entrada para Gunicorn/Waitress en producción
# o para desarrollo local.
if __name__ == "__main__":
    # --- LÍNEA CORREGIDA ---
    app.run(debug=True, host="0.0.0.0", port=3000)