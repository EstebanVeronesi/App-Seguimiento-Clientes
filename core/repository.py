# core/repository.py
import psycopg2
from psycopg2.extras import DictCursor
from core.db import db_pool, get_db_connection, release_db_connection
from core.password import hash_password

# =============================================================================
# REPOSITORIO DE USUARIOS
# =============================================================================
class UserRepository:
    @staticmethod
    def create(dni: str, nombre: str, email: str, hashed_password: str, rol: str, zona: str = None):
        conn = None
        try:
            conn = get_db_connection()
            with conn.cursor(cursor_factory=DictCursor) as cur:
                cur.execute("SELECT 1 FROM users WHERE email = %s OR dni = %s", (email, dni))
                if cur.fetchone(): raise ValueError('Email o DNI ya existen')
                cur.execute(
                    """INSERT INTO users (dni, nombre, email, password_hash, zona, rol) VALUES (%s, %s, %s, %s, %s, %s)""",
                    (dni, nombre, email, hashed_password, zona, rol)
                )
                conn.commit()
                return {"email": email}
        except (Exception, psycopg2.DatabaseError) as error:
            if conn: conn.rollback()
            raise error
        finally:
            if conn: release_db_connection(conn)

    @staticmethod
    def get_vendedores(conn):
        try:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                cur.execute("SELECT dni, nombre FROM users WHERE rol = 'vendedor' ORDER BY nombre ASC;")
                result = cur.fetchall()
                return result if result else []
        except (Exception, psycopg2.DatabaseError) as error:
             print(f"Error al obtener lista de vendedores: {error}")
             raise error

