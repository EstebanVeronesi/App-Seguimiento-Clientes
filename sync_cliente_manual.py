# sync_clientes_manual.py
# --- PRINT INICIAL ---
print("DEBUG: Iniciando script sync_clientes_manual.py...")
# --------------------
import sys
import os
import psycopg2
from dotenv import load_dotenv

# --- PRINT ANTES DE SYS.PATH ---
print("DEBUG: Antes de sys.path.append...")
# -----------------------------
# Asegurarse de que Python encuentre los módulos en 'core'
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.append(script_dir)
# --- PRINT DESPUÉS DE SYS.PATH ---
print(f"DEBUG: Después de sys.path.append. sys.path ahora incluye: {script_dir}")
# -----------------------------

# --- PRINTS ANTES Y DESPUÉS DE CADA IMPORT ---
print("DEBUG: Intentando importar core.db...")
from core.db import init_db_pool, get_db_connection, release_db_connection
print("DEBUG: Éxito importando core.db.")
print("DEBUG: Intentando importar core.services...")
from core.services import ErpService
print("DEBUG: Éxito importando core.services.")
print("DEBUG: Intentando importar core.repository...")
from core.repository import CrmRepository
print("DEBUG: Éxito importando core.repository.")
# ---------------------------------------------

def run_sync():
    """Ejecuta el proceso completo de sincronización."""
    print("DEBUG: Entrando en la función run_sync()...")
    print("--- Iniciando Sincronización Manual de Clientes ---")
    load_dotenv()
    print("DEBUG: load_dotenv() ejecutado.")

    try:
        print("1/3: Inicializando pool de base de datos...")
        init_db_pool()
        print("   Pool inicializado.")

        print("2/3: Obteniendo clientes desde el ERP...")
        clientes_erp = ErpService.fetch_clientes_from_erp()
        print(f"   Se recibieron {len(clientes_erp)} clientes del ERP.")
        if not clientes_erp:
            print("   WARN: No se recibieron clientes válidos del ERP. Terminando.")
            return

        print("3/3: Sincronizando clientes en la base de datos local...")
        # --- VERIFICA ESTA LÍNEA ---
        # La llamada correcta NO debe pasar 'conn'
        resultado = CrmRepository.sincronizar_clientes(clientes_erp)
        # -------------------------

        print("\n--- ¡Sincronización Finalizada! ---")
        print(f"   Clientes recibidos: {len(clientes_erp)}")
        print(f"   Insertados nuevos:  {resultado.get('insertados', 0)}")
        print(f"   Actualizados:       {resultado.get('actualizados', 0)}")
        print(f"   Omitidos (error/inválido): {resultado.get('omitidos', 0)}")
        print("------------------------------------")

    except Exception as e:
        print("\n--- !!! ERROR DURANTE LA SINCRONIZACIÓN !!! ---")
        import traceback
        traceback.print_exc()
        print(f"   Detalle: {e}")
        print("-------------------------------------------------")
    finally:
        print("   Proceso de sincronización manual terminado.")

if __name__ == "__main__":
    print("DEBUG: Bloque __main__ alcanzado. Llamando a run_sync()...")
    run_sync()