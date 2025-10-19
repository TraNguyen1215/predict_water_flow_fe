from dash import html, dcc
import dash_bootstrap_components as dbc


def create_weather_widget():
    """Return a Dash layout block that shows current weather for user's location.
    """

    card = dbc.Card([
        dbc.CardBody([
            html.Div([
                html.Div([
                    html.H5("Thời tiết địa phương", className='mb-1'),
                    html.H3(id='weather-location', className='mb-0'),
                    html.P(id='weather-localtime', className='text-muted small mt-1')
                ], className='d-inline-block align-middle me-3'),
            ], className='mb-3 d-flex align-items-center justify-content-between'),

            html.Div([
                html.Div([
                    html.Div(id='weather-icon', className='weather-icon'),
                    html.Div(id='weather-main-info', children=[
                        html.H2(id='weather-temp'),
                        html.P(id='weather-desc', className='text-muted')
                    ])
                ], className='weather-left')
            ], className='mb-3'),

            html.Div([
                dbc.Row([
                    dbc.Col(dbc.Button("Xem dự báo", id='show-forecast', color='primary', size='sm'), width='auto'),
                    dbc.Col(dbc.RadioItems(
                        id='forecast-length',
                        options=[{'label': '3 ngày', 'value': 3}, {'label': '7 ngày', 'value': 7}],
                        value=3,
                        inline=True,
                        className='small text-muted'
                    ), className='d-flex align-items-center'),
                ], className='g-2 align-items-center')
            ], className='mb-2'),

            html.Div([
                dbc.Row([
                    dbc.Col(html.Div([html.Small('Nhiệt độ'), html.Div(id='stat-temp', className='fw-bold')]), xs=6, sm=3),
                    dbc.Col(html.Div([html.Small('Độ ẩm'), html.Div(id='stat-humidity', className='fw-bold')]), xs=6, sm=3),
                    dbc.Col(html.Div([html.Small('Áp suất'), html.Div(id='stat-pressure', className='fw-bold')]), xs=6, sm=3),
                    dbc.Col(html.Div([html.Small('Mưa (mm)'), html.Div(id='stat-precip', className='fw-bold')]), xs=6, sm=3),
                ], className='text-center')
            ], className='mb-3'),

            html.Div(id='weather-forecast', className='weather-forecast'),

            html.Div(id='weather-updated', className='weather-updated'),
            html.Pre(id='weather-raw', style={'display': 'none', 'whiteSpace': 'pre-wrap', 'wordBreak': 'break-word'})
        ])
    ], className='shadow-sm')

    return html.Div([
        dcc.Store(id='weather-store'),
        html.Div(id='weather-container', children=[card], className='text-start')
    ], className='weather-widget')
