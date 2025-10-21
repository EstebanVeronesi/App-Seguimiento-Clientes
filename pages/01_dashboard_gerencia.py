# pages/01_dashboard_gerencia.py
import dash
from dash import dcc, html, callback, Input, Output, State, dash_table, ctx
import dash_bootstrap_components as dbc
import plotly.express as px
from flask_login import current_user
from core.services import CrmService

dash.register_page(
    __name__,
    path='/dashboard-gerencia', # Nueva ruta
    name="Dashboard Gerencia", # Nuevo nombre para la navbar
    title="Dashboard Gerencia"
)

# --- Layout de Filtros (CORREGIDO: 'align="stretch"') ---
filtros_layout = dbc.Card(dbc.CardBody([
    dbc.Row([
        dbc.Col(
            dcc.Dropdown(
                id='filtro-vendedor-gerencia', placeholder='Filtrar por Vendedor...', options=[], clearable=True,
                className="h-100" # Ocupar 100% de altura
            ),
            md=4,
            id='col-filtro-vendedor-gerencia'
        ),
        dbc.Col(
            dcc.Dropdown(
                id='filtro-cliente-gerencia', placeholder='Filtrar por Cliente...', options=[], clearable=True,
                className="h-100" # Ocupar 100% de altura
            ),
             md=4
        ),
        dbc.Col(
            dcc.DatePickerRange(
                id='filtro-fechas-gerencia', display_format='YYYY-MM-DD', clearable=True,
                className="w-100" # Ocupar 100% de ancho
            ),
            md=4
        ),
    ],
    align="stretch", # <-- CORRECCIÓN AQUÍ (era align_itemsDStretch)
    className="g-2" # Añade un pequeño espacio entre columnas
    ),
    dbc.Button("Aplicar Filtros", id='btn-aplicar-filtros-gerencia', color="primary", className="mt-3")
]))
# --- FIN CORRECCIÓN LAYOUT FILTROS ---


# --- Layout de KPIs (Sin Kg) (sin cambios) ---
kpis_layout = dbc.Row([
    dbc.Col(dbc.Card(dbc.CardBody(id='kpi-total-interacciones-gerencia')), md=4),
    dbc.Col(dbc.Card(dbc.CardBody(id='kpi-tasa-contacto-gerencia')), md=4),
    dbc.Col(dbc.Card(dbc.CardBody(id='kpi-tasa-cierre-gerencia')), md=4),
])

# --- Layout de Gráficos (Solo Motivos) (sin cambios) ---
graficos_layout = dbc.Row([
    dbc.Col(dcc.Graph(id='grafico-motivos-no-venta-gerencia'), md=12),
])

# --- Layout Tabla (Sin Kg) ---
columnas_tabla_base_gerencia = [
    {"name": "Fecha", "id": "fecha_interaccion"},
    {"name": "Tipo", "id": "tipo_interaccion"},
    {"name": "Cliente", "id": "cliente_razon_social"},
    {"name": "Venta Cerrada", "id": "venta_cerrada"},
    {"name": "Respuesta / Comentarios", "id": "comentarios_venta"}
]
tabla_layout = dbc.Row(
    dbc.Col(
        dash_table.DataTable(
            id='tabla-interacciones-gerencia',
            data=[], page_size=10, style_table={'overflowX': 'auto'},
            style_as_list_view=True, # Mantiene responsive
            style_cell={ 'textAlign': 'left', 'padding': '5px', 'overflow': 'hidden', 'textOverflow': 'ellipsis', 'minWidth': '80px', 'width': '120px', 'maxWidth': '180px' },
            style_cell_conditional=[
                { 'if': {'column_id': 'comentarios_venta'}, 'maxWidth': '350px', 'whiteSpace': 'normal', 'textAlign': 'left' },
                { 'if': {'column_id': 'fecha_interaccion'}, 'minWidth': '130px', 'width': '130px'},
                { 'if': {'column_id': 'venta_cerrada'}, 'textAlign': 'center', 'minWidth': '80px', 'width': '80px'}
            ],
            tooltip_data=[], tooltip_duration=None,
            style_header={'backgroundColor': 'rgb(230, 230, 230)', 'fontWeight': 'bold'},
            filter_action="native", sort_action="native",
        ), width=12
    )
)

# --- Layout Principal (sin cambios) ---
def layout():
    if not current_user.is_authenticated:
        return dcc.Location(pathname="/login", id="redirect-login-gerencia-auth")
    if current_user.rol != 'gerente':
        return dcc.Location(pathname="/login", id="redirect-login-gerencia-role")

    children = [
        dcc.Store(id='dashboard-gerencia-data-store'),
        dcc.Store(id='initial-load-trigger-gerencia'),
        html.H1("Dashboard Gerencia"),
        filtros_layout,
        html.Hr(), kpis_layout, html.Hr(), graficos_layout, html.Hr(),
        html.H3("Últimas Interacciones (General)"), tabla_layout
    ]
    return dbc.Container(children, fluid=True)


