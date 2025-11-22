from dash import html, dcc, callback, Input, Output, State
import dash_bootstrap_components as dbc
import dash
from api.auth import register_user, authenticate_user
from dash.exceptions import PreventUpdate


layout = html.Div(
    className="auth-container",
    children=[
        html.Div(
            className="auth-box",
            style={"max-width": "1100px", "height": "80%"},
            
            children=[
                html.Div(
                    className="auth-panel left-panel d-none d-md-flex",
                    children=[
                        html.Img(
                            src="/assets/logo_waterflow.png",
                            style={"width": "90px", "border-radius": "50% !important", "background-color": "white"},
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
                                html.H3("Đăng Ký Tài Khoản", className="text-center mb-4 fw-bold", style={"color": "#023E73"}),

                                dcc.Loading(
                                    id='loading-register-message',
                                    type='default',
                                    children=html.Div(id='register-message', className="mb-3")
                                ),

                                dbc.Form([
                                    dbc.Label("Tên đăng nhập", className="fw-bold"),
                                    dbc.Input(
                                        id='register-username',
                                        type='text',
                                        placeholder='Nhập số điện thoại',
                                        className="mb-3 px-3 py-2"
                                    ),

                                    dbc.Label("Họ và tên", className="fw-bold"),
                                    dbc.Input(
                                        id='register-fullname',
                                        type='text',
                                        placeholder='Nhập họ và tên',
                                        className="mb-3 px-3 py-2"
                                    ),

                                    dbc.Label("Mật khẩu", className="fw-bold"),
                                    html.Div(className='pw-input-wrapper mb-3', children=[
                                        dbc.Input(
                                            id='register-password',
                                            type='password',
                                            placeholder='Nhập mật khẩu',
                                            className="px-3 py-2"
                                        ),
                                        html.Span(html.I(className='fas fa-eye'), className='pw-toggle', **{'data-target':'register-password'})
                                    ]),

                                    dbc.Label("Xác nhận mật khẩu", className="fw-bold"),
                                    html.Div(className='pw-input-wrapper mb-3', children=[
                                        dbc.Input(
                                            id='register-confirm-password',
                                            type='password',
                                            placeholder='Nhập lại mật khẩu',
                                            className="px-3 py-2"
                                        ),
                                        html.Span(html.I(className='fas fa-eye'), className='pw-toggle', **{'data-target':'register-confirm-password'})
                                    ]),

                                    dbc.Row([
                                        dbc.Col(
                                            dbc.Checkbox(
                                                id='accept-terms',
                                                label='Tôi đồng ý với điều khoản sử dụng',
                                                value=False,
                                                className="mb-2"
                                            ), width=9
                                        ),
                                    ], className="mb-3"),

                                    dbc.Button(
                                        [html.I(className="fas me-2"), "Đăng Ký"],
                                        id='register-btn',
                                        className="w-100 py-2 fw-bold rounded-pill",
                                        size="lg",
                                        style={"background-color": "#023E73", "border": "none"},
                                    ),

                                    html.Hr(className="my-4"),

                                    html.P(
                                        ["Đã có tài khoản? ",
                                            html.A("Đăng nhập ngay", href="/login", className="fw-bold", style={"text-decoration": "none", "color": "#023E73"})],
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
    ]
)


@callback(
    [Output('register-message', 'children'),
     Output('session-store', 'data', allow_duplicate=True),
     Output('url', 'pathname', allow_duplicate=True)],
    Input('register-btn', 'n_clicks'),
    [State('register-username', 'value'),
     State('register-fullname', 'value'),
     State('register-password', 'value'),
     State('register-confirm-password', 'value'),
     State('accept-terms', 'value')],
    prevent_initial_call=True
)
def register_new_user(n_clicks, username, fullname, password, confirm_password, accept_terms):
    if not n_clicks:
        raise PreventUpdate

    if not username or not fullname or not password or not confirm_password:
        return dbc.Alert("Vui lòng nhập đầy đủ thông tin!", color="warning", dismissable=True), dash.no_update, dash.no_update

    if not accept_terms:
        return dbc.Alert("Vui lòng đồng ý với điều khoản sử dụng!", color="warning", dismissable=True), dash.no_update, dash.no_update

    if password != confirm_password:
        return dbc.Alert("Mật khẩu xác nhận không khớp!", color="danger", dismissable=True), dash.no_update, dash.no_update

    if len(password) < 6:
        return dbc.Alert("Mật khẩu phải có ít nhất 6 ký tự!", color="warning", dismissable=True), dash.no_update, dash.no_update

    success, message = register_user(username, fullname, password)

    if success:
        auth_success, auth_message, token, token_exp = authenticate_user(username, password)
        if auth_success:
            session_data = {
                'authenticated': True,
                'username': username,
                'token': token,
                'token_exp': token_exp
            }
            return dbc.Alert(message + " Đăng ký thành công!", color="success", dismissable=True), session_data, '/account'
        else:
            return dbc.Alert(message + " Tuy nhiên tự động đăng nhập thất bại. Vui lòng đăng nhập.", color="warning", dismissable=True), dash.no_update, '/login'
    else:
        return dbc.Alert(message, color="danger", dismissable=True), dash.no_update, dash.no_update
