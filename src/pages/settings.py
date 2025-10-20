from dash import html, dcc, callback, Input, Output, State
import dash_bootstrap_components as dbc
import dash
from components.navbar import create_navbar
from utils.auth import change_password, get_user_info, update_user_info

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
                        html.Div([
                            html.Img(id='profile-avatar', src='', className="rounded-circle mb-3", style={'width':'96px','height':'96px','object-fit':'cover'}),
                            html.H4(id='profile-username', className="mb-2"),
                            html.Div(id='profile-status', className="mb-2"),
                            html.Div([html.Span("Được tạo: "), html.Span(id='profile-created')], className="small text-muted"),
                            html.Div([html.Span("Lần đăng nhập: "), html.Span(id='profile-lastlogin')], className="small text-muted mb-2"),
                            html.P(id='profile-address', className="text-muted mb-3"),
                        ], className="text-center"),

                        dbc.Nav([
                            dbc.NavLink([
                                html.I(className="fas fa-user-circle me-2"),
                                "Tài khoản"
                            ], id="nav-account", className="mb-2"),
                            dbc.NavLink([
                                "Đổi mật khẩu"
                            ], id="nav-security", className="mb-2"),
                            dbc.NavLink([
                                html.I(className="fas fa-bell me-2"),
                                "Thông báo"
                            ], id="nav-notifications", className="mb-2"),
                            dbc.NavLink([
                                html.I(className="fas fa-paint-brush me-2"),
                                "Giao diện"
                            ], id="nav-appearance", className="mb-2"),
                        ], vertical=True, pills=True, className="settings-nav")
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
            "Đổi mật khẩu"
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
            ]),

            dbc.Row([
                dbc.Col([
                    dbc.Button(
                        ["Lưu mật khẩu"],
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

# Data Settings removed as requested

# Account content (merged from account.py)
account_content = html.Div([
    dbc.Card([
        dbc.CardHeader(html.H5([html.I(className="fas fa-user me-2"), "Thông Tin Tài Khoản"], className="mb-0")),
        dbc.CardBody([
            dcc.Loading(id='loading-account-message', type='default', children=html.Div(id='account-message', className="mb-3")),
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.Img(id='profile-avatar', src='', className='rounded-circle', style={'width':'120px','height':'120px','object-fit':'cover'}),
                        html.H4(id='profile-username', className='mt-3 mb-1'),
                        html.Div(id='profile-status', className='text-muted')
                    ], className='text-center')
                ], md=4),
                dbc.Col([
                    dbc.ListGroup([
                        dbc.ListGroupItem([html.Strong("Họ và tên: "), html.Span(id='profile-username-item')]),
                        dbc.ListGroupItem([html.Strong("Số điện thoại: "), html.Span(id='profile-phone')]),
                        dbc.ListGroupItem([html.Strong("Địa chỉ: "), html.Span(id='profile-address')]),
                        dbc.ListGroupItem([html.Strong("Trạng thái: "), html.Span(id='profile-status-item')]),
                        dbc.ListGroupItem([html.Strong("Tạo lúc: "), html.Span(id='profile-created')]),
                        dbc.ListGroupItem([html.Strong("Lần đăng nhập cuối: "), html.Span(id='profile-lastlogin')]),
                    ])
                ], md=8)
            ])
        ])
    ], className="shadow-sm p-3")
])

