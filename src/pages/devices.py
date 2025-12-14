from dash import html, dcc, callback, Input, Output, State
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
from components.navbar import create_navbar
from components.topbar import TopBar
from api.sensor import list_sensors, create_sensor, update_sensor, delete_sensor, get_sensor, get_sensor_types
from api.pump import list_pumps, create_pump, update_pump, delete_pump, get_pump
import dash
import datetime
import pandas as pd


def create_status_badge(status):
    if status:
        return dbc.Badge("● Đang chạy", color="success", className="me-2")
    else:
        return dbc.Badge("● Đã dừng", color="warning", className="me-2")


def format_datetime(dt_str):
    if not dt_str:
        return "Không có dữ liệu"
    try:
        dt = pd.to_datetime(dt_str, utc=True)
        dt_local = dt.tz_convert('Asia/Bangkok')
        return dt_local.strftime('%H:%M:%S %d/%m/%Y')
    except:
        return "Không có dữ liệu"


def create_sensor_card(sensor, pump_name=""):
    """Tạo card hiển thị dữ liệu cảm biến"""
    return dbc.Col([
        dbc.Card([
            dbc.CardBody([
                html.Div([
                    html.Div([
                        html.H6(sensor.get('ten_cam_bien', 'Cảm biến'), className="mb-1"),
                        html.Small(f"Loại: {sensor.get('ten_loai_cam_bien', 'Chưa xác định')}", className="text-muted d-block"),
                    ]),
                ], className="d-flex justify-content-between align-items-start mb-3"),
                
                html.Div([
                    html.P("Mô tả:", className="mb-1 fw-bold"),
                    html.P(sensor.get('mo_ta', 'Không có'), className="text-muted small mb-2"),
                ]),

                html.Div([
                    html.P("Máy bơm:", className="mb-1 fw-bold"),
                    html.P(pump_name if pump_name else "Chưa kết nối", className="text-muted small mb-2"),
                ]),
                
                html.Small([
                    f"Lắp đặt: {sensor.get('ngay_lap_dat', 'N/A')}"
                ], className="text-muted d-block")
            ])
        ], className="sensor-card")
    ], xs=12, sm=6, md=3, className="mb-3")


