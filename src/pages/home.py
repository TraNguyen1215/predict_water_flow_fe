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

def generate_sample_data():
    dates = pd.date_range(start='2025-01-01', end='2025-10-16', freq='D')
    np.random.seed(42)
    flow_rate = 100 + np.cumsum(np.random.randn(len(dates)) * 2)
    pressure = 50 + np.cumsum(np.random.randn(len(dates)) * 0.5)
    temperature = 20 + 5 * np.sin(np.arange(len(dates)) * 2 * np.pi / 365)
    
    df = pd.DataFrame({
        'date': dates,
        'flow_rate': flow_rate,
        'pressure': pressure,
        'temperature': temperature
    })
    return df

df = generate_sample_data()

# Create layout
layout = html.Div([
    create_navbar(is_authenticated=False),
    
    dbc.Container([
        dbc.Row([
            dbc.Col([
                create_weather_widget()
            ], width=12)
        ], className="mb-5"),
        
        # Statistics Cards
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.I(className="fas fa-tint fa-3x text-primary mb-3"),
                            html.H3(f"{df['flow_rate'].iloc[-1]:.1f} L/s", className="mb-2"),
                            html.P("Lưu lượng hiện tại", className="text-muted mb-0")
                        ], className="text-center")
                    ])
                ], className="shadow-sm stat-card")
            ], md=3, sm=6, className="mb-4"),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.I(className="fas fa-gauge-high fa-3x text-success mb-3"),
                            html.H3(f"{df['pressure'].iloc[-1]:.1f} Bar", className="mb-2"),
                            html.P("Áp suất", className="text-muted mb-0")
                        ], className="text-center")
                    ])
                ], className="shadow-sm stat-card")
            ], md=3, sm=6, className="mb-4"),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.I(className="fas fa-temperature-half fa-3x text-warning mb-3"),
                            html.H3(f"{df['temperature'].iloc[-1]:.1f}°C", className="mb-2"),
                            html.P("Nhiệt độ", className="text-muted mb-0")
                        ], className="text-center")
                    ])
                ], className="shadow-sm stat-card")
            ], md=3, sm=6, className="mb-4"),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.I(className="fas fa-check-circle fa-3x text-info mb-3"),
                            html.H3("98.5%", className="mb-2"),
                            html.P("Độ chính xác", className="text-muted mb-0")
                        ], className="text-center")
                    ])
                ], className="shadow-sm stat-card")
            ], md=3, sm=6, className="mb-4"),
        ]),
        
        # Charts Section
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
                                    xaxis={'title': 'Ngày', 'gridcolor': '#f0f0f0'},
                                    yaxis={'title': 'Lưu lượng (L/s)', 'gridcolor': '#f0f0f0'},
                                    hovermode='x unified',
                                    plot_bgcolor='white',
                                    paper_bgcolor='white',
                                    margin=dict(l=50, r=20, t=20, b=50)
                                )
                            },
                            config={'displayModeBar': False}
                        )
                    ])
                ], className="shadow-sm mb-4")
            ], md=8),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5([
                            html.I(className="fas fa-chart-pie me-2"),
                            "Phân Tích Dữ Liệu"
                        ], className="mb-0")
                    ]),
                    dbc.CardBody([
                        dcc.Graph(
                            id='distribution-chart',
                            figure={
                                'data': [
                                    go.Box(
                                        y=df['flow_rate'],
                                        name='Lưu lượng',
                                        marker=dict(color='#1f77b4'),
                                        boxmean='sd'
                                    )
                                ],
                                'layout': go.Layout(
                                    yaxis={'title': 'L/s', 'gridcolor': '#f0f0f0'},
                                    plot_bgcolor='white',
                                    paper_bgcolor='white',
                                    margin=dict(l=50, r=20, t=20, b=50),
                                    showlegend=False
                                )
                            },
                            config={'displayModeBar': False}
                        )
                    ])
                ], className="shadow-sm mb-4")
            ], md=4),
        ]),
        
        # Multi-parameter chart
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
                                        x=df['date'][-30:],
                                        y=df['flow_rate'][-30:],
                                        mode='lines+markers',
                                        name='Lưu lượng (L/s)',
                                        line=dict(color='#1f77b4', width=2),
                                        marker=dict(size=6)
                                    ),
                                    go.Scatter(
                                        x=df['date'][-30:],
                                        y=df['pressure'][-30:] * 2,
                                        mode='lines+markers',
                                        name='Áp suất (Bar x2)',
                                        line=dict(color='#2ca02c', width=2),
                                        marker=dict(size=6),
                                        yaxis='y2'
                                    ),
                                    go.Scatter(
                                        x=df['date'][-30:],
                                        y=df['temperature'][-30:] * 5,
                                        mode='lines+markers',
                                        name='Nhiệt độ (°C x5)',
                                        line=dict(color='#ff7f0e', width=2),
                                        marker=dict(size=6),
                                        yaxis='y3'
                                    )
                                ],
                                'layout': go.Layout(
                                    xaxis={'title': 'Ngày (30 ngày gần nhất)', 'gridcolor': '#f0f0f0'},
                                    yaxis={'title': 'Lưu lượng', 'gridcolor': '#f0f0f0'},
                                    yaxis2={'title': 'Áp suất', 'overlaying': 'y', 'side': 'right'},
                                    yaxis3={'title': 'Nhiệt độ', 'overlaying': 'y', 'side': 'right', 'position': 0.95},
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
                            config={'displayModeBar': False}
                        )
                    ])
                ], className="shadow-sm mb-4")
            ], width=12)
        ]),
        
        # Features Section
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
                        html.H4("AI Dự Đoán", className="mb-3"),
                        html.P("Sử dụng machine learning để dự đoán lưu lượng nước chính xác",
                              className="text-muted")
                    ], className="text-center")
                ], className="shadow-sm feature-card h-100")
            ], md=4, className="mb-4"),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.I(className="fas fa-clock fa-3x text-success mb-3"),
                        html.H4("Realtime", className="mb-3"),
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
    
    # Footer
    html.Footer([
        dbc.Container([
            dbc.Row([
                dbc.Col([
                html.P("© 2025 Dự Đoán Lưu Lượng Nước. Bảo lưu mọi quyền.",
                    className="text-center mb-0",
                    style={"color": "white !important"}
                    )
                ], width=12)
            ])
        ])
    ], className="py-4 mt-5", style={"background-color": "#023E73"} )
], className="page-container")


