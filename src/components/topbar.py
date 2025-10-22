from dash import html, dcc, callback
import dash_bootstrap_components as dbc
import datetime


def TopBar(title, search_id=None, date_id=None, unit_id=None, add_button=None, extra_right=None, show_add=True, date_last=False):
    """
    Reusable top bar used above tables in pages.
    - title: string shown on left
    - search_id: id for the search input (optional)
    - date_id: id for the date input (optional)
    - unit_id: id for a Dropdown to choose unit/department (optional)
    - add_button: a dict {"id": "open-add-...", "label": "Thêm ..."} to render on the right
    - extra_right: optional list of components to place on the far right
    """
    left = html.Div(html.H3(title), className='topbar-left')

    center = html.Div([], className='topbar-center')

    right_children = []
    controls = []
    if search_id:
        controls.append(dbc.Input(id=search_id, placeholder='Tìm kiếm theo tên', type='text', className='topbar-search me-2'))
    if unit_id:
        controls.append(dcc.Dropdown(id=unit_id, options=[], placeholder='Chọn máy bơm', clearable=True, className='topbar-unit me-2'))

    date_control = None
    if date_id:
        today = str(datetime.date.today())
        prev_btn = dbc.Button(html.I(className='fas fa-chevron-left'), id=f'{date_id}-prev', color='light', size='sm', className='me-1')
        next_btn = dbc.Button(html.I(className='fas fa-chevron-right'), id=f'{date_id}-next', color='light', size='sm', className='ms-1')
        date_input = dbc.Input(id=date_id, type='date', value=today, className='topbar-date')
        date_control = html.Div([prev_btn, date_input, next_btn], className='d-flex align-items-center me-2')

    # assemble controls in desired order
    if date_last:
        # put date at end
        right_children.extend(controls)
        if date_control:
            right_children.append(date_control)
    else:
        # date earlier
        if date_control:
            right_children.append(date_control)
        right_children.extend(controls)

    # add button
    if show_add and add_button and isinstance(add_button, dict):
        right_children.append(dbc.Button(add_button.get('label', 'Thêm'), id=add_button.get('id'), color='primary'))
    if extra_right:
        right_children.extend(extra_right)

    right = html.Div(right_children, className='topbar-right d-flex align-items-center')

    bar = html.Div([left, center, right], className='topbar d-flex align-items-center justify-content-between')
    return bar
