import dash_bootstrap_components as dbc
from dash import html, dcc, callback, Input, Output, State
import dash


def create_navbar(is_authenticated=False, is_admin=False, current_path: str = None):
    def is_active(href: str) -> bool:
        if not current_path:
            return False
        if href == '/' and (current_path == '/' or current_path == ''):
            return True
        return current_path.rstrip('/') == href.rstrip('/')

    if is_authenticated:
        if is_admin:
            nav_items = [
                dbc.NavItem(dbc.NavLink("Trang chủ", href="/admin", className="nav-link-custom", active=is_active('/admin'))),
                dbc.NavItem(dbc.NavLink("Người dùng", href="/admin/users", className="nav-link-custom", active= is_active('/admin/users'))),
                dbc.NavItem(dbc.NavLink("Loại cảm biến", href="/admin/sensor-types", className="nav-link-custom", active=is_active('/admin/sensor-types'))),
                dbc.NavItem(dbc.NavLink("Firmware", href="/admin/firmware", className="nav-link-custom", active=is_active('/admin/firmware'))),
                dbc.NavItem(dbc.NavLink("Mô hình", href="/admin/models", className="nav-link-custom", active=is_active('/admin/models'))),
            ]
        else:
            nav_items = [
                dbc.NavItem(dbc.NavLink("Trang chủ", href="/", className="nav-link-custom", active=is_active('/'))),
                dbc.NavItem(dbc.NavLink("Thiết bị", href="/devices", className="nav-link-custom", active=is_active('/devices'))),
                dbc.NavItem(dbc.NavLink("Dự đoán", href="/predict_data", className="nav-link-custom", active=is_active('/predict_data'))),
            ]

        user_dropdown = dbc.DropdownMenu(
            children=[
                dbc.DropdownMenuItem("Thông tin tài khoản", id='nav-open-account', n_clicks=0),
                dbc.DropdownMenuItem("Đổi mật khẩu", id='nav-open-change-password', n_clicks=0),
                dbc.DropdownMenuItem(divider=True),
                dbc.DropdownMenuItem("Tài liệu", href="/documentation"),
                dbc.DropdownMenuItem("Đăng xuất", href="/logout")
            ],
            nav=True,
            in_navbar=True,
            align_end=True,
            menu_variant='light',
            className='nav-user-dropdown',
            toggleClassName='nav-user-toggle',
            toggle_style={'background': 'transparent', 'border': 'none', 'padding': '0.25rem 0.5rem'},
            label=html.Span([
                html.Span(className='nav-user-avatar', children=html.I(className='fas fa-user')), 
                html.Span(id='navbar-username', children='Tài khoản', className='ms-2 nav-user-name')
            ], className='d-flex align-items-center')
        )

        nav_items.append(dbc.NavItem(user_dropdown))
    else:
        nav_items = [
            dbc.NavItem(dbc.NavLink("Đăng nhập", href="/login", className="nav-link-custom", active=is_active('/login'))),
            dbc.NavItem(dbc.NavLink("Đăng ký", href="/register", className="nav-link-custom", active=is_active('/register'))),
        ]

    brand_href = "/admin" if is_authenticated and is_admin else ("/" if is_authenticated else "/login")

    navbar = dbc.Navbar(
        dbc.Container([
            html.A(
                dbc.Row([
                    dbc.Col(html.Img(src='/assets/logo_waterflow.png', style={'height':'40px'}, alt='Logo')),
                    dbc.Col(dbc.NavbarBrand("Giám sát và dự báo lưu lượng nước", className="ms-2 navbar-brand-custom")),
                ], align="center", className="g-0"),
                href=brand_href,
                style={"textDecoration": "none"}
            ),
            dbc.NavbarToggler(id="navbar-toggler", n_clicks=0),
            dbc.Collapse(
                dbc.Nav(
                    nav_items,
                    className="ms-auto",
                    navbar=True
                ),
                id="navbar-collapse",
                navbar=True,
            ),
        ], fluid=True),
        color="white",
        dark=False,
        className="navbar-custom shadow-sm mb-4",
        sticky="top"
    )

    account_modal = dbc.Modal([
        dbc.ModalHeader("Thông tin tài khoản"),
        dbc.ModalBody(
            dbc.Container([
                dbc.Row([
                    dbc.Col([
                        html.I(className="fas fa-user-circle fa-5x text-primary mb-3"),
                        html.H4(id='profile-username', className="mb-2"),
                        dbc.Button([html.I(className="fas fa-edit me-2"), html.Span(id='edit-account-btn-text', children="Chỉnh sửa")], id='edit-account-btn', className='mb-3 btn-edit')
                    ], className='text-center'),
                ], className='mb-3'),

                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader(html.H5([html.I(className="fas fa-edit me-2"), html.Span(id='account-card-title-text', children="Thông Tin Tài Khoản") ])),
                            dbc.CardBody([
                                dcc.Loading(id='loading-account-message', type='default', children=html.Div(id='account-message', className="mb-3")),

                                html.Div(id='account-view-container', children=[
                                    dbc.Row([dbc.Col(html.Strong("Họ và tên:"), md=4), dbc.Col(html.Span(id='view-fullname'), md=8)], className='mb-2'),
                                    dbc.Row([dbc.Col(html.Strong("Số điện thoại:"), md=4), dbc.Col(html.Span(id='view-phone'), md=8)], className='mb-2'),
                                    dbc.Row([dbc.Col(html.Strong("Địa chỉ:"), md=4), dbc.Col(html.Span(id='view-address'), md=8)], className='mb-2'),
                                    dbc.Row([dbc.Col(html.Strong("Trạng thái:"), md=4), dbc.Col(html.Div(id='view-status-badge'), md=8)], className='mb-2'),
                                    dbc.Row([dbc.Col(html.Strong("Tạo lúc:"), md=4), dbc.Col(html.Span(id='view-created'), md=8)], className='mb-2'),
                                    dbc.Row([dbc.Col(html.Strong("Đăng nhập lần cuối:"), md=4), dbc.Col(html.Span(id='view-last-login'), md=8)], className='mb-2'),
                                ]),

                                html.Div(id='account-form-container', style={'display': 'none'}, children=[
                                    dbc.Form([
                                        dbc.Row([
                                            dbc.Col([dbc.Label("Họ và tên", className="fw-bold"), dbc.Input(id='account-fullname', type='text', placeholder='Nhập họ và tên', className="mb-3")], md=6),
                                            dbc.Col([dbc.Label("Số điện thoại", className="fw-bold"), dbc.Input(id='account-phone', type='tel', placeholder='Nhập số điện thoại', className="mb-3")], md=6)
                                        ]),
                                        dbc.Row([
                                            dbc.Col([dbc.Label("Địa chỉ", className="fw-bold"), dbc.Input(id='account-address', type='text', placeholder='Nhập địa chỉ', className="mb-3")], md=6),
                                        ]),
                                        dbc.Row([
                                            dbc.Col([dbc.Label("Tạo lúc", className="fw-bold"), dbc.Input(id='account-created', type='text', disabled=True, className="mb-3")], md=6),
                                            dbc.Col([dbc.Label("Đăng nhập lần cuối", className="fw-bold"), dbc.Input(id='account-last-login', type='text', disabled=True, className="mb-3")], md=6)
                                        ]),
                                        dbc.Row([dbc.Col(dbc.Button([html.I(className="fas fa-save me-2"), "Lưu Thay Đổi"], id='save-account-btn', color='primary', className="px-4"), width=12)])
                                    ])
                                ])
                            ])
                        ], className='shadow-sm mb-4')
                    ], md=12)
                ])
            ], fluid=True)
        ),
        dbc.ModalFooter(dbc.Button("Đóng", id='modal-account-close', className='ms-auto'))
    ], id='modal-account-info', is_open=False, centered=True, size='lg')

    change_pwd_modal = dbc.Modal([
        dbc.ModalHeader("Đổi mật khẩu"),
        dbc.ModalBody(
            dbc.Container([
                dcc.Loading(id='loading-account-settings-message', type='default', children=html.Div(id='account-settings-message', className="mb-3")),
                dbc.Form([
                    dbc.Row([
                        dbc.Col([dbc.Label("Mật khẩu hiện tại", className="fw-bold"), html.Div(className='pw-input-wrapper mb-3', children=[dbc.Input(id='current-password', type='password', placeholder='Nhập mật khẩu hiện tại'), html.Span(html.I(className='fas fa-eye'), className='pw-toggle', **{'data-target':'current-password'})])], md=12),
                        dbc.Col([dbc.Label("Mật khẩu mới", className="fw-bold"), html.Div(className='pw-input-wrapper mb-3', children=[dbc.Input(id='new-password', type='password', placeholder='Nhập mật khẩu mới'), html.Span(html.I(className='fas fa-eye'), className='pw-toggle', **{'data-target':'new-password'})])], md=12),
                        dbc.Col([dbc.Label("Xác nhận mật khẩu mới", className="fw-bold"), html.Div(className='pw-input-wrapper mb-4', children=[dbc.Input(id='confirm-new-password', type='password', placeholder='Nhập lại mật khẩu mới'), html.Span(html.I(className='fas fa-eye'), className='pw-toggle', **{'data-target':'confirm-new-password'})])], md=12),
                    ]),
                    dbc.Row([dbc.Col(dbc.Button(["Lưu mật khẩu"], id='save-security-settings', color='primary', className="px-4"), width=12)])
                ])
            ], fluid=True)
        ),
        dbc.ModalFooter(dbc.Button("Đóng", id='modal-change-password-close', className='ms-auto'))
    ], id='modal-change-password', is_open=False, centered=True, size='md')

    settings_modal = dbc.Modal([
        dbc.ModalHeader("Cài đặt"),
        dbc.ModalBody(
            dbc.Container([
                dbc.Row([dbc.Col([
                    html.H5([html.I(className="fas fa-bell me-2"), "Cài Đặt Thông Báo"]),
                    dcc.Loading(id='loading-settings-message', type='default', children=html.Div(id='settings-message', className="mb-3")),
                    dbc.Form([
                        dbc.Row([dbc.Col([html.H6("Thông báo Email", className="mb-3"), dbc.Checkbox(id='email-notifications', label='Nhận thông báo qua email', value=True, className="mb-2"), dbc.Checkbox(id='email-alerts', label='Cảnh báo quan trọng', value=True, className="mb-2"), dbc.Checkbox(id='email-reports', label='Báo cáo định kỳ', value=False, className="mb-4")], width=12)]),
                        dbc.Row([dbc.Col([html.H6("Thông báo Push", className="mb-3"), dbc.Checkbox(id='push-notifications', label='Bật thông báo đẩy', value=True, className="mb-2"), dbc.Checkbox(id='push-sound', label='Âm thanh thông báo', value=True, className="mb-4")], width=12)]),
                        dbc.Row([dbc.Col([dbc.Button([html.I(className="fas fa-save me-2"), "Lưu Cài Đặt"], id='save-notification-settings', color='primary', className="px-4")], width=12)])
                    ])
                ], md=6), dbc.Col([
                    html.H5([html.I(className="fas fa-paint-brush me-2"), "Cài Đặt Giao Diện"]),
                    dbc.Form([dbc.Row([dbc.Col([html.H6("Chủ đề", className="mb-3"), dbc.RadioItems(id='theme-selection', options=[{'label': ' Sáng', 'value': 'light'},{'label': ' Tối', 'value': 'dark'},{'label': ' Tự động', 'value': 'auto'},], value='light', className="mb-4")], width=12)]), dbc.Row([dbc.Col([dbc.Button([html.I(className="fas fa-palette me-2"), "Áp Dụng"], id='save-appearance-settings', color='primary', className="px-4")], width=12)])])
                ], md=6)])
            ], fluid=True)
        ),
        dbc.ModalFooter(dbc.Button("Đóng", id='modal-settings-close', className='ms-auto'))
    ], id='modal-settings', is_open=False, centered=True, size='md')

    root = html.Div([
        dcc.Location(id='account-url', refresh=False),
        navbar,
        account_modal,
        change_pwd_modal,
        settings_modal
    ])

    return root

