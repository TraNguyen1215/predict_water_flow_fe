from typing import Tuple, Dict, Any, Optional
import os
import requests
import time
import base64
import json

URL_API_BASE = os.environ.get('URL_API_BASE', 'http://127.0.0.1:8000/api/v1')


def _url(path: str) -> str:
    return URL_API_BASE.rstrip('/') + '/' + path.lstrip('/')


def register_user(username: str, name: str, password: str) -> Tuple[bool, str]:
    """Đăng ký người dùng mới qua API backend.

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


def authenticate_user(username: str, password: str) -> Tuple[bool, str, Optional[str], Optional[float]]:
    """ Đăng nhập người dùng qua API backend.
    Trả về (success, message, token, token_exp).
    token_exp là thời điểm hết hạn của token dưới dạng dấu thời gian unix (giây) nếu có.
    """
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

            token_exp = None
            if isinstance(data, dict):
                if 'exp' in data and isinstance(data['exp'], (int, float)):
                    token_exp = float(data['exp'])
                elif 'expires_at' in data:
                    try:
                        token_exp = float(data['expires_at'])
                    except Exception:
                        token_exp = None
                elif 'expires_in' in data:
                    try:
                        token_exp = time.time() + float(data['expires_in'])
                    except Exception:
                        token_exp = None
                elif data.get('data') and isinstance(data['data'], dict):
                    d = data['data']
                    if 'exp' in d and isinstance(d['exp'], (int, float)):
                        token_exp = float(d['exp'])
                    elif 'expires_at' in d:
                        try:
                            token_exp = float(d['expires_at'])
                        except Exception:
                            token_exp = None
                    elif 'expires_in' in d:
                        try:
                            token_exp = time.time() + float(d['expires_in'])
                        except Exception:
                            token_exp = None

            if not token_exp and token:
                try:
                    parts = token.split('.')
                    if len(parts) >= 2:
                        payload_b64 = parts[1]
                        padding = '=' * (-len(payload_b64) % 4)
                        payload_bytes = base64.urlsafe_b64decode(payload_b64 + padding)
                        payload = json.loads(payload_bytes.decode('utf-8'))
                        exp = payload.get('exp')
                        if exp:
                            token_exp = float(exp)
                except Exception:
                    token_exp = None

            return True, data.get('message', 'Đăng nhập thành công'), token, token_exp
        else:
            return False, data.get('message', data.get('error', 'Đăng nhập thất bại')), None, None
    except requests.RequestException as e:
        return False, f'Lỗi kết nối tới server: {e}', None, None


def get_user_info(ma_nguoi_dung: str, token: Optional[str] = None) -> Dict[str, Any]:
    """Lấy thông tin người dùng

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
    """Cập nhật thông tin người dùng qua API backend.

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
    """Đổi mật khẩu người dùng qua API backend.

    """
    try:
        headers = {}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        resp = requests.post(_url('auth/doi-mat-khau'), json={
            'mat_khau_cu': current_password,
            'mat_khau_moi': new_password,
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


def forgot_password_verify(ten_dang_nhap: str, ten_may_bom: str, ngay_tuoi_gan_nhat: str) -> Tuple[bool, str]:
    """Verify identity before allowing password reset.

    """
    try:
        resp = requests.post(_url('auth/quen-mat-khau/verify'), json={
            'ten_dang_nhap': ten_dang_nhap,
            'ten_may_bom': ten_may_bom,
            'ngay_tuoi_gan_nhat': ngay_tuoi_gan_nhat,
        }, timeout=5)
        data = resp.json() if resp.content else {}
        if resp.status_code == 200:
            return True, data.get('message', 'Xác thực thành công')
        return False, data.get('message', data.get('error', 'Xác thực thất bại'))
    except requests.RequestException as e:
        return False, f'Lỗi kết nối tới server: {e}'


def forgot_password_reset(ten_dang_nhap: str, mat_khau_moi: str) -> Tuple[bool, str]:
    """Reset password after successful verification.

    """
    try:
        resp = requests.post(_url('auth/quen-mat-khau/reset'), json={
            'ten_dang_nhap': ten_dang_nhap,
            'mat_khau_moi': mat_khau_moi,
        }, timeout=5)
        data = resp.json() if resp.content else {}
        if resp.status_code == 200:
            return True, data.get('message', 'Đặt lại mật khẩu thành công')
        return False, data.get('message', data.get('error', 'Đặt lại mật khẩu thất bại'))
    except requests.RequestException as e:
        return False, f'Lỗi kết nối tới server: {e}'


def is_token_expired(token: Optional[str]) -> bool:
    """Kiểm tra xem token JWT có hết hạn hay không.
    """
    if not token:
        return True

    try:
        parts = token.split('.')
        if len(parts) < 2:
            return True
        payload_b64 = parts[1]
        padding = '=' * (-len(payload_b64) % 4)
        payload_bytes = base64.urlsafe_b64decode(payload_b64 + padding)
        payload = json.loads(payload_bytes.decode('utf-8'))
        exp = payload.get('exp')
        if not exp:
            return True
        return time.time() > float(exp)
    except Exception:
        return True

