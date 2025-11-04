from dash import html, dcc, callback, Input, Output, State, ctx, MATCH
import dash_bootstrap_components as dbc
import dash
from components.navbar import create_navbar
import base64
from api import models as api_models
from datetime import datetime
import json

layout = html.Div([
    create_navbar(is_authenticated=True, is_admin=True),
    dcc.Location(id='admin-models-url', refresh=False),
    dcc.Store(id='session-store', storage_type='session'),
    dbc.Toast(
        id='admin-models-toast',
        header='Thông báo',
        is_open=False,
        dismissable=True,
        duration=3500,
        icon='success',
        children='',
        style={'position': 'fixed', 'top': '80px', 'right': '24px', 'zIndex': 2100}
    ),
    # Toast for delete operations
    html.Div(id='delete-toasts-container', children=[
        dbc.Toast(
            id={'type': 'admin-models-toast-delete', 'index': i},
            header='Thông báo',
            is_open=False,
            dismissable=True,
            duration=3500,
            icon='success',
            children='',
            style={'position': 'fixed', 'top': f'{80 + i*60}px', 'right': '24px', 'zIndex': 2100}
        ) for i in range(10)  # Support up to 10 simultaneous delete operations
    ]),
    dbc.Container([
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.Span('Tải lên mô hình mới', className='user-table-title')),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                dcc.Upload(
                                    id='admin-model-upload',
                                    children=html.Div(id='model-upload-display', children=[
                                        html.I(className='fas fa-file-upload me-2'),
                                        html.Span('Kéo thả tệp ở đây hoặc bấm để chọn'),
                                        html.Br(),
                                        html.Small('Chỉ chấp nhận file .h5, .pkl', className='text-muted')
                                    ]),
                                    style={
                                        'border': '2px dashed #dee2e6',
                                        'borderRadius': '8px',
                                        'padding': '30px 20px',
                                        'textAlign': 'center',
                                        'cursor': 'pointer',
                                        'backgroundColor': '#f8f9fa',
                                        'transition': 'all 0.3s ease'
                                    },
                                    multiple=False
                                )
                            ], md=12, className='mb-4')
                        ]),
                        dbc.Row([
                            dbc.Col([
                                dbc.Label('Tên mô hình', className='mb-2 fw-medium'),
                                dbc.Input(
                                    id='admin-model-name',
                                    placeholder='Nhập tên mô hình...',
                                    className='mb-3'
                                )
                            ], md=4),
                            dbc.Col([
                                dbc.Label('Phiên bản', className='mb-2 fw-medium'),
                                dbc.Input(
                                    id='admin-model-version',
                                    placeholder='Ví dụ: 1.0.0',
                                    className='mb-3'
                                )
                            ], md=4),
                            dbc.Col([
                                dbc.Label('Mô tả', className='mb-2 fw-medium'),
                                dbc.Textarea(
                                    id='admin-model-description',
                                    placeholder='Nhập mô tả mô hình (tùy chọn)...',
                                    className='mb-3',
                                    style={'height': '50px', 'resize': 'none'}
                                )
                            ], md=4),
                        ]),
                        dbc.Row([
                            dbc.Col([
                                dbc.Button(
                                    [html.I(className='fas fa-upload me-2'), 'Tải lên'],
                                    id='admin-model-upload-btn',
                                    color='primary',
                                    className='d-flex align-items-center justify-content-center h-100 px-4'
                                )
                            ], md=12, className='d-flex align-items-center justify-content-center')
                        ])
                    ])
                ], className='mb-4 user-table-card', style={'marginTop': '70px'})
            ], md=12)
        ]),

        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.Span('Danh sách mô hình', className='user-table-title')),
                    dbc.CardBody(
                        id='admin-models-table-container',
                        children=[
                            html.Div(id='admin-models-table', className='table-responsive')
                        ]
                    )
                ], className='user-table-card')
            ], md=12)
        ])
    ], fluid=True, className='py-4'),
    dcc.Interval(id='admin-models-interval', interval=5000),  # Refresh every 5 seconds
])

