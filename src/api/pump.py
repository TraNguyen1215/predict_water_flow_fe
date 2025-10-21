from typing import Tuple, Dict, Any, Optional
import os
import requests

URL_API_BASE = os.environ.get('URL_API_BASE', 'http://127.0.0.1:8000/api/v1')


def _url(path: str) -> str:
    return URL_API_BASE.rstrip('/') + '/' + path.lstrip('/')


def list_pumps(limit: int = 50, offset: int = 0, token: Optional[str] = None) -> Dict[str, Any]:
    """Lấy danh sách máy bơm từ API.
    """
    try:
        headers = {}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        resp = requests.get(_url('may-bom'), params={'limit': limit, 'offset': offset}, timeout=5, headers=headers)
        try:
            data = resp.json() if resp.content else {}
        except Exception:
            data = {}
        if resp.status_code == 200:
            return data
        return {'data': [], 'limit': limit, 'offset': offset, 'total': 0, 'error': data}
    except requests.RequestException as e:
        return {'data': [], 'limit': limit, 'offset': offset, 'total': 0, 'error': str(e)}


def get_pump(ma_may_bom: int, token: Optional[str] = None) -> Dict[str, Any]:
    try:
        headers = {}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        resp = requests.get(_url(f'may-bom/{ma_may_bom}'), timeout=5, headers=headers)
        try:
            data = resp.json() if resp.content else {}
        except Exception:
            data = {}
        if resp.status_code == 200:
            return data
        return {}
    except requests.RequestException:
        return {}


def create_pump(pump: Dict[str, Any], token: Optional[str] = None) -> Tuple[bool, str]:
    try:
        headers = {}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        resp = requests.post(_url('may-bom/'), json=pump, timeout=5, headers=headers)
        try:
            data = resp.json() if resp.content else {}
        except Exception:
            data = {}
        if resp.status_code in (200, 201):
            return True, data.get('message', 'Tạo máy bơm thành công')
        return False, data.get('message', data.get('error', 'Tạo máy bơm thất bại'))
    except requests.RequestException as e:
        return False, f'Lỗi kết nối tới server: {e}'


def update_pump(ma_may_bom: int, pump: Dict[str, Any], token: Optional[str] = None) -> Tuple[bool, str]:
    try:
        headers = {}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        resp = requests.put(_url(f'may-bom/{ma_may_bom}'), json=pump, timeout=5, headers=headers)
        try:
            data = resp.json() if resp.content else {}
        except Exception:
            data = {}
        if resp.status_code in (200, 204):
            return True, data.get('message', 'Cập nhật máy bơm thành công')
        return False, data.get('message', data.get('error', 'Cập nhật máy bơm thất bại'))
    except requests.RequestException as e:
        return False, f'Lỗi kết nối tới server: {e}'


def delete_pump(ma_may_bom: int, token: Optional[str] = None) -> Tuple[bool, str]:
    try:
        headers = {}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        resp = requests.delete(_url(f'may-bom/{ma_may_bom}'), timeout=5, headers=headers)
        try:
            data = resp.json() if resp.content else {}
        except Exception:
            data = {}
        if resp.status_code in (200, 204):
            return True, data.get('message', 'Xóa máy bơm thành công')
        return False, data.get('message', data.get('error', 'Xóa máy bơm thất bại'))
    except requests.RequestException as e:
        return False, f'Lỗi kết nối tới server: {e}'
