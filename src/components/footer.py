from dash import html
import dash_bootstrap_components as dbc


def create_footer():
    return html.Footer([
        dbc.Container([
            dbc.Row([
                dbc.Col([
                    html.P("© 2025 Dự Đoán Lưu Lượng Nước. Bảo lưu mọi quyền.",
                           className="text-center mb-0 footer-text")
                ], width=12)
            ])
        ])
    ], className="py-4 mt-5 site-footer")
