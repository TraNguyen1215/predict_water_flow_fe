from typing import Tuple, Dict, Any, Optional
import os
import requests

URL_API_BASE = os.environ.get('URL_API_BASE', 'http://127.0.0.1:8000/api/v1')


def _url(path: str) -> str:
    return URL_API_BASE.rstrip('/') + '/' + path.lstrip('/')


def list_logs(limit: int = 20, offset: int = 0, token: Optional[str] = None) -> Dict[str, Any]:
    try:
        headers = {}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        params = {'limit': limit, 'offset': offset}
        resp = requests.get(_url('nhat-ky-gieo-trong'), params=params, timeout=5, headers=headers)
        try:
            data = resp.json() if resp.content else {}
        except Exception:
            data = {}
        if resp.status_code == 200:
            return data
        return {'data': [], 'limit': limit, 'offset': offset, 'total': 0, 'error': data}
    except requests.RequestException as e:
        return {'data': [], 'limit': limit, 'offset': offset, 'total': 0, 'error': str(e)}


def get_log(log_id: str, token: Optional[str] = None) -> Dict[str, Any]:
    try:
        headers = {}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        resp = requests.get(_url(f'nhat-ky-gieo-trong/{log_id}'), timeout=5, headers=headers)
        try:
            data = resp.json() if resp.content else {}
        except Exception:
            data = {}
        if resp.status_code == 200:
            return data
        return {'data': None, 'error': data}
    except requests.RequestException as e:
        return {'data': None, 'error': str(e)}


def list_by_date(ngay: str, token: Optional[str] = None, limit: Optional[int] = None, offset: Optional[int] = None) -> Dict[str, Any]:
    try:
        headers = {}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        params = {'limit': limit, 'offset': offset}
        resp = requests.get(_url(f'nhat-ky-gieo-trong/ngay/{ngay}'), timeout=5, headers=headers, params=params)
        try:
            data = resp.json() if resp.content else {}
        except Exception:
            data = {}
        if resp.status_code == 200:
            return data
        return {'data': [], 'error': data}
    except requests.RequestException as e:
        return {'data': [], 'error': str(e)}


def create_log(payload: Dict[str, Any], token: Optional[str] = None) -> Tuple[bool, str]:
    try:
        headers = {}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        resp = requests.post(_url('nhat-ky-gieo-trong'), json=payload, timeout=5, headers=headers)
        try:
            data = resp.json() if resp.content else {}
        except Exception:
            data = {}
        if resp.status_code in (200, 201):
            return True, data.get('message', 'Đã tạo mục nhật ký')
        return False, data.get('message', data.get('error', 'Tạo mục nhật ký thất bại'))
    except requests.RequestException as e:
        return False, f'Lỗi kết nối tới server: {e}'


def update_log(log_id: str, payload: Dict[str, Any], token: Optional[str] = None) -> Tuple[bool, str]:
    try:
        headers = {}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        resp = requests.put(_url(f'nhat-ky-gieo-trong/{log_id}'), json=payload, timeout=5, headers=headers)
        try:
            data = resp.json() if resp.content else {}
        except Exception:
            data = {}
        if resp.status_code in (200, 204):
            return True, data.get('message', 'Cập nhật mục nhật ký thành công')
        return False, data.get('message', data.get('error', 'Cập nhật thất bại'))
    except requests.RequestException as e:
        return False, f'Lỗi kết nối tới server: {e}'


def delete_log(log_id: str, token: Optional[str] = None) -> Tuple[bool, str]:
    try:
        headers = {}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        resp = requests.delete(_url(f'nhat-ky-gieo-trong/{log_id}'), timeout=5, headers=headers)
        try:
            data = resp.json() if resp.content else {}
        except Exception:
            data = {}
        if resp.status_code in (200, 204):
            return True, data.get('message', 'Xóa mục nhật ký thành công')
        return False, data.get('message', data.get('error', 'Xóa thất bại'))
    except requests.RequestException as e:
        return False, f'Lỗi kết nối tới server: {e}'
