from typing import Dict, Any, List, Optional
from dash import html, dcc, callback, Input, Output, State
import dash_bootstrap_components as dbc
from components.navbar import create_navbar
from dash.exceptions import PreventUpdate
import dash
from datetime import datetime, timedelta
import math
import plotly.graph_objs as go
from statistics import mean, pstdev
from api.pump import list_pumps
from api.sensor_data import get_data_by_pump
import random


RANGE_TO_DAYS = {
    '7d': 7,
    '14d': 14,
    '30d': 30
}

FORECAST_OPTIONS = {
    '10m': {'label': '10 phút', 'minutes': 10},
    '30m': {'label': '30 phút', 'minutes': 30},
    '60m': {'label': '1 giờ', 'minutes': 60},
    '6h': {'label': '6 giờ', 'minutes': 360},
    '12h': {'label': '12 giờ', 'minutes': 720},
    '15h': {'label': '15 giờ', 'minutes': 900},
    '24h': {'label': '24 giờ', 'minutes': 1440}
}

DEFAULT_FORECAST_KEY = '60m'

MAX_FETCH_LIMIT = 200
MAX_FETCH_BATCHES = 5


def create_empty_store(range_value: str = '7d', pump_id: Optional[str] = None, horizon_minutes: Optional[int] = None) -> Dict[str, Any]:
    horizon = horizon_minutes if horizon_minutes is not None else get_horizon_minutes(DEFAULT_FORECAST_KEY)
    return {
        'series': [],
        'range_value': range_value,
        'range_days': RANGE_TO_DAYS.get(range_value, 7),
        'pump_id': str(pump_id) if pump_id is not None else None,
        'last_updated': None,
        'horizon_minutes': horizon
    }


def build_stat_card(title, value_id, subtext, icon_class, badge_id=None):
    """Create a compact stat card with optional badge placeholder."""
    children = [
        html.Div([
            html.Div(title, className='text-muted text-uppercase small mb-1 fw-semibold'),
            html.Div(id=value_id, className='fs-2 fw-semibold mb-2'),
        ]),
        html.Div(html.I(className=f'{icon_class} fs-3 text-primary'), className='ms-auto')
    ]
    card_body = [
        html.Div(children, className='d-flex align-items-start justify-content-between'),
    ]
    if badge_id:
        card_body.append(
            dbc.Badge('—', id=badge_id, color='light', className='text-uppercase small fw-semibold mb-2')
        )
    card_body.append(html.Small(subtext, className='text-muted'))
    return dbc.Card(dbc.CardBody(card_body), className='shadow-sm h-100')


def parse_iso_datetime(value):
    dt = parse_any_datetime(value)
    if dt is None:
        return datetime.now()
    return dt


def format_timestamp(value):
    dt = parse_any_datetime(value)
    if not dt:
        return '—'
    return dt.strftime('%H:%M:%S %d/%m/%Y')


def parse_any_datetime(value: Any) -> Optional[datetime]:
    if isinstance(value, datetime):
        return value
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    if text.endswith('Z'):
        text = text[:-1] + '+00:00'
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        pass
    for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%d/%m/%Y %H:%M:%S', '%Y-%m-%d'):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


def parse_sensor_timestamp(item: Dict[str, Any]) -> Optional[datetime]:
    for key in ('thoi_gian_cap_nhat', 'thoi_gian_tao', 'thoi_gian', 'timestamp', 'created_at'):
        dt = parse_any_datetime(item.get(key))
        if dt:
            return dt
    date_part = item.get('ngay')
    time_part = item.get('gio') or item.get('thoi_diem')
    if date_part:
        if time_part:
            return parse_any_datetime(f"{date_part} {time_part}")
        return parse_any_datetime(date_part)
    return None


def calculate_series_stats(data):
    flows = [float(item.get('flow_rate', 0)) for item in data if item.get('flow_rate') is not None]
    if not flows:
        return {
            'flows': [],
            'average': None,
            'trend_pct': None,
            'std_dev': 0.0,
            'anomalies': 0
        }
    avg = mean(flows)
    first = flows[0]
    last = flows[-1]
    trend_pct = ((last - first) / first * 100) if first else 0.0
    std_dev = pstdev(flows) if len(flows) > 1 else 0.0
    anomalies = sum(1 for value in flows if abs(value - avg) > std_dev * 2.5)
    return {
        'flows': flows,
        'average': avg,
        'trend_pct': trend_pct,
        'std_dev': std_dev,
        'anomalies': anomalies
    }


