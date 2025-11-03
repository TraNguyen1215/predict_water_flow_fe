from dash import html, dcc, Input, Output, State, callback, no_update, MATCH
import dash_bootstrap_components as dbc
import dash
from dash.exceptions import PreventUpdate
from datetime import datetime
from components.navbar import create_navbar
from api.sensor import get_sensor_types

def fetch_sensor_types_data():
    try:
        response = get_sensor_types()
        if response and 'data' in response:
            return response['data']
        return []
    except Exception as e:
        print(f"Error fetching sensor types: {e}")
        return []

def format_date(date_str):
    if date_str:
        try:
            date = datetime.strptime(date_str.split('T')[0], "%Y-%m-%d")
            return date.strftime("%d/%m/%Y")
        except:
            return date_str
    return "N/A"

def create_sensor_types_table(search_value='', user_filter='all', pump_filter='all', status_filter='all'):
    sensor_types = fetch_sensor_types_data()
    # Build a Bootstrap table (styled like the users table)
    rows = []
    # Flatten sensors for rows
    for sensor_type in sensor_types:
        for sensor in sensor_type.get('cam_bien', []):
            identifier = sensor.get('ma_cam_bien')
            status = sensor.get('trang_thai')
            status_label = 'Hoạt động' if status else ('Không hoạt động' if status is not None else 'Chưa xác định')
            
            if search_value:
                search_lower = search_value.lower()
                name_match = search_lower in (sensor.get('ten_cam_bien') or '').lower()
                desc_match = search_lower in (sensor.get('mo_ta') or '').lower()
                date_match = search_lower in (format_date(sensor.get('ngay_lap_dat')) or '').lower()
                if not (name_match or desc_match or date_match):
                    continue

            if user_filter != 'all':
                if not sensor.get('nguoi_dung') or str(sensor['nguoi_dung'].get('ma_nguoi_dung')) != user_filter:
                    continue

            if pump_filter != 'all':
                if not sensor.get('may_bom') or str(sensor['may_bom'].get('ma_may_bom')) != pump_filter:
                    continue

            if status_filter != 'all':
                if status_filter == 'active' and not status:
                    continue
                if status_filter == 'inactive' and status is not False:
                    continue
                if status_filter == 'unknown' and status is not None:
                    continue

            rows.append(html.Tr([
                html.Td(html.Strong(sensor.get('ten_cam_bien') or f"CB-{identifier}")),
                html.Td(html.Span(sensor_type.get('ten_loai_cam_bien'))),
                html.Td(sensor.get('mo_ta') or '--'),
                html.Td(sensor.get('nguoi_dung', {}).get('ho_ten') or sensor.get('nguoi_dung', {}).get('ten_dang_nhap') or '--', className='text-nowrap'),
                html.Td(sensor.get('may_bom', {}).get('ten_may_bom') or '--'),
                html.Td(format_date(sensor.get('ngay_lap_dat'))),
                html.Td(html.Span(status_label, className=f"user-status-badge {'active' if status else 'inactive' if status is not None else ''}"), className='text-nowrap')
            ]))

    table_header = html.Thead(html.Tr([
        html.Th('Tên cảm biến'),
        html.Th('Loại cảm biến'),
        html.Th('Mô tả'),
        html.Th('Người dùng'),
        html.Th('Máy bơm'),
        html.Th('Ngày lắp đặt'),
        html.Th('Trạng thái')
    ]))

    table = dbc.Table([
        table_header,
        html.Tbody(rows)
    ], bordered=False, hover=True, responsive=True, className='user-table sensor-type-table')

    table_card = dbc.Card([
        dbc.CardHeader(html.Span('Chi tiết cảm biến theo loại', className='user-table-title')),
        dbc.CardBody([table])
    ], className='user-table-card')

    return table_card

def create_summary_cards():
    sensor_types = fetch_sensor_types_data()
    total_types = len(sensor_types)
    total_sensors = sum(st['tong_cam_bien'] for st in sensor_types)
    active_sensors = sum(len([s for s in st['cam_bien'] if s['trang_thai']]) for st in sensor_types)
    
    return dbc.Row([
        dbc.Col(
            dbc.Card([
                dbc.CardBody([
                    html.H4(total_types, className='card-title text-primary'),
                    html.P('Tổng số loại cảm biến', className='card-text')
                ])
            ], className='mb-3')
        , width=4),
        dbc.Col(
            dbc.Card([
                dbc.CardBody([
                    html.H4(total_sensors, className='card-title text-success'),
                    html.P('Tổng số cảm biến', className='card-text')
                ])
            ], className='mb-3')
        , width=4),
        dbc.Col(
            dbc.Card([
                dbc.CardBody([
                    html.H4(active_sensors, className='card-title text-info'),
                    html.P('Cảm biến đang hoạt động', className='card-text')
                ])
            ], className='mb-3')
        , width=4)
    ])

def create_add_sensor_type_modal():
    return dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("Thêm loại cảm biến")),
        dbc.ModalBody([
            dbc.Form([
                dbc.Row([
                    dbc.Label("Tên loại cảm biến", width=12),
                    dbc.Col([
                        dbc.Input(
                            type="text",
                            id="new-sensor-type-name",
                            placeholder="Nhập tên loại cảm biến"
                        )
                    ])
                ], className="mb-3")
            ])
        ]),
        dbc.ModalFooter([
            dbc.Button("Hủy", id="cancel-add-sensor-type", className="me-2", color="secondary"),
            dbc.Button("Lưu", id="save-sensor-type", color="primary")
        ])
    ], id="add-sensor-type-modal", is_open=False)

