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
    dcc.Store(id='admin-model-delete-id', storage_type='session'),
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
    dbc.Toast(
        id='admin-model-delete-toast',
        header='Thông báo',
        is_open=False,
        dismissable=True,
        duration=3500,
        icon='success',
        children='',
        style={'position': 'fixed', 'top': '140px', 'right': '24px', 'zIndex': 2100}
    ),
    dbc.Modal([
        dbc.ModalHeader(html.H5('Xác nhận xóa')),
        dbc.ModalBody(html.Div('Bạn có chắc chắn muốn xóa mô hình này?', id='admin-model-delete-body')),
        dbc.ModalFooter([
            dbc.Button('Xóa', id='confirm-delete-model', color='danger'),
            dbc.Button('Hủy', id='cancel-delete-model', className='ms-2')
        ])
    ], id='admin-model-delete-modal', is_open=False, centered=True),
    # Edit model modal
    dcc.Store(id='admin-model-edit-id', storage_type='session'),
    dbc.Modal([
        dbc.ModalHeader(html.H5(id='admin-model-modal-title')),
        dbc.ModalBody([
            dbc.Form([
                dbc.Row([
                    dbc.Col(dbc.Label('Tên mô hình', className='fw-bold'), md=12),
                    dbc.Col(dbc.Input(id='admin-model-modal-name', type='text'), md=12),
                ]),
                dbc.Row([
                    dbc.Col(dbc.Label('Phiên bản', className='fw-bold'), md=12),
                    dbc.Col(dbc.Input(id='admin-model-modal-version', type='text'), md=12),
                ]),
                dbc.Row([
                    dbc.Col(dbc.Label('Mô tả', className='fw-bold'), md=12),
                    dbc.Col(dbc.Textarea(id='admin-model-modal-description', style={'height':'80px', 'resize':'none'}), md=12),
                ]),
                dbc.Row([
                    dbc.Col(dbc.Checkbox(id='admin-model-modal-status', label='Hoạt động'), md=12),
                ])
            ])
        ]),
        dbc.ModalFooter([
            dbc.Button('Lưu', id='admin-model-save', color='primary'),
            dbc.Button('Hủy', id='admin-model-cancel', className='ms-2')
        ])
    ], id='admin-model-modal', is_open=False, centered=True),
    dbc.Toast(
        id='admin-model-edit-toast',
        header='Thông báo',
        is_open=False,
        dismissable=True,
        duration=3500,
        icon='success',
        children='',
        style={'position': 'fixed', 'top': '200px', 'right': '24px', 'zIndex': 2100}
    ),
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
                                        'transition': 'all 0.3s ease',
                                        'marginBottom': '0'
                                    },
                                    multiple=False,
                                    accept='.h5,.pkl'
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
    [Input('admin-models-interval', 'n_intervals'),
     Input('admin-models-url', 'pathname')],
    State('session-store', 'data'),
)
def update_models_table(n_intervals, pathname, session_data):
    if not session_data:
        return html.Div('Vui lòng đăng nhập để xem danh sách mô hình.', className='text-center my-3')
        
    token = session_data.get('token', None)
    if not token:
        return html.Div('Vui lòng đăng nhập để xem danh sách mô hình.', className='text-center my-3')
    
    models_data = api_models.list_models(token=token)
    # print("Models data:", models_data)  # Debug log
    
    if not models_data or not models_data.get('data'):
        return html.Div('Không có mô hình nào.', className='text-center my-3')
    
    rows = []
    for model in models_data.get('data', []):
        mid = model.get('ma_mo_hinh')
        name = model.get('ten_mo_hinh') or f"Model-{mid}"
        version = model.get('phien_ban') or '--'
        created = model.get('thoi_gian_tao')
        updated = model.get('thoi_gian_cap_nhat')

        created_str = str(created).split('T')[0] if created and 'T' in str(created) else (str(created) if created else '--')
        updated_str = str(updated).split('T')[0] if updated and 'T' in str(updated) else (str(updated) if updated else '--')

        rows.append(html.Tr([
            html.Td(html.Strong(name or f"Model-{mid}")),
            html.Td(version, className='text-nowrap'),
            html.Td(created_str, className='text-nowrap'),
            html.Td(updated_str, className='text-nowrap'),
            html.Td(html.Span('Hoạt động' if model.get('trang_thai', False) else 'Không hoạt động',
                            className=f"user-status-badge {'active' if model.get('trang_thai', False) else 'inactive'}")),
            html.Td(html.Div([
                dbc.Button(
                    html.I(className='fas fa-edit'),
                    id={'type': 'admin-model-edit-btn', 'index': str(mid)},
                    color='light',
                    size='sm',
                    className='action-btn edit',
                    title='Chỉnh sửa'
                ),
                dbc.Button(
                    html.I(className='fas fa-trash'),
                    id={'type': 'admin-model-delete-btn', 'index': str(mid)},
                    color='light',
                    size='sm',
                    className='action-btn delete',
                    title='Xóa mô hình'
                )
            ], className='user-actions'), className='text-end')
        ]))

    table = dbc.Table([
        html.Thead(html.Tr([
            html.Th('Tên mô hình'),
            html.Th('Phiên bản'),
            html.Th('Thời gian tạo'),
            html.Th('Thời gian cập nhật'),
            html.Th('Trạng thái'),
            html.Th('Hành động')
        ])),
        html.Tbody(rows)
    ], bordered=False, hover=True, responsive=True, className='user-table')

    table_card = dbc.Card([
        dbc.CardHeader(html.Span('Danh sách mô hình', className='user-table-title')),
        dbc.CardBody([table])
    ], className='user-table-card')

    return table_card

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
     State('admin-model-upload', 'filename'),
     State('session-store', 'data')]
)
def handle_model_upload(upload_clicks, file_content, name, version, filename, session_data):
    if not ctx.triggered_id or not upload_clicks:
        return dash.no_update, dash.no_update, False, '', 'success'
    
    # Debug logs
    # print("Upload button clicked")
    # print(f"Name: {name}")
    # print(f"Version: {version}")
    # print(f"Filename: {filename}")
    
    if not session_data or not session_data.get('token'):
        return dash.no_update, dash.no_update, True, 'Vui lòng đăng nhập lại.', 'danger'
    
    token = session_data.get('token')
    
    # Check required fields
    if not name:
        return name, version, True, 'Vui lòng nhập tên mô hình', 'danger'
    if not version:
        return name, version, True, 'Vui lòng nhập phiên bản mô hình', 'danger'
    
    try:
        # Create model
        success, message = api_models.create_model(
            metadata={
                'ten_mo_hinh': name,
                'phien_ban': version,
                'trang_thai': True
            },
            token=token
        )
        if success:
            return '', '', True, 'Tải lên mô hình thành công!', 'success'
        else:
            return name, version, True, f'Lỗi: {message}', 'danger'
            
    except Exception as e:
        print(f"Error uploading model: {str(e)}")
        return name, version, True, f'Lỗi khi tải lên mô hình: {str(e)}', 'danger'

