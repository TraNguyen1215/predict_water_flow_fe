from dash import html, dcc, callback, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from components.navbar import create_navbar
from dash.exceptions import PreventUpdate
import requests
import json
from api.sensor_data import get_data_by_date
from api.pump import list_pumps, get_pump, update_pump
from api.sensor import list_sensors
from api.user import get_user, list_users
from api.memory_pump import get_pump_memory_logs
import dash

def create_empty_dataframe():
    return pd.DataFrame({
        'ma_du_lieu': [],
        'ma_may_bom': [],
        'ma_nguoi_dung': [],
        'ngay': [],
        'luu_luong_nuoc': [],
        'do_am_dat': [],
        'nhiet_do': [],
        'do_am': [],
        'mua': [],
        'so_xung': [],
        'tong_the_tich': [],
        'thoi_gian_tao': [],
        'ghi_chu': []
    })

def format_display_time(iso_ts: str) -> str:
    if not iso_ts:
        return ''
    try:
        from datetime import timezone as tz_module
        dt = datetime.fromisoformat(iso_ts)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=tz_module.utc)
        target_tz = tz_module(timedelta(hours=7))
        dt_local = dt.astimezone(target_tz)
        return dt_local.strftime('%H:%M %d/%m/%Y')
    except Exception:
        return iso_ts

def fetch_sensor_data(token=None, date_str=None):
    try:
        if date_str is None:
            date_str = datetime.now().strftime('%Y-%m-%d')
        response_data = get_data_by_date(date_str, token)

        if isinstance(response_data, dict) and 'data' in response_data:
            data = response_data['data']
        else:
            data = response_data
        
        if not data or not isinstance(data, list):
            return create_empty_dataframe()
            
        df = pd.DataFrame.from_records(data)
        
        required_columns = ['thoi_gian_tao', 'luu_luong_nuoc', 'do_am_dat', 'nhiet_do', 'do_am']
        for col in required_columns:
            if col not in df.columns:
                print(f"Missing required column: {col}")
                return create_empty_dataframe()
        
        df['thoi_gian_tao'] = pd.to_datetime(df['thoi_gian_tao'], errors='coerce')
        try:
            if df['thoi_gian_tao'].dt.tz is None:
                df['thoi_gian_tao'] = df['thoi_gian_tao'].dt.tz_localize('Asia/Bangkok')
            else:
                df['thoi_gian_tao'] = df['thoi_gian_tao'].dt.tz_convert('Asia/Bangkok')
        except Exception:
            df['thoi_gian_tao'] = pd.to_datetime(df['thoi_gian_tao'])

        df['ngay'] = pd.to_datetime(df['ngay'], errors='coerce')
        
        df = df.rename(columns={
            'thoi_gian_tao': 'date',
            'luu_luong_nuoc': 'flow_rate',
            'do_am_dat': 'soil_moisture',
            'nhiet_do': 'temperature',
            'do_am': 'humidity',
            'mua': 'rain',
            'so_xung': 'pulse_count',
            'tong_the_tich': 'total_volume',
            'ghi_chu': 'notes'
        })
        
        df = df.sort_values('date')
        
        numeric_columns = ['flow_rate', 'soil_moisture', 'temperature', 'humidity']
        for col in numeric_columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        return df
    except Exception as e:
        print(f"Error fetching sensor data: {e}")
        return create_empty_dataframe()

def fetch_pump_list(token=None):
    try:
        response = list_pumps(limit=50, offset=0, token=token)
        if isinstance(response, dict):
            data = response.get('data')
            if isinstance(data, list):
                return data
            return []
        if isinstance(response, list):
            return response
        return []
    except Exception as e:
        print(f"Error fetching pump list: {e}")
        return []