layout = html.Div([
    create_navbar(is_authenticated=True),
    
    dbc.Container([
        dbc.Row([
            dbc.Col(TopBar(
                'Hệ Thống Cảm Biến & Máy Bơm',
                extra_left=[],
                extra_right=[]
            ), md=12)
        ], className='my-3'),

        # Phần Máy Bơm (Một máy bơm) và Lịch sử
        dbc.Row([
            dbc.Col([
                html.H5("Máy Bơm Chính", className="section-title mb-3")
            ], md=12)
        ]),

        dbc.Row([
            dbc.Col(id="device-main-pump-container", md=8, className="mb-4"),
            dbc.Col(id="device-pump-history-container", md=4, className="mb-4")
        ]),

        # Phần Cảm Biến (Tối đa 4 cảm biến)
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.H5("Cảm Biến Hệ Thống", className="section-title mb-0"),
                ], className="d-flex align-items-center justify-content-between")
            ], md=12)
        ], className="mb-3"),

        dbc.Row(id="device-sensors-grid", className="sensors-grid mb-4"),

        html.Div(id="device-no-sensors-alert", style={"display": "none"}),

        # Phần Biểu đồ Cảm Biến (dưới cùng)
        dbc.Row([
            dbc.Col([
                html.H5("Dữ Liệu Cảm Biến", className="section-title mb-3")
            ], md=12)
        ]),

        dbc.Row([
            dbc.Col([
                dcc.Graph(id='device-sensor-chart')
            ], md=12, className="mb-4")
        ]),

        # Data stores
        dcc.Store(id='device-pump-data-store'),
        dcc.Store(id='device-sensor-data-store'),
        dcc.Store(id='device-sensor-types-store'),
        dcc.Store(id='device-sensor-pumps-store'),
        dcc.Store(id='device-sensor-delete-id'),
        dcc.Store(id='device-pump-delete-id'),
        dcc.Store(id='device-sensor-edit-id'),
        dcc.Store(id='device-pump-edit-id'),
        dcc.Interval(id='device-refresh-interval', interval=5*1000, n_intervals=0),

        # Modals for Pump
        dbc.Modal([
            dbc.ModalHeader(id='device-pump-modal-title'),
            dbc.ModalBody([
                dbc.Form([
                    dbc.Label('Tên máy bơm'),
                    dbc.Input(id='device-pump-ten', type='text'),
                    dbc.Label('Mô tả', className='mt-2'),
                    dbc.Textarea(id='device-pump-mo-ta'),
                    dbc.Label('Chế độ', className='mt-2'),
                    dcc.Dropdown(
                        id='device-pump-che-do',
                        options=[
                            {'label': 'Thủ công', 'value': 0},
                            {'label': 'Tự động', 'value': 1}
                        ],
                        value=0,
                        clearable=False
                    ),
                    dbc.Label('Trạng thái', className='mt-2'),
                    dcc.Dropdown(id='device-pump-trang-thai', options=[{'label': 'Tắt', 'value': False}, {'label': 'Bật', 'value': True}], value=False, clearable=False),
                ])
            ]),
            dbc.ModalFooter([
                dbc.Button('Lưu', id='device-pump-save', className='btn-edit'),
                dbc.Button('Đóng', id='device-pump-cancel', className='ms-2 btn-cancel')
            ])
        ], id='device-pump-modal', is_open=False, centered=True),

        dbc.Modal([
            dbc.ModalHeader('Xác nhận xóa máy bơm'),
            dbc.ModalBody('Bạn có chắc chắn muốn xóa máy bơm này?'),
            dbc.ModalFooter([
                dbc.Button('Xóa', id='device-confirm-delete-pump', className='btn-delete'),
                dbc.Button('Hủy', id='device-confirm-cancel-pump', className='ms-2 btn-cancel')
            ])
        ], id='device-confirm-delete-pump-modal', is_open=False, centered=True),

        # Modals for Sensor
        dbc.Modal([
            dbc.ModalHeader(id='device-sensor-modal-title'),
            dbc.ModalBody([
                dbc.Form([
                    dbc.Label('Tên cảm biến'),
                    dbc.Input(id='device-sensor-ten', type='text'),
                    dbc.Label('Mô tả', className='mt-2'),
                    dbc.Textarea(id='device-sensor-mo-ta'),
                    dbc.Label('Máy bơm', className='mt-2'),
                    dcc.Dropdown(id='device-sensor-ma-may-bom', options=[], value=None, placeholder='Chọn máy bơm', clearable=False),
                    dbc.Label('Ngày lắp đặt', className='mt-2'),
                    dbc.Input(id='device-sensor-ngay-lap-dat', type='date', value=str(datetime.date.today())),
                    dbc.Label('Loại cảm biến', className='mt-2'),
                    dcc.Dropdown(id='device-sensor-loai', options=[], value=None, placeholder='Chọn loại cảm biến', clearable=False),
                ])
            ]),
            dbc.ModalFooter([
                dbc.Button('Lưu', id='device-sensor-save', className='btn-edit'),
                dbc.Button('Đóng', id='device-sensor-cancel', className='ms-2 btn-cancel')
            ])
        ], id='device-sensor-modal', is_open=False, centered=True),

        dbc.Modal([
            dbc.ModalHeader('Xác nhận xóa cảm biến'),
            dbc.ModalBody('Bạn có chắc chắn muốn xóa cảm biến này?'),
            dbc.ModalFooter([
                dbc.Button('Xóa', id='device-confirm-delete-sensor', className='btn-delete'),
                dbc.Button('Hủy', id='device-confirm-cancel-sensor', className='ms-2 btn-cancel')
            ])
        ], id='device-confirm-delete-sensor-modal', is_open=False, centered=True)

    ], fluid=True, style={"padding":"20px 40px"})
], className='page-container', style={"paddingTop": "5px"})


# ============ LOAD DATA CALLBACKS ============

