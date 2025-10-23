# pages/01_dashboard_gerencia.py
import dash
from dash import dcc, html, callback, Input, Output, State, dash_table, ctx, no_update
import dash_bootstrap_components as dbc
import plotly.express as px
from flask_login import current_user
from core.services import CrmService
import pandas as pd
import re
from unidecode import unidecode

dash.register_page(
    __name__,
    path='/dashboard-gerencia',
    name="Dashboard Gerencia",
    title="Dashboard Gerencia"
)

# --- Layout de Filtros ---
filtros_layout = dbc.Card(dbc.CardBody([
    html.H4("Filtros Generales"),
    dbc.Row([
        dbc.Col(
            dcc.Dropdown(
                id='filtro-vendedor-gerencia', placeholder='Filtrar por Vendedor...', options=[], clearable=True,
                className="h-100"
            ),
            md=4,
            id='col-filtro-vendedor-gerencia' # ID Mantenido
        ),
        dbc.Col(
            dcc.Dropdown(
                id='filtro-cliente-gerencia', placeholder='Filtrar por Cliente...', options=[], clearable=True,
                className="h-100"
            ),
             md=4
        ),
        dbc.Col(
            dcc.DatePickerRange(
                id='filtro-fechas-gerencia', display_format='YYYY-MM-DD', clearable=True,
                className="w-100"
            ),
            md=4
        ),
    ],
    align="stretch",
    className="g-2"
    ),
    dbc.Button("Aplicar Filtros Generales", id='btn-aplicar-filtros-gerencia', color="primary", className="mt-3")
]))

# --- Layout de KPIs ---
kpis_layout = dbc.Row([
    dbc.Col(dbc.Card(dbc.CardBody(id='kpi-total-interacciones-gerencia')), md=4),
    dbc.Col(dbc.Card(dbc.CardBody(id='kpi-tasa-contacto-gerencia')), md=4),
    dbc.Col(dbc.Card(dbc.CardBody(id='kpi-tasa-cierre-gerencia')), md=4),
])

# --- Layout de Gráficos ---
graficos_layout = dbc.Row([
    dbc.Col(dcc.Graph(id='grafico-motivos-no-venta-gerencia'), md=12),
])

# --- Layout Tabla ---
columnas_tabla_base_gerencia = [
    {"name": "Fecha", "id": "fecha_interaccion"}, # Se formatea con AM/PM en CrmService
    {"name": "Tipo", "id": "tipo_interaccion"},
    # Columna Vendedor se añade dinámicamente
    {"name": "Cliente", "id": "cliente_razon_social"},
    {"name": "Venta Cerrada", "id": "venta_cerrada"},
    {"name": "Respuesta / Comentarios", "id": "comentarios_venta"},
]
tabla_layout = dbc.Row(
    dbc.Col(
        dash_table.DataTable(
            id='tabla-interacciones-gerencia',
            columns=[], # Se actualizan dinámicamente
            data=[], page_size=10, style_table={'overflowX': 'auto'},
            style_as_list_view=True,
            style_cell={ 'textAlign': 'left', 'padding': '5px', 'overflow': 'hidden', 'textOverflow': 'ellipsis', 'minWidth': '80px', 'width': 'auto', 'maxWidth': '180px' },
            style_cell_conditional=[
                { 'if': {'column_id': 'comentarios_venta'}, 'maxWidth': '350px', 'whiteSpace': 'normal', 'textAlign': 'left' },
                { 'if': {'column_id': 'fecha_interaccion'}, 'minWidth': '180px', 'width': '180px'}, # Ancho para AM/PM
                { 'if': {'column_id': 'venta_cerrada'}, 'textAlign': 'center', 'minWidth': '80px', 'width': '80px'},
                { 'if': {'column_id': 'vendedor_nombre'}, 'minWidth': '150px', 'width': '150px'}
            ],
            tooltip_data=[], tooltip_duration=None,
            style_header={'backgroundColor': 'rgb(230, 230, 230)', 'fontWeight': 'bold'},
            filter_action="custom", filter_query='', # Mantenemos filtro custom
            sort_action="native",
        ), width=12
    )
)

# --- Layout Principal ---
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

@callback(
    Output('filtro-vendedor-gerencia', 'options'),
    Input('initial-load-trigger-gerencia', 'data')
)
def cargar_opciones_vendedores(initial_trigger):
    try:
        vendedores = CrmService.get_vendedores_dropdown()
        options = [{'label': v['nombre'], 'value': v['dni']} for v in vendedores]
        return options
    except Exception as e:
        print(f"Error cargando vendedores: {e}")
        return []

@callback( Output('filtro-cliente-gerencia', 'options'), Input('initial-load-trigger-gerencia', 'data') )
def cargar_opciones_clientes_gerencia(initial_trigger):
    try: return [{'label': f"{c['razon_social']} ({c['cuit']})", 'value': c['cuit']} for c in CrmService.get_clientes_dropdown()]
    except Exception as e: print(f"Error cargando clientes: {e}"); return []

