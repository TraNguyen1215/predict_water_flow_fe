from dash import html, dcc, callback, Input, Output, State, ctx, MATCH, no_update
import dash_bootstrap_components as dbc
import dash
from dash.exceptions import PreventUpdate
from datetime import datetime
from components.navbar import create_navbar
from api import sensor as api_sensor
from api import pump as api_pump
from api import user as api_user

ROWS_PER_PAGE = 10


def format_date(date_str):
    if date_str:
        try:
            date = datetime.strptime(date_str.split('T')[0], "%Y-%m-%d")
            return date.strftime("%d/%m/%Y")
        except:
            return date_str
    return "N/A"


def fetch_devices_data(token=None):
    """Fetch all device related data"""
    try:
        sensor_types = api_sensor.get_sensor_types(token=token) or {}
        sensor_type_data = sensor_types.get('data', []) if isinstance(sensor_types, dict) else (sensor_types if isinstance(sensor_types, list) else [])
        
        sensors = api_sensor.list_sensors(limit=200, offset=0, token=token) or {}
        sensor_data = sensors.get('data', []) if isinstance(sensors, dict) else (sensors if isinstance(sensors, list) else [])
        
        pumps = api_pump.list_pumps(limit=200, offset=0, token=token) or {}
        pump_data = pumps.get('data', []) if isinstance(pumps, dict) else (pumps if isinstance(pumps, list) else [])
        
        users = api_user.list_users(token=token) or []
        user_data = users if isinstance(users, list) else (users.get('data', []) if isinstance(users, dict) else [])
        
        return {
            'sensor_types': sensor_type_data,
            'sensors': sensor_data,
            'pumps': pump_data,
            'users': user_data
        }
    except Exception as e:
        print(f"Error fetching devices data: {e}")
        return {
            'sensor_types': [],
            'sensors': [],
            'pumps': [],
            'users': []
        }


def create_summary_cards(data):
    """Create summary statistics cards"""
    total_devices = len(data.get('sensors', []))
    total_types = len(data.get('sensor_types', []))
    total_pumps = len(data.get('pumps', []))
    total_users = len(data.get('users', []))
    
    active_sensors = sum(1 for s in data.get('sensors', []) if s.get('trang_thai'))
    
    return dbc.Row([
        dbc.Col(
            dbc.Card([
                dbc.CardBody([
                    html.H4(total_devices, className='card-title text-primary'),
                    html.P('Tổng số thiết bị cảm biến', className='card-text')
                ])
            ], className='mb-3')
        , width=4, md=2),
        dbc.Col(
            dbc.Card([
                dbc.CardBody([
                    html.H4(total_types, className='card-title text-success'),
                    html.P('Loại thiết bị', className='card-text')
                ])
            ], className='mb-3')
        , width=4, md=2),
        dbc.Col(
            dbc.Card([
                dbc.CardBody([
                    html.H4(active_sensors, className='card-title text-info'),
                    html.P('Thiết bị đang hoạt động', className='card-text')
                ])
            ], className='mb-3')
        , width=4, md=2),
        dbc.Col(
            dbc.Card([
                dbc.CardBody([
                    html.H4(total_pumps, className='card-title text-warning'),
                    html.P('Số máy bơm', className='card-text')
                ])
            ], className='mb-3')
        , width=4, md=2),
        dbc.Col(
            dbc.Card([
                dbc.CardBody([
                    html.H4(total_users, className='card-title text-danger'),
                    html.P('Người dùng', className='card-text')
                ])
            ], className='mb-3')
        , width=4, md=2)
    ])


