from dash import html, dcc, callback
import dash_bootstrap_components as dbc
import datetime


def TopBar(title, search_id=None, date_id=None, unit_id=None, add_button=None, extra_right=None, extra_left=None, show_add=True, date_last=False):
    left_children = []
    if search_id:
        left_children.append(html.Div([
            html.I(className='fas fa-search topbar-search-icon'),
            dbc.Input(id=search_id, placeholder='Tìm kiếm theo tên', type='text', className='topbar-search topbar-search--slim')
        ], className='topbar-search-wrapper me-2'))

    if unit_id:
        left_children.append(dcc.Dropdown(id=unit_id, options=[], placeholder='Chọn máy bơm', clearable=True, className='topbar-unit me-2'))

    if extra_left:
        if not isinstance(extra_left, (list, tuple)):
            left_children.append(extra_left)
        else:
            left_children.extend(extra_left)

    left = html.Div(left_children, className='topbar-left d-flex align-items-center')

    center = html.Div([], className='topbar-center')

    right_children = []
    controls = []

    date_control = None
    if date_id:
        today = str(datetime.date.today())
        prev_btn = dbc.Button(html.I(className='fas fa-chevron-left'), id=f'{date_id}-prev', color='light', size='sm', className='me-1 topbar-date-btn')
        next_btn = dbc.Button(html.I(className='fas fa-chevron-right'), id=f'{date_id}-next', color='light', size='sm', className='ms-1 topbar-date-btn')
        date_input = dbc.Input(id=date_id, type='date', value=today, max=today, className='topbar-date')
        date_control = html.Div([prev_btn, date_input, next_btn], className='d-flex align-items-center me-2')

    if date_last:
        right_children.extend(controls)
        if date_control:
            right_children.append(date_control)
    else:
        if date_control:
            right_children.append(date_control)
        right_children.extend(controls)

    if show_add and add_button and isinstance(add_button, dict):
        add_label = add_button.get('label', 'Thêm')
        add_btn = dbc.Button([html.I(className='fas fa-plus me-2'), add_label], id=add_button.get('id'), color='primary', className='btn-add')
        right_children.append(add_btn)
    if extra_right:
        right_children.extend(extra_right)

    right = html.Div(right_children, className='topbar-right d-flex align-items-center')

    bar = html.Div([left, center, right], className='topbar d-flex align-items-center justify-content-between')
    return bar
