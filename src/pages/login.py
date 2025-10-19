from dash import html, dcc, callback, Input, Output, State
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
import dash
from utils.auth import authenticate_user, forgot_password

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
                        html.H2("HỆ THỐNG DỰ BÁO LƯU LƯỢNG NƯỚC", className="fw-bold text-white mb-3"),
                        html.P(
                            "Giải pháp hỗ trợ tưới tiêu thông minh, giúp nông dân tối ưu nguồn nước, "
                            "dự báo lưu lượng và ra quyết định hiệu quả cho sản xuất nông nghiệp bền vững.",
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
                                        placeholder='Nhập tên đăng nhập',
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

        # Modal quên mật khẩu
        dbc.Modal([
            dbc.ModalHeader("Khôi phục mật khẩu"),
            dbc.ModalBody([
                dbc.Label("Email hoặc tên đăng nhập"),
                dbc.Input(
                    id='forgot-email',
                    type='text',
                    placeholder='Nhập email hoặc tên đăng nhập',
                    className='mb-2 rounded-pill'
                ),
                html.Div(id='forgot-message', className='mt-2')
            ]),
            dbc.ModalFooter([
                dbc.Button("Gửi", id='forgot-submit', color='primary'),
                dbc.Button("Đóng", id='forgot-close', className='ms-2')
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

    if not username or not password:
        return dbc.Alert("Vui lòng nhập đầy đủ thông tin!", color="warning", dismissable=True), dash.no_update, dash.no_update
    
    success, message, token, token_exp = authenticate_user(username, password)
    if success:
        session_data = {
            'authenticated': True,
            'username': username,
            'token': token,
            'token_exp': token_exp
        }
        return dbc.Alert(message, color="success", dismissable=True), session_data, '/dashboard'
    else:
        return dbc.Alert(message, color="danger", dismissable=True), dash.no_update, dash.no_update


@callback(
    Output('forgot-modal', 'is_open'),
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
    [Output('forgot-message', 'children'), Output('forgot-modal', 'is_open', allow_duplicate=True)],
    Input('forgot-submit', 'n_clicks'),
    [State('forgot-email', 'value')],
    prevent_initial_call=True
)
def submit_forgot(n_clicks, identifier):
    if not identifier:
        return dbc.Alert('Vui lòng nhập email hoặc tên đăng nhập', color='warning'), dash.no_update

    success, message = forgot_password(identifier)
    if success:
        return dbc.Alert(message, color='success', dismissable=True), False
    else:
        return dbc.Alert(message, color='danger', dismissable=True), True