def create_sensors_table(data, search_value='', type_filter='all', user_filter='all', pump_filter='all', status_filter='all'):
    """Create sensors management table"""
    sensors = data.get('sensors', [])
    rows = []
    
    for sensor in sensors:
        identifier = sensor.get('ma_cam_bien', 'N/A')
        sensor_type = sensor.get('loai_cam_bien', {})
        user = sensor.get('nguoi_dung', {})
        pump = sensor.get('may_bom', {})
        status = sensor.get('trang_thai')
        status_label = 'Hoạt động' if status else ('Không hoạt động' if status is not None else 'Chưa xác định')
        
        # Apply filters
        if search_value:
            search_lower = search_value.lower()
            name_match = search_lower in (sensor.get('ten_cam_bien') or '').lower()
            desc_match = search_lower in (sensor.get('mo_ta') or '').lower()
            if not (name_match or desc_match):
                continue
        
        if type_filter != 'all':
            if str(sensor_type.get('ma_loai_cam_bien', '')) != type_filter:
                continue
        
        if user_filter != 'all':
            if str(user.get('ma_nguoi_dung', '')) != user_filter:
                continue
        
        if pump_filter != 'all':
            if str(pump.get('ma_may_bom', '')) != pump_filter:
                continue
        
        if status_filter != 'all':
            if status_filter == 'active' and not status:
                continue
            if status_filter == 'inactive' and status:
                continue
        
        rows.append(html.Tr([
            html.Td(html.Strong(sensor.get('ten_cam_bien', f"CB-{identifier}"))),
            html.Td(sensor_type.get('ten_loai_cam_bien', '--')),
            html.Td(user.get('ho_ten') or user.get('ten_dang_nhap') or '--'),
            html.Td(pump.get('ten_may_bom') or '--'),
            html.Td(sensor.get('mo_ta') or '--', style={'maxWidth': '200px', 'overflow': 'hidden', 'textOverflow': 'ellipsis'}),
            html.Td(format_date(sensor.get('ngay_lap_dat'))),
            html.Td(html.Span(status_label, className=f"user-status-badge {'active' if status else 'inactive'}" if status is not None else ''), className='text-nowrap')
        ]))
    
    table_header = html.Thead(html.Tr([
        html.Th('Tên cảm biến'),
        html.Th('Loại thiết bị'),
        html.Th('Người dùng'),
        html.Th('Máy bơm'),
        html.Th('Mô tả'),
        html.Th('Ngày lắp đặt'),
        html.Th('Trạng thái')
    ]))
    
    table = dbc.Table([
        table_header,
        html.Tbody(rows) if rows else html.Tbody([html.Tr([html.Td('Không có dữ liệu', colSpan=7, className='text-center text-muted')])])
    ], bordered=False, hover=True, responsive=True, className='user-table sensor-table')
    
    return dbc.Card([
        dbc.CardHeader(html.Span('Quản lý thiết bị cảm biến', className='user-table-title')),
        dbc.CardBody([table])
    ], className='user-table-card')


def create_sensor_types_table(data):
    """Create sensor types management table"""
    sensor_types = data.get('sensor_types', [])
    rows = []
    
    for st in sensor_types:
        sensor_count = len(st.get('cam_bien', []))
        active_count = sum(1 for s in st.get('cam_bien', []) if s.get('trang_thai'))
        
        rows.append(html.Tr([
            html.Td(html.Strong(st.get('ten_loai_cam_bien', 'N/A'))),
            html.Td(str(sensor_count)),
            html.Td(html.Span(f"{active_count}/{sensor_count}", className='text-info')),
            html.Td(st.get('mo_ta') or '--'),
            html.Td(format_date(st.get('ngay_tao')))
        ]))
    
    table_header = html.Thead(html.Tr([
        html.Th('Tên loại thiết bị'),
        html.Th('Tổng cảm biến'),
        html.Th('Đang hoạt động'),
        html.Th('Mô tả'),
        html.Th('Ngày tạo')
    ]))
    
    table = dbc.Table([
        table_header,
        html.Tbody(rows) if rows else html.Tbody([html.Tr([html.Td('Không có dữ liệu', colSpan=5, className='text-center text-muted')])])
    ], bordered=False, hover=True, responsive=True, className='user-table')
    
    return dbc.Card([
        dbc.CardHeader(html.Span('Loại thiết bị', className='user-table-title')),
        dbc.CardBody([table])
    ], className='user-table-card')


