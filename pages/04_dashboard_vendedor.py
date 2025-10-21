# pages/04_dashboard_vendedor.py
import dash
from dash import dcc, html, callback, Input, Output, State, dash_table
import dash_bootstrap_components as dbc
from flask_login import current_user
from core.services import CrmService
import pandas as pd
import re # <-- AÑADIDO

dash.register_page(
    __name__,
    path='/dashboard-vendedor',
    name="Mi Dashboard",
    title="Mi Dashboard Vendedor"
)

# --- Layouts Específicos para Vendedor ---

# KPIs Vendedor (sin cambios)
kpis_vendedor_layout = dbc.Row([
    dbc.Col(dbc.Card(dbc.CardBody(id='kpi-vendedor-interacciones')), md=4),
    dbc.Col(dbc.Card(dbc.CardBody(id='kpi-vendedor-tasa-contacto')), md=4),
    dbc.Col(dbc.Card(dbc.CardBody(id='kpi-vendedor-tasa-cierre')), md=4),
])

# Próximos Seguimientos (CORREGIDO: filter_action="custom")
seguimientos_cols = [
    {"name": "Fecha Seguimiento", "id": "fecha_prox_seguimiento", 'type': 'datetime'},
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
                style_as_list_view=True, # Responsive
                style_cell={ 'textAlign': 'left', 'padding': '5px', 'overflow': 'hidden', 'textOverflow': 'ellipsis', 'minWidth': '80px', 'width': '150px'},
                style_cell_conditional=[
                     { 'if': {'column_id': 'respuesta_cliente'}, 'maxWidth': '300px', 'whiteSpace': 'normal' },
                     { 'if': {'column_id': 'fecha_prox_seguimiento'}, 'minWidth': '120px', 'width': '120px' }
                ],
                 style_header={'backgroundColor': 'rgb(240, 240, 240)', 'fontWeight': 'bold'},
                 sort_action="native",
                 # --- CORRECCIÓN ---
                 filter_action="custom",
                 filter_query='',
                 # ------------------
            )
        )
    ]
)

# Últimas Interacciones Vendedor (CORREGIDO: filter_action="custom")
ultimas_interacciones_cols_vendedor = [
    {"name": "Fecha", "id": "fecha_interaccion"},
    {"name": "Tipo", "id": "tipo_interaccion"},
    {"name": "Cliente", "id": "cliente_razon_social"},
    {"name": "Venta Cerrada", "id": "venta_cerrada"},
    {"name": "Respuesta / Comentarios", "id": "comentarios_venta"}
]
ultimas_interacciones_layout = dash_table.DataTable(
    id='tabla-ultimas-interacciones-vendedor',
    columns=ultimas_interacciones_cols_vendedor, data=[], page_size=10, style_table={'overflowX': 'auto'},
    style_as_list_view=True, # Responsive
    style_cell={ 'textAlign': 'left', 'padding': '5px', 'overflow': 'hidden', 'textOverflow': 'ellipsis', 'minWidth': '80px', 'width': '120px', 'maxWidth': '180px' },
    style_cell_conditional=[
        { 'if': {'column_id': 'comentarios_venta'}, 'maxWidth': '350px', 'whiteSpace': 'normal', 'textAlign': 'left' },
        { 'if': {'column_id': 'fecha_interaccion'}, 'minWidth': '130px', 'width': '130px'},
        { 'if': {'column_id': 'venta_cerrada'}, 'textAlign': 'center', 'minWidth': '80px', 'width': '80px'}
    ],
    tooltip_data=[], tooltip_duration=None,
    style_header={'backgroundColor': 'rgb(230, 230, 230)', 'fontWeight': 'bold'},
    # --- CORRECCIÓN ---
    filter_action="custom",
    filter_query='',
    # ------------------
    sort_action="native",
)

# --- Layout Principal Vendedor (sin cambios) ---
def layout():
    if not current_user.is_authenticated: return dcc.Location(pathname="/login", id="redirect-login-vend-auth")
    if current_user.rol != 'vendedor': return dcc.Location(pathname="/login", id="redirect-login-vend-role")
    children = [
        dcc.Store(id='dashboard-vendedor-data-store'),
        dcc.Store(id='initial-load-trigger-vendedor'),
        html.H1(f"Mi Dashboard - {current_user.nombre}"),
        html.Hr(), kpis_vendedor_layout, html.Hr(),
        dbc.Row([
            dbc.Col(seguimientos_layout, md=5),
            dbc.Col([ html.H3("Mis Últimas Interacciones"), ultimas_interacciones_layout ], md=7)
        ]),
    ]
    return dbc.Container(children, fluid=True)

# --- CALLBACKS VENDEDOR ---

