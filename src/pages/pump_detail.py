from dash import html, dcc, callback, Input, Output, State
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
from components.navbar import create_navbar
from components.topbar import TopBar
from api.pump import get_pump
from api.sensor import list_sensors
from api.sensor_data import get_data_by_date, get_data_by_pump
import dash
import datetime
import pandas as pd


def format_datetime(dt_str):
    if not dt_str:
        return "Không có dữ liệu"
    try:
        dt = pd.to_datetime(dt_str, utc=True)
        dt_local = dt.tz_convert('Asia/Bangkok')
        return dt_local.strftime('%H:%M %d/%m/%Y')
    except:
        return "Không có dữ liệu"


def create_pump_info_section(pump):
    """Tạo phần thông tin chi tiết máy bơm"""
    status = "Đang chạy" if pump.get('trang_thai', False) else "Đã dừng"
    status_color = "success" if pump.get('trang_thai', False) else "warning"
    
    mode_map = {0: "Thủ công", 1: "Tự động", 2: "Bảo trì"}
    mode = mode_map.get(pump.get('che_do', 0), "Thủ công")
    
    return dbc.Card([
        dbc.CardBody([
            html.H4(pump.get('ten_may_bom', 'N/A'), className="mb-3"),
            
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.Label("Trạng thái", className="fw-bold"),
                        html.Span(status, className=f"badge bg-{status_color} ms-2")
                    ], className="mb-3")
                ], md=6),
                dbc.Col([
                    html.Div([
                        html.Label("Chế độ", className="fw-bold"),
                        html.Span(mode, className="badge bg-info ms-2")
                    ], className="mb-3")
                ], md=6),
            ]),
            
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.Label("Mô tả", className="fw-bold"),
                        html.P(pump.get('mo_ta', 'Không có mô tả'))
                    ], className="mb-3")
                ], md=12),
            ]),
            
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.Label("Mã IoT", className="fw-bold"),
                        html.P(pump.get('ma_iot', 'Không có mã IoT'))
                    ], className="mb-3")
                ], md=6),
                dbc.Col([
                    html.Div([
                        html.Label("Ngày tạo", className="fw-bold"),
                        html.P(format_datetime(pump.get('thoi_gian_tao')))
                    ], className="mb-3")
                ], md=6),
            ]),
            
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.Label("Lưu lượng (L/phút)", className="fw-bold"),
                        html.P(f"{pump.get('luu_luong', 0)}")
                    ], className="mb-3")
                ], md=3),
                dbc.Col([
                    html.Div([
                        html.Label("Nhiệt độ (°C)", className="fw-bold"),
                        html.P(f"{pump.get('nhiet_do', 0)}")
                    ], className="mb-3")
                ], md=3),
                dbc.Col([
                    html.Div([
                        html.Label("Độ ẩm (%)", className="fw-bold"),
                        html.P(f"{pump.get('do_am', 0)}")
                    ], className="mb-3")
                ], md=3),
                dbc.Col([
                    html.Div([
                        html.Label("Mưa", className="fw-bold"),
                        html.P("Có" if pump.get('mua', False) else "Không")
                    ], className="mb-3")
                ], md=3),
            ]),
        ])
    ], className="mb-4")


def create_sensor_list_section(sensors, pump_sensors):
    """Tạo phần danh sách cảm biến"""
    sensor_dict = {s.get('ma_cam_bien'): s for s in sensors}
    
    sensor_rows = []
    if pump_sensors:
        for idx, sensor_id in enumerate(pump_sensors, 1):
            sensor = sensor_dict.get(sensor_id, {})
            sensor_rows.append(
                html.Tr([
                    html.Td(idx),
                    html.Td(sensor.get('ten_cam_bien', 'Không xác định')),
                    html.Td(sensor.get('loai_cam_bien', 'N/A')),
                    html.Td(format_datetime(sensor.get('thoi_gian_tao')))
                ])
            )
    
    if not sensor_rows:
        sensor_rows = [html.Tr([html.Td("Không có cảm biến nào", colSpan=4, className="text-center text-muted")])]
    
    return dbc.Card([
        dbc.CardHeader(html.H5("Danh sách cảm biến", className="mb-0")),
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
    ], className="mb-4")


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
                dbc.Col(html.Div(id="pump-info-container"))
            ]),
            
            dbc.Row([
                dbc.Col(html.Div(id="pump-sensors-container"))
            ]),
            
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([
                            html.H5("Dữ liệu cảm biến theo ngày", className="mb-0 d-inline-block"),
                            dbc.Row([
                                dbc.Col([
                                    dcc.DatePickerSingle(
                                        id='pump-detail-date-picker',
                                        date=datetime.date.today().isoformat(),
                                        display_format='DD/MM/YYYY',
                                        max_date_allowed=datetime.date.today().isoformat(),
                                        initial_visible_month=datetime.date.today().isoformat(),
                                        className='d-inline-block ms-3'
                                    )
                                ], width=3)
                            ], className="mt-2")
                        ]),
                        dbc.CardBody([
                            dcc.Loading(html.Div(id="pump-detail-data-container"))
                        ])
                    ], className="mb-4")
                ])
            ]),
            
            dcc.Store(id='pump-detail-store', storage_type='memory'),
        ], fluid=True, style={"padding": "20px 40px"})
    ], className='page-container', style={"paddingTop": "5px"})


