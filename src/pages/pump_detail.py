from dash import html, dcc, callback, Input, Output, State, ALL
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
from components.navbar import create_navbar
from api.pump import get_pump
from api.sensor import list_sensors
from api.sensor_data import get_data_by_date
from api.pump import update_pump
import plotly.graph_objs as go
import dash
import json
import datetime
import pandas as pd


def format_datetime(dt_str):
    if not dt_str:
        return "Không có dữ liệu"
    try:
        dt = pd.to_datetime(dt_str, errors='coerce')
        if pd.isna(dt):
            return "Không có dữ liệu"
        try:
            if getattr(dt, 'tz', None) is None:
                dt = dt.tz_localize('Asia/Bangkok')
            else:
                dt = dt.tz_convert('Asia/Bangkok')
        except Exception:
            pass
        return dt.strftime('%H:%M %d/%m/%Y')
    except:
        return "Không có dữ liệu"


def create_pump_info_section(pump):
    """Tạo phần thông tin chi tiết máy bơm"""
    status = "Đang chạy" if pump.get('trang_thai', False) else "Đã dừng"
    status_color = "success" if pump.get('trang_thai', False) else "warning"
    
    mode_map = {0: "Thủ công", 1: "Tự động", 2: "Bảo trì"}
    mode = mode_map.get(pump.get('che_do', 0), "Thủ công")
    
    
    def row_item(label, value, width_label=4, width_value=8):
        return dbc.Row([
            dbc.Col(html.Div(label, className='fw-bold text-end'), width=width_label),
            dbc.Col(html.Div(value), width=width_value)
        ], className='mb-2 align-items-center')

    return dbc.Card([
        dbc.CardHeader(html.H5("Thông tin máy bơm", className="mb-0", style={"color": "white"}), style={"backgroundColor": "#0358A3"}),
        dbc.CardBody([
            row_item('Tên máy bơm', html.B(pump.get('ten_may_bom', 'N/A'))),
            row_item('Trạng thái', html.Span(status, className=f"badge bg-{status_color}")),
            row_item('Chế độ', html.Span(mode, className='badge bg-info')),
            row_item('Mô tả', pump.get('mo_ta', 'Không có mô tả')),
            row_item('Ngày tạo', format_datetime(pump.get('thoi_gian_tao'))),
        ])
    ], className="mb-4 h-100")


def create_sensor_list_section(sensors, pump_sensors):
    """Tạo phần danh sách cảm biến"""
    sensor_dict = {}
    for s in (sensors or []):
        key = s.get('ma_cam_bien') if isinstance(s, dict) else None
        if key is None:
            continue
        sensor_dict[str(key)] = s

    
    sensor_ids = []
    if pump_sensors is None:
        pump_sensors = []
    
    if isinstance(pump_sensors, str):
        parts = [p.strip() for p in pump_sensors.split(',') if p.strip()]
        for p in parts:
            sensor_ids.append(p)
    elif isinstance(pump_sensors, (list, tuple)):
        for item in pump_sensors:
            if isinstance(item, dict):
                
                id_val = item.get('ma_cam_bien') or item.get('id') or item.get('ma')
                if id_val is not None:
                    sensor_ids.append(str(id_val))
            else:
                
                sensor_ids.append(str(item))
    else:
        
        sensor_ids.append(str(pump_sensors))

    sensor_rows = []
    if sensor_ids:
        for idx, sensor_id in enumerate(sensor_ids, 1):
            sensor = sensor_dict.get(str(sensor_id), {})
            
            sensor_rows.append(
                html.Tr([
                    html.Td(idx, style={'width': '5%'}),
                    html.Td(sensor.get('ten_cam_bien', 'Không xác định'), style={'width': '30%'}),
                    html.Td(sensor.get('ten_loai_cam_bien', 'N/A'), style={'width': '40%'}),
                    html.Td(format_datetime(sensor.get('thoi_gian_tao')), style={'width': '25%'})
                ])
            )
    
    if not sensor_rows:
        sensor_rows = [html.Tr([html.Td("Không có cảm biến nào", colSpan=4, className="text-center text-muted")])]
    
    return dbc.Card([
        dbc.CardHeader(html.H5("Danh sách cảm biến", className="mb-0", style={"color": "white"}), style={"backgroundColor": "#0358A3"}),
        dbc.CardBody([
            html.Div([
                html.Table([
                    html.Thead(
                        html.Tr([
                            html.Th("STT"),
                            html.Th("Tên cảm biến"),
                            html.Th("Loại"),
                            html.Th("Ngày tạo")
                        ])
                    ),
                    html.Tbody(sensor_rows)
                ], className="table table-sm table-hover mb-0")
            ], className="table-responsive")
        ])
    ], className="mb-4 h-100")


