from dash import html, dcc, callback, Input, Output, State
import dash_bootstrap_components as dbc
import dash
from components.navbar import create_navbar
from api import firmware as api_firmware
import base64


layout = html.Div([
    create_navbar(is_authenticated=True, is_admin=True),
    dcc.Location(id='admin-firmware-url', refresh=False),
    dbc.Toast(
        id='admin-firmware-toast',
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
                dbc.Card([
                    dbc.CardHeader(html.Span('Tải lên firmware mới', className='user-table-title')),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                dcc.Upload(
                                    id='admin-firmware-upload',
                                    children=html.Div(id='upload-display', children=[
                                        html.I(className='fas fa-file-upload me-2'),
                                        html.Span('Kéo thả tệp ở đây hoặc bấm để chọn'),
                                        html.Br(),
                                        html.Small('Chỉ chấp nhận file .bin', className='text-muted')
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
                                dbc.Label('Tên firmware', className='mb-2 fw-medium'),
                                dbc.Input(
                                    id='admin-firmware-name',
                                    placeholder='Nhập tên firmware...',
                                    className='mb-3'
                                )
                            ], md=4),
                            dbc.Col([
                                dbc.Label('Phiên bản', className='mb-2 fw-medium'),
                                dbc.Input(
                                    id='admin-firmware-version',
                                    placeholder='Ví dụ: 1.0.0',
                                    className='mb-3'
                                )
                            ], md=4),
                            dbc.Col([
                                dbc.Label('Mô tả', className='mb-2 fw-medium'),
                                dbc.Textarea(
                                    id='admin-firmware-description',
                                    placeholder='Nhập mô tả firmware (tùy chọn)...',
                                    className='mb-3',
                                    style={'height': '50px', 'resize': 'none'}
                                    
                                )
                            ], md=4),
                        ]),
                        dbc.Row([
                            dbc.Col([
                                dbc.Button(
                                    [html.I(className='fas fa-upload me-2'), 'Tải lên'],
                                    id='admin-firmware-upload-btn',
                                    color='primary',
                                    className='d-flex align-items-center justify-content-center h-100 px-4'
                                )
                            ], md=12, className='d-flex align-items-center justify-content-center')
                        ])
                    ])
                ], className='mb-4 user-table-card',  style={'marginTop': '70px'})
            ], md=12)
        ]),

        dbc.Row([
            dbc.Col([
                html.Div([
                    dcc.Store(id='admin-firmware-store'),
                    html.Div(id='admin-firmware-table-container')
                ])
            ], md=12)
        ], className='mt-3')
    ], fluid=True, className='py-4')
])


