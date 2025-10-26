from dash import html, dcc, callback, Input, Output, State
import dash_bootstrap_components as dbc
import dash
from components.navbar import create_navbar
from api import user as api_user
from api import sensor as api_sensor
from api import pump as api_pump
from api import sensor_data as api_sensor_data
import pandas as pd
import plotly.express as px


layout = html.Div([
    create_navbar(is_authenticated=True, is_admin=True),
    dcc.Location(id='admin-url', refresh=False),
    html.Div(id='admin-dashboard', style={'margin-bottom': '100px', 'margin-top': '80px', 'margin-left': '20px', 'margin-right': '20px'})
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
        sensors = api_sensor.list_sensors(limit=1, offset=0, token=token) or {}
        total_sensors = sensors.get('total', 0) if isinstance(sensors, dict) else 0
    except Exception:
        total_sensors = 0

    try:
        pumps = api_pump.list_pumps(limit=1, offset=0, token=token) or {}
        total_pumps = pumps.get('total', 0) if isinstance(pumps, dict) else 0
    except Exception:
        total_pumps = 0

    try:
        data = api_sensor_data.get_data_by_pump(limit=1, offset=0, token=token) or {}
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

    cards = dbc.Row([
        dbc.Col(dbc.Card(dbc.CardBody([html.H6('Tổng người dùng', className='card-title'), html.H3(str(total_users))])), md=3),
        dbc.Col(dbc.Card(dbc.CardBody([html.H6('Tổng cảm biến', className='card-title'), html.H3(str(total_sensors))])), md=3),
        dbc.Col(dbc.Card(dbc.CardBody([html.H6('Tổng máy bơm', className='card-title'), html.H3(str(total_pumps))])), md=3),
        dbc.Col(dbc.Card(dbc.CardBody([html.H6('Tổng bản ghi cảm biến', className='card-title'), html.H3(str(total_data))])), md=3),
    ], className='mb-4')

    charts_row = html.Div()
    try:
        df = pd.DataFrame(users) if users else pd.DataFrame()

        if not df.empty:
            if 'vai_tro' in df.columns:
                df['role_mapped'] = df['vai_tro'].fillna('user')
            elif 'role' in df.columns:
                df['role_mapped'] = df['role'].fillna('user')
            else:
                if 'is_admin' in df.columns:
                    df['role_mapped'] = df['is_admin'].apply(lambda v: 'admin' if v else 'user')
                else:
                    df['role_mapped'] = 'user'

            if 'trang_thai' in df.columns:
                df['active_mapped'] = df['trang_thai'].apply(lambda v: 'active' if v in (True, 'active', 'dang_hoat_dong', 1) else 'inactive')
            else:
                df['active_mapped'] = 'unknown'

            role_counts = df['role_mapped'].value_counts().rename_axis('role').reset_index(name='count')
            fig_roles = px.pie(role_counts, names='role', values='count', title='Phân bố vai trò người dùng')
            
            act_counts = df['active_mapped'].value_counts().rename_axis('status').reset_index(name='count')
            fig_active = px.bar(act_counts, x='status', y='count', title='Trạng thái hoạt động')

            fig_reg = None
            if 'thoi_gian_tao' in df.columns:
                df['thoi_tao'] = pd.to_datetime(df['thoi_gian_tao'], errors='coerce')
                if df['thoi_tao'].notna().any():
                    monthly = df.dropna(subset=['thoi_tao']).set_index('thoi_tao').resample('ME').size().reset_index(name='count')
                    if not monthly.empty:
                        fig_reg = px.line(monthly, x='thoi_tao', y='count', markers=True, title='Người dùng đăng ký theo tháng')

            left_col = html.Div([
                dcc.Graph(figure=fig_roles, style={'height': '350px'}),
                dcc.Graph(figure=fig_active, style={'height': '300px'})
            ])

            right_col_children = []
            if fig_reg is not None:
                right_col_children.append(dcc.Graph(figure=fig_reg, style={'height': '680px'}))
            else:
                right_col_children.append(dbc.Alert('Không có dữ liệu đăng ký để vẽ biểu đồ theo thời gian', color='secondary'))

            charts_row = dbc.Row([
                dbc.Col(left_col, md=6),
                dbc.Col(right_col_children, md=6)
            ], className='mb-4')
        else:
            charts_row = dbc.Alert('Không có dữ liệu người dùng để hiển thị biểu đồ.', color='info')
    except Exception:
        charts_row = dbc.Alert('Lỗi khi tạo biểu đồ người dùng.', color='danger')

    activity = dbc.Row([
        dbc.Col(dbc.Card(dbc.CardBody([
            html.H6('Đang đăng nhập', className='card-title'),
            html.P(current_user or 'Không có', className='mb-0')
        ])), md=6),
        dbc.Col(dbc.Card(dbc.CardBody([
            html.H6('Người dùng hoạt động', className='card-title'),
            html.Ul([html.Li(str(u)) for u in (active_users[:10] if active_users else ['Không có'])])
        ])), md=6),
    ], className='mb-4')

    return html.Div([cards, charts_row, activity])

