from dash import html, dcc, callback, Input, Output, State
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
from components.navbar import create_navbar
from api.pump import list_pumps, create_pump, update_pump, delete_pump, get_pump
import dash
import datetime


def _pump_row_item(p):
    return html.Tr([
        html.Td(p.get('ma_may_bom')),
        html.Td(p.get('ten_may_bom')),
        html.Td(p.get('mo_ta')),
        html.Td(p.get('ma_iot_lk') or ''),
        html.Td(p.get('che_do')),
        html.Td(str(p.get('trang_thai'))),
        html.Td(dbc.ButtonGroup([
            dbc.Button(html.I(className='fas fa-edit'), id={'type': 'edit-pump', 'index': p.get('ma_may_bom')}, color='warning', size='sm'),
            dbc.Button(html.I(className='fas fa-trash'), id={'type': 'delete-pump', 'index': p.get('ma_may_bom')}, color='danger', size='sm')
        ]))
    ])


layout = html.Div([
    create_navbar(is_authenticated=True),
    dbc.Container([
        dbc.Row([
            dbc.Col(html.H3('Quản lý máy bơm'), width=8),
            dbc.Col(dbc.Button('Thêm máy bơm', id='open-add-pump', color='primary'), width=4, className='text-end')
        ], className='my-3'),

        dbc.Row([
            dbc.Col(dbc.Input(id='pump-search', placeholder='Tìm kiếm (tên, mô tả, mã IoT)', type='text'))
        ], className='mb-3', style={"max-width": "400px"}),

        dbc.Row([
            dbc.Col(dcc.Loading(html.Div(id='pump-table-container')))
        ]),

    dcc.Store(id='pump-data-store'),
    dcc.Store(id='pump-delete-id'),

        dbc.Modal([
            dbc.ModalHeader(id='pump-modal-title'),
            dbc.ModalBody([
                dbc.Form([
                    dbc.Label('Tên máy bơm'),
                    dbc.Input(id='pump-ten', type='text'),
                    dbc.Label('Mô tả', className='mt-2'),
                    dbc.Textarea(id='pump-mo-ta'),
                    dbc.Label('Mã IoT liên kết', className='mt-2'),
                    dbc.Input(id='pump-ma-iot', type='text'),
                    dbc.Label('Chế độ', className='mt-2'),
                    dbc.Input(id='pump-che-do', type='number', value=0),
                    dbc.Label('Trạng thái', className='mt-2'),
                    dcc.Dropdown(id='pump-trang-thai', options=[{'label': 'Tắt', 'value': False}, {'label': 'Bật', 'value': True}], value=False, clearable=False),
                    dcc.Store(id='pump-edit-id')
                ])
            ]),
            dbc.ModalFooter([
                dbc.Button('Lưu', id='pump-save', color='primary'),
                dbc.Button('Đóng', id='pump-cancel', className='ms-2')
            ])
        ], id='pump-modal', is_open=False, centered=True),

        dbc.Modal([
            dbc.ModalHeader('Xác nhận xóa'),
            dbc.ModalBody(html.Div(id='confirm-delete-body', children='Bạn có chắc chắn muốn xóa máy bơm này?')),
            dbc.ModalFooter([
                dbc.Button('Xóa', id='confirm-delete-pump', color='danger'),
                dbc.Button('Hủy', id='confirm-cancel-pump', className='ms-2')
            ])
        ], id='confirm-delete-pump-modal', is_open=False, centered=True)

    ], fluid=True)
], className='page-container', style={"paddingTop": "20px"})


@callback(
    Output('pump-data-store', 'data', allow_duplicate=True),
    Input('url', 'pathname'),
    State('session-store', 'data'),
    prevent_initial_call='initial_duplicate'
)
def load_pumps(pathname, session_data):
    if pathname != '/pump':
        raise PreventUpdate
    token = None
    if session_data and isinstance(session_data, dict):
        token = session_data.get('token')
    data = list_pumps(limit=200, offset=0, token=token)
    return data


@callback(
    Output('pump-table-container', 'children'),
    [Input('pump-data-store', 'data'), Input('pump-search', 'value')]
)
def render_pump_table(data, search):
    if not data or 'data' not in data:
        return dbc.Alert('Không có dữ liệu máy bơm.', color='info')

    rows = []
    for p in data.get('data', []):
        text = ' '.join([
            str(p.get('ten_may_bom') or ''),
            str(p.get('mo_ta') or ''),
            str(p.get('ma_iot_lk') or '')
        ])
        if search and search.strip().lower() not in text.lower():
            continue
        rows.append(_pump_row_item(p))

    table = dbc.Table([
        html.Thead(html.Tr([html.Th('ID'), html.Th('Tên'), html.Th('Mô tả'), html.Th('Mã IoT'), html.Th('Chế độ'), html.Th('Trạng thái'), html.Th('Thao tác')])),
        html.Tbody(rows)
    ], bordered=True, hover=True, responsive=True)

    return table