def create_layout():
    """Tạo layout cho trang chi tiết máy bơm"""
    return html.Div([
        create_navbar(is_authenticated=True),
        dbc.Container([
            dbc.Row([
                dbc.Col([
                    dbc.Button([
                        html.I(className="fas fa-arrow-left me-2"),
                        "Quay lại"
                    ], id="pump-detail-back", color="secondary", size="sm", outline=True, className="mb-3")
                ])
            ]),
            
            dbc.Row([
                dbc.Col(html.Div(id="pump-info-container", className='w-100 h-100'), md=3, className='d-flex'),
                dbc.Col(html.Div(id="pump-control-container", className='w-100 h-100'), md=3, className='d-flex'),
                dbc.Col(html.Div(id="pump-sensors-container", className='w-100 h-100'), md=6, className='d-flex'),
            ], className='mb-4 align-items-stretch'),
            
            dbc.Row([
                dbc.Col(html.Div(id="pump-charts-container"), style={"margin-bottom": "24px"})
            ]),
            
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([
                            # html.H5("Dữ liệu cảm biến theo ngày", className="mb-0 d-inline-block"),
                            dbc.Row([
                                        dbc.Col(html.H5("Dữ liệu cảm biến theo ngày", className="mb-0 d-inline-block"), align='center'),
                                        dbc.Col([
                                            dbc.Button(html.I(className='fas fa-chevron-left'), id='pump-detail-prev', color='light', size='sm', className='me-2'),
                                            dcc.DatePickerSingle(
                                                id='pump-detail-date-picker',
                                                date=datetime.date.today().isoformat(),
                                                display_format='DD/MM/YYYY',
                                                max_date_allowed=datetime.date.today().isoformat(),
                                                initial_visible_month=datetime.date.today().isoformat(),
                                                className='d-inline-block ms-1'
                                            ),
                                            dbc.Button(html.I(className='fas fa-chevron-right'), id='pump-detail-next', color='light', size='sm', className='ms-2')
                                        ], width=6, className='d-flex align-items-center'),
                                        dbc.Col(dbc.Button([html.I(className='fas fa-list me-2'), 'Xem chi tiết'], id='pump-detail-show-details', color='primary', className='btn-add'), width='auto', className='text-end')
                            ], className="g-0")
                        ]),
                        dbc.CardBody([
                            dcc.Loading(html.Div(id="pump-detail-data-container"))
                        ])
                    ], className="mb-4")
                ])
            ], style={"margin-bottom": "24px"}),
            
            dcc.Store(id='pump-detail-page-store', storage_type='memory', data={'page': 1, 'limit': 15, 'total': 0}),
            dcc.Interval(id='interval-component', interval=1000, n_intervals=0),
            
            dcc.Store(id='pump-detail-showing-details', storage_type='memory', data=False),
            
            dcc.Dropdown(id='data-filter-pump', options=[], style={'display': 'none'}),
        ], fluid=True, style={"padding": "20px 40px"})
    ], className='page-container', style={"paddingTop": "5px"})


layout = create_layout()


