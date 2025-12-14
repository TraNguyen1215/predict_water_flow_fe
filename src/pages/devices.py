from dash import html, dcc, callback, Input, Output, State, ALL, ctx
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
from components.navbar import create_navbar
from components.topbar import TopBar
from api.sensor import list_sensors, create_sensor, update_sensor, delete_sensor, get_sensor, get_sensor_types
from api.pump import list_pumps, create_pump, update_pump, delete_pump, get_pump
from api.sensor_data import get_data_by_date, get_data_by_pump
from api.memory_pump import get_pump_memory_logs
import dash
from datetime import datetime, timedelta
import pandas as pd
import plotly.graph_objects as go


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


def format_time_with_seconds(time_str):
    """Format time string to HH:MM:SS format in Asia/Bangkok timezone."""
    if not time_str:
        return "N/A"
    try:
        from datetime import timezone as tz_module
        dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
        target_tz = tz_module(timedelta(hours=7))
        dt_local = dt.astimezone(target_tz)
        return dt_local.strftime('%H:%M:%S')
    except:
        return time_str

def calculate_duration(start_time, end_time):
    """Calculate duration between two timestamps and return formatted string."""
    if not start_time or not end_time:
        return "N/A"
    try:
        start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
        duration = end_dt - start_dt
        
        # Calculate hours, minutes, seconds
        total_seconds = int(duration.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"
    except Exception as e:
        print(f"Error calculating duration: {e}")
        return "N/A"

def create_sensor_card(sensor, pump_name="", index=0):
    """Tạo card hiển thị dữ liệu cảm biến"""
    return dbc.Col([
        html.Div([
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
            ], className="sensor-card h-100 shadow-sm")
        ], id={'type': 'sensor-card', 'index': index}, n_clicks=0, style={'cursor': 'pointer'})
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
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.Div([
                            html.H6("Lịch sử hoạt động", className="mb-0"),
                            dbc.Button(
                                [html.I(className='fas fa-eye me-1'), 'Xem tất cả'],
                                id='device-pump-history-view-all-btn',
                                color='link',
                                outline=False,
                                size='sm',
                                style={'padding': '0', 'font-size': '0.875rem'}
                            )
                        ], className="d-flex justify-content-between align-items-center")
                    ]),
                    dbc.CardBody(id="device-pump-history-body", children=[
                        html.Small('Đang tải...', className='text-muted')
                    ])
                ])
            ], md=4, className="mb-4")
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
                html.Div([
                    html.H5("Biểu Đồ Chi Tiết", className="section-title mb-0"),
                    dbc.RadioItems(
                        id='chart-time-filter',
                        options=[
                            {'label': '24 Giờ', 'value': '24h'},
                            {'label': '7 Ngày', 'value': '7d'},
                            {'label': '1 Tháng', 'value': '30d'},
                        ],
                        value='24h',
                        inline=True,
                        className="ms-3"
                    )
                ], className="d-flex align-items-center mb-3")
            ], md=12)
        ]),

        dbc.Row([
            dbc.Col([
                dcc.Graph(id='device-sensor-detail-chart')
            ], md=12, className="mb-4")
        ]),

        # Data stores
        dcc.Store(id='device-pump-data-store'),
        dcc.Store(id='device-sensor-data-store'),
        dcc.Store(id='selected-sensor-store', data=None),
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
                    dbc.Label('Giới hạn thời gian', className='mt-2'),
                    dcc.Dropdown(id='device-pump-gioi-han-thoi-gian', options=[{'label': 'Tắt', 'value': False}, {'label': 'Bật', 'value': True}], value=False, clearable=False),
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
                    dbc.Input(id='device-sensor-ngay-lap-dat', type='date', value=datetime.now().strftime('%Y-%m-%d')),
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
        ], id='device-confirm-delete-sensor-modal', is_open=False, centered=True),

        # Modal for Pump History
        dbc.Modal([
            dbc.ModalHeader(
                html.H5("Lịch sử hoạt động máy bơm", className="mb-0"),
                close_button=True
            ),
            dbc.ModalBody([
                html.Div(id='device-pump-history-modal-content', children=[
                    html.P("Đang tải...", className="text-muted text-center")
                ], style={
                    'max-height': '600px',
                    'overflow-y': 'auto',
                    'padding-right': '10px'
                })
            ]),
            dbc.ModalFooter([
                dbc.Button("Đóng", id='device-pump-history-modal-close', className="ms-auto")
            ])
        ], id='device-pump-history-modal', size='lg', centered=True)

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
                    html.P("Giới hạn thời gian", className="text-muted small mb-1"),
                    html.H6("Bật" if pump.get('gioi_han_thoi_gian', False) else "Tắt", className="mb-0")
                ], xs=6, sm=6),
                dbc.Col([
                    html.P("Ngày lắp đặt", className="text-muted small mb-1"),
                    html.H6(format_datetime(pump.get('thoi_gian_tao')), className="mb-0")
                ], xs=6, sm=6),
            ]),

            html.Div([
                dbc.Button([html.I(className="fas fa-edit me-2"), "Chỉnh sửa"], 
                           id='device-pump-edit-btn', 
                           n_clicks=0,
                           color="light", 
                           className="ms-auto text-primary border-0")
            ], className="d-flex mt-3")
        ])
    ], className="pump-main-card")