layout = html.Div([
    create_navbar(is_authenticated=True, is_admin=True),
    dcc.Location(id='admin-sensor-types-url', refresh=False),
    dcc.Store(id='user-options-store', data=[]),
    dcc.Store(id='pump-options-store', data=[]),
    dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H2([
                    html.I(className='fas fa-thermometer-half me-2'), 
                    'Quản lý loại cảm biến'
                ], className='text-primary mb-4'),
            ], width=12)
        ]),
        
        # Summary cards
        create_summary_cards(),
        
        # Search and filter section
        dbc.Row([
            dbc.Col([
                dbc.InputGroup([
                    dbc.Input(
                        id='search-input',
                        type='text',
                        placeholder='Tìm kiếm theo tên, mô tả...',
                        className='me-2'
                    ),
                    dbc.Select(
                        id='user-filter',
                        placeholder='Lọc theo người dùng',
                        options=[],
                        className='me-2'
                    ),
                    dbc.Select(
                        id='pump-filter',
                        placeholder='Lọc theo máy bơm',
                        options=[],
                        className='me-2'
                    ),
                    dbc.Select(
                        id='status-filter',
                        placeholder='Lọc theo trạng thái',
                        options=[
                            {'label': 'Tất cả', 'value': 'all'},
                            {'label': 'Hoạt động', 'value': 'active'},
                            {'label': 'Không hoạt động', 'value': 'inactive'},
                            {'label': 'Chưa xác định', 'value': 'unknown'}
                        ],
                        value='all',
                        className='me-2'
                    ),
                    dbc.Button([
                        html.I(className='fas fa-plus me-2'),
                        'Thêm loại cảm biến'
                    ], 
                    id='add-sensor-type-btn', 
                    color='primary',
                    className='d-flex align-items-center'
                    )
                ], className='mb-3')
            ], width=12)
        ]),
        
        # Main data table
        dbc.Row([
            dbc.Col([
                html.Div(id='sensor-types-content', children=create_sensor_types_table())
            ], width=12)
        ], className='mt-3'),
        
        ], fluid=True, className='py-4'),
    
    # Add sensor type modal
    create_add_sensor_type_modal()
])# Callbacks for filter functionality
@callback(
    [Output('user-filter', 'options'),
     Output('pump-filter', 'options')],
    Input('admin-sensor-types-url', 'pathname')
)
def update_filter_options(pathname):
    if not pathname or pathname != '/admin/sensor-types':
        raise dash.exceptions.PreventUpdate
        
    sensor_types = fetch_sensor_types_data()
    users = set()
    pumps = set()
    
    for sensor_type in sensor_types:
        for sensor in sensor_type.get('cam_bien', []):
            if sensor.get('nguoi_dung'):
                users.add((
                    sensor['nguoi_dung'].get('ma_nguoi_dung'),
                    sensor['nguoi_dung'].get('ho_ten') or sensor['nguoi_dung'].get('ten_dang_nhap')
                ))
            if sensor.get('may_bom'):
                pumps.add((
                    sensor['may_bom'].get('ma_may_bom'),
                    sensor['may_bom'].get('ten_may_bom')
                ))
    
    user_options = [{'label': name, 'value': str(uid)} for uid, name in sorted(users, key=lambda x: x[1])]
    pump_options = [{'label': name, 'value': str(pid)} for pid, name in sorted(pumps, key=lambda x: x[1])]
    
    # Add "All" option to both
    user_options.insert(0, {'label': 'Tất cả người dùng', 'value': 'all'})
    pump_options.insert(0, {'label': 'Tất cả máy bơm', 'value': 'all'})
    
    return user_options, pump_options

@callback(
    Output('sensor-types-content', 'children'),
    [Input('search-input', 'value'),
     Input('user-filter', 'value'),
     Input('pump-filter', 'value'),
     Input('status-filter', 'value')]
)
def update_table_content(search, user_filter, pump_filter, status_filter):
    return create_sensor_types_table(
        search_value=search or '',
        user_filter=user_filter or 'all',
        pump_filter=pump_filter or 'all',
        status_filter=status_filter or 'all'
    )

@callback(
    Output('add-sensor-type-modal', 'is_open'),
    [Input('add-sensor-type-btn', 'n_clicks'),
     Input('cancel-add-sensor-type', 'n_clicks'),
     Input('save-sensor-type', 'n_clicks')],
    prevent_initial_call=True
)
def toggle_modal(add_clicks, cancel_clicks, save_clicks):
    trigger = dash.callback_context.triggered_id
    if trigger and any([add_clicks, cancel_clicks, save_clicks]):
        return trigger == 'add-sensor-type-btn'
    return False

@callback(
    Output('add-sensor-type-modal', 'children'),
    Input('save-sensor-type', 'n_clicks'),
    State('new-sensor-type-name', 'value'),
    prevent_initial_call=True
)
def save_sensor_type(n_clicks, name):
    if not n_clicks or not name:
        raise dash.exceptions.PreventUpdate
        
    # Add API call here to save new sensor type
    # api_sensor.add_sensor_type(name)
    
    return no_update