def create_pump_control_section(pump, pump_id):
    """Tạo phần điều khiển máy bơm (Start/Stop, chế độ)"""
    pump_info = pump if isinstance(pump, dict) else {}
    try:
        if pump_info.get('che_do') is None and pump_id:
            fresh = get_pump(pump_id) or {}
            if fresh.get('che_do') is not None:
                pump_info = fresh
    except Exception:
        pass

    return dbc.Card([
        dbc.CardHeader(html.H5("Điều khiển Máy Bơm", className="mb-0", style={"color": "white"}), style={"backgroundColor": "#0358A3"}),
        dbc.CardBody([
            html.Div([
                html.Div([
                    html.Span("Máy bơm được chọn", className="control-label text-muted"),
                    html.Strong(pump_info.get('ten_may_bom', ''), id='control-selected-pump-name', className="control-selected-name")
                ], className="pump-control-summary mb-3"),

                html.Div([
                    dbc.Button(
                        [html.I(className="fas fa-play me-1"), "Bật"],
                        color='success', size='sm', id='pump-start-btn', className="pump-control-btn start-btn"
                    ),
                    dbc.Button(
                        [html.I(className="fas fa-stop me-1"), "Tắt"],
                        color='danger', outline=True, size='sm', id='pump-stop-btn', className='pump-control-btn stop-btn ms-2'
                    )
                ], className="pump-control-actions d-flex align-items-center mb-3"),
                html.Div(id='pump-control-result'),

                html.Div([
                    html.Span("Chế độ vận hành", className="control-label text-muted"),
                    dbc.RadioItems(
                        id='pump-mode-select',
                        options=[
                            {'label': 'Thủ công', 'value': 0},
                            {'label': 'Tự động', 'value': 1},
                            {'label': 'Bảo trì', 'value': 2}
                        ],
        value=(pump_info.get('che_do') if isinstance(pump_info, dict) and pump_info.get('che_do') is not None else None),
                        inline=True,
                        className="pump-mode-select mt-2"
                    )
                ], className="pump-mode-wrapper")
            ])
        ])
    ], className='mb-4 h-100')


@callback(
    [Output('pump-detail-store', 'data', allow_duplicate=True), Output('selected-pump-store', 'data', allow_duplicate=True)],
    Input('url', 'pathname'),
    State('session-store', 'data'),
    prevent_initial_call='initial_duplicate'
)
def load_pump_detail(pathname, session_data):
    """Load thông tin chi tiết máy bơm từ URL and store to pump-detail-store."""
    if not pathname or not pathname.startswith('/pump/'):
        raise PreventUpdate

    try:
        try:
            pump_id = int(pathname.split('/')[-1])
        except (ValueError, IndexError):
            return dash.no_update, dash.no_update

        token = None
        if session_data and isinstance(session_data, dict):
            token = session_data.get('token')

        pump_data = get_pump(pump_id, token=token) or {}

        sensors_data = list_sensors(limit=1000, token=token)
        sensors = sensors_data.get('data', []) if sensors_data else []

        pump_sensors = []
        if isinstance(pump_data, dict):
            pump_sensors = pump_data.get('cam_bien', [])
            if isinstance(pump_sensors, str):
                try:
                    pump_sensors = [int(x.strip()) for x in pump_sensors.split(',') if x.strip().isdigit()]
                except Exception:
                    pump_sensors = []

        store = {
            'pump_id': pump_id,
            'pump_data': pump_data,
            'sensors': sensors,
            'pump_sensors': pump_sensors
        }

        selected = {
            'ma_may_bom': pump_data.get('ma_may_bom') or pump_id,
            'ten_may_bom': pump_data.get('ten_may_bom') or ''
        }

        return store, selected
    except Exception as e:
        # Defensive: prevent unhandled exceptions from breaking callback schema
        import traceback
        print(f"Error in load_pump_detail: {e}\n{traceback.format_exc()}")
        return dash.no_update, dash.no_update


@callback(
    [Output('pump-info-container', 'children'), Output('pump-control-container', 'children'), Output('pump-sensors-container', 'children')],
    Input('pump-detail-store', 'data')
)
def render_pump_from_store(store):
    """Render UI parts from the centralized pump-detail store."""
    if not store or not isinstance(store, dict):
        raise PreventUpdate

    pump_data = store.get('pump_data') or {}
    sensors = store.get('sensors', [])
    pump_sensors = store.get('pump_sensors', [])

    pump_info = create_pump_info_section(pump_data)
    pump_control = create_pump_control_section(pump_data, store.get('pump_id'))
    sensor_list = create_sensor_list_section(sensors, pump_sensors)

    return pump_info, pump_control, sensor_list