@callback(
    Output('admin-model-delete-modal', 'is_open'),
    Output('admin-model-delete-id', 'data'),
    Output('admin-model-delete-toast', 'is_open'),
    Output('admin-model-delete-toast', 'children'),
    Output('admin-model-delete-toast', 'icon'),
    Input({'type': 'admin-model-delete-btn', 'index': dash.ALL}, 'n_clicks'),
    Input('confirm-delete-model', 'n_clicks'),
    Input('cancel-delete-model', 'n_clicks'),
    State('admin-model-delete-id', 'data'),
    State('session-store', 'data'),
    prevent_initial_call=True
)
def handle_model_delete_flow(delete_btns, confirm_click, cancel_click, stored_model_id, session_data):
    """Unified handler for delete button, confirm and cancel actions.

    Returns:
      is_open (bool): whether modal is open
      model_id (any): stored model id (or None)
      toast_open (bool): whether to show toast
      toast_children (str|html): toast content
      toast_icon (str): 'success'|'danger'
    """
    trigger = ctx.triggered_id
    # Use callback_context to determine which input fired and its value
    triggered = dash.callback_context.triggered
    if not triggered:
        raise dash.exceptions.PreventUpdate
    fired = triggered[0]
    prop = fired.get('prop_id', '')
    value = fired.get('value', None)

    # Normalize trigger id into python object when pattern-matching ids are used
    try:
        trigger = json.loads(prop.split('.')[0].replace("'", '"'))
    except Exception:
        trigger = prop

    # Delete button clicked -> open modal and store id
    if isinstance(trigger, dict) and trigger.get('type') == 'admin-model-delete-btn':
        # find which button triggered and extract its index
        try:
            # use dash.callback_context to find the prop_id
            btn_id = prop.split('.')[0]
            btn_obj = json.loads(btn_id.replace("'", '"'))
            model_id = btn_obj.get('index')
        except Exception:
            raise dash.exceptions.PreventUpdate
        # Only open modal when the button click value is truthy (prevents opens on layout updates)
        if not value:
            raise dash.exceptions.PreventUpdate
        return True, model_id, False, '', 'success'

    # Confirm clicked -> perform delete
    if trigger == 'confirm-delete-model' or (isinstance(trigger, dict) and trigger.get('id') == 'confirm-delete-model'):
        model_id = stored_model_id
        # Only act when confirm button has a truthy click value
        if not value or not model_id or not session_data:
            raise dash.exceptions.PreventUpdate
        token = session_data.get('token')
        try:
            success, message = api_models.delete_model(model_id, token=token)
        except Exception as e:
            success = False
            message = str(e)
        # Close modal, clear stored id, show delete-toast (index 0)
        return False, None, True, message, 'success' if success else 'danger'

    # Cancel clicked -> close modal without action
    if trigger == 'cancel-delete-model' or (isinstance(trigger, dict) and trigger.get('id') == 'cancel-delete-model'):
        # Only act when cancel button has a truthy click value
        if not value:
            raise dash.exceptions.PreventUpdate
        return False, None, False, '', 'success'

    # Default: prevent update
    raise dash.exceptions.PreventUpdate


