from dash import html, dcc, callback, Input, Output, State
import dash_bootstrap_components as dbc
import dash
from components.navbar import create_navbar
from api import user as api_user
from api import sensor as api_sensor
from api import pump as api_pump
from api import sensor_data as api_sensor_data
from api import models as api_models
import pandas as pd
import plotly.express as px

PRIMARY_BLUE = '#0358a3'
BLUE_SCALE = ['#0358a3', '#1d4ed8', '#2563eb', '#38bdf8', '#60a5fa']
USER_STATUS_BLUE_MAP = {'Hoạt động': '#0358a3', 'Không hoạt động': '#60a5fa'}
PUMP_STATUS_BLUE_MAP = {'Đang chạy': '#0358a3', 'Đã dừng': '#60a5fa'}


layout = html.Div([
    create_navbar(is_authenticated=True, is_admin=True),
    dcc.Location(id='admin-url', refresh=False),
    html.Div(
        id='admin-dashboard',
        style={
            'marginBottom': '100px',
            'marginTop': '80px',
            'marginLeft': '20px',
            'marginRight': '20px'
        }
    )
])


@callback(
    Output('admin-dashboard', 'children'),
    Input('url', 'pathname'),
    State('session-store', 'data'),
    prevent_initial_call='initial_duplicate'
)
def load_admin_dashboard(pathname, session_data):
    if pathname != '/admin':
        raise dash.exceptions.PreventUpdate

    if not session_data or not session_data.get('authenticated') or not session_data.get('is_admin'):
        raise dash.exceptions.PreventUpdate

    token = session_data.get('token')

    try:
        users = api_user.list_users(token=token) or []
        total_users = len(users) if isinstance(users, list) else (users.get('total') if isinstance(users, dict) else 0)
    except Exception:
        users = []
        total_users = 0

    try:
        sensors = api_sensor.list_sensors(limit=200, offset=0, token=token) or {}
        print(sensors)
        total_sensors = sensors.get('total', 9) if isinstance(sensors, dict) else 0
    except Exception:
        total_sensors = 0

    try:
        sensor_types = api_sensor.get_sensor_types(token=token) or {}
        if isinstance(sensor_types, dict):
            sensor_type_data = sensor_types.get('data') or []
            total_sensor_types = sensor_types.get('total') or len(sensor_type_data)
        elif isinstance(sensor_types, list):
            total_sensor_types = len(sensor_types)
        else:
            total_sensor_types = 0
    except Exception:
        total_sensor_types = 0

    try:
        pumps = api_pump.list_pumps(limit=200, offset=0, token=token) or {}
        total_pumps = pumps.get('total', 13) if isinstance(pumps, dict) else 0
    except Exception:
        total_pumps = 0

    try:
        data = api_sensor_data.get_data_by_pump(limit=500, offset=0, token=token) or {}
        total_data = data.get('total', 0) if isinstance(data, dict) else 0
    except Exception:
        total_data = 0
    active_users = []
    try:
        if isinstance(users, list):
            for u in users:
                if u.get('trang_thai') in (True, 'active', 'dang_hoat_dong', 1):
                    username = u.get('ten_dang_nhap') or u.get('username') or u.get('ho_ten')
                    active_users.append(username)
    except Exception:
        active_users = []

    current_user = session_data.get('username')

    pump_items = []
    if isinstance(pumps, dict):
        pump_items = pumps.get('data') or []
        if not total_pumps:
            total_pumps = pumps.get('total') or len(pump_items)
    elif isinstance(pumps, list):
        pump_items = pumps
        if not total_pumps:
            total_pumps = len(pump_items)

    sensor_items = []
    if isinstance(sensors, dict):
        sensor_items = sensors.get('data') or []
        if not total_sensors:
            total_sensors = sensors.get('total') or len(sensor_items)
    elif isinstance(sensors, list):
        sensor_items = sensors
        if not total_sensors:
            total_sensors = len(sensor_items)

    if not total_sensor_types:
        inferred_type_ids = set()
        inferred_type_names = set()
        for item in sensor_items:
            if not isinstance(item, dict):
                continue
            for key in ('ma_loai_cam_bien', 'ma_loai', 'loai_cam_bien_id', 'sensor_type_id'):
                val = item.get(key)
                if val is not None:
                    inferred_type_ids.add(val)
            for key in ('ten_loai_cam_bien', 'loai_cam_bien', 'ten_loai', 'sensor_type_name'):
                name = item.get(key)
                if name:
                    inferred_type_names.add(str(name))
        if inferred_type_ids:
            total_sensor_types = len(inferred_type_ids)
        elif inferred_type_names:
            total_sensor_types = len(inferred_type_names)

    sensor_records = []
    if isinstance(data, dict):
        sensor_records = data.get('data') or []
        if not total_data:
            total_data = data.get('total') or len(sensor_records)
    elif isinstance(data, list):
        sensor_records = data
        if not total_data:
            total_data = len(sensor_records)

    def _is_truthy(value):
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value != 0
        if isinstance(value, str):
            lowered = value.strip().lower()
            return lowered in {'true', '1', 'active', 'dang_hoat_dong', 'yes', 'running'}
        return False

    active_users_count = 0
    try:
        if isinstance(users, list) and users:
            df_users = pd.DataFrame(users)
            if 'trang_thai' in df_users.columns:
                df_users['is_active'] = df_users['trang_thai'].apply(_is_truthy)
            elif 'status' in df_users.columns:
                df_users['is_active'] = df_users['status'].apply(_is_truthy)
            elif 'is_active' in df_users.columns:
                df_users['is_active'] = df_users['is_active'].apply(_is_truthy)
            else:
                df_users['is_active'] = False

            created_series = pd.Series(pd.NaT, index=df_users.index)
            for created_col in ('thoi_gian_tao', 'created_at', 'ngay_tao'):
                if created_col in df_users.columns:
                    converted = pd.to_datetime(df_users[created_col], errors='coerce')
                    if converted.notna().any():
                        created_series = converted
                        break
            df_users['created_at'] = created_series

            active_users_count = int(df_users['is_active'].sum())
        else:
            df_users = pd.DataFrame()
    except Exception:
        df_users = pd.DataFrame()
        active_users_count = len(active_users)

    running_pumps = sum(1 for item in pump_items if _is_truthy(item.get('trang_thai')))

    # Compute device totals using the most reliable available source:
    # prefer explicit 'total' reported by API when > length of items, otherwise use actual list lengths
    try:
        sensor_count = 0
        if isinstance(sensors, dict):
            reported = sensors.get('total')
            try:
                reported_int = int(reported) if reported is not None else 0
            except Exception:
                reported_int = 0
            sensor_count = max(reported_int, len(sensor_items))
        elif isinstance(sensors, list):
            sensor_count = len(sensors)
        else:
            sensor_count = len(sensor_items)
    except Exception:
        sensor_count = len(sensor_items)

    try:
        pump_count = 0
        if isinstance(pumps, dict):
            reported = pumps.get('total')
            try:
                reported_int = int(reported) if reported is not None else 0
            except Exception:
                reported_int = 0
            pump_count = max(reported_int, len(pump_items))
        elif isinstance(pumps, list):
            pump_count = len(pumps)
        else:
            pump_count = len(pump_items)
    except Exception:
        pump_count = len(pump_items)

    device_total = sensor_count + pump_count

    try:
        from pages.predict_data import FORECAST_OPTIONS
        total_models = len(FORECAST_OPTIONS)
    except Exception:
        total_models = 0

    # Prefer counting actual models from API when available
    try:
        models_resp = api_models.list_models(token=token) or {}
        if isinstance(models_resp, dict):
            model_items = models_resp.get('data', []) or []
            total_models = int(models_resp.get('total') or len(model_items))
        elif isinstance(models_resp, list):
            model_items = models_resp
            total_models = len(model_items)
        else:
            model_items = []
    except Exception:
        model_items = []



    # Build summary cards: Active users, Total devices, Sensor types, Models
    summary_cards = html.Div([
        html.Div(dbc.Card(dbc.CardBody([
            html.Div([
                html.Div([
                    html.Span('Người dùng hoạt động', className='admin-summary-title'),
                    html.H3(str(active_users_count), className='admin-summary-value'),
                    html.Span(f'Trên tổng số {total_users}', className='admin-summary-subtitle')
                ]),
                html.Div(html.I(className='fas fa-user-check'), className='admin-summary-icon bg-admin-primary')
            ], className='d-flex justify-content-between align-items-start')
        ])), style={'flex': '1 1 0', 'minWidth': '160px'}),

        html.Div(dbc.Card(dbc.CardBody([
            html.Div([
                html.Div([
                    html.Span('Tổng thiết bị', className='admin-summary-title'),
                    html.H3(str(device_total), className='admin-summary-value'),
                    html.Span(f'{len(sensor_items)} cảm biến · {len(pump_items)} máy bơm', className='admin-summary-subtitle')
                ]),
                html.Div(html.I(className='fas fa-microchip'), className='admin-summary-icon bg-admin-info')
            ], className='d-flex justify-content-between align-items-start')
        ])), style={'flex': '1 1 0', 'minWidth': '160px'}),

        html.Div(dbc.Card(dbc.CardBody([
            html.Div([
                html.Div([
                    html.Span('Tổng loại cảm biến', className='admin-summary-title'),
                    html.H3(str(total_sensor_types), className='admin-summary-value'),
                    html.Span('Phân loại thiết bị giám sát', className='admin-summary-subtitle')
                ]),
                html.Div(html.I(className='fas fa-layer-group'), className='admin-summary-icon bg-admin-warning')
            ], className='d-flex justify-content-between align-items-start')
        ])), style={'flex': '1 1 0', 'minWidth': '160px'}),

        html.Div(dbc.Card(dbc.CardBody([
            html.Div([
                html.Div([
                    html.Span('Tổng mô hình dự báo', className='admin-summary-title'),
                    html.H3(str(total_models), className='admin-summary-value'),
                    html.Span('Tích hợp AI & dự báo', className='admin-summary-subtitle')
                ]),
                html.Div(html.I(className='fas fa-robot'), className='admin-summary-icon bg-admin-model')
            ], className='d-flex justify-content-between align-items-start')
        ])), style={'flex': '1 1 0', 'minWidth': '160px'}),


    ], style={'display': 'flex', 'gap': '12px', 'alignItems': 'stretch', 'flexWrap': 'nowrap'})

    def _style_figure(fig):
        if fig is None:
            return None
        legend_text = 'Chú thích'
        try:
            existing_title = fig.layout.legend.title.text
            if existing_title:
                legend_text = existing_title
        except Exception:
            pass
        fig.update_layout(
            margin=dict(l=20, r=20, t=60, b=20),
            paper_bgcolor='#ffffff',
            plot_bgcolor='#f8fafc',
            font=dict(color='#0f172a'),
            legend=dict(
                title=dict(text=legend_text, font=dict(size=12, color='#0f172a')),
                orientation='h',
                y=-0.3,
                x=0,
                bgcolor='#ffffff',
                bordercolor='rgba(15, 23, 42, 0.12)',
                borderwidth=1,
                font=dict(size=12, color='#0f172a')
            )
        )
        fig.update_xaxes(showgrid=True, gridcolor='rgba(148, 163, 184, 0.2)')
        fig.update_yaxes(showgrid=True, gridcolor='rgba(148, 163, 184, 0.2)')
        return fig

    registration_fig = None
    activity_fig = None
    try:
        if not df_users.empty and df_users['created_at'].notna().any():
            monthly = (
                df_users.dropna(subset=['created_at'])
                .assign(month=lambda d: d['created_at'].dt.to_period('M').dt.to_timestamp())
                .groupby('month')
                .size()
                .reset_index(name='Số người đăng ký')
            )
            if not monthly.empty:
                registration_fig = px.line(
                    monthly,
                    x='month',
                    y='Số người đăng ký',
                    markers=True,
                    title='Lượt đăng ký người dùng theo tháng',
                    color_discrete_sequence=[PRIMARY_BLUE],
                    labels={'month': 'Thời gian', 'Số người đăng ký': 'Số người đăng ký'}
                )
                registration_fig.update_traces(line=dict(color=PRIMARY_BLUE), marker=dict(color=PRIMARY_BLUE))

            monthly_activity = (
                df_users.dropna(subset=['created_at'])
                .assign(month=lambda d: d['created_at'].dt.to_period('M').dt.to_timestamp())
                .groupby('month')
                .agg(total=('is_active', 'count'), active=('is_active', 'sum'))
                .reset_index()
            )
            if not monthly_activity.empty:
                monthly_activity['inactive'] = monthly_activity['total'] - monthly_activity['active']
                activity_long = monthly_activity.melt(
                    id_vars='month',
                    value_vars=['active', 'inactive'],
                    var_name='Trạng thái',
                    value_name='Số lượng'
                )
                activity_long['Trạng thái'] = activity_long['Trạng thái'].map({'active': 'Hoạt động', 'inactive': 'Không hoạt động'})
                activity_fig = px.bar(
                    activity_long,
                    x='month',
                    y='Số lượng',
                    color='Trạng thái',
                    barmode='stack',
                    title='Người dùng hoạt động theo tháng',
                    color_discrete_map=USER_STATUS_BLUE_MAP,
                    labels={'month': 'Thời gian', 'Số lượng': 'Số lượng', 'Trạng thái': 'Trạng thái'}
                )
                activity_fig.update_layout(legend=dict(title=dict(text='Trạng thái')))
    except Exception:
        registration_fig = None
        activity_fig = None

    sensor_df = pd.DataFrame(sensor_records) if sensor_records else pd.DataFrame()
    sensor_fig = None
    pump_activity_fig = None

    if not sensor_df.empty:
        timestamp_col = None
        for col in ('thoi_gian_cap_nhat', 'thoi_gian', 'thoi_gian_tao', 'timestamp', 'created_at'):
            if col in sensor_df.columns:
                converted = pd.to_datetime(sensor_df[col], errors='coerce')
                if converted.notna().any():
                    sensor_df['timestamp'] = converted
                    timestamp_col = 'timestamp'
                    break
        if timestamp_col is None and 'ngay' in sensor_df.columns:
            converted = pd.to_datetime(sensor_df['ngay'], errors='coerce')
            if converted.notna().any():
                sensor_df['timestamp'] = converted
                timestamp_col = 'timestamp'

        if timestamp_col:
            sensor_df = sensor_df.dropna(subset=['timestamp']).sort_values('timestamp')

            if not sensor_df.empty:
                try:
                    sensor_df['is_running'] = sensor_df.get(
                        'luu_luong_nuoc',
                        pd.Series([0] * len(sensor_df), index=sensor_df.index)
                    ).apply(lambda v: float(v or 0) > 0)
                except Exception:
                    sensor_df['is_running'] = False

                pump_group = sensor_df.groupby(sensor_df['timestamp'].dt.floor('4H')).agg(
                    running=('is_running', 'sum'),
                    total=('is_running', 'count')
                ).reset_index()

                if not pump_group.empty:
                    pump_group['stopped'] = pump_group['total'] - pump_group['running']
                    pump_long = pump_group.melt(
                        id_vars='timestamp',
                        value_vars=['running', 'stopped'],
                        var_name='Trạng thái',
                        value_name='Số lần'
                    )
                    pump_long['Trạng thái'] = pump_long['Trạng thái'].map({'running': 'Đang chạy', 'stopped': 'Đã dừng'})
                    pump_activity_fig = px.bar(
                        pump_long,
                        x='timestamp',
                        y='Số lần',
                        color='Trạng thái',
                        barmode='stack',
                        title='Hoạt động máy bơm theo thời gian',
                        color_discrete_map=PUMP_STATUS_BLUE_MAP,
                        labels={'timestamp': 'Thời gian', 'Số lần': 'Số lần', 'Trạng thái': 'Trạng thái'}
                    )

                value_columns = {
                    'luu_luong_nuoc': 'Lưu lượng (L/phút)',
                    'nhiet_do': 'Nhiệt độ (°C)',
                    'do_am_dat': 'Áp suất (bar)',
                    'do_am': 'Độ ẩm (%)'
                }
                available_cols = [col for col in value_columns if col in sensor_df.columns]

                if available_cols:
                    sensor_values = sensor_df[['timestamp'] + available_cols]
                    sensor_long = sensor_values.melt(
                        id_vars='timestamp',
                        value_vars=available_cols,
                        var_name='Chỉ số',
                        value_name='Giá trị'
                    )
                    sensor_long['Chỉ số'] = sensor_long['Chỉ số'].map(value_columns)
                    sensor_long = sensor_long.dropna(subset=['Giá trị'])
                    if not sensor_long.empty:
                        sensor_fig = px.line(
                            sensor_long,
                            x='timestamp',
                            y='Giá trị',
                            color='Chỉ số',
                            markers=True,
                            title='Giá trị cảm biến theo thời gian',
                            color_discrete_sequence=BLUE_SCALE,
                            labels={'timestamp': 'Thời gian', 'Giá trị': 'Giá trị', 'Chỉ số': 'Chỉ số'}
                        )
                        sensor_fig.update_layout(legend=dict(title=dict(text='Chỉ số cảm biến')))

    registration_fig = _style_figure(registration_fig)
    if registration_fig is not None:
        registration_fig.update_xaxes(tickformat='%m/%Y')

    activity_fig = _style_figure(activity_fig)
    if activity_fig is not None:
        activity_fig.update_xaxes(tickformat='%m/%Y')

    pump_activity_fig = _style_figure(pump_activity_fig)
    if pump_activity_fig is not None:
        pump_activity_fig.update_xaxes(tickformat='%d/%m %H:%M')

    sensor_fig = _style_figure(sensor_fig)
    if sensor_fig is not None:
        sensor_fig.update_xaxes(tickformat='%d/%m %H:%M')

    def _graph_or_alert(fig, message):
        if fig is not None:
            return dcc.Graph(figure=fig, config={'displayModeBar': False})
        return html.Div(className='admin-empty', children=dbc.Alert(message, color='secondary', className='mb-0'))

    charts_top = dbc.Row([
        dbc.Col(
            dbc.Card(dbc.CardBody([_graph_or_alert(registration_fig, 'Không có dữ liệu đăng ký.')])),
            md=12, lg=6
        ),
        dbc.Col(
            dbc.Card(dbc.CardBody([_graph_or_alert(activity_fig, 'Không có dữ liệu hoạt động.') ])),
            md=12, lg=6
        )
    ], className='admin-chart-row g-3 mt-1')

    # Nếu không có dữ liệu biểu đồ chi tiết, tạo biểu đồ tóm tắt (bar) hiển thị tổng và số đang hoạt động
    pump_total = total_pumps or len(pump_items)
    pump_active = running_pumps or 0

    try:
        if not sensor_df.empty and 'is_running' in sensor_df.columns:
            sensor_active = int(sensor_df['is_running'].sum())
        else:
            sensor_active = sum(1 for it in sensor_items if _is_truthy(it.get('trang_thai') or it.get('is_running') or it.get('luu_luong_nuoc')))
    except Exception:
        sensor_active = 0

    sensor_total = total_sensors or len(sensor_items)

    pump_summary_fig = None
    sensor_summary_fig = None
    try:
        pump_summary_fig = px.bar(
            x=['Máy bơm đã thêm', 'Máy bơm đang hoạt động'],
            y=[pump_total, pump_active],
            color=['Tổng', 'Đang hoạt động'],
            title='Tổng quan máy bơm',
            color_discrete_sequence=[PRIMARY_BLUE, BLUE_SCALE[1]]
        )
        pump_summary_fig.update_yaxes(title_text='Số lượng')
        pump_summary_fig.update_layout(showlegend=False)
    except Exception:
        pump_summary_fig = None

    try:
        sensor_summary_fig = px.bar(
            x=['Cảm biến đã thêm', 'Cảm biến đang hoạt động'],
            y=[sensor_total, sensor_active],
            color=['Tổng', 'Đang hoạt động'],
            title='Tổng quan cảm biến',
            color_discrete_sequence=[BLUE_SCALE[2], BLUE_SCALE[3]]
        )
        sensor_summary_fig.update_yaxes(title_text='Số lượng')
        sensor_summary_fig.update_layout(showlegend=False)
    except Exception:
        sensor_summary_fig = None

    # Nếu có fig chi tiết, ưu tiên hiển thị; nếu không, hiển thị biểu đồ tóm tắt
    charts_bottom = dbc.Row([
        dbc.Col(
            dbc.Card(dbc.CardBody([
                dcc.Graph(figure=pump_activity_fig, config={'displayModeBar': False}) if pump_activity_fig is not None else dcc.Graph(figure=pump_summary_fig, config={'displayModeBar': False})
            ])),
            md=12, lg=6
        ),
        dbc.Col(
            dbc.Card(dbc.CardBody([
                dcc.Graph(figure=sensor_fig, config={'displayModeBar': False}) if sensor_fig is not None else dcc.Graph(figure=sensor_summary_fig, config={'displayModeBar': False})
            ])),
            md=12, lg=6
        )
    ], className='admin-chart-row g-3 mt-1')

    # Hide bottom overview charts for pumps and sensors (tổng quan máy bơm, tổng quan cảm biến)
    # The `charts_bottom` section is intentionally omitted to keep the admin dashboard concise.
    return dbc.Container([
        summary_cards,
        charts_top
    ], fluid=True, className='admin-dashboard-container')

