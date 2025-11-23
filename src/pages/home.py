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

def fetch_sensor_data(token=None):
    try:
        today = datetime.now().strftime('%Y-%m-%d')
        response_data = get_data_by_date(today, token)

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

empty_df = create_empty_dataframe()

layout = html.Div([
    create_navbar(is_authenticated=False),
    
    dbc.Container([
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H6("Thống Kê", className="card-header-title")
                    ]),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                dbc.Card([
                                    dbc.CardBody([
                                        html.Div([
                                            html.Div([
                                                html.H6("Máy Bơm Hoạt Động", className="stat-label"),
                                                html.H3(id='active-pumps', children="0/0", className="stat-value"),
                                                html.Small("Đang chạy", className="stat-desc")
                                            ]),
                                            html.I(className="fas fa-wave-square stat-icon text-primary")
                                        ], className="stat-card-content")
                                    ])
                                ], className="stat-card-wrapper")
                            ], lg=3, md=6, className="mb-3"),
                            
                            dbc.Col([
                                dbc.Card([
                                    dbc.CardBody([
                                        html.Div([
                                            html.Div([
                                                html.H6("Lưu Lượng Tổng", className="stat-label"),
                                                html.H3(id='total-flow', children="N/A", className="stat-value"),
                                                html.Small(id='total-flow-change', children="+0%", className="stat-desc text-success")
                                            ]),
                                            html.I(className="fas fa-tint stat-icon text-info")
                                        ], className="stat-card-content")
                                    ])
                                ], className="stat-card-wrapper")
                            ], lg=3, md=6, className="mb-3"),
                            
                            dbc.Col([
                                dbc.Card([
                                    dbc.CardBody([
                                        html.Div([
                                            html.Div([
                                                html.H6("Dự Đoán Lưu Lượng", className="stat-label"),
                                                html.H3(id='predicted-flow', children="N/A", className="stat-value"),
                                                html.Small("Trung bình 24h", className="stat-desc")
                                            ]),
                                            html.I(className="fas fa-chart-line stat-icon text-success")
                                        ], className="stat-card-content")
                                    ])
                                ], className="stat-card-wrapper")
                            ], lg=3, md=6, className="mb-3"),
                            
                            dbc.Col([
                                dbc.Card([
                                    dbc.CardBody([
                                        html.Div([
                                            html.Div([
                                                html.H6("Tổng Cảm Biến", className="stat-label"),
                                                html.H3(id='total-sensors', children="0", className="stat-value"),
                                                html.Small("Cảm biến hoạt động", className="stat-desc")
                                            ]),
                                            html.I(className="fas fa-microchip stat-icon text-warning")
                                        ], className="stat-card-content")
                                    ])
                                ], className="stat-card-wrapper")
                            ], lg=3, md=6, className="mb-3"),
                        ])
                    ],  style={"padding": "12px"})
                ], className="h-100 stats-card")
            ], lg=9, className="mb-4 h-100"),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H6("Thông Tin Người Dùng", className="card-header-title")
                    ]),
                    dbc.CardBody([
                        html.Div([
                            html.Span([
                                html.I(className="fas fa-user me-2"),
                                html.Span(id='user-name', children="Không xác định"),
                                " - ",
                                html.Span(id='user-role', children="Người dùng", className="text-muted")
                            ], className="mb-3")
                        ]),
                        
                        html.Hr(),
                        
                        html.Div([
                            html.Div([
                                html.Strong("Trạng thái:"),
                                html.Span(id='user-status', children="N/A", className="ms-2")
                            ], className="operator-info-row mb-2"),
                            html.Div([
                                html.Strong("Đăng nhập lần cuối:"),
                                html.Span(id='user-last-login', children="N/A", className="ms-2")
                            ], className="operator-info-row"),
                        ])
                    ])
                ], className="h-100 operator-card")
            ], lg=3, className="mb-4 h-100"),
        ], className="mb-4 equal-height-row"),
        
        dbc.Card([
            dbc.CardHeader([
                html.Div([
                    html.H6("Chọn Máy Bơm", className="card-header-title"),
                    html.A([
                        "Xem tất cả"
                    ], href="/pump", className="view-all-link", style={"textDecoration": "none", "color": "#0d6efd", "fontWeight": "500"})
                ], className="d-flex justify-content-between align-items-center")
            ])
        ], className="mb-3"),
        
        html.Div(id='pump-list-container', children=[]),
        dcc.Store(id='pump-mode-refresh', data={'mode': None, 'ts': None}),
        
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.Div([
                            html.H6(id='pump-detail-title', children="Chi Tiết Máy Bơm - Máy Bơm Nước Chính", className="card-header-title"),
                            html.Span(id='pump-detail-status', children="đang chạy", className="badge badge-running ms-2")
                        ], className="d-flex align-items-center")
                    ]),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                dbc.Card([
                                    dbc.CardBody([
                                        html.H6("Lưu Lượng", className="card-metric-label"),
                                        html.H4(id='selected-flow-rate', children="N/A", className="card-metric-value"),
                                    ])
                                ], className="metric-card")
                            ], md=3),

                            dbc.Col([
                                dbc.Card([
                                    dbc.CardBody([
                                        html.H6("Độ Ẩm Đất", className="card-metric-label"),
                                        html.H4(id='selected-soil-moisture', children="N/A", className="card-metric-value"),
                                    ])
                                ], className="metric-card")
                            ], md=3),

                            dbc.Col([
                                dbc.Card([
                                    dbc.CardBody([
                                        html.H6("Độ Ẩm", className="card-metric-label"),
                                        html.H4(id='selected-humidity', children="N/A", className="card-metric-value"),
                                    ])
                                ], className="metric-card")
                            ], md=3),

                            dbc.Col([
                                dbc.Card([
                                    dbc.CardBody([
                                        html.H6("Nhiệt Độ", className="card-metric-label"),
                                        html.H4(id='selected-temperature', children="N/A", className="card-metric-value"),
                                    ])
                                ], className="metric-card")
                            ], md=3),
                        ], className="mb-4"),

                        dbc.Row([
                            dbc.Col([
                                dbc.Card([
                                    dbc.CardBody([
                                        html.H6("Mưa", className="card-metric-label"),
                                        html.H4(id='selected-rain', children="N/A", className="card-metric-value"),
                                    ])
                                ], className="metric-card")
                            ], md=3),

                            dbc.Col([
                                dbc.Card([
                                    dbc.CardBody([
                                        html.H6("Thời Gian Bật", className="card-metric-label"),
                                        html.H4(id='pump-last-on', children="—", className="card-metric-value"),
                                    ])
                                ], className="metric-card")
                            ], md=3),

                            dbc.Col([
                                dbc.Card([
                                    dbc.CardBody([
                                        html.H6("Thời Gian Tắt", className="card-metric-label"),
                                        html.H4(id='pump-last-off', children="—", className="card-metric-value"),
                                    ])
                                ], className="metric-card")
                            ], md=3),

                            dbc.Col([
                                dbc.Card([
                                    dbc.CardBody([
                                        html.H6("Thời Gian Chạy", className="card-metric-label"),
                                        html.H4(id='pump-run-duration', children="—", className="card-metric-value"),
                                    ])
                                ], className="metric-card")
                            ], md=3),
                        ])
                    ])
                ], className="details-card mb-4", style={"height": "100%"})
            ], lg=9, className="mb-4"),

            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H6("Điều Khiển Máy Bơm", className="card-header-title")
                    ]),
                    dbc.CardBody([
                        html.Div([
                            html.Div([
                                html.Span("Máy bơm được chọn", className="control-label text-muted"),
                                html.Strong("", id='control-selected-pump-name', className="control-selected-name")
                            ], className="pump-control-summary mb-3"),

                            html.Div([
                                dbc.Button(
                                    [html.I(className="fas fa-play me-1"), "Bật"],
                                    color='success',
                                    size='sm',
                                    id='pump-start-btn',
                                    className="pump-control-btn start-btn",
                                    disabled=True
                                ),
                                dbc.Button(
                                    [html.I(className="fas fa-stop me-1"), "Tắt"],
                                    color='danger',
                                    outline=True,
                                    size='sm',
                                    id='pump-stop-btn',
                                    className="pump-control-btn stop-btn ms-2",
                                    disabled=True
                                )
                            ], className="pump-control-actions d-flex align-items-center mb-3"),

                            html.Div([
                                html.Span("Chế độ vận hành", className="control-label text-muted"),
                                dbc.RadioItems(
                                    id='pump-mode-select',
                                    options=[
                                        {'label': 'Thủ công', 'value': 0},
                                        {'label': 'Tự động', 'value': 1},
                                        {'label': 'Bảo trì', 'value': 2}
                                    ],
                                    value=None,
                                    inline=True,
                                    className="pump-mode-select mt-2"
                                )
                            ], className="pump-mode-wrapper")
                        ])
                    ])
                ], className="operator-card", style={"height": "100%"})
            ], lg=3, className="mb-4")
        ]),

        dbc.Row([
            dbc.Col([
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader([
                                html.H6([
                                    html.I(className="fas fa-chart-area me-2"),
                                    "Phân Tích Lưu Lượng"
                                ], className="card-header-title")
                            ]),
                            dbc.CardBody([
                                dcc.Graph(id='selected-flow-rate-chart', config={'displayModeBar': True, 'scrollZoom': True}) ,
                                html.P("So sánh Thực Tế vs Dự Đoán (Xem trong 24 giờ)", className="text-center text-muted small mt-3 mb-0")
                            ])
                        ], className="chart-card")
                    ], md=12, lg=6),
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader([
                                html.H6([
                                    html.I(className="fas fa-temperature-high me-2"),
                                    "Nhiệt Độ"
                                ], className="card-header-title")
                            ]),
                            dbc.CardBody([
                                dcc.Graph(id='selected-temperature-chart', config={'displayModeBar': False})
                            ])
                        ], className="chart-card")
                    ], md=12, lg=6),
                ], className="mb-4"),

                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader([
                                html.H6([
                                    html.I(className="fas fa-droplets me-2"),
                                    "Độ Ẩm"
                                ], className="card-header-title")
                            ]),
                            dbc.CardBody([
                                dcc.Graph(id='selected-humidity-chart', config={'displayModeBar': False})
                            ])
                        ], className="chart-card")
                    ], md=12, lg=6),
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader([
                                html.H6([
                                    html.I(className="fas fa-leaf me-2"),
                                    "Độ Ẩm Đất"
                                ], className="card-header-title")
                            ]),
                            dbc.CardBody([
                                dcc.Graph(id='selected-soil-moisture-chart', config={'displayModeBar': False})
                            ])
                        ], className="chart-card")
                    ], md=12, lg=6),
                ], className="mb-4"),
            ], lg=12)
        ]),
        
    ], fluid=True, className="home-page-container px-4"),
    
    dcc.Interval(
        id='interval-component',
        interval=5*1000,
        n_intervals=0
    )
], className="page-container")
@callback(
    [
        Output('total-flow', 'children'),
        Output('total-flow-change', 'children'),
        Output('predicted-flow', 'children'),
    ],
    [
        Input('interval-component', 'n_intervals'),
        Input('url', 'pathname'),
        Input('session-store', 'modified_timestamp'),
    ],
    [
        State('session-store', 'data')
    ]
)
def update_summary_stats(n, pathname, session_modified, session):
    """Update summary statistics only."""
    if pathname not in ('', '/', None):
        raise PreventUpdate
    
    token = None
    if session and isinstance(session, dict):
        token = session.get('token')
    
    df = fetch_sensor_data(token)
    
    if df.empty:
        raise PreventUpdate
    
    total_flow = f"{df['flow_rate'].sum():.1f} L" if not df.empty else "N/A"
    avg_flow = df['flow_rate'].mean() if not df.empty else 0
    predicted_flow = f"{avg_flow:.1f} L/phút" if not df.empty else "N/A"
    
    if len(df) > 1:
        flow_change = ((df['flow_rate'].iloc[-1] - df['flow_rate'].iloc[0]) / df['flow_rate'].iloc[0] * 100) if df['flow_rate'].iloc[0] != 0 else 0
        flow_change_str = f"+{flow_change:.1f}%" if flow_change >= 0 else f"{flow_change:.1f}%"
    else:
        flow_change_str = "+0%"
    
    return (
        total_flow,
        flow_change_str,
        predicted_flow,
    )

