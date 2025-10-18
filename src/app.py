import dash
from dash import html, dcc, Input, Output, State
import dash_bootstrap_components as dbc
from flask import session
import os

# Import pages
from pages import home, login, register, account, settings
from components.navbar import create_navbar

# Initialize app with Bootstrap theme
app = dash.Dash(
    __name__,
    suppress_callback_exceptions=True,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP, 
        dbc.icons.FONT_AWESOME,
        "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css"
    ],
    assets_folder='assets',
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1"}
    ]
)

# Server for session management
server = app.server
server.config['SECRET_KEY'] = os.urandom(24)

# Main layout
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    dcc.Store(id='session-store', storage_type='session'),
    html.Div(id='page-content')
])

# Routing callback
@app.callback(
    Output('page-content', 'children'),
    Input('url', 'pathname'),
    State('session-store', 'data')
)
def display_page(pathname, session_data):
    
    is_authenticated = session_data and session_data.get('authenticated', False)
    
    if pathname == '/login':
        page = login.layout
    elif pathname == '/register':
        page = register.layout
    elif pathname == '/account':
        if is_authenticated:
            page = account.layout
        else:
            page = login.layout
    elif pathname == '/settings':
        if is_authenticated:
            page = settings.layout
        else:
            page = login.layout
    else:
        page = home.layout

    try:
        if hasattr(page, 'children') and isinstance(page.children, (list, tuple)) and len(page.children) > 0:
            page.children[0] = create_navbar(is_authenticated)
    except Exception:
        pass

    return page

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=8050)