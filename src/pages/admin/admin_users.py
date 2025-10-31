from dash import html, dcc, callback, Input, Output, State
import dash_bootstrap_components as dbc
import dash
import pandas as pd
from datetime import datetime, timedelta, timezone
import math
from components.navbar import create_navbar
from api import user as api_user
from dash.dependencies import ALL

ROWS_PER_PAGE = 5


def _coerce_bool(value, default=False):
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {'true', '1', 'yes', 'dang_hoat_dong', 'đang hoạt động', 'hoat_dong', 'active', 'co'}:
            return True
        if normalized in {'false', '0', 'no', 'khong', 'không', 'khong_hoat_dong', 'không hoạt động', 'inactive'}:
            return False
    return default


layout = html.Div([
    create_navbar(is_authenticated=True, is_admin=True),
    dcc.Location(id='admin-users-url', refresh=False),
    dcc.Store(id='admin-users-page-store', data=[]),
    dcc.Store(id='admin-current-username-users', data=None),
    dcc.Store(id='admin-users-table-page', data={'page': 1}),

    dcc.Loading(html.Div(id='admin-users-dashboard'), type='default'),

    dbc.Toast(
        id='admin-users-toast',
        header='Thông báo',
        is_open=False,
        dismissable=True,
        duration=3500,
        icon='primary',
        children='',
        style={'position': 'fixed', 'top': '80px', 'right': '24px', 'zIndex': 2100}
    ),

    dbc.Modal([
        dbc.ModalHeader(html.H5(id='modal-title-users')),
        dbc.ModalBody([
            dbc.Form([
                dbc.Row([
                    dbc.Col(dbc.Label('Tên đăng nhập', className='fw-bold'), md=12),
                    dbc.Col(dbc.Input(id='user-username-users', type='text', readonly=True), md=12),
                ]),
                dbc.Row([
                    dbc.Col(dbc.Label('Họ tên', className='fw-bold'), md=12),
                    dbc.Col(dbc.Input(id='user-fullname-users', type='text', readonly=True), md=12),
                ]),
                dbc.Row([
                    dbc.Col(dbc.Label('Số điện thoại', className='fw-bold'), md=12),
                    dbc.Col(dbc.Input(id='user-phone-users', type='text', readonly=True), md=12),
                ]),
                dbc.Row([
                    dbc.Col(dbc.Label('Địa chỉ', className='fw-bold'), md=12),
                    dbc.Col(dbc.Input(id='user-address-users', type='text', readonly=True), md=12),
                ]),
                dbc.Row([
                    dbc.Col(dbc.Checkbox(id='user-is-admin-users', label='Quyền admin'), md=6),
                    dbc.Col(dbc.Checkbox(id='user-is-active-users', label='Hoạt động', value=True, disabled=True), md=6),
                ])
            ])
        ]),
        dbc.ModalFooter([
            dbc.Button('Lưu', id='save-user-btn-users', color='primary'),
            dbc.Button('Hủy', id='cancel-user-btn-users', className='ms-2')
        ])
    ], id='user-modal-users', is_open=False, size='lg', style={"marginTop": "150px"}),

    dbc.Modal([
        dbc.ModalHeader('Xác nhận xóa'),
        dbc.ModalBody(html.Div(id='delete-confirm-body-users')),
        dbc.ModalFooter([
            dbc.Button('Xóa', id='confirm-delete-btn-users', color='danger'),
            dbc.Button('Hủy', id='cancel-delete-btn-users', className='ms-2')
        ])
    ], id='delete-modal-users', is_open=False, style = {"marginTop":"350px"})

], className='page-container')


@callback(
    Output('admin-users-page-store', 'data', allow_duplicate=True),
    Input('url', 'pathname'),
    State('session-store', 'data'),
    prevent_initial_call='initial_duplicate'
)
def load_users_page(pathname, session_data):
    if pathname != '/admin/users':
        raise dash.exceptions.PreventUpdate

    if not session_data or not session_data.get('authenticated') or not session_data.get('is_admin'):
        return []

    token = session_data.get('token')
    users = api_user.list_users(token=token)
    return users or []