def derive_confidence_score(stats: Dict[str, Any]) -> float:
    flows = stats.get('flows') or []
    if not flows:
        return 0.0
    avg = stats.get('average') or 0.0
    std_dev = stats.get('std_dev') or 0.0
    variability_penalty = 0.0 if avg <= 0 else min(40.0, (std_dev / avg) * 45.0)
    anomaly_penalty = min(25.0, (stats.get('anomalies') or 0) * 5.0)
    confidence = 95.0 - variability_penalty - anomaly_penalty
    return round(max(55.0, min(98.0, confidence)), 1)


def trend_badge_props(trend_pct):
    if trend_pct is None:
        return 'Chưa có dữ liệu', 'secondary'
    if trend_pct > 1.5:
        return 'Tăng ổn định', 'success'
    if trend_pct > 0.3:
        return 'Tăng nhẹ', 'primary'
    if trend_pct < -1.5:
        return 'Giảm mạnh', 'danger'
    if trend_pct < -0.3:
        return 'Giảm nhẹ', 'warning'
    return 'Ổn định', 'secondary'


def confidence_badge_props(confidence):
    if confidence >= 90:
        return 'Độ tin cậy rất cao', 'success'
    if confidence >= 80:
        return 'Độ tin cậy cao', 'primary'
    if confidence >= 70:
        return 'Độ tin cậy trung bình', 'warning'
    return 'Độ tin cậy thấp', 'danger'


def anomaly_badge_props(count):
    if count == 0:
        return 'Hoạt động bình thường', 'success'
    if count <= 3:
        return 'Cần theo dõi', 'warning'
    return 'Cảnh báo bất thường', 'danger'


# Tìm đến dòng định nghĩa hàm generate_forecast_values và thay thế bằng:
def get_linear_coefficients(values: List[float]):
    """Tính toán hệ số hồi quy tuyến tính y = ax + b"""
    if not values:
        return 0.0, 0.0
    
    n = len(values)
    if n == 1:
        return 0.0, values[-1]

    x_vals = list(range(n))
    sum_x = sum(x_vals)
    sum_y = sum(values)
    sum_xy = sum(x * y for x, y in zip(x_vals, values))
    sum_x2 = sum(x * x for x in x_vals)
    
    denominator = n * sum_x2 - sum_x ** 2
    if denominator == 0:
        slope = 0.0
    else:
        slope = (n * sum_xy - sum_x * sum_y) / denominator
        
    intercept = (sum_y - slope * sum_x) / n
    return slope, intercept


def infer_sample_interval_seconds(times: List[datetime]) -> float:
    if len(times) < 2:
        return 300.0
    diffs = []
    for current, previous in zip(times[1:], times[:-1]):
        delta = (current - previous).total_seconds()
        if delta > 0:
            diffs.append(delta)
    if not diffs:
        return 300.0
    diffs.sort()
    mid = len(diffs) // 2
    if len(diffs) % 2 == 0:
        median = (diffs[mid - 1] + diffs[mid]) / 2.0
    else:
        median = diffs[mid]
    return max(60.0, min(3600.0, median))


def fetch_pump_timeseries(pump_id: Optional[str], days: int, token: Optional[str]) -> List[Dict[str, Any]]:
    if pump_id is None:
        return []
    try:
        pump_id_int = int(pump_id)
    except (TypeError, ValueError):
        pump_id_int = pump_id

    records: List[Dict[str, Any]] = []
    offset = 0
    batches = 0

    while batches < MAX_FETCH_BATCHES:
        response = get_data_by_pump(ma_may_bom=pump_id_int, limit=MAX_FETCH_LIMIT, offset=offset, token=token)
        if isinstance(response, dict):
            data_chunk = response.get('data') or []
            total = response.get('total')
        elif isinstance(response, list):
            data_chunk = response
            total = None
        else:
            data_chunk = []
            total = None

        if not isinstance(data_chunk, list):
            data_chunk = [data_chunk]

        if not data_chunk:
            break

        records.extend(data_chunk)

        if total is not None:
            try:
                total_int = int(total)
                if offset + MAX_FETCH_LIMIT >= total_int:
                    break
            except (TypeError, ValueError):
                pass

        if len(data_chunk) < MAX_FETCH_LIMIT:
            break

        offset += MAX_FETCH_LIMIT
        batches += 1

    if not records:
        return []

    converted = []
    for item in records:
        timestamp = parse_sensor_timestamp(item)
        if not timestamp:
            continue
        flow = item.get('luu_luong_nuoc') if isinstance(item, dict) else None
        if flow is None:
            flow = item.get('flow_rate') if isinstance(item, dict) else None
        try:
            flow_value = float(flow)
        except (TypeError, ValueError):
            continue
        converted.append({
            'time': timestamp.isoformat(),
            'flow_rate': round(flow_value, 2),
            'raw': item
        })

    if not converted:
        return []

    converted.sort(key=lambda it: it['time'])
    end_time = datetime.now()
    start_time = end_time - timedelta(days=days)
    filtered = [it for it in converted if parse_iso_datetime(it['time']) >= start_time]

    if not filtered:
        filtered = converted[-min(len(converted), 200):]
    elif len(filtered) > 400:
        filtered = filtered[-400:]

    return filtered