# ============ PUMP HISTORY CALLBACK ============

@callback(
    Output('device-pump-history-body', 'children'),
    [Input('device-pump-data-store', 'data')],
    State('session-store', 'data')
)
def device_render_pump_history(pump_data, session):
    if not pump_data or not isinstance(pump_data, dict):
        return html.P("Không có dữ liệu", className="text-muted")
    
    pumps = pump_data.get('data', [])
    if not pumps:
        return html.P("Không có dữ liệu", className="text-muted")
    
    pump = pumps[0]
    pump_id = pump.get('ma_may_bom')
    token = session.get('token') if session else None
    
    try:
        # Collect logs from last 5 days
        all_logs = []
        for i in range(5):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            logs = get_pump_memory_logs(pump_id, limit=100, offset=0, token=token, date=date)
            
            if isinstance(logs, dict):
                data = logs.get('data', [])
            elif isinstance(logs, list):
                data = logs
            else:
                data = []
            
            all_logs.extend(data)
        
        # Sort by time, most recent first, and take last 3
        if all_logs:
            try:
                all_logs = sorted(all_logs, key=lambda x: x.get('thoi_gian_tao', ''), reverse=True)
            except:
                pass
            all_logs = all_logs[:3]
        
        if not all_logs:
            history_content = [html.Small('Không có hoạt động gần đây', className='text-muted')]
        else:
            # Sort by start time, most recent first, and take last 3
            all_logs = sorted(all_logs, key=lambda x: x.get('thoi_gian_bat', ''), reverse=True)[:3]
            
            history_items = []
            for log in all_logs:
                thoi_gian_bat = log.get('thoi_gian_bat', '')
                thoi_gian_tat = log.get('thoi_gian_tat', '')
                
                # Format times
                bat_time = ''
                tat_time = ''
                
                if thoi_gian_bat:
                    try:
                        bat_dt = datetime.fromisoformat(thoi_gian_bat.replace('Z', '+00:00'))
                        bat_time = bat_dt.strftime('%H:%M')
                    except:
                        bat_time = thoi_gian_bat
                
                if thoi_gian_tat:
                    try:
                        tat_dt = datetime.fromisoformat(thoi_gian_tat.replace('Z', '+00:00'))
                        tat_time = tat_dt.strftime('%H:%M')
                    except:
                        tat_time = thoi_gian_tat
                
                # Display time range
                time_range = f"Bắt đầu {bat_time}" if bat_time else "Bắt đầu N/A"
                if tat_time:
                    time_range += f" - Kết thúc {tat_time}"
                
                history_items.append(
                    html.Small(time_range, className='text-muted', style={'display': 'block', 'font-size': '0.85rem', 'margin-bottom': '8px'})
                )
            history_content = history_items

    except Exception as e:
        print(f"Error fetching pump history: {e}")
        history_content = [html.Small('Không thể tải lịch sử', className='text-muted')]

    return html.Div(history_content)


# ============ SENSOR CHART CALLBACK ============