def fetch_pump_latest_data(ma_may_bom, token=None):
    try:
        today = datetime.now().strftime('%Y-%m-%d')
        response = get_data_by_date(today, token=token, limit=1000, offset=0)

        if isinstance(response, dict):
            data = response.get('data')
        else:
            data = response

        if not isinstance(data, list):
            return None

        str_id = str(ma_may_bom) if ma_may_bom is not None else None
        filtered = [item for item in data if str(item.get('ma_may_bom')) == str_id]

        if not filtered:
            return None

        filtered.sort(key=lambda item: item.get('thoi_gian_tao', ''), reverse=True)
        return filtered[0]
    except Exception as e:
        print(f"Error fetching pump data: {e}")
        return None

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

empty_df = create_empty_dataframe()

layout = html.Div([
    create_navbar(is_authenticated=False),

    dbc.Container([
        # Top small stat cards (four across)
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.Div([
                                html.H6("Lưu Lượng Nước", className="stat-label"),
                                html.H3(id='flow-rate', children="N/A", className="stat-value"),
                                html.Small("L/phút", className="stat-desc text-muted")
                            ]),
                            html.I(className="fas fa-tint stat-icon text-info")
                        ], className="stat-card-content")
                    ])
                ], className="stat-card-wrapper")
            ], md=6, lg=3),

            dbc.Col([
                html.Div(
                    dbc.Card([
                        dbc.CardBody([
                            html.Div([
                                html.Div([
                                    html.H6("Độ Ẩm Đất", className="stat-label"),
                                    html.H3(id='soil-moisture', children="N/A", className="stat-value"),
                                    html.Small("%", className="stat-desc text-muted")
                                ]),
                                html.I(className="fas fa-seedling stat-icon text-success")
                            ], className="stat-card-content")
                        ])
                    ], className="stat-card-wrapper"),
                    id='soil-moisture-card',
                    style={'cursor': 'pointer', 'transition': 'transform 0.2s, box-shadow 0.2s'},
                    n_clicks=0
                )
            ], md=6, lg=3),

            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.Div([
                                html.H6("Độ Ẩm Không Khí", className="stat-label"),
                                html.H3(id='humidity', children="N/A", className="stat-value"),
                                html.Small("%", className="stat-desc text-muted")
                            ]),
                            html.I(className="fas fa-wind stat-icon text-primary")
                        ], className="stat-card-content")
                    ])
                ], className="stat-card-wrapper")
            ], md=6, lg=3),

            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.Div([
                                html.H6("Nhiệt Độ", className="stat-label"),
                                html.H3(id='temperature', children="N/A", className="stat-value"),
                                html.Small("°C", className="stat-desc text-muted")
                            ]),
                            html.I(className="fas fa-temperature-high stat-icon text-danger")
                        ], className="stat-card-content")
                    ])
                ], className="stat-card-wrapper")
            ], md=6, lg=3),
        ], className="mb-4"),

        # Main chart and pump control column
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H6([html.I(className="fas fa-chart-line me-2"), "Biểu Đồ Dòng Chảy & Dự Báo"], className="card-header-title")
                    ]),
                    dbc.CardBody([
                        dcc.Graph(id='selected-flow-rate-chart', config={'displayModeBar': False}),
                        html.Div([
                            html.Div([html.Small("Trung bình", className="small text-muted"), html.Strong(id='predicted-flow', children='N/A', className='ms-2')], className='me-4'),
                            html.Div([html.Small("Tối đa", className="small text-muted"), html.Strong(id='max-flow', children='N/A', className='ms-2')], className='me-4'),
                            html.Div([html.Small("Tối thiểu", className="small text-muted"), html.Strong(id='min-flow', children='N/A', className='ms-2')], className='me-4'),
                        ], className='d-flex justify-content-start align-items-center mt-3')
                    ])
                ], className='mb-4')
            ], lg=9),

            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H6([html.I(className="fas fa-cog me-2"), "Điều Khiển Máy Bơm"], className='card-header-title')),
                    dbc.CardBody([
                        # Status section with large power icon
                        html.Div([
                            html.Div(
                                html.I(className='fas fa-power-off', style={'font-size': '3rem', 'color': '#1abc9c'}),
                                className='text-center mb-3',
                                style={
                                    'width': '80px',
                                    'height': '80px',
                                    'background-color': 'rgba(26, 188, 156, 0.1)',
                                    'border-radius': '50%',
                                    'display': 'flex',
                                    'align-items': 'center',
                                    'justify-content': 'center',
                                    'margin': '0 auto 20px'
                                }
                            ),
                            html.H6('Trạng Thái', className='text-center mb-1', style={'font-size': '0.875rem', 'color': '#666'}),
                            html.Div(id='pump-control-status', children='Đang Hoạt Động', className='text-center text-success', style={'font-weight': '600', 'font-size': '1rem'}),
                        ], style={'padding-bottom': '20px', 'border-bottom': '1px solid #eee', 'margin-bottom': '20px'}),
                        
                        # Pump controls
                        html.Div([
                            # Pump toggle
                            html.Div([
                                html.Div([
                                    html.I(className='fas fa-water me-2', style={'color': '#3498db'}),
                                    html.Span('Máy Bơm', style={'flex': '1'})
                                ], style={'display': 'flex', 'align-items': 'center', 'justify-content': 'space-between', 'flex': '1'}),
                                html.Span(id='control-selected-pump-name', children='Bật/Tắt thủ công', style={'font-size': '0.875rem', 'color': '#666', 'margin-right': '20px'})
                            ], style={'display': 'flex', 'justify-content': 'space-between', 'align-items': 'center', 'margin-bottom': '15px'}),
                            html.Div([dbc.Checklist(id='pump-toggle', options=[{'label':'','value':1}], value=[], switch=True, style={})], 
                                    style={'display': 'flex', 'align-items': 'center', 'margin-left': 'auto', 'transform': 'scale(1.3)', 'transform-origin': 'right'}),
                        ], style={'display': 'flex', 'justify-content': 'space-between', 'align-items': 'center', 'margin-bottom': '20px'}),
                        
                        # Auto mode toggle
                        html.Div([
                            html.Div([
                                html.I(className='fas fa-bolt me-2', style={'color': '#f39c12'}),
                                html.Span('Chế Độ Tự Động', style={'flex': '1'}),
                                html.Span(id='auto-mode-desc', children='Điều khiển theo độ ẩm đất', style={'font-size': '0.875rem', 'color': '#666', 'margin-right': '20px'})
                            ], style={'display': 'flex', 'align-items': 'center', 'justify-content': 'space-between', 'flex': '1'}),
                            html.Div([dbc.Checklist(id='auto-mode-btn', options=[{'label':'','value':1}], value=[], switch=True, style={})],
                                    style={'display': 'flex', 'align-items': 'center', 'margin-left': 'auto', 'transform': 'scale(1.3)', 'transform-origin': 'right'})
                        ], style={'display': 'flex', 'justify-content': 'space-between', 'align-items': 'center'})
                    ])
                ], className='mb-4'),
                
                # History card
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.H6('Lịch sử hoạt động máy bơm', className='card-header-title', style={'margin': '0'}),
                            dbc.Button(
                                [html.I(className='fas fa-eye me-1'), 'Xem tất cả'],
                                id='pump-history-view-all-btn',
                                color='link',
                                outline=False,
                                size='sm',
                                style={'padding': '0', 'font-size': '0.875rem'}
                            )
                        ], style={'display': 'flex', 'justify-content': 'space-between', 'align-items': 'center', 'margin-bottom': '15px'}),
                        html.Div(id='pump-history', children=[
                            html.Small('Không có hoạt động gần đây', className='text-muted', style={'display': 'block'})
                        ])
                    ])
                ]),
                
                # Modal for pump history
                dbc.Modal([
                    dbc.ModalHeader(
                        html.H5("Lịch sử hoạt động máy bơm", className="mb-0"),
                        close_button=True
                    ),
                    dbc.ModalBody([
                        html.Div(id='pump-history-modal-content', children=[
                            html.P("Đang tải...", className="text-muted text-center")
                        ], style={
                            'max-height': '600px',
                            'overflow-y': 'auto',
                            'padding-right': '10px'
                        })
                    ]),
                    dbc.ModalFooter([
                        dbc.Button("Đóng", id='pump-history-modal-close', className="ms-auto")
                    ])
                ], id='pump-history-modal', size='lg', centered=True),
                
                # Modal for soil moisture chart
                dbc.Modal([
                    dbc.ModalHeader(
                        html.H5("Biểu Đồ Độ Ẩm Đất", className="mb-0"),
                        close_button=True
                    ),
                    dbc.ModalBody([
                        html.Div([
                            html.Label("Chọn Ngày:", className="fw-bold mb-2"),
                            dcc.DatePickerSingle(
                                id='soil-moisture-date-picker',
                                date=datetime.now().strftime('%Y-%m-%d'),
                                display_format='DD/MM/YYYY',
                                style={
                                    'width': '100%',
                                    'padding': '8px',
                                    'border': '1px solid #ddd',
                                    'border-radius': '4px',
                                    'fontSize': '14px'
                                }
                            )
                        ], className="mb-4"),
                        dcc.Graph(id='soil-moisture-chart', config={'displayModeBar': False}),
                        html.Div([
                            html.Div([html.Small("Trung bình", className="small text-muted"), html.Strong(id='soil-moisture-avg', children='N/A', className='ms-2')], className='me-4'),
                            html.Div([html.Small("Tối đa", className="small text-muted"), html.Strong(id='soil-moisture-max', children='N/A', className='ms-2')], className='me-4'),
                            html.Div([html.Small("Tối thiểu", className="small text-muted"), html.Strong(id='soil-moisture-min', children='N/A', className='ms-2')], className='me-4'),
                        ], className='d-flex justify-content-start align-items-center mt-3')
                    ], style={
                        'max-height': '600px',
                        'overflow-y': 'auto',
                        'padding-right': '10px'
                    }),
                    dbc.ModalFooter([
                        dbc.Button("Đóng", id='soil-moisture-modal-close', className="ms-auto")
                    ])
                ], id='soil-moisture-modal', size='lg', centered=True),
    
    dcc.Store(id='selected-history-date-store', data=None)
            ], lg=3)
        ])

    ], fluid=True, className='home-page-container px-4'),

    dcc.Interval(id='interval-component', interval=5*1000, n_intervals=0)
], className='page-container')