# --- CALLBACKS ---

# Callbacks para cargar opciones dropdowns (sin cambios)
@callback( Output('filtro-vendedor-gerencia', 'options'), Input('initial-load-trigger-gerencia', 'data') )
def cargar_opciones_vendedores_gerencia(initial_trigger):
    try: return [{'label': v['nombre'], 'value': v['dni']} for v in CrmService.get_vendedores_dropdown()]
    except Exception as e: print(f"Error cargando vendedores: {e}"); return []
@callback( Output('filtro-cliente-gerencia', 'options'), Input('initial-load-trigger-gerencia', 'data') )
def cargar_opciones_clientes_gerencia(initial_trigger):
    try: return [{'label': f"{c['razon_social']} ({c['cuit']})", 'value': c['cuit']} for c in CrmService.get_clientes_dropdown()]
    except Exception as e: print(f"Error cargando clientes: {e}"); return []

# Callback para cargar datos (sin 'zona')
@callback(
    Output('dashboard-gerencia-data-store', 'data'),
    Input('initial-load-trigger-gerencia', 'data'), Input('btn-aplicar-filtros-gerencia', 'n_clicks'),
    State('filtro-vendedor-gerencia', 'value'), State('filtro-cliente-gerencia', 'value'),
    State('filtro-fechas-gerencia', 'start_date'), State('filtro-fechas-gerencia', 'end_date'),
)
def cargar_datos_dashboard_gerencia(initial_trigger, n_clicks, vendedor_dni, cliente_cuit, fecha_desde, fecha_hasta): # 'zona' eliminado
    filters = {'vendedorDni': vendedor_dni, 'clienteCuit': cliente_cuit, 'fechaDesde': fecha_desde, 'fechaHasta': fecha_hasta} # 'zona' eliminado
    data = CrmService.get_dashboard(filters)
    return data

# Callback para actualizar KPIs (sin cambios)
@callback(
    Output('kpi-total-interacciones-gerencia', 'children'), Output('kpi-tasa-contacto-gerencia', 'children'),
    Output('kpi-tasa-cierre-gerencia', 'children'),
    Input('dashboard-gerencia-data-store', 'data')
)
def actualizar_kpis_gerencia(data):
    default_kpi = [html.H5("..."), html.H3("...")]
    if not data or not data.get('kpis'): return default_kpi, default_kpi, default_kpi
    kpis = data['kpis']
    return ([html.H5("Interacciones", className="card-title"), html.H3(kpis.get('totalInteracciones', 0), className="card-text")],
            [html.H5("Tasa Contacto", className="card-title"), html.H3(kpis.get('tasaContacto', 'N/A'), className="card-text")],
            [html.H5("Tasa Cierre", className="card-title"), html.H3(kpis.get('tasaCierreVenta', '0%'), className="card-text")])

# Callback para actualizar Gráficos (sin cambios)
@callback( Output('grafico-motivos-no-venta-gerencia', 'figure'), Input('dashboard-gerencia-data-store', 'data') )
def actualizar_graficos_gerencia(data):
    empty_fig = {'data': [], 'layout': {'xaxis': {'visible': False}, 'yaxis': {'visible': False}, 'annotations': [{'text': 'No hay datos', 'xref': 'paper', 'yref': 'paper', 'showarrow': False, 'font': {'size': 16}}]}}
    if not data or not data.get('graficos'): return empty_fig
    graficos = data['graficos']
    if graficos.get('motivosNoVenta'):
        fig_motivos = px.pie(graficos['motivosNoVenta'], names='label', values='value', title="Motivos de No-Venta")
        fig_motivos.update_traces(textposition='inside', textinfo='percent+label')
    else: fig_motivos = empty_fig; fig_motivos['layout']['annotations'][0]['text'] = 'No hay datos de Motivos'
    return fig_motivos

# Callback para actualizar Tabla (sin cambios)
@callback( Output('tabla-interacciones-gerencia', 'data'), Output('tabla-interacciones-gerencia', 'tooltip_data'), Input('dashboard-gerencia-data-store', 'data'), State('tabla-interacciones-gerencia', 'columns') )
def actualizar_tabla_gerencia(data, current_columns):
    if not data or not data.get('ultimasInteracciones'): return [], []
    table_data = data['ultimasInteracciones']
    tooltip_data = [{col['id']: {'value': str(row.get(col['id'], '')), 'type': 'markdown'} for col in current_columns} for row in table_data]
    return table_data, tooltip_data

# Callback para actualizar COLUMNAS de la tabla (sin cambios)
@callback( Output('tabla-interacciones-gerencia', 'columns'), Input('initial-load-trigger-gerencia', 'data') )
def update_table_columns_gerencia(initial_trigger):
    current_columns = columnas_tabla_base_gerencia.copy()
    if not any(col['id'] == 'vendedor_nombre' for col in current_columns):
        vendedor_col = {"name": "Vendedor", "id": "vendedor_nombre"}
        current_columns.insert(2, vendedor_col)
    return current_columns