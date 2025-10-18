from dash import html, dcc, callback, Input, Output, State
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
import dash
from components.navbar import create_navbar
from utils.auth import authenticate_user

layout = html.Div([
    create_navbar(is_authenticated=False),
    
    dbc.Container([
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.I(className="fas fa-water fa-3x text-primary mb-4"),
                            html.H2("Đăng Nhập", className="text-center mb-4"),
                        ], className="text-center"),
                        
                        dcc.Loading(
                            id='loading-login-message',
                            type='default',
                            children=html.Div(id='login-message', className="mb-3")
                        ),
                        
                        dbc.Form([
                            dbc.Row([
                                dbc.Col([
                                    dbc.Label("Tên đăng nhập", className="fw-bold"),
                                    dbc.Input(
                                        id='login-username',
                                        type='text',
                                        placeholder='Nhập tên đăng nhập',
                                        className="mb-3"
                                    ),
                                ], width=12)
                            ]),
                            
                            dbc.Row([
                                dbc.Col([
                                    dbc.Label("Mật khẩu", className="fw-bold"),
                                    dbc.Input(
                                        id='login-password',
                                        type='password',
                                        placeholder='Nhập mật khẩu',
                                        className="mb-3"
                                    ),
                                ], width=12)
                            ]),
                            
                            dbc.Row([
                                dbc.Col([
                                    dbc.Checkbox(
                                        id='remember-me',
                                        label='Ghi nhớ đăng nhập',
                                        value=False,
                                        className="mb-3"
                                    ),
                                ], width=12)
                            ]),
                            
                            dbc.Row([
                                dbc.Col([
                                    dbc.Button(
                                        [html.I(className="fas fa-sign-in-alt me-2"), "Đăng Nhập"],
                                        id='login-btn',
                                        color='primary',
                                        className="w-100 py-2 fw-bold",
                                        size="lg"
                                    ),
                                ], width=12)
                            ]),
                        ]),
                        
                        html.Hr(className="my-4"),
                        
                        html.Div([
                            html.P([
                                "Chưa có tài khoản? ",
                                html.A("Đăng ký ngay", href="/register", className="text-primary fw-bold")
                            ], className="text-center mb-0")
                        ])
                    ])
                ], className="shadow-lg login-card")
            ], md=6, lg=5, className="mx-auto")
        ], className="min-vh-100 align-items-center")
    ], fluid=True)
], className="login-page")

@callback(
    [Output('login-message', 'children'),
     Output('session-store', 'data'),
     Output('url', 'pathname')],
    Input('login-btn', 'n_clicks'),
    [State('login-username', 'value'),
     State('login-password', 'value')],
    prevent_initial_call=True
)
def login_user(n_clicks, username, password):
    if not username or not password:
        return dbc.Alert("Vui lòng nhập đầy đủ thông tin!", color="warning", dismissable=True), dash.no_update, dash.no_update
    
    success, message, token = authenticate_user(username, password)
    
    if success:
        session_data = {
            'authenticated': True,
            'username': username,
            'token': token
        }
        return dbc.Alert(message, color="success", dismissable=True), session_data, '/'
    else:
        return dbc.Alert(message, color="danger", dismissable=True), dash.no_update, dash.no_update