from dash import html, dcc, callback, Input, Output, State
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
import dash
from api.auth import authenticate_user, forgot_password_verify, forgot_password_reset, get_user_info

layout = html.Div(
    className="auth-container",
    children=[
        html.Div(
            className="auth-box",
            children=[
                html.Div(
                    className="auth-panel left-panel",
                    children=[
                        html.Img(
                            src="/assets/logo_waterflow.png",
                            style={"width": "90px", "background-color": "white", "border-radius": "50%"},
                            className="mb-3"
                        ),
                        html.H2("HỆ THỐNG GIÁM SÁT VÀ DỰ BÁO DÒNG CHẢY NƯỚC", className="fw-bold text-white mb-3"),
                        html.P(
                            "Giải pháp giám sát thời gian thực và dự báo lưu lượng nước, giúp tối ưu nguồn nước "
                            "và hỗ trợ ra quyết định cho quản lý nguồn nước và nông nghiệp bền vững.",
                            className="text-light mb-4"
                        ),
                    ],
                ),

                html.Div(
                    className="auth-panel right-panel",
                    children=[
                        dbc.Card(
                            dbc.CardBody([
                                html.H3("Đăng Nhập", className="text-center mb-4 fw-bold", style={"color": "#023E73"}),

                                dcc.Loading(
                                    id='loading-login-message',
                                    type='default',
                                    children=html.Div(id='login-message', className="mb-3")
                                ),

                                dbc.Form([
                                    dbc.Label("Tên đăng nhập", className="fw-bold"),
                                    dbc.Input(
                                        id='login-username',
                                        type='text',
                                        placeholder='Nhập số điện thoại',
                                        className="mb-3 px-3 py-2"
                                    ),

                                    dbc.Label("Mật khẩu", className="fw-bold"),
                                    dbc.Input(
                                        id='login-password',
                                        type='password',
                                        placeholder='Nhập mật khẩu',
                                        className="mb-3 px-3 py-2"
                                    ),

                                    dbc.Row([
                                        dbc.Col(
                                            dbc.Checkbox(
                                                id='remember-me',
                                                label='Ghi nhớ đăng nhập',
                                                value=False,
                                                className="mb-2"
                                            ), width=6
                                        ),
                                        dbc.Col(
                                            dbc.Button(
                                                "Quên mật khẩu?",
                                                id='forgot-link',
                                                color='link',
                                                className='p-0 small text-decoration-none float-end',
                                                style={"color": "#023E73"}
                                            ), width=6
                                        )
                                    ], className="mb-3"),

                                    dbc.Button(
                                        [html.I(className="fas me-2"), "Đăng Nhập"],
                                        id='login-btn',
                                        className="w-100 py-2 fw-bold rounded-pill",
                                        size="lg",
                                        style={"background-color": "#023E73", "border": "none"},
                                    ),

                                    html.Hr(className="my-4"),

                                    html.P(
                                        ["Chưa có tài khoản? ",
                                            html.A("Đăng ký ngay", href="/register", className="fw-bold", style={"text-decoration": "none", "color": "#023E73"})],
                                        className="text-center mb-0"
                                    )
                                ])
                            ]),
                            className="border-0 p-4 rounded-4 login-card"
                        )
                    ],
                ),
            ],
        ),

        dcc.Store(id='forgot-verified-store', data=None),

        dbc.Modal([
            dbc.ModalHeader("Khôi phục mật khẩu"),
            dbc.ModalBody(html.Div(id='forgot-body')),
            dbc.ModalFooter([
                html.Div(id='forgot-footer'),
                dbc.Button("Đóng", id='forgot-close', className='ms-2 btn-cancel')
            ])
        ], id='forgot-modal', is_open=False, centered=True)
    ]
)


@callback(
    [Output('login-message', 'children'),
     Output('session-store', 'data', allow_duplicate=True),
     Output('url', 'pathname', allow_duplicate=True)],
    Input('login-btn', 'n_clicks'),
    [State('login-username', 'value'),
     State('login-password', 'value')],
    prevent_initial_call=True
)
def login_user(n_clicks, username, password):
    if not n_clicks:
        raise PreventUpdate

    if not username or not password:
        return dbc.Alert("Vui lòng nhập đầy đủ thông tin!", color="warning", dismissable=True), dash.no_update, dash.no_update
    
    success, message, token, token_exp = authenticate_user(username, password)
    if success:
        is_admin = False
        try:
            user_info = get_user_info(username, token=token)
            if user_info.get('quan_tri_vien')==True:
                is_admin = True
            else:
                is_admin = False
            
        except Exception:
            is_admin = False

        session_data = {
            'authenticated': True,
            'username': username,
            'token': token,
            'token_exp': token_exp,
            'is_admin': is_admin
        }
        redirect_path = '/admin' if is_admin else '/'
        return dbc.Alert(message, color="success", dismissable=True), session_data, redirect_path
    else:
        return dbc.Alert(message, color="danger", dismissable=True), dash.no_update, dash.no_update


