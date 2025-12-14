from dash import html, dcc, callback, Input, Output, State, ctx, MATCH, ALL, no_update
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
        
        # Extract sensors from sensor types structure
        extracted_sensors = []
        for st in sensor_type_data:
            type_info = {
                'ma_loai_cam_bien': st.get('ma_loai_cam_bien'),
                'ten_loai_cam_bien': st.get('ten_loai_cam_bien')
            }
            for s in st.get('cam_bien', []):
                s_copy = s.copy()
                s_copy['loai_cam_bien'] = type_info
                extracted_sensors.append(s_copy)
        
        pumps = api_pump.list_pumps(limit=200, offset=0, token=token) or {}
        pump_data = pumps.get('data', []) if isinstance(pumps, dict) else (pumps if isinstance(pumps, list) else [])
        
        users = api_user.list_users(token=token) or []
        user_data = users if isinstance(users, list) else (users.get('data', []) if isinstance(users, dict) else [])
        
        return {
            'sensor_types': sensor_type_data,
            'sensors': extracted_sensors,
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


def create_sensors_table(data, search_value='', type_filter='all', user_filter='all', status_filter='all', pump_filter='all', filter_date=None):
    """Create sensors management table"""
    sensors = data.get('sensors', [])
    rows = []
    
    for sensor in sensors:
        identifier = sensor.get('ma_cam_bien', 'N/A')
        sensor_type = sensor.get('loai_cam_bien', {})
        user = sensor.get('nguoi_dung', {})
        pump = sensor.get('may_bom', {})
        status = sensor.get('trang_thai') # True/False
        
        # Get last updated time
        updated_at = sensor.get('thoi_gian_cap_nhat')
        last_updated = "Chưa cập nhật"
        if updated_at:
            try:
                # Try to parse full datetime
                dt_part = str(updated_at).split('.')[0].replace('Z', '')
                dt = datetime.strptime(dt_part, "%Y-%m-%dT%H:%M:%S")
                last_updated = dt.strftime("%H:%M %d/%m/%Y")
            except:
                # Fallback to date only
                last_updated = format_date(updated_at)
        
        # Apply filters
        if search_value:
            search_lower = search_value.lower()
            name_match = search_lower in (sensor.get('ten_cam_bien') or '').lower()
            code_match = search_lower in str(identifier).lower()
            user_match = search_lower in (user.get('ho_ten') or '').lower()
            if not (name_match or code_match or user_match):
                continue
        
        if type_filter != 'all':
            if str(sensor_type.get('ma_loai_cam_bien', '')) != type_filter:
                continue
        
        if user_filter != 'all':
            if str(user.get('ma_nguoi_dung', '')) != user_filter:
                continue
        
        if status_filter != 'all':
            if status_filter == 'active' and not status:
                continue
            if status_filter == 'inactive' and status:
                continue

        if pump_filter != 'all':
            if str(pump.get('ma_may_bom', '')) != pump_filter:
                continue

        if filter_date:
            try:
                install_date_str = sensor.get('ngay_lap_dat')
                if install_date_str:
                    install_date = datetime.strptime(install_date_str.split('T')[0], "%Y-%m-%d").date()
                    target_date = datetime.strptime(filter_date.split('T')[0], "%Y-%m-%d").date()
                    if install_date != target_date:
                        continue
                else:
                    continue
            except:
                pass

        # Status Dot
        status_color = 'success' if status else 'danger'
        status_text = "Đang hoạt động" if status else "Không hoạt động"
        
        rows.append(html.Tr([
            # Device Info
            html.Td([
                html.Div(html.Strong(sensor.get('ten_cam_bien', 'N/A')), className='mb-1'),
                html.Div([
                    html.Span(f"Mã: CB-{identifier}", className='text-muted small me-2'),
                    html.I(className="far fa-copy text-primary cursor-pointer", title="Copy", id={'type': 'copy-sensor-id', 'index': str(identifier)})
                ], className='d-flex align-items-center')
            ]),
            # Type
            html.Td([
                html.Span(sensor_type.get('ten_loai_cam_bien', '--'))
            ]),
            # Owner
            html.Td([
                html.Div([
                    html.Span(user.get('ho_ten') or user.get('ten_dang_nhap') or '--', className='text-primary cursor-pointer')
                ], className='d-flex align-items-center')
            ]),
            # Associated Device (Pump)
            html.Td(pump.get('ten_may_bom') or '--'),
            # Status
            html.Td([
                html.Div([
                    html.Span(className=f"bg-{status_color} rounded-circle d-inline-block me-2", style={'width': '10px', 'height': '10px'}),
                    html.Span(status_text)
                ], className='d-flex align-items-center'),
                html.Div(html.Small(f"Cập nhật: {last_updated}", className='text-muted'), className='mt-1')
            ]),
            # Installation Date
            html.Td(format_date(sensor.get('ngay_lap_dat'))),
            # Actions
            html.Td([
                dbc.Button(html.I(className="fas fa-edit"), color="light", size="sm", className="me-1", title="Sửa", id={'type': 'edit-sensor-btn', 'index': str(identifier)}),
                dbc.Button(html.I(className="fas fa-info-circle"), color="light", size="sm", className="me-1", title="Chi tiết", id={'type': 'open-sensor-detail', 'index': str(identifier)}),
                dbc.Button(html.I(className="fas fa-trash"), color="light", size="sm", title="Xóa", id={'type': 'delete-sensor-btn', 'index': str(identifier)})
            ])
        ]))
    
    table_header = html.Thead(html.Tr([
        html.Th('Thông tin thiết bị'),
        html.Th('Loại cảm biến'),
        html.Th('Tên người dùng'),
        html.Th('Thiết bị sở hữu'),
        html.Th('Trạng thái'),
        html.Th('Ngày lắp đặt'),
        html.Th('Hành động')
    ]))
    
    table = dbc.Table([
        table_header,
        html.Tbody(rows) if rows else html.Tbody([html.Tr([html.Td('Không có dữ liệu', colSpan=7, className='text-center text-muted')])])
    ], bordered=False, hover=True, responsive=True, className='user-table sensor-table align-middle')
    
    return dbc.Card([
        dbc.CardBody([table], className='p-0')
    ], className='user-table-card border-0 shadow-sm')


def create_pumps_table(data, search_value='', user_filter='all', status_filter='all'):
    """Create pumps management table"""
    pumps = data.get('pumps', [])
    rows = []
    
    for pump in pumps:
        identifier = pump.get('ma_may_bom', 'N/A')
        user = pump.get('nguoi_dung', {})
        status = pump.get('trang_thai') # True (ON) / False (OFF)
        
        # Mock data
        runtime = "1h 30p" if status else ""
        control_mode = "auto" # or manual
        power = "1000W" # from mo_ta
        flow = "100L/h" # from mo_ta
        
        # Apply filters
        if search_value:
            search_lower = search_value.lower()
            name_match = search_lower in (pump.get('ten_may_bom') or '').lower()
            code_match = search_lower in str(identifier).lower()
            user_match = search_lower in (user.get('ho_ten') or '').lower()
            if not (name_match or code_match or user_match):
                continue
        
        if user_filter != 'all':
            if str(user.get('ma_nguoi_dung', '')) != user_filter:
                continue
        
        if status_filter != 'all':
            if status_filter == 'active' and not status:
                continue
            if status_filter == 'inactive' and status:
                continue

        # Status Badge
        status_badge = dbc.Badge(
            [html.I(className="fas fa-power-off me-1"), "ON" if status else "OFF"],
            color="success" if status else "secondary",
            className="me-2"
        )
        
        # Control Mode Badge
        mode_badge = dbc.Badge(
            "Auto" if control_mode == 'auto' else "Manual",
            color="primary" if control_mode == 'auto' else "warning",
            pill=True
        )

        rows.append(html.Tr([
            # Pump Info
            html.Td([
                html.Div(html.Strong(pump.get('ten_may_bom', 'N/A')), className='mb-1'),
                html.Div(html.Small(f"Mã: {identifier}", className='text-muted'))
            ]),
            # Owner
            html.Td(user.get('ho_ten') or user.get('ten_dang_nhap') or '--'),
            # Operating Status
            html.Td([
                html.Div([status_badge, html.Span(runtime, className='small text-muted') if status else None])
            ]),
            # Control Mode
            html.Td(mode_badge),
            # Specs
            html.Td([
                html.Div(f"Công suất: {power}", className='small'),
                html.Div(f"Lưu lượng: {flow}", className='small text-muted')
            ]),
            # Actions
            html.Td([
                dbc.Button(html.I(className="fas fa-history"), color="light", size="sm", className="me-1", title="Nhật ký"),
                dbc.Button(html.I(className="fas fa-cog"), color="light", size="sm", className="me-1", title="Cấu hình"),
                dbc.Button(html.I(className="fas fa-edit"), color="light", size="sm", title="Sửa", id={'type': 'edit-pump-btn', 'index': str(identifier)}),
                dbc.Button(html.I(className="fas fa-trash"), color="light", size="sm", title="Xóa", className="ms-1", id={'type': 'delete-pump-btn', 'index': str(identifier)})
            ])
        ]))
    
    table_header = html.Thead(html.Tr([
        html.Th('Thông tin Máy bơm'),
        html.Th('Người sở hữu'),
        html.Th('Trạng thái hoạt động'),
        html.Th('Chế độ điều khiển'),
        html.Th('Thông số kỹ thuật'),
        html.Th('Hành động')
    ]))
    
    table = dbc.Table([
        table_header,
        html.Tbody(rows) if rows else html.Tbody([html.Tr([html.Td('Không có dữ liệu', colSpan=6, className='text-center text-muted')])])
    ], bordered=False, hover=True, responsive=True, className='align-middle')

    return dbc.Card([
        dbc.CardBody([table], className='p-0')
    ], className='user-table-card border-0 shadow-sm')


def create_sensor_types_table(data):
    """Create sensor types management table"""
    sensor_types = data.get('sensor_types', [])
    rows = []
    
    for st in sensor_types:
        sensor_count = len(st.get('cam_bien', []))
        active_count = sum(1 for s in st.get('cam_bien', []) if s.get('trang_thai'))
        identifier = st.get('ma_loai_cam_bien')
        
        rows.append(html.Tr([
            html.Td(html.Strong(st.get('ten_loai_cam_bien', 'N/A'))),
            html.Td(str(sensor_count)),
            html.Td(html.Span(f"{active_count}/{sensor_count}", className='text-info')),
            html.Td(st.get('mo_ta') or '--'),
            html.Td(format_date(st.get('thoi_gian_tao'))),
            html.Td([
                dbc.Button(html.I(className="fas fa-edit"), color="light", size="sm", className="me-1", title="Sửa", id={'type': 'edit-type-btn', 'index': str(identifier)}),
                dbc.Button(html.I(className="fas fa-trash"), color="light", size="sm", title="Xóa", id={'type': 'delete-type-btn', 'index': str(identifier)})
            ])
        ]))
    
    table_header = html.Thead(html.Tr([
        html.Th('Tên loại thiết bị'),
        html.Th('Tổng cảm biến'),
        html.Th('Đang hoạt động'),
        html.Th('Mô tả'),
        html.Th('Ngày tạo'),
        html.Th('Hành động')
    ]))
    
    table = dbc.Table([
        table_header,
        html.Tbody(rows) if rows else html.Tbody([html.Tr([html.Td('Không có dữ liệu', colSpan=6, className='text-center text-muted')])])
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
    ], id="device-assignment-modal", is_open=False, centered=True)


def create_sensor_type_modal():
    """Modal for adding/editing sensor types"""
    return dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("Thêm loại thiết bị mới", id="sensor-type-modal-title")),
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
    ], id="sensor-type-modal", is_open=False, centered=True)