@callback(
    [
        Output('flow-rate-chart', 'figure'),
        Output('temperature-chart', 'figure'),
        Output('humidity-chart', 'figure'),
        Output('soil-moisture-chart', 'figure'),
        Output('flow-rate', 'children'),
        Output('temperature', 'children'),
        Output('humidity', 'children'),
        Output('soil-moisture', 'children'),
    ],
    [
        Input('interval-component', 'n_intervals'),
        Input('url', 'pathname'),
        Input('session-store', 'modified_timestamp'),
    ],
    [
        State('session-store', 'data')
    ]
)
def update_all_charts(n, pathname, session_modified, session):
    """Update all charts with daily data."""
    if pathname not in ('', '/', None):
        raise PreventUpdate
    
    token = None
    if session and isinstance(session, dict):
        token = session.get('token')
    
    df = fetch_sensor_data(token)
    
    if df.empty:
        raise PreventUpdate
    
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
            xaxis={
                'title': 'Thời Gian',
                'gridcolor': '#f0f0f0',
            },
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
    
    temperature_figure = {
        'data': [
            go.Scatter(
                x=df['date'],
                y=df['temperature'],
                mode='lines',
                name='Nhiệt Độ',
                line=dict(color='#ff7f0e', width=2),
                fill='tozeroy',
                fillcolor='rgba(255, 127, 14, 0.2)'
            )
        ],
        'layout': go.Layout(
            xaxis={'title': 'Thời Gian', 'gridcolor': '#f0f0f0'},
            yaxis={'title': 'Nhiệt Độ (°C)', 'gridcolor': '#f0f0f0'},
            hovermode='x unified',
            plot_bgcolor='white',
            paper_bgcolor='white',
            margin=dict(l=50, r=20, t=20, b=50),
        )
    }
    
    humidity_figure = {
        'data': [
            go.Scatter(
                x=df['date'],
                y=df['humidity'],
                mode='lines',
                name='Độ Ẩm',
                line=dict(color='#1f77b4', width=2),
                fill='tozeroy',
                fillcolor='rgba(31, 119, 180, 0.2)'
            )
        ],
        'layout': go.Layout(
            xaxis={'title': 'Thời Gian', 'gridcolor': '#f0f0f0'},
            yaxis={'title': 'Độ Ẩm (%)', 'gridcolor': '#f0f0f0'},
            hovermode='x unified',
            plot_bgcolor='white',
            paper_bgcolor='white',
            margin=dict(l=50, r=20, t=20, b=50),
        )
    }
    
    soil_moisture_figure = {
        'data': [
            go.Scatter(
                x=df['date'],
                y=df['soil_moisture'],
                mode='lines',
                name='Độ Ẩm Đất',
                line=dict(color='#2ca02c', width=2),
                fill='tozeroy',
                fillcolor='rgba(44, 160, 44, 0.2)'
            )
        ],
        'layout': go.Layout(
            xaxis={'title': 'Thời Gian', 'gridcolor': '#f0f0f0'},
            yaxis={'title': 'Độ Ẩm Đất (%)', 'gridcolor': '#f0f0f0'},
            hovermode='x unified',
            plot_bgcolor='white',
            paper_bgcolor='white',
            margin=dict(l=50, r=20, t=20, b=50),
        )
    }
    
    flow_rate = f"{df['flow_rate'].iloc[-1]:.1f} L/phút" if not df.empty else "N/A"
    temperature = f"{df['temperature'].iloc[-1]:.1f}°C" if not df.empty else "N/A"
    humidity = f"{df['humidity'].iloc[-1]:.0f}%" if not df.empty else "N/A"
    soil_moisture = f"{df['soil_moisture'].iloc[-1]:.0f}%" if not df.empty else "N/A"
    
    total_flow = f"{df['flow_rate'].sum():.1f} L" if not df.empty else "N/A"
    avg_flow = df['flow_rate'].mean() if not df.empty else 0
    predicted_flow = f"{avg_flow:.1f} L/phút" if not df.empty else "N/A"
    
    if len(df) > 1:
        flow_change = ((df['flow_rate'].iloc[-1] - df['flow_rate'].iloc[0]) / df['flow_rate'].iloc[0] * 100) if df['flow_rate'].iloc[0] != 0 else 0
        flow_change_str = f"+{flow_change:.1f}%" if flow_change >= 0 else f"{flow_change:.1f}%"
    else:
        flow_change_str = "+0%"
    
    return (
        flow_rate_figure,
        temperature_figure,
        humidity_figure,
        soil_moisture_figure,
        flow_rate,
        temperature,
        humidity,
        soil_moisture,
    )

