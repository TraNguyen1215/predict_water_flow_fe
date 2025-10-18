import dash_bootstrap_components as dbc
from dash import html, dcc

def create_navbar(is_authenticated=False):
    """Create responsive navbar"""
    
    if is_authenticated:
        nav_items = [
            dbc.NavItem(dbc.NavLink("Trang chủ", href="/", className="nav-link-custom")),
            dbc.NavItem(dbc.NavLink("Tài khoản", href="/account", className="nav-link-custom")),
            dbc.NavItem(dbc.NavLink("Cài đặt", href="/settings", className="nav-link-custom")),
            dbc.NavItem(dbc.NavLink([
                html.I(className="fas fa-sign-out-alt me-2"),
                "Đăng xuất"
            ], href="/logout", className="nav-link-custom")),
        ]
    else:
        nav_items = [
            dbc.NavItem(dbc.NavLink("Trang chủ", href="/", className="nav-link-custom")),
            dbc.NavItem(dbc.NavLink("Đăng nhập", href="/login", className="nav-link-custom")),
            dbc.NavItem(dbc.NavLink("Đăng ký", href="/register", className="nav-link-custom")),
        ]
    
    navbar = dbc.Navbar(
        dbc.Container([
            html.A(
                dbc.Row([
                    dbc.Col(html.I(className="fas fa-water fa-2x text-primary")),
                    dbc.Col(dbc.NavbarBrand("Dự Đoán Lưu Lượng Nước", className="ms-2 navbar-brand-custom")),
                ], align="center", className="g-0"),
                href="/",
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
