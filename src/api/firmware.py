from typing import Tuple, Dict, Any, Optional
import os
import requests

URL_API_BASE = os.environ.get('URL_API_BASE', 'http://127.0.0.1:8000/api/v1')


def _url(path: str) -> str:
    return URL_API_BASE.rstrip('/') + '/' + path.lstrip('/')


def list_firmwares(limit: int = 50, offset: int = 0, token: Optional[str] = None) -> Dict[str, Any]:
    try:
        headers = {}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        resp = requests.get(_url('tep-ma-nhung'), params={'limit': limit, 'offset': offset}, timeout=10, headers=headers)
        try:
            data = resp.json() if resp.content else {}
        except Exception:
            data = {}
        if resp.status_code == 200:
            return data
        return {'data': [], 'limit': limit, 'offset': offset, 'total': 0, 'error': data}
    except requests.RequestException as e:
        return {'data': [], 'limit': limit, 'offset': offset, 'total': 0, 'error': str(e)}


def get_firmware(firmware_id: int, token: Optional[str] = None) -> Dict[str, Any]:
    try:
        headers = {}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        resp = requests.get(_url(f'tep-ma-nhung/{firmware_id}'), timeout=10, headers=headers)
        try:
            data = resp.json() if resp.content else {}
        except Exception:
            data = {}
        if resp.status_code == 200:
            return data
        return {}
    except requests.RequestException:
        return {}


def upload_firmware(file_tuple: Tuple[str, bytes], metadata: Dict[str, Any] = None, token: Optional[str] = None) -> Tuple[bool, str]:
    """Upload a firmware file. file_tuple should be (filename, filebytes).    """
    try:
        headers = {}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        files = {'file': (file_tuple[0], file_tuple[1])}
        data = metadata or {}
        resp = requests.post(_url('tep-ma-nhung/'), files=files, data=data, timeout=30, headers=headers)
        try:
            resp_data = resp.json() if resp.content else {}
        except Exception:
            resp_data = {}
        if resp.status_code in (200, 201):
            return True, resp_data.get('message', 'Tải firmware lên thành công')
        return False, resp_data.get('message', resp_data.get('error', 'Tải firmware thất bại'))
    except requests.RequestException as e:
        return False, f'Lỗi kết nối tới server: {e}'


def delete_firmware(firmware_id: int, token: Optional[str] = None) -> Tuple[bool, str]:
    try:
        headers = {}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        resp = requests.delete(_url(f'tep-ma-nhung/{firmware_id}'), timeout=10, headers=headers)
        try:
            data = resp.json() if resp.content else {}
        except Exception:
            data = {}
        if resp.status_code in (200, 204):
            return True, data.get('message', 'Xóa firmware thành công')
        return False, data.get('message', data.get('error', 'Xóa firmware thất bại'))
    except requests.RequestException as e:
        return False, f'Lỗi kết nối tới server: {e}'


def download_url(firmware_id: int, token: Optional[str] = None) -> Optional[str]:
    """Return a URL to download the firmware.
    
    Args:
        firmware_id (int): ID of the firmware to download
        token (Optional[str]): Bearer token for authentication
        
    Returns:
        Optional[str]: Download URL if firmware exists, None otherwise
    """
    if not token:
        return None
    return _url(f'tep-ma-nhung/{firmware_id}/download')