@callback(
    [
        Output('flow-rate', 'children'),
        Output('soil-moisture', 'children'),
        Output('humidity', 'children'),
        Output('temperature', 'children'),
        Output('predicted-flow', 'children'),
        Output('max-flow', 'children'),
        Output('min-flow', 'children'),
        Output('selected-flow-rate-chart', 'figure'),
    ],
    [
        Input('interval-component', 'n_intervals'),
        Input('url', 'pathname'),
        Input('session-store', 'modified_timestamp'),
    ],
    [
        State('session-store', 'data'),
        State('selected-pump-store', 'data')
    ]
)
def update_sensor_data(n, pathname, session_modified, session, selected_pump):
    """Update all sensor data and charts."""
    if pathname not in ('', '/', None):
        raise PreventUpdate
    
    token = None
    if session and isinstance(session, dict):
        token = session.get('token')
    
    try:
        df = fetch_sensor_data(token)
        
        if df.empty:
            raise PreventUpdate
        
        # Update stat cards
        flow_rate = f"{df['flow_rate'].iloc[-1]:.1f} L/phút" if not df.empty else "N/A"
        soil_moisture = f"{df['soil_moisture'].iloc[-1]:.0f}%" if not df.empty else "N/A"
        humidity = f"{df['humidity'].iloc[-1]:.0f}%" if not df.empty else "N/A"
        temperature = f"{df['temperature'].iloc[-1]:.1f}°C" if not df.empty else "N/A"
        
        # Calculate flow stats
        avg_flow = df['flow_rate'].mean() if not df.empty else 0
        predicted_flow = f"{avg_flow:.1f} L/phút" if not df.empty else "N/A"
        
        max_flow = f"{df['flow_rate'].max():.1f} L/phút" if not df.empty else "N/A"
        min_flow = f"{df['flow_rate'].min():.1f} L/phút" if not df.empty else "N/A"
        
        # Create flow rate chart
        flow_rate_figure = {
            'data': [
                go.Scatter(
                    x=df['date'],
                    y=df['flow_rate'],
                    mode='lines',
                    name='Lưu Lượng Thực Tế',
                    line=dict(color='#1f77b4', width=3),
                    fill='tozeroy',
                    fillcolor='rgba(31, 119, 180, 0.2)'
                ),
                go.Scatter(
                    x=df['date'],
                    y=df['flow_rate'].rolling(window=min(3, len(df)), center=True).mean(),
                    mode='lines',
                    name='Lưu Lượng Dự Đoán (Trung bình)',
                    line=dict(color='#2ca02c', width=2, dash='dash'),
                )
            ],
            'layout': go.Layout(
                xaxis={'title': 'Thời Gian', 'gridcolor': '#f0f0f0'},
                yaxis={'title': 'Lưu Lượng (L/phút)', 'gridcolor': '#f0f0f0'},
                hovermode='x unified',
                plot_bgcolor='white',
                paper_bgcolor='white',
                margin=dict(l=50, r=20, t=20, b=50),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )
        }
        
        return (
            flow_rate,
            soil_moisture,
            humidity,
            temperature,
            predicted_flow,
            max_flow,
            min_flow,
            flow_rate_figure
        )
    
    except Exception as e:
        print(f"Error updating sensor data: {e}")
        raise PreventUpdate

