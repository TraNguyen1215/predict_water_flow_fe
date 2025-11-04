from dash import html, dcc, callback, Input, Output, State
import dash_bootstrap_components as dbc
import dash
from components.navbar import create_navbar
import base64


layout = html.Div([
    create_navbar(is_authenticated=True, is_admin=True),
    dcc.Location(id='admin-models-url', refresh=False),
    dbc.Toast(
        id='admin-models-toast',
        header='Thông báo',
        is_open=False,
        dismissable=True,
        duration=3500,
        icon='success',
        children='',
        style={'position': 'fixed', 'top': '80px', 'right': '24px', 'zIndex': 2100}
    ),
    dbc.Container([
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.Span('Tải lên mô hình mới', className='user-table-title')),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                dcc.Upload(
                                    id='admin-model-upload',
                                    children=html.Div(id='model-upload-display', children=[
                                        html.I(className='fas fa-file-upload me-2'),
                                        html.Span('Kéo thả tệp ở đây hoặc bấm để chọn'),
                                        html.Br(),
                                        html.Small('Chỉ chấp nhận file .h5, .pkl', className='text-muted')
                                    ]),
                                    style={
                                        'border': '2px dashed #dee2e6',
                                        'borderRadius': '8px',
                                        'padding': '30px 20px',
                                        'textAlign': 'center',
                                        'cursor': 'pointer',
                                        'backgroundColor': '#f8f9fa',
                                        'transition': 'all 0.3s ease'
                                    },
                                    multiple=False
                                )
                            ], md=12, className='mb-4')
                        ]),
                        dbc.Row([
                            dbc.Col([
                                dbc.Label('Tên mô hình', className='mb-2 fw-medium'),
                                dbc.Input(
                                    id='admin-model-name',
                                    placeholder='Nhập tên mô hình...',
                                    className='mb-3'
                                )
                            ], md=4),
                            dbc.Col([
                                dbc.Label('Phiên bản', className='mb-2 fw-medium'),
                                dbc.Input(
                                    id='admin-model-version',
                                    placeholder='Ví dụ: 1.0.0',
                                    className='mb-3'
                                )
                            ], md=4),
                            dbc.Col([
                                dbc.Label('Mô tả', className='mb-2 fw-medium'),
                                dbc.Textarea(
                                    id='admin-model-description',
                                    placeholder='Nhập mô tả mô hình (tùy chọn)...',
                                    className='mb-3',
                                    style={'height': '50px', 'resize': 'none'}
                                )
                            ], md=4),
                        ]),
                        dbc.Row([
                            dbc.Col([
                                dbc.Button(
                                    [html.I(className='fas fa-upload me-2'), 'Tải lên'],
                                    id='admin-model-upload-btn',
                                    color='primary',
                                    className='d-flex align-items-center justify-content-center h-100 px-4'
                                )
                            ], md=12, className='d-flex align-items-center justify-content-center')
                        ])
                    ])
                ], className='mb-4 user-table-card', style={'marginTop': '70px'})
            ], md=12)
        ]),

        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.Span('Danh sách mô hình', className='user-table-title')),
                    dbc.CardBody(
                        id='admin-models-table-container',
                        children=[
                            html.Div(id='admin-models-table', className='table-responsive')
                        ]
                    )
                ], className='user-table-card')
            ], md=12)
        ])
    ], fluid=True, className='py-4')
])