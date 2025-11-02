from dash import html, dcc, callback, Input, Output, State
import dash_bootstrap_components as dbc
import dash
from components.navbar import create_navbar
from api import firmware as api_firmware
import base64


layout = html.Div([
    create_navbar(is_authenticated=True, is_admin=True),
    dcc.Location(id='admin-firmware-url', refresh=False),
    dbc.Container([
        dbc.Row([
            dbc.Col(html.H2([html.I(className='fas fa-chip me-2'), 'Quản lý Firmware']), md=9),
        ], className='my-3'),

        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader('Tải lên firmware mới'),
                    dbc.CardBody([
                        dcc.Upload(id='admin-firmware-upload', children=
                                    html.Div(['Kéo thả tệp ở đây hoặc bấm để chọn (file .bin)']),
                                    style={'border': '1px dashed #ced4da', 'padding': '20px', 'textAlign': 'center'}),
                        dbc.Row([
                            dbc.Col(dbc.Input(id='admin-firmware-name', placeholder='Tên tệp (ten_tep)', className='mb-2')),
                            dbc.Col(dbc.Input(id='admin-firmware-version', placeholder='Phiên bản (ví dụ 1.0.0)', className='mb-2')),
                            dbc.Col(dbc.Input(id='admin-firmware-url', placeholder='URL tải xuống (tuỳ chọn)', className='mb-2')),
                        ], className='mt-2'),
                        dbc.Row([
                            dbc.Col(dbc.Input(id='admin-firmware-description', placeholder='Mô tả (tuỳ chọn)', className='mb-2')),
                            dbc.Col(dbc.Button('Tải lên', id='admin-firmware-upload-btn', color='primary'))
                        ], className='mt-2')
                    ])
                ], className='mb-3')
            ], md=12)
        ]),

        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader('Danh sách firmware'),
                    dbc.CardBody([
                        dcc.Store(id='admin-firmware-store'),
                        html.Div(id='admin-firmware-table-container')
                    ])
                ])
            ], md=12)
        ])
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
        # Map backend fields to expected model names
        fid = item.get('ma_tep_ma_nhung') or item.get('id') or item.get('firmware_id')
        name = item.get('ten_tep') or item.get('ten') or item.get('filename') or ''
        version = item.get('phien_ban') or item.get('phienban') or item.get('version') or ''
        description = item.get('mo_ta') or item.get('description') or ''
        created = item.get('thoi_gian_tao') or item.get('created_at') or ''
        updated = item.get('thoi_gian_cap_nhat') or item.get('updated_at') or ''
        download_link = item.get('url') or (api_firmware.download_url(fid) if fid else '#')

        rows.append(html.Tr([
            html.Td(str(fid)),
            html.Td(name),
            html.Td(version),
            html.Td(description),
            html.Td(str(created)),
            html.Td(str(updated)),
            html.Td([
                dbc.Button('Tải xuống', href=download_link, target='_blank', size='sm', color='info', className='me-2'),
                dbc.Button('Xóa', id={'type': 'delete-firmware-btn', 'index': str(fid)}, color='danger', size='sm')
            ])
        ]))

    table = dbc.Table([
        html.Thead(html.Tr([html.Th('ID'), html.Th('Tên'), html.Th('Phiên bản'), html.Th('Mô tả'), html.Th('Thời gian tạo'), html.Th('Thời gian cập nhật'), html.Th('Hành động')])),
        html.Tbody(rows)
    ], bordered=True, hover=True, responsive=True)

    return table


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
    Output('admin-firmware-store', 'data'),
    Output('admin-firmware-upload', 'children'),
    Input('admin-firmware-upload-btn', 'n_clicks'),
    State('admin-firmware-upload', 'contents'),
    State('admin-firmware-upload', 'filename'),
    State('admin-firmware-name', 'value'),
    State('admin-firmware-version', 'value'),
    State('admin-firmware-description', 'value'),
    State('admin-firmware-url', 'value'),
    State('session-store', 'data'),
    prevent_initial_call=True
)
def handle_firmware_upload(n_clicks, contents, filename, name, version, description, url, session_data):
    if not n_clicks:
        raise dash.exceptions.PreventUpdate

    if not session_data or not session_data.get('authenticated') or not session_data.get('is_admin'):
        return dash.no_update, dash.no_update

    parsed = _parse_uploaded_contents(contents, filename)
    if not parsed:
        return dash.no_update, html.Div(['Kéo thả tệp ở đây hoặc bấm để chọn (file .bin)'])

    token = session_data.get('token')
    meta = {
        'ten_tep': (name or filename) or '',
        'phien_ban': version or '',
        'mo_ta': description or '',
        'url': url or ''
    }
    success, msg = api_firmware.upload_firmware(parsed, metadata=meta, token=token)
    if success:
        return {'status': 'uploaded'}, html.Div(['Tải lên thành công: ', html.Strong(filename)])
    return dash.no_update, html.Div(['Kéo thả tệp ở đây hoặc bấm để chọn (file .bin)'])


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