def create_edit_sensor_modal():
    """Modal for editing sensor"""
    return dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("Chỉnh sửa cảm biến", id="edit-sensor-modal-title")),
        dbc.ModalBody([
            dbc.Form([
                dbc.Row([
                    dbc.Col(dbc.Label("Tên cảm biến", className='fw-bold'), md=12),
                    dbc.Col([
                        dbc.Input(id="edit-sensor-name", type="text")
                    ], md=12)
                ], className="mb-3"),
                dbc.Row([
                    dbc.Col(dbc.Label("Mô tả", className='fw-bold'), md=12),
                    dbc.Col([
                        dbc.Textarea(id="edit-sensor-desc", style={'height': '80px', 'resize': 'none'})
                    ], md=12)
                ], className="mb-3"),
                dbc.Row([
                    dbc.Col(dbc.Label("Máy bơm", className='fw-bold'), md=12),
                    dbc.Col([
                        dcc.Dropdown(id="edit-sensor-pump", placeholder="Chọn máy bơm")
                    ], md=12)
                ], className="mb-3"),
                dbc.Row([
                    dbc.Col(dbc.Label("Loại cảm biến", className='fw-bold'), md=12),
                    dbc.Col([
                        dcc.Dropdown(id="edit-sensor-type", placeholder="Chọn loại cảm biến")
                    ], md=12)
                ], className="mb-3"),
                dbc.Row([
                    dbc.Col(dbc.Label("Ngày lắp đặt", className='fw-bold'), md=12),
                    dbc.Col([
                        dcc.DatePickerSingle(
                            id="edit-sensor-date",
                            display_format='DD/MM/YYYY',
                            style={'width': '100%'}
                        )
                    ], md=12)
                ], className="mb-3"),
                dbc.Row([
                    dbc.Col(dbc.Label("Trạng thái", className='fw-bold'), md=12),
                    dbc.Col([
                        dbc.Select(
                            id="edit-sensor-status",
                            options=[
                                {"label": "Hoạt động", "value": "active"},
                                {"label": "Không hoạt động", "value": "inactive"}
                            ]
                        )
                    ], md=12)
                ], className="mb-3")
            ])
        ]),
        dbc.ModalFooter([
            dbc.Button("Hủy", id="cancel-edit-sensor", className="me-2", color="secondary"),
            dbc.Button("Lưu", id="save-edit-sensor", color="primary")
        ])
    ], id="edit-sensor-modal", is_open=False, centered=True)