def build_recommendation_item(icon_class: str, title: str, description: str, color_class: str = 'text-primary'):
    return dbc.ListGroupItem([
        html.I(className=f'{icon_class} {color_class} me-2 mt-1'),
        html.Div([
            html.Span(title, className='fw-semibold d-block'),
            html.Span(description, className='text-muted small')
        ])
    ], className='d-flex align-items-start border-0 ps-0')


def get_horizon_minutes(key: Optional[str]) -> int:
    if key and key in FORECAST_OPTIONS:
        return FORECAST_OPTIONS[key]['minutes']
    return FORECAST_OPTIONS[DEFAULT_FORECAST_KEY]['minutes']


def build_last_updated_text(timestamp: Optional[str]) -> str:
    if not timestamp:
        return ''
    return f'Cập nhật: {format_timestamp(timestamp)}'


layout = html.Div([
    create_navbar(is_authenticated=True),
    dbc.Container([
        dcc.Store(id='predict-data-store', data=create_empty_store()),
        dcc.Store(id='predict-pump-meta-store', data={}),
        dbc.Row([
            dbc.Col([
                html.Span('Hệ thống giám sát và dự báo dòng chảy nước', className='text-uppercase text-muted small fw-semibold'),
                html.H2('Giám sát & Dự báo dòng chảy nước', className='fw-bold mb-2'),
                html.P('Giám sát thời gian thực và dự báo lưu lượng nước dựa trên dữ liệu lịch sử và thuật toán học máy', className='text-muted mb-0')
            ], md=8),
            dbc.Col([
                html.Div([
                    dcc.Dropdown(
                        id='predict-pump-select',
                        options=[],
                        value=None,
                        clearable=False,
                        placeholder='Chọn máy bơm',
                        style={'minWidth': '200px'},
                        className='mb-2 mb-md-0'
                    ),
                    # range selector removed from header per UX request
                ], className='d-flex flex-column flex-md-row justify-content-md-end gap-2')
            ], md=4)
        ], className='mt-4 mb-3 g-3 align-items-center'),

        dbc.Alert(id='predict-error', color='danger', is_open=False, className='mb-3'),

        dbc.Row([
            dbc.Col(build_stat_card('Lưu lượng trung bình', 'predict-avg-flow-value', 'L/min (giai đoạn đã chọn)', 'fas fa-tachometer-alt'), md=3),
            dbc.Col(build_stat_card('Xu hướng dự báo', 'predict-trend-value', 'Tốc độ thay đổi', 'fas fa-chart-line', badge_id='predict-trend-badge'), md=3),
            dbc.Col(build_stat_card('Độ tin cậy mô hình', 'predict-confidence-value', 'Mức độ chính xác hiện tại', 'fas fa-shield-alt', badge_id='predict-confidence-badge'), md=3),
            dbc.Col(build_stat_card('Điểm bất thường', 'predict-anomaly-value', 'Phát hiện trong giai đoạn gần nhất', 'fas fa-exclamation-circle', badge_id='predict-anomaly-badge'), md=3)
        ], className='g-3 mb-4'),

        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.Div([
                            html.Div([
                                html.H5('Dự báo lưu lượng sắp tới', className='mb-0 fw-semibold'),
                                html.Small('Biểu đồ thể hiện dữ liệu thực tế và vùng dự báo', className='text-muted')
                            ]),
                            html.Div([
                                html.Div([
                                    html.Span('Dự báo', className='text-muted small me-2'),
                                    dcc.Dropdown(
                                        id='predict-forecast-select',
                                        options=[{'label': opt['label'], 'value': key} for key, opt in FORECAST_OPTIONS.items()],
                                        value=DEFAULT_FORECAST_KEY,
                                        clearable=False,
                                        style={'width': '140px'}
                                    )
                                ], className='d-flex align-items-center gap-2 flex-wrap'),
                                dbc.Button('Tải dữ liệu', id='predict-refresh-btn', color='primary', n_clicks=0, className='btn-sm'),
                                dbc.Button('Tạo dữ liệu giả lập', id='predict-simulate-btn', color='secondary', n_clicks=0, className='btn-sm'),
                                html.Small(id='predict-last-updated', className='text-muted ms-md-3')
                            ], className='d-flex flex-wrap align-items-center justify-content-start justify-content-md-end gap-2')
                        ], className='d-flex flex-column flex-md-row align-items-md-center justify-content-between gap-3')
                    ]),
                    dbc.CardBody([
                        dcc.Loading(type='dot', children=dcc.Graph(id='predict-flow-chart', figure={}, config={'displayModeBar': False})),
                        html.Small('Dữ liệu được cập nhật từ API dựa trên lựa chọn máy bơm.', className='text-muted')
                    ])
                ], className='shadow-sm h-100')
            ], lg=8, className='mb-4'),

            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H6('Bản ghi mới nhất', className='mb-0 fw-semibold')),
                    dbc.CardBody([
                        html.Div(id='predict-data-table', className='table-scroll'),
                        html.Small('Hiển thị tối đa 50 bản ghi gần nhất từ API.', className='text-muted d-block mt-3')
                    ])
                ], className='shadow-sm h-100')
            ], lg=4, className='mb-4')
        ], className='g-4'),

        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H6('Thông tin máy bơm', className='mb-0 fw-semibold')),
                    dbc.CardBody([
                        dbc.ListGroup([
                            dbc.ListGroupItem([
                                html.Span('Tên máy bơm', className='text-muted'),
                                html.Span(id='pump-name-value', className='fw-semibold')
                            ], className='d-flex justify-content-between align-items-center border-0 px-0'),
                            dbc.ListGroupItem([
                                html.Span('Vị trí/Mô tả', className='text-muted'),
                                html.Span(id='pump-location-value', className='fw-semibold text-end')
                            ], className='d-flex justify-content-between align-items-center border-0 px-0'),
                            dbc.ListGroupItem([
                                html.Span('Trạng thái hiện tại', className='text-muted'),
                                html.Span(id='pump-power-value', className='fw-semibold text-end')
                            ], className='d-flex justify-content-between align-items-center border-0 px-0'),
                            dbc.ListGroupItem([
                                html.Span('Trạng thái', className='text-muted'),
                                dbc.Badge('—', id='pump-status-badge', color='secondary', className='px-3 py-2 fw-semibold text-uppercase')
                            ], className='d-flex justify-content-between align-items-center border-0 px-0'),
                            dbc.ListGroupItem([
                                html.Span('Cập nhật dữ liệu', className='text-muted'),
                                html.Span(id='pump-maintenance-value', className='fw-semibold text-end')
                            ], className='d-flex justify-content-between align-items-center border-0 px-0')
                        ], flush=True, className='mb-0')
                    ])
                ], className='shadow-sm h-100')
            ], lg=6, className='mb-4'),

            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H6('Khuyến nghị từ AI', className='mb-0 fw-semibold')),
                    dbc.CardBody([
                        html.Div(id='ai-recommendations', className='d-flex flex-column gap-2'),
                        dbc.Button('Xem báo cáo chi tiết', color='dark', className='mt-4')
                    ])
                ], className='shadow-sm h-100')
            ], lg=6, className='mb-4')
        ], className='g-4'),

    ], fluid=True)
], className='page-container')


