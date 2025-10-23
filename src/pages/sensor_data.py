from dash import html, dcc, callback, Input, Output, State
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
from components.navbar import create_navbar
from components.topbar import TopBar
from api.sensor_data import get_data_by_pump, get_data_by_date, put_sensor_data
from api.sensor import list_sensors
from api.pump import list_pumps
import dash
import datetime
import dash


def _data_row_item(d, index=None):
    return html.Tr([
        html.Td(index if index is not None else ''),
        html.Td(d.get('ngay')),
        html.Td(d.get('luu_luong_nuoc')),
        html.Td(d.get('do_am_dat')),
        html.Td(d.get('nhiet_do')),
        html.Td(d.get('do_am')),
        html.Td('Có mưa' if d.get('mua') else 'Không mưa'),
        html.Td(d.get('so_xung')),
        html.Td(d.get('tong_the_tich')),
        html.Td(d.get('ghi_chu') or '')
    ])


layout = html.Div([
    create_navbar(is_authenticated=True),
    dbc.Container([
    dbc.Row([dbc.Col(TopBar('Dữ liệu cảm biến', search_id=None, date_id='data-filter-date', add_button={'id':'open-add-data','label':'Thêm dữ liệu'}, unit_id='data-filter-pump', extra_left=[dcc.Dropdown(id='data-limit-dropdown', options=[{'label':'20','value':20},{'label':'50','value':50},{'label':'200','value':200}], value=20, clearable=False, className='topbar-limit me-2')], show_add=False, date_last=True))], className='my-3'),

        dbc.Row([
            dbc.Col(html.Div(className='table-area', children=[
                dcc.Loading(html.Div(id='data-table-container')),
                html.Div(className='pagination-footer', children=[html.Div(id='data-pagination'), html.Div(id='data-total', className='pt-2 total-text')])
            ]))
        ]),

    dcc.Store(id='data-store'),
    dcc.Store(id='data-edit-id'),
    dcc.Store(id='data-page-store', data={'page': 1, 'limit': 20}),
    dcc.Store(id='data-pagination-store', data={'max': 1}),

        dbc.Modal([
            dbc.ModalHeader(id='data-modal-title'),
            dbc.ModalBody([
                dbc.Form([
                    dbc.Label('Ngày'),
                    dbc.Input(id='data-ngay', type='date', value=str(datetime.date.today())),
                    dbc.Label('Lưu lượng nước'),
                    dbc.Input(id='data-luu-luong', type='number', value=0),
                    dbc.Label('Độ ẩm đất', className='mt-2'),
                    dbc.Input(id='data-do-am-dat', type='number', value=0),
                    dbc.Label('Nhiệt độ', className='mt-2'),
                    dbc.Input(id='data-nhiet-do', type='number', value=0),
                    dbc.Label('Độ ẩm', className='mt-2'),
                    dbc.Input(id='data-do-am', type='number', value=0),
                    dbc.Label('Mưa', className='mt-2'),
                    dcc.Dropdown(id='data-mua', options=[{'label':'Không', 'value': False}, {'label':'Có','value': True}], value=False, clearable=False),
                    dbc.Label('Số xung', className='mt-2'),
                    dbc.Input(id='data-so-xung', type='number', value=0),
                    dbc.Label('Tổng thể tích', className='mt-2'),
                    dbc.Input(id='data-tong-the-tich', type='number', value=0),
                    dbc.Label('Ghi chú', className='mt-2'),
                    dbc.Textarea(id='data-ghi-chu'),
                    dcc.Store(id='data-edit-id-store')
                ])
            ]),
            dbc.ModalFooter([
                dbc.Button('Lưu', id='data-save', className='btn-edit'),
                dbc.Button('Đóng', id='data-cancel', className='ms-2 btn-cancel')
            ])
        ], id='data-modal', is_open=False, centered=True)

    ], fluid=True)
], className='page-container', style={"paddingTop": "5px"})


@callback(
    Output('data-filter-pump', 'options'),
    Input('url', 'pathname'),
    State('session-store', 'data')
)
def load_pumps_options(pathname, session_data):
    if pathname not in ('/sensor-data', '/sensor_data', '/du-lieu-cam-bien'):
        raise PreventUpdate
    token = None
    if session_data and isinstance(session_data, dict):
        token = session_data.get('token')
    data = list_pumps(limit=1000, offset=0, token=token)
    opts = []
    opts.append({'label': 'Tất cả', 'value': ''})
    for it in (data.get('data') or []):
        opts.append({'label': it.get('ten_may_bom') or str(it.get('ma_may_bom')), 'value': it.get('ma_may_bom')})
    return opts