@callback(
    [
        Output('active-pumps', 'children'),
        Output('total-sensors', 'children'),
    ],
    [
        Input('interval-component', 'n_intervals'),
        Input('url', 'pathname'),
        Input('session-store', 'modified_timestamp'),
    ],
    [
        State('session-store', 'data')
    ]
)
def update_active_pumps_and_sensors(n, pathname, session_modified, session):
    """Update active pump count and total sensors independently."""
    if pathname not in ('', '/', None):
        raise PreventUpdate
    
    token = None
    if session and isinstance(session, dict):
        token = session.get('token')
    
    pumps = fetch_pump_list(token)
    if not isinstance(pumps, list):
        pumps = []

    running_count = 0
    for pump in pumps:
        if isinstance(pump, dict):
            status = pump.get('trang_thai', False)
            if status in (True, 1):
                running_count += 1
    
    active_pumps_str = f"{running_count}/{len(pumps)}" if pumps else "0/0"
    
    try:
        sensors_response = list_sensors(limit=1000, offset=0, token=token)
        if isinstance(sensors_response, dict):
            data = sensors_response.get('data')
            sensors = data if isinstance(data, list) else []
        elif isinstance(sensors_response, list):
            sensors = sensors_response
        else:
            sensors = []
        total_sensors_str = str(len(sensors)) if sensors else "0"
    except Exception as e:
        print(f"Error fetching sensors: {e}")
        total_sensors_str = "0"
    
    
    return (
        active_pumps_str,
        total_sensors_str,
    )

