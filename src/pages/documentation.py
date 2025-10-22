from dash import html, dcc
import dash_bootstrap_components as dbc
from components.navbar import create_navbar


layout = html.Div([
    create_navbar(is_authenticated=True),

    dbc.Container([
        dbc.Row([
            dbc.Col(html.H2("Tài liệu — Rau cải"), width=12)
        ], className="mb-4"),

        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5("Hướng dẫn dùng web")),
                    dbc.CardBody([
                        html.P("Trang web này dùng để giám sát và dự đoán lưu lượng nước, đồng thời quản lý cảm biến và máy bơm."),
                        html.Ol([
                            html.Li("Đăng nhập bằng tài khoản của bạn."),
                            html.Li("Xem trang 'Cảm biến' để quản lý thiết bị."),
                            html.Li("Trang 'Dữ liệu cảm biến' hiển thị lịch sử cảm biến và cho phép xuất dữ liệu."),
                            html.Li("Trang 'Máy bơm' để bật/tắt và kiểm soát cài đặt máy bơm."),
                            html.Li("Trang này ('Tài liệu') là chỉ đọc — cung cấp hướng dẫn chuyên môn về trồng rau cải và các thông số liên quan.")
                        ])
                    ])
                ], className="mb-4 shadow-sm")
            ], width=12)
        ]),

        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5("Giới thiệu về rau cải")),
                    dbc.CardBody([
                        html.P("Rau cải (ví dụ: cải bó xôi, cải ngọt, cải thìa) là nhóm rau lá có giá trị dinh dưỡng cao, phát triển nhanh và phù hợp trồng theo luống hoặc thủy canh."),
                        html.P("Mục tiêu tài liệu: mô tả các chỉ số môi trường quan trọng, kỹ thuật nuôi trồng, và cách thời tiết ảnh hưởng đến sinh trưởng rau cải.")
                    ])
                ], className="mb-4 shadow-sm")
            ], width=12)
        ]),

        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5("Các chỉ số quan trọng")),
                    dbc.CardBody([
                        html.Ul([
                            html.Li([html.B("Độ ẩm đất:"), "  Rau cải ưa ẩm nhưng không ngập úng. Độ ẩm đất tối ưu: 60–80% (tùy loại đất)." ]),
                            html.Li([html.B("Nhiệt độ:"), "  Nhiệt độ sinh trưởng tốt: 15–25°C. Nhiệt độ <10°C hoặc >30°C gây stress." ]),
                            html.Li([html.B("Độ ẩm không khí:"), "  50–80% phù hợp; độ ẩm quá thấp tăng nguy cơ rụng và bệnh hại do sâu bệnh." ]),
                            html.Li([html.B("pH đất:"), "  pH tối ưu: 6.0–7.0. Điều chỉnh bằng vôi (tăng) hoặc lưu huỳnh (giảm) khi cần." ]),
                            html.Li([html.B("Ánh sáng:"), "  Rau cải cần ánh sáng vừa đủ; 10–14 giờ/ngày cho năng suất tốt. Trong nhà kính hoặc thủy canh có thể dùng đèn LED bổ sung." ]),
                            html.Li([html.B("Dinhn dưỡng (N-P-K):"), "  Rau lá cần nhiều Nitơ (N) để phát triển lá xanh. Liều lượng và lịch bón phụ thuộc vào phương pháp trồng (đất/nhà kính/thủy canh)." ]),
                            html.Li([html.B("Lưu lượng nước/tiêu thụ:"), "  Theo dõi lưu lượng tưới để tránh thiếu/đẫm nước. Hệ thống tưới tự động nên đặt lịch theo giai đoạn sinh trưởng." ]),
                        ])
                    ])
                ], className="mb-4 shadow-sm")
            ], width=12)
        ]),

        dbc.Row([
            dbc.Col(md=6, children=[
                dbc.Card([
                    dbc.CardHeader(html.H5("Hướng dẫn nuôi trồng (Tại ruộng)")),
                    dbc.CardBody([
                        html.Ol([
                            html.Li("Chuẩn bị luống: đất tơi xốp, bón phân nền phù hợp (phân hữu cơ + phân cân đối)."),
                            html.Li("Gieo: mật độ gieo tùy giống; thường gieo thành hàng, sau này tỉa để đạt khoảng cách 15–25 cm tùy loại."),
                            html.Li("Tưới: giữ ẩm đều, hạn chế ngập úng. Tưới sáng sớm hoặc chiều mát."),
                            html.Li("Bón thúc: ưu tiên phân có N để tăng sinh khối lá; tránh bón thừa gây cháy rễ."),
                            html.Li("Phòng trừ sâu bệnh: luân canh, sử dụng bẫy sinh học, kiểm tra lá định kỳ."),
                        ])
                    ])
                ], className="mb-4 shadow-sm")
            ]),

            dbc.Col(md=6, children=[
                dbc.Card([
                    dbc.CardHeader(html.H5("Hướng dẫn nuôi trồng (Thủy canh/NFT)")),
                    dbc.CardBody([
                        html.Ol([
                            html.Li("Dung dịch dinh dưỡng: sử dụng công thức dành cho rau lá; kiểm tra EC và pH thường xuyên."),
                            html.Li("pH dung dịch: duy trì 5.8–6.5 cho hấp thụ dinh dưỡng tối ưu."),
                            html.Li("EC: điều chỉnh theo giai đoạn; tránh EC quá cao gây thừa muối."),
                            html.Li("Tốc độ dòng và tuần hoàn: đảm bảo rễ luôn có oxy; thay dung dịch định kỳ để tránh tích tụ chất thải."),
                            html.Li("Ánh sáng và nhiệt độ trong nhà kính: kiểm soát để giữ trong khoảng sinh trưởng tối ưu."),
                        ])
                    ])
                ], className="mb-4 shadow-sm")
            ])
        ], className="mb-4"),

        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5("Ảnh hưởng của thời tiết")),
                    dbc.CardBody([
                        html.P("Thời tiết là yếu tố quyết định đối với rau cải. Dưới đây là các tác động chính và cách giảm nhẹ:"),
                        html.Ul([
                            html.Li([html.B("Mưa nhiều:"), "  Ngập úng, rễ thiếu oxy => cần hệ rãnh thoát nước hoặc nâng luống."]),
                            html.Li([html.B("Nắng nóng kéo dài:"), "  Làm giảm sinh trưởng, lá bị cháy; nên che nắng hoặc tưới mát. "]),
                            html.Li([html.B("Sương giá/đông lạnh:"), "  Gây tổn thương mô lá; cần che phủ hoặc sưởi ấm cho nhà kính. "]),
                            html.Li([html.B("Độ ẩm cao:"), "  Tăng nguy cơ bệnh nấm; cần thoáng khí, hạn chế tưới lá vào chiều tối."]),
                        ])
                    ])
                ], className="mb-4 shadow-sm")
            ], width=12)
        ]),

        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5("Tích hợp với hệ thống giám sát")),
                    dbc.CardBody([
                        html.P("Gợi ý cách dùng dữ liệu hệ thống để tối ưu trồng rau cải:"),
                        html.Ul([
                            html.Li("Sử dụng cảm biến độ ẩm đất để bật/tắt hệ thống tưới tự động; tránh tưới theo giờ cứng."),
                            html.Li("Theo dõi nhiệt độ và dự báo thời tiết để điều chỉnh che phủ và lịch tưới."),
                            html.Li("Giữ lịch sử dữ liệu để phân tích năng suất liên quan đến thông số môi trường."),
                        ])
                    ])
                ], className="mb-4 shadow-sm")
            ], width=12)
        ]),

        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5("Tài liệu tham khảo & nguồn hữu ích")),
                    dbc.CardBody([
                        html.Ul([
                            html.Li(html.A("FAO - Production and Protection: Leafy Vegetables", href="#", target="_blank")),
                            html.Li(html.A("Research articles on leafy vegetable cultivation (local extension services)", href="#", target="_blank")),
                        ])
                    ])
                ], className="mb-4 shadow-sm")
            ], width=12)
        ])

    ], fluid=True, className="px-4"),

    html.Footer([
        dbc.Container([
            dbc.Row([
                dbc.Col(html.P("© 2025 Dự Đoán Lưu Lượng Nước — Tài liệu chỉ đọc", className="text-center mb-0"), width=12)
            ])
        ])
    ], className="py-4 mt-5", style={"background-color": "#023E73"})
], className="page-container")
