# pages/02_interaccion.py
import dash
from datetime import datetime as dt, time as datetime_time, date as datetime_date
from dash import dcc, html, callback, Input, Output, State, no_update, ctx
import dash_bootstrap_components as dbc
from flask_login import current_user
import psycopg2
from core.services import CrmService
import traceback

dash.register_page(__name__, path='/nueva-interaccion', name="Nueva Interacción", title="Registrar Interacción")

# --- Helper create_yes_no_buttons (sin cambios) ---
def create_yes_no_buttons(base_id: str, label: str, default_value: bool = False):
    store_id = f"{base_id}-store"
    button_yes_id = f"{base_id}-yes"
    button_no_id = f"{base_id}-no"
    style_yes = {"outline": False, "color": "success"} if default_value else {"outline": True, "color": "success"}
    style_no = {"outline": False, "color": "danger"} if not default_value else {"outline": True, "color": "danger"}
    return dbc.Col([
        dbc.Label(label),
        html.Div([
            dbc.ButtonGroup([
                dbc.Button("Sí", id=button_yes_id, **style_yes, n_clicks=0),
                dbc.Button("No", id=button_no_id, **style_no, n_clicks=0)
            ]),
            dcc.Store(id=store_id, data=default_value)
        ])
    ], md=6, className="mb-3")


# --- Layout del Formulario (sin cambios) ---
def layout():
    if not current_user.is_authenticated:
        return dcc.Location(pathname="/login", id="redirect-login-interaccion-auth")
    allowed_roles = ['vendedor', 'gerente']
    if current_user.rol not in allowed_roles:
        print(f"DEBUG (Interaccion): Rol '{current_user.rol}' no autorizado.")
        return dcc.Location(pathname="/login", id="redirect-login-interaccion-role")

    initial_venta_cerrada = False
    hour_options = [{'label': f"{h:02d}", 'value': h} for h in range(24)]
    minute_options = [{'label': f"{m:02d}", 'value': m} for m in range(60)]

    return dbc.Container([
        html.H2("Registrar Nueva Interacción Comercial"), html.Hr(),
        dbc.Alert(id="interaccion-feedback-alert", color="info", is_open=False, duration=4000),
        dbc.Form([
            dbc.Row([ # Cliente
                dbc.Col([ dbc.Label("Cliente", html_for='interaccion-cliente-cuit'), dcc.Dropdown(id='interaccion-cliente-cuit', options=[], placeholder="Seleccione...", searchable=True, clearable=True) ], md=6, className="mb-3"),
                dcc.Store(id='interaccion-cliente-razon-social-store'),
            ]), html.Hr(),
            dbc.Row([ # Interacción
                dbc.Col([ dbc.Label("Tipo", html_for='interaccion-tipo'), dbc.Select(id='interaccion-tipo', options=[{'label': i, 'value': i} for i in ['Llamada', 'Visita', 'WhatsApp', 'Email']], value='Llamada') ], md=6, className="mb-3"),
                create_yes_no_buttons(base_id="interaccion-concretada", label="¿Interacción concretada?", default_value=False),
                dbc.Col([ dbc.Label("Respuesta / Observaciones", html_for='interaccion-respuesta'), dbc.Textarea(id='interaccion-respuesta', placeholder="Detalles...", rows=3) ], md=12, className="mb-3"),
                dbc.Col([
                    dbc.Label("Fecha Próx. Seguimiento", html_for='interaccion-fecha-prox-seguimiento'),
                    dcc.DatePickerSingle(id='interaccion-fecha-prox-seguimiento', min_date_allowed=datetime_date.today(), display_format='YYYY-MM-DD', date=None, className="mb-2")
                ], md=4),
                dbc.Col([
                    dbc.Label("Hora (24h)", html_for='interaccion-hora-prox-seguimiento'),
                    dbc.Select(id='interaccion-hora-prox-seguimiento', options=hour_options, value=8, placeholder="HH")
                ], md=2),
                 dbc.Col([
                    dbc.Label("Minutos", html_for='interaccion-minuto-prox-seguimiento'),
                    dbc.Select(id='interaccion-minuto-prox-seguimiento', options=minute_options, value=0, placeholder="MM")
                ], md=2),
            ]), html.Hr(),
            dbc.Collapse( id='collapse-gestion', children=[ # Collapse
                    html.H4("Gestión"),
                    dbc.Row([ # Venta
                         create_yes_no_buttons(base_id="interaccion-venta-cerrada", label="¿Venta Cerrada?", default_value=initial_venta_cerrada),
                         dbc.Col( dbc.Collapse(id='collapse-no-venta', children=[ dbc.Row([
                                     dbc.Col([ dbc.Label("Motivo No-Venta", html_for='interaccion-motivo-no-venta'), dbc.Select(id='interaccion-motivo-no-venta', options=[{'label': m, 'value': m} for m in ['Precio', 'Completo de mercadería', 'Otro']], placeholder="Seleccione...") ], md=6),
                                     create_yes_no_buttons(base_id="interaccion-ofrecio-precios", label="¿Ofreció Otros Precios?", default_value=False),
                                 ]) ], is_open = not initial_venta_cerrada ), md=12, className="mb-3" ),
                         create_yes_no_buttons(base_id="interaccion-conoce-catalogo", label="¿Conoce Catálogo?", default_value=False),
                         create_yes_no_buttons(base_id="interaccion-llego-bien-pedido", label="¿Llegó bien pedido?", default_value=True),
                         dbc.Col([ dbc.Label("Comentarios Adicionales Venta", html_for='interaccion-comentarios-venta'), dbc.Textarea(id='interaccion-comentarios-venta', placeholder="Notas adicionales...", rows=3) ], md=12, className="mb-3"),
                    ]), html.Hr(),
                    dbc.Row([ # Cobranza
                         create_yes_no_buttons(base_id="interaccion-informo-pago", label="¿Informó Pago?", default_value=False),
                         create_yes_no_buttons(base_id="interaccion-reviso-ctacte", label="¿Revisó Cta. Cte.?", default_value=False),
                         dbc.Col([ dbc.Label("Comentarios Cobranza", html_for='interaccion-comentarios-cobranza'), dbc.Textarea(id='interaccion-comentarios-cobranza', placeholder="Notas...", rows=3) ], md=12, className="mb-3"),
                    ]),
                ], is_open=False ),
            dbc.Button("Guardar Interacción", id='interaccion-btn-guardar', color="success", n_clicks=0, className="mt-3 w-100")
        ])
    ], fluid=True)


