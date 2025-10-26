from dash import html, dcc, callback, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from components.navbar import create_navbar
from components.weather_widget import create_weather_widget
from dash.exceptions import PreventUpdate
import requests
import json
from api.sensor_data import get_data_by_date
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

def fetch_sensor_data():
    try:
        token = dash.callback_context.states.get('session-store.data', {}).get('token')
        
        if not token:
            print("No authentication token found")
            return create_empty_dataframe()
        
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

empty_df = create_empty_dataframe()
df = pd.DataFrame({
    'date': [],
    'flow_rate': [],
    'soil_moisture': [],
    'temperature': [],
    'humidity': [],
    'rain': [],
    'pulse_count': [],
    'total_volume': [],
    'notes': []
})

layout = html.Div([
    create_navbar(is_authenticated=False),
    
    dbc.Container([
        dbc.Row([
            dbc.Col([
                create_weather_widget()
            ], width=12)
        ], className="mb-5"),
        
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.I(className="fas fa-tint fa-3x text-primary mb-3"),
                            html.H3(id='flow-rate', children=f"{df['flow_rate'].iloc[-1]:.1f} L/s" if not df.empty else "N/A", className="mb-2"),
                            html.P("Lưu lượng hiện tại", className="text-muted mb-0")
                        ], className="text-center")
                    ])
                ], className="shadow-sm stat-card")
            ], md=3, sm=6, className="mb-4"),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.I(className="fas fa-seedling fa-3x text-success mb-3"),
                            html.H3(id='soil-moisture', children=f"{df['soil_moisture'].iloc[-1]:.1f}%" if not df.empty else "N/A", className="mb-2"),
                            html.P("Độ ẩm đất", className="text-muted mb-0")
                        ], className="text-center")
                    ])
                ], className="shadow-sm stat-card")
            ], md=3, sm=6, className="mb-4"),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.I(className="fas fa-temperature-half fa-3x text-warning mb-3"),
                            html.H3(id='temperature', children=f"{df['temperature'].iloc[-1]:.1f}°C" if not df.empty else "N/A", className="mb-2"),
                            html.P("Nhiệt độ", className="text-muted mb-0")
                        ], className="text-center")
                    ])
                ], className="shadow-sm stat-card")
            ], md=3, sm=6, className="mb-4"),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.I(className="fas fa-droplet fa-3x text-info mb-3"),
                            html.H3(id='humidity', children=f"{df['humidity'].iloc[-1]:.1f}%" if not df.empty else "N/A", className="mb-2"),
                            html.P("Độ ẩm không khí", className="text-muted mb-0")
                        ], className="text-center")
                    ])
                ], className="shadow-sm stat-card")
            ], md=3, sm=6, className="mb-4"),
        ]),
        
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5([
                            html.I(className="fas fa-chart-area me-2"),
                            "Lưu Lượng Nước Theo Thời Gian"
                        ], className="mb-0")
                    ]),
                    dbc.CardBody([
                        dcc.Graph(
                            id='flow-rate-chart',
                            figure={
                                'data': [
                                    go.Scatter(
                                        x=df['date'] if not df.empty else [],
                                        y=df['flow_rate'] if not df.empty else [],
                                        mode='lines',
                                        name='Lưu lượng',
                                        line=dict(color='#1f77b4', width=3),
                                        fill='tozeroy',
                                        fillcolor='rgba(31, 119, 180, 0.2)'
                                    )
                                ],
                                'layout': go.Layout(
                                                            xaxis={
                                                                'title': 'Thời gian',
                                                                'type': 'date',
                                                                'tickformat': '%H:%M\n%d/%m/%Y',
                                                                'gridcolor': '#f0f0f0',
                                                                'rangeslider': {'visible': True}
                                                            },
                                    yaxis={'title': 'Lưu lượng (L/s)', 'gridcolor': '#f0f0f0'},
                                    hovermode='x unified',
                                    plot_bgcolor='white',
                                    paper_bgcolor='white',
                                    margin=dict(l=50, r=20, t=20, b=50)
                                )
                            },
                            config={'displayModeBar': True, 'scrollZoom': True}
                        )
                    ])
                ], className="shadow-sm mb-4")
            ], md=12),
            
        #     dbc.Col([
        #         dbc.Card([
        #             dbc.CardHeader([
        #                 html.H5([
        #                     html.I(className="fas fa-chart-pie me-2"),
        #                     "Phân Tích Dữ Liệu"
        #                 ], className="mb-0")
        #             ]),
        #             dbc.CardBody([
        #                 dcc.Graph(
        #                     id='distribution-chart',
        #                     figure={
        #                         'data': [
        #                             go.Box(
        #                                 y=df['flow_rate'],
        #                                 name='Lưu lượng',
        #                                 marker=dict(color='#1f77b4'),
        #                                 boxmean='sd'
        #                             )
        #                         ],
        #                         'layout': go.Layout(
        #                             yaxis={'title': 'L/s', 'gridcolor': '#f0f0f0'},
        #                             plot_bgcolor='white',
        #                             paper_bgcolor='white',
        #                             margin=dict(l=50, r=20, t=20, b=50),
        #                             showlegend=False
        #                         )
        #                     },
        #                     config={'displayModeBar': False}
        #                 )
        #             ])
        #         ], className="shadow-sm mb-4")
        #     ], md=4),
        ]),
        
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5([
                            html.I(className="fas fa-chart-line me-2"),
                            "Tổng Quan Các Thông Số"
                        ], className="mb-0")
                    ]),
                    dbc.CardBody([
                        dcc.Graph(
                            id='multi-param-chart',
                            figure={
                                'data': [
                                    go.Scatter(
                                        x=df['date'].iloc[-30:] if not df.empty else [],
                                        y=df['flow_rate'].iloc[-30:] if not df.empty else [],
                                        mode='lines+markers',
                                        name='Lưu lượng (L/s)',
                                        line=dict(color='#1f77b4', width=2),
                                        marker=dict(size=6)
                                    ),
                                    go.Scatter(
                                        x=df['date'].iloc[-30:] if not df.empty else [],
                                        y=df['soil_moisture'].iloc[-30:] if not df.empty else [],
                                        mode='lines+markers',
                                        name='Độ ẩm đất (%)',
                                        line=dict(color='#2ca02c', width=2),
                                        marker=dict(size=6),
                                        yaxis='y2'
                                    ),
                                    go.Scatter(
                                        x=df['date'].iloc[-30:] if not df.empty else [],
                                        y=df['temperature'].iloc[-30:] if not df.empty else [],
                                        mode='lines+markers',
                                        name='Nhiệt độ (°C)',
                                        line=dict(color='#ff7f0e', width=2),
                                        marker=dict(size=6),
                                        yaxis='y3'
                                    ),
                                    go.Scatter(
                                        x=df['date'].iloc[-30:] if not df.empty else [],
                                        y=df['humidity'].iloc[-30:] if not df.empty else [],
                                        mode='lines+markers',
                                        name='Độ ẩm không khí (%)',
                                        line=dict(color='#9467bd', width=2),
                                        marker=dict(size=6),
                                        yaxis='y4'
                                    )
                                ],
                                'layout': go.Layout(
                                xaxis={'title': 'Thời gian (30 mẫu gần nhất)', 'type': 'date', 'tickformat': '%d/%m %H:%M', 'gridcolor': '#f0f0f0'},
                                    yaxis={'title': 'Lưu lượng (L/s)', 'gridcolor': '#f0f0f0'},
                                    yaxis2={'title': 'Độ ẩm đất (%)', 'overlaying': 'y', 'side': 'right'},
                                    yaxis3={'title': 'Nhiệt độ (°C)', 'overlaying': 'y', 'side': 'right', 'position': 0.95},
                                    yaxis4={'title': 'Độ ẩm KK (%)', 'overlaying': 'y', 'side': 'right', 'position': 0.85},
                                    hovermode='x unified',
                                    plot_bgcolor='white',
                                    paper_bgcolor='white',
                                    margin=dict(l=50, r=100, t=20, b=50),
                                    legend=dict(
                                        orientation="h",
                                        yanchor="bottom",
                                        y=1.02,
                                        xanchor="right",
                                        x=1
                                    )
                                )
                            },
                            config={'displayModeBar': True, 'scrollZoom': True}
                        )
                    ])
                ], className="shadow-sm mb-4")
            ], width=12)
        ]),
        
        dbc.Row([
            dbc.Col([
                html.H2("Tính Năng Nổi Bật", className="text-center mb-5 mt-4")
            ], width=12)
        ]),
        
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.I(className="fas fa-brain fa-3x text-primary mb-3"),
                        html.H4("Mô Hình Máy Học Dự Đoán", className="mb-3"),
                        html.P("Sử dụng máy học để dự đoán lưu lượng nước chính xác",
                                className="text-muted")
                    ], className="text-center")
                ], className="shadow-sm feature-card h-100")
            ], md=4, className="mb-4"),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.I(className="fas fa-clock fa-3x text-success mb-3"),
                        html.H4("Dữ liệu thời gian thực", className="mb-3"),
                        html.P("Giám sát dữ liệu theo thời gian thực với độ trễ tối thiểu",
                            className="text-muted")
                    ], className="text-center")
                ], className="shadow-sm feature-card h-100")
            ], md=4, className="mb-4"),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.I(className="fas fa-bell fa-3x text-warning mb-3"),
                        html.H4("Cảnh Báo", className="mb-3"),
                        html.P("Thông báo ngay khi phát hiện bất thường trong hệ thống",
                            className="text-muted")
                    ], className="text-center")
                ], className="shadow-sm feature-card h-100")
            ], md=4, className="mb-4"),
        ], className="mb-5"),
        
    ], fluid=True, className="px-4"),
    
    dcc.Interval(
        id='interval-component',
        interval=5*1000,
        n_intervals=0
    )
], className="page-container")


