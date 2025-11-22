from dash import html, dcc, callback, Input, Output, State
import dash_bootstrap_components as dbc
from components.navbar import create_navbar
import dash
from datetime import datetime

layout = html.Div([
    create_navbar(is_authenticated=True),
    dcc.Location(id='planting-log-url', refresh=False),

    dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H2([html.I(className="fas fa-leaf me-3"), "Nhật ký gieo trồng"]),
                html.P("Ghi lại hoạt động gieo trồng của bạn.")
            ], width=12)
        ], className='mb-3'),

        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5("Thêm mục nhật ký")),
                    dbc.CardBody([
                        dbc.Form([
                            dbc.Row([
                                dbc.Col([
                                    dbc.Label("Ngày"),
                                    dbc.Input(id='log-date', type='date', value=datetime.now().strftime('%Y-%m-%d'))
                                ], md=4),
                                dbc.Col([
                                    dbc.Label("Cây trồng"),
                                    dbc.Input(id='log-crop', placeholder='Ví dụ: Cà chua')
                                ], md=4),
                                dbc.Col([
                                    dbc.Label("Số lượng/diện tích"),
                                    dbc.Input(id='log-qty', placeholder='Ví dụ: 10 cây / 5m²')
                                ], md=4),
                            ], className='mb-2'),

                            dbc.Row([
                                dbc.Col([
                                    dbc.Label("Ghi chú"),
                                    dbc.Textarea(id='log-notes', placeholder='Ghi chú thêm...', className='mb-2')
                                ], md=12)
                            ]),

                            dbc.Row([
                                dbc.Col(dbc.Button('Thêm', id='add-log-btn', color='primary'), width=3),
                                dbc.Col(html.Div(id='add-log-status'), width=9)
                            ])
                        ])
                    ])
                ], className='shadow-sm')
            ], md=4),

            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5('Danh sách nhật ký')),
                    dbc.CardBody([
                        html.Div(id='planting-log-list')
                    ])
                ], className='shadow-sm')
            ], md=8)
        ])

    ], fluid=True, className='py-4')
])


@callback(
    Output('planting-log-store', 'data', allow_duplicate=True),
    Output('add-log-status', 'children'),
    Input('add-log-btn', 'n_clicks'),
    State('log-date', 'value'),
    State('log-crop', 'value'),
    State('log-qty', 'value'),
    State('log-notes', 'value'),
    State('planting-log-store', 'data'),
    prevent_initial_call=True
)
def add_log(n_clicks, date, crop, qty, notes, current_data):
    if not current_data or not isinstance(current_data, list):
        current_data = []
    entry = {
        'id': str(datetime.utcnow().timestamp()).replace('.', ''),
        'date': date or datetime.now().strftime('%Y-%m-%d'),
        'crop': crop or '',
        'qty': qty or '',
        'notes': notes or ''
    }
    current_data.insert(0, entry)
    return current_data, dbc.Alert('Đã thêm mục nhật ký.', color='success', duration=2500)


@callback(
    Output('planting-log-list', 'children'),
    Input('planting-log-store', 'data')
)
def render_list(data):
    if not data:
        return html.Div('Chưa có mục nhật ký nào.', className='text-muted')
    items = []
    for item in data:
        items.append(
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.Strong(item.get('crop') or '—'),
                        html.Span(item.get('date') or '', className='text-muted ms-3')
                    ], className='d-flex justify-content-between'),
                    html.Div(item.get('qty') or ''),
                    html.P(item.get('notes') or '', className='small text-muted mt-2')
                ])
            ], className='mb-2')
        )
    return items