def create_edit_pump_modal():
    """Modal for editing pump"""
    return dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("Chỉnh sửa máy bơm", id="edit-pump-modal-title")),
        dbc.ModalBody([
            dbc.Form([
                dbc.Row([
                    dbc.Col(dbc.Label("Tên máy bơm", className='fw-bold'), md=12),
                    dbc.Col([
                        dbc.Input(id="edit-pump-name", type="text")
                    ], md=12)
                ], className="mb-3"),
                dbc.Row([
                    dbc.Col(dbc.Label("Mô tả", className='fw-bold'), md=12),
                    dbc.Col([
                        dbc.Textarea(id="edit-pump-desc", style={'height': '80px', 'resize': 'none'})
                    ], md=12)
                ], className="mb-3"),
                dbc.Row([
                    dbc.Col(dbc.Label("Chế độ", className='fw-bold'), md=12),
                    dbc.Col([
                        dbc.Select(
                            id="edit-pump-mode",
                            options=[
                                {"label": "Thủ công", "value": "0"},
                                {"label": "Tự động", "value": "1"}
                            ],
                            value="0"
                        )
                    ], md=12)
                ], className="mb-3"),
                dbc.Row([
                    dbc.Col(dbc.Label("Trạng thái", className='fw-bold'), md=12),
                    dbc.Col([
                        dbc.Select(
                            id="edit-pump-status",
                            options=[
                                {"label": "Hoạt động", "value": "active"},
                                {"label": "Không hoạt động", "value": "inactive"}
                            ]
                        )
                    ], md=12)
                ], className="mb-3"),
                dbc.Row([
                    dbc.Col([
                        dbc.Checkbox(
                            id="edit-pump-time-limit",
                            label="Giới hạn thời gian",
                            value=True
                        )
                    ], md=12)
                ], className="mb-3")
            ])
        ]),
        dbc.ModalFooter([
            dbc.Button("Hủy", id="cancel-edit-pump", className="me-2", color="secondary"),
            dbc.Button("Lưu", id="save-edit-pump", color="primary")
        ])
    ], id="edit-pump-modal", is_open=False, centered=True)


def create_delete_confirm_modal():
    """Modal for delete confirmation"""
    return dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("Xác nhận xóa")),
        dbc.ModalBody(html.P("Bạn có chắc chắn muốn xóa mục này?", id="delete-confirm-body")),
        dbc.ModalFooter([
            dbc.Button("Hủy", id="cancel-delete", className="me-2", color="secondary"),
            dbc.Button("Xóa", id="confirm-delete", color="danger")
        ])
    ], id="delete-confirm-modal", is_open=False, centered=True)


def create_mini_dashboard(data):
    """Create mini dashboard with stats"""
    sensors = data.get('sensors', [])
    pumps = data.get('pumps', [])
    
    total_devices = len(sensors) + len(pumps)
    
    online_sensors = sum(1 for s in sensors if s.get('trang_thai'))
    online_pumps = sum(1 for p in pumps if p.get('trang_thai'))
    total_online = online_sensors + online_pumps
    
    offline_sensors = len(sensors) - online_sensors
    offline_pumps = len(pumps) - online_pumps
    total_offline = offline_sensors + offline_pumps
    
    return dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.Div([
                            html.H6("Tổng thiết bị", className="stat-label"),
                            html.H3(f"{total_devices:,}", className="stat-value"),
                            html.Small("Thiết bị", className="stat-desc text-muted")
                        ]),
                        html.I(className="fas fa-microchip stat-icon text-primary")
                    ], className="stat-card-content")
                ])
            ], className="stat-card-wrapper")
        ], md=4),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.Div([
                            html.H6("Đang Online", className="stat-label"),
                            html.H3(f"{total_online:,}", className="stat-value"),
                            html.Small("Hoạt động", className="stat-desc text-muted")
                        ]),
                        html.I(className="fas fa-wifi stat-icon text-success")
                    ], className="stat-card-content")
                ])
            ], className="stat-card-wrapper")
        ], md=4),
        
        dbc.Col([
            html.Div(
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.Div([
                                html.H6("Cảnh báo/Offline", className="stat-label"),
                                html.H3(f"{total_offline:,}", className="stat-value"),
                                html.Small("Cần kiểm tra", className="stat-desc text-muted")
                            ]),
                            html.I(className="fas fa-exclamation-triangle stat-icon text-danger")
                        ], className="stat-card-content")
                    ])
                ], className="stat-card-wrapper"),
                id="filter-offline-btn", style={'cursor': 'pointer'}
            )
        ], md=4),
    ], className="mb-4")


