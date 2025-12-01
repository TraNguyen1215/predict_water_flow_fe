from dash import html, dcc, callback, Input, Output, State
import dash_bootstrap_components as dbc
from components.navbar import create_navbar
from components.topbar import TopBar
import dash
from dash.exceptions import PreventUpdate
from datetime import datetime
from api.planting_log import list_logs, create_log, update_log, delete_log
import requests

layout = html.Div([
    create_navbar(is_authenticated=True),
    dcc.Location(id='planting-log-url', refresh=False),
    dcc.Store(id='planting-log-store', data=[]),
    dcc.Store(id='planting-log-edit-id'),
    dcc.Store(id='planting-log-delete-id'),

    dbc.Container([
        dbc.Row([
                dbc.Col(TopBar(
                    'Nhật ký gieo trồng',
                    search_id='planting-log-search',
                    date_id='planting-log-filter-date',
                    extra_right=[dbc.Button('Xóa lọc', id='planting-log-filter-clear', color='danger', size='sm')],
                    show_add=False
                ), width=12)
            ], className='mb-3'),

        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5("Thêm mục nhật ký")),
                    dbc.CardBody([
                        dbc.Form([
                            dbc.Row([
                                dbc.Col([
                                    dbc.Label("Ngày"),
                                    dbc.Input(id='log-date', type='date', value=datetime.now().strftime('%Y-%m-%d'))
                                ], md=4),
                                dbc.Col([
                                    dbc.Label("Cây trồng"),
                                    dbc.Input(id='log-crop', placeholder='Ví dụ: Cà chua')
                                ], md=4),
                                dbc.Col([
                                    dbc.Label("Số lượng/diện tích"),
                                    dbc.Input(id='log-qty', placeholder='Ví dụ: 10 cây / 5m²')
                                ], md=4),
                            ], className='mb-2'),

                            dbc.Row([
                                dbc.Col([
                                    dbc.Label("Ghi chú"),
                                    dbc.Textarea(id='log-notes', placeholder='Ghi chú thêm...', className='mb-2')
                                ], md=12)
                            ]),

                            dbc.Row([
                                dbc.Col([dbc.Label('Nguồn (URL file)'), dbc.Input(id='log-file-url', placeholder='https://...')], md=9),
                                dbc.Col(dbc.Button('Tải từ URL', id='load-log-from-url', color='secondary'), md=3)
                            ], className='mb-2'),

                            dbc.Row([
                                dbc.Col(dbc.Button('Thêm', id='add-log-btn', color='primary'), width=3),
                                dbc.Col(html.Div(id='add-log-status'), width=9)
                            ])
                        ])
                    ])
                ], className='shadow-sm')
            ], md=4),

            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5('Danh sách nhật ký')),
                    dbc.CardBody([
                        html.Div(id='planting-log-list')
                    ])
                ], className='shadow-sm')
            ], md=8)
        ])

    ], fluid=True, className='py-4')
], className='page-container')

# Edit modal
edit_modal = dbc.Modal([
    dbc.ModalHeader('Sửa mục nhật ký'),
    dbc.ModalBody([
        dbc.Form([
            dbc.Row([dbc.Col(dbc.Label('Ngày')), dbc.Col(dbc.Input(id='edit-log-date', type='date'))]),
            dbc.Row([dbc.Col(dbc.Label('Cây trồng')), dbc.Col(dbc.Input(id='edit-log-crop'))]),
            dbc.Row([dbc.Col(dbc.Label('Số lượng/diện tích')), dbc.Col(dbc.Input(id='edit-log-qty'))]),
            dbc.Row([dbc.Col(dbc.Label('Ghi chú')), dbc.Col(dbc.Textarea(id='edit-log-notes'))]),
            dbc.Row([dbc.Col(dbc.Label('Nguồn (URL file)'), md=9), dbc.Col(dbc.Button('Tải từ URL', id='edit-load-log-from-url', color='secondary'), md=3)]),
            html.Div(id='edit-log-status', className='mt-2'),
            dcc.Store(id='edit-load-temp')
        ])
    ]),
    dbc.ModalFooter([
        dbc.Button('Lưu', id='save-edit-log', color='primary'),
        dbc.Button('Hủy', id='edit-cancel', className='ms-2 btn-cancel')
    ])
], id='edit-log-modal', is_open=False, centered=True)

# Delete confirm modal
delete_confirm_modal = dbc.Modal([
    dbc.ModalHeader('Xác nhận xóa'),
    dbc.ModalBody(html.Div('Bạn có chắc muốn xóa mục nhật ký này?')),
    dbc.ModalFooter([
        dbc.Button('Xóa', id='confirm-delete-log', color='danger'),
        dbc.Button('Hủy', id='cancel-delete-log', className='ms-2 btn-cancel')
    ])
], id='confirm-delete-log-modal', is_open=False, centered=True)

 # append modals to layout root by wrapping existing layout and adding modals
layout = html.Div([layout, edit_modal, delete_confirm_modal])


