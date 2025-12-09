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
                    html.Div([
                        dbc.Button(
                            [html.I(className="fas fa-edit me-1"), "Sửa"],
                            id={'type': 'device-edit-sensor', 'index': sensor.get('ma_cam_bien')},
                            color="primary",
                            outline=True,
                            size="sm",
                            className="me-2"
                        ),
                        dbc.Button(
                            [html.I(className="fas fa-trash me-1"), "Xóa"],
                            id={'type': 'device-delete-sensor', 'index': sensor.get('ma_cam_bien')},
                            color="danger",
                            outline=True,
                            size="sm"
                        )
                    ])
                ], className="d-flex justify-content-between align-items-start mb-3"),
                
                html.Div([
                    html.P("Mô tả:", className="mb-1 fw-bold"),
                    html.P(sensor.get('mo_ta', 'Không có'), className="text-muted small mb-2"),
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
                    dbc.Button([
                        html.I(className="fas fa-plus me-2"),
                        "Thêm cảm biến"
                    ], id="device-open-add-sensor", color="primary", size="sm", className="ms-2")
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
                dbc.Button(
                    [html.I(className="fas fa-edit me-2"), "Sửa"],
                    id={'type': 'device-edit-pump', 'index': pump.get('ma_may_bom')},
                    color="primary",
                    outline=True,
                    size="sm",
                    className="me-2"
                ),
                dbc.Button(
                    [html.I(className="fas fa-trash me-2"), "Xóa"],
                    id={'type': 'device-delete-pump', 'index': pump.get('ma_may_bom')},
                    color="danger",
                    outline=True,
                    size="sm",
                    className="me-2"
                ),
                dbc.Button([
                    html.I(className="fas fa-plus me-2"),
                    "Thêm"
                ],
                    id="device-open-add-pump",
                    color="success",
                    size="sm",
                    className="ms-auto"
                )
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
    Input('device-sensor-data-store', 'data')
)
def device_render_sensors(sensor_data):
    if not sensor_data or not isinstance(sensor_data, dict):
        alert = dbc.Alert("❌ Lỗi tải dữ liệu cảm biến", color="danger")
        return [], alert
    
    sensors = sensor_data.get('data', [])
    
    if not sensors:
        alert = dbc.Alert([
            html.I(className="fas fa-info-circle me-2"),
            "Chưa có cảm biến nào. Thêm cảm biến để theo dõi hệ thống."
        ], color="info")
        return [], alert
    
    # Giới hạn tối đa 4 cảm biến
    sensor_cards = [create_sensor_card(s) for s in sensors[:4]]
    
    # Nếu có ít hơn 4 cảm biến, hiển thị thông báo
    if len(sensors) < 4:
        alert = dbc.Alert([
            html.I(className="fas fa-exclamation-triangle me-2"),
            f"Có {len(sensors)}/4 cảm biến. Hãy thêm cảm biến khác để có đầy đủ thông tin."
        ], color="warning")
        return sensor_cards, alert
    
    return sensor_cards, html.Div()


# ============ PUMP FORM CALLBACKS ============

@callback(
    Output('device-pump-modal', 'is_open'),
    [Input('device-open-add-pump', 'n_clicks'), 
     Input('device-pump-save', 'n_clicks'),
     Input('device-pump-cancel', 'n_clicks'),
     Input({'type': 'device-edit-pump', 'index': dash.ALL}, 'n_clicks'),
     Input({'type': 'device-delete-pump', 'index': dash.ALL}, 'n_clicks')],
    State('device-pump-modal', 'is_open'),
    prevent_initial_call=True
)
def device_toggle_pump_modal(add_click, save_click, cancel_click, edit_clicks, delete_clicks, is_open):
    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate
    
    trig_id = ctx.triggered[0]['prop_id'].split('.')[0]
    trig_value = ctx.triggered[0]['value']
    
    # Nếu chưa được nhấp (n_clicks=0 hoặc None), không xử lý
    if trig_value is None or trig_value == 0:
        raise PreventUpdate
    
    # Không mở modal khi xóa
    if 'device-delete-pump' in trig_id:
        raise PreventUpdate
    
    # Nếu lưu thành công, đóng modal
    if 'device-pump-save' in trig_id:
        return False
    
    # Nếu hủy, đóng modal
    if 'device-pump-cancel' in trig_id:
        return False
    
    # Nếu mở thêm hoặc sửa, mở modal
    return True


@callback(
    [Output('device-pump-modal-title', 'children'),
     Output('device-pump-edit-id', 'data'),
     Output('device-pump-ten', 'value'),
     Output('device-pump-mo-ta', 'value'),
     Output('device-pump-che-do', 'value'),
     Output('device-pump-trang-thai', 'value')],
    [Input('device-open-add-pump', 'n_clicks'),
     Input({'type': 'device-edit-pump', 'index': dash.ALL}, 'n_clicks')],
    State('device-pump-data-store', 'data'),
    prevent_initial_call=True
)
def device_load_pump_form(add_click, edit_clicks, pump_data):
    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate
    
    trig_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if 'device-open-add-pump' in trig_id:
        return 'Thêm máy bơm mới', None, '', '', 0, False
    
    try:
        import json
        obj = json.loads(trig_id)
        pump_id = obj.get('index')
        
        if pump_data and isinstance(pump_data, dict):
            pumps = pump_data.get('data', [])
            for pump in pumps:
                if pump.get('ma_may_bom') == pump_id:
                    return f"Sửa máy bơm: {pump.get('ten_may_bom')}", pump_id, \
                           pump.get('ten_may_bom', ''), pump.get('mo_ta', ''), \
                           pump.get('che_do', 0), pump.get('trang_thai', False)
    except Exception:
        pass
    
    raise PreventUpdate


@callback(
    Output('device-pump-data-store', 'data', allow_duplicate=True),
    Input('device-pump-save', 'n_clicks'),
    [State('device-pump-ten', 'value'),
     State('device-pump-mo-ta', 'value'),
     State('device-pump-che-do', 'value'),
     State('device-pump-trang-thai', 'value'),
     State('device-pump-edit-id', 'data'),
     State('session-store', 'data')],
    prevent_initial_call=True
)
def device_save_pump(n_clicks, ten, mo_ta, che_do, trang_thai, pump_id, session_data):
    if not ten or n_clicks is None:
        raise PreventUpdate
    
    token = None
    if session_data and isinstance(session_data, dict):
        token = session_data.get('token')
    
    try:
        payload = {'ten_may_bom': ten, 'mo_ta': mo_ta, 'che_do': che_do, 'trang_thai': trang_thai}
        if pump_id:
            update_pump(pump_id, payload, token=token)
        else:
            create_pump(payload, token=token)
        
        return list_pumps(limit=1, offset=0, token=token)
    except Exception:
        raise PreventUpdate


@callback(
    Output('device-confirm-delete-pump-modal', 'is_open'),
    [Input({'type': 'device-delete-pump', 'index': dash.ALL}, 'n_clicks'),
     Input('device-confirm-delete-pump', 'n_clicks'),
     Input('device-confirm-cancel-pump', 'n_clicks')],
    State('device-confirm-delete-pump-modal', 'is_open'),
    prevent_initial_call=True
)
def device_toggle_delete_pump_modal(delete_clicks, confirm_click, cancel_click, is_open):
    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate
    
    trig_id = ctx.triggered[0]['prop_id'].split('.')[0]
    trig_value = ctx.triggered[0]['value']
    
    # Nếu chưa được nhấp (n_clicks=0 hoặc None), không xử lý
    if trig_value is None or trig_value == 0:
        raise PreventUpdate
    
    # Nếu nhấn xác nhận xóa hoặc hủy, đóng modal
    if 'device-confirm-delete-pump' in trig_id or 'device-confirm-cancel-pump' in trig_id:
        return False
    
    # Nếu nhấn nút xóa, mở modal
    if 'device-delete-pump' in trig_id:
        return True
    
    raise PreventUpdate


@callback(
    Output('device-pump-delete-id', 'data'),
    Input({'type': 'device-delete-pump', 'index': dash.ALL}, 'n_clicks'),
    prevent_initial_call=True
)
def device_store_delete_pump_id(delete_clicks):
    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate
    
    trig_id = ctx.triggered[0]['prop_id'].split('.')[0]
    try:
        import json
        obj = json.loads(trig_id)
        return obj.get('index')
    except Exception:
        raise PreventUpdate


@callback(
    [Output('device-pump-data-store', 'data', allow_duplicate=True),
     Output('device-confirm-delete-pump-modal', 'is_open', allow_duplicate=True)],
    Input('device-confirm-delete-pump', 'n_clicks'),
    State('device-pump-delete-id', 'data'),
    State('session-store', 'data'),
    prevent_initial_call=True
)
def device_confirm_delete_pump(n_clicks, pump_id, session_data):
    if not pump_id or n_clicks is None:
        raise PreventUpdate
    
    token = None
    if session_data and isinstance(session_data, dict):
        token = session_data.get('token')
    
    try:
        delete_pump(pump_id, token=token)
        pump_data = list_pumps(limit=1, offset=0, token=token)
        return pump_data, False
    except Exception:
        raise PreventUpdate


# ============ SENSOR FORM CALLBACKS ============

@callback(
    Output('device-sensor-types-store', 'data'),
    Input('device-sensor-modal', 'is_open'),
    State('session-store', 'data')
)
def device_load_sensor_types(is_open, session_data):
    if not is_open:
        raise PreventUpdate
    
    token = None
    if session_data and isinstance(session_data, dict):
        token = session_data.get('token')
    
    try:
        types = get_sensor_types(token=token)
        return types
    except Exception:
        return {}


@callback(
    [Output('device-sensor-loai', 'options')],
    Input('device-sensor-types-store', 'data')
)
def device_populate_sensor_type_options(types_data):
    if not types_data or not isinstance(types_data, dict):
        return [[]]
    
    items = types_data.get('data', [])
    opts = []
    for it in items:
        ma = it.get('ma_loai_cam_bien')
        ten = it.get('ten_loai_cam_bien')
        if ma is None:
            continue
        opts.append({'label': str(ten or ma), 'value': ma})
    
    return [opts]


@callback(
    Output('device-sensor-pumps-store', 'data'),
    Input('device-sensor-modal', 'is_open'),
    State('session-store', 'data')
)
def device_load_sensor_pumps(is_open, session_data):
    if not is_open:
        raise PreventUpdate
    
    token = None
    if session_data and isinstance(session_data, dict):
        token = session_data.get('token')
    
    try:
        pumps = list_pumps(limit=100, offset=0, token=token)
        return pumps
    except Exception:
        return {}


@callback(
    Output('device-sensor-ma-may-bom', 'options'),
    Input('device-sensor-pumps-store', 'data')
)
def device_populate_sensor_pump_options(pumps_data):
    if not pumps_data or not isinstance(pumps_data, dict):
        return []
    
    pumps = pumps_data.get('data', [])
    opts = []
    for pump in pumps:
        ma = pump.get('ma_may_bom')
        ten = pump.get('ten_may_bom')
        if ma is None:
            continue
        opts.append({'label': str(ten or ma), 'value': ma})
    
    return opts


@callback(
    Output('device-sensor-modal', 'is_open'),
    [Input('device-open-add-sensor', 'n_clicks'),
     Input('device-sensor-save', 'n_clicks'),
     Input('device-sensor-cancel', 'n_clicks'),
     Input({'type': 'device-edit-sensor', 'index': dash.ALL}, 'n_clicks')],
    State('device-sensor-modal', 'is_open'),
    prevent_initial_call=True
)
def device_toggle_sensor_modal(add_click, save_click, cancel_click, edit_clicks, is_open):
    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate
    
    trig_id = ctx.triggered[0]['prop_id'].split('.')[0]
    trig_value = ctx.triggered[0]['value']
    
    # Nếu chưa được nhấp (n_clicks=0 hoặc None), không xử lý
    if trig_value is None or trig_value == 0:
        raise PreventUpdate
    
    # Không mở modal khi xóa
    if 'device-delete-sensor' in trig_id:
        raise PreventUpdate
    
    # Nếu lưu thành công, đóng modal
    if 'device-sensor-save' in trig_id:
        return False
    
    # Nếu hủy, đóng modal
    if 'device-sensor-cancel' in trig_id:
        return False
    
    # Nếu mở thêm hoặc sửa, mở modal
    return True


@callback(
    [Output('device-sensor-modal-title', 'children'),
     Output('device-sensor-edit-id', 'data'),
     Output('device-sensor-ten', 'value'),
     Output('device-sensor-mo-ta', 'value'),
     Output('device-sensor-ma-may-bom', 'value'),
     Output('device-sensor-ngay-lap-dat', 'value'),
     Output('device-sensor-loai', 'value')],
    [Input('device-open-add-sensor', 'n_clicks'),
     Input({'type': 'device-edit-sensor', 'index': dash.ALL}, 'n_clicks')],
    State('device-sensor-data-store', 'data'),
    prevent_initial_call=True
)
def device_load_sensor_form(add_click, edit_clicks, sensor_data):
    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate
    
    trig_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if 'device-open-add-sensor' in trig_id:
        return 'Thêm cảm biến mới', None, '', '', None, str(datetime.date.today()), None
    
    try:
        import json
        obj = json.loads(trig_id)
        sensor_id = obj.get('index')
        
        if sensor_data and isinstance(sensor_data, dict):
            sensors = sensor_data.get('data', [])
            for sensor in sensors:
                if sensor.get('ma_cam_bien') == sensor_id:
                    return f"Sửa cảm biến: {sensor.get('ten_cam_bien')}", sensor_id, \
                           sensor.get('ten_cam_bien', ''), sensor.get('mo_ta', ''), \
                           sensor.get('ma_may_bom'), sensor.get('ngay_lap_dat', str(datetime.date.today())), \
                           sensor.get('ma_loai_cam_bien')
    except Exception:
        pass
    
    raise PreventUpdate


@callback(
    Output('device-sensor-data-store', 'data', allow_duplicate=True),
    Input('device-sensor-save', 'n_clicks'),
    [State('device-sensor-ten', 'value'),
     State('device-sensor-mo-ta', 'value'),
     State('device-sensor-ma-may-bom', 'value'),
     State('device-sensor-ngay-lap-dat', 'value'),
     State('device-sensor-loai', 'value'),
     State('device-sensor-edit-id', 'data'),
     State('session-store', 'data')],
    prevent_initial_call=True
)
def device_save_sensor(n_clicks, ten, mo_ta, ma_may_bom, ngay_lap_dat, ma_loai, sensor_id, session_data):
    if not ten or not ma_loai or n_clicks is None:
        raise PreventUpdate
    
    token = None
    if session_data and isinstance(session_data, dict):
        token = session_data.get('token')
    
    try:
        payload = {
            'ten_cam_bien': ten,
            'mo_ta': mo_ta,
            'ma_may_bom': ma_may_bom,
            'ngay_lap_dat': ngay_lap_dat,
            'ma_loai_cam_bien': ma_loai
        }
        
        if sensor_id:
            update_sensor(sensor_id, payload, token=token)
        else:
            create_sensor(payload, token=token)
        
        return list_sensors(limit=100, offset=0, token=token)
    except Exception:
        raise PreventUpdate


@callback(
    Output('device-confirm-delete-sensor-modal', 'is_open'),
    [Input({'type': 'device-delete-sensor', 'index': dash.ALL}, 'n_clicks'),
     Input('device-confirm-delete-sensor', 'n_clicks'),
     Input('device-confirm-cancel-sensor', 'n_clicks')],
    State('device-confirm-delete-sensor-modal', 'is_open'),
    prevent_initial_call=True
)
def device_toggle_delete_sensor_modal(delete_clicks, confirm_click, cancel_click, is_open):
    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate
    
    trig_id = ctx.triggered[0]['prop_id'].split('.')[0]
    trig_value = ctx.triggered[0]['value']
    
    # Nếu chưa được nhấp (n_clicks=0 hoặc None), không xử lý
    if trig_value is None or trig_value == 0:
        raise PreventUpdate
    
    # Nếu nhấn xác nhận xóa hoặc hủy, đóng modal
    if 'device-confirm-delete-sensor' in trig_id or 'device-confirm-cancel-sensor' in trig_id:
        return False
    
    # Nếu nhấn nút xóa, mở modal
    if 'device-delete-sensor' in trig_id:
        return True
    
    raise PreventUpdate


@callback(
    Output('device-sensor-delete-id', 'data'),
    Input({'type': 'device-delete-sensor', 'index': dash.ALL}, 'n_clicks'),
    prevent_initial_call=True
)
def device_store_delete_sensor_id(delete_clicks):
    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate
    
    trig_id = ctx.triggered[0]['prop_id'].split('.')[0]
    try:
        import json
        obj = json.loads(trig_id)
        return obj.get('index')
    except Exception:
        raise PreventUpdate


@callback(
    [Output('device-sensor-data-store', 'data', allow_duplicate=True),
     Output('device-confirm-delete-sensor-modal', 'is_open', allow_duplicate=True)],
    Input('device-confirm-delete-sensor', 'n_clicks'),
    State('device-sensor-delete-id', 'data'),
    State('session-store', 'data'),
    prevent_initial_call=True
)
def device_confirm_delete_sensor(n_clicks, sensor_id, session_data):
    if not sensor_id or n_clicks is None:
        raise PreventUpdate
    
    token = None
    if session_data and isinstance(session_data, dict):
        token = session_data.get('token')
    
    try:
        delete_sensor(sensor_id, token=token)
        sensor_data = list_sensors(limit=100, offset=0, token=token)
        return sensor_data, False
    except Exception:
        raise PreventUpdate