@callback(
    Output('selected-pump-store', 'data', allow_duplicate=True),
    [
        Input('initial-pump-select', 'n_intervals'),
        Input('url', 'pathname'),
        Input('session-store', 'modified_timestamp'),
    ],
    [
        State('session-store', 'data')
    ],
    prevent_initial_call=True
)
def auto_select_first_pump(n, pathname, session_modified, session):
    """Automatically select the first pump when the page loads."""
    if pathname not in ('', '/', None):
        raise PreventUpdate
    
    token = None
    if session and isinstance(session, dict):
        token = session.get('token')
    
    pumps = fetch_pump_list(token)
    if not pumps:
        raise PreventUpdate
    
    pumps = sorted(pumps, key=lambda x: (
        not x.get('trang_thai', False),  # True first for trang_thai
        x.get('ma_may_bom', ''),        # Then by ma_may_bom
        x.get('che_do', 0)              # Finally by che_do
    ))
    
    first_pump = pumps[0]
    return {
        'ma_may_bom': first_pump.get('ma_may_bom'),
        'ten_may_bom': first_pump.get('ten_may_bom', 'Máy Bơm Nước Chính')
    }

@callback(
    Output('selected-pump-store', 'data', allow_duplicate=True),
    [
        Input({'type': 'pump-card-btn', 'index': dash.ALL}, 'n_clicks'),
    ],
    prevent_initial_call=True
)
def select_pump(n_clicks):
    if not n_clicks:
        raise PreventUpdate
    if sum(n_clicks) == 0:
        raise PreventUpdate
    
    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate

    prop_id = ctx.triggered[0]['prop_id']
    try:
        import json
        id_dict = json.loads(prop_id.split('.')[0])
        pump_id = id_dict.get('index')
    except:
        raise PreventUpdate
    
    return {
        'ma_may_bom': pump_id,
        'ten_may_bom': pump_id
    }