def create_device_assignment_modal():
    """Modal for assigning devices to users and pumps"""
    return dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("Cấu hình gắn thiết bị")),
        dbc.ModalBody([
            dbc.Form([
                dbc.Row([
                    dbc.Col(dbc.Label("Chọn thiết bị cảm biến", className='fw-bold'), md=12),
                    dbc.Col([
                        dcc.Dropdown(
                            id="device-assignment-sensor",
                            placeholder="Chọn cảm biến...",
                            style={'width': '100%'}
                        )
                    ], md=12)
                ], className="mb-3"),
                dbc.Row([
                    dbc.Col(dbc.Label("Gán cho người dùng", className='fw-bold'), md=12),
                    dbc.Col([
                        dcc.Dropdown(
                            id="device-assignment-user",
                            placeholder="Chọn người dùng...",
                            style={'width': '100%'}
                        )
                    ], md=12)
                ], className="mb-3"),
                dbc.Row([
                    dbc.Col(dbc.Label("Sử dụng cho máy bơm", className='fw-bold'), md=12),
                    dbc.Col([
                        dcc.Dropdown(
                            id="device-assignment-pump",
                            placeholder="Chọn máy bơm...",
                            style={'width': '100%'}
                        )
                    ], md=12)
                ], className="mb-3"),
                dbc.Row([
                    dbc.Col(dbc.Label("Ngày lắp đặt", className='fw-bold'), md=12),
                    dbc.Col([
                        dcc.DatePickerSingle(
                            id="device-assignment-date",
                            date=datetime.now().date(),
                            display_format='DD/MM/YYYY'
                        )
                    ], md=12)
                ], className="mb-3"),
                dbc.Row([
                    dbc.Col(dbc.Checkbox(id='device-assignment-status', label='Hoạt động', value=True), md=12)
                ], className="mb-3")
            ])
        ]),
        dbc.ModalFooter([
            dbc.Button("Hủy", id="cancel-device-assignment", className="me-2", color="secondary"),
            dbc.Button("Lưu", id="save-device-assignment", color="primary")
        ])
    ], id="device-assignment-modal", is_open=False)


def create_sensor_type_modal():
    """Modal for adding/editing sensor types"""
    return dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("Thêm loại thiết bị mới")),
        dbc.ModalBody([
            dbc.Form([
                dbc.Row([
                    dbc.Col(dbc.Label("Tên loại thiết bị", className='fw-bold'), md=12),
                    dbc.Col([
                        dbc.Input(
                            id="new-sensor-type-name",
                            type="text",
                            placeholder="Nhập tên loại thiết bị"
                        )
                    ], md=12)
                ], className="mb-3"),
                dbc.Row([
                    dbc.Col(dbc.Label("Mô tả", className='fw-bold'), md=12),
                    dbc.Col([
                        dbc.Textarea(
                            id="new-sensor-type-desc",
                            placeholder="Nhập mô tả loại thiết bị",
                            style={'height': '80px', 'resize': 'none'}
                        )
                    ], md=12)
                ], className="mb-3")
            ])
        ]),
        dbc.ModalFooter([
            dbc.Button("Hủy", id="cancel-sensor-type-modal", className="me-2", color="secondary"),
            dbc.Button("Lưu", id="save-sensor-type-modal", color="primary")
        ])
    ], id="sensor-type-modal", is_open=False)


