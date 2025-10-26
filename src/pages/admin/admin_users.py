from dash import html, dcc, callback, Input, Output, State
import dash_bootstrap_components as dbc
import dash
from components.navbar import create_navbar
from api import user as api_user


layout = html.Div([
    create_navbar(is_authenticated=True, is_admin=True),
    dcc.Location(id='admin-users-url', refresh=False),
    dcc.Store(id='admin-users-page-store', data=[]),

    dbc.Container([
        dbc.Row([
            dbc.Col(html.H2([html.I(className='fas fa-users me-2'), 'Quản lý người dùng']), md=9),
            dbc.Col(dbc.Button([html.I(className='fas fa-plus me-2'), 'Tạo người dùng mới'], id='btn-new-user-users', color='primary'), md=3, className='text-end')
        ], className='my-3'),

        dbc.Row([
            dbc.Col(dcc.Loading(id='loading-users-table-users', children=html.Div(id='users-table-container-users')))
        ]),

        dbc.Modal([
            dbc.ModalHeader(html.H5(id='modal-title-users')),
            dbc.ModalBody([
                dbc.Form([
                    dbc.Row([
                        dbc.Col(dbc.Label('Tên đăng nhập', className='fw-bold'), md=12),
                        dbc.Col(dbc.Input(id='user-username-users', type='text'), md=12),
                    ]),
                    dbc.Row([
                        dbc.Col(dbc.Label('Họ tên', className='fw-bold'), md=12),
                        dbc.Col(dbc.Input(id='user-fullname-users', type='text'), md=12),
                    ]),
                    dbc.Row([
                        dbc.Col(dbc.Label('Số điện thoại', className='fw-bold'), md=12),
                        dbc.Col(dbc.Input(id='user-phone-users', type='text'), md=12),
                    ]),
                    dbc.Row([
                        dbc.Col(dbc.Label('Địa chỉ', className='fw-bold'), md=12),
                        dbc.Col(dbc.Input(id='user-address-users', type='text'), md=12),
                    ]),
                    dbc.Row([
                        dbc.Col(dbc.Label('Mật khẩu (chỉ tạo hoặc khi đổi)', className='fw-bold small'), md=12),
                        dbc.Col(dbc.Input(id='user-password-users', type='password'), md=12),
                    ]),
                    dbc.Row([
                        dbc.Col(dbc.Checkbox(id='user-is-admin-users', label='Quyền admin'), md=6),
                        dbc.Col(dbc.Checkbox(id='user-is-active-users', label='Hoạt động', value=True), md=6),
                    ])
                ])
            ]),
            dbc.ModalFooter([
                dbc.Button('Lưu', id='save-user-btn-users', color='primary'),
                dbc.Button('Hủy', id='cancel-user-btn-users', className='ms-2')
            ])
        ], id='user-modal-users', is_open=False, size='lg'),

        dcc.Store(id='admin-current-username-users', data=None),

        dbc.Modal([
            dbc.ModalHeader('Xác nhận xóa'),
            dbc.ModalBody(html.Div(id='delete-confirm-body-users')),
            dbc.ModalFooter([
                dbc.Button('Xóa', id='confirm-delete-btn-users', color='danger'),
                dbc.Button('Hủy', id='cancel-delete-btn-users', className='ms-2')
            ])
        ], id='delete-modal-users', is_open=False)

    ], fluid=True, className='py-4')
])


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
    Output('users-table-container-users', 'children'),
    Input('admin-users-page-store', 'data')
)
def render_users_table_users(users):
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
            dbc.Button('Sửa', id={'type': 'edit-user-users', 'index': username}, size='sm', color='secondary'),
            dbc.Button('Xóa', id={'type': 'delete-user-users', 'index': username}, size='sm', color='danger')
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
    [Output('user-modal-users', 'is_open'), Output('modal-title-users', 'children'), Output('admin-current-username-users', 'data'),
     Output('user-username-users', 'value'), Output('user-fullname-users', 'value'), Output('user-phone-users', 'value'),
     Output('user-address-users', 'value'), Output('user-password-users', 'value'), Output('user-is-admin-users', 'value'), Output('user-is-active-users', 'value')],
    [Input('btn-new-user-users', 'n_clicks'), Input({'type': 'edit-user-users', 'index': dash.dependencies.ALL}, 'n_clicks')],
    [State('admin-users-page-store', 'data'), State('session-store', 'data'), State('admin-current-username-users', 'data')],
    prevent_initial_call=True
)
def open_user_modal_users(new_click, edit_clicks, users, session_data, current):
    ctx = dash.callback_context
    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate
    triggered = ctx.triggered[0]
    btn = triggered['prop_id'].split('.')[0]
    if not triggered.get('value'):
        raise dash.exceptions.PreventUpdate

    if btn == 'btn-new-user-users':
        return True, 'Tạo người dùng mới', None, '', '', '', '', '', False, True

    try:
        if btn.startswith('{') and 'edit-user-users' in btn:
            import json
            obj = json.loads(btn)
            username = obj.get('index')
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
    Output('admin-users-page-store', 'data', allow_duplicate=True),
    [Input('save-user-btn-users', 'n_clicks'), Input('confirm-delete-btn-users', 'n_clicks')],
    [State('admin-current-username-users', 'data'), State('user-username-users', 'value'), State('user-fullname-users', 'value'),
     State('user-phone-users', 'value'), State('user-address-users', 'value'), State('user-password-users', 'value'),
     State('user-is-admin-users', 'value'), State('user-is-active-users', 'value'), State('session-store', 'data')],
    prevent_initial_call=True
)
def handle_save_or_delete_users(save_click, del_click, current_username, username, fullname, phone, address, password, is_admin, is_active, session_data):
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
        }
        if is_admin:
            data['vai_tro'] = 'admin'

        if not current_username:
            if password:
                data['mat_khau'] = password
            success, msg = api_user.create_user(data, token=token)
        else:
            if password:
                data['mat_khau'] = password
            success, msg = api_user.update_user(current_username, data, token=token)

        users = api_user.list_users(token=token)
        return users or []

    if action == 'confirm-delete-btn-users':
        if not current_username:
            raise dash.exceptions.PreventUpdate
        success, msg = api_user.delete_user(current_username, token=token)
        users = api_user.list_users(token=token)
        return users or []

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
            username = obj.get('index')
            return dash.no_update, True, username, f"Bạn có chắc chắn muốn xóa người dùng '{username}'?"
    except Exception:
        pass

    raise dash.exceptions.PreventUpdate