@callback(
    [
        Output('control-selected-pump-name', 'children'),
        Output('pump-toggle', 'value'),
        Output('pump-toggle', 'disabled'),
        Output('pump-control-status', 'children'),
        Output('auto-mode-btn', 'value'),
        Output('auto-mode-desc', 'children'),
    ],
    [
        Input('selected-pump-store', 'data'),
        Input('interval-component', 'n_intervals'),
        Input('pump-toggle', 'value'),
        Input('auto-mode-btn', 'value'),
    ],
    [
        State('session-store', 'data'),
        State('url', 'pathname'),
    ],
    prevent_initial_call=False
)
def update_pump_control_panel(selected_pump, n_intervals, toggle_value, auto_mode_value, session, pathname):
    """Unified callback to refresh control panel state and handle pump toggling & mode changes.
    
    Distinguishes between triggers using dash.callback_context:
    - 'selected-pump-store.data': User selected a different pump or page reloaded
    - 'interval-component.n_intervals': Periodic refresh
    - 'pump-toggle.value': User toggled the pump switch (update trang_thai)
    - 'auto-mode-btn.value': User toggled the auto mode (update che_do)
    """
    ctx = dash.callback_context
    
    if pathname and not (pathname == '/' or pathname.startswith('/pump')):
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

    if not selected_pump or not selected_pump.get('ma_may_bom'):
        return ("Chưa chọn máy bơm", [], False, "Chưa chọn", [], "Chế độ không xác định")

    pump_id = selected_pump.get('ma_may_bom')
    token = session.get('token') if session else None

    try:
        pump_info = get_pump(pump_id, token)
        if not pump_info:
            pump_name = selected_pump.get('ten_may_bom', 'Máy Bơm Nước Chính')
            return (pump_name, [], False, "Không có dữ liệu", [], "Chế độ không xác định")

        pump_name = pump_info.get('ten_may_bom', 'Máy Bơm Nước Chính')
        status = pump_info.get('trang_thai', False)
        mode = pump_info.get('che_do', 0)  # 0 = manual (thủ công), 1 = auto (tự động)

        # Determine which trigger fired
        triggered_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None

        # Handle pump toggle (trang_thai update)
        if 'pump-toggle' in str(triggered_id):
            new_status = True if (isinstance(toggle_value, list) and 1 in toggle_value) else False
            payload = {
                'ten_may_bom': pump_info.get('ten_may_bom', ''),
                'mo_ta': pump_info.get('mo_ta', ''),
                'ma_iot_lk': pump_info.get('ma_iot_lk', ''),
                'che_do': int(mode),
                'trang_thai': new_status
            }
            success, message = update_pump(pump_id, payload, token=token)
            if not success:
                print(f"Lỗi cập nhật trạng thái máy bơm: {message}")
                status_text = "Lỗi"
                status = pump_info.get('trang_thai', False)  # Revert to API value
            else:
                status = new_status
                status_text = "Đang Hoạt Động" if new_status else "Dừng"
        else:
            # Regular refresh (interval or pump selection change)
            status = pump_info.get('trang_thai', False)
            status_text = "Đang Hoạt Động" if status in (True, 1) else "Dừng"

        # Handle auto mode toggle (che_do update)
        if 'auto-mode-btn' in str(triggered_id):
            new_mode = 1 if (isinstance(auto_mode_value, list) and 1 in auto_mode_value) else 0
            payload = {
                'ten_may_bom': pump_info.get('ten_may_bom', ''),
                'mo_ta': pump_info.get('mo_ta', ''),
                'ma_iot_lk': pump_info.get('ma_iot_lk', ''),
                'che_do': new_mode,
                'trang_thai': bool(status)
            }
            success, message = update_pump(pump_id, payload, token=token)
            if not success:
                print(f"Lỗi cập nhật chế độ máy bơm: {message}")
                mode_text = "Lỗi"
                mode = pump_info.get('che_do', 0)  # Revert to API value
            else:
                mode = new_mode
                mode_text = "Tự động (theo độ ẩm đất)" if new_mode == 1 else "Thủ công"
        else:
            mode = pump_info.get('che_do', 0)
            mode_text = "Tự động (theo độ ẩm đất)" if mode == 1 else "Thủ công"

        pump_toggle = [1] if status in (True, 1) else []
        auto_mode_toggle = [1] if mode == 1 else []
        pump_toggle_disabled = True if mode == 1 else False

        return (pump_name, pump_toggle, pump_toggle_disabled, status_text, auto_mode_toggle, mode_text)

    except Exception as e:
        print(f"Error updating pump control panel: {e}")
        import traceback
        traceback.print_exc()
        pump_name = selected_pump.get('ten_may_bom', 'Máy Bơm Nước Chính')
        return (pump_name, [], False, "Lỗi", [], "Lỗi")

