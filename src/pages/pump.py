from dash import html, dcc, callback, Input, Output, State
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
from components.navbar import create_navbar
from components.topbar import TopBar
from api.pump import list_pumps, create_pump, update_pump, delete_pump, get_pump
from api.memory_pump import get_pump_memory_logs
import dash
import datetime
import pandas as pd


def _pump_row_item(p):
    return html.Tr([
        html.Td(p.get('ma_may_bom')),
        html.Td(p.get('ten_may_bom')),
        html.Td(p.get('mo_ta')),
        html.Td(p.get('ma_iot_lk') or ''),
        html.Td(p.get('che_do')),
    html.Td('Bật' if p.get('trang_thai') else 'Tắt'),
        html.Td(dbc.ButtonGroup([
            dbc.Button('Nhật ký', id={'type': 'memory-pump', 'index': p.get('ma_may_bom')}, className='btn-action btn-outline-detail', size='sm'),
            html.Div(style={'width':'4px'}),
            dbc.Button('Sửa', id={'type': 'edit-pump', 'index': p.get('ma_may_bom')}, className='btn-action btn-outline-edit', size='sm'),
            html.Div(style={'width':'4px'}),
            dbc.Button('Xóa', id={'type': 'delete-pump', 'index': p.get('ma_may_bom')}, className='btn-action btn-outline-delete', size='sm'),
        ]), className='col-action')
    ])


layout = html.Div([
    create_navbar(is_authenticated=True),
    dbc.Container([
        dbc.Row([dbc.Col(TopBar('Quản lý máy bơm', search_id='pump-search', add_button={'id':'open-add-pump','label':'Thêm máy bơm'}))], className='my-3'),

        dbc.Row([
            dbc.Col(html.Div(className='table-area', children=[
                dcc.Loading(html.Div(id='pump-table-container')),
                html.Div(className='pagination-footer', children=[html.Div(id='pump-pagination'), html.Div(id='pump-total', className='pt-2 total-text')])
            ]))
        ]),

        dcc.Store(id='pump-data-store'),
        dcc.Store(id='pump-page-store', data={'page': 1, 'limit': 20}),
        dcc.Store(id='pump-pagination-store', data={'max': 1}),
        dcc.Store(id='pump-delete-id'),
        dcc.Interval(id='pump-interval', interval=5*1000, n_intervals=0),

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
                dbc.Button('Lưu', id='pump-save', className='btn-edit'),
                dbc.Button('Đóng', id='pump-cancel', className='ms-2 btn-cancel')
            ])
        ], id='pump-modal', is_open=False, centered=True),

        dbc.Modal([
            dbc.ModalHeader('Xác nhận xóa'),
            dbc.ModalBody(html.Div(id='confirm-delete-body', children='Bạn có chắc chắn muốn xóa máy bơm này?')),
            dbc.ModalFooter([
                dbc.Button('Xóa', id='confirm-delete-pump', className='btn-delete'),
                dbc.Button('Hủy', id='confirm-cancel-pump', className='ms-2 btn-cancel')
            ])
        ], id='confirm-delete-pump-modal', is_open=False, centered=True)

        ,
        dbc.Modal([
            dbc.ModalHeader(id='pump-memory-modal-title'),
            dbc.ModalBody(dcc.Loading(html.Div([
                dcc.DatePickerSingle(id='pump-memory-date', date=datetime.date.today().isoformat(), display_format='DD/MM/YYYY', className='mb-3', max_date_allowed=datetime.date.today().isoformat(),
                                     initial_visible_month=datetime.date.today().isoformat()),
                html.Div(id='pump-memory-body')
            ]))),
            dbc.ModalFooter([
                dbc.Button('Trước', id='pump-memory-prev', className='btn-edit me-2', size='sm'),
                dbc.Button('Sau', id='pump-memory-next', className='btn-edit me-2', size='sm'),
                html.Div(id='pump-memory-total', className='ms-3'),
            ])
        ], id='pump-memory-modal', is_open=False, centered=True)
        ,
        dcc.Store(id='pump-memory-page-store', data={'page': 1, 'limit': 5, 'total': 0, 'ma_id': None}),

    ], fluid=True)
], className='page-container', style={"paddingTop": "5px"})


