from dash import html, dcc, callback, Input, Output, State
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
from components.navbar import create_navbar
from components.topbar import TopBar
from api.sensor import list_sensors, create_sensor, update_sensor, delete_sensor, get_sensor, get_sensor_types
import dash
import datetime


def _sensor_row_row_item(s):
    return html.Tr([
        html.Td(s.get('ma_cam_bien')),
        html.Td(s.get('ten_cam_bien')),
        html.Td(s.get('mo_ta')),
        html.Td(s.get('ten_may_bom') or ''),
        html.Td(s.get('ten_loai_cam_bien') or ''),
        html.Td(s.get('ngay_lap_dat')),
        html.Td(dbc.ButtonGroup([
            dbc.Button(html.I(className='fas fa-edit'), id={'type': 'edit-sensor', 'index': s.get('ma_cam_bien')}, color='warning', size='sm'),
            dbc.Button(html.I(className='fas fa-trash'), id={'type': 'delete-sensor', 'index': s.get('ma_cam_bien')}, color='danger', size='sm')
        ]))
    ])


layout = html.Div([
    create_navbar(is_authenticated=True),
    
    dbc.Container([
        dbc.Row([dbc.Col(TopBar('Quản lý cảm biến', search_id='sensor-search', add_button={'id':'open-add-sensor','label':'Thêm cảm biến'}))], className='my-3'),

        dbc.Row([
            dbc.Col(dcc.Loading(html.Div(id='sensor-table-container')))
        ]),
        dbc.Row([
            dbc.Col(html.Div(id='sensor-total', className='pt-2')),
        ], className='mt-2'),

        dbc.Row([
            dbc.Col(html.Div(className='pagination-footer', children=[html.Div(id='sensor-pagination')]))
        ]),

    dcc.Store(id='sensor-data-store'),
    dcc.Store(id='sensor-types-store'),
    dcc.Store(id='sensor-selected-type'),
    dcc.Store(id='sensor-delete-id'),
    dcc.Store(id='sensor-page-store', data={'page': 1, 'limit': 20}),
    dcc.Store(id='sensor-pagination-store', data={'max': 1}),

        dbc.Modal([
            dbc.ModalHeader(id='sensor-modal-title'),
            dbc.ModalBody([
                dbc.Form([
                    dbc.Label('Tên cảm biến'),
                    dbc.Input(id='sensor-ten', type='text'),
                    dbc.Label('Mô tả', className='mt-2'),
                    dbc.Textarea(id='sensor-mo-ta'),
                    dbc.Label('Mã máy bơm', className='mt-2'),
                    dbc.Input(id='sensor-ma-may-bom', type='number', value=1),
                    dbc.Label('Ngày lắp đặt', className='mt-2'),
                    dbc.Input(id='sensor-ngay-lap-dat', type='date', value=str(datetime.date.today())),
                    dbc.Label('Loại cảm biến', className='mt-2'),
                    dcc.Dropdown(id='sensor-loai', options=[], value=None, placeholder='Chọn loại cảm biến', clearable=False),
                    dcc.Store(id='sensor-edit-id')
                ])
            ]),
            dbc.ModalFooter([
                dbc.Button('Lưu', id='sensor-save', color='primary'),
                dbc.Button('Đóng', id='sensor-cancel', className='ms-2')
            ])
        ], id='sensor-modal', is_open=False, centered=True)

        ,
        dbc.Modal([
            dbc.ModalHeader('Xác nhận xóa'),
            dbc.ModalBody(html.Div(id='confirm-delete-body', children='Bạn có chắc chắn muốn xóa cảm biến này?')),
            dbc.ModalFooter([
                dbc.Button('Xóa', id='confirm-delete', color='danger'),
                dbc.Button('Hủy', id='confirm-cancel', className='ms-2')
            ])
        ], id='confirm-delete-modal', is_open=False, centered=True)

    ], fluid=True)
], className='page-container', style={"paddingTop": "20px"})


