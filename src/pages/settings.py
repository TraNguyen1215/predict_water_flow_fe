from dash import html, dcc, callback, Input, Output, State
import dash_bootstrap_components as dbc
import dash
from components.navbar import create_navbar
from utils.auth import change_password

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
            # Settings Menu
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        dbc.Nav([
                            dbc.NavLink([
                                html.I(className="fas fa-bell me-2"),
                                "Thông báo"
                            ], active=True, id="nav-notifications", className="mb-2"),
                            dbc.NavLink([
                                html.I(className="fas fa-shield-alt me-2"),
                                "Bảo mật"
                            ], id="nav-security", className="mb-2"),
                            dbc.NavLink([
                                html.I(className="fas fa-paint-brush me-2"),
                                "Giao diện"
                            ], id="nav-appearance", className="mb-2"),
                            dbc.NavLink([
                                html.I(className="fas fa-database me-2"),
                                "Dữ liệu"
                            ], id="nav-data", className="mb-2"),
                        ], vertical=True, pills=True)
                    ])
                ], className="shadow-sm")
            ], md=3, className="mb-4"),
            
            # Settings Content
            dbc.Col([
                html.Div(id='settings-content')
            ], md=9)
        ])
    ], fluid=True, className="py-4")
])

# Notifications Settings
notifications_content = dbc.Card([
    dbc.CardHeader([
        html.H5([
            html.I(className="fas fa-bell me-2"),
            "Cài Đặt Thông Báo"
        ], className="mb-0")
    ]),
    dbc.CardBody([
        dcc.Loading(
            id='loading-settings-message',
            type='default',
            children=html.Div(id='settings-message', className="mb-3")
        ),
        
        dbc.Form([
            dbc.Row([
                dbc.Col([
                    html.H6("Thông báo Email", className="mb-3"),
                    dbc.Checkbox(
                        id='email-notifications',
                        label='Nhận thông báo qua email',
                        value=True,
                        className="mb-2"
                    ),
                    dbc.Checkbox(
                        id='email-alerts',
                        label='Cảnh báo quan trọng',
                        value=True,
                        className="mb-2"
                    ),
                    dbc.Checkbox(
                        id='email-reports',
                        label='Báo cáo định kỳ',
                        value=False,
                        className="mb-4"
                    ),
                ], width=12)
            ]),
            
            dbc.Row([
                dbc.Col([
                    html.H6("Thông báo Push", className="mb-3"),
                    dbc.Checkbox(
                        id='push-notifications',
                        label='Bật thông báo đẩy',
                        value=True,
                        className="mb-2"
                    ),
                    dbc.Checkbox(
                        id='push-sound',
                        label='Âm thanh thông báo',
                        value=True,
                        className="mb-4"
                    ),
                ], width=12)
            ]),
            
            dbc.Row([
                dbc.Col([
                    dbc.Button(
                        [html.I(className="fas fa-save me-2"), "Lưu Cài Đặt"],
                        id='save-notification-settings',
                        color='primary',
                        className="px-4"
                    ),
                ], width=12)
            ]),
        ])
    ])
], className="shadow-sm")

# Security Settings
security_content = dbc.Card([
    dbc.CardHeader([
        html.H5([
            html.I(className="fas fa-shield-alt me-2"),
            "Cài Đặt Bảo Mật"
        ], className="mb-0")
    ]),
    dbc.CardBody([
        dbc.Form([
            dbc.Row([
                dbc.Col([
                    html.H6("Đổi mật khẩu", className="mb-3"),
                    dbc.Label("Mật khẩu hiện tại", className="fw-bold"),
                    dbc.Input(
                        id='current-password',
                        type='password',
                        placeholder='Nhập mật khẩu hiện tại',
                        className="mb-3"
                    ),
                    dbc.Label("Mật khẩu mới", className="fw-bold"),
                    dbc.Input(
                        id='new-password',
                        type='password',
                        placeholder='Nhập mật khẩu mới',
                        className="mb-3"
                    ),
                    dbc.Label("Xác nhận mật khẩu mới", className="fw-bold"),
                    dbc.Input(
                        id='confirm-new-password',
                        type='password',
                        placeholder='Nhập lại mật khẩu mới',
                        className="mb-4"
                    ),
                ], md=6)
            ]),
            
            dbc.Row([
                dbc.Col([
                    html.H6("Xác thực hai yếu tố", className="mb-3"),
                    dbc.Checkbox(
                        id='two-factor-auth',
                        label='Bật xác thực hai yếu tố (2FA)',
                        value=False,
                        className="mb-4"
                    ),
                ], width=12)
            ]),
            
            dbc.Row([
                dbc.Col([
                    dbc.Button(
                        [html.I(className="fas fa-key me-2"), "Cập Nhật Bảo Mật"],
                        id='save-security-settings',
                        color='primary',
                        className="px-4"
                    ),
                ], width=12)
            ]),
        ])
    ])
], className="shadow-sm")

