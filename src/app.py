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
    dcc.Interval(id='token-check-interval', interval=30*1000, n_intervals=0),
    html.Div(id='page-content')
])

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
    elif pathname == '/' or pathname == '':
        if is_authenticated:
            page = home.layout
        else:
            page = login.layout
    elif pathname == '/account':
        if is_authenticated:
            page = account.layout
        else:
            page = login.layout
    # elif pathname == '/settings':
    #     if is_authenticated:
    #         page = settings.layout
    #     else:
    #         page = login.layout
    else:
        page = home.layout

    try:
        if is_authenticated and hasattr(page, 'children') and isinstance(page.children, (list, tuple)) and len(page.children) > 0:
            page.children[0] = create_navbar(is_authenticated)
    except Exception:
        pass

    return page

@app.callback(
    [Output('session-store', 'data', allow_duplicate=True), Output('url', 'pathname', allow_duplicate=True)],
    Input('token-check-interval', 'n_intervals'),
    State('session-store', 'data'),
    prevent_initial_call='initial_duplicate'
)
def check_token_expiry(n_intervals, session_data):
    from api.auth import is_token_expired

    if not session_data or not isinstance(session_data, dict):
        return dash.no_update, dash.no_update

    token = session_data.get('token')
    if not token:
        return dash.no_update, dash.no_update

    if is_token_expired(token):
        return {}, '/login'

    return dash.no_update, dash.no_update


@app.callback(
    [Output('session-store', 'data', allow_duplicate=True), Output('url', 'pathname', allow_duplicate=True)],
    Input('url', 'pathname'),
    prevent_initial_call=True
)
def handle_logout(pathname):
    if pathname == '/logout':
        return {}, '/login'
    return dash.no_update, dash.no_update

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=8050)