@callback(
    Output('pump-list-container', 'children'),
    [
        Input('interval-component', 'n_intervals'),
        Input('url', 'pathname'),
        Input('session-store', 'modified_timestamp'),
    ],
    [
        State('session-store', 'data')
    ]
)
def update_pump_list(n, pathname, session_modified, session):
    """Update pump list independently."""
    if pathname not in ('', '/', None):
        raise PreventUpdate
    
    token = None
    if session and isinstance(session, dict):
        token = session.get('token')
    
    pumps = fetch_pump_list(token)
    
    if not pumps:
        return [html.P("Không có máy bơm nào để hiển thị", className="text-center text-muted")]
    
    pumps = sorted(pumps, key=lambda x: (
        not x.get('trang_thai', False),  # True first for trang_thai
        x.get('ma_may_bom', ''),        # Then by ma_may_bom
        x.get('che_do', 0)              # Finally by che_do
    ))
    
    pump_cards = []
    for pump in pumps:
        pump_id = pump.get('ma_may_bom')
        pump_name = pump.get('ten_may_bom', 'Không xác định')
        status = pump.get('trang_thai', False)  # True = đang chạy, False = dừng
        mode = pump.get('che_do', 0)  # 1 = tự động, 0 = thủ công, 2 = bảo trì
        
        latest_data = fetch_pump_latest_data(pump_id, token) if pump_id else None
        flow = 0
        if latest_data:
            flow = float(latest_data.get('luu_luong_nuoc', 0))
        
        mode_text = {0: 'Thủ công', 1: 'Tự động', 2: 'Bảo trì'}.get(mode, f'Chế độ {mode}')
        
        if mode == 2:
            badge_class = 'badge badge-maintenance'
            icon_class = 'fas fa-droplet pump-status-icon maintenance'
            status_text = 'bảo trì'
        elif status == True or status == 1:  # Đang chạy (support both True and 1)
            badge_class = 'badge badge-running'
            icon_class = 'fas fa-droplet pump-status-icon running'
            status_text = 'đang chạy'
        else:  # Dừng (False or 0)
            badge_class = 'badge badge-stopped'
            icon_class = 'fas fa-droplet pump-status-icon stopped'
            status_text = 'dừng'
        
        pump_card = html.Div(
            [
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.Div([
                                html.I(className=icon_class),
                                html.Div([
                                    html.H6(pump_name, className="mb-1"),
                                    html.Small(f"Chế độ: {mode_text}", className="text-muted")
                                ], className="pump-info")
                            ], className="pump-header"),
                            html.Div([
                                html.H6(f"{flow:.1f} L/phút", className="pump-flow"),
                                html.Span(status_text, className=badge_class)
                            ], className="pump-stats")
                        ], className="pump-card-content")
                    ], className="pump-card-body")
                ], className="pump-card")
            ],
            id={'type': 'pump-card-btn', 'index': pump_id},
            n_clicks=0,
            className="pump-card-scroll-item",
            style={"cursor": "pointer"}
        )
        pump_cards.append(pump_card)
    
    pump_list_content = html.Div(
        pump_cards,
        className="pump-card-scroll-container"
    )
    
    return pump_list_content

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
        Output('pump-detail-title', 'children'),
        Output('pump-detail-status', 'children'),
        Output('pump-detail-status', 'className'),
        Output('selected-flow-rate-chart', 'figure'),
        Output('selected-temperature-chart', 'figure'),
        Output('selected-humidity-chart', 'figure'),
        Output('selected-soil-moisture-chart', 'figure'),
        Output('selected-flow-rate', 'children'),
        Output('selected-temperature', 'children'),
        Output('selected-humidity', 'children'),
        Output('selected-soil-moisture', 'children'),
        Output('selected-rain', 'children'),
        Output('pump-last-on', 'children'),
        Output('pump-last-off', 'children'),
        Output('pump-run-duration', 'children'),
    ],
    [
        Input('selected-pump-store', 'data'),
        Input('interval-component', 'n_intervals'),
        Input('url', 'pathname'),
    ],
    [
        State('session-store', 'data')
    ]
)
def update_pump_details(selected_pump, n, pathname, session):
    """Update pump details based on selected pump."""
    if pathname not in ('', '/', None):
        raise PreventUpdate
    
    if not selected_pump or not selected_pump.get('ma_may_bom'):
        raise PreventUpdate
    
    try:
        token = None
        if session and isinstance(session, dict):
            token = session.get('token')
        
        pump_id = selected_pump.get('ma_may_bom')
        
        pump_info = get_pump(pump_id, token) if pump_id else None
        pump_name = pump_info.get('ten_may_bom', 'Không xác định') if pump_info else 'Không xác định'
        status = pump_info.get('trang_thai', False) if pump_info else False
        
        if status == True or status == 1:
            badge_text = 'đang chạy'
            badge_class = 'badge badge-running ms-2'
        else:
            badge_text = 'dừng'
            badge_class = 'badge badge-stopped ms-2'
        
        title = f"Chi Tiết Máy Bơm - {pump_name}"
        
        today = datetime.now().strftime('%Y-%m-%d')
        df_all = fetch_sensor_data(token)

        if df_all.empty:
            empty_figure = {
                'data': [go.Scatter(x=[], y=[], mode='lines')],
                'layout': go.Layout(
                    xaxis={'title': 'Thời Gian'},
                    yaxis={'title': 'Value'},
                    plot_bgcolor='white',
                    paper_bgcolor='white',
                )
            }
            return (
                title,
                badge_text,
                badge_class,
                empty_figure,  # flow rate chart
                empty_figure,  # temperature chart
                empty_figure,  # humidity chart
                empty_figure,  # soil moisture chart
                "N/A",  # flow rate value
                "N/A",  # temperature value
                "N/A",  # humidity value
                "N/A",  # soil moisture value
                "N/A",  # rain value
                "—",    # last on time
                "—",    # last off time
                "—",    # run duration
            )

        str_id = str(pump_id) if pump_id is not None else None
        if 'ma_may_bom' in df_all.columns and str_id is not None:
            df = df_all[df_all['ma_may_bom'].astype(str) == str_id].copy()
        else:
            df = df_all.copy()

        if df.empty:
            empty_figure = {
                'data': [go.Scatter(x=[], y=[], mode='lines')],
                'layout': go.Layout(
                    xaxis={'title': 'Thời Gian'},
                    yaxis={'title': 'Value'},
                    plot_bgcolor='white',
                    paper_bgcolor='white',
                )
            }
            return (
                title,
                badge_text,
                badge_class,
                empty_figure,
                empty_figure,
                empty_figure,
                empty_figure,
                "N/A",
                "N/A",
                "N/A",
                "N/A",
                "N/A",
                "—",
                "—",
                "—",
            )
        
        pump_logs = get_pump_memory_logs(pump_id, limit=10, offset=0, token=token)
        last_on_time = "—"
        last_off_time = "—"
        run_duration = "—"
        
        if isinstance(pump_logs, dict) and 'data' in pump_logs:
            logs = pump_logs['data']
            if logs and isinstance(logs, list):
                logs.sort(key=lambda x: x.get('thoi_gian_tao', ''), reverse=True)
                
                for log in logs:
                    status = log.get('trang_thai')
                    time = log.get('thoi_gian_tao')
                    if time:
                        formatted_time = format_display_time(time)
                        if status == True or status == 1:  # On event
                            if last_on_time == "—":
                                last_on_time = formatted_time
                            if last_off_time == "—":
                                last_off_time = formatted_time
                
                if len(logs) >= 2:
                    latest = logs[0]
                    previous = logs[1]
                    if latest and previous and 'thoi_gian_tao' in latest and 'thoi_gian_tao' in previous:
                        try:
                            latest_time = datetime.fromisoformat(latest['thoi_gian_tao'].replace('Z', '+00:00'))
                            previous_time = datetime.fromisoformat(previous['thoi_gian_tao'].replace('Z', '+00:00'))
                            duration = latest_time - previous_time
                            minutes = duration.total_seconds() / 60
                            if minutes < 60:
                                run_duration = f"{int(minutes)} phút"
                            else:
                                hours = minutes / 60
                                run_duration = f"{int(hours)} giờ {int(minutes % 60)} phút"
                        except:
                            run_duration = "—"
        
        if 'thoi_gian_tao' in df.columns:
            df['thoi_gian_tao'] = pd.to_datetime(df['thoi_gian_tao'], errors='coerce')
            try:
                if df['thoi_gian_tao'].dt.tz is None:
                    df['thoi_gian_tao'] = df['thoi_gian_tao'].dt.tz_localize('Asia/Bangkok')
                else:
                    df['thoi_gian_tao'] = df['thoi_gian_tao'].dt.tz_convert('Asia/Bangkok')
            except Exception:
                df['thoi_gian_tao'] = pd.to_datetime(df['thoi_gian_tao'])
            
            df = df.rename(columns={
                'thoi_gian_tao': 'date',
                'luu_luong_nuoc': 'flow_rate',
                'do_am_dat': 'soil_moisture',
                'nhiet_do': 'temperature',
                'do_am': 'humidity',
            })
            
            df = df.sort_values('date')
            
            for col in ['flow_rate', 'soil_moisture', 'temperature', 'humidity']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
        elif 'date' in df.columns:
            df = df.sort_values('date')
        
        flow_rate_figure = {
            'data': [
                go.Scatter(
                    x=df['date'] if 'date' in df.columns else [],
                    y=df['flow_rate'] if 'flow_rate' in df.columns else [],
                    mode='lines',
                    name='Lưu Lượng Thực Tế',
                    line=dict(color='#1f77b4', width=3),
                    fill='tozeroy',
                    fillcolor='rgba(31, 119, 180, 0.2)'
                ),
            ],
            'layout': go.Layout(
                xaxis={'title': 'Thời Gian', 'gridcolor': '#f0f0f0'},
                yaxis={'title': 'Lưu Lượng (L/phút)', 'gridcolor': '#f0f0f0'},
                hovermode='x unified',
                plot_bgcolor='white',
                paper_bgcolor='white',
                margin=dict(l=50, r=20, t=20, b=50),
            )
        }
        
        temperature_figure = {
            'data': [
                go.Scatter(
                    x=df['date'] if 'date' in df.columns else [],
                    y=df['temperature'] if 'temperature' in df.columns else [],
                    mode='lines',
                    name='Nhiệt Độ',
                    line=dict(color='#ff7f0e', width=2),
                    fill='tozeroy',
                    fillcolor='rgba(255, 127, 14, 0.2)'
                )
            ],
            'layout': go.Layout(
                xaxis={'title': 'Thời Gian', 'gridcolor': '#f0f0f0'},
                yaxis={'title': 'Nhiệt Độ (°C)', 'gridcolor': '#f0f0f0'},
                hovermode='x unified',
                plot_bgcolor='white',
                paper_bgcolor='white',
                margin=dict(l=50, r=20, t=20, b=50),
            )
        }
        
        humidity_figure = {
            'data': [
                go.Scatter(
                    x=df['date'] if 'date' in df.columns else [],
                    y=df['humidity'] if 'humidity' in df.columns else [],
                    mode='lines',
                    name='Độ Ẩm',
                    line=dict(color='#1f77b4', width=2),
                    fill='tozeroy',
                    fillcolor='rgba(31, 119, 180, 0.2)'
                )
            ],
            'layout': go.Layout(
                xaxis={'title': 'Thời Gian', 'gridcolor': '#f0f0f0'},
                yaxis={'title': 'Độ Ẩm (%)', 'gridcolor': '#f0f0f0'},
                hovermode='x unified',
                plot_bgcolor='white',
                paper_bgcolor='white',
                margin=dict(l=50, r=20, t=20, b=50),
            )
        }
        
        soil_moisture_figure = {
            'data': [
                go.Scatter(
                    x=df['date'] if 'date' in df.columns else [],
                    y=df['soil_moisture'] if 'soil_moisture' in df.columns else [],
                    mode='lines',
                    name='Độ Ẩm Đất',
                    line=dict(color='#2ca02c', width=2),
                    fill='tozeroy',
                    fillcolor='rgba(44, 160, 44, 0.2)'
                )
            ],
            'layout': go.Layout(
                xaxis={'title': 'Thời Gian', 'gridcolor': '#f0f0f0'},
                yaxis={'title': 'Độ Ẩm Đất (%)', 'gridcolor': '#f0f0f0'},
                hovermode='x unified',
                plot_bgcolor='white',
                paper_bgcolor='white',
                margin=dict(l=50, r=20, t=20, b=50),
            )
        }
        
        flow_rate = "N/A"
        temperature = "N/A"
        humidity = "N/A"
        soil_moisture = "N/A"
        
        if 'flow_rate' in df.columns and not df.empty:
            try:
                val = df['flow_rate'].iloc[-1]
                flow_rate = f"{float(val):.1f} L/phút" if pd.notna(val) else "N/A"
            except:
                flow_rate = "N/A"
        
        if 'temperature' in df.columns and not df.empty:
            try:
                val = df['temperature'].iloc[-1]
                temperature = f"{float(val):.1f}°C" if pd.notna(val) else "N/A"
            except:
                temperature = "N/A"
        
        if 'humidity' in df.columns and not df.empty:
            try:
                val = df['humidity'].iloc[-1]
                humidity = f"{float(val):.0f}%" if pd.notna(val) else "N/A"
            except:
                humidity = "N/A"
        
        if 'soil_moisture' in df.columns and not df.empty:
            try:
                val = df['soil_moisture'].iloc[-1]
                soil_moisture = f"{float(val):.0f}%" if pd.notna(val) else "N/A"
            except:
                soil_moisture = "N/A"
        selected_rain = "N/A"
        try:
            rv = None
            if 'mua' in df.columns:
                rv = df['mua'].iloc[-1]
            elif 'rain' in df.columns:
                rv = df['rain'].iloc[-1]
            else:
                latest = fetch_pump_latest_data(pump_id, token)
                if latest and isinstance(latest, dict):
                    rv = latest.get('mua') or latest.get('rain')
            selected_rain = "Có mưa" if bool(rv) else "Không mưa"
        except Exception:
            selected_rain = "N/A"

        pump_last_on = "—"
        pump_last_off = "—"
        pump_run_duration = '—'
        try:
            mem_resp = get_pump_memory_logs(pump_id, token=token, limit=10, offset=0, date=today)
            items = mem_resp.get('data') if isinstance(mem_resp, dict) else mem_resp
            if items:
                if isinstance(items, dict):
                    items = [items]

                def _parse_ts(it):
                    for k in ('thoi_gian_bat', 'thoi_gian_on', 'thoi_gian_tat', 'thoi_gian_off'):
                        v = it.get(k)
                        if v:
                            try:
                                return pd.to_datetime(v, utc=True)
                            except Exception:
                                try:
                                    return pd.to_datetime(v)
                                except Exception:
                                    continue
                    return pd.NaT

                try:
                    items_sorted = sorted(items, key=lambda it: _parse_ts(it) or pd.NaT, reverse=True)
                    last_item = items_sorted[0]
                except Exception:
                    last_item = items[0] if isinstance(items, list) and len(items) > 0 else items

                bat_ts = last_item.get('thoi_gian_bat') or last_item.get('thoi_gian_on')
                tat_ts = last_item.get('thoi_gian_tat') or last_item.get('thoi_gian_off')
                pump_last_on = format_display_time(bat_ts) if bat_ts else "—"
                pump_last_off = format_display_time(tat_ts) if tat_ts else "—"

                try:
                    if bat_ts and tat_ts:
                        try:
                            bat_dt = pd.to_datetime(bat_ts, utc=True)
                        except Exception:
                            bat_dt = pd.to_datetime(bat_ts)
                        try:
                            tat_dt = pd.to_datetime(tat_ts, utc=True)
                        except Exception:
                            tat_dt = pd.to_datetime(tat_ts)

                        try:
                            if getattr(bat_dt, 'tzinfo', None) is None:
                                bat_dt = bat_dt.tz_localize('Asia/Bangkok')
                            else:
                                bat_dt = bat_dt.tz_convert('Asia/Bangkok')
                        except Exception:
                            pass
                        try:
                            if getattr(tat_dt, 'tzinfo', None) is None:
                                tat_dt = tat_dt.tz_localize('Asia/Bangkok')
                            else:
                                tat_dt = tat_dt.tz_convert('Asia/Bangkok')
                        except Exception:
                            pass

                        delta = (tat_dt - bat_dt)
                        try:
                            total_seconds = int(delta.total_seconds())
                        except Exception:
                            total_seconds = None

                        if total_seconds is not None and total_seconds >= 0:
                            h = total_seconds // 3600
                            m = (total_seconds % 3600) // 60
                            s = total_seconds % 60
                            if h > 0:
                                pump_run_duration = f"{h}giờ {m}ph {s}giây"
                            elif m > 0:
                                pump_run_duration = f"{m}ph {s}giây"
                            else:
                                pump_run_duration = f"{s}giây"
                        else:
                            pump_run_duration = '—'
                except Exception:
                    pump_run_duration = '—'
        except Exception:
            pump_last_on = "—"
            pump_last_off = "—"
            pump_run_duration = '—'

        return (
            title,
            badge_text,
            badge_class,
            flow_rate_figure,
            temperature_figure,
            humidity_figure,
            soil_moisture_figure,
            flow_rate,
            temperature,
            humidity,
            soil_moisture,
            selected_rain,
            pump_last_on,
            pump_last_off,
            pump_run_duration,
        )
    
    except Exception as e:
        print(f"Error in update_pump_details: {e}")
        import traceback
        traceback.print_exc()
        
        empty_figure = {
            'data': [go.Scatter(x=[], y=[], mode='lines')],
            'layout': go.Layout(
                xaxis={'title': 'Thời Gian'},
                yaxis={'title': 'Value'},
                plot_bgcolor='white',
                paper_bgcolor='white',
            )
        }
        return (
            "Chi Tiết Máy Bơm",
            "Lỗi",
            "badge badge-error ms-2",
            empty_figure,
            empty_figure,
            empty_figure,
            empty_figure,
            "Lỗi",  # flow rate value
            "Lỗi",  # temperature value
            "Lỗi",  # humidity value
            "Lỗi",  # soil moisture value
            "Lỗi",  # rain value
            "—",    # last on time
            "—",    # last off time
            "—"     # run duration
        )