@callback(
    Output('weather-store', 'data'),
    Input('url', 'hash')
)
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
        print(data)
        

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
        Output('weather-location', 'children'),
        Output('weather-localtime', 'children'),
        Output('weather-temp', 'children'),
        Output('weather-desc', 'children'),
        Output('weather-icon', 'className'),
        Output('stat-temp', 'children'),
        Output('stat-humidity', 'children'),
        Output('stat-pressure', 'children'),
        Output('stat-precip', 'children'),
        Output('weather-forecast', 'children'),
        Output('weather-updated', 'children'),
        Output('weather-container', 'className'),
        Output('weather-raw', 'children')
    ],
    [
        Input('weather-store', 'data'),
        Input('show-forecast', 'n_clicks'),
        Input('forecast-length', 'value')
    ],
    [State('weather-store', 'data')]
)
def render_weather(store_data, n_clicks, forecast_length, stored):
    default_container_class = 'text-start'

    def empty_response(msg=''):
        return (
            'Thời tiết địa phương',  # weather-location
            '',                     # weather-localtime
            '—',                    # weather-temp
            msg or 'Vui lòng cho phép truy cập vị trí để xem thời tiết.',  # weather-desc
            'weather-icon',         # weather-icon className
            '—', '—', '—', '—',     # stat-temp, stat-humidity, stat-pressure, stat-precip
            [],                     # forecast children
            '',                     # weather-updated
            default_container_class
            , ''
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
        if n_clicks and n_clicks > 0:
            length = int(forecast_length or 3)
            for i in range(min(length, len(dates))):
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

    details = html.Div([
        html.H3(f"{temp}°C", className='mb-1'),
        html.P(f"{desc}", className='text-muted mb-1'),
        html.Div([html.Small(f"Gió: {wind} km/h"), html.Span(" • "), html.Small(f"Độ ẩm: {humidity if humidity is not None else '—'}%")], className='text-muted'),
    ])

    # forecast cards
    forecast_nodes = []
    for f in forecast_items:
        # short date
        try:
            dd = datetime.fromisoformat(f['date']).strftime('%d/%m')
        except Exception:
            dd = f['date']
        forecast_nodes.append(html.Div([
            html.Div(dd, className='small text-muted'),
            html.Div(f['label'], className='small'),
            html.Div(f"{f.get('hi','—')}° / {f.get('lo','—')}°", className='fw-bold'),
            html.Div((f.get('precip') or 0), className='small text-muted')
        ], className='day'))

    updated = f"Cập nhật: {localtime_str}"

    location_out = place
    localtime_out = localtime_str
    temp_out = f"{temp}°C"
    desc_out = desc
    icon_class_out = f'weather-icon {icon_class}'

    stat_temp_out = f"{temp} °C"
    stat_humidity_out = f"{humidity if humidity is not None else '—'} %"
    stat_pressure_out = f"{pressure if pressure is not None else '—'} hPa"
    stat_precip_out = f"{precip if precip is not None else 0}"

    forecast_out = forecast_nodes

    updated_out = updated

    container_class = f'text-start weather-{container_variant}'

    return (
        location_out,
        localtime_out,
        temp_out,
        desc_out,
        icon_class_out,
        stat_temp_out,
        stat_humidity_out,
        stat_pressure_out,
        stat_precip_out,
        forecast_out,
        updated_out,
        container_class,
        json.dumps(store_data, ensure_ascii=False, indent=2)
    )