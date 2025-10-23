# pages/04_dashboard_vendedor.py
import dash
from datetime import datetime as dt, time as datetime_time, date as datetime_date
from dash import dcc, html, callback, Input, Output, State, dash_table, no_update
import dash_bootstrap_components as dbc
from flask_login import current_user
from core.services import CrmService
import pandas as pd
import re
from unidecode import unidecode

dash.register_page(
    __name__,
    path='/dashboard-vendedor',
    name="Mi Dashboard",
    title="Mi Dashboard Vendedor"
)

# --- Layouts Específicos para Vendedor ---

kpis_vendedor_layout = dbc.Row([
    dbc.Col(dbc.Card(dbc.CardBody(id='kpi-vendedor-interacciones')), md=4),
    dbc.Col(dbc.Card(dbc.CardBody(id='kpi-vendedor-tasa-contacto')), md=4),
    dbc.Col(dbc.Card(dbc.CardBody(id='kpi-vendedor-tasa-cierre')), md=4),
])

# Próximos Seguimientos (MODIFICADO: Estilo Columna Fecha/Hora 24h)
seguimientos_cols = [
    # --- MODIFICACIÓN: Ajustar nombre y mantener type='text' ---
    {"name": "Fecha y Hora Seguim.", "id": "fecha_prox_seguimiento", 'type': 'text'},
    # -------------------------------------------------------------
    {"name": "Cliente", "id": "cliente_razon_social"},
    {"name": "Última Respuesta", "id": "respuesta_cliente"},
]
seguimientos_layout = dbc.Card(
    [
        dbc.CardHeader("Próximos Seguimientos"),
        dbc.CardBody(
            dash_table.DataTable(
                id='tabla-seguimientos',
                columns=seguimientos_cols, data=[], page_size=5, style_table={'overflowX': 'auto'},
                style_as_list_view=True,
                style_cell={ 'textAlign': 'left', 'padding': '5px', 'overflow': 'hidden', 'textOverflow': 'ellipsis', 'minWidth': '80px', 'width': 'auto'},
                style_cell_conditional=[
                     { 'if': {'column_id': 'respuesta_cliente'}, 'maxWidth': '300px', 'whiteSpace': 'normal' },
                     # --- MODIFICACIÓN: Ancho para formato YYYY-MM-DD HH:MM ---
                     { 'if': {'column_id': 'fecha_prox_seguimiento'}, 'minWidth': '160px', 'width': '160px' }
                     # -----------------------------------------------------------
                ],
                 style_header={'backgroundColor': 'rgb(240, 240, 240)', 'fontWeight': 'bold'},
                 sort_action="native",
                 filter_action="custom",
                 filter_query='',
            )
        )
    ]
)

# Últimas Interacciones Vendedor (MODIFICADO: Estilo Columna Fecha/Hora 24h)
ultimas_interacciones_cols_vendedor = [
    {"name": "Fecha", "id": "fecha_interaccion"}, # Se formatea con 24h en CrmService
    {"name": "Tipo", "id": "tipo_interaccion"},
    {"name": "Cliente", "id": "cliente_razon_social"},
    {"name": "Venta Cerrada", "id": "venta_cerrada"},
    {"name": "Respuesta / Comentarios", "id": "comentarios_venta"}
]
ultimas_interacciones_layout = dash_table.DataTable(
    id='tabla-ultimas-interacciones-vendedor',
    columns=ultimas_interacciones_cols_vendedor, data=[], page_size=10, style_table={'overflowX': 'auto'},
    style_as_list_view=True,
    style_cell={ 'textAlign': 'left', 'padding': '5px', 'overflow': 'hidden', 'textOverflow': 'ellipsis', 'minWidth': '80px', 'width': 'auto', 'maxWidth': '180px' },
    style_cell_conditional=[
        { 'if': {'column_id': 'comentarios_venta'}, 'maxWidth': '350px', 'whiteSpace': 'normal', 'textAlign': 'left' },
        # --- MODIFICACIÓN: Ancho para formato YYYY-MM-DD HH:MM ---
        { 'if': {'column_id': 'fecha_interaccion'}, 'minWidth': '160px', 'width': '160px'},
        # -----------------------------------------------------------
        { 'if': {'column_id': 'venta_cerrada'}, 'textAlign': 'center', 'minWidth': '80px', 'width': '80px'}
    ],
    tooltip_data=[], tooltip_duration=None,
    style_header={'backgroundColor': 'rgb(230, 230, 230)', 'fontWeight': 'bold'},
    filter_action="custom",
    filter_query='',
    sort_action="native",
)

