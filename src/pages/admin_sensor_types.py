from dash import html, dcc, callback, Input, Output, State
import dash_bootstrap_components as dbc
from components.navbar import create_navbar


layout = html.Div([
    create_navbar(is_authenticated=True, is_admin=True),
    dcc.Location(id='admin-sensor-types-url', refresh=False),
    dbc.Container([
        dbc.Row([
            dbc.Col(html.H2([html.I(className='fas fa-thermometer-half me-2'), 'Loại cảm biến']), md=9),
        ], className='my-3'),

        dbc.Row([
            dbc.Col(html.P('Danh sách loại cảm biến sẽ hiển thị ở đây. Hiện là placeholder.'), md=12)
        ])
    ], fluid=True, className='py-4')
])