layout = html.Div([
    create_navbar(is_authenticated=True, is_admin=True),
    dcc.Location(id='admin-devices-url', refresh=False),
    dcc.Store(id='admin-devices-data-store', data={}),
    
    dbc.Toast(
        id='admin-devices-toast',
        header='Thông báo',
        is_open=False,
        dismissable=True,
        duration=3500,
        icon='success',
        children='',
        style={'position': 'fixed', 'top': '80px', 'right': '24px', 'zIndex': 2100}
    ),
    
    dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H2([
                    html.I(className='fas fa-microchip me-2'), 
                    'Quản lý Thiết bị'
                ], className='text-primary mb-4'),
            ], width=12)
        ]),
        
        # Summary cards
        html.Div(id='devices-summary-cards'),
        
        # Tabs for different management views
        dbc.Tabs([
            # Tab 1: Sensors Management
            dbc.Tab(label='⚙️ Thiết bị cảm biến', children=[
                dbc.Row([
                    dbc.Col([
                        dbc.InputGroup([
                            dbc.Input(
                                id='device-search-input',
                                type='text',
                                placeholder='Tìm kiếm theo tên, mô tả...',
                                className='me-2'
                            ),
                            dcc.Dropdown(
                                id='device-type-filter',
                                placeholder='Lọc theo loại',
                                options=[],
                                style={'width': '150px', 'marginRight': '8px'}
                            ),
                            dcc.Dropdown(
                                id='device-user-filter',
                                placeholder='Lọc theo người dùng',
                                options=[],
                                style={'width': '150px', 'marginRight': '8px'}
                            ),
                            dcc.Dropdown(
                                id='device-pump-filter',
                                placeholder='Lọc theo máy bơm',
                                options=[],
                                style={'width': '150px', 'marginRight': '8px'}
                            ),
                            dcc.Dropdown(
                                id='device-status-filter',
                                placeholder='Lọc theo trạng thái',
                                options=[
                                    {'label': 'Tất cả', 'value': 'all'},
                                    {'label': 'Hoạt động', 'value': 'active'},
                                    {'label': 'Không hoạt động', 'value': 'inactive'}
                                ],
                                value='all',
                                style={'width': '150px', 'marginRight': '8px'}
                            ),
                            dbc.Button(html.Span([
                                html.I(className='fas fa-cog me-2'),
                                'Cấu hình'
                            ]), 
                            id='open-device-assignment-btn', 
                            color='primary',
                            className='d-flex align-items-center'
                            )
                        ], className='mb-3')
                    ], width=12)
                ]),
                
                dbc.Row([
                    dbc.Col([
                        html.Div(id='device-sensors-content')
                    ], width=12)
                ], className='mt-3'),
            ], tab_id='tab-sensors'),
            
            # Tab 2: Sensor Types
            dbc.Tab(label='📋 Loại thiết bị', children=[
                dbc.Row([
                    dbc.Col([
                        dbc.Button(html.Span([
                            html.I(className='fas fa-plus me-2'),
                            'Thêm loại thiết bị'
                        ]), 
                        id='open-sensor-type-btn', 
                        color='success',
                        className='d-flex align-items-center'
                        )
                    ], width=12)
                ], className='mb-3'),
                
                dbc.Row([
                    dbc.Col([
                        html.Div(id='device-types-content')
                    ], width=12)
                ], className='mt-3'),
            ], tab_id='tab-types'),
            
            # Tab 3: Device Configuration
            dbc.Tab(label='🔧 Cấu hình thiết bị', children=[
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader(html.Span('Cấu hình nâng cao thiết bị', className='user-table-title')),
                            dbc.CardBody([
                                dbc.Row([
                                    dbc.Col([
                                        dbc.Label('Chọn thiết bị để cấu hình', className='fw-bold'),
                                        dcc.Dropdown(
                                            id='config-device-select',
                                            placeholder='Chọn thiết bị...',
                                            options=[],
                                            style={'width': '100%'}
                                        )
                                    ], md=6),
                                    dbc.Col([
                                        dbc.Label('Tần suất lấy mẫu (giây)', className='fw-bold'),
                                        dbc.Input(
                                            id='config-sampling-rate',
                                            type='number',
                                            min=1,
                                            max=3600,
                                            value=300,
                                            placeholder='Nhập tần suất lấy mẫu'
                                        )
                                    ], md=6)
                                ], className='mb-3'),
                                
                                dbc.Row([
                                    dbc.Col([
                                        dbc.Label('Độ nhạy (sensitivity)', className='fw-bold'),
                                        dcc.Slider(
                                            id='config-sensitivity',
                                            min=1,
                                            max=100,
                                            step=1,
                                            value=50,
                                            marks={i: str(i) for i in range(1, 101, 10)},
                                            tooltip={"placement": "bottom", "always_visible": True}
                                        )
                                    ], md=12)
                                ], className='mb-3'),
                                
                                dbc.Row([
                                    dbc.Col([
                                        dbc.Label('Giới hạn thấp', className='fw-bold'),
                                        dbc.Input(
                                            id='config-min-value',
                                            type='number',
                                            value=0,
                                            placeholder='Giới hạn thấp'
                                        )
                                    ], md=6),
                                    dbc.Col([
                                        dbc.Label('Giới hạn cao', className='fw-bold'),
                                        dbc.Input(
                                            id='config-max-value',
                                            type='number',
                                            value=100,
                                            placeholder='Giới hạn cao'
                                        )
                                    ], md=6)
                                ], className='mb-3'),
                                
                                dbc.Row([
                                    dbc.Col([
                                        dbc.Button('Lưu cấu hình', id='save-device-config-btn', color='primary', className='w-100')
                                    ], width=12)
                                ])
                            ])
                        ], className='user-table-card')
                    ], width=12)
                ], className='mt-3'),
            ], tab_id='tab-config'),
        ], id='device-management-tabs', active_tab='tab-sensors'),
        
    ], fluid=True, className='py-4', style={'marginBottom': '100px', 'marginTop': '80px'}),
    
    # Modals
    create_device_assignment_modal(),
    create_sensor_type_modal()
])


