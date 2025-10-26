from dash import html, dcc, callback, Input, Output, State
import dash_bootstrap_components as dbc
import dash
from components.navbar import create_navbar
from api import user as api_user
from api import sensor as api_sensor
from api import pump as api_pump
from api import sensor_data as api_sensor_data


layout = html.Div([
    create_navbar(is_authenticated=True, is_admin=True),
    dcc.Location(id='admin-url', refresh=False),
    dcc.Store(id='admin-users-store', data=[]),
    dcc.Store(id='admin-dashboard-store', data={}),
    html.Div(id='admin-dashboard'),

    dbc.Container([
        dbc.Row([
            dbc.Col(html.H2([html.I(className='fas fa-users me-2'), 'Quản trị người dùng']), md=9),
            dbc.Col(dbc.Button([html.I(className='fas fa-plus me-2'), 'Tạo người dùng mới'], id='btn-new-user', color='primary'), md=3, className='text-end')
        ], className='my-3'),

        dbc.Row([
            dbc.Col(dcc.Loading(id='loading-users-table', children=html.Div(id='users-table-container')))
        ]),

        # Modal for create/edit
        dbc.Modal([
            dbc.ModalHeader(html.H5(id='modal-title')),
            dbc.ModalBody([
                dbc.Form([
                    dbc.Row([
                        dbc.Col(dbc.Label('Tên đăng nhập', className='fw-bold'), md=12),
                        dbc.Col(dbc.Input(id='user-username', type='text'), md=12),
                    ]),
                    dbc.Row([
                        dbc.Col(dbc.Label('Họ tên', className='fw-bold'), md=12),
                        dbc.Col(dbc.Input(id='user-fullname', type='text'), md=12),
                    ]),
                    dbc.Row([
                        dbc.Col(dbc.Label('Số điện thoại', className='fw-bold'), md=12),
                        dbc.Col(dbc.Input(id='user-phone', type='text'), md=12),
                    ]),
                    dbc.Row([
                        dbc.Col(dbc.Label('Địa chỉ', className='fw-bold'), md=12),
                        dbc.Col(dbc.Input(id='user-address', type='text'), md=12),
                    ]),
                    dbc.Row([
                        dbc.Col(dbc.Label('Mật khẩu (chỉ tạo hoặc khi đổi)', className='fw-bold small'), md=12),
                        dbc.Col(dbc.Input(id='user-password', type='password'), md=12),
                    ]),
                    dbc.Row([
                        dbc.Col(dbc.Checkbox(id='user-is-admin', label='Quyền admin'), md=6),
                        dbc.Col(dbc.Checkbox(id='user-is-active', label='Hoạt động', value=True), md=6),
                    ])
                ])
            ]),
            dbc.ModalFooter([
                dbc.Button('Lưu', id='save-user-btn', color='primary'),
                dbc.Button('Hủy', id='cancel-user-btn', className='ms-2')
            ])
        ], id='user-modal', is_open=False, size='lg'),

        # Hidden store for currently edited username
        dcc.Store(id='admin-current-username', data=None),

        # Confirmation modal for delete
        dbc.Modal([
            dbc.ModalHeader('Xác nhận xóa'),
            dbc.ModalBody(html.Div(id='delete-confirm-body')),
            dbc.ModalFooter([
                dbc.Button('Xóa', id='confirm-delete-btn', color='danger'),
                dbc.Button('Hủy', id='cancel-delete-btn', className='ms-2')
            ])
        ], id='delete-modal', is_open=False)

    ], fluid=True, className='py-4')
])


@callback(
    Output('admin-users-store', 'data', allow_duplicate=True),
    Input('url', 'pathname'),
    State('session-store', 'data'),
    prevent_initial_call='initial_duplicate'
)
def load_users(pathname, session_data):
    # load when admin page is active
    if pathname != '/admin':
        raise dash.exceptions.PreventUpdate

    if not session_data or not session_data.get('authenticated') or not session_data.get('is_admin'):
        return []

    token = session_data.get('token')
    users = api_user.list_users(token=token)
    return users or []


