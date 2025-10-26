from typing import Optional, Dict, Any
import os
import requests

URL_API_BASE = os.environ.get('URL_API_BASE', 'http://127.0.0.1:8000/api/v1')


def _url(path: str) -> str:
    return URL_API_BASE.rstrip('/') + '/' + path.lstrip('/')


def get_pump_memory_logs(ma_may_bom: int, token: Optional[str] = None, limit: Optional[int] = None, offset: int = 0, date: Optional[str] = None) -> Dict[str, Any]:


    try:
        headers = {}
        if token:
            headers['Authorization'] = f'Bearer {token}'

        params = {'limit': limit, 'offset': offset, 'ma_may_bom': ma_may_bom}

        if date:
            endpoint = f'nhat-ky-may-bom/ngay/{date}'
            resp = requests.get(_url(endpoint), params=params, timeout=5, headers=headers)
        else:
            resp = requests.get(_url('nhat-ky-may-bom'), params=params, timeout=5, headers=headers)

        try:
            data = resp.json() if resp.content else {}
        except Exception:
            data = {}
        if resp.status_code == 200:
            return data
        return {'data': [], 'limit': limit, 'offset': offset, 'total': 0, 'error': data}
    except requests.RequestException as e:
        return {'data': [], 'limit': limit, 'offset': offset, 'total': 0, 'error': str(e)}
    