@callback(
    [Output('device-pump-data-store', 'data', allow_duplicate=True), Output('device-sensor-data-store', 'data', allow_duplicate=True)],
    [Input('device-refresh-interval', 'n_intervals')],
    State('session-store', 'data'),
    prevent_initial_call='initial_duplicate'
)
def device_load_all_data(n_intervals, session_data):
    token = None
    if session_data and isinstance(session_data, dict):
        token = session_data.get('token')
    
    pump_data = {'data': []}
    sensor_data = {'data': []}
    
    try:
        pump_data = list_pumps(limit=1, offset=0, token=token)
        # print(f"DEBUG: pump_data = {pump_data}")
    except Exception as e:
        print(f"ERROR loading pumps: {str(e)}")
        import traceback
        traceback.print_exc()
    
    try:
        sensor_data = list_sensors(limit=100, offset=0, token=token)
        # print(f"DEBUG: sensor_data = {sensor_data}")
    except Exception as e:
        print(f"ERROR loading sensors: {str(e)}")
        import traceback
        traceback.print_exc()
    
    return pump_data, sensor_data


# ============ PUMP DISPLAY CALLBACKS ============

@callback(
    Output('device-main-pump-container', 'children'),
    Input('device-pump-data-store', 'data')
)
def device_render_main_pump(pump_data):
    # print(f"[DEBUG] device_render_main_pump: pump_data = {pump_data}")
    
    if not pump_data or not isinstance(pump_data, dict):
        return dbc.Alert("Chưa có máy bơm. Vui lòng thêm máy bơm mới.", color="info", className="mt-3")
    
    pumps = pump_data.get('data', [])
    # print(f"[DEBUG] pumps = {pumps}")
    
    if not pumps:
        return dbc.Alert("Chưa có máy bơm. Vui lòng thêm máy bơm mới.", color="info", className="mt-3")
    
    pump = pumps[0]  # Lấy máy bơm đầu tiên (chỉ có 1 máy bơm)
    # print(f"[DEBUG] rendering pump: {pump}")
    
    return dbc.Card([
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.H5(pump.get('ten_may_bom', 'Máy bơm'), className="mb-2"),
                        html.P(pump.get('mo_ta', 'Mô tả máy bơm'), className="text-muted"),
                    ])
                ], md=8),
                dbc.Col([
                    html.Div([
                        create_status_badge(pump.get('trang_thai', False)),
                        dbc.Badge(
                            {0: "Thủ công", 1: "Tự động"}.get(pump.get('che_do', 0), "Thủ công"),
                            color="primary",
                            className="ms-2"
                        )
                    ], className="text-end")
                ], md=4, className="d-flex justify-content-end align-items-center")
            ]),
            
            html.Hr(className="my-3"),
            
            dbc.Row([
                dbc.Col([
                    html.P("Lưu lượng", className="text-muted small mb-1"),
                    html.H6(f"{pump.get('luu_luong', 0)} L/phút", className="mb-0")
                ], xs=6, sm=3),
                dbc.Col([
                    html.P("Mưa", className="text-muted small mb-1"),
                    html.H6("Có" if pump.get('mua', False) else "Không", className="mb-0")
                ], xs=6, sm=3),
                dbc.Col([
                    html.P("Nhiệt độ", className="text-muted small mb-1"),
                    html.H6(f"{pump.get('nhiet_do', 0)}°C", className="mb-0")
                ], xs=6, sm=3),
                dbc.Col([
                    html.P("Độ ẩm", className="text-muted small mb-1"),
                    html.H6(f"{pump.get('do_am', 0)}%", className="mb-0")
                ], xs=6, sm=3),
            ]),
            
            html.Hr(className="my-3"),
            
            html.Div([
                # Removed Edit/Delete/Add buttons for pump
            ], className="d-flex")
        ])
    ], className="pump-main-card")


# ============ PUMP HISTORY CALLBACK ============