@callback(
    Output('admin-dashboard', 'children'),
    Input('url', 'pathname'),
    State('session-store', 'data'),
    prevent_initial_call='initial_duplicate'
)
def load_admin_dashboard(pathname, session_data):
    # load dashboard summary when admin page is active
    if pathname != '/admin':
        raise dash.exceptions.PreventUpdate

    if not session_data or not session_data.get('authenticated') or not session_data.get('is_admin'):
        raise dash.exceptions.PreventUpdate

    token = session_data.get('token')

    # fetch counts from API endpoints (use limit=1 to read total metadata)
    try:
        users = api_user.list_users(token=token) or []
        total_users = len(users) if isinstance(users, list) else (users.get('total') if isinstance(users, dict) else 0)
    except Exception:
        total_users = 0

    try:
        sensors = api_sensor.list_sensors(limit=1, offset=0, token=token) or {}
        total_sensors = sensors.get('total', 0) if isinstance(sensors, dict) else 0
    except Exception:
        total_sensors = 0

    try:
        pumps = api_pump.list_pumps(limit=1, offset=0, token=token) or {}
        total_pumps = pumps.get('total', 0) if isinstance(pumps, dict) else 0
    except Exception:
        total_pumps = 0

    try:
        data = api_sensor_data.get_data_by_pump(limit=1, offset=0, token=token) or {}
        total_data = data.get('total', 0) if isinstance(data, dict) else 0
    except Exception:
        total_data = 0

    # find active users (from users list if returned as list)
    active_users = []
    try:
        if isinstance(users, list):
            for u in users:
                if u.get('trang_thai') in (True, 'active', 'dang_hoat_dong', 1):
                    username = u.get('ten_dang_nhap') or u.get('username') or u.get('ho_ten')
                    active_users.append(username)
    except Exception:
        active_users = []

    # current logged-in username from session
    current_user = session_data.get('username')

    cards = dbc.Row([
        dbc.Col(dbc.Card(dbc.CardBody([html.H6('Tổng người dùng', className='card-title'), html.H3(str(total_users))])), md=3),
        dbc.Col(dbc.Card(dbc.CardBody([html.H6('Tổng cảm biến', className='card-title'), html.H3(str(total_sensors))])), md=3),
        dbc.Col(dbc.Card(dbc.CardBody([html.H6('Tổng máy bơm', className='card-title'), html.H3(str(total_pumps))])), md=3),
        dbc.Col(dbc.Card(dbc.CardBody([html.H6('Tổng bản ghi cảm biến', className='card-title'), html.H3(str(total_data))])), md=3),
    ], className='mb-4')

    activity = dbc.Row([
        dbc.Col(dbc.Card(dbc.CardBody([
            html.H6('Đang đăng nhập', className='card-title'),
            html.P(current_user or 'Không có', className='mb-0')
        ])), md=6),
        dbc.Col(dbc.Card(dbc.CardBody([
            html.H6('Người dùng hoạt động', className='card-title'),
            html.Ul([html.Li(str(u)) for u in (active_users[:10] if active_users else ['Không có'])])
        ])), md=6),
    ], className='mb-4')

    return html.Div([cards, activity])


@callback(
    Output('users-table-container', 'children'),
    Input('admin-users-store', 'data')
)
def render_users_table(users):
    if not users:
        return dbc.Alert('Không tìm thấy người dùng nào.', color='info')

    table_header = [html.Thead(html.Tr([html.Th('#'), html.Th('Tên đăng nhập'), html.Th('Họ tên'), html.Th('SĐT'), html.Th('Trạng thái'), html.Th('Quyền'), html.Th('Hành động')]))]
    rows = []
    for idx, u in enumerate(users, start=1):
        username = u.get('ten_dang_nhap') or u.get('username') or u.get('ma_nguoi_dung')
        fullname = u.get('ho_ten') or ''
        phone = u.get('so_dien_thoai') or ''
        active = u.get('trang_thai', True)
        is_admin = u.get('is_admin') or u.get('vai_tro') == 'admin' or u.get('role') == 'admin'

        actions = dbc.ButtonGroup([
            dbc.Button('Sửa', id={'type': 'edit-user', 'index': username}, size='sm', color='secondary'),
            dbc.Button('Xóa', id={'type': 'delete-user', 'index': username}, size='sm', color='danger')
        ])

        rows.append(html.Tr([
            html.Td(idx),
            html.Td(username),
            html.Td(fullname),
            html.Td(phone),
            html.Td(dbc.Badge('Hoạt động', color='success') if active else dbc.Badge('Ngưng', color='secondary')),
            html.Td('Admin' if is_admin else 'User'),
            html.Td(actions)
        ]))

    table = dbc.Table(table_header + [html.Tbody(rows)], bordered=True, hover=True, responsive=True)
    return table


