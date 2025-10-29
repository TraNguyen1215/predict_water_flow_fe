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
from api.sensor_data import get_data_by_date, get_data_by_pump
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
        if isinstance(response, dict) and 'data' in response:
            return response['data']
        return []
    except Exception as e:
        print(f"Error fetching pump list: {e}")
        return []


def fetch_pump_latest_data(ma_may_bom, token=None):
    try:
        response = get_data_by_pump(ma_may_bom=ma_may_bom, limit=1, offset=0, token=token)
        if isinstance(response, dict) and 'data' in response:
            data = response['data']
            if data and isinstance(data, list) and len(data) > 0:
                return data[0]
        return None
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
                        html.H5("Thống Kê", className="mb-0")
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
                    ])
                ], className="stats-card", style={"padding": "12px"})
            ], lg=9, className="mb-4"),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5("Thông Tin Người Dùng", className="mb-0")
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
                ], className="operator-card")
            ], lg=3, className="mb-4"),
        ], className="mb-4"),
        
        dbc.Row([
            dbc.Col([
                html.H5("Chọn Máy Bơm", className="section-title mb-3")
            ], width="auto"),
            dbc.Col([
                html.A([
                    "Xem tất cả"
                ], href="/pump", className="view-all-link", style={"textDecoration": "none", "color": "#0d6efd", "fontWeight": "500"})
            ], width="auto", className="ms-auto d-flex align-items-center")
        ], className="mb-3 d-flex align-items-center"),
        
        html.Div(id='pump-list-container', children=[]),
        dcc.Store(id='home-pump-pagination-store', data={'current_page': 0}),
        dcc.Store(id='selected-pump-store', data={'ma_may_bom': None, 'ten_may_bom': 'Máy Bơm Nước Chính'}),
        
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.Div([
                            html.H5(id='pump-detail-title', children="Chi Tiết Máy Bơm - Máy Bơm Nước Chính", className="mb-0"),
                            html.Span(id='pump-detail-status', children="đang chạy", className="badge badge-running ms-2")
                        ], style={"display": "flex", "alignItems": "center"})
                    ]),
                    dbc.CardBody([
                        # First row: flow, soil moisture, humidity, temperature
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

                        # Second row: rain, last on, last off, run duration
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
                ], className="details-card mb-4")
            ], lg=8, className="mb-4"),

            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5("Điều Khiển Máy Bơm", className="mb-0")
                    ]),
                    dbc.CardBody([
                        html.Div([
                            html.Div([
                                html.Span("Máy bơm được chọn: ", className="text-muted"),
                                html.Strong("", id='control-selected-pump-name')
                            ], className="mb-3 pb-3", style={"borderBottom": "1px solid #e9ecef"}),
                            
                            html.H6("Trạng Thái Máy Bơm", className="mb-3"),
                            dbc.Row([
                                dbc.Col([
                                    dbc.Button([
                                        html.I(className="fas fa-play me-2"),
                                        "Bắt Đầu"
                                    ], color='success', className="w-100", id='pump-start-btn', disabled=True)
                                ], md=6),
                                dbc.Col([
                                    dbc.Button([
                                        html.I(className="fas fa-stop me-2"),
                                        "Dừng"
                                    ], color='danger', outline=True, className="w-100", id='pump-stop-btn', disabled=True)
                                ], md=6),
                            ], className="mb-4"),
                            
                            html.Hr(),
                            
                            html.Div([
                                html.H6("Chế Độ Tự Động", className="mb-3"),
                                dbc.Row([
                                    dbc.Col([
                                        html.Span("Tắt", className="me-2")
                                    ], width="auto"),
                                    dbc.Col([
                                        dbc.Checklist(
                                            options=[{"label": "", "value": 1}],
                                            value=[],
                                            id='auto-mode-toggle',
                                            switch=True,
                                            className="toggle-switch",
                                            inputStyle={"cursor": "not-allowed", "opacity": 0.5}
                                        )
                                    ], width="auto", id='auto-mode-toggle-col'),
                                    dbc.Col([
                                        html.Span("Bật", className="ms-2")
                                    ], width="auto"),
                                ], className="d-flex align-items-center mb-3"),
                            ], className="mb-4"),
                            
                            html.Hr(),
                            
                            html.Div([
                                dbc.Button([
                                    html.I(className="fas fa-tools me-2"),
                                    "Vào Chế Độ Bảo Trì"
                                ], color='warning', outline=True, className="w-100", id='maintenance-mode-btn', disabled=True)
                            ])
                        ])
                    ])
                ], className="operator-card")
            ], lg=4, className="mb-4")
        ]),

        # Charts are shown in a separate full-width row below details/control
        dbc.Row([
            dbc.Col([
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader([
                                html.H5([
                                    html.I(className="fas fa-chart-area me-2"),
                                    "Phân Tích Lưu Lượng"
                                ], className="mb-0")
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
                                html.H5([
                                    html.I(className="fas fa-temperature-high me-2"),
                                    "Nhiệt Độ"
                                ], className="mb-0")
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
                                html.H5([
                                    html.I(className="fas fa-droplets me-2"),
                                    "Độ Ẩm"
                                ], className="mb-0")
                            ]),
                            dbc.CardBody([
                                dcc.Graph(id='selected-humidity-chart', config={'displayModeBar': False})
                            ])
                        ], className="chart-card")
                    ], md=12, lg=6),
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader([
                                html.H5([
                                    html.I(className="fas fa-leaf me-2"),
                                    "Độ Ẩm Đất"
                                ], className="mb-0")
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
    
    running_count = 0
    sensor_count = 0
    for pump in pumps:
        status = pump.get('trang_thai', False)
        if status == True or status == 1:
            running_count += 1
    
    active_pumps_str = f"{running_count}/{len(pumps)}" if pumps else "0/0"
    
    try:
        sensors_response = list_sensors(limit=1000, offset=0, token=token)
        if isinstance(sensors_response, dict) and 'data' in sensors_response:
            sensors = sensors_response['data']
        else:
            sensors = sensors_response if isinstance(sensors_response, list) else []
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
        Input('home-pump-pagination-store', 'data'),
    ],
    [
        State('session-store', 'data')
    ]
)
def update_pump_list(n, pathname, session_modified, pagination_data, session):
    """Update pump list independently."""
    if pathname not in ('', '/', None):
        raise PreventUpdate
    
    token = None
    if session and isinstance(session, dict):
        token = session.get('token')
    
    pumps = fetch_pump_list(token)
    
    if not pumps:
        return [html.P("Không có máy bơm nào để hiển thị", className="text-center text-muted")]
    
    current_page = pagination_data.get('current_page', 0) if pagination_data else 0
    items_per_page = 4
    total_pumps = len(pumps)
    total_pages = (total_pumps + items_per_page - 1) // items_per_page if total_pumps > 0 else 1
    
    start_idx = current_page * items_per_page
    end_idx = start_idx + items_per_page
    page_pumps = pumps[start_idx:end_idx]
    
    pump_cards = []
    for pump in page_pumps:
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
        
        pump_card = dbc.Col([
            html.Div([
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
            ], id={'type': 'pump-card-btn', 'index': pump_id}, 
               n_clicks=0, style={"cursor": "pointer"})
        ], lg=3, md=6, className="mb-3")
        pump_cards.append(pump_card)
    
    pagination_controls = []
    if total_pages > 1:
        pagination_controls = [
            html.Div([
                dbc.ButtonGroup([
                    dbc.Button(
                        html.I(className="fas fa-chevron-left"),
                        id='pump-prev-btn',
                        disabled=(current_page == 0),
                        color='primary',
                        outline=True,
                        size='sm',
                        className="pump-nav-btn"
                    ),
                    dbc.Button(
                        f"{current_page + 1}/{total_pages}",
                        disabled=True,
                        color='secondary',
                        outline=True,
                        size='sm',
                        className="pump-page-indicator"
                    ),
                    dbc.Button(
                        html.I(className="fas fa-chevron-right"),
                        id='pump-next-btn',
                        disabled=(current_page >= total_pages - 1),
                        color='primary',
                        outline=True,
                        size='sm',
                        className="pump-nav-btn"
                    ),
                ], className="me-2"),
            ], style={"display": "flex", "alignItems": "center", "justifyContent": "center", "marginTop": "1rem"})
        ]
    
    pump_list_content = [
        dbc.Row(pump_cards, className="mb-3"),
        *pagination_controls
    ]
    
    return pump_list_content

