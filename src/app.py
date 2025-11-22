import dash
from dash import html, dcc, Input, Output, State
import dash_bootstrap_components as dbc
from flask import session
import os
from pages import home, login, register, account, settings, sensor, pump, pump_detail, sensor_data, documentation, predict_data, esp_flash
from pages.admin import *
from components.navbar import create_navbar
from components.footer import create_footer

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

server = app.server
server.config['SECRET_KEY'] = os.urandom(24)

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    dcc.Store(id='session-store', storage_type='session'),
    dcc.Store(id='pump-detail-store', storage_type='memory'),
    # Global store to hold the selected pump across pages (ensures callbacks targeting
    # `selected-pump-store` always find the component in the layout)
    dcc.Store(id='selected-pump-store', data={'ma_may_bom': None, 'ten_may_bom': None}),
    # Interval used to trigger initial pump selection on pages that expect it.
    # Placed in the root layout so callbacks referencing `initial-pump-select`
    # always find the component regardless of the current page.
    dcc.Interval(id='initial-pump-select', interval=500, max_intervals=1, n_intervals=0),
    dcc.Interval(id='token-check-interval', interval=30*1000, n_intervals=0),
    html.Div(id='page-content'),
    html.Div(id='app-footer', children=create_footer()),
    # Placeholder elements for callbacks that expect these ids to exist in the root layout
    html.Div(id='pump-control-result', style={'display': 'none'})
])

@app.callback(
    Output('page-content', 'children'),
    Input('url', 'pathname'),
    State('session-store', 'data')
)
def display_page(pathname, session_data):
    
    is_authenticated = session_data and session_data.get('authenticated', False)
    is_admin = session_data and session_data.get('is_admin', False)
    
    if pathname == '/login':
        page = login.layout
    elif pathname == '/register':
        page = register.layout
    elif pathname == '/' or pathname == '':
        if is_authenticated:
            if is_admin:
                page = admin.layout
            else:
                page = home.layout
        else:
            page = login.layout
    elif pathname == '/account':
        if is_authenticated:
            page = account.layout
        else:
            page = login.layout
    elif pathname == '/sensor':
        if is_authenticated and is_admin == False:
            page = sensor.layout
        else:
            page = login.layout
    elif pathname == '/pump':
        if is_authenticated and is_admin == False:
            page = pump.layout
        else:
            page = login.layout
    elif pathname and pathname.startswith('/pump/'):
        if is_authenticated and is_admin == False:
            page = pump_detail.layout
        else:
            page = login.layout
    # '/sensor_data' route removed to hide the sensor data page (access by direct URL is no longer served)
    elif pathname == '/predict_data':
        if is_authenticated and is_admin == False:
            page = predict_data.layout
        else:
            page = login.layout
    elif pathname == '/esp-flash':
        if is_authenticated and is_admin == False:
            page = esp_flash.layout
        else:
            page = login.layout
    elif pathname == '/documentation':
        page = documentation.layout
    elif pathname == '/admin/models':
        if is_authenticated and is_admin:
            page = admin_models.layout
        else:
            page = login.layout
    elif pathname == '/admin/firmware':
        if is_authenticated and is_admin:
            try:
                from pages.admin import admin_firmware
                page = admin_firmware.layout
            except Exception:
                page = admin.layout
        else:
            page = login.layout
    elif pathname == '/admin/sensor-types':
        if is_authenticated and is_admin:
            page = admin_sensor_types.layout
        else:
            page = login.layout
    elif pathname == '/admin/users':
        if is_authenticated and is_admin:
            page = admin_users.layout
        else:
            page = login.layout
    elif pathname == '/admin' or (pathname and pathname.startswith('/admin')):
        if is_authenticated and is_admin:
            page = admin.layout
        else:
            page = login.layout
    else:
        page = home.layout

    try:
        if is_authenticated and hasattr(page, 'children') and isinstance(page.children, (list, tuple)) and len(page.children) > 0:
            page.children[0] = create_navbar(is_authenticated, is_admin, current_path=pathname)
    except Exception:
        pass

    if pathname in ['/login', '/register']:
        return page

    return page

@app.callback(
    Output('app-footer', 'style'),
    Input('url', 'pathname')
)
def toggle_footer(pathname):
    if pathname in ['/login', '/register']:
        return {'display': 'none'}
    return {'display': 'block'}

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