def layout():
    # ... (código sin cambios) ...
    if not current_user.is_authenticated: return dcc.Location(pathname="/login", id="redirect-login-vend-auth")
    allowed_roles = ['vendedor', 'gerente']
    if current_user.rol not in allowed_roles: return dcc.Location(pathname="/login", id="redirect-login-vend-role")
    children = [
        dcc.Store(id='dashboard-vendedor-data-store'), dcc.Store(id='initial-load-trigger-vendedor'),
        html.H1(f"Mi Dashboard - {getattr(current_user, 'nombre', 'Usuario')}"), html.Hr(),
        kpis_vendedor_layout, html.Hr(),
        dbc.Row([ dbc.Col(seguimientos_layout, md=5), dbc.Col([ html.H3("Mis Últimas Interacciones"), ultimas_interacciones_layout ], md=7)]),
    ]
    return dbc.Container(children, fluid=True)

# --- CALLBACKS VENDEDOR ---

@callback( Output('dashboard-vendedor-data-store', 'data'), Input('initial-load-trigger-vendedor', 'data') )
def cargar_datos_vendedor(initial_trigger):
    # ... (código sin cambios) ...
    allowed_roles = ['vendedor', 'gerente']
    if not current_user.is_authenticated or current_user.rol not in allowed_roles: return no_update
    user_dni = getattr(current_user, 'dni', None)
    if not user_dni: print("ERROR: Usuario autenticado pero sin DNI."); return no_update
    data = CrmService.get_datos_vendedor(user_dni) # Ahora devuelve fecha/hora 24h
    return data

@callback(
    Output('kpi-vendedor-interacciones', 'children'), Output('kpi-vendedor-tasa-contacto', 'children'),
    Output('kpi-vendedor-tasa-cierre', 'children'), Input('dashboard-vendedor-data-store', 'data')
)
def actualizar_kpis_vendedor(data):
    # ... (código sin cambios) ...
    default_kpi = [html.H5("..."), html.H3("...")]
    kpis = data.get('kpis', {}) if data else {}
    return ([html.H5("Mis Interacciones", className="card-title"), html.H3(kpis.get('totalInteracciones', 0), className="card-text")],
            [html.H5("Mi Tasa Contacto", className="card-title"), html.H3(kpis.get('tasaContacto', 'N/A'), className="card-text")],
            [html.H5("Mi Tasa Cierre", className="card-title"), html.H3(kpis.get('tasaCierreVenta', '0%'), className="card-text")])

def apply_custom_filter(data_list, filter_query):
    # ... (código sin cambios) ...
    if not filter_query: return pd.DataFrame(data_list)
    if not data_list: return pd.DataFrame()
    dff = pd.DataFrame(data_list)
    filter_pattern = re.compile(r'^{\s* (.*?)\s*} \s* (\S+) \s* ([\'"]? (.*?) [\'"]?)$', re.X)
    filtering_expressions = filter_query.split(' && ')
    for expression in filtering_expressions:
        expression = expression.strip();
        if not expression or 'filter data...' in expression: continue
        try:
            match = filter_pattern.match(expression)
            if not match: continue
            col_name = match.group(1).strip()
            value_from_input = match.group(4).strip()
            if col_name not in dff.columns: continue
            col_as_str = dff[col_name].fillna('').astype(str)
            col_normalized = col_as_str.apply(lambda x: unidecode(x).lower())
            value_normalized = unidecode(value_from_input).lower()
            dff = dff[col_normalized.str.contains(value_normalized, na=False)]
        except Exception as e: print(f"Error filtro: '{expression}' - {e}"); pass
    return dff

@callback(
    Output('tabla-seguimientos', 'data'),
    Input('dashboard-vendedor-data-store', 'data'),
    Input('tabla-seguimientos', 'filter_query')
)
def actualizar_tabla_seguimientos(data, filter_query):
    # ... (código sin cambios) ...
    seguimientos = data.get('proximos_seguimientos', []) if data else []
    dff_filtered = apply_custom_filter(seguimientos, filter_query)
    table_data = dff_filtered.to_dict('records')
    for seg in table_data:
        if 'respuesta_cliente' in seg and seg['respuesta_cliente']:
             respuesta = seg['respuesta_cliente']
             seg['respuesta_cliente'] = (respuesta[:70] + '...') if len(respuesta or '') > 70 else respuesta
    return table_data

@callback(
    Output('tabla-ultimas-interacciones-vendedor', 'data'),
    Output('tabla-ultimas-interacciones-vendedor', 'tooltip_data'),
    Input('dashboard-vendedor-data-store', 'data'),
    Input('tabla-ultimas-interacciones-vendedor', 'filter_query')
)
def actualizar_tabla_ultimas_interacciones(data, filter_query):
    # ... (código sin cambios) ...
    table_data_raw = data.get('ultimas_interacciones', []) if data else []
    dff_filtered = apply_custom_filter(table_data_raw, filter_query)
    table_data = dff_filtered.to_dict('records')
    tooltip_data = [{col['id']: {'value': str(row.get(col['id'], '')), 'type': 'markdown'} for col in ultimas_interacciones_cols_vendedor} for row in table_data]
    return table_data, tooltip_data