@callback(
    Output('home-pump-pagination-store', 'data'),
    [
        Input('pump-next-btn', 'n_clicks'),
        Input('pump-prev-btn', 'n_clicks'),
    ],
    [
        State('home-pump-pagination-store', 'data')
    ],
    prevent_initial_call=True
)
def update_pagination(next_clicks, prev_clicks, data):
    """Handle pagination for pump list."""
    if not data:
        data = {'current_page': 0}
    
    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    current_page = data.get('current_page', 0)
    
    if button_id == 'pump-next-btn':
        current_page += 1
    elif button_id == 'pump-prev-btn':
        current_page = max(0, current_page - 1)
    
    return {'current_page': current_page}

@callback(
    Output('selected-pump-store', 'data'),
    [
        Input({'type': 'pump-card-btn', 'index': dash.ALL}, 'n_clicks'),
    ],
    prevent_initial_call=True
)
def select_pump(n_clicks):
    if not n_clicks or sum(n_clicks) == 0:
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
        response_data = get_data_by_pump(ma_may_bom=pump_id, limit=1000, offset=0, token=token)
        
        if isinstance(response_data, dict) and 'data' in response_data:
            data = response_data['data']
        else:
            data = response_data if isinstance(response_data, list) else []
        
        if not data:
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
                "N/A",  # rain
                "—",    # last on
                "—",    # last off
            )
        
        df = pd.DataFrame.from_records(data)
        
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
            
            # Convert numeric columns
            for col in ['flow_rate', 'soil_moisture', 'temperature', 'humidity']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
        
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
        
        # Safe access to dataframe values
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
        # Determine rain status from sensor data (mua/rain) or latest pump data
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

                # Compute run duration string (thoi_gian_chay)
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

                        # Try to set/convert timezone to Asia/Bangkok
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
            "Lỗi",
            "Lỗi",
            "Lỗi",
            "Lỗi",
            "Lỗi",
            "Lỗi",
            "Lỗi",
            "Lỗi",
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
        Output('auto-mode-toggle-col', 'style'),
        Output('maintenance-mode-btn', 'disabled'),
    ],
    [
        Input('selected-pump-store', 'data'),
        Input('interval-component', 'n_intervals'),
    ],
    State('session-store', 'data')
)
def update_pump_control_panel(selected_pump, n_intervals, session):
    """Update pump control panel based on selected pump."""
    if not selected_pump or not selected_pump.get('ma_may_bom'):
        disabled_style = {"opacity": 0.5, "pointerEvents": "none"}
        return ("Chưa chọn máy bơm", True, True, disabled_style, True)
    
    try:
        pump_id = selected_pump.get('ma_may_bom')
        token = session.get('token') if session else None
        
        pump_info = get_pump(pump_id, token)
        if not pump_info:
            pump_name = selected_pump.get('ten_may_bom', 'Máy Bơm Nước Chính')
            enabled_style = {"opacity": 1, "pointerEvents": "auto"}
            return (pump_name, False, False, enabled_style, False)
        
        pump_name = pump_info.get('ten_may_bom', 'Máy Bơm Nước Chính')
        mode = pump_info.get('che_do', 0)
        
        if mode == 2:
            disabled_style = {"opacity": 0.5, "pointerEvents": "none"}
            return (pump_name, True, True, disabled_style, False)
        
        enabled_style = {"opacity": 1, "pointerEvents": "auto"}
        return (pump_name, False, False, enabled_style, False)
    
    except Exception as e:
        print(f"Error updating pump control panel: {e}")
        pump_name = selected_pump.get('ten_may_bom', 'Máy Bơm Nước Chính')
        enabled_style = {"opacity": 1, "pointerEvents": "auto"}
        return (pump_name, False, False, enabled_style, False)

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
        
        # Get current pump info
        pump_info = get_pump(pump_id, token)
        if not pump_info:
            print(f"✗ Không thể lấy thông tin máy bơm {pump_id}")
            return n_clicks
        
        # Prepare payload with all required fields
        payload = {
            'ten_may_bom': pump_info.get('ten_may_bom', ''),
            'mo_ta': pump_info.get('mo_ta', ''),
            'ma_iot_lk': pump_info.get('ma_iot_lk', ''),
            'che_do': int(pump_info.get('che_do', 0)),
            'trang_thai': True  # Set to True (on)
        }
        
        success, message = update_pump(pump_id, payload, token=token)
        if success:
            print(f"✓ Máy bơm {pump_id} bắt đầu thành công")
        else:
            print(f"✗ Lỗi bắt đầu máy bơm: {message}")
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
        
        # Get current pump info
        pump_info = get_pump(pump_id, token)
        if not pump_info:
            print(f"✗ Không thể lấy thông tin máy bơm {pump_id}")
            return n_clicks
        
        # Prepare payload with all required fields
        payload = {
            'ten_may_bom': pump_info.get('ten_may_bom', ''),
            'mo_ta': pump_info.get('mo_ta', ''),
            'ma_iot_lk': pump_info.get('ma_iot_lk', ''),
            'che_do': int(pump_info.get('che_do', 0)),
            'trang_thai': False  # Set to False (off)
        }
        
        success, message = update_pump(pump_id, payload, token=token)
        if success:
            print(f"✓ Máy bơm {pump_id} dừng thành công")
        else:
            print(f"✗ Lỗi dừng máy bơm: {message}")
    except Exception as e:
        print(f"Error stopping pump: {e}")
        import traceback
        traceback.print_exc()
    
    return n_clicks