# Khởi tạo layout
layout = create_layout()


@callback(
    [Output('pump-info-container', 'children'),
     Output('pump-sensors-container', 'children'),
     Output('pump-detail-store', 'data')],
    Input('url', 'pathname'),
    State('session-store', 'data'),
    prevent_initial_call=True
)
def load_pump_detail(pathname, session_data):
    """Load thông tin chi tiết máy bơm từ URL"""
    if not pathname or not pathname.startswith('/pump/'):
        raise PreventUpdate
    
    try:
        pump_id = int(pathname.split('/')[-1])
    except (ValueError, IndexError):
        return (
            dbc.Alert("Mã máy bơm không hợp lệ", color="danger"),
            dbc.Alert("Mã máy bơm không hợp lệ", color="danger"),
            {'pump_id': None}
        )
    
    token = None
    if session_data and isinstance(session_data, dict):
        token = session_data.get('token')
    
    # Lấy thông tin máy bơm
    pump_data = get_pump(pump_id, token=token)
    if not pump_data or isinstance(pump_data, dict) and pump_data.get('error'):
        return (
            dbc.Alert("Không tìm thấy máy bơm", color="warning"),
            dbc.Alert("Không tìm thấy máy bơm", color="warning"),
            {'pump_id': None}
        )
    
    # Lấy danh sách cảm biến
    sensors_data = list_sensors(limit=1000, token=token)
    sensors = sensors_data.get('data', []) if sensors_data else []
    
    # Lấy danh sách cảm biến của máy bơm
    pump_sensors = []
    if isinstance(pump_data, dict):
        pump_sensors = pump_data.get('cam_bien', [])
        if isinstance(pump_sensors, str):
            pump_sensors = [int(x.strip()) for x in pump_sensors.split(',') if x.strip().isdigit()]
    
    pump_info = create_pump_info_section(pump_data)
    sensor_list = create_sensor_list_section(sensors, pump_sensors)
    
    return (
        pump_info,
        sensor_list,
        {'pump_id': pump_id, 'sensors': pump_sensors}
    )


@callback(
    Output('pump-detail-data-container', 'children'),
    [Input('pump-detail-date-picker', 'date'),
     Input('url', 'pathname')],
    [State('session-store', 'data')],
    prevent_initial_call=False
)
def load_pump_sensor_data(selected_date, pathname, session_data):
    """Load dữ liệu cảm biến theo ngày"""
    if not pathname or not pathname.startswith('/pump/'):
        raise PreventUpdate
    
    try:
        pump_id = int(pathname.split('/')[-1])
    except (ValueError, IndexError):
        return dbc.Alert("Mã máy bơm không hợp lệ", color="danger")
    
    token = None
    if session_data and isinstance(session_data, dict):
        token = session_data.get('token')
    
    if not selected_date:
        selected_date = datetime.date.today().isoformat()
    
    # Lấy dữ liệu cảm biến của máy bơm theo ngày
    data_response = get_data_by_date(selected_date, token=token, limit=1440)
    data_list = data_response.get('data', []) if data_response else []
    
    # Lọc dữ liệu cho máy bơm hiện tại
    pump_data_list = [d for d in data_list if d.get('ma_may_bom') == pump_id]
    
    if not pump_data_list:
        return dbc.Alert(f"Không có dữ liệu cho ngày {selected_date}", color="info")
    
    # Tạo bảng dữ liệu
    rows = []
    for idx, d in enumerate(pump_data_list, 1):
        rows.append(
            html.Tr([
                html.Td(idx),
                html.Td(d.get('ngay', 'N/A')),
                html.Td(f"{d.get('luu_luong_nuoc', 0)}"),
                html.Td(f"{d.get('do_am_dat', 0)}"),
                html.Td(f"{d.get('nhiet_do', 0)}"),
                html.Td(f"{d.get('do_am', 0)}"),
                html.Td("Có mưa" if d.get('mua', False) else "Không mưa"),
                html.Td(d.get('so_xung', 0)),
                html.Td(f"{d.get('tong_the_tich', 0)}"),
                html.Td(d.get('ghi_chu', '') or ''),
            ])
        )
    
    return html.Div([
        html.Div([
            html.Table([
                html.Thead(
                    html.Tr([
                        html.Th("STT"),
                        html.Th("Ngày"),
                        html.Th("Lưu lượng (L/phút)"),
                        html.Th("Độ ẩm đất (%)"),
                        html.Th("Nhiệt độ (°C)"),
                        html.Th("Độ ẩm (%)"),
                        html.Th("Mưa"),
                        html.Th("Số xung"),
                        html.Th("Tổng thể tích (L)"),
                        html.Th("Ghi chú")
                    ])
                ),
                html.Tbody(rows)
            ], className="table table-sm table-hover mb-0")
        ], className="table-responsive")
    ])


@callback(
    Output('url', 'pathname', allow_duplicate=True),
    Input('pump-detail-back', 'n_clicks'),
    prevent_initial_call=True
)
def go_back(n_clicks):
    """Quay lại trang danh sách máy bơm"""
    return '/pump'