@callback(
    Output('admin-devices-data-store', 'data'),
    Input('admin-devices-url', 'pathname'),
    State('session-store', 'data'),
    prevent_initial_call='initial_duplicate'
)
def load_devices_data(pathname, session_data):
    if pathname != '/admin/devices':
        raise PreventUpdate
    
    if not session_data or not session_data.get('authenticated') or not session_data.get('is_admin'):
        raise PreventUpdate
    
    token = session_data.get('token')
    data = fetch_devices_data(token=token)
    
    return data


@callback(
    Output('devices-summary-cards', 'children'),
    Input('admin-devices-data-store', 'data')
)
def update_summary_cards(data):
    if not data:
        raise PreventUpdate
    return create_summary_cards(data)


@callback(
    [Output('device-type-filter', 'options'),
     Output('device-user-filter', 'options'),
     Output('device-pump-filter', 'options'),
     Output('config-device-select', 'options')],
    Input('admin-devices-data-store', 'data')
)
def update_filter_options(data):
    if not data:
        raise PreventUpdate
    
    sensor_types = data.get('sensor_types', [])
    sensors = data.get('sensors', [])
    pumps = data.get('pumps', [])
    users = data.get('users', [])
    
    # Sensor type options
    type_options = [{'label': 'Tất cả loại', 'value': 'all'}]
    for st in sensor_types:
        type_options.append({
            'label': st.get('ten_loai_cam_bien', 'N/A'),
            'value': str(st.get('ma_loai_cam_bien', ''))
        })
    
    # User options
    user_options = [{'label': 'Tất cả người dùng', 'value': 'all'}]
    for user in users:
        user_options.append({
            'label': user.get('ho_ten') or user.get('ten_dang_nhap', 'N/A'),
            'value': str(user.get('ma_nguoi_dung', ''))
        })
    
    # Pump options
    pump_options = [{'label': 'Tất cả máy bơm', 'value': 'all'}]
    for pump in pumps:
        pump_options.append({
            'label': pump.get('ten_may_bom', 'N/A'),
            'value': str(pump.get('ma_may_bom', ''))
        })
    
    # Device select options for config
    device_options = []
    for sensor in sensors:
        device_options.append({
            'label': f"{sensor.get('ten_cam_bien', 'N/A')} - {sensor.get('loai_cam_bien', {}).get('ten_loai_cam_bien', 'N/A')}",
            'value': str(sensor.get('ma_cam_bien', ''))
        })
    
    return type_options, user_options, pump_options, device_options


@callback(
    Output('device-sensors-content', 'children'),
    [Input('device-search-input', 'value'),
     Input('device-type-filter', 'value'),
     Input('device-user-filter', 'value'),
     Input('device-pump-filter', 'value'),
     Input('device-status-filter', 'value'),
     Input('admin-devices-data-store', 'data')]
)
def update_sensors_table(search, type_filter, user_filter, pump_filter, status_filter, data):
    if not data:
        raise PreventUpdate
    
    return create_sensors_table(
        data,
        search_value=search or '',
        type_filter=type_filter or 'all',
        user_filter=user_filter or 'all',
        pump_filter=pump_filter or 'all',
        status_filter=status_filter or 'all'
    )