@callback(
    Output('data-filter-date', 'value', allow_duplicate=True),
    [Input('data-filter-date-prev', 'n_clicks'), Input('data-filter-date-next', 'n_clicks'), Input('data-filter-date', 'n_blur')],
    State('data-filter-date', 'value'),
    prevent_initial_call=True
)
def navigate_date(prev_clicks, next_clicks, blur, current_value):
    try:
        if not current_value:
            cur = datetime.date.today()
        else:
            cur = datetime.date.fromisoformat(str(current_value))
    except Exception:
        cur = datetime.date.today()

    ctx = dash.callback_context
    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate
    prop = ctx.triggered[0]['prop_id'].split('.')[0]
    if prop == 'data-filter-date-prev':
        new = cur - datetime.timedelta(days=1)
        return str(new)
    if prop == 'data-filter-date-next':
        new = cur + datetime.timedelta(days=1)
        today = datetime.date.today()
        if new > today:
            return str(current_value or str(today))
        return str(new)
    return current_value



@callback(
    Output('data-filter-date', 'value', allow_duplicate=True),
    Input('url', 'pathname'),
    prevent_initial_call='initial_duplicate'
)
def ensure_default_date_on_page(pathname):
    if pathname not in ('/sensor-data', '/sensor_data', '/du-lieu-cam-bien'):
        raise PreventUpdate
    today = datetime.date.today()
    return str(today)



@callback(
    Output('data-filter-date-next', 'disabled'),
    Input('data-filter-date', 'value')
)
def disable_next_if_today(current_value):
    try:
        if not current_value:
            return True
        cur = datetime.date.fromisoformat(str(current_value))
        return cur >= datetime.date.today()
    except Exception:
        return True


@callback(
    [Output('data-store', 'data'), Output('data-pagination-store', 'data'), Output('data-total', 'children')],
    [Input('data-filter-pump', 'value'), Input('data-filter-date', 'value'), Input('data-page-store', 'data')],
    State('session-store', 'data')
)
def load_data(ma_may_bom, ngay, page_store, session_data):
    token = None
    if session_data and isinstance(session_data, dict):
        token = session_data.get('token')
    page = 1
    limit = 20
    if page_store and isinstance(page_store, dict):
        page = int(page_store.get('page', 1))
        limit = int(page_store.get('limit', 20))
    data = {'data': []}
    max_pages = 1
    total_text = 'Tổng: 0'

    if ngay:
        offset = (page - 1) * limit
        try:
            data = get_data_by_date(ngay, limit=limit, offset=offset, token=token)
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
                total_text = f'0 trong tổng số 0'
        except Exception:
            data = {'data': []}
            max_pages = 1
            total_text = '0 trong tổng số 0'
        return data, {'max': max_pages}, total_text

    offset = (page - 1) * limit
    try:
        pump_param = int(ma_may_bom) if (ma_may_bom is not None and str(ma_may_bom).isdigit()) else None
        data = get_data_by_pump(pump_param, limit=limit, offset=offset, token=token)
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
            total_text = f'0 trong tổng số 0'
    except Exception:
        data = {'data': []}
        max_pages = 1
        total_text = '0 trong tổng số 0'
    return data, {'max': max_pages}, total_text

    return data, {'max': 1}, total_text


@callback(
    Output('data-page-store', 'data', allow_duplicate=True),
    Input('data-limit-dropdown', 'value'),
    State('data-page-store', 'data'),
    prevent_initial_call=True
)
def set_limit(limit_value, current):
    data = current or {'page': 1, 'limit': 20}
    try:
        data['limit'] = int(limit_value)
    except Exception:
        data['limit'] = 20
    data['page'] = 1
    return data


@callback(
    Output('data-table-container', 'children'),
    [Input('data-store', 'data'), Input('data-page-store', 'data')]
)
def render_table(data, page_store):
    if not data or 'data' not in data or not data.get('data'):
        return html.Div(className='empty-state', children=[
            html.Div(className='empty-icon', children=[
                html.Img(src='/assets/img/empty-box.svg', style={'width':'64px','height':'64px'})
            ]),
            html.Div('Không có dữ liệu', className='empty-text')
        ])
    rows = []
    items = data.get('data', []) or []
    start_idx = 0
    try:
        if page_store and isinstance(page_store, dict):
            page = int(page_store.get('page', 1) or 1)
            limit = int(page_store.get('limit', 20) or 20)
            start_idx = (page - 1) * limit
    except Exception:
        start_idx = 0

    for idx, d in enumerate(items, start= start_idx + 1):
        rows.append(_data_row_item(d, index=idx))

    table = dbc.Table([
        html.Thead(html.Tr([html.Th('STT'), html.Th('Ngày'), html.Th('Lưu lượng'), html.Th('Độ ẩm đất'), html.Th('Nhiệt độ'), html.Th('Độ ẩm'), html.Th('Mưa'), html.Th('Số xung'), html.Th('Tổng thể tích'), html.Th('Ghi chú')])),
        html.Tbody(rows)
    ], bordered=True, hover=True, responsive=True)
    return html.Div(className='table-scroll', children=[table])


