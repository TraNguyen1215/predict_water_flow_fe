from dash import html, dcc, callback, Input, Output, State
import dash_bootstrap_components as dbc
import dash
from datetime import datetime, timezone, timedelta
from components.navbar import create_navbar
from api.auth import get_user_info, update_user_info
from api.auth import change_password

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
                    dbc.Button([
                        html.I(className="fas fa-save me-2"), "Lưu Cài Đặt"],
                        id='save-notification-settings',
                        color='primary',
                        className="px-4"
                    ),
                ], width=12)
            ]),
        ])
    ])
], className="shadow-sm dark-card")

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
            dbc.Row([
                dbc.Col([
                    dbc.Button([
                        html.I(className="fas fa-palette me-2"), "Áp Dụng"],
                        id='save-appearance-settings',
                        color='primary',
                        className="px-4"
                    ),
                ], width=12)
            ]),
        ])
    ])
], className="shadow-sm dark-card")

def format_relative_time(iso_ts: str) -> str:
    if not iso_ts:
        return ''
    try:
        dt = datetime.fromisoformat(iso_ts)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
            
        target_tz = timezone(timedelta(hours=7))
        dt_local = dt.astimezone(target_tz)
        now = datetime.now(target_tz)
        delta = now - dt_local
        seconds = int(delta.total_seconds())
        if seconds < 0:
            return 'vừa xong'
        if seconds < 60:
            return 'vừa xong'
        minutes = seconds // 60
        if minutes < 60:
            return f"{minutes} phút trước"
        hours = minutes // 60
        if hours < 24:
            return f"{hours} giờ trước"
        days = hours // 24
        if days < 30:
            return f"{days} ngày trước"
        months = days // 30
        if months < 12:
            return f"{months} tháng trước"
        years = months // 12
        return f"{years} năm trước"
    except Exception:
        return iso_ts


def format_display_time(iso_ts: str) -> str:
    if not iso_ts:
        return ''
    try:
        dt = datetime.fromisoformat(iso_ts)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        target_tz = timezone(timedelta(hours=7))
        dt_local = dt.astimezone(target_tz)
        return dt_local.strftime('%H:%M %d/%m/%Y')
    except Exception:
        return iso_ts

layout = html.Div([
    create_navbar(is_authenticated=True),
    dbc.Container([
        dbc.Row([dbc.Col(html.P("Quản lý thông tin tài khoản, đổi mật khẩu và cài đặt từ menu người dùng (icon góc trên bên phải)."), width=12)])
    ], fluid=True, className="py-4")
])

@callback(
    [Output('profile-username', 'children'),
        Output('view-fullname', 'children'),
        Output('view-phone', 'children'),
        Output('view-address', 'children'),
        Output('view-status-badge', 'children'),
        Output('view-created', 'children'),
        Output('view-last-login', 'children'),
        Output('account-fullname', 'value'),
        Output('account-address', 'value'),
        Output('account-phone', 'value'),
        Output('account-created', 'value'),
        Output('account-last-login', 'value')
    ],
    Input('url', 'pathname'),
    State('session-store', 'data')
)
def load_user_info(pathname, session_data):
    if not session_data or not session_data.get('authenticated'):
        return (
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
        )
    
    username = session_data.get('username')
    token = session_data.get('token')
    user_info = get_user_info(username, token=token)
    full_name = user_info.get('ho_ten') or ''
    phone = user_info.get('so_dien_thoai') or ''
    address = user_info.get('dia_chi') or ''
    status = user_info.get('trang_thai')
    created = user_info.get('thoi_gian_tao')
    
    last_login = user_info.get('dang_nhap_lan_cuoi')

    if isinstance(status, bool):
        if status:
            status_el = dbc.Badge("Đang hoạt động", color="success", className="ms-1")
        else:
            status_el = dbc.Badge("Ngừng hoạt động", color="secondary", className="ms-1")
    else:
        status_el = html.Span("")

    rel_time = format_relative_time(created) if created else ''
    time_el = html.Span(rel_time, className="text-muted small ms-2") if rel_time else html.Span("")

    status_time_div = html.Div([status_el, time_el], className="d-flex justify-content-center align-items-center")

    created_display = format_display_time(created) if created else ''
    last_login_display = format_display_time(last_login) if last_login else ''

    return (
        username,
        full_name,
        phone,
        address,
        status_el,
        created_display,
        last_login_display,
        full_name,
        address,
        phone,
        created_display,
        last_login_display,
    )

