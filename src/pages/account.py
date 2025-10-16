from dash import html, dcc, callback, Input, Output, State
import dash_bootstrap_components as dbc
import dash
from components.navbar import create_navbar
from utils.auth import get_user_info, update_user_info

layout = html.Div([
    create_navbar(is_authenticated=True),
    
    dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H2([
                    html.I(className="fas fa-user-circle me-3"),
                    "Thông Tin Tài Khoản"
                ], className="mb-4")
            ], width=12)
        ]),
        
        dbc.Row([
            # Sidebar
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.I(className="fas fa-user-circle fa-5x text-primary mb-3"),
                            html.H4(id='profile-username', className="mb-2"),
                            html.P(id='profile-email', className="text-muted mb-4"),
                        ], className="text-center"),
                        
                        dbc.Nav([
                            dbc.NavLink([
                                html.I(className="fas fa-info-circle me-2"),
                                "Thông tin cá nhân"
                            ], active=True, href="#", className="mb-2"),
                            dbc.NavLink([
                                html.I(className="fas fa-lock me-2"),
                                "Đổi mật khẩu"
                            ], href="#", className="mb-2"),
                            dbc.NavLink([
                                html.I(className="fas fa-history me-2"),
                                "Lịch sử hoạt động"
                            ], href="#", className="mb-2"),
                        ], vertical=True, pills=True)
                    ])
                ], className="shadow-sm")
            ], md=4, className="mb-4"),
            
            # Main content
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5([
                            html.I(className="fas fa-edit me-2"),
                            "Cập Nhật Thông Tin"
                        ], className="mb-0")
                    ]),
                    dbc.CardBody([
                        dcc.Loading(
                            id='loading-account-message',
                            type='default',
                            children=html.Div(id='account-message', className="mb-3")
                        ),
                        
                        dbc.Form([
                            dbc.Row([
                                dbc.Col([
                                    dbc.Label("Họ và tên", className="fw-bold"),
                                    dbc.Input(
                                        id='account-fullname',
                                        type='text',
                                        placeholder='Nhập họ và tên',
                                        className="mb-3"
                                    ),
                                ], md=6)
                            ]),
                            
                            dbc.Row([
                                dbc.Col([
                                    dbc.Label("Email", className="fw-bold"),
                                    dbc.Input(
                                        id='account-email',
                                        type='email',
                                        placeholder='Nhập email',
                                        className="mb-3",
                                        disabled=True
                                    ),
                                ], md=6),
                                
                                dbc.Col([
                                    dbc.Label("Số điện thoại", className="fw-bold"),
                                    dbc.Input(
                                        id='account-phone',
                                        type='tel',
                                        placeholder='Nhập số điện thoại',
                                        className="mb-3"
                                    ),
                                ], md=6)
                            ]),
                            
                            dbc.Row([
                                dbc.Col([
                                    dbc.Button(
                                        [html.I(className="fas fa-save me-2"), "Lưu Thay Đổi"],
                                        id='save-account-btn',
                                        color='primary',
                                        className="px-4"
                                    ),
                                ], width=12)
                            ]),
                        ])
                    ])
                ], className="shadow-sm mb-4"),
                
                # Statistics
                dbc.Card([
                    dbc.CardHeader([
                        html.H5([
                            html.I(className="fas fa-chart-bar me-2"),
                            "Thống Kê Hoạt Động"
                        ], className="mb-0")
                    ]),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                html.Div([
                                    html.I(className="fas fa-eye fa-2x text-primary mb-2"),
                                    html.H4("125", className="mb-1"),
                                    html.P("Lượt xem", className="text-muted mb-0 small")
                                ], className="text-center")
                            ], md=4),
                            
                            dbc.Col([
                                html.Div([
                                    html.I(className="fas fa-calendar fa-2x text-success mb-2"),
                                    html.H4("30", className="mb-1"),
                                    html.P("Ngày hoạt động", className="text-muted mb-0 small")
                                ], className="text-center")
                            ], md=4),
                            
                            dbc.Col([
                                html.Div([
                                    html.I(className="fas fa-clock fa-2x text-warning mb-2"),
                                    html.H4("15h", className="mb-1"),
                                    html.P("Thời gian sử dụng", className="text-muted mb-0 small")
                                ], className="text-center")
                            ], md=4),
                        ])
                    ])
                ], className="shadow-sm")
            ], md=8)
        ])
    ], fluid=True, className="py-4")
])

@callback(
    [Output('profile-username', 'children'),
     Output('profile-email', 'children'),
     Output('account-fullname', 'value'),
     Output('account-email', 'value'),
     Output('account-phone', 'value')],
    Input('url', 'pathname'),
    State('session-store', 'data')
)
def load_user_info(pathname, session_data):
    if not session_data or not session_data.get('authenticated'):
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
    
    username = session_data.get('username')
    user_info = get_user_info(username)
    
    return (
        username,
        user_info.get('email', ''),
        user_info.get('full_name', ''),
        user_info.get('email', ''),
        user_info.get('phone', '')
    )

@callback(
    Output('account-message', 'children'),
    Input('save-account-btn', 'n_clicks'),
    [State('account-fullname', 'value'),
     State('account-phone', 'value'),
     State('session-store', 'data')],
    prevent_initial_call=True
)
def save_account_info(n_clicks, fullname, phone, session_data):
    if not session_data or not session_data.get('authenticated'):
        return dbc.Alert("Phiên đăng nhập đã hết hạn!", color="danger", dismissable=True)
    
    username = session_data.get('username')
    user_data = {
        'full_name': fullname or '',
        'phone': phone or ''
    }
    
    success, message = update_user_info(username, user_data)
    
    if success:
        return dbc.Alert(message, color="success", dismissable=True)
    else:
        return dbc.Alert(message, color="danger", dismissable=True)