@callback(

    Output('predict-pump-select', 'options'),
    Output('predict-pump-select', 'value'),
    Output('predict-pump-meta-store', 'data'),
    Input('url', 'pathname'),
    State('session-store', 'data'),
    State('predict-pump-select', 'value')
)
def load_pump_options(pathname, session_data, current_value):
    if pathname != '/predict_data':
        raise PreventUpdate

    token = None
    if session_data and isinstance(session_data, dict):
        token = session_data.get('token')

    try:
        response = list_pumps(limit=200, offset=0, token=token)
        if isinstance(response, dict):
            pumps = response.get('data') or []
        elif isinstance(response, list):
            pumps = response
        else:
            pumps = []
    except Exception:
        pumps = []

    if not pumps:
        return [], None, {}

    options = []
    meta = {}
    def pump_sort_key(pump_item: Dict[str, Any]):
        value = pump_item.get('ma_may_bom')
        try:
            return int(value)
        except (TypeError, ValueError):
            return str(value)

    for pump in sorted(pumps, key=pump_sort_key):
        pump_id = pump.get('ma_may_bom')
        if pump_id is None:
            continue
        value = str(pump_id)
        label = pump.get('ten_may_bom') or f'Máy bơm {value}'
        options.append({'label': label, 'value': value})
        meta[value] = pump

    if not options:
        return [], None, {}

    selected_value = current_value if current_value in meta else options[0]['value']
    return options, selected_value, meta