@callback(
    Output('navbar-username', 'children'),
    Input('session-store', 'data')
)
def _update_navbar_username(session_data):
    if session_data and isinstance(session_data, dict):
        username = session_data.get('username') or session_data.get('ten_dang_nhap')
        if username:
            return str(username)
    return 'Tài khoản'


@callback(
    Output('modal-account-info', 'is_open'),
    Output('modal-change-password', 'is_open'),
    Output('modal-settings', 'is_open'),
    Input('nav-open-account', 'n_clicks'),
    Input('nav-open-change-password', 'n_clicks'),
    Input('modal-account-close', 'n_clicks'),
    Input('modal-change-password-close', 'n_clicks'),
    Input('modal-settings-close', 'n_clicks'),
    State('modal-account-info', 'is_open'),
    State('modal-change-password', 'is_open'),
    State('modal-settings', 'is_open')
)
def _toggle_modals(n_account, n_change, n_close_account, n_close_change, n_close_settings, open_account, open_change, open_settings):
    ctx = dash.callback_context
    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate
    prop = ctx.triggered[0]['prop_id'].split('.')[0]

    if prop == 'modal-account-close':
        return False, False, False
    if prop == 'modal-change-password-close':
        return False, False, False
    if prop == 'modal-settings-close':
        return False, False, False

    if prop == 'nav-open-account':
        if open_account:
            return False, False, False
        return True, False, False

    if prop == 'nav-open-change-password':
        if open_change:
            return False, False, False
        return False, True, False

    return open_account, open_change, open_settings

