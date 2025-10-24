from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc


def create_weather_widget():
    card = dbc.Card([
        dbc.CardBody([
            html.Div([
                dbc.Row([
                    dbc.Col([
                        html.Div([
                            html.Div([
                                html.I(className='fas fa-map-pin', style={'color': '#0358a3', 'fontSize': '1rem', 'marginRight': '0.4rem'}),
                                html.Span(id='weather-location', style={
                                    'fontSize': '0.9rem', 
                                    'fontWeight': '700', 
                                    'color': '#0358a3',
                                    'letterSpacing': '0.2px'
                                })
                            ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '0.3rem'}),
                            
                            html.Div(id='weather-localtime', style={
                                'fontSize': '0.75rem',
                                'color': '#64b5f6',
                                'marginBottom': '0.8rem',
                                'fontWeight': '500'
                            }),
                            
                            html.Div(id='weather-temp', style={
                                'fontSize': '2.4rem',
                                'fontWeight': '800',
                                'background': 'linear-gradient(135deg, #d32f2f 0%, #f57c00 100%)',
                                '-WebkitBackgroundClip': 'text',
                                '-WebkitTextFillColor': 'transparent',
                                'backgroundClip': 'text',
                                'lineHeight': '1',
                                'marginBottom': '0.2rem',
                                'letterSpacing': '-1px'
                            })
                        ])
                    ], md=3, sm=12, style={'paddingRight': '0.8rem', 'borderRight': '2px solid #e0eef7'}),

                    dbc.Col([
                        html.Div([
                            html.Div(id='weather-icon', className='weather-icon-large', style={
                                'backgroundColor': '#1e88e5',
                                'borderRadius': '12px',
                                'display': 'flex',
                                'alignItems': 'center',
                                'justifyContent': 'center',
                                'minHeight': '120px',
                                'marginBottom': '0.8rem'
                            }),
                            html.Div(id='weather-desc', style={
                                'fontSize': '0.8rem',
                                'fontWeight': '600',
                                'color': '#1a1a1a',
                                'textAlign': 'center',
                                'background': 'linear-gradient(135deg, #fff9c4 0%, #ffe082 100%)',
                                'padding': '0.5rem 0.4rem',
                                'borderRadius': '8px',
                                'lineHeight': '1.3',
                                'border': '1px solid #ffd54f',
                                'boxShadow': '0 2px 8px rgba(255, 214, 0, 0.1)'
                            })
                        ], style={'padding': '0 0.6rem', 'textAlign': 'center'})
                    ], md=5, sm=12),

                    dbc.Col([
                        html.Div([
                            html.Div([
                                html.I(className='fas fa-cloud-rain', style={'color': '#2196f3', 'fontSize': '0.95rem', 'width': '20px', 'textAlign': 'center', 'fontWeight': '600'}),
                                html.Span('Có thể mưa:', style={'fontSize': '0.75rem', 'color': '#64b5f6', 'minWidth': '60px', 'marginLeft': '0.4rem', 'fontWeight': '500'}),
                                html.Span(id='weather-sunrise', style={'fontSize': '0.75rem', 'fontWeight': '700', 'color': '#0358a3', 'marginLeft': 'auto'})
                            ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '0.5rem', 'padding': '0.4rem', 'background': 'rgba(33, 150, 243, 0.05)', 'borderRadius': '6px'}),

                            html.Div([
                                html.I(className='fas fa-wind', style={'color': '#00bcd4', 'fontSize': '0.95rem', 'width': '20px', 'textAlign': 'center', 'fontWeight': '600'}),
                                html.Span('Gió:', style={'fontSize': '0.75rem', 'color': '#64b5f6', 'minWidth': '60px', 'marginLeft': '0.4rem', 'fontWeight': '500'}),
                                html.Span(id='weather-sunset', style={'fontSize': '0.75rem', 'fontWeight': '700', 'color': '#0358a3', 'marginLeft': 'auto'})
                            ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '0.5rem', 'padding': '0.4rem', 'background': 'rgba(0, 188, 212, 0.05)', 'borderRadius': '6px'}),
                            
                            html.Div([
                                html.I(className='fas fa-droplet', style={'color': '#2196f3', 'fontSize': '0.95rem', 'width': '20px', 'textAlign': 'center', 'fontWeight': '600'}),
                                html.Span('Độ ẩm:', style={'fontSize': '0.75rem', 'color': '#64b5f6', 'minWidth': '60px', 'marginLeft': '0.4rem', 'fontWeight': '500'}),
                                html.Span(id='stat-humidity', style={'fontSize': '0.75rem', 'fontWeight': '700', 'color': '#0358a3', 'marginLeft': 'auto'})
                            ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '0.5rem', 'padding': '0.4rem', 'background': 'rgba(33, 150, 243, 0.05)', 'borderRadius': '6px'}),
                            
                            html.Div([
                                html.I(className='fas fa-gauge', style={'color': '#616161', 'fontSize': '0.95rem', 'width': '20px', 'textAlign': 'center', 'fontWeight': '600'}),
                                html.Span('Áp suất:', style={'fontSize': '0.75rem', 'color': '#64b5f6', 'minWidth': '60px', 'marginLeft': '0.4rem', 'fontWeight': '500'}),
                                html.Span(id='stat-pressure', style={'fontSize': '0.75rem', 'fontWeight': '700', 'color': '#0358a3', 'marginLeft': 'auto'})
                            ], style={'display': 'flex', 'alignItems': 'center', 'padding': '0.4rem', 'background': 'rgba(97, 97, 97, 0.05)', 'borderRadius': '6px'})
                        ], style={'fontSize': '0.75rem'})
                    ], md=4, sm=12, style={'paddingLeft': '0.8rem'})
                ], className='g-0', style={'marginBottom': '0.8rem'}),

                html.Div([
                    html.Div([
                        html.I(className='fas fa-chevron-down', id='forecast-icon', style={'marginRight': '0.4rem', 'transition': 'transform 0.3s ease', 'fontSize': '0.7rem', 'color': '#0358a3'}),
                        html.Span('Dự báo 7 ngày', style={
                            'fontSize': '0.85rem',
                            'fontWeight': '700',
                            'color': '#0358a3',
                            'cursor': 'pointer',
                            'userSelect': 'none'
                        })
                    ], id='toggle-forecast-btn', style={
                        'display': 'flex',
                        'alignItems': 'center',
                        'cursor': 'pointer',
                        'padding': '0.6rem 0',
                        'borderTop': '2px solid #e0eef7',
                        'paddingTop': '0.8rem',
                        'transition': 'color 0.2s ease'
                    })
                ]),

                html.Div(id='forecast-container', style={'display': 'none','width': 'calc(100% + 2.4rem)',
                    'marginLeft': '-1.2rem',
                    'marginRight': '-1.2rem',
                    'paddingLeft': '1.2rem',
                    'paddingRight': '1.2rem',
                    'marginTop': '0.8rem',
                    'borderTop': '2px solid #e0eef7',
                    'paddingTop': '0.8rem'}, children=[
                    html.Div(id='weather-forecast', className='weather-forecast', style={
                        'gap': '0.8rem',
                        'overflowX': 'auto',
                        'paddingBottom': '0.5rem',
                        'width': '100%'
                    })
                ]),

                html.Div(id='weather-updated', style={
                    'fontSize': '0.7rem',
                    'color': '#b0bec5',
                    'textAlign': 'right',
                    'marginTop': '0.8rem',
                    'fontStyle': 'italic'
                }),
                html.Pre(id='weather-raw', style={'display': 'none', 'whiteSpace': 'pre-wrap', 'wordBreak': 'break-word'})
            ])
        ], style={'padding': '1.2rem'})
    ], style={
        'border': 'none',
        'boxShadow': '0 8px 24px rgba(3, 88, 163, 0.12), 0 2px 4px rgba(0, 0, 0, 0.04)',
        'borderRadius': '12px',
        'backgroundColor': '#fff',
        'background': 'linear-gradient(135deg, #ffffff 0%, #f8fbff 100%)',
        'transition': 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)'
    })

    return html.Div([
        dcc.Store(id='weather-store'),
        html.Div(id='weather-container', children=[card], className='weather-widget-container', style={'margin-top': '10px'})
    ], className='weather-widget')


@callback(
    [
        Output('forecast-container', 'style'),
        Output('forecast-icon', 'className')
    ],
    [
        Input('toggle-forecast-btn', 'n_clicks')
    ],
    prevent_initial_call=True
)
def toggle_forecast(n_clicks):
    if n_clicks is None or n_clicks == 0:
        return {'display': 'none'}, 'fas fa-chevron-down'
    
    is_visible = n_clicks % 2 == 1
    display_style = 'flex' if is_visible else 'none'
    icon_class = 'fas fa-chevron-up' if is_visible else 'fas fa-chevron-down'
    
    return {'display': display_style, 'marginBottom': '0.8rem', 'borderTop': '2px solid #e0eef7', 'paddingTop': '0.8rem'}, icon_class