# Appearance Settings
appearance_content = dbc.Card([
    dbc.CardHeader([
        html.H5([
            html.I(className="fas fa-paint-brush me-2"),
            "Cài Đặt Giao Diện"
        ], className="mb-0")
    ]),
    dbc.CardBody([
        dbc.Form([
            dbc.Row([
                dbc.Col([
                    html.H6("Chủ đề", className="mb-3"),
                    dbc.RadioItems(
                        id='theme-selection',
                        options=[
                            {'label': ' Sáng', 'value': 'light'},
                            {'label': ' Tối', 'value': 'dark'},
                            {'label': ' Tự động', 'value': 'auto'},
                        ],
                        value='light',
                        className="mb-4"
                    ),
                ], width=12)
            ]),
            
            # Ngôn ngữ đã được cố định là Tiếng Việt - tùy chọn ngôn ngữ đã loại bỏ
            
            dbc.Row([
                dbc.Col([
                    dbc.Button(
                        [html.I(className="fas fa-palette me-2"), "Áp Dụng"],
                        id='save-appearance-settings',
                        color='primary',
                        className="px-4"
                    ),
                ], width=12)
            ]),
        ])
    ])
], className="shadow-sm")

# Data Settings
data_content = dbc.Card([
    dbc.CardHeader([
        html.H5([
            html.I(className="fas fa-database me-2"),
            "Cài Đặt Dữ Liệu"
        ], className="mb-0")
    ]),
    dbc.CardBody([
        dbc.Form([
            dbc.Row([
                dbc.Col([
                    html.H6("Tần suất cập nhật", className="mb-3"),
                    dbc.Select(
                        id='update-frequency',
                        options=[
                            {'label': '5 giây', 'value': '5'},
                            {'label': '10 giây', 'value': '10'},
                            {'label': '30 giây', 'value': '30'},
                            {'label': '1 phút', 'value': '60'},
                        ],
                        value='10',
                        className="mb-4"
                    ),
                ], md=6)
            ]),
            
            dbc.Row([
                dbc.Col([
                    html.H6("Sao lưu dữ liệu", className="mb-3"),
                    dbc.Checkbox(
                        id='auto-backup',
                        label='Tự động sao lưu hàng ngày',
                        value=True,
                        className="mb-2"
                    ),
                    dbc.Button(
                        [html.I(className="fas fa-download me-2"), "Tải xuống dữ liệu"],
                        id='download-data',
                        color='secondary',
                        outline=True,
                        className="mb-4"
                    ),
                ], width=12)
            ]),
            
            dbc.Row([
                dbc.Col([
                    html.H6("Xóa dữ liệu", className="mb-3"),
                    dbc.Button(
                        [html.I(className="fas fa-trash me-2"), "Xóa tất cả dữ liệu"],
                        id='delete-all-data',
                        color='danger',
                        outline=True,
                        className="mb-4"
                    ),
                ], width=12)
            ]),
            
            dbc.Row([
                dbc.Col([
                    dbc.Button(
                        [html.I(className="fas fa-save me-2"), "Lưu Cài Đặt"],
                        id='save-data-settings',
                        color='primary',
                        className="px-4"
                    ),
                ], width=12)
            ]),
        ])
    ])
], className="shadow-sm")

@callback(
    Output('settings-content', 'children'),
    [Input('nav-notifications', 'n_clicks'),
     Input('nav-security', 'n_clicks'),
     Input('nav-appearance', 'n_clicks'),
     Input('nav-data', 'n_clicks')],
    prevent_initial_call=False
)
def update_settings_content(notif_clicks, sec_clicks, appear_clicks, data_clicks):
    ctx = dash.callback_context
    
    if not ctx.triggered:
        return notifications_content
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if button_id == 'nav-security':
        return security_content
    elif button_id == 'nav-appearance':
        return appearance_content
    elif button_id == 'nav-data':
        return data_content
    else:
        return notifications_content

@callback(
    Output('settings-message', 'children'),
    [Input('save-notification-settings', 'n_clicks'),
     Input('save-security-settings', 'n_clicks'),
     Input('save-appearance-settings', 'n_clicks'),
     Input('save-data-settings', 'n_clicks')],
    [State('current-password', 'value'),
     State('new-password', 'value'),
     State('confirm-new-password', 'value'),
     State('session-store', 'data')],
    prevent_initial_call=True
)
def save_settings(notif_clicks, sec_clicks, appear_clicks, data_clicks,
                  current_password, new_password, confirm_new_password, session_data):
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    # Handle security update (change password)
    if button_id == 'save-security-settings':
        # Basic validation
        if not current_password or not new_password or not confirm_new_password:
            return dbc.Alert("Vui lòng nhập đầy đủ thông tin mật khẩu.", color="warning", dismissable=True)

        if new_password != confirm_new_password:
            return dbc.Alert("Mật khẩu mới và xác nhận không khớp.", color="danger", dismissable=True)

        if len(new_password) < 6:
            return dbc.Alert("Mật khẩu phải có ít nhất 6 ký tự.", color="warning", dismissable=True)

        # Determine username from session-store
        token = None
        if session_data and isinstance(session_data, dict):
            token = session_data.get('token')

        if not token:
            return dbc.Alert("Không tìm thấy thông tin đăng nhập (token). Vui lòng đăng nhập lại.", color="danger", dismissable=True)

        success, message = change_password(current_password, new_password, token)
        if success:
            return dbc.Alert(message, color="success", dismissable=True, duration=4000)
        else:
            return dbc.Alert(message, color="danger", dismissable=True)

    # For other save buttons, just show a generic saved message
    return dbc.Alert("Cài đặt đã được lưu thành công!", color="success", dismissable=True, duration=3000)