@callback(
    [
        Output('user-name', 'children'),
        Output('user-role', 'children'),
        Output('user-status', 'children'),
        Output('user-last-login', 'children'),
    ],
    [
        Input('interval-component', 'n_intervals'),
        Input('url', 'pathname'),
        Input('session-store', 'modified_timestamp'),
    ],
    [
        State('session-store', 'data')
    ]
)
def update_user_info(n, pathname, session_modified, session):
    if pathname not in ('', '/', None):
        raise PreventUpdate
    
    token = None
    user_name = None
    if session and isinstance(session, dict):
        token = session.get('token')
        user_name = session.get('username')
    
    if not user_name or not token:
        return ("Không xác định", "Người dùng", "N/A", "N/A")
    
    try:
        user_data = get_user(user_name, token)
        
        if not user_data:
            return ("Không xác định", "Người dùng", "N/A", "N/A")
        
        name = user_data.get('ho_ten', 'Không xác định')
        role = user_data.get('vai_tro', 'Người dùng')
        status = user_data.get('trang_thai')
        last_login = user_data.get('dang_nhap_lan_cuoi')
        
        if isinstance(status, bool):
            status_text = "Đang hoạt động" if status else "Ngừng hoạt động"
        else:
            status_text = "N/A"
        
        last_login_text = format_display_time(last_login) if last_login else "N/A"
        
        return (
            name,
            role,
            status_text,
            last_login_text,
        )
    except Exception as e:
        print(f"Error fetching user info: {e}")
        import traceback
        traceback.print_exc()
        return ("Không xác định", "N/A", "N/A")

