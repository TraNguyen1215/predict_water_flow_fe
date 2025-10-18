from typing import Tuple, Dict, Any, Optional
import os
import requests

URL_API_BASE = os.environ.get('URL_API_BASE', 'http://127.0.0.1:8000/api/v1')


def _url(path: str) -> str:
    return URL_API_BASE.rstrip('/') + '/' + path.lstrip('/')


def register_user(username: str, name: str, password: str) -> Tuple[bool, str]:
    """Register a new user via backend API.

    """
    try:
        resp = requests.post(_url('auth/dang-ky'), json={
            'ten_dang_nhap': username,
            'ho_ten': name,
            'mat_khau': password,
        }, timeout=5)
        data = resp.json() if resp.content else {}
        if resp.status_code in (200, 201):
            return True, data.get('message', 'Đăng ký thành công')
        else:
            return False, data.get('message', data.get('error', 'Đăng ký thất bại'))
    except requests.RequestException as e:
        return False, f'Lỗi kết nối tới server: {e}'


def authenticate_user(username: str, password: str) -> Tuple[bool, str, Optional[str]]:
    """Authenticate user against backend API. Returns (success, message, token)."""
    try:
        resp = requests.post(_url('auth/dang-nhap'), json={
            'ten_dang_nhap': username,
            'mat_khau': password,
        }, timeout=5)
        data = resp.json() if resp.content else {}
        if resp.status_code == 200:
            token = (
                data.get('access_token') or data.get('token') or data.get('jwt') or
                data.get('accessToken') or (data.get('data') and data['data'].get('token'))
            )
            return True, data.get('message', 'Đăng nhập thành công'), token
        else:
            return False, data.get('message', data.get('error', 'Đăng nhập thất bại')), None
    except requests.RequestException as e:
        return False, f'Lỗi kết nối tới server: {e}', None


def get_user_info(ma_nguoi_dung: str, token: Optional[str] = None) -> Dict[str, Any]:
    """Get user information from backend API. Returns dict or empty dict.

    """
    try:
        headers = {}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        resp = requests.get(_url(f'nguoi-dung/{ma_nguoi_dung}'), timeout=5, headers=headers)
        if resp.status_code == 200 and resp.content:
            return resp.json()
        return {}
    except requests.RequestException:
        return {}


def update_user_info(ma_nguoi_dung: str, user_data: Dict[str, Any], token: Optional[str] = None) -> Tuple[bool, str]:
    """Update user information via backend API.

    """
    try:
        headers = {}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        resp = requests.put(_url(f'nguoi-dung/{ma_nguoi_dung}'), json=user_data, timeout=5, headers=headers)
        data = resp.json() if resp.content else {}
        if resp.status_code in (200, 204):
            return True, data.get('message', 'Cập nhật thành công')
        return False, data.get('message', data.get('error', 'Cập nhật thất bại'))
    except requests.RequestException as e:
        return False, f'Lỗi kết nối tới server: {e}'


def change_password(current_password: str, new_password: str, token: Optional[str] = None) -> Tuple[bool, str]:
    """Change user's password via backend API.

    """
    try:
        headers = {}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        resp = requests.post(_url('auth/doi-mat-khau'), json={
            'current_password': current_password,
            'new_password': new_password,
        }, timeout=5, headers=headers)
        data = resp.json() if resp.content else {}
        if resp.status_code == 200:
            return True, data.get('message', 'Đổi mật khẩu thành công')
        return False, data.get('message', data.get('error', 'Đổi mật khẩu thất bại'))
    except requests.RequestException as e:
        return False, f'Lỗi kết nối tới server: {e}'


def forgot_password(email: str) -> Tuple[bool, str]:
    """Request password reset via backend API (forgot password).

    """
    try:
        resp = requests.post(_url('auth/quen-mat-khau'), json={'email': email}, timeout=5)
        data = resp.json() if resp.content else {}
        if resp.status_code == 200:
            return True, data.get('message', 'Yêu cầu đặt lại mật khẩu đã được gửi')
        return False, data.get('message', data.get('error', 'Yêu cầu thất bại'))
    except requests.RequestException as e:
        return False, f'Lỗi kết nối tới server: {e}'