def fetch_weather_from_hash(hash_value):
    if not hash_value:
        raise PreventUpdate

    try:
        s = hash_value.lstrip('#')
        parts = dict([p.split('=') for p in s.split('&') if '=' in p])
        lat = float(parts.get('lat'))
        lon = float(parts.get('lon'))
    except Exception:
        raise PreventUpdate

    try:
        url = 'https://api.open-meteo.com/v1/forecast'
        params = {
            'latitude': lat,
            'longitude': lon,
            'current_weather': True,
            'hourly': 'relativehumidity_2m,pressure_msl,precipitation',
            'daily': 'weathercode,temperature_2m_max,temperature_2m_min,precipitation_sum',
            'timezone': 'auto'
        }

        resp = requests.get(url, params=params, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        # print(data)

        try:
            geocode_url = 'https://geocoding-api.open-meteo.com/v1/reverse'
            gparams = {'latitude': lat, 'longitude': lon, 'name': True}
            gresp = requests.get(geocode_url, params=gparams, timeout=3)
            gresp.raise_for_status()
            gdata = gresp.json()
            if gdata.get('results') and len(gdata['results'])>0:
                data['place_name'] = gdata['results'][0].get('name')
                admin = gdata['results'][0].get('admin1')
                country = gdata['results'][0].get('country')
                if admin:
                    data['place_name'] += f', {admin}'
                if country:
                    data['place_name'] += f', {country}'
        except Exception:
            pass

        return data
    except Exception as e:
        return {'error': str(e)}
@callback(
    [
        Output('flow-rate-chart', 'figure'),
        Output('multi-param-chart', 'figure'),
        Output('flow-rate', 'children'),
        Output('soil-moisture', 'children'),
        Output('temperature', 'children'),
        Output('humidity', 'children'),
        Output('weather-location', 'children'),
        Output('weather-localtime', 'children'),
        Output('weather-temp', 'children'),
        Output('weather-desc', 'children'),
        Output('weather-sunrise', 'children'),
        Output('weather-sunset', 'children'),
        Output('weather-icon', 'className'),
        Output('stat-humidity', 'children'),
        Output('stat-pressure', 'children'),
        Output('weather-forecast', 'children'),
        Output('weather-updated', 'children'),
        Output('weather-container', 'className'),
        Output('weather-raw', 'children')
    ],
    [
        Input('interval-component', 'n_intervals'),
        Input('url', 'pathname'),
        Input('url', 'hash'),
        Input('session-store', 'modified_timestamp')
    ],
    [
        State('weather-store', 'data'),
        State('session-store', 'data')
    ]
)
def update_all(n, pathname, hash_value, session_modified, stored, session):
    if pathname not in ('', '/', None):
        raise PreventUpdate
    df = fetch_sensor_data()
    
    if df.empty:
        raise PreventUpdate
    
    flow_rate_figure = {
        'data': [
            go.Scatter(
                x=df['date'],
                y=df['flow_rate'],
                mode='lines',
                name='Lưu lượng',
                line=dict(color='#1f77b4', width=3),
                fill='tozeroy',
                fillcolor='rgba(31, 119, 180, 0.2)'
            )
        ],
        'layout': go.Layout(
            xaxis={
                'title': 'Thời gian',
                'gridcolor': '#f0f0f0',
                'rangeslider': {'visible': True}
            },
            yaxis={'title': 'Lưu lượng (L/s)', 'gridcolor': '#f0f0f0'},
            hovermode='x unified',
            plot_bgcolor='white',
            paper_bgcolor='white',
            margin=dict(l=50, r=20, t=20, b=50)
        )
    }
    
    multi_param_figure = {
        'data': [
            go.Scatter(
                x=df['date'].iloc[-30:],
                y=df['flow_rate'].iloc[-30:],
                mode='lines+markers',
                name='Lưu lượng (L/s)',
                line=dict(color='#1f77b4', width=2),
                marker=dict(size=6)
            ),
            go.Scatter(
                x=df['date'].iloc[-30:],
                y=df['soil_moisture'].iloc[-30:],
                mode='lines+markers',
                name='Độ ẩm đất (%)',
                line=dict(color='#2ca02c', width=2),
                marker=dict(size=6),
                yaxis='y2'
            ),
            go.Scatter(
                x=df['date'].iloc[-30:],
                y=df['temperature'].iloc[-30:],
                mode='lines+markers',
                name='Nhiệt độ (°C)',
                line=dict(color='#ff7f0e', width=2),
                marker=dict(size=6),
                yaxis='y3'
            ),
            go.Scatter(
                x=df['date'].iloc[-30:],
                y=df['humidity'].iloc[-30:],
                mode='lines+markers',
                name='Độ ẩm không khí (%)',
                line=dict(color='#9467bd', width=2),
                marker=dict(size=6),
                yaxis='y4'
            )
        ],
        'layout': go.Layout(
            xaxis={'title': 'Thời gian (30 mẫu gần nhất)', 'gridcolor': '#f0f0f0'},
            yaxis={'title': 'Lưu lượng (L/s)', 'gridcolor': '#f0f0f0'},
            yaxis2={'title': 'Độ ẩm đất (%)', 'overlaying': 'y', 'side': 'right'},
            yaxis3={'title': 'Nhiệt độ (°C)', 'overlaying': 'y', 'side': 'right', 'position': 0.95},
            yaxis4={'title': 'Độ ẩm KK (%)', 'overlaying': 'y', 'side': 'right', 'position': 0.85},
            hovermode='x unified',
            plot_bgcolor='white',
            paper_bgcolor='white',
            margin=dict(l=50, r=100, t=20, b=50),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
    }
    
    flow_rate = f"{df['flow_rate'].iloc[-1]:.1f} L/s" if not df.empty else "N/A"
    soil_moisture = f"{df['soil_moisture'].iloc[-1]:.1f}%" if not df.empty else "N/A"
    temperature = f"{df['temperature'].iloc[-1]:.1f}°C" if not df.empty else "N/A"
    humidity = f"{df['humidity'].iloc[-1]:.1f}%" if not df.empty else "N/A"
    
    try:
        if hash_value:
            store_data = fetch_weather_from_hash(hash_value)
        else:
            store_data = stored
        weather_data = render_weather(store_data, stored)
    except:
        weather_data = render_weather(None, stored)
    
    return (
        flow_rate_figure,  # flow-rate-chart
        multi_param_figure,  # multi-param-chart
        flow_rate,  # flow-rate
        soil_moisture,  # soil-moisture
        temperature,  # temperature
        humidity,  # humidity
        *weather_data  # weather components
    )

def render_weather(store_data, stored):
    default_container_class = 'text-start'

    def empty_response(msg=''):
        return (
            'Thời tiết địa phương',  # weather-location
            '',                     # weather-localtime
            '—',                    # weather-temp
            msg or 'Vui lòng cho phép truy cập vị trí để xem thời tiết.',  # weather-desc
            '—',                    # weather-sunrise (rain)
            '—',                    # weather-sunset (wind)
            'weather-icon',         # weather-icon className
            '—',                    # stat-humidity
            '—',                    # stat-pressure
            [],                     # weather-forecast
            '',                     # weather-updated
            default_container_class,
            ''
        )

    if not store_data:
        return empty_response()

    if isinstance(store_data, dict) and store_data.get('error'):
        return empty_response(f"Lỗi: {store_data.get('error')}")

    cw = store_data.get('current_weather') if isinstance(store_data, dict) else None
    if not cw:
        return empty_response('Không có dữ liệu thời tiết hiện tại.')

    temp = cw.get('temperature')
    wind = cw.get('windspeed')
    weather_code = cw.get('weathercode')
    time = cw.get('time')

    humidity = None
    pressure = None
    precip = None
    try:
        hourly = store_data.get('hourly', {})
        if hourly:
            times = hourly.get('time', [])
            if time in times:
                idx = times.index(time)
            else:
                idx = -1
            humidity = hourly.get('relativehumidity_2m', [None])[idx]
            pressure = hourly.get('pressure_msl', [None])[idx]
            precip = hourly.get('precipitation', [0])[idx]
    except Exception:
        humidity = None

    rain_out = f"{precip if precip is not None else '—'} mm" if precip is not None else "—"
    wind_out = f"{wind if wind is not None else '—'} km/h" if wind is not None else "—"

    wc_map = {
        0: 'Quang đãng',
        1: 'Ít mây',
        2: 'Mây rải rác',
        3: 'Râm',
        45: 'Sương mù',
        48: 'Sương khô',
        51: 'Mưa nhẹ',
        53: 'Mưa vừa',
        61: 'Mưa',
        71: 'Tuyết',
        80: 'Mưa rào'
    }

    forecast_items = []
    try:
        daily = store_data.get('daily', {})
        dates = daily.get('time', [])
        wcodes = daily.get('weathercode', [])
        tmax = daily.get('temperature_2m_max', [])
        tmin = daily.get('temperature_2m_min', [])
        psum = daily.get('precipitation_sum', [])
        length = min(7, len(dates))
        for i in range(length):
            d = dates[i]
            wc = wcodes[i] if i < len(wcodes) else None
            hi = tmax[i] if i < len(tmax) else None
            lo = tmin[i] if i < len(tmin) else None
            pd = psum[i] if i < len(psum) else None
            label = wc_map.get(wc, 'N/A')
            forecast_items.append({'date': d, 'label': label, 'hi': hi, 'lo': lo, 'precip': pd, 'code': wc})
    except Exception:
        forecast_items = []

    desc = wc_map.get(weather_code, f'Code {weather_code}')

    icon_class = 'sunny'
    container_variant = ''
    if weather_code in (61, 80, 51, 53):
        icon_class = 'rain'
        container_variant = 'rain'
    elif weather_code in (2,3,45,48):
        icon_class = 'cloudy'
        container_variant = 'cloudy'
    else:
        container_variant = 'sunny'

    place = store_data.get('place_name') if isinstance(store_data, dict) else None
    if not place:
        place = 'Vị trí của bạn'

    try:
        from datetime import datetime
        dt = datetime.fromisoformat(time)
        localtime_str = dt.strftime('%H:%M %d/%m/%Y')
    except Exception:
        localtime_str = time

    try:
        wind_dir_deg = cw.get('winddirection') if isinstance(cw, dict) else None
        if wind_dir_deg is None:
            wind_dir_deg = None
        wind_dir_label = ''
        if wind_dir_deg is not None:
            deg = int(wind_dir_deg) % 360
            dirs = ['Bắc','Bắc-Đông','Đông','Nam-Đông','Nam','Nam-Tây','Tây','Bắc-Tây']
            idx = int((deg + 22.5) // 45) % 8
            wind_dir_label = dirs[idx]
    except Exception:
        wind_dir_label = ''

    details = html.Div([
        html.H3(f"{temp}°C", className='mb-1'),
        html.P(f"{desc}", className='text-muted mb-1'),
        html.Div([html.Small(f"Gió: {wind} km/h"), html.Span(" • "), html.Small(f"Độ ẩm: {humidity if humidity is not None else '—'}%")], className='text-muted'),
    ])

    forecast_nodes = []
    for f in forecast_items:
        try:
            dd = datetime.fromisoformat(f['date']).strftime('%d/%m')
        except Exception:
            dd = f['date']
        forecast_nodes.append(html.Div([
            html.Div(dd, className='small text-muted'),
            html.Div(f['label'], className='small'),
            html.Div(f"{f.get('hi','—')}°C / {f.get('lo','—')}°C", className='fw-bold'),
            html.Div(f"{(f.get('precip') or 0)} mm", className='small text-muted')
        ], className='day'))

    updated = f"Cập nhật: {localtime_str}"

    location_out = place
    localtime_out = localtime_str
    temp_out = f"{temp}°C"
    
    desc_out = desc
    icon_class_out = f'weather-icon {icon_class}'

    stat_humidity_out = f"{humidity if humidity is not None else '—'} %"
    stat_pressure_out = f"{pressure if pressure is not None else '—'} hPa"

    forecast_out = forecast_nodes

    updated_out = updated

    container_class = f'text-start weather-{container_variant}'

    return (
        location_out,
        localtime_out,
        temp_out,
        desc_out,
        rain_out,
        wind_out,
        icon_class_out,
        stat_humidity_out,
        stat_pressure_out,
        forecast_out,
        updated_out,
        container_class,
        json.dumps(store_data, ensure_ascii=False, indent=2)
    )