@callback(
    [
        Output('control-selected-pump-name', 'children'),
        Output('pump-start-btn', 'disabled'),
        Output('pump-stop-btn', 'disabled'),
        Output('pump-mode-select', 'value'),
    ],
    [
        Input('selected-pump-store', 'data'),
        Input('interval-component', 'n_intervals'),
    ],
        State('session-store', 'data'),
        State('url', 'pathname')
)
def update_pump_control_panel(selected_pump, n_intervals, session, pathname):
    """Refresh control panel state, button availability, and mode selection."""
    if pathname and not (pathname == '/' or pathname.startswith('/pump')):
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update

    if not selected_pump or not selected_pump.get('ma_may_bom'):
        return ("Chưa chọn máy bơm", True, True, None)

    try:
        pump_id = selected_pump.get('ma_may_bom')
        token = session.get('token') if session else None

        pump_info = get_pump(pump_id, token)
        if not pump_info:
            pump_name = selected_pump.get('ten_may_bom', 'Máy Bơm Nước Chính')
            return (pump_name, True, True, None)

        pump_name = pump_info.get('ten_may_bom', 'Máy Bơm Nước Chính')
        status = bool(pump_info.get('trang_thai', False))
        mode = pump_info.get('che_do', 0)

        if not isinstance(mode, int):
            mode = 0

        mode_value = mode

        if mode == 2:
            return (pump_name, True, True, mode_value)

        start_disabled = status  # disable start when already running
        stop_disabled = not status  # disable stop when already stopped

        return (pump_name, start_disabled, stop_disabled, mode_value)

    except Exception as e:
        print(f"Error updating pump control panel: {e}")
        pump_name = selected_pump.get('ten_may_bom', 'Máy Bơm Nước Chính')
        return (pump_name, True, True, None)