@callback(
    Output('planting-log-store', 'data', allow_duplicate=True),
    Output('add-log-status', 'children', allow_duplicate=True),
    Input('add-log-btn', 'n_clicks'),
    State('log-date', 'value'),
    State('log-crop', 'value'),
    State('log-qty', 'value'),
    State('log-notes', 'value'),
    State('planting-log-store', 'data'),
    State('session-store', 'data'),
    prevent_initial_call=True
)
def add_log(n_clicks, date, crop, qty, notes, current_data, session_data):
    if not n_clicks:
        raise PreventUpdate
    token = None
    if session_data and isinstance(session_data, dict):
        token = session_data.get('token')

    payload = {
        'date': date or datetime.now().strftime('%Y-%m-%d'),
        'crop': crop or '',
        'qty': qty or '',
        'notes': notes or ''
    }

    ok, msg = create_log(payload, token=token)
    if not ok:
        return dash.no_update, dbc.Alert(str(msg or 'Lỗi khi tạo mục nhật ký.'), color='danger', duration=4000)

    # refresh list from server
    data = list_logs(limit=200, offset=0, token=token)
    items = []
    try:
        if isinstance(data, dict):
            items = data.get('data') or []
    except Exception:
        items = []

    return items, dbc.Alert(str(msg or 'Đã thêm mục nhật ký.'), color='success', duration=2500)


@callback(
    Output('planting-log-list', 'children'),
    [Input('planting-log-store', 'data'), Input('planting-log-search', 'value'), Input('planting-log-filter-date', 'date')]
)
def render_list(data, search, filter_date):
    if not data:
        return html.Div('Chưa có mục nhật ký nào.', className='text-muted')
    items = []
    for item in data:
        # filter by date if provided
        if filter_date:
            try:
                if not item.get('date') or not str(item.get('date')).startswith(str(filter_date)):
                    continue
            except Exception:
                pass

        # filter by search text
        if search and search.strip():
            txt = ' '.join([str(item.get('crop') or ''), str(item.get('notes') or ''), str(item.get('qty') or '')])
            if search.strip().lower() not in txt.lower():
                continue

        items.append(
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.Strong(item.get('crop') or '—'),
                        html.Span(item.get('date') or '', className='text-muted ms-3')
                    ], className='d-flex justify-content-between'),
                    html.Div(item.get('qty') or ''),
                    html.P(item.get('notes') or '', className='small text-muted mt-2'),
                    dbc.ButtonGroup([
                        dbc.Button('Sửa', id={'type': 'edit-log', 'index': str(item.get('id'))}, color='light', size='sm'),
                        dbc.Button('Xóa', id={'type': 'delete-log', 'index': str(item.get('id'))}, color='danger', size='sm')
                    ], className='mt-2')
                ])
            ], className='mb-2')
        )
    if not items:
        return html.Div('Không tìm thấy mục nhật ký phù hợp.', className='text-muted')
    return items


@callback(
    [Output('planting-log-search', 'value'), Output('planting-log-filter-date', 'date')],
    Input('planting-log-filter-clear', 'n_clicks'),
    prevent_initial_call=True
)
def clear_filters(n):
    return None, None


@callback(
    [Output('edit-log-modal', 'is_open', allow_duplicate=True), Output('edit-log-date', 'value', allow_duplicate=True), Output('edit-log-crop', 'value', allow_duplicate=True), Output('edit-log-qty', 'value', allow_duplicate=True), Output('edit-log-notes', 'value', allow_duplicate=True), Output('planting-log-edit-id', 'data')],
    [Input({'type': 'edit-log', 'index': dash.ALL}, 'n_clicks'), Input('edit-cancel', 'n_clicks')],
    [State('edit-log-modal', 'is_open'), State('planting-log-store', 'data')],
    prevent_initial_call=True
)
def open_edit_modal(edit_clicks, cancel_clicks, is_open, store):
    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate
    prop = ctx.triggered[0]['prop_id'].split('.')[0]
    if prop == 'edit-cancel':
        return False, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

    # triggered by an edit button
    try:
        import json as _json
        obj = _json.loads(prop)
        idx = str(obj.get('index'))
    except Exception:
        raise PreventUpdate

    item = None
    try:
        for it in (store or []):
            if str(it.get('id')) == idx:
                item = it
                break
    except Exception:
        item = None

    if not item:
        raise PreventUpdate

    return True, item.get('date'), item.get('crop'), item.get('qty'), item.get('notes'), idx


@callback(
    [Output('planting-log-store', 'data', allow_duplicate=True), Output('edit-log-modal', 'is_open', allow_duplicate=True), Output('edit-log-status', 'children', allow_duplicate=True)],
    Input('save-edit-log', 'n_clicks'),
    [State('planting-log-edit-id', 'data'), State('edit-log-date', 'value'), State('edit-log-crop', 'value'), State('edit-log-qty', 'value'), State('edit-log-notes', 'value'), State('session-store', 'data')],
    prevent_initial_call=True
)
def save_edit(n_clicks, edit_id, date, crop, qty, notes, session_data):
    if not n_clicks or not edit_id:
        raise PreventUpdate
    token = None
    if session_data and isinstance(session_data, dict):
        token = session_data.get('token')

    payload = {'date': date, 'crop': crop, 'qty': qty, 'notes': notes}
    ok, msg = update_log(edit_id, payload, token=token)
    if not ok:
        return dash.no_update, True, dbc.Alert(str(msg or 'Lỗi cập nhật'), color='danger')
    data = list_logs(limit=200, offset=0, token=token)
    items = []
    try:
        if isinstance(data, dict):
            items = data.get('data') or []
    except Exception:
        items = []
    return items, False, dbc.Alert(str(msg or 'Đã cập nhật'), color='success', duration=2500)