@callback(
    Output('admin-models-table', 'children'),
    Input('admin-models-interval', 'n_intervals'),
    State('session-store', 'data'),
)
def update_models_table(n_intervals, session_data):
    token = session_data.get('token', None)
    print("Token:", token)  # Debug log
    
    models_data = api_models.list_models(token=token)
    print("Models data:", models_data)  # Debug log
    
    if not models_data or not models_data.get('data'):
        return html.Div('Không có mô hình nào.', className='text-center my-3')
    
    # Create table
    table_header = [
        html.Thead(html.Tr([
            html.Th('Mã mô hình', className='text-center'),
            html.Th('Tên mô hình'),
            html.Th('Phiên bản'),
            html.Th('Thời gian tạo'),
            html.Th('Thời gian cập nhật'),
            html.Th('Trạng thái'),
            html.Th('Thao tác', className='text-center')
        ]), className='table-header')
    ]
    
    rows = []
    for model in models_data.get('data', []):
        # Handle created time
        try:
            created_time = datetime.fromisoformat(model['thoi_gian_tao'].replace('Z', '+00:00')) if model['thoi_gian_tao'] else None
            created_time_str = created_time.strftime('%d/%m/%Y %H:%M:%S') if created_time else 'N/A'
        except (AttributeError, ValueError):
            created_time_str = 'N/A'

        # Handle updated time
        try:
            updated_time = datetime.fromisoformat(model['thoi_gian_cap_nhat'].replace('Z', '+00:00')) if model['thoi_gian_cap_nhat'] else None
            updated_time_str = updated_time.strftime('%d/%m/%Y %H:%M:%S') if updated_time else 'N/A'
        except (AttributeError, ValueError):
            updated_time_str = 'N/A'
        
        # Status badge
        status_badge = dbc.Badge(
            'Hoạt động' if model.get('trang_thai', False) else 'Không hoạt động',
            color='success' if model.get('trang_thai', False) else 'danger',
            className='me-1'
        )
        
        # Action buttons
        action_buttons = html.Div([
            dbc.Button(
                html.I(className='fas fa-edit'),
                id={'type': 'admin-model-edit-btn', 'index': model['ma_mo_hinh']},
                color='primary',
                size='sm',
                className='me-2'
            ),
            dbc.Button(
                html.I(className='fas fa-trash-alt'),
                id={'type': 'admin-model-delete-btn', 'index': model['ma_mo_hinh']},
                color='danger',
                size='sm'
            )
        ], className='d-flex justify-content-center')
        
        row = html.Tr([
            html.Td(model.get('ma_mo_hinh', 'N/A'), className='text-center'),
            html.Td(model.get('ten_mo_hinh', 'N/A')),
            html.Td(model.get('phien_ban', 'N/A')),
            html.Td(created_time_str),
            html.Td(updated_time_str),
            html.Td(status_badge),
            html.Td(action_buttons, className='text-center')
        ])
        rows.append(row)
    
    table_body = [html.Tbody(rows)]
    
    return dbc.Table(
        table_header + table_body,
        bordered=True,
        hover=True,
        responsive=True,
        className='mb-0'
    )

@callback(
    [Output('admin-model-name', 'value'),
     Output('admin-model-version', 'value'),
     Output('admin-models-toast', 'is_open'),
     Output('admin-models-toast', 'children'),
     Output('admin-models-toast', 'icon')],
    Input('admin-model-upload-btn', 'n_clicks'),
    [State('admin-model-upload', 'contents'),
     State('admin-model-name', 'value'),
     State('admin-model-version', 'value'),
     State('session-store', 'data')]
)
def handle_model_upload(upload_clicks, file_content, name, version, session_data):
    if not ctx.triggered_id or not upload_clicks:
        return dash.no_update, dash.no_update, False, '', 'success'
    
    if not session_data:
        return dash.no_update, dash.no_update, True, 'Vui lòng đăng nhập lại.', 'danger'
    
    token = session_data.get('token', None)
    
    if not all([file_content, name, version]):
        return name, version, True, 'Vui lòng điền đầy đủ thông tin và chọn file', 'danger'
    
    # Process file content
    content_type, content_string = file_content.split(',')
    decoded = base64.b64decode(content_string)
    
    # Create model
    success, message = api_models.create_model(
        file_tuple=('model.h5', decoded),
        metadata={
            'ten_mo_hinh': name,
            'phien_ban': version,
            'trang_thai': True
        },
        token=token
    )
    
    return '', '', True, message, 'success' if success else 'danger'

@callback(
    [Output({'type': 'admin-models-toast-delete', 'index': MATCH}, 'is_open'),
     Output({'type': 'admin-models-toast-delete', 'index': MATCH}, 'children'),
     Output({'type': 'admin-models-toast-delete', 'index': MATCH}, 'icon')],
    Input({'type': 'admin-model-delete-btn', 'index': MATCH}, 'n_clicks'),
    State('session-store', 'data'),
    prevent_initial_call=True
)
def handle_model_delete(delete_clicks, session_data):
    if not ctx.triggered_id:
        return False, '', 'success'
    
    token = session_data.get('token', None)
    model_id = ctx.triggered_id['index']
    
    success, message = api_models.delete_model(model_id, token=token)
    return True, message, 'success' if success else 'danger'