@callback(
    Output('pump-history', 'children'),
    [
        Input('selected-pump-store', 'data'),
        Input('interval-component', 'n_intervals'),
    ],
    [
        State('session-store', 'data')
    ]
)
def update_pump_history(selected_pump, n_intervals, session):
    """Update pump history with recent logs from last 5 days."""
    if not selected_pump or not selected_pump.get('ma_may_bom'):
        return [html.Small('Chưa chọn máy bơm', className='text-muted')]
    
    try:
        from datetime import datetime
        pump_id = selected_pump.get('ma_may_bom')
        token = session.get('token') if session else None
        
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
            return [html.Small('Không có hoạt động gần đây', className='text-muted')]
        
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
        
        return history_items
        
    except Exception as e:
        print(f"Error fetching pump history: {e}")
        return [html.Small('Không thể tải lịch sử', className='text-muted')]

@callback(
    Output('pump-history-modal', 'is_open'),
    [
        Input('pump-history-view-all-btn', 'n_clicks'),
        Input('pump-history-modal-close', 'n_clicks'),
    ],
    [
        State('pump-history-modal', 'is_open')
    ]
)
def toggle_pump_history_modal(n_clicks_open, n_clicks_close, is_open):
    """Toggle pump history modal."""
    if n_clicks_open or n_clicks_close:
        return not is_open
    return is_open