@callback(
    Output('account-message', 'children'),
    Input('save-account-btn', 'n_clicks'),
    [State('account-fullname', 'value'),
        State('account-address', 'value'),
        State('account-phone', 'value'),
        State('session-store', 'data')
    ],
    prevent_initial_call=True
)
def save_account_info(n_clicks, fullname, address, phone, session_data):
    if not session_data or not session_data.get('authenticated'):
        return dbc.Alert("Phiên đăng nhập đã hết hạn!", color="danger", dismissable=True)

    username = session_data.get('username')
    user_data = {
        'ho_ten': fullname or '',
        'dia_chi': address or '',
        'so_dien_thoai': phone or '',
    }

    token = session_data.get('token')
    success, message = update_user_info(username, user_data, token=token)

    if success:
        return dbc.Alert(message, color="success", dismissable=True)
    else:
        return dbc.Alert(message, color="danger", dismissable=True)


@callback(
    [Output('account-form-container', 'style'),
        Output('account-view-container', 'style'),
        Output('account-card-title-text', 'children'),
        Output('edit-account-btn-text', 'children')],
        [Input('edit-account-btn', 'n_clicks'), Input('account-url', 'hash')],
    State('account-form-container', 'style'),
)
def toggle_account_form(n_clicks, url_hash, current_style):
    if url_hash and url_hash.lstrip('#') == 'security':
        return ({'display': 'none'}, {'display': 'none'}, "Đổi mật khẩu", "Chỉnh sửa")

    if url_hash and url_hash.lstrip('#') == 'settings':
        return ({'display': 'none'}, {'display': 'none'}, "Cài đặt", "Chỉnh sửa")

    if not n_clicks:
        return ({'display': 'none'}, {}, "Thông tin Tài khoản", "Chỉnh sửa")

    if not current_style or current_style.get('display') == 'none':
        return ({'display': 'block'}, {'display': 'none'}, "Cập Nhật Thông Tin", "Hủy")
    else:
        return ({'display': 'none'}, {}, "Thông Tin Tài Khoản", "Chỉnh sửa")


@callback(
    Output('account-settings-message', 'children'),
    Input('save-security-settings', 'n_clicks'),
    [State('current-password', 'value'),
        State('new-password', 'value'),
        State('confirm-new-password', 'value'),
        State('session-store', 'data')],
    prevent_initial_call=True
)
def handle_change_password(n_clicks, current_password, new_password, confirm_new_password, session_data):
    if not session_data or not session_data.get('authenticated'):
        return dbc.Alert("Phiên đăng nhập đã hết hạn! Vui lòng đăng nhập lại.", color="danger", dismissable=True)

    if not current_password or not new_password or not confirm_new_password:
        return dbc.Alert("Vui lòng nhập đầy đủ thông tin mật khẩu.", color="warning", dismissable=True)

    if new_password != confirm_new_password:
        return dbc.Alert("Mật khẩu mới và xác nhận không khớp.", color="danger", dismissable=True)

    if len(new_password) < 6:
        return dbc.Alert("Mật khẩu phải có ít nhất 6 ký tự.", color="warning", dismissable=True)

    token = session_data.get('token')
    if not token:
        return dbc.Alert("Không tìm thấy token. Vui lòng đăng nhập lại.", color="danger", dismissable=True)

    success, message = change_password(current_password, new_password, token)
    if success:
        return dbc.Alert(message, color="success", dismissable=True, duration=4000)
    else:
        return dbc.Alert(message, color="danger", dismissable=True)


@callback(
    [Output('security', 'style'),
        Output('account-main-card', 'style'),
        Output('account-settings-container', 'style')],
    Input('account-url', 'hash')
)
def show_security_card(url_hash):
    if url_hash and url_hash.lstrip('#') == 'security':
        return {'display': 'block'}, {'display': 'none'}, {'display': 'none'}

    if url_hash and url_hash.lstrip('#') == 'settings':
        return {'display': 'none'}, {'display': 'none'}, {'display': 'block'}

    return {'display': 'none'}, {}, {'display': 'none'}

