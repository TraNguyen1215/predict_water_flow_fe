from typing import Tuple, Dict, Any, Optional
import os
import requests

URL_API_BASE = os.environ.get('URL_API_BASE', 'http://127.0.0.1:8000/api/v1')


def _url(path: str) -> str:
    return URL_API_BASE.rstrip('/') + '/' + path.lstrip('/')


def get_data_by_pump(ma_may_bom: Optional[int] = None, limit: int = 20, offset: int = 0, token: Optional[str] = None) -> Dict[str, Any]:

    try:
        headers = {}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        params = {'limit': limit, 'offset': offset}
        if ma_may_bom is not None:
            params['ma_may_bom'] = ma_may_bom
        resp = requests.get(_url('du-lieu-cam-bien'), params=params, timeout=5, headers=headers)
        try:
            data = resp.json() if resp.content else {}
        except Exception:
            data = {}
        if resp.status_code == 200:
            return data
        return {'data': [], 'limit': limit, 'offset': offset, 'total': 0, 'error': data}
    except requests.RequestException as e:
        return {'data': [], 'limit': limit, 'offset': offset, 'total': 0, 'error': str(e)}


def get_data_by_date(ngay: str, token: Optional[str] = None, limit: Optional[int] = None, offset: Optional[int] = None) -> Dict[str, Any]:
    """Get sensor data for a given date (ngay in YYYY-MM-DD)."""
    try:
        headers = {}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        
        params = {'limit': limit, 'offset': offset}
        resp = requests.get(_url(f'du-lieu-cam-bien/ngay/{ngay}'), timeout=5, headers=headers, params=params)
        try:
            data = resp.json() if resp.content else {}
        except Exception:
            data = {}
        if resp.status_code == 200:
            return data
        return {'data': [], 'error': data}
    except requests.RequestException as e:
        return {'data': [], 'error': str(e)}


def put_sensor_data(payload: Dict[str, Any], token: Optional[str] = None) -> Tuple[bool, str]:
    """PUT /du-lieu-cam-bien/ with payload containing sensor data for a date."""
    try:
        headers = {}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        resp = requests.put(_url('du-lieu-cam-bien/'), json=payload, timeout=5, headers=headers)
        try:
            data = resp.json() if resp.content else {}
        except Exception:
            data = {}
        if resp.status_code in (200, 204):
            return True, data.get('message', 'Cập nhật dữ liệu thành công')
        return False, data.get('message', data.get('error', 'Cập nhật dữ liệu thất bại'))
    except requests.RequestException as e:
        return False, f'Lỗi kết nối tới server: {e}'
