from typing import Tuple, Dict, Any, List, Optional
import os
import requests

URL_API_BASE = os.environ.get('URL_API_BASE', 'http://127.0.0.1:8000/api/v1')


def _url(path: str) -> str:
    return URL_API_BASE.rstrip('/') + '/' + path.lstrip('/')


def list_users(token: Optional[str] = None, params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    """Lấy danh sách người dùng từ backend. Trả về list các dict (rỗng khi lỗi)."""
    try:
        headers = {}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        resp = requests.get(_url('nguoi-dung'), timeout=5, headers=headers, params=params)
        if resp.status_code == 200 and resp.content:
            data = resp.json()
            # Nếu API trả về {"data": [...]}
            if isinstance(data, dict) and 'data' in data and isinstance(data['data'], list):
                return data['data']
            if isinstance(data, list):
                return data
        return []
    except requests.RequestException:
        return []


def get_user(ma_nguoi_dung: str, token: Optional[str] = None) -> Dict[str, Any]:
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


def create_user(user_data: Dict[str, Any], token: Optional[str] = None) -> Tuple[bool, str]:
    try:
        headers = {}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        resp = requests.post(_url('nguoi-dung'), json=user_data, timeout=5, headers=headers)
        data = resp.json() if resp.content else {}
        if resp.status_code in (200, 201):
            return True, data.get('message', 'Tạo người dùng thành công')
        return False, data.get('message', data.get('error', 'Tạo người dùng thất bại'))
    except requests.RequestException as e:
        return False, f'Lỗi kết nối tới server: {e}'


def update_user(ma_nguoi_dung: str, user_data: Dict[str, Any], token: Optional[str] = None) -> Tuple[bool, str]:
    try:
        headers = {}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        resp = requests.put(_url(f'nguoi-dung/{ma_nguoi_dung}'), json=user_data, timeout=5, headers=headers)
        data = resp.json() if resp.content else {}
        if resp.status_code in (200, 204):
            return True, data.get('message', 'Cập nhật người dùng thành công')
        return False, data.get('message', data.get('error', 'Cập nhật người dùng thất bại'))
    except requests.RequestException as e:
        return False, f'Lỗi kết nối tới server: {e}'


def delete_user(ma_nguoi_dung: str, token: Optional[str] = None) -> Tuple[bool, str]:
    try:
        headers = {}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        resp = requests.delete(_url(f'nguoi-dung/{ma_nguoi_dung}'), timeout=5, headers=headers)
        data = resp.json() if resp.content else {}
        if resp.status_code in (200, 204):
            return True, data.get('message', 'Xóa người dùng thành công')
        return False, data.get('message', data.get('error', 'Xóa người dùng thất bại'))
    except requests.RequestException as e:
        return False, f'Lỗi kết nối tới server: {e}'