@callback(
    Output('pump-start-btn', 'n_clicks'),
    Input('pump-start-btn', 'n_clicks'),
    State('selected-pump-store', 'data'),
    State('session-store', 'data'),
    prevent_initial_call=True
)
def handle_pump_start(n_clicks, selected_pump, session):
    """Handle pump start button click - set trang_thai to True (enabled)."""
    if not selected_pump or not selected_pump.get('ma_may_bom'):
        return 0
    
    try:
        pump_id = selected_pump.get('ma_may_bom')
        token = session.get('token') if session else None
        
        pump_info = get_pump(pump_id, token)
        if not pump_info:
            print(f"Không thể lấy thông tin máy bơm {pump_id}")
            return n_clicks
        
        payload = {
            'ten_may_bom': pump_info.get('ten_may_bom', ''),
            'mo_ta': pump_info.get('mo_ta', ''),
            'ma_iot_lk': pump_info.get('ma_iot_lk', ''),
            'che_do': int(pump_info.get('che_do', 0)),
            'trang_thai': True  # Set to True (on)
        }
        
        success, message = update_pump(pump_id, payload, token=token)
        if success:
            print(f"Máy bơm {pump_id} bắt đầu thành công")
        else:
            print(f"Lỗi bắt đầu máy bơm: {message}")
    except Exception as e:
        print(f"Error starting pump: {e}")
        import traceback
        traceback.print_exc()
    
    return n_clicks