@callback(
    [Output('confirm-delete-log-modal', 'is_open', allow_duplicate=True), Output('planting-log-delete-id', 'data')],
    [Input({'type': 'delete-log', 'index': dash.ALL}, 'n_clicks'), Input('cancel-delete-log', 'n_clicks')],
    [State('confirm-delete-log-modal', 'is_open')],
    prevent_initial_call=True
)
def open_delete_modal(delete_clicks, cancel_clicks, is_open):
    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate
    prop = ctx.triggered[0]['prop_id'].split('.')[0]
    if prop == 'cancel-delete-log':
        return False, dash.no_update
    try:
        import json as _json
        obj = _json.loads(prop)
        idx = str(obj.get('index'))
    except Exception:
        raise PreventUpdate
    return True, idx


@callback(
    [Output('planting-log-store', 'data', allow_duplicate=True), Output('confirm-delete-log-modal', 'is_open', allow_duplicate=True)],
    Input('confirm-delete-log', 'n_clicks'),
    [State('planting-log-delete-id', 'data'), State('session-store', 'data')],
    prevent_initial_call=True
)
def perform_delete(n_clicks, delete_id, session_data):
    if not n_clicks or not delete_id:
        raise PreventUpdate
    token = None
    if session_data and isinstance(session_data, dict):
        token = session_data.get('token')
    ok, msg = delete_log(delete_id, token=token)
    if not ok:
        return dash.no_update, True
    data = list_logs(limit=200, offset=0, token=token)
    items = []
    try:
        if isinstance(data, dict):
            items = data.get('data') or []
    except Exception:
        items = []
    return items, False


@callback(
    [Output('log-date', 'value'), Output('log-crop', 'value'), Output('log-qty', 'value'), Output('log-notes', 'value'), Output('add-log-status', 'children', allow_duplicate=True)],
    Input('load-log-from-url', 'n_clicks'),
    [State('log-file-url', 'value')],
    prevent_initial_call=True
)
def load_from_url(n_clicks, url):
    if not n_clicks or not url:
        raise PreventUpdate
    try:
        resp = requests.get(url, timeout=6)
        if resp.status_code != 200:
            return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dbc.Alert('Không tải được file từ URL', color='danger')
        try:
            data = resp.json()
            # expect keys: date, crop, qty, notes
            date = data.get('date')
            crop = data.get('crop')
            qty = data.get('qty')
            notes = data.get('notes')
            return date or dash.no_update, crop or dash.no_update, qty or dash.no_update, notes or dash.no_update, dbc.Alert('Đã tải dữ liệu từ URL', color='success', duration=2000)
        except Exception:
            text = resp.text
            # fallback: put entire text into notes
            return dash.no_update, dash.no_update, dash.no_update, text, dbc.Alert('Tải file thành công, nội dung được đặt vào ghi chú', color='success', duration=2500)
    except Exception as e:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dbc.Alert(f'Lỗi khi tải URL: {e}', color='danger')


@callback(
    [Output('edit-log-date', 'value', allow_duplicate=True), Output('edit-log-crop', 'value', allow_duplicate=True), Output('edit-log-qty', 'value', allow_duplicate=True), Output('edit-log-notes', 'value', allow_duplicate=True), Output('edit-log-status', 'children', allow_duplicate=True)],
    Input('edit-load-log-from-url', 'n_clicks'),
    [State('edit-log-date', 'value'), State('edit-log-crop', 'value'), State('edit-log-qty', 'value'), State('edit-log-notes', 'value'), State('edit-load-temp', 'data')],
    prevent_initial_call=True
)
def edit_load_from_url(n_clicks, cur_date, cur_crop, cur_qty, cur_notes, temp):
    # this callback expects the user to paste a URL into edit modal's input; to keep it simple,
    # read URL from edit-load-temp store if present (we keep same behavior as add for now)
    raise PreventUpdate


@callback(
    Output('planting-log-store', 'data', allow_duplicate=True),
    Input('url', 'pathname'),
    State('session-store', 'data'),
    prevent_initial_call='initial_duplicate'
)
def load_logs_on_page(pathname, session_data):
    if pathname != '/planting-log':
        raise PreventUpdate
    token = None
    if session_data and isinstance(session_data, dict):
        token = session_data.get('token')
    data = list_logs(limit=200, offset=0, token=token)
    try:
        if isinstance(data, dict):
            return data.get('data') or []
    except Exception:
        pass
    return []