@callback(
    Output('dashboard-gerencia-data-store', 'data'),
    Input('initial-load-trigger-gerencia', 'data'),
    Input('btn-aplicar-filtros-gerencia', 'n_clicks'),
    State('filtro-vendedor-gerencia', 'value'), State('filtro-cliente-gerencia', 'value'),
    State('filtro-fechas-gerencia', 'start_date'), State('filtro-fechas-gerencia', 'end_date'),
)
def cargar_datos_dashboard_gerencia(initial_trigger, n_clicks_filter, vendedor_dni, cliente_cuit, fecha_desde, fecha_hasta):
    trigger_id = ctx.triggered_id
    if trigger_id is None or trigger_id == 'btn-aplicar-filtros-gerencia':
        filters = {'vendedorDni': vendedor_dni, 'clienteCuit': cliente_cuit, 'fechaDesde': fecha_desde, 'fechaHasta': fecha_hasta}
        data = CrmService.get_dashboard(filters) # Devuelve fechas formateadas AM/PM
        return data
    return no_update

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


@callback(
    Output('grafico-motivos-no-venta-gerencia', 'figure'),
    Input('dashboard-gerencia-data-store', 'data')
)
def actualizar_graficos_gerencia(data):
    empty_fig = {'data': [], 'layout': {'xaxis': {'visible': False}, 'yaxis': {'visible': False}, 'annotations': [{'text': 'No hay datos', 'xref': 'paper', 'yref': 'paper', 'showarrow': False, 'font': {'size': 16}}]}}
    if not data or not data.get('graficos'):
        return empty_fig
    graficos = data['graficos']
    motivos_data = graficos.get('motivosNoVenta')
    if motivos_data:
        fig_motivos = px.pie(motivos_data, names='label', values='value', title="Motivos de No-Venta")
        fig_motivos.update_traces(textposition='inside', textinfo='percent+label')
        # Ajustes de layout para leyenda y márgenes
        fig_motivos.update_layout(
            legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
            margin=dict(l=20, r=20, t=50, b=20)
        )
    else:
        fig_motivos = empty_fig
        fig_motivos['layout']['annotations'][0]['text'] = 'No hay datos de Motivos'
    return fig_motivos


# --- Función helper de filtrado (ignora acentos, mayúsculas, usa 'contains') ---
def apply_custom_filter(data_list, filter_query):
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
            # Convertir a string ANTES de quitar acentos
            col_as_str = dff[col_name].fillna('').astype(str)
            col_normalized = col_as_str.apply(lambda x: unidecode(x).lower())
            value_normalized = unidecode(value_from_input).lower()
            dff = dff[col_normalized.str.contains(value_normalized, na=False)]
        except Exception as e: print(f"Error filtro: '{expression}' - {e}"); pass
    return dff

# --- Callback Tabla GERENCIA (CORREGIDO: Manejo de current_columns en tooltip) ---
@callback(
    Output('tabla-interacciones-gerencia', 'data'),
    Output('tabla-interacciones-gerencia', 'tooltip_data'),
    Input('dashboard-gerencia-data-store', 'data'),
    Input('tabla-interacciones-gerencia', 'filter_query'),
    State('tabla-interacciones-gerencia', 'columns') # Columnas actuales definidas dinámicamente
)
def actualizar_tabla_gerencia(data, filter_query, current_columns):
    if not data or not data.get('ultimasInteracciones'):
        return [], []

    table_data_raw = data['ultimasInteracciones']
    dff_filtered = apply_custom_filter(table_data_raw, filter_query)
    table_data = dff_filtered.to_dict('records')

    # --- CORRECCIÓN: Verificar que current_columns no sea None antes de iterar ---
    tooltip_data = []
    if current_columns: # Solo generar tooltips si hay columnas definidas
        try:
            tooltip_data = [
                {
                    col['id']: {'value': str(row.get(col['id'], '')), 'type': 'markdown'}
                    for col in current_columns if isinstance(col, dict) and 'id' in col # Asegurar formato correcto de col
                }
                for row in table_data
            ]
        except Exception as e:
             print(f"Error generando tooltip_data: {e}")
             tooltip_data = [] # Devolver lista vacía en caso de error
    # --- FIN CORRECCIÓN ---

    return table_data, tooltip_data

# --- Callback Columnas Tabla GERENCIA ---
@callback(
    Output('tabla-interacciones-gerencia', 'columns'),
    Input('initial-load-trigger-gerencia', 'data') # Se dispara al cargar datos inicialmente
)
def update_table_columns_gerencia(initial_trigger):
    current_columns = columnas_tabla_base_gerencia.copy()
    # Asegurarse de que la columna 'vendedor_nombre' exista
    if not any(col['id'] == 'vendedor_nombre' for col in current_columns):
        vendedor_col = {"name": "Vendedor", "id": "vendedor_nombre"}
        current_columns.insert(2, vendedor_col) # Insertar después de 'Tipo'
    return current_columns