def _build_pagination(current, max_pages, window=3):
    items = []
    # previous
    prev_disabled = (current <= 1)
    items.append(dbc.Button(html.I(className='fas fa-chevron-left'), id={'type': 'data-page-prev', 'index': 'prev'}, color='light', size='sm', className='me-1', disabled=prev_disabled))

    def page_button(p):
        active = (p == current)
        return dbc.Button(str(p), id={'type': 'data-page', 'index': str(p)}, color='primary' if active else 'light', size='sm', className='me-1')

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

    # next
    next_disabled = (current >= max_pages)
    items.append(dbc.Button(html.I(className='fas fa-chevron-right'), id={'type': 'data-page-next', 'index': 'next'}, color='light', size='sm', className='ms-1', disabled=next_disabled))
    return dbc.ButtonGroup(items, className='page-pagination')


@callback(
    Output('data-pagination', 'children'),
    [Input('data-pagination-store', 'data'), Input('data-page-store', 'data')]
)
def render_pagination(pagination_meta, page_store):
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
    return _build_pagination(current, max_pages)


@callback(
    Output('data-page-store', 'data'),
    [Input({'type': 'data-page', 'index': dash.ALL}, 'n_clicks'), Input({'type': 'data-page-prev', 'index': dash.ALL}, 'n_clicks'), Input({'type': 'data-page-next', 'index': dash.ALL}, 'n_clicks')],
    State('data-page-store', 'data'), State('data-pagination-store', 'data'),
    prevent_initial_call=True
)
def handle_pagination_click(page_clicks, prev_clicks, next_clicks, current, pagination_meta):
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
    if t == 'data-page':
        # clamp target page
        target = int(idx)
        if target < 1:
            target = 1
        if target > max_pages:
            target = max_pages
        data['page'] = target
        return data
    if t == 'data-page-prev':
        data['page'] = max(1, int(data.get('page', 1)) - 1)
        return data
    if t == 'data-page-next':
        nextp = int(data.get('page', 1)) + 1
        if nextp > max_pages:
            nextp = max_pages
        data['page'] = nextp
        return data
    raise PreventUpdate


@callback(
    [Output('data-modal', 'is_open'), Output('data-modal-title', 'children')],
    [Input('open-add-data', 'n_clicks'), Input('data-cancel', 'n_clicks')],
    prevent_initial_call=True
)
def open_modal(n_add, n_cancel):
    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate
    btn = ctx.triggered[0]['prop_id'].split('.')[0]
    if btn == 'open-add-data':
        return True, 'Thêm dữ liệu'
    return False, dash.no_update


@callback(
    [Output('data-store', 'data', allow_duplicate=True), Output('data-modal', 'is_open', allow_duplicate=True)],
    Input('data-save', 'n_clicks'),
    [State('data-ngay', 'value'), State('data-luu-luong', 'value'), State('data-do-am-dat', 'value'), State('data-nhiet-do', 'value'), State('data-do-am', 'value'), State('data-mua', 'value'), State('data-so-xung', 'value'), State('data-tong-the-tich', 'value'), State('data-ghi-chu', 'value'), State('session-store', 'data')],
    prevent_initial_call=True
)
def save_data(n_save, ngay, luu_luong, do_am_dat, nhiet_do, do_am, mua, so_xung, tong_the_tich, ghi_chu, session_data):
    if not n_save:
        raise PreventUpdate
    token = None
    if session_data and isinstance(session_data, dict):
        token = session_data.get('token')
    payload = {
        'ngay': ngay,
        'luu_luong_nuoc': float(luu_luong) if luu_luong is not None else 0,
        'do_am_dat': float(do_am_dat) if do_am_dat is not None else 0,
        'nhiet_do': float(nhiet_do) if nhiet_do is not None else 0,
        'do_am': float(do_am) if do_am is not None else 0,
        'mua': bool(mua) if mua is not None else False,
        'so_xung': int(so_xung) if so_xung is not None else 0,
        'tong_the_tich': float(tong_the_tich) if tong_the_tich is not None else 0,
        'ghi_chu': ghi_chu or ''
    }
    success, msg = put_sensor_data(payload, token=token)
    data = get_data_by_date(ngay, token=token)
    return data, False



