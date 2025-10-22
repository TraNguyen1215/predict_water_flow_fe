from dash import html, dcc, callback, Input, Output, State
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
from components.navbar import create_navbar
from api.sensor_data import get_data_by_pump, get_data_by_date, put_sensor_data
from api.sensor import list_sensors
import dash
import datetime


def _data_row_item(d):
    return html.Tr([
        html.Td(d.get('ngay')),
        html.Td(d.get('luu_luong_nuoc')),
        html.Td(d.get('do_am_dat')),
        html.Td(d.get('nhiet_do')),
        html.Td(d.get('do_am')),
        html.Td(str(d.get('mua'))),
        html.Td(d.get('so_xung')),
        html.Td(d.get('tong_the_tich')),
        html.Td(d.get('ghi_chu') or '')
    ])


layout = html.Div([
    create_navbar(is_authenticated=True),
    dbc.Container([
        dbc.Row([
            dbc.Col(html.H3('Dữ liệu cảm biến'), width=8),
            dbc.Col(dbc.Button('Thêm dữ liệu', id='open-add-data', color='primary'), width=4, className='text-end')
        ], className='my-3'),

        dbc.Row([
            dbc.Col(dcc.Dropdown(id='data-filter-pump', options=[], placeholder='Chọn máy bơm', clearable=True)),
            dbc.Col(dbc.Input(id='data-filter-date', type='date', value=str(datetime.date.today())))
        ], className='mb-3'),

        dbc.Row([
            dbc.Col(dcc.Loading(html.Div(id='data-table-container')))
        ]),

    dcc.Store(id='data-store'),
    dcc.Store(id='data-edit-id'),

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
                dbc.Button('Lưu', id='data-save', color='primary'),
                dbc.Button('Đóng', id='data-cancel', className='ms-2')
            ])
        ], id='data-modal', is_open=False, centered=True)

    ], fluid=True)
], className='page-container', style={"paddingTop": "20px"})


@callback(
    Output('data-filter-pump', 'options'),
    Input('url', 'pathname'),
    State('session-store', 'data')
)
def load_pumps_options(pathname, session_data):
    if pathname != '/sensor-data' and pathname != '/du-lieu-cam-bien':
        raise PreventUpdate
    token = None
    if session_data and isinstance(session_data, dict):
        token = session_data.get('token')
    data = list_sensors(limit=200, offset=0, token=token)
    opts = []
    for it in (data.get('data') or []):
        opts.append({'label': it.get('ten_may_bom') or str(it.get('ma_may_bom')), 'value': it.get('ma_may_bom')})
    return opts


@callback(
    Output('data-store', 'data'),
    [Input('data-filter-pump', 'value'), Input('data-filter-date', 'value')],
    State('session-store', 'data')
)
def load_data(ma_may_bom, ngay, session_data):
    token = None
    if session_data and isinstance(session_data, dict):
        token = session_data.get('token')
    if ma_may_bom:
        return get_data_by_pump(int(ma_may_bom), token=token)
    if ngay:
        return get_data_by_date(ngay, token=token)
    return {'data': []}


@callback(
    Output('data-table-container', 'children'),
    Input('data-store', 'data')
)
def render_table(data):
    if not data or 'data' not in data:
        return dbc.Alert('Không có dữ liệu.', color='info')
    rows = []
    for d in data.get('data', []):
        rows.append(_data_row_item(d))

    table = dbc.Table([
        html.Thead(html.Tr([html.Th('Ngày'), html.Th('Lưu lượng'), html.Th('Độ ẩm đất'), html.Th('Nhiệt độ'), html.Th('Độ ẩm'), html.Th('Mưa'), html.Th('Số xung'), html.Th('Tổng thể tích'), html.Th('Ghi chú')])),
        html.Tbody(rows)
    ], bordered=True, hover=True, responsive=True)
    return table


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
    # reload store by date
    data = get_data_by_date(ngay, token=token)
    return data, False
