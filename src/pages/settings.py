from dash import html, dcc
import dash_bootstrap_components as dbc
from components.navbar import create_navbar

layout = html.Div([
    create_navbar(is_authenticated=True),
    dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H2([
                    html.I(className="fas fa-cog me-3"),
                    "Cài Đặt"
                ], className="mb-4")
            ], width=12)
        ]),
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.P("Giao diện Cài đặt đã được chuyển sang trang Tài khoản."),
                        dbc.Button("Mở Cài đặt", href="/account#settings", color="primary")
                    ])
                ], className="shadow-sm")
            ], md=8)
        ])
    ], fluid=True, className="py-4")
])
