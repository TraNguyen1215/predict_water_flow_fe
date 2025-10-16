from dash import html, dcc, callback, Input, Output, State
import dash_bootstrap_components as dbc
import dash
from components.navbar import create_navbar
from utils.auth import register_user

layout = html.Div([
    create_navbar(is_authenticated=False),
    
    dbc.Container([
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.I(className="fas fa-user-plus fa-3x text-primary mb-4"),
                            html.H2("Đăng Ký Tài Khoản", className="text-center mb-4"),
                        ], className="text-center"),
                        
                        dcc.Loading(
                            id='loading-register-message',
                            type='default',
                            children=html.Div(id='register-message', className="mb-3")
                        ),
                        
                        dbc.Form([
                            dbc.Row([
                                dbc.Col([
                                    dbc.Label("Tên đăng nhập", className="fw-bold"),
                                    dbc.Input(
                                        id='register-username',
                                        type='text',
                                        placeholder='Nhập tên đăng nhập',
                                        className="mb-3"
                                    ),
                                ], width=12)
                            ]),
                            
                            dbc.Row([
                                dbc.Col([
                                    dbc.Label("Email", className="fw-bold"),
                                    dbc.Input(
                                        id='register-email',
                                        type='email',
                                        placeholder='Nhập email',
                                        className="mb-3"
                                    ),
                                ], width=12)
                            ]),
                            
                            dbc.Row([
                                dbc.Col([
                                    dbc.Label("Mật khẩu", className="fw-bold"),
                                    dbc.Input(
                                        id='register-password',
                                        type='password',
                                        placeholder='Nhập mật khẩu',
                                        className="mb-3"
                                    ),
                                ], width=12)
                            ]),
                            
                            dbc.Row([
                                dbc.Col([
                                    dbc.Label("Xác nhận mật khẩu", className="fw-bold"),
                                    dbc.Input(
                                        id='register-confirm-password',
                                        type='password',
                                        placeholder='Nhập lại mật khẩu',
                                        className="mb-3"
                                    ),
                                ], width=12)
                            ]),
                            
                            dbc.Row([
                                dbc.Col([
                                    dbc.Checkbox(
                                        id='accept-terms',
                                        label='Tôi đồng ý với điều khoản sử dụng',
                                        value=False,
                                        className="mb-3"
                                    ),
                                ], width=12)
                            ]),
                            
                            dbc.Row([
                                dbc.Col([
                                    dbc.Button(
                                        [html.I(className="fas fa-user-plus me-2"), "Đăng Ký"],
                                        id='register-btn',
                                        color='success',
                                        className="w-100 py-2 fw-bold",
                                        size="lg"
                                    ),
                                ], width=12)
                            ]),
                        ]),
                        
                        html.Hr(className="my-4"),
                        
                        html.Div([
                            html.P([
                                "Đã có tài khoản? ",
                                html.A("Đăng nhập ngay", href="/login", className="text-primary fw-bold")
                            ], className="text-center mb-0")
                        ])
                    ])
                ], className="shadow-lg login-card")
            ], md=6, lg=5, className="mx-auto")
        ], className="min-vh-100 align-items-center")
    ], fluid=True)
], className="register-page")

@callback(
    [Output('register-message', 'children'),
     Output('url', 'pathname', allow_duplicate=True)],
    Input('register-btn', 'n_clicks'),
    [State('register-username', 'value'),
     State('register-email', 'value'),
     State('register-password', 'value'),
     State('register-confirm-password', 'value'),
     State('accept-terms', 'value')],
    prevent_initial_call=True
)
def register_new_user(n_clicks, username, email, password, confirm_password, accept_terms):
    if not username or not email or not password or not confirm_password:
        return dbc.Alert("Vui lòng nhập đầy đủ thông tin!", color="warning", dismissable=True), dash.no_update
    
    if not accept_terms:
        return dbc.Alert("Vui lòng đồng ý với điều khoản sử dụng!", color="warning", dismissable=True), dash.no_update
    
    if password != confirm_password:
        return dbc.Alert("Mật khẩu xác nhận không khớp!", color="danger", dismissable=True), dash.no_update
    
    if len(password) < 6:
        return dbc.Alert("Mật khẩu phải có ít nhất 6 ký tự!", color="warning", dismissable=True), dash.no_update
    
    success, message = register_user(username, email, password)
    
    if success:
        return dbc.Alert(message + " Đang chuyển đến trang đăng nhập...", color="success", dismissable=True), '/login'
    else:
        return dbc.Alert(message, color="danger", dismissable=True), dash.no_update