@callback(
    Output('pump-stop-btn', 'n_clicks'),
    Input('pump-stop-btn', 'n_clicks'),
    State('selected-pump-store', 'data'),
    State('session-store', 'data'),
    prevent_initial_call=True
)
def handle_pump_stop(n_clicks, selected_pump, session):
    """Handle pump stop button click - set trang_thai to False (disabled)."""
    if not selected_pump or not selected_pump.get('ma_may_bom'):
        return 0
    
    try:
        pump_id = selected_pump.get('ma_may_bom')
        token = session.get('token') if session else None
        
        pump_info = get_pump(pump_id, token)
        if not pump_info:
            print(f"Không thể lấy thông tin máy bơm {pump_id}")
            return n_clicks
        
        payload = {
            'ten_may_bom': pump_info.get('ten_may_bom', ''),
            'mo_ta': pump_info.get('mo_ta', ''),
            'ma_iot_lk': pump_info.get('ma_iot_lk', ''),
            'che_do': int(pump_info.get('che_do', 0)),
            'trang_thai': False  # Set to False (off)
        }
        
        success, message = update_pump(pump_id, payload, token=token)
        if success:
            print(f"Máy bơm {pump_id} dừng thành công")
        else:
            print(f"Lỗi dừng máy bơm: {message}")
    except Exception as e:
        print(f"Error stopping pump: {e}")
        import traceback
        traceback.print_exc()
    
    return n_clicks

@callback(
    Output('pump-mode-refresh', 'data'),
    Input('pump-mode-select', 'value'),
    State('selected-pump-store', 'data'),
    State('session-store', 'data'),
    State('pump-mode-refresh', 'data'),
    prevent_initial_call=True
)
def handle_mode_selection(value, selected_pump, session, current_store):
    """Persist mode changes and signal downstream updates."""
    default_store = current_store if isinstance(current_store, dict) else {'mode': None, 'ts': None}

    if not selected_pump or not selected_pump.get('ma_may_bom'):
        return default_store

    try:
        token = session.get('token') if session else None
        pump_id = selected_pump.get('ma_may_bom')
        pump_info = get_pump(pump_id, token)
        if not pump_info:
            print(f"✗ Không thể lấy thông tin máy bơm {pump_id}")
            return default_store

        store_mode = default_store.get('mode') if isinstance(default_store, dict) else None

        api_mode = pump_info.get('che_do', 0)
        if not isinstance(api_mode, int):
            api_mode = None

        if value is None:
            if api_mode is None:
                if store_mode is None:
                    return dash.no_update
                return {'mode': None, 'ts': datetime.utcnow().isoformat()}
            if store_mode == api_mode:
                return dash.no_update
            return {'mode': api_mode, 'ts': datetime.utcnow().isoformat()}

        try:
            new_mode = int(value)
        except (ValueError, TypeError):
            new_mode = api_mode

        if new_mode is None:
            if store_mode is None:
                return dash.no_update
            return {'mode': None, 'ts': datetime.utcnow().isoformat()}

        if store_mode == new_mode and api_mode == new_mode:
            return dash.no_update

        if new_mode == api_mode:
            if store_mode == new_mode:
                return dash.no_update
            return {'mode': new_mode, 'ts': datetime.utcnow().isoformat()}

        payload = {
            'ten_may_bom': pump_info.get('ten_may_bom', ''),
            'mo_ta': pump_info.get('mo_ta', ''),
            'ma_iot_lk': pump_info.get('ma_iot_lk', ''),
            'che_do': new_mode,
            'trang_thai': bool(pump_info.get('trang_thai', False))
        }

        if new_mode == 2:
            payload['trang_thai'] = False

        success, message = update_pump(pump_id, payload, token=token)
        if not success:
            # print(f"✗ Lỗi cập nhật chế độ: {message}")
            fallback_mode = pump_info.get('che_do', None)
            fallback_mode = fallback_mode if isinstance(fallback_mode, int) else None
            return {'mode': fallback_mode, 'ts': datetime.utcnow().isoformat()}

        mode_name = {0: 'thủ công', 1: 'tự động', 2: 'bảo trì'}.get(new_mode, str(new_mode))
        # print(f"✓ Máy bơm {pump_id} chuyển sang chế độ {mode_name}")
        return {'mode': new_mode, 'ts': datetime.utcnow().isoformat()}

    except Exception as e:
        print(f"Error updating pump mode: {e}")
        import traceback
        traceback.print_exc()
        return default_store