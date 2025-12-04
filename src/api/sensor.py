from typing import Tuple, Dict, Any, Optional
import os
import requests
import time
import base64
import json

URL_API_BASE = os.environ.get('URL_API_BASE', 'http://127.0.0.1:8000/api/v1')


def _url(path: str) -> str:
    return URL_API_BASE.rstrip('/') + '/' + path.lstrip('/')


def list_sensors(limit: int = 50, offset: int = 0, token: Optional[str] = None) -> Dict[str, Any]:
    """Lấy danh sách cảm biến từ API.
    """
    try:
        headers = {}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        resp = requests.get(_url('cam-bien'), params={'limit': limit, 'offset': offset}, timeout=5, headers=headers)
        try:
            data = resp.json() if resp.content else {}
        except Exception:
            data = {}
        if resp.status_code == 200:
            # print(data)
            return data
        return {'data': [], 'limit': limit, 'offset': offset, 'total': 0, 'error': data}
    except requests.RequestException as e:
        return {'data': [], 'limit': limit, 'offset': offset, 'total': 0, 'error': str(e)}


def get_sensor(ma_cam_bien: int, token: Optional[str] = None) -> Dict[str, Any]:
    try:
        headers = {}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        resp = requests.get(_url(f'cam-bien/{ma_cam_bien}'), timeout=5, headers=headers)
        try:
            data = resp.json() if resp.content else {}
        except Exception:
            data = {}
        if resp.status_code == 200:
            return data
        return {}
    except requests.RequestException:
        return {}


def create_sensor(sensor: Dict[str, Any], token: Optional[str] = None) -> Tuple[bool, str]:
    try:
        headers = {}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        resp = requests.post(_url('cam-bien/'), json=sensor, timeout=5, headers=headers)
        try:
            data = resp.json() if resp.content else {}
        except Exception:
            data = {}
        if resp.status_code in (200, 201):
            return True, data.get('message', 'Tạo cảm biến thành công')
        return False, data.get('message', data.get('error', 'Tạo cảm biến thất bại'))
    except requests.RequestException as e:
        return False, f'Lỗi kết nối tới server: {e}'


def update_sensor(ma_cam_bien: int, sensor: Dict[str, Any], token: Optional[str] = None) -> Tuple[bool, str]:
    try:
        headers = {}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        resp = requests.put(_url(f'cam-bien/{ma_cam_bien}'), json=sensor, timeout=5, headers=headers)
        try:
            data = resp.json() if resp.content else {}
        except Exception:
            data = {}
        if resp.status_code in (200, 204):
            return True, data.get('message', 'Cập nhật cảm biến thành công')
        return False, data.get('message', data.get('error', 'Cập nhật cảm biến thất bại'))
    except requests.RequestException as e:
        return False, f'Lỗi kết nối tới server: {e}'


def delete_sensor(ma_cam_bien: int, token: Optional[str] = None) -> Tuple[bool, str]:
    try:
        headers = {}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        resp = requests.delete(_url(f'cam-bien/{ma_cam_bien}'), timeout=5, headers=headers)
        try:
            data = resp.json() if resp.content else {}
        except Exception:
            data = {}
        if resp.status_code in (200, 204):
            return True, data.get('message', 'Xóa cảm biến thành công')
        return False, data.get('message', data.get('error', 'Xóa cảm biến thất bại'))
    except requests.RequestException as e:
        return False, f'Lỗi kết nối tới server: {e}'


def get_sensor_types(token: Optional[str] = None) -> Dict[str, Any]:
    """Lấy danh sách loại cảm biến từ API: GET /loai_cam_bien

    """
    try:
        headers = {}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        resp = requests.get(_url('loai-cam-bien'), timeout=5, headers=headers)
        try:
            data = resp.json() if resp.content else {}
        except Exception:
            data = {}
        if resp.status_code == 200:
            return data
        return {'data': [], 'error': data}
    except requests.RequestException as e:
        return {'data': [], 'error': str(e)}

# thêm loại cảm biến, cập nhật, xóa loại cảm biến có thể được thêm tương tự khi cần thiết
def create_sensor_type(sensor_type: Dict[str, Any], token: Optional[str] = None) -> Tuple[bool, str]:
    try:
        headers = {}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        resp = requests.post(_url('loai-cam-bien/'), json=sensor_type, timeout=5, headers=headers)
        try:
            data = resp.json() if resp.content else {}
        except Exception:
            data = {}
        if resp.status_code in (200, 201):
            return True, data.get('message', 'Tạo loại cảm biến thành công')
        return False, data.get('message', data.get('error', 'Tạo loại cảm biến thất bại'))
    except requests.RequestException as e:
        return False, f'Lỗi kết nối tới server: {e}'
    
def delete_sensor_type(ma_loai_cam_bien: int, token: Optional[str] = None) -> Tuple[bool, str]:
    try:
        headers = {}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        resp = requests.delete(_url(f'loai-cam-bien/{ma_loai_cam_bien}'), timeout=5, headers=headers)
        try:
            data = resp.json() if resp.content else {}
        except Exception:
            data = {}
        if resp.status_code in (200, 204):
            return True, data.get('message', 'Xóa loại cảm biến thành công')
        return False, data.get('message', data.get('error', 'Xóa loại cảm biến thất bại'))
    except requests.RequestException as e:
        return False, f'Lỗi kết nối tới server: {e}'
    
def update_sensor_type(ma_loai_cam_bien: int, sensor_type: Dict[str, Any], token: Optional[str] = None) -> Tuple[bool, str]:
    try:
        headers = {}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        resp = requests.put(_url(f'loai-cam-bien/{ma_loai_cam_bien}'), json=sensor_type, timeout=5, headers=headers)
        try:
            data = resp.json() if resp.content else {}
        except Exception:
            data = {}
        if resp.status_code in (200, 204):
            return True, data.get('message', 'Cập nhật loại cảm biến thành công')
        return False, data.get('message', data.get('error', 'Cập nhật loại cảm biến thất bại'))
    except requests.RequestException as e:
        return False, f'Lỗi kết nối tới server: {e}'