@callback(
    Output('admin-firmware-table-container', 'children'),
    Input('url', 'pathname'),
    State('session-store', 'data'),
    prevent_initial_call='initial_duplicate'
)
def load_firmware_page(pathname, session_data):
    if pathname != '/admin/firmware':
        raise dash.exceptions.PreventUpdate

    if not session_data or not session_data.get('authenticated') or not session_data.get('is_admin'):
        raise dash.exceptions.PreventUpdate

    token = session_data.get('token')
    try:
        data = api_firmware.list_firmwares(limit=200, offset=0, token=token) or {}
        items = data.get('data', []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
    except Exception:
        items = []

    if not items:
        return html.Div(html.P('Chưa có firmware nào được tải lên.'), className='text-muted')

    rows = []
    for item in items:
        fid = item.get('ma_tep_ma_nhung')
        name = item.get('ten_tep')
        version = item.get('phien_ban')
        description = item.get('mo_ta')
        created = item.get('thoi_gian_tao')
        updated = item.get('thoi_gian_cap_nhat')
        download_link = item.get('url') or (api_firmware.download_url(fid, token) if fid else '#')

        rows.append(html.Tr([
            html.Td(html.Strong(name or f"FW-{fid}")),
            html.Td(version, className='text-nowrap'),
            html.Td(description or '--'),
            html.Td(download_link if download_link and download_link != '#' else '--', className='text-break'),
            html.Td(str(created).split('T')[0] if 'T' in str(created) else str(created), className='text-nowrap'),
            html.Td(str(updated).split('T')[0] if 'T' in str(updated) else str(updated), className='text-nowrap'),
            html.Td(html.Div([
                dbc.Button(
                    html.I(className='fas fa-download'),
                    href=download_link,
                    target='_blank',
                    color='light',
                    size='sm',
                    className='action-btn download',
                    title='Tải xuống'
                ),
                dbc.Button(
                    html.I(className='fas fa-trash'),
                    id={'type': 'delete-firmware-btn', 'index': str(fid)},
                    color='light',
                    size='sm',
                    className='action-btn delete',
                    title='Xóa firmware'
                )
            ], className='user-actions'), className='text-end')
        ]))

    table = dbc.Table([
        html.Thead(html.Tr([
            html.Th('Tên firmware'),
            html.Th('Phiên bản'),
            html.Th('Mô tả'),
            html.Th('URL'),
            html.Th('Thời gian tạo'),
            html.Th('Thời gian cập nhật'),
            html.Th('Hành động')
        ])),
        html.Tbody(rows)
    ], bordered=False, hover=True, responsive=True, className='user-table firmware-table')

    table_card = dbc.Card([
        dbc.CardHeader(html.Span('Danh sách firmware', className='user-table-title')),
        dbc.CardBody([table])
    ], className='user-table-card')

    return table_card


def _parse_uploaded_contents(contents, filename):
    if not contents or not isinstance(contents, str):
        return None
    try:
        header, b64 = contents.split(',', 1)
        data = base64.b64decode(b64)
        return (filename, data)
    except Exception:
        return None


@callback(
    Output('upload-display', 'children'),
    Input('admin-firmware-upload', 'contents'),
    State('admin-firmware-upload', 'filename'),
    prevent_initial_call=True
)
def update_upload_display(contents, filename):
    if not contents or not filename:
        return [
            html.I(className='fas fa-file-upload me-2'),
            html.Span('Kéo thả tệp ở đây hoặc bấm để chọn'),
            html.Br(),
            html.Small('Chỉ chấp nhận file .bin', className='text-muted')
        ]
    
    return [
        html.I(className='fas fa-file me-2'),
        html.Strong(filename, className='me-2'),
        html.Small('(Đã chọn)', className='text-success'),
        html.Br(),
        html.Small('Nhấn nút tải lên để hoàn tất', className='text-muted')
    ]

@callback(
    Output('admin-firmware-store', 'data'),
    Output('admin-firmware-upload', 'contents'),
    Input('admin-firmware-upload-btn', 'n_clicks'),
    State('admin-firmware-upload', 'contents'),
    State('admin-firmware-upload', 'filename'),
    State('admin-firmware-name', 'value'),
    State('admin-firmware-version', 'value'),
    State('admin-firmware-description', 'value'),
    State('session-store', 'data'),
    prevent_initial_call=True
)
def handle_firmware_upload(n_clicks, contents, filename, name, version, description, session_data):
    if not n_clicks:
        raise dash.exceptions.PreventUpdate

    if not session_data or not session_data.get('authenticated') or not session_data.get('is_admin'):
        return dash.no_update, dash.no_update

    # Validate required fields
    if not name or not name.strip():
        return dash.no_update, html.Div([
            html.I(className='fas fa-exclamation-circle me-2'),
            'Vui lòng nhập tên firmware'
        ], className='text-danger')

    # Validate file upload
    parsed = _parse_uploaded_contents(contents, filename)
    if not parsed:
        return dash.no_update, html.Div([
            html.I(className='fas fa-exclamation-circle me-2'),
            'Vui lòng chọn tệp firmware (file .bin)'
        ], className='text-danger')

    token = session_data.get('token')
    meta = {
        'ten_tep': name.strip(),  # Use cleaned name
        'phien_ban': version or '',
        'mo_ta': description or ''
    }
    try:
        success, msg = api_firmware.upload_firmware(parsed, metadata=meta, token=token)
    except Exception:
        success = False
    if success:
        return {'status': 'uploaded', 'filename': filename}, html.Div([
            html.I(className='fas fa-check-circle me-2 text-success'),
            'Tải lên thành công: ',
            html.Strong(filename)
        ])
    return dash.no_update, html.Div([
        html.I(className='fas fa-exclamation-circle me-2'),
        'Không thể tải lên firmware. Vui lòng thử lại.'
    ], className='text-danger')


@callback(
    Output('admin-firmware-toast', 'is_open'),
    Output('admin-firmware-toast', 'children'),
    Output('admin-firmware-toast', 'icon'),
    Input('admin-firmware-store', 'data'),
    prevent_initial_call=True
)
def show_firmware_toast(store):
    if not store or not isinstance(store, dict):
        raise dash.exceptions.PreventUpdate
    if store.get('status') == 'uploaded':
        fname = store.get('filename') or ''
        return True, html.Span(['Tải lên thành công: ', html.Strong(fname)]), 'success'
    raise dash.exceptions.PreventUpdate


@callback(
    Output({'type': 'delete-firmware-btn', 'index': dash.ALL}, 'n_clicks'),
    Input({'type': 'delete-firmware-btn', 'index': dash.ALL}, 'n_clicks'),
    State('session-store', 'data'),
    prevent_initial_call=True
)
def handle_delete_firmware(n_clicks_list, session_data):
    if not session_data or not session_data.get('authenticated') or not session_data.get('is_admin'):
        raise dash.exceptions.PreventUpdate

    ctx = dash.callback_context
    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate
    triggered = ctx.triggered[0]
    prop_id = triggered.get('prop_id', '')
    # prop_id format: {"type":"delete-firmware-btn","index":"<id>"}.n_clicks
    try:
        import json
        btn_id = prop_id.split('.')[0]
        btn_obj = json.loads(btn_id.replace("'", '"'))
        fid = btn_obj.get('index')
    except Exception:
        fid = None

    if fid is None:
        raise dash.exceptions.PreventUpdate

    token = session_data.get('token')
    try:
        try:
            fid_int = int(fid)
        except Exception:
            fid_int = fid
        success, msg = api_firmware.delete_firmware(fid_int, token=token)
    except Exception:
        success = False

    return [0 for _ in (n_clicks_list or [])]
