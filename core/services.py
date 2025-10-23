# core/services.py
import pandas as pd
import requests
from requests.auth import HTTPBasicAuth
import os
import json
import psycopg2
from core.db import get_db_connection, release_db_connection
from core.repository import CrmRepository, UserRepository
from psycopg2.extras import DictCursor
import traceback
from datetime import datetime as dt, timedelta
from flask_login import current_user
# Asegúrate que el import relativo funcione según tu estructura
from . import google_auth

# --- ERP Service ---
class ErpService:
    @staticmethod
    def fetch_clientes_from_erp(filtros=None):
        """ Obtiene clientes del ERP, devuelve lista vacía en error. """
        url = os.getenv('ERP_API_URL'); user = os.getenv('ERP_API_USER'); pwd = os.getenv('ERP_API_PASSWORD')
        if not url or not user or not pwd: print("[ErpService] Error: Faltan variables de entorno ERP."); return []
        try:
            response = requests.post( url, json={"params": {"filtros": filtros or {}}}, auth=HTTPBasicAuth(user, pwd), timeout=45 )
            if response.status_code == 401: print("[ErpService] Error 401: Autenticación fallida."); return []
            response.raise_for_status()
            try: data = response.json()
            except json.JSONDecodeError: print(f"[ErpService] Error: Respuesta ERP no JSON. Resp:\n{response.text[:500]}..."); return []
            clientes = None;
            if isinstance(data, dict): clientes = data.get('result') or data.get('clientes')
            elif isinstance(data, list): clientes = data
            if isinstance(clientes, list):
                 clientes_mapeados = []
                 for c in clientes:
                     if isinstance(c, dict): clientes_mapeados.append({ **c, 'documento': c.get('numero_documento') or c.get('documento'), 'celular': c.get('mobile'), 'telefono': c.get('phone') })
                 return clientes_mapeados
            else: print(f"[ErpService] Advertencia: Respuesta JSON ERP sin lista. Resp: {data}"); return []
        except requests.exceptions.Timeout: print(f"[ErpService] Error: Timeout ERP en {url}."); return []
        except requests.exceptions.ConnectionError: print(f"[ErpService] Error: No se pudo conectar a ERP en {url}."); return []
        except requests.exceptions.RequestException as e: print(f"[ErpService] Error HTTP/Red ERP: {e}"); return []
        except Exception as e: print(f"[ErpService] Error inesperado ERP: {e}"); return []