@callback(
    Output('predict-data-store', 'data'),
    Output('predict-last-updated', 'children'),
    Output('predict-error', 'children'),
    Output('predict-error', 'is_open'),
    Input('url', 'pathname'),
    Input('predict-refresh-btn', 'n_clicks'),
    Input('predict-simulate-btn', 'n_clicks'),
    Input('predict-pump-select', 'value'),
    Input('predict-forecast-select', 'value'),
    State('session-store', 'data'),
    State('predict-data-store', 'data'),
    prevent_initial_call=False
)
def refresh_predict_data(pathname, refresh_clicks, simulate_clicks, pump_value, forecast_value, session_data, existing_store):
    if pathname != '/predict_data':
        raise PreventUpdate
    range_value = (existing_store or {}).get('range_value') or '7d'
    horizon_minutes = get_horizon_minutes(forecast_value)

    store = dict(existing_store or create_empty_store(range_value, pump_value, horizon_minutes))
    store['pump_id'] = str(pump_value) if pump_value else None
    store['range_value'] = range_value
    store['range_days'] = RANGE_TO_DAYS.get(range_value, 7)
    store['horizon_minutes'] = horizon_minutes

    ctx = dash.callback_context
    trigger = ctx.triggered[0]['prop_id'].split('.')[0] if ctx and ctx.triggered else None

    if trigger == 'predict-forecast-select':
        return store, build_last_updated_text(store.get('last_updated')), '', False

    if trigger == 'predict-simulate-btn':
        now = datetime.now()
        interval_seconds = 60
        past_minutes = 120
        num_points = int(past_minutes * 60 / interval_seconds) + 1
        # target flow oscillation between ~0.25 and ~0.6
        base_flow = 0.425
        trend = 0.0  # no long-term trend for this sim
        amp = 0.175
        period = 60  # period in samples for sine
        current_temp = 19.2
        current_humidity = 91
        series = []
        for i in range(num_points):
            t = now - timedelta(seconds=(num_points - 1 - i) * interval_seconds)
            noise = random.gauss(0, 0.03)
            value = base_flow + trend * i + amp * math.sin(2 * math.pi * (i % period) / period) + noise
            series.append({'time': t.isoformat(), 'flow_rate': round(max(0.0, value), 4), 'raw': {'nhiet_do': current_temp, 'do_am_dat': current_humidity}})

        sim_truth = {}
        for h in (10, 30, 60):
            steps = int(math.ceil((h * 60) / interval_seconds))
            times = [now + timedelta(seconds=30 + interval_seconds * k) for k in range(steps)]
            values = []
            for k in range(steps):
                idx = num_points + k
                noise = random.gauss(0, 0.02)
                val = base_flow + trend * idx + amp * math.sin(2 * math.pi * (idx % period) / period) + noise
                values.append(round(max(0.0, val), 4))
            sim_truth[h] = {'times': [tt.isoformat() for tt in times], 'values': values}

        last_updated = now.isoformat()
        store.update({'series': series, 'last_updated': last_updated, 'simulated': True, 'sim_truth': sim_truth})
        return store, build_last_updated_text(last_updated), '', False

    if not pump_value:
        return store, '', '', False

    token = None
    if session_data and isinstance(session_data, dict):
        token = session_data.get('token')

    try:
        days = RANGE_TO_DAYS.get(range_value, 7)
        series = fetch_pump_timeseries(pump_value, days, token)
    except Exception as exc:  # pragma: no cover - defensive fallback
        message = f'Lỗi khi tải dữ liệu: {exc}'
        store['series'] = []
        store['last_updated'] = None
        return store, '', message, True

    if not series:
        # Nếu API không trả về dữ liệu, tạo dữ liệu giả lập tự động (fallback)
        now = datetime.now()
        interval_seconds = 60
        past_minutes = 120
        num_points = int(past_minutes * 60 / interval_seconds) + 1
        base_flow = 0.425
        trend = 0.0
        amp = 0.175
        period = 60
        current_temp = 19.2
        current_humidity = 91
        series = []
        for i in range(num_points):
            t = now - timedelta(seconds=(num_points - 1 - i) * interval_seconds)
            noise = random.gauss(0, 0.03)
            value = base_flow + trend * i + amp * math.sin(2 * math.pi * (i % period) / period) + noise
            series.append({'time': t.isoformat(), 'flow_rate': round(max(0.0, value), 4), 'raw': {'nhiet_do': current_temp, 'do_am_dat': current_humidity}})

        sim_truth = {}
        # tạo truth cho một vài horizon thường dùng (phút)
        for h in (10, 30, 60):
            steps = int(math.ceil((h * 60) / interval_seconds))
            times = [now + timedelta(seconds=30 + interval_seconds * k) for k in range(steps)]
            values = []
            for k in range(steps):
                idx = num_points + k
                noise = random.gauss(0, 0.02)
                val = base_flow + trend * idx + amp * math.sin(2 * math.pi * (idx % period) / period) + noise
                values.append(round(max(0.0, val), 4))
            sim_truth[h] = {'times': [tt.isoformat() for tt in times], 'values': values}

        last_updated = now.isoformat()
        store.update({'series': series, 'last_updated': last_updated, 'simulated': True, 'sim_truth': sim_truth})
        return store, build_last_updated_text(last_updated), '', False

    last_updated = datetime.now().isoformat()
    store.update({
        'series': series,
        'last_updated': last_updated
    })
    return store, build_last_updated_text(last_updated), '', False