@callback(
    [Output('settings-content', 'children'),
     Output('nav-account', 'active'),
     Output('nav-security', 'active'),
     Output('nav-notifications', 'active'),
     Output('nav-appearance', 'active')],
    [Input('nav-account', 'n_clicks'),
     Input('nav-security', 'n_clicks'),
     Input('nav-notifications', 'n_clicks'),
     Input('nav-appearance', 'n_clicks')],
    prevent_initial_call=False
)
def update_settings_content(account_clicks, sec_clicks, notif_clicks, appear_clicks):
    """Return the content for the settings pane and set which nav link is active.

    Returns: (content, notif_active, sec_active, appear_active)
    """
    ctx = dash.callback_context

    account_active = sec_active = notif_active = appear_active = False

    if not ctx.triggered:
        account_active = True
        return account_content, account_active, sec_active, notif_active, appear_active

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if button_id == 'nav-account':
        account_active = True
        return account_content, account_active, sec_active, notif_active, appear_active
    if button_id == 'nav-security':
        sec_active = True
        return security_content, account_active, sec_active, notif_active, appear_active
    elif button_id == 'nav-notifications':
        notif_active = True
        return notifications_content, account_active, sec_active, notif_active, appear_active
    elif button_id == 'nav-appearance':
        appear_active = True
        return appearance_content, account_active, sec_active, notif_active, appear_active
    else:
        account_active = True
        return account_content, account_active, sec_active, notif_active, appear_active

@callback(
    Output('settings-message', 'children'),
    [Input('save-notification-settings', 'n_clicks'),
     Input('save-security-settings', 'n_clicks'),
     Input('save-appearance-settings', 'n_clicks')],
    [State('current-password', 'value'),
     State('new-password', 'value'),
     State('confirm-new-password', 'value'),
     State('session-store', 'data')],
    prevent_initial_call=True
)
def save_settings(notif_clicks, sec_clicks, appear_clicks,
                  current_password, new_password, confirm_new_password, session_data):
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if button_id == 'save-security-settings':
        if not current_password or not new_password or not confirm_new_password:
            return dbc.Alert("Vui lòng nhập đầy đủ thông tin mật khẩu.", color="warning", dismissable=True)

        if new_password != confirm_new_password:
            return dbc.Alert("Mật khẩu mới và xác nhận không khớp.", color="danger", dismissable=True)

        if len(new_password) < 6:
            return dbc.Alert("Mật khẩu phải có ít nhất 6 ký tự.", color="warning", dismissable=True)

        token = None
        if session_data and isinstance(session_data, dict):
            token = session_data.get('token')

        if not token:
            return dbc.Alert("Không tìm thấy thông tin đăng nhập. Vui lòng đăng nhập lại.", color="danger", dismissable=True)

        success, message = change_password(current_password, new_password, token)
        if success:
            return dbc.Alert(message, color="success", dismissable=True, duration=4000)
        else:
            return dbc.Alert(message, color="danger", dismissable=True)

    return dbc.Alert("Cài đặt đã được lưu thành công!", color="success", dismissable=True, duration=3000)


@callback(
    [Output('profile-avatar', 'src'),
        Output('profile-username', 'children'),
        Output('profile-status', 'children'),
        Output('profile-created', 'children'),
        Output('profile-lastlogin', 'children'),
        Output('profile-address', 'children'),
        Output('account-fullname', 'value'),
        Output('account-phone', 'value'),
        Output('account-address', 'value')],
    Input('url', 'pathname'),
    State('session-store', 'data')
)
def load_user_info(pathname, session_data):
    if not session_data or not session_data.get('authenticated'):
        return tuple([dash.no_update]*9)
    
    username = session_data.get('username')
    token = session_data.get('token')
    user_info = get_user_info(username, token=token)
    
    avatar = user_info.get('avatar', '') or '/assets/default-avatar.svg'
    full_name = user_info.get('ho_ten') or ''
    status = user_info.get('trang_thai', '')
    created = user_info.get('thoi_gian_tao', '')
    last_login = user_info.get('dang_nhap_lan_cuoi', '')
    address = user_info.get('dia_chi', '')
    phone = user_info.get('so_dien_thoai') or ''

    def _format_ts(val):
        if not val:
            return ''
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(val)
            return dt.strftime('%d/%m/%Y %H:%M')
        except Exception:
            try:
                ts = float(val)
                from datetime import datetime
                dt = datetime.fromtimestamp(ts)
                return dt.strftime('%d/%m/%Y %H:%M')
            except Exception:
                return str(val)

    created_fmt = _format_ts(created)
    lastlogin_fmt = _format_ts(last_login)

    return (
        avatar,
        username,
        full_name,
        status,
        created_fmt,
        lastlogin_fmt,
        address,
        phone,
        address
    )