def create_drawer():
    """Create slide-in drawer for device details"""
    return dbc.Offcanvas(
        html.Div([
            # Content will be populated by callback
            html.Div(id="drawer-content")
        ]),
        id="device-detail-drawer",
        title="Chi tiết thiết bị",
        is_open=False,
        placement="end",
        style={'width': '400px'}
    )



layout = html.Div([
    create_navbar(is_authenticated=True, is_admin=True),
    dcc.Location(id='admin-devices-url', refresh=False),
    dcc.Store(id='session-store', storage_type='session'),
    dcc.Store(id='admin-devices-data-store', data={}),
    dcc.Store(id='current-action-store', data={}),
    
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
                html.Div(id='mini-dashboard-container')
            ], width=12)
        ]),
        
        dbc.Row([
            dbc.Col([
                dbc.Button([
                    html.I(className='fas fa-plus me-2'),
                    "Thêm thiết bị mới"
                ], color="success", id="add-device-btn", className="float-end mb-3")
            ], width=12)
        ]),
        
        # Tabs
        dbc.Tabs([
            # Tab 1: Sensors
            dbc.Tab(label='Danh sách Cảm biến', children=[
                html.Div([
                    # Toolbar
                    dbc.Row([
                        dbc.Col([
                            dbc.InputGroup([
                                dbc.InputGroupText(html.I(className='fas fa-search')),
                                dbc.Input(id='ad-sensor-search', placeholder='Tìm kiếm...', type='text'),
                            ])
                        ], width=2),
                        dbc.Col([
                            dcc.Dropdown(id='ad-sensor-type-filter', placeholder='Loại CB', value='all')
                        ], width=2),
                         dbc.Col([
                            dcc.Dropdown(id='ad-sensor-pump-filter', placeholder='Máy bơm', value='all')
                        ], width=2),
                        dbc.Col([
                            dcc.Dropdown(
                                id='ad-sensor-status-filter',
                                options=[
                                    {'label': 'Tất cả', 'value': 'all'},
                                    {'label': 'Đang hoạt động', 'value': 'active'},
                                    {'label': 'Không hoạt động', 'value': 'inactive'}
                                ],
                                value='all',
                                placeholder='Trạng thái',
                                clearable=False
                            )
                        ], width=2),
                        dbc.Col([
                            dcc.Dropdown(id='ad-sensor-user-filter', placeholder='Người dùng', value='all')
                        ], width=2),
                        dbc.Col([
                            dcc.DatePickerSingle(
                                id='ad-sensor-date-filter',
                                display_format='DD/MM/YYYY',
                                placeholder='Chọn ngày',
                                style={'width': '100%'}
                            )
                        ], width=2),
                    ], className='mb-3 mt-3'),
                    
                    # Table
                    html.Div(id='device-sensors-content')
                ])
            ], tab_id='tab-sensors'),
            
            # Tab 2: Pumps
            dbc.Tab(label='Danh sách Máy bơm', children=[
                html.Div([
                    # Toolbar
                    dbc.Row([
                        dbc.Col([
                            dbc.InputGroup([
                                dbc.InputGroupText(html.I(className='fas fa-search')),
                                dbc.Input(id='ad-pump-search', placeholder='Tìm theo tên, mã máy bơm...', type='text'),
                            ])
                        ], width=4),
                        dbc.Col([
                            dcc.Dropdown(
                                id='ad-pump-status-filter',
                                options=[
                                    {'label': 'Tất cả', 'value': 'all'},
                                    {'label': 'Đang hoạt động', 'value': 'active'},
                                    {'label': 'Đang tắt', 'value': 'inactive'}
                                ],
                                value='all',
                                placeholder='Trạng thái',
                                clearable=False
                            )
                        ], width=3),
                        dbc.Col([
                            dcc.Dropdown(id='ad-pump-user-filter', placeholder='Lọc theo người dùng', value='all')
                        ], width=3),
                        dbc.Col([
                            # Placeholder
                        ], width=2)
                    ], className='mb-3 mt-3'),
                    
                    # Table
                    html.Div(id='device-pumps-content')
                ])
            ], tab_id='tab-pumps'),
            
            # Tab 3: Device Types
            dbc.Tab(label='Quản lý Loại thiết bị', children=[
                html.Div([
                    dbc.Row([
                        dbc.Col([
                            dbc.Button([html.I(className='fas fa-plus me-2'), "Thêm loại thiết bị"], color='primary', id='open-sensor-type-btn')
                        ], className='mb-3 mt-3 text-end')
                    ]),
                    html.Div(id='device-types-content')
                ])
            ], tab_id='tab-types')
        ], id='device-management-tabs', active_tab='tab-sensors'),
        
    ], fluid=True, className='py-4', style={'marginBottom': '100px', 'marginTop': '80px', 'paddingLeft': '20px', 'paddingRight': '20px'}),
    
    # Modals & Drawers
    create_device_assignment_modal(),
    create_sensor_type_modal(),
    create_edit_sensor_modal(),
    create_edit_pump_modal(),
    create_delete_confirm_modal(),
    create_drawer(),
    
    # Add Device Popup
    dbc.Modal([
        dbc.ModalHeader("Thêm thiết bị mới"),
        dbc.ModalBody([
            dbc.Row([
                dbc.Col([
                    dbc.Button([
                        html.Div(html.I(className="fas fa-wifi fa-3x mb-3")),
                        "Thêm Cảm biến"
                    ], color="primary", outline=True, className="w-100 h-100 p-4", id="btn-add-sensor")
                ], width=6),
                dbc.Col([
                    dbc.Button([
                        html.Div(html.I(className="fas fa-water fa-3x mb-3")),
                        "Thêm Máy bơm"
                    ], color="info", outline=True, className="w-100 h-100 p-4", id="btn-add-pump")
                ], width=6)
            ])
        ])
    ], id="add-device-modal", is_open=False, size="lg", centered=True)
])