@callback(
    Output('admin-model-modal', 'is_open', allow_duplicate=True), Output('admin-model-modal-title', 'children'), Output('admin-model-edit-id', 'data', allow_duplicate=True),
    Output('admin-model-modal-name', 'value'), Output('admin-model-modal-version', 'value'), Output('admin-model-modal-description', 'value'), Output('admin-model-modal-status', 'value'),
    Input({'type': 'admin-model-edit-btn', 'index': dash.ALL}, 'n_clicks'),
    State('admin-model-edit-id', 'data'), State('session-store', 'data'),
    prevent_initial_call=True
)
def open_model_edit_modal(edit_clicks, stored_edit_id, session_data):
    # Open edit modal when an edit button is clicked and populate fields
    ctx_trigger = dash.callback_context
    if not ctx_trigger.triggered:
        raise dash.exceptions.PreventUpdate
    trig = ctx_trigger.triggered[0]
    prop = trig.get('prop_id', '')
    value = trig.get('value')
    if not value:
        raise dash.exceptions.PreventUpdate
    try:
        import json as _json
        btn_obj = _json.loads(prop.split('.')[0].replace("'", '"'))
        model_id = btn_obj.get('index')
    except Exception:
        raise dash.exceptions.PreventUpdate

    token = None
    if session_data and isinstance(session_data, dict):
        token = session_data.get('token')

    model = {}
    try:
        model = api_models.get_model(int(model_id), token=token) if model_id is not None else {}
    except Exception:
        model = {}

    name = model.get('ten_mo_hinh') if isinstance(model, dict) else ''
    version = model.get('phien_ban') if isinstance(model, dict) else ''
    description = model.get('mo_ta') or model.get('moTa') or model.get('description') or ''
    status = bool(model.get('trang_thai', False)) if isinstance(model, dict) else False

    return True, 'Chỉnh sửa mô hình', model_id, name, version, description, status


@callback(
    Output('admin-model-modal', 'is_open', allow_duplicate=True), Output('admin-model-edit-id', 'data', allow_duplicate=True),
    Output('admin-model-edit-toast', 'is_open'), Output('admin-model-edit-toast', 'children'), Output('admin-model-edit-toast', 'icon'),
    Input('admin-model-save', 'n_clicks'), Input('admin-model-cancel', 'n_clicks'),
    State('admin-model-edit-id', 'data'), State('admin-model-modal-name', 'value'), State('admin-model-modal-version', 'value'), State('admin-model-modal-description', 'value'), State('admin-model-modal-status', 'value'), State('session-store', 'data'),
    prevent_initial_call=True
)
def handle_model_save(save_click, cancel_click, edit_id, name, version, description, status, session_data):
    ctx = dash.callback_context
    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate
    action = ctx.triggered[0]['prop_id'].split('.')[0]

    if action == 'admin-model-cancel':
        return False, None, False, '', 'success'

    if action == 'admin-model-save':
        if not edit_id or not session_data:
            raise dash.exceptions.PreventUpdate
        token = session_data.get('token')
        payload = {
            'ten_mo_hinh': name or '',
            'phien_ban': version or '',
            'trang_thai': bool(status),
            'mo_ta': description or ''
        }
        try:
            success, message = api_models.update_model(int(edit_id), payload, token=token)
        except Exception as e:
            success = False
            message = str(e)
        return False, None, True, message or ('Cập nhật thành công' if success else 'Lỗi khi cập nhật'), 'success' if success else 'danger'

    raise dash.exceptions.PreventUpdate

@callback(
    Output('model-upload-display', 'children'),
    Input('admin-model-upload', 'contents'),
    State('admin-model-upload', 'filename'),
    prevent_initial_call=True
)
def update_upload_display(contents, filename):
    if not contents or not filename:
        return [
            html.I(className='fas fa-file-upload me-2'),
            html.Span('Kéo thả tệp ở đây hoặc bấm để chọn'),
            html.Br(),
            html.Small('Chỉ chấp nhận file .h5, .pkl', className='text-muted')
        ]
    
    if not filename.lower().endswith(('.h5', '.pkl')):
        return [
            html.I(className='fas fa-exclamation-circle me-2', style={'color': '#dc3545'}),
            html.Strong(filename, className='me-2'),
            html.Small('(File không hợp lệ)', className='text-danger'),
            html.Br(),
            html.Small('Chỉ chấp nhận file .h5, .pkl', className='text-muted')
        ]

    return [
        html.I(className='fas fa-file me-2'),
        html.Strong(filename, className='me-2'),
        html.Small('(Đã chọn)', className='text-success'),
        html.Br(),
        html.Small('Nhấn nút tải lên để hoàn tất', className='text-muted')
    ]