@callback(
    Output('admin-users-dashboard', 'children'),
    [Input('admin-users-page-store', 'data'), Input('admin-users-table-page', 'data')]
)
def render_users_dashboard(users, page_state):
    def _extract_first(item, keys, default=''):
        for key in keys:
            val = item.get(key)
            if val not in (None, ''):
                return val
        return default

    def _parse_datetime(value):
        if not value:
            return None
        try:
            dt = pd.to_datetime(value, errors='coerce')
            if pd.isna(dt):
                return None
            if isinstance(dt, pd.Timestamp):
                py_dt = dt.to_pydatetime()
                if py_dt.tzinfo is not None and py_dt.tzinfo.utcoffset(py_dt) is not None:
                    return py_dt.astimezone(timezone.utc).replace(tzinfo=None)
                return py_dt
        except Exception:
            return None
        return None

    if not users:
        empty_state = dbc.Container([
            html.Div(className='admin-empty', children=dbc.Alert('Không tìm thấy người dùng nào.', color='secondary'))
        ], fluid=True, className='admin-dashboard-container')
        return empty_state

    total_users = len(users)
    current_page = 1
    if isinstance(page_state, dict):
        try:
            current_page = int(page_state.get('page', 1))
        except (TypeError, ValueError):
            current_page = 1
    if current_page < 1:
        current_page = 1
    now = datetime.utcnow()
    today = now.date()
    week_start = today - timedelta(days=today.weekday())
    week_start_dt = datetime.combine(week_start, datetime.min.time())
    month_start = today.replace(day=1)
    month_start_dt = datetime.combine(month_start, datetime.min.time())

    active_count = 0
    weekly_registrations = []
    monthly_registrations = []
    processed_rows = []

    for idx, user in enumerate(users, start=1):
        ten_dang_nhap = user.get('ten_dang_nhap')
        username = ten_dang_nhap or _extract_first(user, ['username', 'ma_nguoi_dung'], f'U{idx:03d}')
        fullname = user.get('ho_ten') or _extract_first(user, ['full_name', 'ten'])
        phone = user.get('so_dien_thoai') or _extract_first(user, ['phone'])
        address = user.get('dia_chi') or _extract_first(user, ['address'])
        created_raw = user.get('thoi_gian_tao') or _extract_first(user, ['created_at', 'ngay_tao', 'created'], None)
        created_at = _parse_datetime(created_raw)
        active = _coerce_bool(user.get('trang_thai'), default=True)
        is_admin = _coerce_bool(user.get('quan_tri_vien'), default=False)
        role_label = 'Quản trị viên' if is_admin else 'Người dùng'
        pumps_total = _extract_first(user, ['tong_may_bom'], 0)
        pumps_running = _extract_first(user, ['may_bom_dang_chay', 'pump_running', 'dang_chay'], 0)
        sensors_total = _extract_first(user, ['tong_cam_bien',], 0)
        devices_total = _extract_first(user, ['tong_thiet_bi'], None)
        last_login_raw = _extract_first(user, ['dang_nhap_lan_cuoi'], None)
        last_login = _parse_datetime(last_login_raw)

        try:
            pumps_total = int(pumps_total)
        except (TypeError, ValueError):
            pumps_total = 0
        try:
            pumps_running = int(pumps_running)
        except (TypeError, ValueError):
            pumps_running = 0
        try:
            sensors_total = int(sensors_total)
        except (TypeError, ValueError):
            sensors_total = 0
        if devices_total is None:
            devices_total = pumps_total + sensors_total
        else:
            try:
                devices_total = int(devices_total)
            except (TypeError, ValueError):
                devices_total = pumps_total + sensors_total

        if active:
            active_count += 1

        if created_at:
            if created_at >= month_start_dt:
                monthly_registrations.append({'name': fullname or username, 'date': created_at, 'active': active})
            if created_at >= week_start_dt:
                weekly_registrations.append({'name': fullname or username, 'date': created_at, 'active': active})

        processed_rows.append({
            'index': idx,
            'username': username,
            'ten_dang_nhap': ten_dang_nhap,
            'fullname': fullname,
            'phone': phone,
            'address': address,
            'active': active,
            'is_admin': is_admin,
            'role_label': role_label,
            'pumps_total': pumps_total,
            'pumps_running': pumps_running,
            'sensors_total': sensors_total,
            'devices_total': devices_total,
            'created_at': created_at,
            'last_login': last_login
        })

    inactive_count = total_users - active_count
    active_ratio = (active_count / total_users * 100) if total_users else 0
    monthly_registrations.sort(key=lambda item: item['date'], reverse=True)
    weekly_registrations.sort(key=lambda item: item['date'], reverse=True)
    monthly_total = len([item for item in monthly_registrations if item['date'] >= month_start_dt])
    processed_rows.sort(key=lambda row: row['created_at'] or datetime.min, reverse=True)
    rows_per_page = ROWS_PER_PAGE
    total_pages = max(1, math.ceil(len(processed_rows) / rows_per_page))
    if current_page > total_pages:
        current_page = total_pages
    if current_page < 1:
        current_page = 1

    def build_summary_card(title, value, subtitle, icon_class, extra=None):
        content = [
            html.Div([
                html.Div([
                    html.Span(title, className='admin-summary-title'),
                    html.H3(f"{value}", className='admin-summary-value'),
                    html.Span(subtitle, className='admin-summary-subtitle')
                ]),
                html.Div(html.I(className=icon_class), className='admin-summary-icon bg-admin-primary')
            ], className='d-flex justify-content-between align-items-center gap-3')
        ]
        if extra is not None:
            content.append(extra)
        return html.Div(
            dbc.Card(dbc.CardBody(content)),
            className='admin-summary-col'
        )

    summary_cards = html.Div([
        build_summary_card('Tổng người dùng', total_users, 'Trong hệ thống', 'fas fa-users'),
        build_summary_card('Đang hoạt động', active_count, f"{active_ratio:.0f}% tổng số", 'fas fa-user-check',
                        dbc.Progress(value=active_ratio, max=100, className='user-progress', color='dark')),
        build_summary_card('Không hoạt động', inactive_count, f"{inactive_count} người dùng", 'fas fa-user-slash'),
        build_summary_card('Đăng ký mới', monthly_total, 'Tháng này', 'fas fa-user-plus')
    ], className='admin-summary-grid user-summary-grid')

    def format_date(dt):
        if not dt:
            return '--'
        return dt.strftime('%Y-%m-%d')

    def format_datetime(dt):
        if not dt:
            return '--'
        return dt.strftime('%Y-%m-%d %H:%M')

    def build_registration_card(title, items):
        if not items:
            body = html.Div('Không có dữ liệu', className='user-card-empty')
        else:
            list_class = 'user-card-list'
            if len(items) > 3:
                list_class += ' user-card-list-scroll'
            body = html.Div([
                html.Div([
                    html.Div(html.Strong(entry['name']), className='user-card-text'),
                    html.Div([
                        html.Span(format_date(entry['date']), className='user-card-date'),
                        html.Span('Hoạt động' if entry['active'] else 'Không hoạt động',
                                className=f"user-status-badge {'active' if entry['active'] else 'inactive'}")
                    ], className='user-card-meta')
                ], className='user-card-item')
                for entry in items
            ], className=list_class)

        return dbc.Card([
            dbc.CardHeader(html.Span(title, className='user-card-title')),
            dbc.CardBody(body)
        ], className='user-card')

    lists_section = html.Div([
        build_registration_card('Người dùng đăng ký tuần này', weekly_registrations),
        build_registration_card('Người dùng đăng ký tháng này', monthly_registrations)
    ], className='user-lists-grid')

    table_header = html.Thead(html.Tr([
        html.Th('Người dùng'),
        html.Th('Số điện thoại'),
        html.Th('Địa chỉ'),
        html.Th('Vai trò'),
        html.Th('Trạng thái'),
        html.Th('Máy bơm'),
        html.Th('Đang chạy'),
        html.Th('Cảm biến'),
        html.Th('Tổng thiết bị'),
        html.Th('Ngày đăng ký'),
        html.Th('Đăng nhập cuối'),
        html.Th('Hành động')
    ]))

    start_index = (current_page - 1) * rows_per_page
    end_index = start_index + rows_per_page
    visible_rows = processed_rows[start_index:end_index]
    prev_disabled = current_page <= 1
    next_disabled = current_page >= total_pages

    table_rows = []
    for row in visible_rows:
        identifier = row.get('ten_dang_nhap') or row['username']

        actions = html.Div([
            dbc.Button(
                html.I(className='fas fa-edit'),
                id={'type': 'edit-user-users', 'index': identifier},
                color='light',
                size='sm',
                className='action-btn edit',
                title='Chỉnh sửa'
            ),
            dbc.Button(
                html.I(className='fas fa-trash'),
                id={'type': 'delete-user-users', 'index': identifier},
                color='light',
                size='sm',
                className='action-btn delete',
                title='Xóa người dùng'
            )
        ], className='user-actions')

        table_rows.append(html.Tr([
            html.Td(html.Div([
                html.Strong(row['fullname'] or identifier),
                html.Span(identifier, className='user-table-username')
            ])),
            html.Td(row['phone'] or '--', className='text-nowrap'),
            html.Td(html.Div(row['address'] or '--', className='user-table-address')),
            html.Td(row['role_label'], className='user-table-role'),
            html.Td(html.Span('Hoạt động' if row['active'] else 'Không hoạt động',
                            className=f"user-status-badge {'active' if row['active'] else 'inactive'}")),
            html.Td(row['pumps_total']),
            html.Td(row['pumps_running']),
            html.Td(row['sensors_total']),
            html.Td(row['devices_total']),
            html.Td(format_date(row['created_at'])),
            html.Td(format_datetime(row['last_login']), className='text-nowrap'),
            html.Td(actions, className='text-end')
        ]))

    pagination_controls = html.Div([
        dbc.Button('Trước', id='admin-users-page-prev', color='light', size='sm', className='pagination-btn', disabled=prev_disabled),
        html.Span(f'Trang {current_page} / {total_pages}', className='pagination-label fw-semibold'),
        dbc.Button('Sau', id='admin-users-page-next', color='light', size='sm', className='pagination-btn', disabled=next_disabled)
    ], className='d-flex align-items-center justify-content-between pagination-controls mt-3')

    table = dbc.Table([
        table_header,
        html.Tbody(table_rows)
    ], bordered=False, hover=True, responsive=True, className='user-table')

    table_card = dbc.Card([
        dbc.CardHeader(html.Span('Chi tiết thiết bị của từng người dùng', className='user-table-title')),
        dbc.CardBody([table, pagination_controls])
    ], className='user-table-card')

    dashboard = dbc.Container([
        summary_cards,
        lists_section,
        table_card
    ], fluid=True, className='admin-dashboard-container user-dashboard')

    return dashboard