@callback(
    Output('device-types-content', 'children'),
    Input('admin-devices-data-store', 'data')
)
def update_types_table(data):
    if not data:
        raise PreventUpdate
    
    return create_sensor_types_table(data)


@callback(
    Output('device-assignment-modal', 'is_open'),
    [Input('open-device-assignment-btn', 'n_clicks'),
     Input('cancel-device-assignment', 'n_clicks'),
     Input('save-device-assignment', 'n_clicks')],
    prevent_initial_call=True
)
def toggle_assignment_modal(open_clicks, cancel_clicks, save_clicks):
    trigger = ctx.triggered_id if ctx.triggered else None
    
    if trigger == 'open-device-assignment-btn':
        return True
    elif trigger in ['cancel-device-assignment', 'save-device-assignment']:
        return False
    
    raise PreventUpdate


@callback(
    Output('sensor-type-modal', 'is_open'),
    [Input('open-sensor-type-btn', 'n_clicks'),
     Input('cancel-sensor-type-modal', 'n_clicks'),
     Input('save-sensor-type-modal', 'n_clicks')],
    prevent_initial_call=True
)
def toggle_sensor_type_modal(open_clicks, cancel_clicks, save_clicks):
    trigger = ctx.triggered_id if ctx.triggered else None
    
    if trigger == 'open-sensor-type-btn':
        return True
    elif trigger in ['cancel-sensor-type-modal', 'save-sensor-type-modal']:
        return False
    
    raise PreventUpdate


@callback(
    Output('device-assignment-sensor', 'options'),
    Input('admin-devices-data-store', 'data')
)
def update_assignment_sensor_options(data):
    if not data:
        raise PreventUpdate
    
    sensors = data.get('sensors', [])
    options = []
    for sensor in sensors:
        options.append({
            'label': f"{sensor.get('ten_cam_bien', 'N/A')} - {sensor.get('loai_cam_bien', {}).get('ten_loai_cam_bien', 'N/A')}",
            'value': str(sensor.get('ma_cam_bien', ''))
        })
    
    return options


@callback(
    Output('device-assignment-user', 'options'),
    Input('admin-devices-data-store', 'data')
)
def update_assignment_user_options(data):
    if not data:
        raise PreventUpdate
    
    users = data.get('users', [])
    options = []
    for user in users:
        options.append({
            'label': f"{user.get('ho_ten') or user.get('ten_dang_nhap', 'N/A')} ({user.get('ten_dang_nhap', 'N/A')})",
            'value': str(user.get('ma_nguoi_dung', ''))
        })
    
    return options


@callback(
    Output('device-assignment-pump', 'options'),
    Input('admin-devices-data-store', 'data')
)
def update_assignment_pump_options(data):
    if not data:
        raise PreventUpdate
    
    pumps = data.get('pumps', [])
    options = []
    for pump in pumps:
        options.append({
            'label': pump.get('ten_may_bom', 'N/A'),
            'value': str(pump.get('ma_may_bom', ''))
        })
    
    return options


@callback(
    Output('admin-devices-toast', 'is_open'),
    Input('save-device-assignment', 'n_clicks'),
    prevent_initial_call=True
)
def save_device_assignment(n_clicks):
    if not n_clicks:
        raise PreventUpdate
    
    # TODO: Add API call to save device assignment
    return True


@callback(
    Output('admin-devices-toast', 'is_open', allow_duplicate=True),
    Input('save-sensor-type-modal', 'n_clicks'),
    prevent_initial_call=True
)
def save_sensor_type(n_clicks):
    if not n_clicks:
        raise PreventUpdate
    
    # TODO: Add API call to save sensor type
    return True


@callback(
    Output('admin-devices-toast', 'is_open', allow_duplicate=True),
    Input('save-device-config-btn', 'n_clicks'),
    prevent_initial_call=True
)
def save_device_config(n_clicks):
    if not n_clicks:
        raise PreventUpdate
    
    # TODO: Add API call to save device configuration
    return True