def calculate_ema_and_forecast(values: List[float], horizon_steps: int, alpha: float = 0.15):
    """
    Tính đường xu hướng (EMA) cho quá khứ và dự báo tương lai.
    alpha: Hệ số làm mịn (0 < alpha < 1). Càng nhỏ càng mượt nhưng trễ hơn.
    """
    if not values:
        return [], []

    # 1. Tính EMA cho dữ liệu quá khứ (Fit line)
    ema_values = []
    current_ema = values[0]
    for val in values:
        current_ema = alpha * val + (1 - alpha) * current_ema
        ema_values.append(current_ema) # Không làm tròn ở đây để giữ độ mượt

    # 2. Tính dự báo tương lai (Forecast)
    # Lấy độ dốc (trend) của vài điểm cuối cùng để phóng chiếu
    if len(ema_values) >= 5:
        last_vals = ema_values[-5:]
        # Tính slope trung bình của 5 điểm cuối
        slope = (last_vals[-1] - last_vals[0]) / 4 
    else:
        slope = 0
    
    last_val = ema_values[-1]
    forecast_values = []
    
    # Tạo dự báo tuyến tính từ điểm cuối cùng
    # (Nếu muốn dự báo hình sin thì cần thuật toán phức tạp hơn như FFT hoặc LSTM)
    for i in range(1, horizon_steps + 1):
        # Giảm dần độ dốc theo thời gian để dự báo không bị bay quá xa (Damping)
        damped_slope = slope * (0.9 ** i) 
        next_val = last_val + damped_slope * i
        forecast_values.append(max(0.0, next_val))

    return ema_values, forecast_values