@callback(
    Output('admin-devices-data-store', 'data'),
    Input('admin-devices-url', 'pathname'),
    State('session-store', 'data'),
    prevent_initial_call='initial_duplicate'
)
def load_or_reset_devices_data(pathname, session_data):
    """Load devices data when navigating to /admin/devices, reset when navigating away"""
    if pathname != '/admin/devices':
        return {}
    
    if not session_data or not session_data.get('authenticated') or not session_data.get('is_admin'):
        raise PreventUpdate
    
    token = session_data.get('token')
    data = fetch_devices_data(token=token)
    
    return data


@callback(
    [Output('ad-sensor-user-filter', 'options'),
     Output('ad-pump-user-filter', 'options'),
     Output('ad-sensor-type-filter', 'options'),
     Output('ad-sensor-pump-filter', 'options')],
    Input('admin-devices-data-store', 'data')
)
def update_filter_options(data):
    if not data:
        raise PreventUpdate
    
    users = data.get('users', [])
    sensor_types = data.get('sensor_types', [])
    pumps = data.get('pumps', [])
    
    # User options
    user_options = [{'label': 'Tất cả người dùng', 'value': 'all'}]
    for user in users:
        user_options.append({
            'label': user.get('ho_ten') or user.get('ten_dang_nhap', 'N/A'),
            'value': str(user.get('ma_nguoi_dung', ''))
        })
        
    # Sensor Type options
    type_options = [{'label': 'Tất cả loại cảm biến', 'value': 'all'}]
    for st in sensor_types:
        type_options.append({
            'label': st.get('ten_loai_cam_bien', 'N/A'),
            'value': str(st.get('ma_loai_cam_bien', ''))
        })
        
    # Pump options
    pump_options = [{'label': 'Tất cả máy bơm', 'value': 'all'}]
    for pump in pumps:
        pump_options.append({
            'label': pump.get('ten_may_bom', 'N/A'),
            'value': str(pump.get('ma_may_bom', ''))
        })
    
    return user_options, user_options, type_options, pump_options


@callback(
    Output('device-sensors-content', 'children'),
    [Input('ad-sensor-search', 'value'),
     Input('ad-sensor-user-filter', 'value'),
     Input('ad-sensor-status-filter', 'value'),
     Input('ad-sensor-type-filter', 'value'),
     Input('ad-sensor-pump-filter', 'value'),
     Input('ad-sensor-date-filter', 'date'),
     Input('admin-devices-data-store', 'data')]
)
def update_sensors_table(search, user_filter, status_filter, type_filter, pump_filter, filter_date, data):
    if not data:
        raise PreventUpdate
    
    return create_sensors_table(
        data,
        search_value=search or '',
        user_filter=user_filter or 'all',
        status_filter=status_filter or 'all',
        type_filter=type_filter or 'all',
        pump_filter=pump_filter or 'all',
        filter_date=filter_date
    )





@callback(
    Output('device-pumps-content', 'children'),
    [Input('ad-pump-search', 'value'),
     Input('ad-pump-user-filter', 'value'),
     Input('ad-pump-status-filter', 'value'),
     Input('admin-devices-data-store', 'data')]
)
def update_pumps_table(search, user_filter, status_filter, data):
    if not data:
        raise PreventUpdate
    
    return create_pumps_table(
        data,
        search_value=search or '',
        user_filter=user_filter or 'all',
        status_filter=status_filter or 'all'
    )


@callback(
    Output('mini-dashboard-container', 'children'),
    Input('admin-devices-data-store', 'data')
)
def update_mini_dashboard_callback(data):
    if not data:
        raise PreventUpdate
    return create_mini_dashboard(data)


@callback(
    Output('ad-sensor-status-filter', 'value', allow_duplicate=True),
    Input('filter-offline-btn', 'n_clicks'),
    prevent_initial_call=True
)
def filter_offline_devices(n_clicks):
    if not n_clicks:
        raise PreventUpdate
    return 'inactive'


@callback(
    Output('add-device-modal', 'is_open'),
    [Input('add-device-btn', 'n_clicks'),
     Input('btn-add-sensor', 'n_clicks'),
     Input('btn-add-pump', 'n_clicks')],
    State('add-device-modal', 'is_open'),
    prevent_initial_call=True
)
def toggle_add_device_modal(n1, n2, n3, is_open):
    if n1 or n2 or n3:
        return not is_open
    return is_open


