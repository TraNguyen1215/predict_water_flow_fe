from dash import html, dcc
import dash_bootstrap_components as dbc

from components.navbar import create_navbar


layout = html.Div([
    create_navbar(is_authenticated=True),
    dbc.Container([
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5('Nạp chương trình cho ESP qua trình duyệt')),
                    dbc.CardBody([
                        dbc.Alert(
                            'Tính năng này hoạt động tốt nhất trên trình duyệt Chrome hoặc Edge mới nhất.',
                            color='info',
                            className='mb-4'
                        ),
                        html.Ol([
                            html.Li('Kết nối bo mạch ESP với máy tính bằng cáp USB dữ liệu.'),
                            html.Li('Nhấn "Kết nối thiết bị" ở khung bên phải và chọn cổng Serial tương ứng.'),
                            html.Li('Chọn tệp firmware (.bin), sau đó bấm "Bắt đầu nạp" để tiến hành.'),
                            html.Li('Theo dõi trạng thái nạp, đợi hoàn tất 100% rồi khởi động lại thiết bị.'),
                            html.Li('Nếu được yêu cầu, giữ nút BOOT trên bo mạch trong khi kết nối.')
                        ], className='esp-flash-steps'),
                        html.Div([
                            html.Img(src='/assets/img/setup_sensor.png', style={'maxWidth': '100%', 'height': 'auto', 'display': 'block', 'marginTop': '16px'}),
                            html.Small('Hình minh họa: kết nối và chuẩn bị cảm biến', className='text-muted d-block mt-2'),
                            html.Div([
                                html.A(
                                    'Tải firmware (.bin)',
                                    href='/assets/sketch_oct15a.ino.bin',
                                    download='sketch_oct15a.ino.bin',
                                    className='btn btn-primary btn-sm mt-2',
                                    target='_blank'
                                ),
                                html.Small('Nhấp để tải về và sử dụng', className='text-muted d-block mt-1')
                            ])
                        ]),
                        dbc.Alert(
                            'Hãy chuẩn bị sẵn tệp firmware (.bin) tương thích với bo mạch trước khi bắt đầu.',
                            color='secondary',
                            className='mt-3'
                        )
                    ])
                ]),
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(html.H6('Câu hỏi thường gặp')),
                        dbc.CardBody([
                            html.H6('1. Tôi cần chuẩn bị gì trước khi nạp?', className='fw-semibold'),
                            html.P('- Firmware định dạng .bin phù hợp với bo mạch ESP của bạn.'),
                            html.P('- Dây cáp USB dữ liệu (không phải chỉ sạc).'),
                            html.P('- Trình duyệt hỗ trợ Web Serial (Chrome, Edge, Opera).'),
                            html.H6('2. Sau khi nạp xong có cần làm gì thêm?', className='fw-semibold mt-3'),
                            html.P('Khởi động lại thiết bị hoặc nhấn nút reset, đảm bảo nguồn cấp ổn định trong suốt quá trình.'),
                            html.H6('3. Nếu quá trình nạp thất bại?', className='fw-semibold mt-3'),
                            html.Ul([
                                html.Li('Kiểm tra lại cáp USB và cổng kết nối.'),
                                html.Li('Đóng các ứng dụng đang sử dụng Serial (Arduino IDE, VS Code, ...).'),
                                html.Li('Đặt bo mạch vào chế độ bootloader (nhấn giữ nút BOOT nếu cần).'),
                                html.Li('Thử giảm baudrate hoặc dùng cáp khác.')
                            ])
                        ])
                    ])
                ], style={'marginTop': '20px'})
            ], lg=5, className='mb-4 h-100'),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5('Công cụ nạp ESP trực tiếp trên trình duyệt')),
                    dbc.CardBody([
                        html.Div([
                            html.Iframe(
                                src='https://espressif.github.io/esptool-js/',
                                style={'width': '100%', 'height': '800px', 'border': '0'},
                                title='esptool-js flasher',
                                allow='serial; usb; fullscreen'
                            ),
                            html.Div([
                                html.Small('Nếu iframe không hiển thị hoặc không cho phép truy cập Serial, mở trực tiếp:', className='text-muted d-block mt-2'),
                                html.A('Mở esptool-js trong tab mới', href='https://espressif.github.io/esptool-js/', target='_blank', rel='noopener')
                            ], className='mt-2')
                        ])
                    ])
                ])
            ], lg=7, className='mb-4 h-100')
        ]),
    ], fluid=True, className='esp-flash-container'),
    # Embedded esptool-js used via iframe; local flasher script removed in favor of upstream UI
], className='page-container')