@callback(
    [Output('pump-detail-data-container', 'children'), Output('pump-charts-container', 'children'), Output('pump-detail-page-store', 'data')],
    [Input('pump-detail-date-picker', 'date'), Input('pump-detail-store', 'data'), Input('pump-detail-page-store', 'data'), Input('pump-detail-showing-details', 'data')],
    [State('session-store', 'data')],
    prevent_initial_call=False
)
def load_pump_sensor_data(selected_date, pump_store, page_store, show_details, session_data):
    """Load dữ liệu cảm biến theo ngày"""
    if not pump_store or not isinstance(pump_store, dict):
        return dash.no_update, dash.no_update, dash.no_update
    pump_id = pump_store.get('pump_id')
    if not pump_id:
        return dash.no_update, dash.no_update, dash.no_update
    
    token = None
    if session_data and isinstance(session_data, dict):
        token = session_data.get('token')
    
    if not selected_date:
        selected_date = datetime.date.today().isoformat()

    page = 1
    limit = 15
    try:
        if page_store and isinstance(page_store, dict):
            page = int(page_store.get('page', 1) or 1)
            limit = int(page_store.get('limit', 15) or 15)
    except Exception:
        page, limit = 1, 15

    offset = max(0, (page - 1) * limit)
    data_response = get_data_by_date(selected_date, token=token, limit=limit, offset=offset, ma_may_bom=pump_id)
    data_list = data_response.get('data', []) if data_response else []

    
    resp_page = None
    resp_total_pages = None
    resp_total = None
    if isinstance(data_response, dict):
        resp_page = data_response.get('page')
        resp_total_pages = data_response.get('total_pages') or data_response.get('total_pages_count')
        resp_total = data_response.get('total')

    
    pump_data_list = [d for d in data_list if str(d.get('ma_may_bom')) == str(pump_id)]

    
    if resp_total is not None:
        total = int(resp_total or 0)
    else:
        total = len(pump_data_list)

    
    if resp_total_pages is not None:
        try:
            max_pages = int(resp_total_pages or 1)
        except Exception:
            max_pages = max(1, (total + 15 - 1) // 15)
    else:
        max_pages = max(1, (total + 15 - 1) // 15)

    
    if resp_page is not None:
        try:
            page = int(resp_page or 1)
        except Exception:
            page = 1

    
    try:
        df = pd.DataFrame.from_records(pump_data_list)
        if 'thoi_gian_tao' in df.columns:
            df['thoi_gian_tao'] = pd.to_datetime(df['thoi_gian_tao'], errors='coerce')
            try:
                if df['thoi_gian_tao'].dt.tz is None:
                    df['thoi_gian_tao'] = df['thoi_gian_tao'].dt.tz_localize('Asia/Bangkok')
                else:
                    df['thoi_gian_tao'] = df['thoi_gian_tao'].dt.tz_convert('Asia/Bangkok')
            except Exception:
                df['thoi_gian_tao'] = pd.to_datetime(df['thoi_gian_tao'], errors='coerce')
        else:
            df['thoi_gian_tao'] = pd.to_datetime(df.get('ngay'))

        
        for c in ['luu_luong_nuoc', 'do_am_dat', 'nhiet_do', 'do_am']:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors='coerce')

        df = df.sort_values('thoi_gian_tao')
    except Exception:
        df = pd.DataFrame.from_records(pump_data_list)

    
    fig = go.Figure()
    if 'luu_luong_nuoc' in df.columns:
        fig.add_trace(go.Scatter(x=df['thoi_gian_tao'], y=df['luu_luong_nuoc'], mode='lines+markers', name='Lưu lượng (L/phút)'))
    if 'nhiet_do' in df.columns:
        fig.add_trace(go.Scatter(x=df['thoi_gian_tao'], y=df['nhiet_do'], mode='lines+markers', name='Nhiệt độ (°C)', yaxis='y2'))
    if 'do_am_dat' in df.columns:
        fig.add_trace(go.Scatter(x=df['thoi_gian_tao'], y=df['do_am_dat'], mode='lines+markers', name='Độ ẩm đất (%)'))

    fig.update_layout(
        margin={'t': 100},
        xaxis_title='Thời gian',
        yaxis_title='Giá trị',
        showlegend=True,
        legend=dict(orientation='h', yanchor='bottom', y=1.08, xanchor='left', x=0)
    )
    fig.update_layout(yaxis2=dict(overlaying='y', side='right', title='Nhiệt độ (°C)'))

    graph = dcc.Graph(figure=fig, config={'displayModeBar': True}, style={'height': '360px'})

    
    if resp_total_pages is None:
        max_pages = max(1, (total + limit - 1) // limit)
    if page > max_pages:
        page = max_pages
    new_page_store = {'page': page, 'limit': limit, 'total': total}
    def build_numeric_buttons(current, last):
        items = []
        items.append(dbc.Button(html.I(className='fas fa-chevron-left'), id='pump-detail-page-prev', color='light', size='sm', className='me-1', disabled=(current<=1)))

        if last <= 7:
            page_sequence = list(range(1, last + 1))
        else:
            page_sequence = [1]
            left = max(2, current - 1)
            right = min(last - 1, current + 1)
            if left > 2:
                page_sequence.append('...')
            for i in range(left, right + 1):
                page_sequence.append(i)
            if right < last - 1:
                page_sequence.append('...')
            page_sequence.append(last)

        for p in page_sequence:
            if p == '...':
                items.append(html.Span('...', className='page-ellipsis mx-2 align-self-center'))
            else:
                btn_id = {'type': 'pump-detail-page', 'index': int(p)}
                is_current = (int(p) == int(current))
                if is_current:
                    items.append(dbc.Button(str(p), id=btn_id, size='sm', className='mx-1',
                                            style={'backgroundColor': '#0358A3', 'borderColor': '#0358A3', 'color': 'white'}))
                else:
                    items.append(dbc.Button(str(p), id=btn_id, color='light', size='sm', disabled=False, className='mx-1'))

        # next
        items.append(dbc.Button(html.I(className='fas fa-chevron-right'), id='pump-detail-page-next', color='light', size='sm', className='ms-1', disabled=(current>=last)))
        return items

    pager = html.Div([
        html.Span(f"Tổng bản ghi: {total}", className='me-3'),
        dbc.ButtonGroup(build_numeric_buttons(page, max_pages), className='page-pagination')
    ], className='d-flex align-items-center')
    
    if show_details:
        try:
            start = offset
        except NameError:
            start = (page - 1) * limit
        if isinstance(data_response, dict) and (resp_page is not None or resp_total_pages is not None):
            slice_rows = pump_data_list
        else:
            end = start + limit
            slice_rows = pump_data_list[start:end]

        cols = ['thoi_gian_tao', 'luu_luong_nuoc', 'nhiet_do', 'do_am', 'do_am_dat', 'ma_cam_bien']
        first = slice_rows[0] if slice_rows else {}
        headers = [c for c in cols if c in first]
        header_map = {
            'thoi_gian_tao': 'Thời gian',
            'luu_luong_nuoc': 'Lưu lượng (L/phút)',
            'nhiet_do': 'Nhiệt độ (°C)',
            'do_am': 'Độ ẩm (%)',
            'do_am_dat': 'Độ ẩm đất (%)',
            'ma_cam_bien': 'Mã cảm biến'
        }

        table_header = html.Thead(html.Tr([html.Th('#')] + [html.Th(header_map.get(h, h)) for h in headers]))
        table_rows = []
        for idx, row in enumerate(slice_rows, start + 1):
            cells = []
            for h in headers:
                val = row.get(h)
                if h == 'thoi_gian_tao':
                    cells.append(html.Td(format_datetime(val)))
                else:
                    cells.append(html.Td(val if val is not None else ''))
            table_rows.append(html.Tr([html.Td(idx)] + cells))

        table = dbc.Table([table_header, html.Tbody(table_rows)], bordered=True, striped=True, hover=True, responsive=True, size='sm')
        inline_pager = html.Div([
            html.Span(f"Tổng bản ghi: {total}", className='me-3'),
            dbc.ButtonGroup(build_numeric_buttons(page, max_pages), className='page-pagination')
        ], className='d-flex align-items-center justify-content-end')

        footer = html.Div([inline_pager, html.Div(f'Tổng: {total}', className='ms-3 text-muted')], className='mt-2')

        details_div = html.Div([table, footer], className='d-flex flex-column')
        return (details_div, graph, new_page_store)

    details_text = pager

    return (details_text, graph, new_page_store)



@callback(
    Output('pump-detail-page-store', 'data', allow_duplicate=True),
    [Input('pump-detail-page-prev', 'n_clicks'), Input('pump-detail-page-next', 'n_clicks'), Input({'type': 'pump-detail-page', 'index': ALL}, 'n_clicks')],
    [State('pump-detail-page-store', 'data')],
    prevent_initial_call=True
)
def change_pump_detail_page(prev_clicks, next_clicks, page_btns, page_store):
    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate
    trig = ctx.triggered[0]
    prop = trig.get('prop_id', '').split('.')[0]
    if not page_store or not isinstance(page_store, dict):
        page_store = {'page': 1, 'limit': 15, 'total': 0}
    page = int(page_store.get('page', 1) or 1)
    limit = int(page_store.get('limit', 15) or 15)
    total = int(page_store.get('total', 0) or 0)
    max_pages = max(1, (total + limit - 1) // limit)

    if 'pump-detail-page-prev' in prop:
        page = max(1, page - 1)
    elif 'pump-detail-page-next' in prop:
        page = min(max_pages, page + 1)
    else:
        # pattern-matching id for numeric page buttons
        try:
            # prop looks like '{"type":"pump-detail-page","index":3}'
            id_dict = json.loads(prop)
            if isinstance(id_dict, dict) and id_dict.get('type') == 'pump-detail-page':
                idx = int(id_dict.get('index', page))
                page = max(1, min(max_pages, idx))
            else:
                raise PreventUpdate
        except Exception:
            raise PreventUpdate

    return {'page': page, 'limit': limit, 'total': total}


@callback(
    [Output('pump-detail-showing-details', 'data'), Output('pump-detail-page-store', 'data', allow_duplicate=True)],
    Input('pump-detail-show-details', 'n_clicks'),
    [State('pump-detail-showing-details', 'data'), State('pump-detail-page-store', 'data')],
    prevent_initial_call=True
)
def toggle_pump_detail_show(n_clicks, current, page_store):
    """Toggle the inline details view when the user clicks 'Xem chi tiết'. """
    current_bool = bool(current)
    new_show = not current_bool

    if not page_store or not isinstance(page_store, dict):
        page_store = {'page': 1, 'limit': 15, 'total': 0}
    try:
        page = int(page_store.get('page', 1) or 1)
    except Exception:
        page = 1
    try:
        limit = int(page_store.get('limit', 15) or 15)
    except Exception:
        limit = 15
    try:
        total = int(page_store.get('total', 0) or 0)
    except Exception:
        total = 0

    if total <= 0:
        max_pages = 1
    else:
        max_pages = max(1, (total + limit - 1) // limit)

    if new_show:
        if page > max_pages:
            page = max_pages
        if page < 1:
            page = 1

    new_page_store = {'page': page, 'limit': limit, 'total': total}
    return new_show, new_page_store


@callback(
    Output('pump-detail-date-picker', 'date'),
    [Input('pump-detail-prev', 'n_clicks'), Input('pump-detail-next', 'n_clicks')],
    State('pump-detail-date-picker', 'date'),
    prevent_initial_call=True
)
def change_pump_detail_date(prev_clicks, next_clicks, current_date):
    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    if not current_date:
        current_date = datetime.date.today().isoformat()
    try:
        current = datetime.datetime.strptime(current_date, '%Y-%m-%d').date()
    except Exception:
        current = datetime.date.today()
    today = datetime.date.today()
    if button_id == 'pump-detail-prev':
        new_date = current - datetime.timedelta(days=1)
        return new_date.isoformat()
    elif button_id == 'pump-detail-next':
        new_date = current + datetime.timedelta(days=1)
        if new_date <= today:
            return new_date.isoformat()
        return current_date
    raise PreventUpdate


@callback(
    Output('url', 'pathname', allow_duplicate=True),
    Input('pump-detail-back', 'n_clicks'),
    prevent_initial_call=True
)
def go_back(n_clicks):
    """Quay lại trang danh sách máy bơm"""
    if not n_clicks:
        raise PreventUpdate
    return '/pump'



@callback(
    [Output('pump-control-result', 'children', allow_duplicate=True), Output('pump-detail-store', 'data', allow_duplicate=True), Output('pump-control-last-action', 'data', allow_duplicate=True)],
    [Input('pump-start-btn', 'n_clicks'), Input('pump-stop-btn', 'n_clicks'), Input('pump-mode-select', 'value')],
    [State('pump-detail-store', 'data'), State('session-store', 'data'), State('pump-control-last-action', 'data')],
    prevent_initial_call=True
)
def handle_pump_control(n_start, n_stop, mode_value, store, session_data, last_action_state):
    """Handle pump start/stop and mode changes using start/stop buttons and the mode selector."""
    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate

    prop = ctx.triggered[0]['prop_id']
    button_id = prop.split('.')[0] if prop else None

    if not store or not isinstance(store, dict):
        return (dbc.Alert('Không có thông tin máy bơm', color='danger'), dash.no_update, dash.no_update)

    pump_id = store.get('pump_id')
    token = None
    if session_data and isinstance(session_data, dict):
        token = session_data.get('token')

    
    pump = get_pump(pump_id, token=token)
    if not pump:
        return (dbc.Alert('Không thể lấy thông tin máy bơm', color='danger'), dash.no_update, dash.no_update)

    payload = {}
    msg = ''
    success = False
    last_action = last_action_state if isinstance(last_action_state, dict) else {'mode': None, 'trang_thai': None}
    last_action_new = last_action.copy()
    try:
        if button_id == 'pump-start-btn':
            if last_action.get('trang_thai') is True:
                return (dash.no_update, dash.no_update, dash.no_update)
            payload = {
                'ten_may_bom': pump.get('ten_may_bom', ''),
                'mo_ta': pump.get('mo_ta', ''),
                'che_do': pump.get('che_do'),
                'trang_thai': True
            }
            success, msg = update_pump(pump_id, payload, token=token)
            last_action_new['trang_thai'] = True
        elif button_id == 'pump-stop-btn':
            if last_action.get('trang_thai') is False:
                return (dash.no_update, dash.no_update, dash.no_update)
            payload = {
                'ten_may_bom': pump.get('ten_may_bom', ''),
                'mo_ta': pump.get('mo_ta', ''),
                'che_do': pump.get('che_do'),
                'trang_thai': False
            }
            success, msg = update_pump(pump_id, payload, token=token)
            last_action_new['trang_thai'] = False
        elif button_id == 'pump-mode-select':
            try:
                new_mode = int(mode_value)
            except Exception:
                new_mode = mode_value
            current_mode = pump.get('che_do') if isinstance(pump, dict) else None
            if new_mode is None or new_mode == current_mode or last_action.get('mode') == new_mode:
                return (dash.no_update, dash.no_update, dash.no_update)
            payload = {
                'ten_may_bom': pump.get('ten_may_bom', ''),
                'mo_ta': pump.get('mo_ta', ''),
                'che_do': new_mode,
                'trang_thai': bool(pump.get('trang_thai', False))
            }
            success, msg = update_pump(pump_id, payload, token=token)
            last_action_new['mode'] = new_mode
        else:
            raise PreventUpdate
    except Exception as e:
        return (dbc.Alert(f'Lỗi khi gọi API: {e}', color='danger'), dash.no_update, dash.no_update)

    updated_pump = get_pump(pump_id, token=token) or pump
    alert = dbc.Alert(msg if msg else ('Thành công' if success else 'Thao tác thất bại'), color='success' if success else 'warning')

    new_store = store.copy() if isinstance(store, dict) else {}
    new_store.update({'pump_id': pump_id, 'pump_data': updated_pump, 'sensors': store.get('sensors', []), 'pump_sensors': store.get('pump_sensors', [])})

    return (alert, new_store, last_action_new)