# =============================================================================
# REPOSITORIO CRM
# =============================================================================
class CrmRepository:

    @staticmethod
    def create_interaccion(conn, input_data: dict, vendedor_dni: str):
        with conn.cursor(cursor_factory=DictCursor) as cur:
            interaccion_query = """
              INSERT INTO interacciones_comerciales (
                fk_vendedor_dni, fk_cliente_cuit, tipo_interaccion, llamada_concretada,
                respuesta_cliente, fecha_prox_seguimiento, venta_cerrada,
                motivo_no_venta, ofrecio_otros_precios, cliente_conoce_catalogo,
                le_llego_bien_pedido, comentarios_venta, cliente_informo_pago,
                reviso_cta_cte, comentarios_cobranza
              ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
              ) RETURNING *;
            """
            params_list = [
                vendedor_dni, input_data.get('clienteCuit'), input_data.get('tipoInteraccion') or None,
                bool(input_data.get('llamadaConcretada', False)), input_data.get('respuestaCliente') or None,
                input_data.get('fechaProxSeguimiento') or None, bool(input_data.get('ventaCerrada', False)),
                input_data.get('motivoNoVenta') or None, bool(input_data.get('ofrecioOtrosPrecios', False)),
                bool(input_data.get('clienteConoceCatalogo', False)), bool(input_data.get('leLlegoBienPedido', False)),
                input_data.get('comentariosVenta') or None, bool(input_data.get('clienteInformoPago', False)),
                bool(input_data.get('revisoCtaCte', False)), input_data.get('comentariosCobranza') or None
            ]
            params = tuple(params_list)
            if len(params) != 15: raise ValueError(f"Fallo en construcción de params, {len(params)} != 15")
            try:
                cur.execute(interaccion_query, params)
                return cur.fetchone()
            except Exception as db_error:
                 print(f"!!! Error directo de DB en cur.execute: {db_error}")
                 import traceback; traceback.print_exc()
                 raise

    @staticmethod
    def get_dashboard_data(filters: dict):
        """
        Obtiene los datos crudos para el dashboard (sin kg_vendidos).
        Maneja su propia conexión. Filtro ZONA ELIMINADO.
        """
        conn = None
        try:
            conn = get_db_connection()
            with conn.cursor(cursor_factory=DictCursor) as cur:
                query = """
                  SELECT
                    i.id, i.fecha_interaccion, i.tipo_interaccion, i.llamada_concretada, i.respuesta_cliente,
                    i.fecha_prox_seguimiento, i.venta_cerrada,
                    i.motivo_no_venta, i.ofrecio_otros_precios, i.cliente_conoce_catalogo, i.le_llego_bien_pedido,
                    i.comentarios_venta, i.cliente_informo_pago, i.reviso_cta_cte, i.comentarios_cobranza,
                    i.fk_vendedor_dni,
                    u.nombre AS vendedor_nombre, u.zona AS vendedor_zona,
                    i.fk_cliente_cuit,
                    c.razon_social AS cliente_razon_social, c.zona AS cliente_zona
                  FROM interacciones_comerciales i
                  JOIN users u ON i.fk_vendedor_dni = u.dni
                  JOIN cliente c ON i.fk_cliente_cuit = c.cuit
                  WHERE 1=1
                """
                params = []
                if filters.get('vendedorDni'): query += " AND i.fk_vendedor_dni = %s"; params.append(filters['vendedorDni'])
                if filters.get('clienteCuit'): query += " AND i.fk_cliente_cuit = %s"; params.append(filters['clienteCuit'])
                if filters.get('fechaDesde'): query += " AND i.fecha_interaccion >= %s"; params.append(filters['fechaDesde'])
                if filters.get('fechaHasta'): query += " AND i.fecha_interaccion < (%s::date + interval '1 day')"; params.append(filters['fechaHasta'])
                
                # --- BLOQUE DE FILTRO ZONA ELIMINADO ---
                # if filters.get('zona'):
                #     zona_param = f"%{filters['zona']}%"
                #     query += " AND (u.zona ILIKE %s OR c.zona ILIKE %s)"
                #     params.extend([zona_param, zona_param])
                # ----------------------------------------

                query += " ORDER BY i.fecha_interaccion DESC"
                
                # print(f"DEBUG SQL Query: {cur.mogrify(query, tuple(params))}") # Descomentar si quieres ver la SQL
                
                cur.execute(query, tuple(params))
                result = cur.fetchall()

                # print(f"DEBUG: Datos crudos desde get_dashboard_data: {len(result) if result else 0} filas") # Debug opcional

                return result
        except (Exception, psycopg2.DatabaseError) as error:
            print(f"Error al obtener datos del dashboard: {error}")
            raise error
        finally:
            if conn: release_db_connection(conn)

    @staticmethod
    def get_clientes_para_dropdown():
        """ Obtiene lista de clientes para dropdowns. """
        conn = None
        try:
            conn = get_db_connection()
            with conn.cursor(cursor_factory=DictCursor) as cur:
                query = "SELECT cuit, razon_social FROM cliente ORDER BY razon_social ASC;"
                cur.execute(query)
                result = cur.fetchall()
                # print(f"DEBUG (Repo): get_clientes_para_dropdown encontró {len(result) if result else 0} clientes.")
                return result if result else []
        except (Exception, psycopg2.DatabaseError) as error:
             print(f"Error Repo get_clientes_para_dropdown: {error}")
             return []
        finally:
             if conn: release_db_connection(conn)

    @staticmethod
    def sincronizar_clientes(clientes_erp: list[dict]):
        # ... (código existente sin cambios) ...
        pass

    @staticmethod
    def find_or_create_cliente(conn, cuit: int, razon_social: str):
        # ... (código existente sin cambios) ...
        pass

    @staticmethod
    def get_proximos_seguimientos(conn, vendedor_dni: str):
        """ Obtiene próximos seguimientos para un vendedor. """
        try:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                query = """
                    SELECT
                        i.fecha_prox_seguimiento, c.razon_social AS cliente_razon_social,
                        c.cuit AS cliente_cuit, i.respuesta_cliente
                    FROM interacciones_comerciales i
                    JOIN cliente c ON i.fk_cliente_cuit = c.cuit
                    WHERE i.fk_vendedor_dni = %s
                      AND i.fecha_prox_seguimiento >= CURRENT_DATE
                    ORDER BY i.fecha_prox_seguimiento ASC;
                """
                cur.execute(query, (vendedor_dni,))
                result = cur.fetchall()
                return result if result else []
        except (Exception, psycopg2.DatabaseError) as error:
            print(f"Error obteniendo próximos seguimientos para DNI {vendedor_dni}: {error}")
            raise error