@callback(
    [Output('device-detail-drawer', 'is_open'),
     Output('drawer-content', 'children')],
    [Input({'type': 'open-sensor-detail', 'index': ALL}, 'n_clicks')],
    [State('admin-devices-data-store', 'data')],
    prevent_initial_call=True
)
def toggle_drawer(n_clicks, data):
    if not any(n_clicks):
        raise PreventUpdate
    
    ctx_triggered = ctx.triggered_id
    if not ctx_triggered:
        raise PreventUpdate
        
    device_id = ctx_triggered['index']
    
    # Find device data
    sensors = data.get('sensors', [])
    device = next((s for s in sensors if str(s.get('ma_cam_bien')) == str(device_id)), None)
    
    if not device:
        return False, no_update
        
    # Create drawer content
    content = html.Div([
        html.Div([
            html.H4(device.get('ten_cam_bien', 'N/A'), className='mb-1'),
            html.Span(f"Mã: CB-{device_id}", className='text-muted')
        ], className='mb-4'),
        
        html.Div([
            html.H6("Thông tin chung", className='fw-bold mb-3'),
            html.Div([
                html.Img(src="https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=" + str(device_id), className='mb-3 border p-2 rounded'),
                html.P([html.Strong("Vị trí: "), device.get('vi_tri_lap_dat', 'Chưa cập nhật')]),
                html.P([html.Strong("Ngày lắp đặt: "), format_date(device.get('ngay_lap_dat'))]),
            ])
        ], className='mb-4'),
        
        html.Div([
            html.H6("Biểu đồ 24h qua", className='fw-bold mb-3'),
            html.Div("Biểu đồ sẽ hiển thị ở đây...", className='bg-light p-4 text-center rounded text-muted')
        ], className='mb-4'),
        
        html.Div([
            html.H6("Lịch sử cảnh báo", className='fw-bold mb-3'),
            dbc.ListGroup([
                dbc.ListGroupItem([
                    html.Div([
                        html.Strong("Pin yếu", className='text-warning'),
                        html.Small("10:30 AM", className='float-end text-muted')
                    ]),
                    html.Small("Pin thiết bị xuống dưới 20%", className='text-muted')
                ])
            ], flush=True)
        ], className='mb-4'),
        
        html.Div([
            html.H6("Cấu hình hiện tại", className='fw-bold mb-3'),
            dbc.Table([
                html.Tbody([
                    html.Tr([html.Td("Ngưỡng trên"), html.Td("80%")]),
                    html.Tr([html.Td("Ngưỡng dưới"), html.Td("20%")]),
                    html.Tr([html.Td("Chu kỳ gửi"), html.Td("5 phút")])
                ])
            ], bordered=True, size='sm')
        ])
    ])
    
    return True, content


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
    [Output('sensor-type-modal', 'is_open'),
     Output('new-sensor-type-name', 'value'),
     Output('new-sensor-type-desc', 'value'),
     Output('sensor-type-modal-title', 'children'),
     Output('current-action-store', 'data', allow_duplicate=True)],
    [Input('open-sensor-type-btn', 'n_clicks'),
     Input({'type': 'edit-type-btn', 'index': ALL}, 'n_clicks'),
     Input('cancel-sensor-type-modal', 'n_clicks')],
    [State('admin-devices-data-store', 'data'),
     State('current-action-store', 'data')],
    prevent_initial_call=True
)
def toggle_sensor_type_modal(open_click, edit_clicks, cancel, data, current_action):
    trigger = ctx.triggered_id if ctx.triggered else None
    
    if not trigger:
        raise PreventUpdate
        
    # Check if the trigger value is valid (not None/0)
    if not ctx.triggered[0]['value']:
        raise PreventUpdate
        
    if trigger == 'open-sensor-type-btn':
        new_action = current_action or {}
        new_action.update({'type': 'sensor_type', 'action': 'add'})
        return True, '', '', 'Thêm loại thiết bị mới', new_action
        
    elif isinstance(trigger, dict) and trigger['type'] == 'edit-type-btn':
        type_id = trigger['index']
        types = data.get('sensor_types', [])
        item = next((t for t in types if str(t.get('ma_loai_cam_bien')) == str(type_id)), None)
        
        if item:
            new_action = current_action or {}
            new_action.update({'type': 'sensor_type', 'id': type_id, 'action': 'edit'})
            return True, item.get('ten_loai_cam_bien', ''), item.get('mo_ta', ''), 'Chỉnh sửa loại thiết bị', new_action
            
    elif trigger == 'cancel-sensor-type-modal':
        return False, no_update, no_update, no_update, no_update
        
    raise PreventUpdate


@callback(
    [Output('edit-sensor-modal', 'is_open'),
     Output('edit-sensor-name', 'value'),
     Output('edit-sensor-desc', 'value'),
     Output('edit-sensor-pump', 'value'),
     Output('edit-sensor-type', 'value'),
     Output('edit-sensor-date', 'date'),
     Output('edit-sensor-status', 'value'),
     Output('edit-sensor-modal-title', 'children'),
     Output('current-action-store', 'data', allow_duplicate=True),
     Output('edit-sensor-pump', 'options'),
     Output('edit-sensor-type', 'options')],
    [Input({'type': 'edit-sensor-btn', 'index': ALL}, 'n_clicks'),
     Input('btn-add-sensor', 'n_clicks'),
     Input('cancel-edit-sensor', 'n_clicks')],
    [State('admin-devices-data-store', 'data'),
     State('current-action-store', 'data')],
    prevent_initial_call=True
)
def toggle_edit_sensor_modal(edit_clicks, add_click, cancel_clicks, data, current_action):
    trigger = ctx.triggered_id if ctx.triggered else None
    
    if not trigger:
        raise PreventUpdate

    # Check if the trigger value is valid (not None/0)
    if not ctx.triggered[0]['value']:
        raise PreventUpdate

    # Prepare options
    pumps = data.get('pumps', [])
    pump_options = [{'label': p.get('ten_may_bom', 'N/A'), 'value': str(p.get('ma_may_bom'))} for p in pumps]
    
    sensor_types = data.get('sensor_types', [])
    type_options = [{'label': t.get('ten_loai_cam_bien', 'N/A'), 'value': str(t.get('ma_loai_cam_bien'))} for t in sensor_types]

    if trigger == 'btn-add-sensor':
        new_action = current_action or {}
        new_action.update({'type': 'sensor', 'action': 'add'})
        return True, '', '', None, None, datetime.now().date(), 'active', 'Thêm cảm biến mới', new_action, pump_options, type_options

    if isinstance(trigger, dict) and trigger['type'] == 'edit-sensor-btn':
        sensor_id = trigger['index']
        sensors = data.get('sensors', [])
        sensor = next((s for s in sensors if str(s.get('ma_cam_bien')) == str(sensor_id)), None)
        
        if sensor:
            status = 'active' if sensor.get('trang_thai') else 'inactive'
            pump_id = str(sensor.get('ma_may_bom')) if sensor.get('ma_may_bom') else None
            type_id = str(sensor.get('loai_cam_bien', {}).get('ma_loai_cam_bien')) if sensor.get('loai_cam_bien') else None
            install_date = sensor.get('ngay_lap_dat')
            
            new_action = current_action or {}
            new_action.update({'type': 'sensor', 'id': sensor_id, 'action': 'edit'})
            return True, sensor.get('ten_cam_bien', ''), sensor.get('mo_ta', ''), pump_id, type_id, install_date, status, 'Chỉnh sửa cảm biến', new_action, pump_options, type_options
            
    elif trigger == 'cancel-edit-sensor':
        return False, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update
        
    raise PreventUpdate


