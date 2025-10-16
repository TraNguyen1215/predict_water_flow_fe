# 🌊 Water Flow Predict - Frontend

Hệ thống dự đoán lưu lượng nước thông minh sử dụng Dash Python với giao diện đẹp mắt và hiện đại.

## ✨ Tính năng

- 🏠 **Trang chủ**: Hiển thị biểu đồ và thống kê lưu lượng nước
- 🔐 **Đăng nhập/Đăng ký**: Quản lý tài khoản người dùng
- 👤 **Trang tài khoản**: Cập nhật thông tin cá nhân
- ⚙️ **Trang cài đặt**: Tùy chỉnh thông báo, bảo mật, giao diện, dữ liệu
- 📊 **Biểu đồ thời gian thực**: Hiển thị dữ liệu bằng Plotly
- 🎨 **Giao diện đẹp**: Responsive, hiện đại với Bootstrap

## 🚀 Cài đặt

### Yêu cầu

- Python 3.8+
- pip

### Các bước cài đặt

1. **Clone repository**
```bash
git clone https://github.com/TraNguyen1215/predict_water_flow_fe.git
cd predict_water_flow_fe
```

2. **Tạo môi trường ảo (khuyến nghị)**
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

3. **Cài đặt dependencies**
```bash
pip install -r requirements.txt
```

## 🎯 Chạy ứng dụng

```bash
cd src
python app.py
```

Mở trình duyệt và truy cập: `http://localhost:8050`

## 📁 Cấu trúc thư mục

```
predict_water_flow_fe/
│
├── src/
│   ├── app.py                 # File chính
│   ├── assets/
│   │   └── styles.css        # CSS tùy chỉnh
│   ├── components/
│   │   ├── __init__.py
│   │   └── navbar.py         # Component navbar
│   ├── pages/
│   │   ├── __init__.py
│   │   ├── home.py           # Trang chủ
│   │   ├── login.py          # Trang đăng nhập
│   │   ├── register.py       # Trang đăng ký
│   │   ├── account.py        # Trang tài khoản
│   │   └── settings.py       # Trang cài đặt
│   ├── utils/
│   │   ├── __init__.py
│   │   └── auth.py           # Xác thực người dùng
│   └── data/
│       └── users.json        # Dữ liệu người dùng (tự động tạo)
│
├── requirements.txt
└── README.md
```

## 🔧 Công nghệ sử dụng

- **Dash**: Framework web Python
- **Dash Bootstrap Components**: Giao diện Bootstrap
- **Plotly**: Biểu đồ tương tác
- **Pandas**: Xử lý dữ liệu
- **Font Awesome**: Icons đẹp

## 📱 Các trang

### 1. Trang chủ (`/`)
- Hiển thị thống kê tổng quan
- Biểu đồ lưu lượng nước theo thời gian
- Phân tích dữ liệu
- Tổng quan các thông số

### 2. Đăng nhập (`/login`)
- Form đăng nhập
- Xác thực người dùng
- Chuyển hướng sau khi đăng nhập

### 3. Đăng ký (`/register`)
- Form đăng ký tài khoản mới
- Xác thực dữ liệu đầu vào
- Tạo tài khoản mới

### 4. Tài khoản (`/account`)
- Hiển thị thông tin người dùng
- Cập nhật thông tin cá nhân
- Thống kê hoạt động

### 5. Cài đặt (`/settings`)
- Cài đặt thông báo
- Cài đặt bảo mật
- Cài đặt giao diện
- Cài đặt dữ liệu

## 🎨 Tùy chỉnh

### Thay đổi màu sắc

Chỉnh sửa file `src/assets/styles.css`:

```css
:root {
    --primary-color: #0d6efd;  /* Màu chính */
    --secondary-color: #6c757d; /* Màu phụ */
    /* ... */
}
```

### Thêm trang mới

1. Tạo file trong `src/pages/`
2. Import trong `src/pages/__init__.py`
3. Thêm route trong `src/app.py`

## 🔐 Xác thực

- Mật khẩu được hash bằng SHA256
- Dữ liệu lưu trong `data/users.json`
- Session management với Flask

## 📊 Dữ liệu mẫu

Ứng dụng tự động tạo dữ liệu mẫu để demo:
- Lưu lượng nước (L/s)
- Áp suất (Bar)
- Nhiệt độ (°C)

## 🤝 Đóng góp

Mọi đóng góp đều được hoan nghênh! Vui lòng tạo issue hoặc pull request.

## 📝 License

MIT License

## 👨‍💻 Tác giả

TraNguyen1215

## 📞 Liên hệ

- GitHub: [@TraNguyen1215](https://github.com/TraNguyen1215)
- Repository: [predict_water_flow_fe](https://github.com/TraNguyen1215/predict_water_flow_fe)

---

⭐ Nếu thấy hữu ích, hãy cho dự án một ngôi sao!