@callback(
    Output('auto-mode-toggle', 'value'),
    Input('auto-mode-toggle', 'value'),
    State('selected-pump-store', 'data'),
    State('session-store', 'data'),
    prevent_initial_call=True
)
def handle_auto_mode(value, selected_pump, session):
    """Handle auto mode toggle - set che_do to 1 when enabled."""
    if not selected_pump or not selected_pump.get('ma_may_bom'):
        return []
    
    try:
        pump_id = selected_pump.get('ma_may_bom')
        token = session.get('token') if session else None
        
        # Get current pump info
        pump_info = get_pump(pump_id, token)
        if not pump_info:
            print(f"✗ Không thể lấy thông tin máy bơm {pump_id}")
            return value
        
        # Determine the new mode
        new_mode = 1 if 1 in value else 0
        
        # Prepare payload with all required fields
        payload = {
            'ten_may_bom': pump_info.get('ten_may_bom', ''),
            'mo_ta': pump_info.get('mo_ta', ''),
            'ma_iot_lk': pump_info.get('ma_iot_lk', ''),
            'che_do': new_mode,
            'trang_thai': bool(pump_info.get('trang_thai', False))
        }
        
        success, message = update_pump(pump_id, payload, token=token)
        if success:
            if new_mode == 1:
                print(f"✓ Máy bơm {pump_id} bật chế độ tự động thành công")
            else:
                print(f"✓ Máy bơm {pump_id} tắt chế độ tự động thành công")
        else:
            print(f"✗ Lỗi cập nhật chế độ: {message}")
    except Exception as e:
        print(f"Error toggling auto mode: {e}")
        import traceback
        traceback.print_exc()
    
    return value