# Cargar datos del vendedor (sin cambios)
@callback( Output('dashboard-vendedor-data-store', 'data'), Input('initial-load-trigger-vendedor', 'data') )
def cargar_datos_vendedor(initial_trigger):
    if not current_user.is_authenticated or current_user.rol != 'vendedor': return dash.no_update
    vendedor_dni = current_user.dni; data = CrmService.get_datos_vendedor(vendedor_dni); return data

# Actualizar KPIs (sin cambios)
@callback(
    Output('kpi-vendedor-interacciones', 'children'), Output('kpi-vendedor-tasa-contacto', 'children'),
    Output('kpi-vendedor-tasa-cierre', 'children'), Input('dashboard-vendedor-data-store', 'data')
)
def actualizar_kpis_vendedor(data):
    default_kpi = [html.H5("..."), html.H3("...")]
    kpis = data.get('kpis', {}) if data else {}
    return ([html.H5("Mis Interacciones", className="card-title"), html.H3(kpis.get('totalInteracciones', 0), className="card-text")],
            [html.H5("Mi Tasa Contacto", className="card-title"), html.H3(kpis.get('tasaContacto', 'N/A'), className="card-text")],
            [html.H5("Mi Tasa Cierre", className="card-title"), html.H3(kpis.get('tasaCierreVenta', '0%'), className="card-text")])


# --- Función helper de filtrado (para ambas tablas) ---
def apply_custom_filter(data_list, filter_query):
    if not filter_query:
        return pd.DataFrame(data_list) # Devolver DataFrame si no hay filtro
    
    if not data_list:
         return pd.DataFrame() # Devolver DF vacío si no hay datos

    dff = pd.DataFrame(data_list)
    filtering_expressions = filter_query.split(' && ')
    for expression in filtering_expressions:
        try:
            if 'filter data...' in expression: continue
            match = re.match(r'^{\s*(.*?)\s*} (.*?) (.*)$', expression.strip())
            if not match: continue

            col_name = match.group(1)
            operator = match.group(2).lower()
            value = match.group(3).strip('\'"')

            if col_name not in dff.columns: continue

            if operator == 'contains':
                dff = dff[dff[col_name].astype(str).str.contains(value, case=False, na=False)]
            elif operator == '=':
                dff = dff[dff[col_name].astype(str).str.eq(value, case=False, na=False)]
            elif operator == '!=':
                dff = dff[~dff[col_name].astype(str).str.eq(value, case=False, na=False)]
            # (Puedes añadir operadores numéricos/fecha si es necesario)
                
        except Exception as e:
            print(f"Error al parsear filtro: {expression} ({e})")
            pass
    return dff # Devolver DataFrame filtrado
# --- Fin Función helper ---


# --- Callback tabla seguimientos (CORREGIDO con filtro custom) ---
@callback(
    Output('tabla-seguimientos', 'data'),
    Input('dashboard-vendedor-data-store', 'data'),
    Input('tabla-seguimientos', 'filter_query') # NUEVO INPUT
)
def actualizar_tabla_seguimientos(data, filter_query):
    seguimientos = data.get('proximos_seguimientos', []) if data else []
    
    # Aplicar filtro
    dff_filtered = apply_custom_filter(seguimientos, filter_query)
    
    # Formatear datos DESPUÉS de filtrar
    table_data = dff_filtered.to_dict('records')
    for seg in table_data:
        if 'respuesta_cliente' in seg and seg['respuesta_cliente']:
             respuesta = seg['respuesta_cliente']
             seg['respuesta_cliente'] = (respuesta[:70] + '...') if len(respuesta or '') > 70 else respuesta
    return table_data
# --- FIN CORRECCIÓN ---


# --- Callback tabla últimas interacciones (CORREGIDO con filtro custom) ---
@callback(
    Output('tabla-ultimas-interacciones-vendedor', 'data'),
    Output('tabla-ultimas-interacciones-vendedor', 'tooltip_data'),
    Input('dashboard-vendedor-data-store', 'data'),
    Input('tabla-ultimas-interacciones-vendedor', 'filter_query') # NUEVO INPUT
)
def actualizar_tabla_ultimas_interacciones(data, filter_query):
    table_data_raw = data.get('ultimas_interacciones', []) if data else []
    
    # Aplicar filtro
    dff_filtered = apply_custom_filter(table_data_raw, filter_query)

    # Devolver datos filtrados y generar tooltips
    table_data = dff_filtered.to_dict('records')
    tooltip_data = [{col['id']: {'value': str(row.get(col['id'], '')), 'type': 'markdown'} for col in ultimas_interacciones_cols_vendedor} for row in table_data]
    return table_data, tooltip_data
# --- FIN CORRECCIÓN ---