@callback(
    Output('admin-users-table-page', 'data'),
    [Input('admin-users-page-prev', 'n_clicks'), Input('admin-users-page-next', 'n_clicks')],
    [State('admin-users-table-page', 'data'), State('admin-users-page-store', 'data')],
    prevent_initial_call=True
)
def change_users_table_page(prev_clicks, next_clicks, page_state, users):
    ctx = dash.callback_context
    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    current_page = 1
    if isinstance(page_state, dict):
        try:
            current_page = int(page_state.get('page', 1))
        except (TypeError, ValueError):
            current_page = 1

    total_pages = max(1, math.ceil(len(users or []) / ROWS_PER_PAGE))

    if button_id == 'admin-users-page-prev':
        if current_page <= 1:
            raise dash.exceptions.PreventUpdate
        current_page -= 1
    elif button_id == 'admin-users-page-next':
        if current_page >= total_pages:
            raise dash.exceptions.PreventUpdate
        current_page += 1
    else:
        raise dash.exceptions.PreventUpdate

    return {'page': current_page}


@callback(
    [Output('user-modal-users', 'is_open'), Output('modal-title-users', 'children'), Output('admin-current-username-users', 'data'),
     Output('user-username-users', 'value'), Output('user-fullname-users', 'value'), Output('user-phone-users', 'value'),
     Output('user-address-users', 'value'), Output('user-is-admin-users', 'value'), Output('user-is-active-users', 'value')],
    Input({'type': 'edit-user-users', 'index': dash.dependencies.ALL}, 'n_clicks'),
    [State('admin-users-page-store', 'data'), State('session-store', 'data'), State('admin-current-username-users', 'data')],
    prevent_initial_call=True
)
def open_user_modal_users(edit_clicks, users, session_data, current):
    ctx = dash.callback_context
    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate
    triggered = ctx.triggered[0]
    btn = triggered['prop_id'].split('.')[0]
    if not triggered.get('value'):
        raise dash.exceptions.PreventUpdate

    try:
        if btn.startswith('{') and 'edit-user-users' in btn:
            import json
            obj = json.loads(btn)
            identifier = obj.get('username')
            u = None
            for candidate in users or []:
                primary_key = candidate.get('index')
                if primary_key is not None and str(primary_key) == str(identifier):
                    u = candidate
                    break
            if u is None:
                u = next((x for x in (users or []) if (x.get('username') == identifier)), None)
            if not u:
                return False, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

            ten_dang_nhap = (u.get('ten_dang_nhap') if u.get('ten_dang_nhap') not in (None, '') else identifier) or ''
            ho_ten = u.get('ho_ten') if u.get('ho_ten') not in (None, '') else ''
            so_dien_thoai = u.get('so_dien_thoai') if u.get('so_dien_thoai') not in (None, '') else ''
            dia_chi = u.get('dia_chi') if u.get('dia_chi') not in (None, '') else ''
            quan_tri_vien = _coerce_bool(u.get('quan_tri_vien'), default=False)
            trang_thai = _coerce_bool(u.get('trang_thai'), default=True)
            
            return True, 'Chỉnh sửa người dùng', ten_dang_nhap, ten_dang_nhap, ho_ten, so_dien_thoai, dia_chi, quan_tri_vien, trang_thai
    except Exception:
        pass

    raise dash.exceptions.PreventUpdate