@callback(
    Output('selected-sensor-store', 'data'),
    [Input({'type': 'sensor-card', 'index': ALL}, 'n_clicks'),
     Input('device-sensor-data-store', 'data')],
    State('selected-sensor-store', 'data')
)
def update_selected_sensor(n_clicks, sensor_data, current_selection):
    # Check if data exists
    if not sensor_data or 'data' not in sensor_data or not sensor_data['data']:
        return None
        
    sensors = sensor_data['data']
    
    # Check what triggered
    ctx_triggered = ctx.triggered
    
    # If triggered by data load or initial call
    if not ctx_triggered or (ctx_triggered and 'device-sensor-data-store' in ctx_triggered[0]['prop_id']):
        # If we already have a selection, keep it
        if current_selection:
            return dash.no_update
        
        # Select first sensor by default
        if sensors:
            first_sensor = sensors[0]
            return {
                'ma_cam_bien': first_sensor.get('ma_cam_bien'),
                'ten_loai_cam_bien': first_sensor.get('ten_loai_cam_bien'),
                'ma_may_bom': first_sensor.get('ma_may_bom'),
                'ten_cam_bien': first_sensor.get('ten_cam_bien')
            }
        return None

    # If triggered by card click
    if ctx_triggered and 'sensor-card' in ctx_triggered[0]['prop_id']:
        try:
            import json
            prop_id = ctx_triggered[0]['prop_id']
            # prop_id looks like '{"index":0,"type":"sensor-card"}.n_clicks'
            id_str = prop_id.split('.')[0]
            id_dict = json.loads(id_str)
            index = id_dict['index']
            
            if index < len(sensors):
                selected_sensor = sensors[index]
                return {
                    'ma_cam_bien': selected_sensor.get('ma_cam_bien'),
                    'ten_loai_cam_bien': selected_sensor.get('ten_loai_cam_bien'),
                    'ma_may_bom': selected_sensor.get('ma_may_bom'),
                    'ten_cam_bien': selected_sensor.get('ten_cam_bien')
                }
        except Exception as e:
            print(f"Error processing click: {e}")
            
    return dash.no_update