@callback(
    [Output('pump-data-store', 'data', allow_duplicate=True), Output('pump-pagination-store', 'data', allow_duplicate=True), Output('pump-total', 'children')],
    [Input('url', 'pathname'), Input('pump-page-store', 'data'), Input('pump-interval', 'n_intervals')],
    State('session-store', 'data'),
    prevent_initial_call='initial_duplicate'
)
def load_pumps(pathname, page_store, n_intervals, session_data):
    if pathname != '/pump':
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
    total_text = '0 trong tổng số 0'
    try:
        data = list_pumps(limit=limit, offset=offset, token=token)
        if isinstance(data, dict) and data.get('total') is not None:
            total = int(data.get('total') or 0)
            max_pages = max(1, (total + limit - 1) // limit)
        else:
            total = len(data.get('data') or [])
        if total > 0:
            start = (page - 1) * limit + 1
            end = min(page * limit, total)
            total_text = f'{start}-{end} trong tổng số {total}'
        else:
            total_text = '0 trong tổng số 0'
    except Exception:
        data = {'data': []}
        max_pages = 1
        total_text = '0 trong tổng số 0'
    return data, {'max': max_pages}, total_text


@callback(
    Output('pump-table-container', 'children'),
    [Input('pump-data-store', 'data'), Input('pump-search', 'value')]
)
def render_pump_table(data, search):
    if not data or 'data' not in data or not data.get('data'):
        return html.Div(className='empty-state', children=[
            html.Div(className='empty-icon', children=[html.Img(src='/assets/img/empty-box.svg', style={'width':'64px','height':'64px'})]),
            html.Div('Không có dữ liệu máy bơm.', className='empty-text')
        ])

    rows = []
    items = list(data.get('data', []) or [])
    try:
        items.sort(key=lambda x: int(x.get('ma_may_bom') or 0))
    except Exception:
        items = items
    for p in items:
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

    return html.Div(className='table-scroll', children=[table])


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

        data = list_pumps(limit=20, offset=0, token=token)
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
    data = list_pumps(limit=20, offset=0, token=token)
    return data, False, False


@callback(
    [Output('pump-memory-modal', 'is_open'), Output('pump-memory-modal-title', 'children'), Output('pump-memory-body', 'children'), Output('pump-memory-page-store', 'data')],
    [Input({'type': 'memory-pump', 'index': dash.ALL}, 'n_clicks'), Input('pump-memory-prev', 'n_clicks'), Input('pump-memory-next', 'n_clicks'), Input('pump-memory-date', 'date')],
    [State('pump-data-store', 'data'), State('session-store', 'data'), State('pump-memory-page-store', 'data')],
    prevent_initial_call=True
)
def toggle_pump_memory(open_clicks, prev_click, next_click, selected_date, store, session_data, page_store):
    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate
    trig = ctx.triggered[0]
    prop = trig.get('prop_id', '').split('.')[0]
    trig_value = trig.get('value')

    if not trig_value:
        raise PreventUpdate

    is_nav_prev = (prop == 'pump-memory-prev')
    is_nav_next = (prop == 'pump-memory-next')
    is_nav = is_nav_prev or is_nav_next
    is_date_change = (prop == 'pump-memory-date')

    ma_id = None
    if is_date_change or is_nav:
        if not page_store or not isinstance(page_store, dict):
            raise PreventUpdate
        try:
            ma_id = int(page_store.get('ma_id'))
        except Exception:
            ma_id = page_store.get('ma_id')
        if not ma_id:
            raise PreventUpdate
    else:
        try:
            import json as _json
            obj = _json.loads(prop)
            ma_id = int(obj.get('index'))
        except Exception:
            raise PreventUpdate

    token = None
    if session_data and isinstance(session_data, dict):
        token = session_data.get('token')

    page = 1
    limit = 5
    total = 0
    try:
        if page_store and isinstance(page_store, dict):
            page = int(page_store.get('page', 1) or 1)
            limit = int(page_store.get('limit', 5) or 5)
    except Exception:
        page, limit = 1, 5

    if is_date_change:
        page = 1
    if (not is_nav) and (not is_date_change):
        page = 1

    if prop == 'pump-memory-prev':
        if page > 1:
            page -= 1
    if prop == 'pump-memory-next':
        page += 1

    offset = (page - 1) * limit

    try:
        resp = get_pump_memory_logs(ma_id, token=token, limit=limit, offset=offset, date=selected_date)
    except Exception as e:
        resp = {'data': [], 'error': str(e), 'total': 0}

    try:
        total_from_resp = int(resp.get('total') or 0)
    except Exception:
        total_from_resp = 0

    max_pages = 1
    try:
        if total_from_resp and int(limit) > 0:
            max_pages = max(1, (int(total_from_resp) + int(limit) - 1) // int(limit))
    except Exception:
        max_pages = 1

    if page > max_pages:
        page = max_pages
        offset = (page - 1) * limit
        try:
            resp = get_pump_memory_logs(ma_id, token=token, limit=limit, offset=offset, date=selected_date)
        except Exception as e:
            resp = {'data': [], 'error': str(e), 'total': 0}

    items = resp.get('data') or []
    if not isinstance(items, list):
        items = [items]

    try:
        items = sorted(items, key=lambda it: it.get('ma_may_bom', 0), reverse=True)
    except Exception:
        items = items

    def _format_dt_iso_to_bk(ts):
        if not ts:
            return None, '—'
        try:
            ts_parsed = pd.to_datetime(ts, utc=True)
            ts_local = ts_parsed.tz_convert('Asia/Bangkok')
            return ts_local, ts_local.strftime('%H:%M %d/%m/%Y')
        except Exception:
            return None, str(ts)

    rows = []
    for idx, r in enumerate(items, start=1):
        if not isinstance(r, dict):
            continue
        try:
            stt = (page - 1) * limit + idx
        except Exception:
            stt = idx
        bat_ts = r.get('thoi_gian_bat')
        tat_ts = r.get('thoi_gian_tat')
        ghi_chu = r.get('ghi_chu') or ''

        bat_dt, bat_str = _format_dt_iso_to_bk(bat_ts)
        tat_dt, tat_str = _format_dt_iso_to_bk(tat_ts)

        duration_str = '—'
        try:
            if bat_dt is not None and tat_dt is not None:
                delta = (tat_dt - bat_dt)
                total_seconds = int(delta.total_seconds())
                if total_seconds < 0:
                    duration_str = str(delta)
                else:
                    h = total_seconds // 3600
                    m = (total_seconds % 3600) // 60
                    s = total_seconds % 60
                    if h > 0:
                        duration_str = f"{h}giờ {m}ph {s}giây"
                    elif m > 0:
                        duration_str = f"{m}ph {s}giây"
                    else:
                        duration_str = f"{s}giây"
        except Exception:
            duration_str = '—'

        rows.append(html.Tr([html.Td(str(stt)), html.Td(bat_str), html.Td(tat_str), html.Td(duration_str), html.Td(ghi_chu)]))
    
    pump_name = None
    try:
        for it in (store.get('data') or []):
            try:
                if int(it.get('ma_may_bom') or 0) == int(ma_id):
                    pump_name = it.get('ten_may_bom')
                    break
            except Exception:
                if str(it.get('ma_may_bom')) == str(ma_id):
                    pump_name = it.get('ten_may_bom')
                    break
    except Exception:
        pump_name = None

    if selected_date:
        if not rows:
            body = html.Div('Không có nhật ký của máy bơm ' + str(pump_name if pump_name else ma_id) + ' vào ngày đã chọn.', className='text-center')

    if not rows:
        body = html.Div('Không có nhật ký của máy bơm ' + str(pump_name if pump_name else ma_id) + '.', className='text-center')
    else:
        table = dbc.Table([
            html.Thead(html.Tr([html.Th('STT'), html.Th('Thời gian bật'), html.Th('Thời gian tắt'), html.Th('Thời lượng'), html.Th('Ghi chú')])),
            html.Tbody(rows)
        ], bordered=True, hover=True, responsive=True)
        body = html.Div(className='table-scroll', children=[table])

    title = f"Nhật ký máy bơm {pump_name if pump_name else ma_id}"

    try:
        total = int(resp.get('total') or 0)
    except Exception:
        total = int(resp.get('total') or len(resp.get('data') or []))

    new_page_store = {'page': page, 'limit': limit, 'total': total, 'ma_id': ma_id}

    return True, title, body, new_page_store


@callback(
    Output('confirm-delete-pump-modal', 'is_open', allow_duplicate=True),
    Input('confirm-cancel-pump', 'n_clicks'),
    prevent_initial_call='initial_duplicate'
)
def cancel_confirm(n):
    if not n:
        raise PreventUpdate
    return False

def _build_pump_pagination(current, max_pages, window=3):
    items = []
    prev_disabled = (current <= 1)
    items.append(dbc.Button(html.I(className='fas fa-chevron-left'), id={'type': 'pump-page-prev', 'index': 'prev'}, color='light', size='sm', className='me-1', disabled=prev_disabled))

    def page_button(p):
        active = (p == current)
        return dbc.Button(str(p), id={'type': 'pump-page', 'index': str(p)}, color='primary' if active else 'light', size='sm', className='me-1')

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
    items.append(dbc.Button(html.I(className='fas fa-chevron-right'), id={'type': 'pump-page-next', 'index': 'next'}, color='light', size='sm', className='ms-1', disabled=next_disabled))
    return dbc.ButtonGroup(items, className='page-pagination')


@callback(
    Output('pump-pagination', 'children'),
    [Input('pump-pagination-store', 'data'), Input('pump-page-store', 'data')]
)
def render_pump_pagination(pagination_meta, page_store):
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
    return _build_pump_pagination(current, max_pages)


@callback(
    Output('pump-memory-total', 'children'),
    Input('pump-memory-page-store', 'data')
)
def render_pump_memory_total(page_store):
    if not page_store or not isinstance(page_store, dict):
        raise PreventUpdate
    try:
        page = int(page_store.get('page', 1) or 1)
        limit = int(page_store.get('limit', 5) or 5)
        total = int(page_store.get('total', 0) or 0)
    except Exception:
        return dash.no_update

    if total <= 0:
        return '0 trong tổng số 0'

    start = (page - 1) * limit + 1
    end = min(page * limit, total)
    return f'{start}-{end} trong tổng số {total}'


@callback(
    Output('pump-page-store', 'data'),
    [Input({'type': 'pump-page', 'index': dash.ALL}, 'n_clicks'), Input({'type': 'pump-page-prev', 'index': dash.ALL}, 'n_clicks'), Input({'type': 'pump-page-next', 'index': dash.ALL}, 'n_clicks')],
    State('pump-page-store', 'data'), State('pump-pagination-store', 'data'),
    prevent_initial_call=True
)
def handle_pump_pagination_click(page_clicks, prev_clicks, next_clicks, current, pagination_meta):
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
    if t == 'pump-page':
        target = int(idx)
        if target < 1:
            target = 1
        if target > max_pages:
            target = max_pages
        data['page'] = target
        return data
    if t == 'pump-page-prev':
        data['page'] = max(1, int(data.get('page', 1)) - 1)
        return data
    if t == 'pump-page-next':
        nextp = int(data.get('page', 1)) + 1
        if nextp > max_pages:
            nextp = max_pages
        data['page'] = nextp
        return data
    raise PreventUpdate