@callback(
    [Output('admin-users-page-store', 'data', allow_duplicate=True), Output('user-modal-users', 'is_open', allow_duplicate=True),
     Output('delete-modal-users', 'is_open', allow_duplicate=True), Output('admin-current-username-users', 'data', allow_duplicate=True),
     Output('admin-users-toast', 'children', allow_duplicate=True), Output('admin-users-toast', 'icon', allow_duplicate=True),
     Output('admin-users-toast', 'is_open', allow_duplicate=True)],
    [Input('save-user-btn-users', 'n_clicks'), Input('confirm-delete-btn-users', 'n_clicks')],
    [State('admin-current-username-users', 'data'), State('user-username-users', 'value'), State('user-fullname-users', 'value'),
     State('user-phone-users', 'value'), State('user-address-users', 'value'),
     State('user-is-admin-users', 'value'), State('user-is-active-users', 'value'), State('session-store', 'data')],
    prevent_initial_call=True
)
def handle_save_or_delete_users(save_click, del_click, current_username, username, fullname, phone, address, is_admin, is_active, session_data):
    ctx = dash.callback_context
    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate
    action = ctx.triggered[0]['prop_id'].split('.')[0]

    if not session_data or not session_data.get('authenticated') or not session_data.get('is_admin'):
        raise dash.exceptions.PreventUpdate

    token = session_data.get('token')

    if action == 'save-user-btn-users':
        data = {
            'ten_dang_nhap': username,
            'ho_ten': fullname or '',
            'so_dien_thoai': phone or '',
            'dia_chi': address or '',
            'trang_thai': bool(is_active),
            'quan_tri_vien': bool(is_admin)
        }

        target_username = current_username or username

        success, message = api_user.update_user(target_username, data, token=token)
        toast_message = message or ('Cập nhật người dùng thành công' if success else 'Cập nhật người dùng thất bại')
        toast_icon = 'success' if success else 'danger'

        if success:
            users = api_user.list_users(token=token)
            return users or [], False, False, None, toast_message, toast_icon, True

        return dash.no_update, True, False, current_username, toast_message, toast_icon, True

    if action == 'confirm-delete-btn-users':
        if not current_username:
            raise dash.exceptions.PreventUpdate
        success, message = api_user.delete_user(current_username, token=token)
        toast_message = message or ('Xóa người dùng thành công' if success else 'Xóa người dùng thất bại')
        toast_icon = 'success' if success else 'danger'

        if success:
            users = api_user.list_users(token=token)
            return users or [], False, False, None, toast_message, toast_icon, True

        return dash.no_update, False, True, current_username, toast_message, toast_icon, True

    raise dash.exceptions.PreventUpdate


