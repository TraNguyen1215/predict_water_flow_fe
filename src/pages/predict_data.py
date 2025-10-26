from dash import html, dcc, callback, Input, Output, State
import dash_bootstrap_components as dbc
from components.navbar import create_navbar
from components.topbar import TopBar
from dash.exceptions import PreventUpdate
import dash
import random
from datetime import datetime
import plotly.graph_objs as go


def create_empty_store():
    return []


layout = html.Div([
    create_navbar(is_authenticated=True),
    dbc.Container([
        dbc.Row([dbc.Col(TopBar('Mô phỏng dữ liệu dự báo', extra_left=[
            dcc.Dropdown(id='predict-interval-select', options=[
                {'label': '1s', 'value': 1000},
                {'label': '2s', 'value': 2000},
                {'label': '5s', 'value': 5000},
                {'label': '10s', 'value': 10000}
            ], value=2000, clearable=False, className='me-2', style={'width':'120px'}),
            dcc.Dropdown(id='predict-sigma-select', options=[
                {'label':'Thấp', 'value':0.2},
                {'label':'Trung bình', 'value':0.6},
                {'label':'Cao', 'value':1.5}
            ], value=0.6, clearable=False, className='me-2', style={'width':'140px'})
        ], extra_right=[
            dbc.Button('Bắt đầu', id='start-sim', color='primary', n_clicks=0, className='me-2'),
            dbc.Button('Xóa', id='clear-sim', color='danger', n_clicks=0)
        ]))], className='my-3'),

        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5([html.I(className='fas fa-chart-area me-2'), 'Lưu lượng nước (L/s) - Mô phỏng'])),
                    dbc.CardBody([
                        dcc.Graph(id='predict-flow-chart', figure={}, config={'displayModeBar': True}),
                        html.Div(className='mt-3', children=[
                            html.Small('Hiển thị các mẫu mô phỏng gần nhất (tự động cập nhật khi đang chạy).', className='text-muted')
                        ])
                    ])
                ], className='shadow-sm mb-4')
            ], md=8),

            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H6('Bảng dữ liệu mô phỏng')),
                    dbc.CardBody([
                        html.Div(id='predict-data-table', children=[] , className='table-scroll')
                    ])
                ], className='shadow-sm')
            ], md=4)
        ]),

        dcc.Store(id='predict-data-store', data=create_empty_store()),
        dcc.Store(id='predict-running', data=False),
        dcc.Interval(id='predict-interval', interval=2000, n_intervals=0)

    ], fluid=True)
], className='page-container')


@callback(
    Output('predict-running', 'data'),
    Input('start-sim', 'n_clicks'),
    State('predict-running', 'data'),
    prevent_initial_call=True
)
def toggle_running(n_clicks, running):
    return not bool(running)


@callback(
    Output('start-sim', 'children'),
    Input('predict-running', 'data')
)
def update_start_label(running):
    return 'Dừng' if running else 'Bắt đầu'


@callback(
    Output('predict-interval', 'interval'),
    Input('predict-interval-select', 'value')
)
def update_interval_interval(val):
    try:
        return int(val)
    except Exception:
        return 2000


@callback(
    Output('predict-data-store', 'data'),
    [Input('predict-interval', 'n_intervals'), Input('clear-sim', 'n_clicks')],
    [State('predict-running', 'data'), State('predict-data-store', 'data'), State('predict-sigma-select', 'value')]
)
def tick_or_clear(n_intervals, clear_clicks, running, data_store, sigma):
    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate
    trigger = ctx.triggered[0]['prop_id'].split('.')[0]

    if trigger == 'clear-sim':
        return create_empty_store()

    if trigger == 'predict-interval':
        if not running:
            raise PreventUpdate
        try:
            ds = list(data_store or [])
            base = 10.0
            if ds:
                last = float(ds[-1].get('flow_rate', base))
            else:
                last = base
            delta = random.gauss(0, float(sigma or 0.6))
            new_val = max(0.0, last + delta)
            point = {'time': datetime.now().isoformat(), 'flow_rate': round(new_val, 2)}
            ds.append(point)
            if len(ds) > 500:
                ds = ds[-500:]
            return ds
        except Exception:
            return data_store or []

    raise PreventUpdate


@callback(
    Output('predict-flow-chart', 'figure'),
    Input('predict-data-store', 'data')
)
def update_chart(data_store):
    data = data_store or []
    x = [d.get('time') for d in data]
    y = [d.get('flow_rate') for d in data]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=y, mode='lines+markers', name='Lưu lượng', line=dict(color='#1f77b4')))
    fig.update_layout(
        xaxis=dict(title='Thời gian', type='date', showgrid=True, gridcolor='#f0f0f0', tickformat='%H:%M\n%d/%m/%Y'),
        yaxis=dict(title='Lưu lượng (L/s)', showgrid=True, gridcolor='#f0f0f0'),
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(l=40, r=20, t=30, b=40)
    )
    return fig


@callback(
    Output('predict-data-table', 'children'),
    Input('predict-data-store', 'data')
)
def render_table(data_store):
    data = data_store or []
    if not data:
        return html.Div('Chưa có dữ liệu mô phỏng', className='empty-text')
    rows = []
    for idx, d in enumerate(reversed(data[-50:]), start=1):
        rows.append(html.Tr([html.Td(idx), html.Td(d.get('time')), html.Td(d.get('flow_rate'))]))
    table = dbc.Table([html.Thead(html.Tr([html.Th('STT'), html.Th('Thời gian'), html.Th('Lưu lượng (L/s)')])), html.Tbody(rows)], bordered=True, hover=True, responsive=True)
    return html.Div(className='table-scroll', children=[table])