@callback(
    [Output('user-modal', 'is_open'), Output('modal-title', 'children'), Output('admin-current-username', 'data'),
     Output('user-username', 'value'), Output('user-fullname', 'value'), Output('user-phone', 'value'),
     Output('user-address', 'value'), Output('user-password', 'value'), Output('user-is-admin', 'value'), Output('user-is-active', 'value')],
    [Input('btn-new-user', 'n_clicks'), Input({'type': 'edit-user', 'index': dash.dependencies.ALL}, 'n_clicks')],
    [State('admin-users-store', 'data'), State('session-store', 'data'), State('admin-current-username', 'data')],
    prevent_initial_call=True
)
def open_user_modal(new_click, edit_clicks, users, session_data, current):
    ctx = dash.callback_context
    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate
    triggered = ctx.triggered[0]
    btn = triggered['prop_id'].split('.')[0]
    # ignore falsy n_clicks (None or 0) which can occur when dynamic components are created
    if not triggered.get('value'):
        raise dash.exceptions.PreventUpdate

    # New user
    if btn == 'btn-new-user':
        return True, 'Tạo người dùng mới', None, '', '', '', '', '', False, True

    # Edit user
    try:
        # prop_id like '{"type":"edit-user","index":"username"}.n_clicks'
        if btn.startswith('{') and 'edit-user' in btn:
            import json
            obj = json.loads(btn)
            username = obj.get('index')
            # find user in store
            u = next((x for x in (users or []) if (x.get('ten_dang_nhap') == username or x.get('username') == username or x.get('ma_nguoi_dung') == username)), None)
            if not u:
                return False, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

            is_admin = u.get('is_admin') or u.get('vai_tro') == 'admin' or u.get('role') == 'admin'
            active = u.get('trang_thai', True)
            return True, 'Chỉnh sửa người dùng', username, username, u.get('ho_ten') or '', u.get('so_dien_thoai') or '', u.get('dia_chi') or '', '', is_admin, active
    except Exception:
        pass

    raise dash.exceptions.PreventUpdate


@callback(
    Output('admin-users-store', 'data', allow_duplicate=True),
    [Input('save-user-btn', 'n_clicks'), Input('confirm-delete-btn', 'n_clicks')],
    [State('admin-current-username', 'data'), State('user-username', 'value'), State('user-fullname', 'value'),
     State('user-phone', 'value'), State('user-address', 'value'), State('user-password', 'value'),
     State('user-is-admin', 'value'), State('user-is-active', 'value'), State('session-store', 'data')],
    prevent_initial_call=True
)
def handle_save_or_delete(save_click, del_click, current_username, username, fullname, phone, address, password, is_admin, is_active, session_data):
    ctx = dash.callback_context
    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate
    action = ctx.triggered[0]['prop_id'].split('.')[0]

    if not session_data or not session_data.get('authenticated') or not session_data.get('is_admin'):
        raise dash.exceptions.PreventUpdate

    token = session_data.get('token')

    if action == 'save-user-btn':
        # If current_username is None -> create
        data = {
            'ten_dang_nhap': username,
            'ho_ten': fullname or '',
            'so_dien_thoai': phone or '',
            'dia_chi': address or '',
            'trang_thai': bool(is_active),
        }
        # role / is_admin mapping
        if is_admin:
            data['vai_tro'] = 'admin'

        if not current_username:
            if password:
                data['mat_khau'] = password
            success, msg = api_user.create_user(data, token=token)
        else:
            # update
            if password:
                data['mat_khau'] = password
            success, msg = api_user.update_user(current_username, data, token=token)

        # refresh list
        users = api_user.list_users(token=token)
        return users or []

    if action == 'confirm-delete-btn':
        if not current_username:
            raise dash.exceptions.PreventUpdate
        success, msg = api_user.delete_user(current_username, token=token)
        users = api_user.list_users(token=token)
        return users or []

    raise dash.exceptions.PreventUpdate


@callback(
    [Output('user-modal', 'is_open', allow_duplicate=True), Output('delete-modal', 'is_open', allow_duplicate=True), Output('admin-current-username', 'data', allow_duplicate=True), Output('delete-confirm-body', 'children')],
    [Input('cancel-user-btn', 'n_clicks'), Input('cancel-delete-btn', 'n_clicks'), Input({'type': 'delete-user', 'index': dash.dependencies.ALL}, 'n_clicks')],
    [State('admin-current-username', 'data'), State('admin-users-store', 'data')],
    prevent_initial_call=True
)
def handle_modals(cancel_user, cancel_delete, delete_clicks, current, users):
    ctx = dash.callback_context
    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate
    triggered = ctx.triggered[0]
    btn = triggered['prop_id'].split('.')[0]
    # ignore falsy n_clicks (None or 0) to avoid auto-opening modals on render
    if not triggered.get('value'):
        raise dash.exceptions.PreventUpdate

    if btn == 'cancel-user-btn':
        return False, dash.no_update, None, dash.no_update

    if btn == 'cancel-delete-btn':
        return dash.no_update, False, None, dash.no_update

    # delete click
    try:
        if btn.startswith('{') and 'delete-user' in btn:
            import json
            obj = json.loads(btn)
            username = obj.get('index')
            return dash.no_update, True, username, f"Bạn có chắc chắn muốn xóa người dùng '{username}'?"
    except Exception:
        pass

    raise dash.exceptions.PreventUpdate