@callback(
    [Output('edit-pump-modal', 'is_open'),
     Output('edit-pump-name', 'value'),
     Output('edit-pump-desc', 'value'),
     Output('edit-pump-status', 'value'),
     Output('edit-pump-mode', 'value'),
     Output('edit-pump-time-limit', 'value'),
     Output('edit-pump-modal-title', 'children'),
     Output('current-action-store', 'data', allow_duplicate=True)],
    [Input({'type': 'edit-pump-btn', 'index': ALL}, 'n_clicks'),
     Input('btn-add-pump', 'n_clicks'),
     Input('cancel-edit-pump', 'n_clicks')],
    [State('admin-devices-data-store', 'data'),
     State('current-action-store', 'data')],
    prevent_initial_call=True
)
def toggle_edit_pump_modal(edit_clicks, add_click, cancel_clicks, data, current_action):
    trigger = ctx.triggered_id if ctx.triggered else None
    
    if not trigger:
        raise PreventUpdate

    # Check if the trigger value is valid (not None/0)
    if not ctx.triggered[0]['value']:
        raise PreventUpdate

    if trigger == 'btn-add-pump':
        new_action = current_action or {}
        new_action.update({'type': 'pump', 'action': 'add'})
        return True, '', '', 'active', '0', True, 'Thêm máy bơm mới', new_action

    if isinstance(trigger, dict) and trigger['type'] == 'edit-pump-btn':
        pump_id = trigger['index']
        pumps = data.get('pumps', [])
        pump = next((p for p in pumps if str(p.get('ma_may_bom')) == str(pump_id)), None)
        
        if pump:
            status = 'active' if pump.get('trang_thai') else 'inactive'
            mode = str(pump.get('che_do', 0))
            time_limit = pump.get('gioi_han_thoi_gian', True)
            new_action = current_action or {}
            new_action.update({'type': 'pump', 'id': pump_id, 'action': 'edit'})
            return True, pump.get('ten_may_bom', ''), pump.get('mo_ta', ''), status, mode, time_limit, 'Chỉnh sửa máy bơm', new_action
            
    elif trigger == 'cancel-edit-pump':
        return False, no_update, no_update, no_update, no_update, no_update, no_update, no_update
        
    raise PreventUpdate


@callback(
    [Output('delete-confirm-modal', 'is_open'),
     Output('delete-confirm-body', 'children'),
     Output('current-action-store', 'data', allow_duplicate=True)],
    [Input({'type': 'delete-sensor-btn', 'index': ALL}, 'n_clicks'),
     Input({'type': 'delete-pump-btn', 'index': ALL}, 'n_clicks'),
     Input({'type': 'delete-type-btn', 'index': ALL}, 'n_clicks'),
     Input('cancel-delete', 'n_clicks')],
    [State('admin-devices-data-store', 'data'),
     State('current-action-store', 'data')],
    prevent_initial_call=True
)
def toggle_delete_modal(sensor_clicks, pump_clicks, type_clicks, cancel, data, current_action):
    trigger = ctx.triggered_id if ctx.triggered else None
    
    if not trigger:
        raise PreventUpdate
        
    # Check if the trigger value is valid (not None/0)
    if not ctx.triggered[0]['value']:
        raise PreventUpdate
        
    if isinstance(trigger, dict):
        item_id = trigger.get('index')
        btn_type = trigger.get('type')
        message = "Bạn có chắc chắn muốn xóa mục này?"
        new_action = current_action or {}
        
        if btn_type == 'delete-sensor-btn':
            sensors = data.get('sensors', [])
            item = next((s for s in sensors if str(s.get('ma_cam_bien')) == str(item_id)), None)
            name = item.get('ten_cam_bien', 'Unknown') if item else 'Unknown'
            message = f"Bạn có chắc chắn muốn xóa cảm biến '{name}'?"
            new_action.update({'type': 'sensor', 'id': item_id, 'action': 'delete'})
            
        elif btn_type == 'delete-pump-btn':
            pumps = data.get('pumps', [])
            item = next((p for p in pumps if str(p.get('ma_may_bom')) == str(item_id)), None)
            name = item.get('ten_may_bom', 'Unknown') if item else 'Unknown'
            message = f"Bạn có chắc chắn muốn xóa máy bơm '{name}'?"
            new_action.update({'type': 'pump', 'id': item_id, 'action': 'delete'})
            
        elif btn_type == 'delete-type-btn':
            types = data.get('sensor_types', [])
            item = next((t for t in types if str(t.get('ma_loai_cam_bien')) == str(item_id)), None)
            name = item.get('ten_loai_cam_bien', 'Unknown') if item else 'Unknown'
            message = f"Bạn có chắc chắn muốn xóa loại thiết bị '{name}'?"
            new_action.update({'type': 'sensor_type', 'id': item_id, 'action': 'delete'})
            
        return True, message, new_action
            
    elif trigger == 'cancel-delete':
        return False, no_update, no_update
        
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
    [Output('admin-devices-toast', 'is_open', allow_duplicate=True),
     Output('admin-devices-toast', 'children', allow_duplicate=True),
     Output('admin-devices-toast', 'icon', allow_duplicate=True),
     Output('sensor-type-modal', 'is_open', allow_duplicate=True),
     Output('admin-devices-url', 'refresh', allow_duplicate=True)],
    Input('save-sensor-type-modal', 'n_clicks'),
    [State('new-sensor-type-name', 'value'),
     State('new-sensor-type-desc', 'value'),
     State('current-action-store', 'data')],
    prevent_initial_call=True
)
def save_sensor_type_callback(n_clicks, name, desc, current_action):
    if not n_clicks:
        raise PreventUpdate
    
    if not name:
        return True, "Vui lòng nhập tên loại thiết bị", "danger", True, no_update
        
    action_type = current_action.get('action') if current_action else 'add'
    
    if action_type == 'add':
        success, msg = api_sensor.create_sensor_type({'ten_loai_cam_bien': name, 'mo_ta': desc})
    elif action_type == 'edit':
        type_id = current_action.get('id')
        success, msg = api_sensor.update_sensor_type(type_id, {'ten_loai_cam_bien': name, 'mo_ta': desc})
    else:
        return True, "Hành động không hợp lệ", "danger", True, no_update
        
    if success:
        return True, msg, "success", False, True
    else:
        return True, msg, "danger", True, no_update