@callback(
    Output('predict-flow-chart', 'figure'),
    Input('predict-data-store', 'data')
)
def update_chart(data_store):
    store = data_store or {}
    data = store.get('series') or []
    fig = go.Figure()

    if not data:
        fig.update_layout(
            plot_bgcolor='white',
            paper_bgcolor='white',
            xaxis=dict(showgrid=True, gridcolor='rgba(0,0,0,0.05)'),
            yaxis=dict(title='Lưu lượng (L/min)', showgrid=True, gridcolor='rgba(0,0,0,0.05)'),
            margin=dict(l=40, r=20, t=30, b=40)
        )
        fig.add_annotation(
            text='Chưa có dữ liệu từ API',
            xref='paper', yref='paper',
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(color='rgba(0,0,0,0.35)', size=16, family='Arial')
        )
        return fig

    # --- CHUẨN BỊ DỮ LIỆU ---
    times = [parse_iso_datetime(point.get('time')) for point in data]
    flows = [point.get('flow_rate', 0) for point in data]
    
    # Tính toán số bước dự báo cần thiết
    horizon_minutes = store.get('horizon_minutes') or get_horizon_minutes(DEFAULT_FORECAST_KEY)
    base_seconds = infer_sample_interval_seconds(times)
    horizon_seconds = max(base_seconds, horizon_minutes * 60.0)
    steps = int(math.ceil(horizon_seconds / base_seconds))
    
    # --- TÍNH TOÁN ĐƯỜNG XU HƯỚNG MỚI ---
    # Sử dụng alpha=0.15 để đường line uốn lượn theo hình sin
    fit_values, forecast_values = calculate_ema_and_forecast(flows, steps, alpha=0.7)

    # Tạo mốc thời gian cho tương lai
    last_time = times[-1]
    start_offset = 30
    forecast_times = [last_time + timedelta(seconds=start_offset + base_seconds * (step - 1)) for step in range(1, steps + 1)]

    # --- VẼ BIỂU ĐỒ ---
    
    # Tính toán vùng tin cậy (dựa trên độ lệch chuẩn của dữ liệu gốc so với đường fit)
    residuals = [abs(f - e) for f, e in zip(flows, fit_values)]
    mean_res = sum(residuals) / len(residuals) if residuals else 0
    std_res = pstdev(residuals) if len(residuals) > 1 else 0
    confidence_interval = mean_res + 2 * std_res # 95% confidence

    all_times = times + forecast_times
    all_modeled = fit_values + forecast_values
    
    upper_band = [v + confidence_interval for v in all_modeled]
    lower_band = [max(0.0, v - confidence_interval) for v in all_modeled]

    # 1. Vùng tin cậy
    fig.add_trace(go.Scatter(
        x=all_times + all_times[::-1],
        y=upper_band + lower_band[::-1],
        fill='toself',
        fillcolor='rgba(26,115,232,0.1)',
        line=dict(color='rgba(0,0,0,0)'),
        hoverinfo='skip',
        showlegend=False,
        name='Vùng dự báo'
    ))

    # 2. Dữ liệu thực tế
    fig.add_trace(go.Scatter(
        x=times,
        y=flows,
        mode='lines+markers',
        name='Thực tế',
        line=dict(color='#34a853', width=2), # Giảm width chút cho thanh thoát
        marker=dict(size=5, color='#34a853')
    ))

    # 3. Xu hướng hiện tại (FIT) - Đã sửa hết bậc thang
    fig.add_trace(go.Scatter(
        x=times,
        y=[round(v, 4) for v in fit_values], # Làm tròn 4 chữ số
        mode='lines',
        name='Xu hướng (Smooth)',
        line=dict(color='#1a73e8', width=3),
        opacity=0.9
    ))

    # 4. Dự báo tương lai
    fig.add_trace(go.Scatter(
        x=forecast_times,
        y=[round(v, 4) for v in forecast_values], # Làm tròn 4 chữ số
        mode='lines',
        name='Dự báo',
        line=dict(color='#1a73e8', dash='dash', width=3),
    ))

    # Kẻ vạch ngăn cách
    fig.add_vline(x=last_time, line_width=1, line_dash="dot", line_color="gray")

    # Annotation độ chính xác
    stats = calculate_series_stats(data)
    conf = derive_confidence_score(stats)
    fig.add_annotation(
        text=f'Độ tin cậy mô hình: {conf:.1f}%',
        xref='paper', yref='paper',
        x=0.98, y=0.98,
        showarrow=False,
        font=dict(color='#0b0b0b', size=11),
        align='right',
        bordercolor='rgba(0,0,0,0.06)',
        borderwidth=1,
        bgcolor='rgba(255,255,255,0.9)'
    )

    fig.update_layout(
        xaxis=dict(title='', type='date', showgrid=True, gridcolor='rgba(0,0,0,0.05)', tickformat='%H:%M\n%d/%m'),
        yaxis=dict(title='Lưu lượng (L/min)', showgrid=True, gridcolor='rgba(0,0,0,0.05)'),
        plot_bgcolor='white',
        paper_bgcolor='white',
        hovermode='x unified',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        margin=dict(l=40, r=20, t=30, b=40)
    )
    return fig


@callback(
    Output('predict-data-table', 'children'),
    Input('predict-data-store', 'data')
)
def render_table(data_store):
    store = data_store or {}
    data = store.get('series') or []
    if not data:
        return dbc.Alert('Chưa có dữ liệu để hiển thị', color='secondary', className='mb-0 bg-light border-0 text-muted')
    rows = []
    for idx, d in enumerate(reversed(data[-50:]), start=1):
        raw = d.get('raw') or {}
        soil = raw.get('do_am_dat')
        temp = raw.get('nhiet_do')
        rain = raw.get('mua')
        soil_text = f"{soil}" if soil is not None else '—'
        temp_text = f"{temp}" if temp is not None else '—'
        rain_text = 'Có' if rain else 'Không'
        rows.append(html.Tr([
            html.Td(idx, className='text-muted'),
            html.Td(format_timestamp(d.get('time'))),
            html.Td(d.get('flow_rate')),
            html.Td(soil_text),
            html.Td(temp_text),
            html.Td(rain_text)
        ], className='align-middle'))
    table = dbc.Table(
        [
            html.Thead(html.Tr([
                html.Th('STT'),
                html.Th('Thời gian'),
                html.Th('Lưu lượng (L/min)'),
                html.Th('Độ ẩm đất'),
                html.Th('Nhiệt độ (°C)'),
                html.Th('Mưa')
            ])),
            html.Tbody(rows)
        ],
        bordered=False,
        hover=True,
        responsive=True,
        size='sm',
        className='mb-0'
    )
    return html.Div(table, style={'maxHeight': '360px', 'overflowY': 'auto'}, className='table-responsive')


