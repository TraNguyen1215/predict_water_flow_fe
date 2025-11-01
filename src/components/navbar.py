import dash_bootstrap_components as dbc
from dash import html


def create_navbar(is_authenticated=False, is_admin=False, current_path: str = None):
    def is_active(href: str) -> bool:
        if not current_path:
            return False
        if href == '/' and (current_path == '/' or current_path == ''):
            return True
        return current_path.rstrip('/') == href.rstrip('/')

    if is_authenticated:
        if is_admin:
            nav_items = [
                dbc.NavItem(dbc.NavLink("Trang chủ", href="/admin", className="nav-link-custom", active=is_active('/admin'))),
                dbc.NavItem(dbc.NavLink("Người dùng", href="/admin/users", className="nav-link-custom", active= is_active('/admin/users'))),
                dbc.NavItem(dbc.NavLink("Mô hình", href="/admin/models", className="nav-link-custom", active=is_active('/admin/models'))),
                dbc.NavItem(dbc.NavLink("Loại cảm biến", href="/admin/sensor-types", className="nav-link-custom", active=is_active('/admin/sensor-types'))),
                dbc.NavItem(dbc.NavLink("Tài liệu", href="/documentation", className="nav-link-custom", active=is_active('/documentation'))),
            ]
        else:
            nav_items = [
                dbc.NavItem(dbc.NavLink("Trang chủ", href="/", className="nav-link-custom", active=is_active('/'))),
                dbc.NavItem(dbc.NavLink("Cảm biến", href="/sensor", className="nav-link-custom", active=is_active('/sensor'))),
                dbc.NavItem(dbc.NavLink("Máy bơm", href="/pump", className="nav-link-custom", active=is_active('/pump'))),
                # Removed "Dữ liệu cảm biến" nav item to hide the sensor data page from navigation
                dbc.NavItem(dbc.NavLink("Dự đoán", href="/predict_data", className="nav-link-custom", active=is_active('/predict_data'))),
                dbc.NavItem(dbc.NavLink("Nạp ESP", href="/esp-flash", className="nav-link-custom", active=is_active('/esp-flash'))),
                dbc.NavItem(dbc.NavLink("Tài liệu", href="/documentation", className="nav-link-custom", active=is_active('/documentation'))),
            ]

        nav_items.extend([
            dbc.NavItem(dbc.NavLink("Tài khoản", href="/account", className="nav-link-custom", active=is_active('/account'))),
            dbc.NavItem(dbc.NavLink([
                html.I(className="fas fa-sign-out-alt me-2"),
                "Đăng xuất"
            ], href="/logout", className="nav-link-custom", active=is_active('/logout'))),
        ])
    else:
        nav_items = [
            dbc.NavItem(dbc.NavLink("Đăng nhập", href="/login", className="nav-link-custom", active=is_active('/login'))),
            dbc.NavItem(dbc.NavLink("Đăng ký", href="/register", className="nav-link-custom", active=is_active('/register'))),
        ]

    brand_href = "/admin" if is_authenticated and is_admin else ("/" if is_authenticated else "/login")

    navbar = dbc.Navbar(
        dbc.Container([
            html.A(
                dbc.Row([
                    dbc.Col(html.Img(src='/assets/logo_waterflow.png', style={'height':'40px'}, alt='Logo')),
                    dbc.Col(dbc.NavbarBrand("Dự Đoán Lưu Lượng Nước", className="ms-2 navbar-brand-custom")),
                ], align="center", className="g-0"),
                href=brand_href,
                style={"textDecoration": "none"}
            ),
            dbc.NavbarToggler(id="navbar-toggler", n_clicks=0),
            dbc.Collapse(
                dbc.Nav(
                    nav_items,
                    className="ms-auto",
                    navbar=True
                ),
                id="navbar-collapse",
                navbar=True,
            ),
        ], fluid=True),
        color="white",
        dark=False,
        className="navbar-custom shadow-sm mb-4",
        sticky="top"
    )

    return navbar