@callback(
    [Output('sensor-data-store', 'data', allow_duplicate=True), Output('sensor-pagination-store', 'data'), Output('sensor-total', 'children')],
    [Input('url', 'pathname'), Input('sensor-page-store', 'data')],
    State('session-store', 'data'),
    prevent_initial_call='initial_duplicate'
)
def load_sensors(pathname, page_store, session_data):
    if pathname != '/sensor':
        raise PreventUpdate
    token = None
    if session_data and isinstance(session_data, dict):
        token = session_data.get('token')
    page = 1
    limit = 20
    if page_store and isinstance(page_store, dict):
        page = int(page_store.get('page', 1))
        limit = int(page_store.get('limit', 20))
    offset = (page - 1) * limit
    data = {'data': []}
    max_pages = 1
    total_text = 'Tổng: 0'
    try:
        data = list_sensors(limit=limit, offset=offset, token=token)
        if isinstance(data, dict) and data.get('total') is not None:
            total = int(data.get('total') or 0)
            max_pages = max(1, (total + limit - 1) // limit)
            total_text = f'Tổng: {total}'
        else:
            total = len(data.get('data') or [])
            total_text = f'Tổng: {total}'
    except Exception:
        data = {'data': []}
        max_pages = 1
        total_text = 'Tổng: 0'
    return data, {'max': max_pages}, total_text


@callback(
    Output('sensor-types-store', 'data'),
    Input('url', 'pathname'),
    State('session-store', 'data')
)
def load_sensor_types(pathname, session_data):
    if pathname != '/sensor':
        raise PreventUpdate
    token = None
    if session_data and isinstance(session_data, dict):
        token = session_data.get('token')
    types = get_sensor_types(token=token)
    return types


@callback(
    Output('sensor-loai', 'options'),
    Input('sensor-types-store', 'data')
)
def populate_type_options(types_data):
    if not types_data or not isinstance(types_data, dict):
        return []
    items = types_data.get('data') or []
    opts = []
    for it in items:
        ma = it.get('ma_loai_cam_bien')
        ten = it.get('ten_loai_cam_bien')
        if ma is None:
            continue
        opts.append({'label': str(ten or ma), 'value': ma})
    return opts

@callback(
    Output('sensor-selected-type', 'data'),
    Input('sensor-loai', 'value'),
    State('sensor-loai', 'options'),
    prevent_initial_call=True
)
def store_selected_type(value, options):
    if value is None:
        return None
    label = None
    if options and isinstance(options, (list, tuple)):
        for opt in options:
            if opt.get('value') == value:
                label = opt.get('label')
                break
    return {'ma_loai_cam_bien': int(value) if isinstance(value, (int, str)) and str(value).isdigit() else value, 'ten_loai_cam_bien': label}


def _build_sensor_pagination(current, max_pages, window=3):
    items = []
    prev_disabled = (current <= 1)
    items.append(dbc.Button(html.I(className='fas fa-chevron-left'), id={'type': 'sensor-page-prev', 'index': 'prev'}, color='light', size='sm', className='me-1', disabled=prev_disabled))

    def page_button(p):
        active = (p == current)
        return dbc.Button(str(p), id={'type': 'sensor-page', 'index': str(p)}, color='primary' if active else 'light', size='sm', className='me-1')

    if max_pages <= 7:
        for p in range(1, max_pages+1):
            items.append(page_button(p))
    else:
        left = max(1, current - window)
        right = min(max_pages, current + window)
        if left > 1:
            items.append(page_button(1))
            if left > 2:
                items.append(html.Span('...', className='mx-1'))
        for p in range(left, right+1):
            items.append(page_button(p))
        if right < max_pages:
            if right < max_pages - 1:
                items.append(html.Span('...', className='mx-1'))
            items.append(page_button(max_pages))

    next_disabled = (current >= max_pages)
    items.append(dbc.Button(html.I(className='fas fa-chevron-right'), id={'type': 'sensor-page-next', 'index': 'next'}, color='light', size='sm', className='ms-1', disabled=next_disabled))
    return dbc.ButtonGroup(items)


@callback(
    Output('sensor-pagination', 'children'),
    [Input('sensor-pagination-store', 'data'), Input('sensor-page-store', 'data')]
)
def render_sensor_pagination(pagination_meta, page_store):
    max_pages = 1
    current = 1
    try:
        if pagination_meta and isinstance(pagination_meta, dict):
            max_pages = int(pagination_meta.get('max', 1) or 1)
    except Exception:
        max_pages = 1
    try:
        if page_store and isinstance(page_store, dict):
            current = int(page_store.get('page', 1) or 1)
    except Exception:
        current = 1
    if current < 1:
        current = 1
    if current > max_pages:
        current = max_pages
    return _build_sensor_pagination(current, max_pages)


@callback(
    Output('sensor-page-store', 'data'),
    [Input({'type': 'sensor-page', 'index': dash.ALL}, 'n_clicks'), Input({'type': 'sensor-page-prev', 'index': dash.ALL}, 'n_clicks'), Input({'type': 'sensor-page-next', 'index': dash.ALL}, 'n_clicks')],
    State('sensor-page-store', 'data'), State('sensor-pagination-store', 'data'),
    prevent_initial_call=True
)
def handle_sensor_pagination_click(page_clicks, prev_clicks, next_clicks, current, pagination_meta):
    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate
    trig = ctx.triggered[0]
    pid = trig['prop_id'].split('.')[0]
    try:
        import json
        obj = json.loads(pid)
    except Exception:
        raise PreventUpdate
    data = current or {'page': 1, 'limit': 20}
    max_pages = 1
    try:
        if pagination_meta and isinstance(pagination_meta, dict):
            max_pages = int(pagination_meta.get('max', 1) or 1)
    except Exception:
        max_pages = 1
    t = obj.get('type')
    idx = obj.get('index')
    if t == 'sensor-page':
        target = int(idx)
        if target < 1:
            target = 1
        if target > max_pages:
            target = max_pages
        data['page'] = target
        return data
    if t == 'sensor-page-prev':
        data['page'] = max(1, int(data.get('page', 1)) - 1)
        return data
    if t == 'sensor-page-next':
        nextp = int(data.get('page', 1)) + 1
        if nextp > max_pages:
            nextp = max_pages
        data['page'] = nextp
        return data
    raise PreventUpdate

@callback(
    Output('sensor-types-store', 'data', allow_duplicate=True),
    [Input('open-add-sensor', 'n_clicks'), Input({'type': 'edit-sensor', 'index': dash.ALL}, 'n_clicks')],
    State('session-store', 'data'),
    prevent_initial_call='initial_duplicate'
)
def fetch_types_on_modal_open(n_add, edit_clicks, session_data):
    ctx = dash.callback_context
    
    if not ctx.triggered:
        raise PreventUpdate
    trig_value = ctx.triggered[0].get('value')
    
    if not trig_value:
        raise PreventUpdate

    token = None
    if session_data and isinstance(session_data, dict):
        token = session_data.get('token')
    types = get_sensor_types(token=token)
    return types


@callback(
    Output('sensor-table-container', 'children'),
    [Input('sensor-data-store', 'data'), Input('sensor-search', 'value')]
)
def render_table(data, search):
    if not data or 'data' not in data or not data.get('data'):
        return html.Div(className='empty-state', children=[
            html.Div(className='empty-icon', children=[html.Img(src='/assets/img/empty-box.svg', style={'width':'64px','height':'64px'})]),
            html.Div('Không có dữ liệu cảm biến.', className='empty-text')
        ])

    rows = []
    items = list(data.get('data', []) or [])
    try:
        items.sort(key=lambda x: int(x.get('ma_cam_bien') or 0))
    except Exception:
        items = items
    for s in items:
        text = ' '.join([
            str(s.get('ten_cam_bien') or ''),
            str(s.get('mo_ta') or ''),
            str(s.get('ten_may_bom') or ''),
            str(s.get('ten_loai_cam_bien') or '')
        ])
        if search and search.strip().lower() not in text.lower():
            continue
        rows.append(_sensor_row_row_item(s))

    table = dbc.Table([
        html.Thead(html.Tr([html.Th('ID'), html.Th('Tên'), html.Th('Mô tả'), html.Th('Tên máy bơm'), html.Th('Loại cảm biến'), html.Th('Ngày lắp đặt'), html.Th('Thao tác')])),
        html.Tbody(rows)
    ], bordered=True, hover=True, responsive=True)

    return table


@callback(
    [Output('sensor-modal', 'is_open'), Output('sensor-modal-title', 'children'), Output('sensor-edit-id', 'data'), Output('sensor-ten', 'value'), Output('sensor-mo-ta', 'value'), Output('sensor-ma-may-bom', 'value'), Output('sensor-ngay-lap-dat', 'value'), Output('sensor-loai', 'value'), Output('sensor-save', 'children')],
    [Input('open-add-sensor', 'n_clicks'), Input({'type': 'edit-sensor', 'index': dash.ALL}, 'n_clicks'), Input('sensor-cancel', 'n_clicks')],
    [State('sensor-data-store', 'data')],
    prevent_initial_call=True
)
def open_modal(n_add, edit_clicks, n_cancel, store):
    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate
    btn = ctx.triggered[0]['prop_id'].split('.')[0]
    trig_value = ctx.triggered[0].get('value')
    if not trig_value:
        raise PreventUpdate
    # add
    if btn == 'open-add-sensor':
        # when adding, set save button label to 'Thêm'
        return True, 'Thêm cảm biến', None, '', '', 1, str(datetime.date.today()), None, 'Thêm'

    if 'edit-sensor' in btn:
        try:
            import json as _json
            obj = _json.loads(btn)
            idx = int(obj.get('index'))
        except Exception:
            raise PreventUpdate
        s = None
        for it in (store.get('data') or []):
            if it.get('ma_cam_bien') == idx:
                s = it
                break
        if not s:
            raise PreventUpdate
        sel_loai = s.get('ma_loai_cam_bien') if s.get('ma_loai_cam_bien') is not None else s.get('loai')
    # when editing, keep save button label as 'Lưu'
    return True, 'Sửa cảm biến', idx, s.get('ten_cam_bien'), s.get('mo_ta'), s.get('ma_may_bom'), s.get('ngay_lap_dat'), sel_loai, 'Lưu'

    return False, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update


@callback(
    [Output('sensor-data-store', 'data', allow_duplicate=True), Output('sensor-modal', 'is_open', allow_duplicate=True)],
    [Input('sensor-save', 'n_clicks')],
    [State('sensor-edit-id', 'data'), State('sensor-ten', 'value'), State('sensor-mo-ta', 'value'), State('sensor-ma-may-bom', 'value'), State('sensor-ngay-lap-dat', 'value'), State('sensor-loai', 'value'), State('sensor-selected-type', 'data'), State('sensor-data-store', 'data'), State('session-store', 'data')],
    prevent_initial_call=True
)
def save_or_delete(n_save, edit_id, ten, mo_ta, ma_may_bom, ngay_lap_dat, loai, sensor_selected_type, store, session_data):
    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate
    prop = ctx.triggered[0]['prop_id'].split('.')[0]
    token = None
    if session_data and isinstance(session_data, dict):
        token = session_data.get('token')

    if prop == 'sensor-save':
        final_loai = None
        if sensor_selected_type and isinstance(sensor_selected_type, dict):
            final_loai = sensor_selected_type.get('ma_loai_cam_bien')
            print(final_loai)
        else:
            final_loai = loai

        try:
            ma_loai_val = int(final_loai) if final_loai is not None else None
        except Exception:
            ma_loai_val = final_loai

        payload = {
            'ten_cam_bien': ten,
            'mo_ta': mo_ta,
            'ma_may_bom': int(ma_may_bom) if ma_may_bom is not None else 0,
            'ngay_lap_dat': ngay_lap_dat,
            'loai': ma_loai_val
        }
        if edit_id:
            update_sensor(edit_id, payload, token=token)
        else:
            create_sensor(payload, token=token)

        data = list_sensors(limit=20, offset=0, token=token)
        # close modal after save
        return data, False

    raise PreventUpdate



@callback(
    [Output('confirm-delete-modal', 'is_open', allow_duplicate=True), Output('sensor-delete-id', 'data')],
    Input({'type': 'delete-sensor', 'index': dash.ALL}, 'n_clicks'),
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
    [Output('sensor-data-store', 'data', allow_duplicate=True), Output('confirm-delete-modal', 'is_open', allow_duplicate=True), Output('sensor-modal', 'is_open', allow_duplicate=True)],
    Input('confirm-delete', 'n_clicks'),
    [State('sensor-delete-id', 'data'), State('session-store', 'data')],
    prevent_initial_call='initial_duplicate'
)
def perform_delete(n_confirm, delete_id, session_data):
    if not n_confirm:
        raise PreventUpdate
    token = None
    if session_data and isinstance(session_data, dict):
        token = session_data.get('token')
    success, msg = delete_sensor(delete_id, token=token)
    data = list_sensors(limit=20, offset=0, token=token)
    # ensure any sensor modal is closed as well
    return data, False, False


@callback(
    Output('confirm-delete-modal', 'is_open', allow_duplicate=True),
    Input('confirm-cancel', 'n_clicks'),
    prevent_initial_call='initial_duplicate'
)
def cancel_confirm(n):
    if not n:
        raise PreventUpdate
    return False