@callback(
    Output('device-pump-history-container', 'children'),
    Input('device-pump-data-store', 'data')
)
def device_render_pump_history(pump_data):
    if not pump_data or not isinstance(pump_data, dict):
        return dbc.Card([
            dbc.CardBody([
                html.P("Không có dữ liệu", className="text-muted")
            ])
        ])
    
    pumps = pump_data.get('data', [])
    if not pumps:
        return dbc.Card([
            dbc.CardBody([
                html.P("Không có dữ liệu", className="text-muted")
            ])
        ])
    
    pump = pumps[0]
    
    return dbc.Card([
        dbc.CardHeader(html.H6("Nhật ký hoạt động", className="mb-0")),
        dbc.CardBody([
            html.Div([
                html.P("Trạng thái hiện tại:", className="mb-1"),
                create_status_badge(pump.get('trang_thai', False)),
                html.Hr(className="my-2"),
                html.P("Chế độ hoạt động:", className="mb-1"),
                html.P(
                    {0: "Thủ công", 1: "Tự động"}.get(pump.get('che_do', 0), "Thủ công"),
                    className="fw-bold"
                ),
                html.Hr(className="my-2"),
                html.P("Ngày cập nhật:", className="mb-1"),
                html.Small(
                    format_datetime(pump.get('ngay_cap_nhat', '')),
                    className="text-muted"
                ),
            ], className="text-muted")
        ])
    ])


# ============ SENSOR CHART CALLBACK ============

@callback(
    Output('device-sensor-chart', 'figure'),
    Input('device-sensor-data-store', 'data')
)
def device_render_sensor_chart(sensor_data):
    import plotly.graph_objects as go
    
    if not sensor_data or not isinstance(sensor_data, dict):
        return {
            'data': [],
            'layout': go.Layout(title="Không có dữ liệu cảm biến")
        }
    
    sensors = sensor_data.get('data', [])
    if not sensors:
        return {
            'data': [],
            'layout': go.Layout(title="Không có dữ liệu cảm biến")
        }
    
    # Tạo biểu đồ với dữ liệu từ cảm biến
    sensor_names = [s.get('ten_cam_bien', 'Cảm biến') for s in sensors]
    sensor_values = [s.get('gia_tri', 0) for s in sensors]
    
    fig = go.Figure(data=[
        go.Bar(
            x=sensor_names,
            y=sensor_values,
            marker=dict(color='#0358a3'),
            text=sensor_values,
            textposition='auto',
        )
    ])
    
    fig.update_layout(
        title="Dữ liệu cảm biến thời gian thực",
        xaxis_title="Cảm biến",
        yaxis_title="Giá trị",
        hovermode='x unified',
        margin=dict(l=50, r=50, t=50, b=50),
        height=300
    )
    
    return fig


# ============ SENSORS DISPLAY CALLBACKS ============

@callback(
    [Output('device-sensors-grid', 'children'), Output('device-no-sensors-alert', 'children')],
    [Input('device-sensor-data-store', 'data'),
     Input('device-pump-data-store', 'data')]
)
def device_render_sensors(sensor_data, pump_data):
    if not sensor_data or not isinstance(sensor_data, dict):
        alert = dbc.Alert("❌ Lỗi tải dữ liệu cảm biến", color="danger")
        return [], alert
    
    sensors = sensor_data.get('data', [])
    
    if not sensors:
        alert = dbc.Alert([
            html.I(className="fas fa-info-circle me-2"),
            "Chưa có cảm biến nào."
        ], color="info")
        return [], alert
    
    # Map pump names
    pump_map = {}
    if pump_data and isinstance(pump_data, dict):
        for p in pump_data.get('data', []):
            pump_map[p.get('ma_may_bom')] = p.get('ten_may_bom')

    # Giới hạn tối đa 4 cảm biến
    sensor_cards = []
    for s in sensors[:4]:
        pump_name = pump_map.get(s.get('ma_may_bom'))
        sensor_cards.append(create_sensor_card(s, pump_name))
    
    # Nếu có ít hơn 4 cảm biến, hiển thị thông báo
    if len(sensors) < 4:
        alert = dbc.Alert([
            html.I(className="fas fa-exclamation-triangle me-2"),
            f"Có {len(sensors)}/4 cảm biến."
        ], color="warning")
        return sensor_cards, alert
    
    return sensor_cards, html.Div()


# ============ PUMP FORM CALLBACKS ============
# Callbacks for pump management (add/edit/delete) have been removed as per requirements.



# ============ SENSOR FORM CALLBACKS ============
# Callbacks for sensor management (add/edit/delete) have been removed as per requirements.