@callback(
    Output('pump-history-modal-content', 'children'),
    [
        Input('pump-history-modal', 'is_open'),
    ],
    [
        State('selected-pump-store', 'data'),
        State('session-store', 'data')
    ]
)
def update_pump_history_modal(is_open, selected_pump, session):
    """Update pump history modal content with all logs from last 30 days, grouped by date."""
    if not is_open or not selected_pump or not selected_pump.get('ma_may_bom'):
        return [html.P("Không có dữ liệu", className="text-muted text-center")]
    
    try:
        from datetime import datetime, timedelta
        from collections import defaultdict
        
        pump_id = selected_pump.get('ma_may_bom')
        token = session.get('token') if session else None
        
        # Get logs from last 30 days
        all_logs = []
        for i in range(30):
            query_date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            logs = get_pump_memory_logs(pump_id, limit=100, offset=0, token=token, date=query_date)
            
            if isinstance(logs, dict):
                data = logs.get('data', [])
            elif isinstance(logs, list):
                data = logs
            else:
                data = []
            
            all_logs.extend(data)
        
        if not all_logs:
            return [html.P("Không có hoạt động trong 30 ngày gần đây", className="text-muted text-center")]
        
        # Group logs by date
        logs_by_date = defaultdict(list)
        for log in all_logs:
            # Use thoi_gian_bat if available, otherwise thoi_gian_tat
            time_str = log.get('thoi_gian_bat') or log.get('thoi_gian_tat') or log.get('thoi_gian_tao', '')
            if time_str:
                # Extract date from timestamp (YYYY-MM-DD)
                date_part = time_str.split('T')[0] if 'T' in time_str else time_str[:10]
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

@callback(
    Output('pump-history-date-picker', 'date'),
    [
        Input('pump-history-modal', 'is_open'),
    ]
)
def init_date_picker(is_open):
    """Initialize date picker with today's date when modal opens."""
    if is_open:
        return datetime.now().strftime('%Y-%m-%d')
    raise PreventUpdate