@callback(
    Output('maintenance-mode-btn', 'n_clicks'),
    Input('maintenance-mode-btn', 'n_clicks'),
    State('selected-pump-store', 'data'),
    State('session-store', 'data'),
    prevent_initial_call=True
)
def handle_maintenance_mode(n_clicks, selected_pump, session):
    """Handle maintenance mode button click - toggle che_do 2."""
    if not selected_pump or not selected_pump.get('ma_may_bom'):
        return 0
    
    try:
        pump_id = selected_pump.get('ma_may_bom')
        token = session.get('token') if session else None
        
        # Get current pump info
        pump_info = get_pump(pump_id, token)
        if not pump_info:
            print(f"✗ Không thể lấy thông tin máy bơm {pump_id}")
            return n_clicks
        
        current_mode = pump_info.get('che_do', 0)
        
        # If already in maintenance mode, exit and switch to auto mode with status off
        if current_mode == 2:
            payload = {
                'ten_may_bom': pump_info.get('ten_may_bom', ''),
                'mo_ta': pump_info.get('mo_ta', ''),
                'ma_iot_lk': pump_info.get('ma_iot_lk', ''),
                'che_do': 1,  # Switch to auto mode
                'trang_thai': False  # Turn off
            }
            success, message = update_pump(pump_id, payload, token=token)
            if success:
                print(f"✓ Máy bơm {pump_id} thoát chế độ bảo trì thành công (chuyển sang tự động, tắt)")
            else:
                print(f"✗ Lỗi thoát chế độ bảo trì: {message}")
        else:
            # Enter maintenance mode
            payload = {
                'ten_may_bom': pump_info.get('ten_may_bom', ''),
                'mo_ta': pump_info.get('mo_ta', ''),
                'ma_iot_lk': pump_info.get('ma_iot_lk', ''),
                'che_do': 2,  # Set to maintenance mode
                'trang_thai': bool(pump_info.get('trang_thai', False))
            }
            success, message = update_pump(pump_id, payload, token=token)
            if success:
                print(f"✓ Máy bơm {pump_id} vào chế độ bảo trì thành công")
            else:
                print(f"✗ Lỗi vào chế độ bảo trì: {message}")
    except Exception as e:
        print(f"Error toggling maintenance mode: {e}")
        import traceback
        traceback.print_exc()
    
    return n_clicks