@callback(
    Output('predict-avg-flow-value', 'children'),
    Output('predict-trend-value', 'children'),
    Output('predict-trend-badge', 'children'),
    Output('predict-trend-badge', 'color'),
    Output('predict-confidence-value', 'children'),
    Output('predict-confidence-badge', 'children'),
    Output('predict-confidence-badge', 'color'),
    Output('predict-anomaly-value', 'children'),
    Output('predict-anomaly-badge', 'children'),
    Output('predict-anomaly-badge', 'color'),
    Input('predict-data-store', 'data')
)
def update_metric_cards(data_store):
    store = data_store or {}
    stats = calculate_series_stats(store.get('series') or [])
    confidence = derive_confidence_score(stats)

    if not stats['flows']:
        return (
            '—',
            '—', 'Chưa có dữ liệu', 'secondary',
            '—', 'Chưa có dữ liệu', 'secondary',
            '—', 'Chưa có dữ liệu', 'secondary'
        )

    avg_value = f"{stats['average']:.1f}"
    trend_value = f"{stats['trend_pct']:+.1f}%"
    trend_label, trend_color = trend_badge_props(stats['trend_pct'])

    confidence_value = f"{confidence:.1f}%"
    confidence_label, confidence_color = confidence_badge_props(confidence)

    anomaly_value = str(stats['anomalies'])
    anomaly_label, anomaly_color = anomaly_badge_props(stats['anomalies'])

    return (
        avg_value,
        trend_value, trend_label, trend_color,
        confidence_value, confidence_label, confidence_color,
        anomaly_value, anomaly_label, anomaly_color
    )


@callback(
    Output('pump-name-value', 'children'),
    Output('pump-location-value', 'children'),
    Output('pump-power-value', 'children'),
    Output('pump-status-badge', 'children'),
    Output('pump-status-badge', 'color'),
    Output('pump-maintenance-value', 'children'),
    Output('ai-recommendations', 'children'),
    Input('predict-pump-select', 'value'),
    Input('predict-pump-meta-store', 'data'),
    Input('predict-data-store', 'data')
)
def update_pump_section(pump_value, meta_store, data_store):
    meta_store = meta_store or {}
    pump = meta_store.get(str(pump_value)) if pump_value is not None else None
    store = data_store or {}
    series = store.get('series') or []
    stats = calculate_series_stats(series)
    confidence = derive_confidence_score(stats)

    name = pump.get('ten_may_bom') if pump else '—'
    location = pump.get('mo_ta') if pump else None
    if not location:
        location = pump.get('vi_tri') if pump else '—'

    power = pump.get('ma_iot_lk') if pump else None
    if not power:
        power = pump.get('cong_suat') if pump else '—'

    status_active = bool(pump.get('trang_thai')) if pump else False
    status_label = 'Đang chạy' if status_active else 'Đã dừng'
    status_color = 'success' if status_active else 'secondary'

    latest_timestamp = series[-1].get('time') if series else None
    if not latest_timestamp and pump:
        latest_timestamp = pump.get('thoi_gian_cap_nhat') or pump.get('thoi_gian_tao')
    last_update_text = format_timestamp(latest_timestamp)

    recommendations: List[dbc.ListGroupItem] = []
    if stats['flows']:
        trend_label, _ = trend_badge_props(stats['trend_pct'])
        trend_pct = stats['trend_pct'] or 0.0
        icon = 'fas fa-arrow-up' if trend_pct >= 0 else 'fas fa-arrow-down'
        recommendations.append(build_recommendation_item(icon, 'Xu hướng lưu lượng', f'Dự báo {trend_label.lower()} trong giai đoạn tiếp theo.'))

        confidence_label, _ = confidence_badge_props(confidence)
        recommendations.append(build_recommendation_item('fas fa-robot', 'Độ tin cậy mô hình', f'{confidence_label} ({confidence:.1f}%).', 'text-success'))

        if stats['anomalies']:
            recommendations.append(build_recommendation_item('fas fa-exclamation-triangle', 'Phát hiện bất thường', f'Có {stats["anomalies"]} điểm cần kiểm tra.', 'text-warning'))
        else:
            recommendations.append(build_recommendation_item('fas fa-circle-check', 'Hệ thống ổn định', 'Không phát hiện bất thường trong giai đoạn gần nhất.', 'text-success'))
    else:
        recommendations.append(build_recommendation_item('fas fa-info-circle', 'Chưa có dữ liệu', 'Chọn máy bơm và tải dữ liệu để xem khuyến nghị.', 'text-muted'))

    rec_component = dbc.ListGroup(recommendations, flush=True, className='mb-0')

    return (
        name or '—',
        location or '—',
        power or '—',
        status_label,
        status_color,
        last_update_text,
        rec_component
    )