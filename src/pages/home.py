from dash import html, dcc, callback, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from components.navbar import create_navbar

# Generate sample data
def generate_sample_data():
    dates = pd.date_range(start='2025-01-01', end='2025-10-16', freq='D')
    np.random.seed(42)
    flow_rate = 100 + np.cumsum(np.random.randn(len(dates)) * 2)
    pressure = 50 + np.cumsum(np.random.randn(len(dates)) * 0.5)
    temperature = 20 + 5 * np.sin(np.arange(len(dates)) * 2 * np.pi / 365)
    
    df = pd.DataFrame({
        'date': dates,
        'flow_rate': flow_rate,
        'pressure': pressure,
        'temperature': temperature
    })
    return df

df = generate_sample_data()

# Create layout
layout = html.Div([
    create_navbar(is_authenticated=False),
    
    dbc.Container([
        # Hero Section
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.H1("Hệ Thống Dự Đoán Lưu Lượng Nước", 
                           className="display-4 fw-bold text-primary mb-3"),
                    html.P("Giám sát và dự đoán lưu lượng nước thông minh với công nghệ AI",
                          className="lead text-muted mb-4"),
                    dbc.Button([
                        html.I(className="fas fa-chart-line me-2"),
                        "Bắt đầu ngay"
                    ], color="primary", size="lg", className="px-5 py-3 shadow", href="/login")
                ], className="hero-section text-center py-5")
            ], width=12)
        ], className="mb-5"),
        
        # Statistics Cards
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.I(className="fas fa-tint fa-3x text-primary mb-3"),
                            html.H3(f"{df['flow_rate'].iloc[-1]:.1f} L/s", className="mb-2"),
                            html.P("Lưu lượng hiện tại", className="text-muted mb-0")
                        ], className="text-center")
                    ])
                ], className="shadow-sm stat-card")
            ], md=3, sm=6, className="mb-4"),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.I(className="fas fa-gauge-high fa-3x text-success mb-3"),
                            html.H3(f"{df['pressure'].iloc[-1]:.1f} Bar", className="mb-2"),
                            html.P("Áp suất", className="text-muted mb-0")
                        ], className="text-center")
                    ])
                ], className="shadow-sm stat-card")
            ], md=3, sm=6, className="mb-4"),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.I(className="fas fa-temperature-half fa-3x text-warning mb-3"),
                            html.H3(f"{df['temperature'].iloc[-1]:.1f}°C", className="mb-2"),
                            html.P("Nhiệt độ", className="text-muted mb-0")
                        ], className="text-center")
                    ])
                ], className="shadow-sm stat-card")
            ], md=3, sm=6, className="mb-4"),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.I(className="fas fa-check-circle fa-3x text-info mb-3"),
                            html.H3("98.5%", className="mb-2"),
                            html.P("Độ chính xác", className="text-muted mb-0")
                        ], className="text-center")
                    ])
                ], className="shadow-sm stat-card")
            ], md=3, sm=6, className="mb-4"),
        ]),
        
        # Charts Section
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5([
                            html.I(className="fas fa-chart-area me-2"),
                            "Lưu Lượng Nước Theo Thời Gian"
                        ], className="mb-0")
                    ]),
                    dbc.CardBody([
                        dcc.Graph(
                            id='flow-rate-chart',
                            figure={
                                'data': [
                                    go.Scatter(
                                        x=df['date'],
                                        y=df['flow_rate'],
                                        mode='lines',
                                        name='Lưu lượng',
                                        line=dict(color='#1f77b4', width=3),
                                        fill='tozeroy',
                                        fillcolor='rgba(31, 119, 180, 0.2)'
                                    )
                                ],
                                'layout': go.Layout(
                                    xaxis={'title': 'Ngày', 'gridcolor': '#f0f0f0'},
                                    yaxis={'title': 'Lưu lượng (L/s)', 'gridcolor': '#f0f0f0'},
                                    hovermode='x unified',
                                    plot_bgcolor='white',
                                    paper_bgcolor='white',
                                    margin=dict(l=50, r=20, t=20, b=50)
                                )
                            },
                            config={'displayModeBar': False}
                        )
                    ])
                ], className="shadow-sm mb-4")
            ], md=8),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5([
                            html.I(className="fas fa-chart-pie me-2"),
                            "Phân Tích Dữ Liệu"
                        ], className="mb-0")
                    ]),
                    dbc.CardBody([
                        dcc.Graph(
                            id='distribution-chart',
                            figure={
                                'data': [
                                    go.Box(
                                        y=df['flow_rate'],
                                        name='Lưu lượng',
                                        marker=dict(color='#1f77b4'),
                                        boxmean='sd'
                                    )
                                ],
                                'layout': go.Layout(
                                    yaxis={'title': 'L/s', 'gridcolor': '#f0f0f0'},
                                    plot_bgcolor='white',
                                    paper_bgcolor='white',
                                    margin=dict(l=50, r=20, t=20, b=50),
                                    showlegend=False
                                )
                            },
                            config={'displayModeBar': False}
                        )
                    ])
                ], className="shadow-sm mb-4")
            ], md=4),
        ]),
        
        # Multi-parameter chart
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5([
                            html.I(className="fas fa-chart-line me-2"),
                            "Tổng Quan Các Thông Số"
                        ], className="mb-0")
                    ]),
                    dbc.CardBody([
                        dcc.Graph(
                            id='multi-param-chart',
                            figure={
                                'data': [
                                    go.Scatter(
                                        x=df['date'][-30:],
                                        y=df['flow_rate'][-30:],
                                        mode='lines+markers',
                                        name='Lưu lượng (L/s)',
                                        line=dict(color='#1f77b4', width=2),
                                        marker=dict(size=6)
                                    ),
                                    go.Scatter(
                                        x=df['date'][-30:],
                                        y=df['pressure'][-30:] * 2,
                                        mode='lines+markers',
                                        name='Áp suất (Bar x2)',
                                        line=dict(color='#2ca02c', width=2),
                                        marker=dict(size=6),
                                        yaxis='y2'
                                    ),
                                    go.Scatter(
                                        x=df['date'][-30:],
                                        y=df['temperature'][-30:] * 5,
                                        mode='lines+markers',
                                        name='Nhiệt độ (°C x5)',
                                        line=dict(color='#ff7f0e', width=2),
                                        marker=dict(size=6),
                                        yaxis='y3'
                                    )
                                ],
                                'layout': go.Layout(
                                    xaxis={'title': 'Ngày (30 ngày gần nhất)', 'gridcolor': '#f0f0f0'},
                                    yaxis={'title': 'Lưu lượng', 'gridcolor': '#f0f0f0'},
                                    yaxis2={'title': 'Áp suất', 'overlaying': 'y', 'side': 'right'},
                                    yaxis3={'title': 'Nhiệt độ', 'overlaying': 'y', 'side': 'right', 'position': 0.95},
                                    hovermode='x unified',
                                    plot_bgcolor='white',
                                    paper_bgcolor='white',
                                    margin=dict(l=50, r=100, t=20, b=50),
                                    legend=dict(
                                        orientation="h",
                                        yanchor="bottom",
                                        y=1.02,
                                        xanchor="right",
                                        x=1
                                    )
                                )
                            },
                            config={'displayModeBar': False}
                        )
                    ])
                ], className="shadow-sm mb-4")
            ], width=12)
        ]),
        
        # Features Section
        dbc.Row([
            dbc.Col([
                html.H2("Tính Năng Nổi Bật", className="text-center mb-5 mt-4")
            ], width=12)
        ]),
        
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.I(className="fas fa-brain fa-3x text-primary mb-3"),
                        html.H4("AI Dự Đoán", className="mb-3"),
                        html.P("Sử dụng machine learning để dự đoán lưu lượng nước chính xác",
                              className="text-muted")
                    ], className="text-center")
                ], className="shadow-sm feature-card h-100")
            ], md=4, className="mb-4"),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.I(className="fas fa-clock fa-3x text-success mb-3"),
                        html.H4("Realtime", className="mb-3"),
                        html.P("Giám sát dữ liệu theo thời gian thực với độ trễ tối thiểu",
                              className="text-muted")
                    ], className="text-center")
                ], className="shadow-sm feature-card h-100")
            ], md=4, className="mb-4"),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.I(className="fas fa-bell fa-3x text-warning mb-3"),
                        html.H4("Cảnh Báo", className="mb-3"),
                        html.P("Thông báo ngay khi phát hiện bất thường trong hệ thống",
                              className="text-muted")
                    ], className="text-center")
                ], className="shadow-sm feature-card h-100")
            ], md=4, className="mb-4"),
        ], className="mb-5"),
        
    ], fluid=True, className="px-4"),
    
    # Footer
    html.Footer([
        dbc.Container([
            dbc.Row([
                dbc.Col([
                    html.P("© 2025 Water Flow Predict. All rights reserved.",
                          className="text-center text-muted mb-0")
                ], width=12)
            ])
        ])
    ], className="py-4 bg-light mt-5")
], className="page-container")