@callback(
    [Output('admin-devices-toast', 'is_open', allow_duplicate=True),
     Output('admin-devices-toast', 'children', allow_duplicate=True),
     Output('admin-devices-toast', 'icon', allow_duplicate=True),
     Output('edit-sensor-modal', 'is_open', allow_duplicate=True),
     Output('admin-devices-url', 'refresh', allow_duplicate=True)],
    Input('save-edit-sensor', 'n_clicks'),
    [State('edit-sensor-name', 'value'),
     State('edit-sensor-desc', 'value'),
     State('edit-sensor-pump', 'value'),
     State('edit-sensor-type', 'value'),
     State('edit-sensor-date', 'date'),
     State('edit-sensor-status', 'value'),
     State('current-action-store', 'data')],
    prevent_initial_call=True
)
def save_edit_sensor_callback(n_clicks, name, desc, pump_id, type_id, install_date, status, current_action):
    if not n_clicks:
        raise PreventUpdate
        
    if not current_action or current_action.get('type') != 'sensor':
        raise PreventUpdate
        
    action = current_action.get('action')
    is_active = status == 'active'
    
    payload = {
        'ten_cam_bien': name,
        'mo_ta': desc,
        'ma_may_bom': int(pump_id) if pump_id else None,
        'ma_loai_cam_bien': int(type_id) if type_id else None,
        'ngay_lap_dat': install_date,
        'trang_thai': is_active
    }
    
    if action == 'add':
        success, msg = api_sensor.create_sensor(payload)
    elif action == 'edit':
        sensor_id = current_action.get('id')
        success, msg = api_sensor.update_sensor(sensor_id, payload)
    else:
        return True, "Hành động không hợp lệ", "danger", True, no_update
    
    if success:
        return True, msg, "success", False, True
    else:
        return True, msg, "danger", True, no_update


@callback(
    [Output('admin-devices-toast', 'is_open', allow_duplicate=True),
     Output('admin-devices-toast', 'children', allow_duplicate=True),
     Output('admin-devices-toast', 'icon', allow_duplicate=True),
     Output('edit-pump-modal', 'is_open', allow_duplicate=True),
     Output('admin-devices-url', 'refresh', allow_duplicate=True)],
    Input('save-edit-pump', 'n_clicks'),
    [State('edit-pump-name', 'value'),
     State('edit-pump-desc', 'value'),
     State('edit-pump-status', 'value'),
     State('edit-pump-mode', 'value'),
     State('edit-pump-time-limit', 'value'),
     State('current-action-store', 'data')],
    prevent_initial_call=True
)
def save_edit_pump_callback(n_clicks, name, desc, status, mode, time_limit, current_action):
    if not n_clicks:
        raise PreventUpdate
        
    if not current_action or current_action.get('type') != 'pump':
        raise PreventUpdate
        
    action = current_action.get('action')
    is_active = status == 'active'
    
    payload = {
        'ten_may_bom': name,
        'mo_ta': desc,
        'trang_thai': is_active,
        'che_do': int(mode) if mode else 0,
        'gioi_han_thoi_gian': time_limit
    }
    
    if action == 'add':
        success, msg = api_pump.create_pump(payload)
    elif action == 'edit':
        pump_id = current_action.get('id')
        success, msg = api_pump.update_pump(pump_id, payload)
    else:
        return True, "Hành động không hợp lệ", "danger", True, no_update
    
    if success:
        return True, msg, "success", False, True
    else:
        return True, msg, "danger", True, no_update


@callback(
    [Output('admin-devices-toast', 'is_open', allow_duplicate=True),
     Output('admin-devices-toast', 'children', allow_duplicate=True),
     Output('admin-devices-toast', 'icon', allow_duplicate=True),
     Output('delete-confirm-modal', 'is_open', allow_duplicate=True),
     Output('admin-devices-url', 'refresh', allow_duplicate=True)],
    Input('confirm-delete', 'n_clicks'),
    [State('current-action-store', 'data')],
    prevent_initial_call=True
)
def confirm_delete_callback(n_clicks, current_action):
    if not n_clicks:
        raise PreventUpdate
        
    if not current_action or current_action.get('action') != 'delete':
        raise PreventUpdate
        
    item_type = current_action.get('type')
    item_id = current_action.get('id')
    
    success = False
    msg = "Lỗi không xác định"
    
    if item_type == 'sensor':
        success, msg = api_sensor.delete_sensor(item_id)
    elif item_type == 'pump':
        success, msg = api_pump.delete_pump(item_id)
    elif item_type == 'sensor_type':
        success, msg = api_sensor.delete_sensor_type(item_id)
        
    if success:
        return True, msg, "success", False, True
    else:
        return True, msg, "danger", True, no_update