# --- CALLBACKS ---

@callback(
    Output('interaccion-cliente-cuit', 'options'),
    Input('url', 'pathname'),
    prevent_initial_call=False
)
def cargar_clientes_dropdown(pathname):
    if pathname == '/nueva-interaccion':
        try:
            clientes = CrmService.get_clientes_dropdown()
            if not isinstance(clientes, list): print("[Callback Carga Clientes] Advertencia..."); return []
            options = [{'label': f"{c.get('razon_social', 'N/A')} ({c.get('cuit', 'N/A')})", 'value': c.get('cuit')} for c in clientes if c.get('cuit')]
            return options
        except Exception as e: print(f"Error en callback cargando clientes: {e}"); return []
    return no_update

@callback(Output('interaccion-cliente-razon-social-store', 'data'), Input('interaccion-cliente-cuit', 'value'), State('interaccion-cliente-cuit', 'options'), prevent_initial_call=True)
def guardar_razon_social_seleccionada(selected_cuit, options):
    if not selected_cuit or not options: return None
    selected_option = next((opt for opt in options if opt['value'] == selected_cuit), None)
    if selected_option: label = selected_option['label']; razon_social = label.split(' (')[0]; return razon_social
    return None

def generate_yes_no_callback(base_id: str):
    store_id = f"{base_id}-store"; button_yes_id = f"{base_id}-yes"; button_no_id = f"{base_id}-no"
    @callback(
        Output(store_id, 'data'), Output(button_yes_id, 'outline'), Output(button_no_id, 'outline'),
        Input(button_yes_id, 'n_clicks'), Input(button_no_id, 'n_clicks'),
        State(store_id, 'data'), prevent_initial_call=True )
    def update_yes_no_state(n_yes, n_no, current_state):
        button_id = ctx.triggered_id; new_state = current_state
        if button_id == button_yes_id and not current_state: new_state = True
        elif button_id == button_no_id and current_state: new_state = False
        else: return no_update, no_update, no_update
        return new_state, not new_state, new_state