@callback(
    Output('device-sensor-detail-chart', 'figure'),
    [Input('device-pump-data-store', 'data'),
     Input('chart-time-filter', 'value')],
    State('session-store', 'data')
)
def device_render_sensor_detail_chart(pump_data, time_filter, session_data):
    if not pump_data or not isinstance(pump_data, dict) or not pump_data.get('data'):
        return {
            'data': [],
            'layout': go.Layout(
                title="Đang tải dữ liệu...",
                xaxis={'title': 'Thời gian'},
                yaxis={'title': 'Giá trị'},
                template='plotly_white'
            )
        }
    
    token = session_data.get('token') if session_data else None
    pump = pump_data['data'][0]
    pump_id = pump.get('ma_may_bom')
    
    # Fetch data based on time filter
    end_date = datetime.now()
    
    if time_filter == '24h':
        days_to_fetch = 1
        start_date = end_date - timedelta(days=1)
    elif time_filter == '7d':
        days_to_fetch = 7
        start_date = end_date - timedelta(days=7)
    elif time_filter == '30d':
        days_to_fetch = 30
        start_date = end_date - timedelta(days=30)
    else:
        days_to_fetch = 1
        start_date = end_date - timedelta(days=1)
        
    all_data = []
    
    # Fetch data day by day
    for i in range(days_to_fetch + 1):
        current_date = end_date - timedelta(days=i)
        date_str = current_date.strftime('%Y-%m-%d')
        
        if current_date < start_date - timedelta(days=1):
            break
            
        resp = get_data_by_date(date_str, token=token, ma_may_bom=pump_id, limit=1000)
        if isinstance(resp, dict):
            day_data = resp.get('data', [])
        else:
            day_data = resp
            
        if isinstance(day_data, list):
            all_data.extend(day_data)
            
    if not all_data:
        return {
            'data': [],
            'layout': go.Layout(
                title=f"Không có dữ liệu",
                xaxis={'title': 'Thời gian'},
                yaxis={'title': 'Giá trị'},
                template='plotly_white'
            )
        }
        
    # Convert to DataFrame
    df = pd.DataFrame(all_data)
    
    # Ensure timestamp column exists
    if 'thoi_gian_tao' not in df.columns:
        return {
            'data': [],
            'layout': go.Layout(title="Lỗi dữ liệu: Thiếu thời gian")
        }
        
    # Convert to datetime and handle timezone
    df['thoi_gian_tao'] = pd.to_datetime(df['thoi_gian_tao'], utc=True)
    
    try:
        df['thoi_gian_tao'] = df['thoi_gian_tao'].dt.tz_convert('Asia/Bangkok')
    except Exception as e:
        print(f"Error converting timezone: {e}")

    # Filter by time range exactly
    from datetime import timezone
    tz_bangkok = timezone(timedelta(hours=7))
    cutoff_time = datetime.now(tz_bangkok)
    
    if time_filter == '24h':
        cutoff_time = cutoff_time - timedelta(hours=24)
    elif time_filter == '7d':
        cutoff_time = cutoff_time - timedelta(days=7)
    elif time_filter == '30d':
        cutoff_time = cutoff_time - timedelta(days=30)
        
    df = df[df['thoi_gian_tao'] >= cutoff_time]
    
    if df.empty:
         return {
            'data': [],
            'layout': go.Layout(
                title=f"Không có dữ liệu trong khoảng thời gian này",
                xaxis={'title': 'Thời gian'},
                yaxis={'title': 'Giá trị'},
                template='plotly_white'
            )
        }

    df = df.sort_values('thoi_gian_tao')
    
    # Create Chart with multiple traces
    fig = go.Figure()
    
    # Add traces for each metric if available
    if 'nhiet_do' in df.columns:
        fig.add_trace(go.Scatter(
            x=df['thoi_gian_tao'],
            y=df['nhiet_do'],
            mode='lines',
            name='Nhiệt độ (°C)',
            line=dict(color='#dc3545', width=2)
        ))
        
    if 'do_am' in df.columns:
        fig.add_trace(go.Scatter(
            x=df['thoi_gian_tao'],
            y=df['do_am'],
            mode='lines',
            name='Độ ẩm không khí (%)',
            line=dict(color='#0d6efd', width=2)
        ))
        
    if 'do_am_dat' in df.columns:
        fig.add_trace(go.Scatter(
            x=df['thoi_gian_tao'],
            y=df['do_am_dat'],
            mode='lines',
            name='Độ ẩm đất (%)',
            line=dict(color='#198754', width=2)
        ))
        
    if 'luu_luong_nuoc' in df.columns:
        fig.add_trace(go.Scatter(
            x=df['thoi_gian_tao'],
            y=df['luu_luong_nuoc'],
            mode='lines',
            name='Lưu lượng (L/phút)',
            line=dict(color='#0dcaf0', width=2),
            visible='legendonly' # Hide by default as scale might be different
        ))
    
    fig.update_layout(
        title=f"Biểu đồ tổng hợp ({time_filter})",
        xaxis_title="Thời gian",
        yaxis_title="Giá trị",
        hovermode='x unified',
        template='plotly_white',
        margin=dict(l=50, r=20, t=50, b=50),
        height=450,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
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
    for idx, s in enumerate(sensors[:4]):
        pump_name = pump_map.get(s.get('ma_may_bom'))
        sensor_cards.append(create_sensor_card(s, pump_name, index=idx))
    
    # Nếu có ít hơn 4 cảm biến, hiển thị thông báo
    if len(sensors) < 4:
        alert = dbc.Alert([
            html.I(className="fas fa-exclamation-triangle me-2"),
            f"Có {len(sensors)}/4 cảm biến."
        ], color="warning")
        return sensor_cards, alert
    
    return sensor_cards, html.Div()


# ============ PUMP FORM CALLBACKS ============

@callback(
    [Output('device-pump-modal', 'is_open'),
     Output('device-pump-modal-title', 'children'),
     Output('device-pump-ten', 'value'),
     Output('device-pump-mo-ta', 'value'),
     Output('device-pump-che-do', 'value'),
     Output('device-pump-trang-thai', 'value'),
     Output('device-pump-gioi-han-thoi-gian', 'value'),
     Output('device-pump-edit-id', 'data')],
    [Input('device-pump-edit-btn', 'n_clicks'),
     Input('device-pump-cancel', 'n_clicks'),
     Input('device-pump-save', 'n_clicks')],
    [State('device-pump-modal', 'is_open'),
     State('device-pump-data-store', 'data')],
    prevent_initial_call=True
)
def device_toggle_pump_modal(n_edit, n_cancel, n_save, is_open, pump_data):
    ctx_triggered = ctx.triggered_id
    
    if ctx_triggered == 'device-pump-edit-btn':
        if not n_edit:
            return is_open, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
            
        if not pump_data or not pump_data.get('data'):
            return True, "Chỉnh sửa máy bơm", "", "", 0, False, False, None
        
        pump = pump_data['data'][0]
        return True, "Chỉnh sửa máy bơm", pump.get('ten_may_bom'), pump.get('mo_ta'), pump.get('che_do'), pump.get('trang_thai'), pump.get('gioi_han_thoi_gian', False), pump.get('ma_may_bom')
        
    if ctx_triggered == 'device-pump-cancel' or ctx_triggered == 'device-pump-save':
        return False, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
        
    return is_open, "Chỉnh sửa máy bơm", "", "", 0, False, False, None


@callback(
    Output('device-refresh-interval', 'n_intervals', allow_duplicate=True),
    Input('device-pump-save', 'n_clicks'),
    State('device-pump-edit-id', 'data'),
    State('device-pump-ten', 'value'),
    State('device-pump-mo-ta', 'value'),
    State('device-pump-che-do', 'value'),
    State('device-pump-trang-thai', 'value'),
    State('device-pump-gioi-han-thoi-gian', 'value'),
    State('session-store', 'data'),
    State('device-refresh-interval', 'n_intervals'),
    prevent_initial_call=True
)
def device_save_pump(n_clicks, pump_id, name, desc, mode, status, time_limit, session_data, current_intervals):
    if not n_clicks:
        raise PreventUpdate
        
    token = session_data.get('token') if session_data else None
    
    data = {
        'ten_may_bom': name,
        'mo_ta': desc,
        'che_do': mode,
        'trang_thai': status,
        'gioi_han_thoi_gian': time_limit
    }
    
    try:
        if pump_id:
            update_pump(pump_id, data, token)
        
        # Close modal is handled by another callback? 
        # No, we need to close the modal too. 
        # But the toggle callback doesn't listen to save.
        # Let's update the toggle callback to listen to save as well?
        # Or just let the user close it? 
        # Better UX: Close on save.
        
        return (current_intervals or 0) + 1
    except Exception as e:
        print(f"Error updating pump: {e}")
        import traceback
        traceback.print_exc()
        
    return dash.no_update


# ============ HISTORY MODAL CALLBACKS ============

@callback(
    Output('device-pump-history-modal', 'is_open'),
    [
        Input('device-pump-history-view-all-btn', 'n_clicks'),
        Input('device-pump-history-modal-close', 'n_clicks'),
    ],
    [
        State('device-pump-history-modal', 'is_open')
    ]
)
def device_toggle_history_modal(n_clicks_view, n_clicks_close, is_open):
    if n_clicks_view or n_clicks_close:
        return not is_open
    return is_open

@callback(
    Output('device-pump-history-modal-content', 'children'),
    [
        Input('device-pump-history-modal', 'is_open'),
    ],
    [
        State('device-pump-data-store', 'data'),
        State('session-store', 'data')
    ]
)
def device_update_history_modal(is_open, pump_data, session):
    if not is_open:
        raise PreventUpdate
    
    if not pump_data or not isinstance(pump_data, dict):
        return [html.P("Không có dữ liệu máy bơm", className="text-muted text-center")]
    
    pumps = pump_data.get('data', [])
    if not pumps:
        return [html.P("Không có dữ liệu máy bơm", className="text-muted text-center")]
    
    pump = pumps[0]
    pump_id = pump.get('ma_may_bom')
    token = session.get('token') if session else None
    
    try:
        # Fetch logs for last 7 days
        all_logs = []
        for i in range(7):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            logs = get_pump_memory_logs(pump_id, limit=100, offset=0, token=token, date=date)
            
            if isinstance(logs, dict):
                data = logs.get('data', [])
            elif isinstance(logs, list):
                data = logs
            else:
                data = []
            
            all_logs.extend(data)
            
        if not all_logs:
            return [html.P("Không có lịch sử hoạt động trong 7 ngày qua", className="text-muted text-center")]
            
        # Group logs by date
        logs_by_date = {}
        for log in all_logs:
            time_str = log.get('thoi_gian_bat') or log.get('thoi_gian_tat') or log.get('thoi_gian_tao', '')
            if time_str:
                # Extract date from timestamp (YYYY-MM-DD)
                date_part = time_str.split('T')[0] if 'T' in time_str else time_str[:10]
                if date_part not in logs_by_date:
                    logs_by_date[date_part] = []
                logs_by_date[date_part].append(log)
        
        # Sort dates in descending order (newest first)
        sorted_dates = sorted(logs_by_date.keys(), reverse=True)
        
        # Create timeline view
        timeline_items = []
        
        for date_key in sorted_dates:
            logs_for_date = logs_by_date[date_key]
            # Sort logs by thoi_gian_bat (oldest first), then reverse to show newest first
            logs_for_date = sorted(logs_for_date, key=lambda x: x.get('thoi_gian_bat') or x.get('thoi_gian_tat') or x.get('thoi_gian_tao', ''), reverse=True)
            
            if not logs_for_date:
                continue
            
            # Parse and format date
            try:
                date_obj = datetime.strptime(date_key, '%Y-%m-%d')
                # Format as "Thứ X, DD/MM/YYYY"
                day_of_week = ['Thứ Hai', 'Thứ Ba', 'Thứ Tư', 'Thứ Năm', 'Thứ Sáu', 'Thứ Bảy', 'Chủ Nhật']
                weekday = day_of_week[date_obj.weekday()]
                formatted_date = f"{weekday}, {date_obj.strftime('%d/%m/%Y')}"
            except:
                formatted_date = date_key
            
            # Create timeline section for this date
            total_logs = len(logs_for_date)
            date_section = html.Div([
                # Date header
                html.Div([
                    html.Span(formatted_date, style={
                        'font-weight': '600',
                        'color': '#333',
                        'font-size': '0.95rem',
                        'padding': '8px 0',
                        'border-bottom': '2px solid #e9ecef',
                        'width': '100%'
                    })
                ], style={'margin': '15px 0 10px 0'}),
                
                # List of events for this date
                html.Div([
                    *[
                        html.Div([
                            html.Div([
                                html.Span(f"Lần {total_logs - idx}: ", style={'font-weight': '600', 'color': '#333'}),
                                html.Span(' Bắt đầu:  ', style={'color': '#666'}),
                                html.Span(
                                    format_time_with_seconds(log.get('thoi_gian_bat', '')),
                                    style={'color': '#28a745', 'font-weight': '500'}
                                ),
                                html.Span(' - Kết thúc: ', style={'color': '#666', 'margin': '0 4px'}),
                                html.Span(
                                    format_time_with_seconds(log.get('thoi_gian_tat', '')) if log.get('thoi_gian_tat') else '(Chưa tắt)',
                                    style={'color': '#dc3545', 'font-weight': '500'}
                                ),
                            ], style={'display': 'flex', 'align-items': 'center', 'flex-wrap': 'wrap'}),
                            # Duration row
                            html.Div([
                                html.Span(' Tổng thời gian: ', style={'color': '#666', 'font-size': '0.85rem'}),
                                html.Span(
                                    calculate_duration(log.get('thoi_gian_bat', ''), log.get('thoi_gian_tat', '')),
                                    style={'color': '#007bff', 'font-weight': '500', 'font-size': '0.85rem'}
                                ),
                            ], style={'display': 'flex', 'align-items': 'center', 'margin-top': '4px'})
                        ], style={'padding': '10px 0', 'border-bottom': '1px solid #f0f0f0'})
                        for idx, log in enumerate(logs_for_date)
                    ]
                ])
            ])
            
            timeline_items.append(date_section)
        
        return timeline_items
        
    except Exception as e:
        print(f"Error fetching pump history modal: {e}")
        import traceback
        traceback.print_exc()
        return [html.P("Lỗi tải dữ liệu", className="text-danger text-center")]

# Add callback to close modal on save success? 
# For simplicity, let's add 'device-pump-save' to the toggle callback inputs.





# ============ SENSOR FORM CALLBACKS ============
# Callbacks for sensor management (add/edit/delete) have been removed as per requirements.