@callback(
    Output('forgot-modal', 'is_open', allow_duplicate=True),
    [Input('forgot-link', 'n_clicks'), Input('forgot-close', 'n_clicks')],
    [State('forgot-modal', 'is_open')],
    prevent_initial_call=True
)
def toggle_forgot(n_open, n_close, is_open):
    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate
    btn = ctx.triggered[0]['prop_id'].split('.')[0]
    return not is_open if btn in ['forgot-link', 'forgot-close'] else is_open


@callback(
    [Output('forgot-body', 'children'), Output('forgot-footer', 'children')],
    [Input('forgot-modal', 'is_open'), Input('forgot-verified-store', 'data')],
    prevent_initial_call=False
)
def render_forgot_modal(is_open, verified):
    if not is_open:
        raise PreventUpdate

    if not verified:
        body = dbc.Form([
            dbc.Label("Tên đăng nhập", className='fw-bold'),
            dbc.Input(id='forgot-username', type='text', placeholder='Nhập tên đăng nhập', className='mb-2'),
            dbc.Label("Tên máy bơm", className='fw-bold'),
            dbc.Input(id='forgot-pump-name', type='text', placeholder='Nhập tên máy bơm', className='mb-2'),
            dbc.Label("Ngày tưới gần nhất", className='fw-bold'),
            dbc.Input(id='forgot-last-irrigation', type='date', className='mb-2'),
            html.Div(id='forgot-step-message')
        ])
        footer = html.Div([
            dbc.Button("Xác thực", id='forgot-verify', color='primary')
        ])
        return body, footer
    else:
        body = dbc.Form([
            dbc.Label("Tên đăng nhập", className='fw-bold'),
            dbc.Input(id='forgot-username-2', type='text', value=verified, disabled=True, className='mb-2'),
            dbc.Label("Mật khẩu mới", className='fw-bold'),
            dbc.Input(id='forgot-new-password', type='password', placeholder='Nhập mật khẩu mới', className='mb-2'),
            html.Div(id='forgot-step-message')
        ])
        footer = html.Div([
            dbc.Button("Đặt lại mật khẩu", id='forgot-reset', color='primary')
        ])
        return body, footer



@callback(
    [Output('forgot-step-message', 'children', allow_duplicate=True), Output('forgot-verified-store', 'data')],
    Input('forgot-verify', 'n_clicks'),
    [State('forgot-username', 'value'), State('forgot-pump-name', 'value'), State('forgot-last-irrigation', 'value')],
    prevent_initial_call=True
)
def handle_forgot_verify(n_clicks, ten_dang_nhap, ten_may_bom, ngay_tuoi):
    
    if not n_clicks:
        raise PreventUpdate
    
    if not ten_dang_nhap or not ten_may_bom or not ngay_tuoi:
        return dbc.Alert('Vui lòng nhập đầy đủ thông tin xác thực', color='warning'), dash.no_update

    success, message = forgot_password_verify(ten_dang_nhap, ten_may_bom, ngay_tuoi)
    if success:
        return dbc.Alert(message, color='success', dismissable=True), ten_dang_nhap
    else:
        return dbc.Alert(message, color='danger', dismissable=True), dash.no_update



@callback(
    [Output('forgot-step-message', 'children', allow_duplicate=True), Output('forgot-modal', 'is_open', allow_duplicate=True), Output('login-message', 'children', allow_duplicate=True)],
    Input('forgot-reset', 'n_clicks'),
    [State('forgot-username-2', 'value'), State('forgot-new-password', 'value')],
    prevent_initial_call=True
)
def handle_forgot_reset(n_clicks, ten_dang_nhap, mat_khau_moi):
    if not mat_khau_moi:
        return dbc.Alert('Vui lòng nhập mật khẩu mới', color='warning'), dash.no_update, dash.no_update

    success, message = forgot_password_reset(ten_dang_nhap, mat_khau_moi)
    if success:
        return dbc.Alert(message, color='success', dismissable=True), False, dbc.Alert(message, color='success', dismissable=True)
    else:
        return dbc.Alert(message, color='danger', dismissable=True), True, dash.no_update