generate_yes_no_callback("interaccion-concretada")
generate_yes_no_callback("interaccion-venta-cerrada")
generate_yes_no_callback("interaccion-ofrecio-precios")
generate_yes_no_callback("interaccion-conoce-catalogo")
generate_yes_no_callback("interaccion-llego-bien-pedido")
generate_yes_no_callback("interaccion-informo-pago")
generate_yes_no_callback("interaccion-reviso-ctacte")

@callback( Output('collapse-gestion', 'is_open'), Input('interaccion-concretada-store', 'data') )
def toggle_collapse_gestion(interaccion_ok_data): return bool(interaccion_ok_data)

@callback( Output('collapse-no-venta', 'is_open'), Input('interaccion-venta-cerrada-store', 'data') )
def toggle_collapse_no_venta(venta_cerrada_data): return not bool(venta_cerrada_data)


# --- Callback para guardar (CORREGIDO: Simplificada lógica de limpieza) ---
@callback(
    Output('interaccion-feedback-alert', 'children'), Output('interaccion-feedback-alert', 'color'), Output('interaccion-feedback-alert', 'is_open'),
    # Resets
    Output('interaccion-respuesta', 'value', allow_duplicate=True), Output('interaccion-comentarios-venta', 'value', allow_duplicate=True),
    Output('interaccion-comentarios-cobranza', 'value', allow_duplicate=True), Output('interaccion-cliente-cuit', 'value', allow_duplicate=True),
    Output('interaccion-motivo-no-venta', 'value', allow_duplicate=True),
    Output('interaccion-fecha-prox-seguimiento', 'date', allow_duplicate=True),
    Output('interaccion-hora-prox-seguimiento', 'value', allow_duplicate=True), # Default 8
    Output('interaccion-minuto-prox-seguimiento', 'value', allow_duplicate=True),# Default 0
    # Output AM/PM eliminado
    Output('interaccion-concretada-store', 'data', allow_duplicate=True), Output('interaccion-venta-cerrada-store', 'data', allow_duplicate=True), Output('interaccion-ofrecio-precios-store', 'data', allow_duplicate=True),
    Output('interaccion-conoce-catalogo-store', 'data', allow_duplicate=True), Output('interaccion-llego-bien-pedido-store', 'data', allow_duplicate=True),
    Output('interaccion-informo-pago-store', 'data', allow_duplicate=True), Output('interaccion-reviso-ctacte-store', 'data', allow_duplicate=True),

    Input('interaccion-btn-guardar', 'n_clicks'),
    # States
    State('interaccion-cliente-cuit', 'value'), State('interaccion-cliente-razon-social-store', 'data'),
    State('interaccion-tipo', 'value'), State('interaccion-concretada-store', 'data'),
    State('interaccion-respuesta', 'value'),
    State('interaccion-fecha-prox-seguimiento', 'date'),
    State('interaccion-hora-prox-seguimiento', 'value'),
    State('interaccion-minuto-prox-seguimiento', 'value'),
    State('interaccion-venta-cerrada-store', 'data'), State('interaccion-motivo-no-venta', 'value'),
    State('interaccion-ofrecio-precios-store', 'data'), State('interaccion-conoce-catalogo-store', 'data'),
    State('interaccion-llego-bien-pedido-store', 'data'), State('interaccion-comentarios-venta', 'value'),
    State('interaccion-informo-pago-store', 'data'), State('interaccion-reviso-ctacte-store', 'data'),
    State('interaccion-comentarios-cobranza', 'value'),
    prevent_initial_call=True
)
def guardar_interaccion(
    n_clicks, cliente_cuit, cliente_razon_social, tipo, interaccion_ok, respuesta,
    fecha_prox_str, hora_prox, minuto_prox,
    venta_ok, motivo_no, ofrecio_precios, conoce_cat,
    llego_bien, com_venta, informo_pago, reviso_cta, com_cobranza
):
    # Definir valores de reset (hora=8, minuto=0)
    reset_textos = ("", "", "", None, None, None, 8, 0) # Sin AM/PM
    reset_stores = (False, False, False, False, True, False, False)
    all_resets = reset_textos + reset_stores

    if n_clicks == 0: return no_update, no_update, False, *all_resets
    if not cliente_cuit or not cliente_razon_social: return "Error: Debe seleccionar un cliente.", "danger", True, *([no_update] * len(all_resets))

    # --- Combinar Fecha y Hora (Formato 24h) ---
    fecha_prox_dt = None
    if fecha_prox_str:
        try:
            fecha_obj = dt.strptime(fecha_prox_str, '%Y-%m-%d').date()
            hora_int = int(hora_prox) if hora_prox is not None else 0
            minuto_int = int(minuto_prox) if minuto_prox is not None else 0
            if not (0 <= hora_int <= 23): raise ValueError("Hora inválida (0-23).")
            if not (0 <= minuto_int <= 59): raise ValueError("Minutos inválidos (0-59).")
            hora_obj = datetime_time(hora_int, minuto_int)
            fecha_prox_dt = dt.combine(fecha_obj, hora_obj)
            print(f"DEBUG guardar_interaccion - Combinado 24h OK: {fecha_prox_dt}")
        except (ValueError, TypeError) as e:
            print(f"Error combinando fecha y hora 24h: {e}")
            return f"Error: {e}", "danger", True, *([no_update] * len(all_resets))
    else:
        print("DEBUG guardar_interaccion - No se seleccionó fecha de seguimiento.")
    # --- Fin Combinar ---

    # --- CORRECCIÓN: Crear diccionario 'input_data' directamente ---
    # La lógica de limpieza ahora está completamente en CrmService.registrar_interaccion
    input_data = {
        'clienteCuit': cliente_cuit,
        'clienteRazonSocial': cliente_razon_social,
        'tipoInteraccion': tipo,
        'llamadaConcretada': bool(interaccion_ok), # Pasamos si se concretó o no
        'respuestaCliente': respuesta or None,
        'fechaProxSeguimiento': fecha_prox_dt, # Pasamos el datetime calculado (o None)
        'ventaCerrada': bool(venta_ok),
        'motivoNoVenta': motivo_no,
        'ofrecioOtrosPrecios': bool(ofrecio_precios),
        'clienteConoceCatalogo': bool(conoce_cat),
        'leLlegoBienPedido': bool(llego_bien),
        'comentariosVenta': com_venta or None,
        'clienteInformoPago': bool(informo_pago),
        'revisoCtaCte': bool(reviso_cta),
        'comentariosCobranza': com_cobranza or None
    }
    # --- FIN CORRECCIÓN ---

    if not current_user.is_authenticated: return "Error: Sesión expirada.", "danger", True, *([no_update] * len(all_resets))

    vendedor_dni = current_user.dni
    try:
        print(f"DEBUG guardar_interaccion - Llamando a CrmService.registrar_interaccion con fecha: {input_data.get('fechaProxSeguimiento')}")
        CrmService.registrar_interaccion(input_data, vendedor_dni) # Pasamos el diccionario completo
        return "¡Interacción guardada con éxito!", "success", True, *all_resets
    except ValueError as ve: return f"Error de validación: {ve}", "danger", True, *([no_update] * len(all_resets))
    except (Exception, psycopg2.DatabaseError) as e:
        print(f"Error DB o Servicio al guardar: {e}"); traceback.print_exc()
        return f"Error al guardar.", "danger", True, *([no_update] * len(all_resets))