@callback(
    Output('soil-moisture-date-picker', 'date'),
    [
        Input('soil-moisture-modal', 'is_open'),
    ]
)
def init_soil_moisture_date_picker(is_open):
    """Initialize soil moisture date picker with today's date when modal opens."""
    if is_open:
        return datetime.now().strftime('%Y-%m-%d')
    raise PreventUpdate

@callback(
    Output('soil-moisture-modal', 'is_open'),
    [
        Input('soil-moisture-card', 'n_clicks'),
        Input('soil-moisture-modal-close', 'n_clicks'),
    ],
    [
        State('soil-moisture-modal', 'is_open')
    ]
)
def toggle_soil_moisture_modal(n_clicks_card, n_clicks_close, is_open):
    """Toggle soil moisture modal when card is clicked."""
    if n_clicks_card or n_clicks_close:
        return not is_open
    return is_open

@callback(
    [
        Output('soil-moisture-chart', 'figure'),
        Output('soil-moisture-avg', 'children'),
        Output('soil-moisture-max', 'children'),
        Output('soil-moisture-min', 'children'),
    ],
    [
        Input('soil-moisture-modal', 'is_open'),
        Input('soil-moisture-date-picker', 'date'),
    ],
    [
        State('session-store', 'data')
    ]
)
def update_soil_moisture_chart(is_open, selected_date, session):
    """Update soil moisture chart when modal opens or date is changed."""
    if not is_open:
        raise PreventUpdate
    
    token = session.get('token') if session else None
    
    try:
        # Use selected date or fall back to today
        date_str = selected_date if selected_date else datetime.now().strftime('%Y-%m-%d')
        
        df = fetch_sensor_data(token, date_str)
        
        if df.empty:
            empty_figure = {
                'data': [],
                'layout': go.Layout(
                    title='Không có dữ liệu',
                    xaxis={'title': 'Thời Gian'},
                    yaxis={'title': 'Độ Ẩm Đất (%)'},
                    plot_bgcolor='white',
                    paper_bgcolor='white',
                )
            }
            return empty_figure, "N/A", "N/A", "N/A"
        
        # Create soil moisture chart
        figure = {
            'data': [
                go.Scatter(
                    x=df['date'],
                    y=df['soil_moisture'],
                    mode='lines+markers',
                    name='Độ Ẩm Đất',
                    line=dict(color='#27ae60', width=3),
                    marker=dict(size=6),
                    fill='tozeroy',
                    fillcolor='rgba(39, 174, 96, 0.2)'
                )
            ],
            'layout': go.Layout(
                xaxis={'title': 'Thời Gian', 'gridcolor': '#f0f0f0'},
                yaxis={'title': 'Độ Ẩm Đất (%)', 'gridcolor': '#f0f0f0'},
                hovermode='x unified',
                plot_bgcolor='white',
                paper_bgcolor='white',
                margin=dict(l=50, r=20, t=20, b=50),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )
        }
        
        # Calculate stats
        avg_moisture = f"{df['soil_moisture'].mean():.1f}%" if not df.empty else "N/A"
        max_moisture = f"{df['soil_moisture'].max():.1f}%" if not df.empty else "N/A"
        min_moisture = f"{df['soil_moisture'].min():.1f}%" if not df.empty else "N/A"
        
        return figure, avg_moisture, max_moisture, min_moisture
    
    except Exception as e:
        print(f"Error updating soil moisture chart: {e}")
        empty_figure = {
            'data': [],
            'layout': go.Layout(
                title='Lỗi tải dữ liệu',
                xaxis={'title': 'Thời Gian'},
                yaxis={'title': 'Độ Ẩm Đất (%)'},
                plot_bgcolor='white',
                paper_bgcolor='white',
            )
        }
        return empty_figure, "N/A", "N/A", "N/A"