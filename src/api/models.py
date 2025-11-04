from typing import Tuple, Dict, Any, Optional
import os
import requests

URL_API_BASE = os.environ.get('URL_API_BASE', 'http://127.0.0.1:8000/api/v1')

def _url(path: str) -> str:
    return URL_API_BASE.rstrip('/') + '/' + path.lstrip('/')


def list_models(limit: int = 50, offset: int = 0, token: Optional[str] = None) -> Dict[str, Any]:
    """Lấy danh sách mô hình dự báo từ API."""
    try:
        headers = {}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        resp = requests.get(_url('mo-hinh-du-bao'), params={'limit': limit, 'offset': offset}, timeout=5, headers=headers)
        try:
            data = resp.json() if resp.content else {}
        except Exception:
            data = {}
        if resp.status_code == 200:
            return data
        return {'data': [], 'limit': limit, 'offset': offset, 'total': 0, 'error': data}
    except requests.RequestException as e:
        return {'data': [], 'limit': limit, 'offset': offset, 'total': 0, 'error': str(e)}


def get_model(ma_mo_hinh: int, token: Optional[str] = None) -> Dict[str, Any]:
    """Lấy thông tin một mô hình dự báo theo mã."""
    try:
        headers = {}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        resp = requests.get(_url(f'mo-hinh-du-bao/{ma_mo_hinh}'), timeout=5, headers=headers)
        try:
            data = resp.json() if resp.content else {}
        except Exception:
            data = {}
        if resp.status_code == 200:
            return data
        return {}
    except requests.RequestException:
        return {}


def create_model(metadata: Dict[str, Any], token: Optional[str] = None) -> Tuple[bool, str]:
    """Tạo mô hình dự báo mới."""
    try:
        headers = {
            'Authorization': f'Bearer {token}' if token else '',
            'Content-Type': 'application/json'
        }
        
        # Prepare the data
        data = {
            'ten_mo_hinh': metadata.get('ten_mo_hinh', ''),
            'phien_ban': metadata.get('phien_ban', ''),
            'trang_thai': metadata.get('trang_thai', False)
        }
            
        resp = requests.post(_url('mo-hinh-du-bao'), json=data, timeout=30, headers=headers)
        try:
            msg = resp.json() if resp.content else {}
        except Exception:
            msg = {}
            
        if resp.status_code == 201:
            return True, 'Tạo mô hình thành công'
        return False, str(msg)
    except requests.RequestException as e:
        return False, str(e)


def update_model(ma_mo_hinh: int, data: Dict[str, Any], token: Optional[str] = None) -> Tuple[bool, str]:
    """Cập nhật thông tin mô hình dự báo."""
    try:
        headers = {}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        
        resp = requests.put(_url(f'mo-hinh-du-bao/{ma_mo_hinh}'), json=data, timeout=5, headers=headers)
        try:
            msg = resp.json() if resp.content else {}
        except Exception:
            msg = {}
            
        if resp.status_code == 200:
            return True, 'Cập nhật mô hình thành công'
        return False, msg.get('detail', 'Lỗi không xác định')
    except requests.RequestException as e:
        return False, str(e)


def delete_model(ma_mo_hinh: int, token: Optional[str] = None) -> Tuple[bool, str]:
    """Xóa một mô hình dự báo."""
    try:
        headers = {}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        
        resp = requests.delete(_url(f'mo-hinh-du-bao/{ma_mo_hinh}'), timeout=5, headers=headers)
        try:
            msg = resp.json() if resp.content else {}
        except Exception:
            msg = {}
            
        if resp.status_code == 200:
            return True, 'Xóa mô hình thành công'
        return False, msg.get('detail', 'Lỗi không xác định')
    except requests.RequestException as e:
        return False, str(e)