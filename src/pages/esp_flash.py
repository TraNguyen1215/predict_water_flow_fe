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
                        dbc.Alert(
                            'Hãy chuẩn bị sẵn tệp firmware (.bin) tương thích với bo mạch trước khi bắt đầu.',
                            color='secondary',
                            className='mt-3'
                        )
                    ])
                ])
            ], lg=5, className='mb-4'),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5('Công cụ nạp ESP trực tiếp trên trình duyệt')),
                    dbc.CardBody([
                        html.Div(id='esp-flasher-root', children=[
                            html.P(
                                'Trình duyệt này sử dụng Web Serial để giao tiếp trực tiếp với bo mạch. Vui lòng dùng Chrome, Edge hoặc trình duyệt tương thích.',
                                className='text-muted'
                            ),
                            dbc.Alert(
                                'Trình duyệt sẽ yêu cầu quyền truy cập thiết bị USB/Serial. Chỉ cấp quyền cho thiết bị bạn tin tưởng.',
                                color='warning',
                                className='esp-browser-note'
                            ),
                            html.Div([
                                dbc.Button('Kết nối thiết bị', id='esp-connect-btn', color='primary', className='me-2 mb-2'),
                                dbc.Button('Ngắt kết nối', id='esp-disconnect-btn', color='secondary', outline=True, className='me-2 mb-2', disabled=True)
                            ], className='esp-actions'),
                            html.Div([
                                html.Label('Chọn firmware (.bin)', htmlFor='esp-firmware-input', className='form-label fw-semibold'),
                                dcc.Upload(
                                    id='esp-firmware-input',
                                    accept='.bin',
                                    multiple=False,
                                    className='esp-upload form-control text-center',
                                    children=html.Div([
                                        html.Span('Kéo thả hoặc bấm để chọn tệp firmware (.bin)', className='small text-muted')
                                    ])
                                ),
                                html.Small('Hoặc:', className='text-muted d-block mt-2'),
                                dbc.Button('Tải firmware từ assets', id='esp-load-from-assets-btn', color='info', outline=True, size='sm', className='mt-2 mb-2'),
                                html.Small('Sau khi chọn tệp, hãy kết nối thiết bị rồi bấm "Bắt đầu nạp".', className='text-muted d-block mt-2'),
                                html.Div(id='esp-firmware-selected', className='text-muted small mt-1')
                            ], className='mt-3'),
                            html.Div([
                                html.Div([
                                    html.Label('Địa chỉ bắt đầu (hex)', htmlFor='esp-start-address', className='form-label fw-semibold'),
                                    dcc.Input(
                                        id='esp-start-address',
                                        type='text',
                                        value='0x1000',
                                        className='form-control form-control-sm',
                                        placeholder='Ví dụ: 0x1000'
                                    )
                                ], className='col-12 col-md-6'),
                                html.Div([
                                    html.Div([
                                        dbc.Checkbox(
                                            id='esp-erase-checkbox',
                                            value=False,
                                            className='form-check-input'
                                        ),
                                        html.Label('Xóa toàn bộ flash trước khi nạp', htmlFor='esp-erase-checkbox', className='form-check-label ms-2')
                                    ], className='form-check form-switch mt-4 mt-md-0')
                                ], className='col-12 col-md-6')
                            ], className='row g-3 align-items-center mt-2'),
                            dbc.Button('Bắt đầu nạp', id='esp-flash-btn', color='success', className='mt-3', disabled=True),
                            html.Div([
                                html.Div(className='esp-progress-bar', children=[
                                    html.Div(id='esp-progress-inner', className='esp-progress-bar-inner')
                                ]),
                                html.Div(id='esp-progress-label', className='esp-progress-label text-muted mt-2')
                            ], className='mt-3'),
                            html.Div(id='esp-status', className='esp-status mt-3'),
                            html.Pre(id='esp-log', className='esp-log mt-3')
                        ])
                    ])
                ])
            ], lg=7, className='mb-4')
        ]),
        dbc.Row([
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
            ])
        ], className='mt-4')
    ], fluid=True, className='esp-flash-container'),
    html.Script(src='/assets/js/esp_flasher.js', type='module', defer=True),
    html.Script("""
    (function(){
      function attempt(i){
        if (window.initializeEspFlasher){
          window.initializeEspFlasher();
        } else if (i < 50){
          setTimeout(function(){ attempt(i+1); }, 200);
        } else {
          console.error('Không thể khởi tạo ESP Flasher sau 50 lần thử');
        }
      }
      attempt(0);
    })();
    """, type='text/javascript')
], className='page-container')