# --- CRM Service (ACTUALIZADO - Formato Fecha dd-mm HH:MM) ---
class CrmService:

    @staticmethod
    def get_dashboard(filters: dict):
        """
        Obtiene datos para el dashboard.
        MODIFICADO: Formatea fecha_interaccion como dd-mm HH:MM.
        """
        conn = None
        empty_dashboard = { 'kpis': {'totalInteracciones': 0, 'tasaContacto': '0%', 'tasaCierreVenta': '0%', 'totalKgVendidos': 'N/A'}, 'graficos': {'motivosNoVenta': []}, 'ultimasInteracciones': [] }
        try:
            raw_data = CrmRepository.get_dashboard_data(filters)
            if not raw_data: return empty_dashboard

            dashboard_columns = ['id','fecha_interaccion','tipo_interaccion','llamada_concretada','respuesta_cliente','fecha_prox_seguimiento','venta_cerrada','motivo_no_venta','ofrecio_otros_precios','cliente_conoce_catalogo','le_llego_bien_pedido','comentarios_venta','cliente_informo_pago','reviso_cta_cte','comentarios_cobranza','fk_vendedor_dni','vendedor_nombre','vendedor_zona','fk_cliente_cuit','cliente_razon_social','cliente_zona']
            df = pd.DataFrame(raw_data, columns=dashboard_columns)

            expected_cols = {'llamada_concretada': (bool, False),'venta_cerrada': (bool, False),'tipo_interaccion': (str, 'Desconocido'),'motivo_no_venta': (str, None),'vendedor_nombre': (str, 'Desconocido'),'cliente_razon_social': (str, 'Desconocido'),'fecha_interaccion': ('datetime', pd.NaT),'fecha_prox_seguimiento': ('datetime', pd.NaT),'respuesta_cliente': (str, ''),'comentarios_venta': (str, '')}
            for col, (dtype, default) in expected_cols.items():
                if col not in df.columns: df[col] = default
                else:
                    if dtype == bool: df[col] = df[col].apply(lambda x: bool(x) if pd.notna(x) else False)
                    elif dtype == str: fill_value = default if default is not None else ''; df[col] = df[col].fillna(fill_value).astype(str)
                    elif dtype == 'datetime': df[col] = pd.to_datetime(df[col], errors='coerce')

            total_interacciones = len(df); tasa_contacto = "N/A"
            if not df.empty:
                if 'llamada_concretada' in df.columns and df['llamada_concretada'].notna().any():
                    tasa_contacto_val = df['llamada_concretada'].mean() * 100
                    tasa_contacto = f"{tasa_contacto_val:.0f}%" if pd.notna(tasa_contacto_val) else "0%"
                else: tasa_contacto = "0%"
            tasa_cierre = "0%"
            if not df.empty and 'venta_cerrada' in df.columns and df['venta_cerrada'].notna().any():
                tasa_cierre_val = df['venta_cerrada'].mean() * 100
                tasa_cierre = f"{tasa_cierre_val:.0f}%" if pd.notna(tasa_cierre_val) else "0%"
            kpis = { 'totalInteracciones': total_interacciones, 'tasaContacto': tasa_contacto, 'tasaCierreVenta': tasa_cierre, 'totalKgVendidos': 'N/A' }

            motivos_agg = pd.DataFrame(columns=['label', 'value'])
            if 'venta_cerrada' in df.columns and 'motivo_no_venta' in df.columns:
                 motivos_df = df[ (df['venta_cerrada'] == False) & (df['motivo_no_venta'].notna()) & (df['motivo_no_venta'] != '') & (df['motivo_no_venta'] != 'Desconocido') ]
                 if not motivos_df.empty:
                     motivos_df['motivo_no_venta_agg'] = motivos_df['motivo_no_venta'].fillna('Sin especificar')
                     motivos_agg = motivos_df.groupby('motivo_no_venta_agg').size().reset_index(name='value').rename(columns={'motivo_no_venta_agg': 'label'}).sort_values(by='value', ascending=False)

            # --- MODIFICACIÓN: Formatear fecha_interaccion como dd-mm HH:MM ---
            df['fecha_interaccion_str'] = df['fecha_interaccion'].dt.strftime('%d-%m %H:%M').where(df['fecha_interaccion'].notna(), 'N/A')
            # -----------------------------------------------------------------
            df['comentarios_display'] = df['respuesta_cliente'].astype(str).fillna('') + "\n" + df['comentarios_venta'].astype(str).fillna('')
            df['comentarios_display'] = df['comentarios_display'].str.strip().replace('\n\n', '\n').replace('\n', '<br>', regex=False)
            df['venta_cerrada_display'] = df['venta_cerrada'].apply(lambda x: 'Sí' if x else 'No')

            columnas_tabla_final = {'fecha_interaccion_str': 'fecha_interaccion','tipo_interaccion': 'tipo_interaccion','vendedor_nombre': 'vendedor_nombre','cliente_razon_social': 'cliente_razon_social','venta_cerrada_display': 'venta_cerrada','comentarios_display': 'comentarios_venta'}
            columnas_existentes_orig = [orig for orig in columnas_tabla_final.keys() if orig in df.columns]
            df_final = df[columnas_existentes_orig].rename(columns=columnas_tabla_final).fillna('')
            ultimas = df_final.head(50).to_dict('records')

            return { 'kpis': kpis, 'graficos': { 'motivosNoVenta': motivos_agg.to_dict('records') }, 'ultimasInteracciones': ultimas }

        except Exception as e: print(f"[CrmService] Error crítico al generar datos del dashboard: {e}"); traceback.print_exc(); return empty_dashboard
        finally: pass


    @staticmethod
    def get_clientes_dropdown():
        try: result = CrmRepository.get_clientes_para_dropdown(); return result if isinstance(result, list) else []
        except Exception as e: print(f"[CrmService] Error obteniendo clientes dropdown: {e}"); return []

    @staticmethod
    def registrar_interaccion(input_data_from_callback: dict, vendedor_dni: str):
        # ... (lógica sin cambios) ...
        cuit = input_data_from_callback.get('clienteCuit'); razon_social = input_data_from_callback.get('clienteRazonSocial') or ""
        interaccion_ok = input_data_from_callback.get('llamadaConcretada', False); venta_cerrada = input_data_from_callback.get('ventaCerrada', False)
        motivo_no_venta = input_data_from_callback.get('motivoNoVenta'); respuesta_cliente = input_data_from_callback.get('respuestaCliente') or ""
        com_venta = input_data_from_callback.get('comentariosVenta') or ""; fecha_prox_dt = input_data_from_callback.get('fechaProxSeguimiento')
        if not cuit or cuit <= 0: raise ValueError("El CUIT del cliente es inválido.")
        if not razon_social.strip(): raise ValueError("La Razón Social del cliente es obligatoria.")
        if interaccion_ok and not venta_cerrada and not motivo_no_venta and not respuesta_cliente.strip() and not com_venta.strip(): raise ValueError("Si la interacción se concretó pero no se cerró la venta, debe indicar un motivo o agregar un comentario.")
        input_data_repo = {'clienteCuit': cuit, 'clienteRazonSocial': razon_social,'tipoInteraccion': input_data_from_callback.get('tipoInteraccion'),'llamadaConcretada': bool(interaccion_ok),'respuestaCliente': respuesta_cliente or None,'fechaProxSeguimiento': fecha_prox_dt,'ventaCerrada': bool(venta_cerrada) if interaccion_ok else False,'motivoNoVenta': motivo_no_venta if interaccion_ok and not venta_cerrada else None,'ofrecioOtrosPrecios': bool(input_data_from_callback.get('ofrecioOtrosPrecios', False)) if interaccion_ok and not venta_cerrada else False,'clienteConoceCatalogo': bool(input_data_from_callback.get('clienteConoceCatalogo', False)) if interaccion_ok else False,'leLlegoBienPedido': bool(input_data_from_callback.get('leLlegoBienPedido', False)) if interaccion_ok else False,'comentariosVenta': com_venta or None if interaccion_ok else None,'clienteInformoPago': bool(input_data_from_callback.get('clienteInformoPago', False)) if interaccion_ok else False,'revisoCtaCte': bool(input_data_from_callback.get('revisoCtaCte', False)) if interaccion_ok else False,'comentariosCobranza': input_data_from_callback.get('comentariosCobranza') or None if interaccion_ok else None}
        conn = None; nueva_interaccion = None
        try:
            conn = get_db_connection(); conn.autocommit = False
            CrmRepository.find_or_create_cliente(conn, cuit, razon_social)
            nueva_interaccion = CrmRepository.create_interaccion(conn, input_data_repo, vendedor_dni)
            conn.commit(); print("Interacción guardada en base de datos.")
            if nueva_interaccion and fecha_prox_dt: # Quitada condición interaccion_ok
                print(f"Intentando crear evento de Google Calendar para seguimiento en {fecha_prox_dt}...")
                try:
                    creds_json = google_auth.load_google_credentials(vendedor_dni)
                    if creds_json:
                        service = google_auth.build_calendar_service(creds_json)
                        if service:
                            event_summary = f"Seguimiento Cliente: {razon_social}"; user_nombre = current_user.nombre if current_user and hasattr(current_user, 'nombre') else 'Usuario desconocido'
                            desc_prefix = "Próximo contacto agendado" if interaccion_ok else "Intentar contactar nuevamente" # Descripción condicional
                            event_description = f"{desc_prefix} con {razon_social} ({cuit}).\nRegistrado por: {user_nombre}\n---\nÚltima respuesta/obs: {respuesta_cliente}"
                            start_time = fecha_prox_dt.isoformat(); end_time = (fecha_prox_dt + timedelta(minutes=30)).isoformat()
                            event_body = {'summary': event_summary,'description': event_description,'start': {'dateTime': start_time, 'timeZone': 'America/Argentina/Buenos_Aires'},'end': {'dateTime': end_time, 'timeZone': 'America/Argentina/Buenos_Aires'},'reminders': {'useDefault': False, 'overrides': [{'method': 'popup', 'minutes': 15}]}}
                            google_auth.create_calendar_event(service, event_body)
                        else: print(f"WARN: No se pudo construir el servicio de Google Calendar para {vendedor_dni}.")
                    else: print(f"INFO: Usuario {vendedor_dni} no tiene credenciales de Google Calendar conectadas.")
                except Exception as cal_error: print(f"Error al intentar crear evento de Google Calendar para {vendedor_dni}: {cal_error}"); traceback.print_exc()
            else: print("DEBUG CrmService.registrar_interaccion - Condiciones no cumplidas para crear evento (No hay fecha o fallo guardado DB).")
            return nueva_interaccion
        except (Exception, psycopg2.DatabaseError) as error:
             if conn: conn.rollback(); print(f"[CrmService] Error DB al registrar interacción: {error}"); raise psycopg2.DatabaseError("Error al guardar en la base de datos.") from error
        finally:
             if conn: conn.autocommit = True; release_db_connection(conn)

    @staticmethod
    def get_vendedores_dropdown():
        # ... (sin cambios) ...
        conn = None;
        try: conn = get_db_connection(); return UserRepository.get_vendedores(conn)
        except Exception as e: print(f"[CrmService] Error obteniendo vendedores dropdown: {e}"); return []
        finally:
            if conn: release_db_connection(conn)

    @staticmethod
    def sincronizar_clientes_erp(clientes_erp: list[dict]):
        # ... (sin cambios) ...
        try: resultado = CrmRepository.sincronizar_clientes(clientes_erp); return resultado
        except (Exception, psycopg2.DatabaseError) as error: print(f"[CrmService] Error al orquestar sincronización ERP: {error}"); raise error

    @staticmethod
    def get_datos_vendedor(vendedor_dni: str):
        """
        Obtiene los datos específicos para el dashboard del vendedor.
        MODIFICADO: Formatea fecha/hora con dd-mm HH:MM.
        """
        conn = None; empty_vendedor_data = { "kpis": {}, "ultimas_interacciones": [], "proximos_seguimientos": [] }
        try:
            conn = get_db_connection(); filtros_vendedor = {'vendedorDni': vendedor_dni}
            datos_generales = CrmService.get_dashboard(filtros_vendedor) # Ya formatea fecha_interaccion dd-mm HH:MM
            proximos_seguimientos_raw = CrmRepository.get_proximos_seguimientos(conn, vendedor_dni)
            proximos_seguimientos = []
            if proximos_seguimientos_raw:
                for seg in proximos_seguimientos_raw:
                    fecha_formateada = 'N/A'; fecha_obj = seg.get('fecha_prox_seguimiento')
                    if fecha_obj and isinstance(fecha_obj, dt):
                        try:
                            # --- MODIFICACIÓN: Formato dd-mm HH:MM ---
                            fecha_formateada = fecha_obj.strftime('%d-%m %H:%M')
                            # ----------------------------------------
                        except ValueError: pass
                    proximos_seguimientos.append({'fecha_prox_seguimiento': fecha_formateada,'cliente_razon_social': str(seg.get('cliente_razon_social', 'N/A')),'respuesta_cliente': str(seg.get('respuesta_cliente', ''))})
            datos_completos = {"kpis": datos_generales.get('kpis', {}),"ultimas_interacciones": datos_generales.get('ultimasInteracciones', []),"proximos_seguimientos": proximos_seguimientos}
            return datos_completos
        except Exception as e: print(f"Error obteniendo datos para vendedor {vendedor_dni}: {e}"); traceback.print_exc(); return empty_vendedor_data
        finally:
            if conn: release_db_connection(conn)