@callback(
    [Output('pump-modal', 'is_open'), Output('pump-modal-title', 'children'), Output('pump-edit-id', 'data'), Output('pump-ten', 'value'), Output('pump-mo-ta', 'value'), Output('pump-ma-iot', 'value'), Output('pump-che-do', 'value'), Output('pump-trang-thai', 'value')],
    [Input('open-add-pump', 'n_clicks'), Input({'type': 'edit-pump', 'index': dash.ALL}, 'n_clicks'), Input('pump-cancel', 'n_clicks')],
    [State('pump-data-store', 'data')],
    prevent_initial_call=True
)
def open_pump_modal(n_add, edit_clicks, n_cancel, store):
    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate
    btn = ctx.triggered[0]['prop_id'].split('.')[0]
    trig_value = ctx.triggered[0].get('value')
    if not trig_value:
        raise PreventUpdate
    # add
    if btn == 'open-add-pump':
        return True, 'Thêm máy bơm', None, '', '', '', 0, False

    if 'edit-pump' in btn:
        try:
            import json as _json
            obj = _json.loads(btn)
            idx = int(obj.get('index'))
        except Exception:
            raise PreventUpdate
        p = None
        for it in (store.get('data') or []):
            if it.get('ma_may_bom') == idx:
                p = it
                break
        if not p:
            raise PreventUpdate
    # when editing
    return True, 'Sửa máy bơm', idx, p.get('ten_may_bom'), p.get('mo_ta'), p.get('ma_iot_lk'), p.get('che_do'), p.get('trang_thai')


@callback(
    [Output('pump-data-store', 'data', allow_duplicate=True), Output('pump-modal', 'is_open', allow_duplicate=True)],
    [Input('pump-save', 'n_clicks')],
    [State('pump-edit-id', 'data'), State('pump-ten', 'value'), State('pump-mo-ta', 'value'), State('pump-ma-iot', 'value'), State('pump-che-do', 'value'), State('pump-trang-thai', 'value'), State('pump-data-store', 'data'), State('session-store', 'data')],
    prevent_initial_call=True
)
def save_pump(n_save, edit_id, ten, mo_ta, ma_iot, che_do, trang_thai, store, session_data):
    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate
    prop = ctx.triggered[0]['prop_id'].split('.')[0]
    token = None
    if session_data and isinstance(session_data, dict):
        token = session_data.get('token')

    if prop == 'pump-save':
        payload = {
            'ten_may_bom': ten,
            'mo_ta': mo_ta,
            'ma_iot_lk': ma_iot,
            'che_do': int(che_do) if che_do is not None else 0,
            'trang_thai': bool(trang_thai) if trang_thai is not None else False
        }
        if edit_id:
            update_pump(edit_id, payload, token=token)
        else:
            create_pump(payload, token=token)

        data = list_pumps(limit=200, offset=0, token=token)
        return data, False

    raise PreventUpdate


@callback(
    [Output('confirm-delete-pump-modal', 'is_open', allow_duplicate=True), Output('pump-delete-id', 'data')],
    Input({'type': 'delete-pump', 'index': dash.ALL}, 'n_clicks'),
    prevent_initial_call='initial_duplicate'
)
def open_confirm_on_delete(delete_clicks):
    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate
    trig = ctx.triggered[0]
    trig_value = trig.get('value')
    if not trig_value:
        raise PreventUpdate
    prop = trig['prop_id'].split('.')[0]
    try:
        import json as _json
        obj = _json.loads(prop)
        idx = int(obj.get('index'))
    except Exception:
        raise PreventUpdate
    return True, idx


@callback(
    [Output('pump-data-store', 'data', allow_duplicate=True), Output('confirm-delete-pump-modal', 'is_open', allow_duplicate=True), Output('pump-modal', 'is_open', allow_duplicate=True)],
    Input('confirm-delete-pump', 'n_clicks'),
    [State('pump-delete-id', 'data'), State('session-store', 'data')],
    prevent_initial_call='initial_duplicate'
)
def perform_delete(n_confirm, delete_id, session_data):
    if not n_confirm:
        raise PreventUpdate
    token = None
    if session_data and isinstance(session_data, dict):
        token = session_data.get('token')
    success, msg = delete_pump(delete_id, token=token)
    data = list_pumps(limit=200, offset=0, token=token)
    return data, False, False


@callback(
    Output('confirm-delete-pump-modal', 'is_open', allow_duplicate=True),
    Input('confirm-cancel-pump', 'n_clicks'),
    prevent_initial_call='initial_duplicate'
)
def cancel_confirm(n):
    if not n:
        raise PreventUpdate
    return False