@callback(
    [Output('user-modal-users', 'is_open', allow_duplicate=True), Output('delete-modal-users', 'is_open', allow_duplicate=True), Output('admin-current-username-users', 'data', allow_duplicate=True), Output('delete-confirm-body-users', 'children')],
    [Input('cancel-user-btn-users', 'n_clicks'), Input('cancel-delete-btn-users', 'n_clicks'), Input({'type': 'delete-user-users', 'index': dash.dependencies.ALL}, 'n_clicks')],
    [State('admin-current-username-users', 'data'), State('admin-users-page-store', 'data')],
    prevent_initial_call=True
)
def handle_modals_users(cancel_user, cancel_delete, delete_clicks, current, users):
    ctx = dash.callback_context
    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate
    triggered = ctx.triggered[0]
    btn = triggered['prop_id'].split('.')[0]
    if not triggered.get('value'):
        raise dash.exceptions.PreventUpdate

    if btn == 'cancel-user-btn-users':
        return False, dash.no_update, None, dash.no_update

    if btn == 'cancel-delete-btn-users':
        return dash.no_update, False, None, dash.no_update

    try:
        if btn.startswith('{') and 'delete-user-users' in btn:
            import json
            obj = json.loads(btn)
            username = obj.get('ten_dang_nhap') or obj.get('index')
            return dash.no_update, True, username, f"Bạn có chắc chắn muốn xóa người dùng '{username}'?"
    except Exception:
        pass

    raise dash.exceptions.PreventUpdate