# --- UserRepository (sin cambios) ---
class UserRepository:
    @staticmethod
    def create(dni: str, nombre: str, email: str, hashed_password: str, rol: str, zona: str = None):
        # ... (sin cambios) ...
        conn = None
        try:
            conn = get_db_connection();
            with conn.cursor(cursor_factory=DictCursor) as cur:
                cur.execute("SELECT 1 FROM users WHERE email = %s OR dni = %s", (email, dni));
                if cur.fetchone(): raise ValueError('Email o DNI ya existen')
                cur.execute( """ INSERT INTO users (dni, nombre, email, password_hash, zona, rol) VALUES (%s, %s, %s, %s, %s, %s) """, (dni, nombre, email, hashed_password, zona, rol) );
                conn.commit(); return {"email": email}
        except (Exception, psycopg2.DatabaseError) as error:
            if conn: conn.rollback(); raise error
        finally:
            if conn: release_db_connection(conn)

    @staticmethod
    def get_vendedores(conn):
        # ... (sin cambios) ...
        try:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                query = "SELECT dni, nombre FROM users WHERE rol = 'vendedor' ORDER BY nombre ASC;"; cur.execute(query);
                result = cur.fetchall(); return result if result else []
        except (Exception, psycopg2.DatabaseError) as error: print(f"Error al obtener lista de vendedores: {error}"); raise error