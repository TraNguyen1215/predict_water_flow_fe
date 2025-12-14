from typing import List, Dict, Any, Optional
import os
import requests
import json
import base64
from datetime import datetime, timedelta

URL_API_BASE = os.environ.get('URL_API_BASE', 'http://127.0.0.1:8000/api/v1')

def _url(path: str) -> str:
    return URL_API_BASE.rstrip('/') + '/' + path.lstrip('/')

def _decode_token(token: str) -> Dict[str, Any]:
    try:
        # JWT has 3 parts: header.payload.signature
        parts = token.split('.')
        if len(parts) < 2:
            return {}
        payload = parts[1]
        # Add padding if needed
        payload += '=' * (-len(payload) % 4)
        decoded_bytes = base64.urlsafe_b64decode(payload)
        return json.loads(decoded_bytes)
    except Exception:
        return {}

def get_notifications(limit=50, offset=0, status=None, token=None):
    """Lấy danh sách thông báo từ API"""
    if not token:
        return {'data': [], 'total': 0}

    user_info = _decode_token(token)
    # Try to find user ID in common claims
    user_id = user_info.get('sub') or user_info.get('id') or user_info.get('user_id') or user_info.get('ma_nguoi_dung')
    
    if not user_id:
        return {'data': [], 'total': 0}

    try:
        headers = {'Authorization': f'Bearer {token}'}
        params = {'limit': limit, 'offset': offset}
        if status is not None:
            params['status'] = status
            
        resp = requests.get(_url(f'thong-bao/user/{user_id}'), headers=headers, params=params, timeout=5)
        
        if resp.status_code == 200:
            data = resp.json()
            
            raw_notifications = []
            if isinstance(data, list):
                raw_notifications = data
            elif isinstance(data, dict) and 'data' in data:
                raw_notifications = data['data']
            
            notifications = []
            for item in raw_notifications:
                # Format created_at to HH:MM dd/mm/yyyy
                created_at = item.get('thoi_gian_tao')
                try:
                    if created_at:
                        # Handle common API date formats
                        if 'T' in created_at:
                            # ISO format: 2023-12-14T15:30:00
                            dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        else:
                            # Standard DB format: 2023-12-14 15:30:00
                            dt = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S')
                        
                        # Add 7 hours
                        dt = dt + timedelta(hours=7)
                        created_at = dt.strftime('%H:%M %d/%m/%Y')
                except Exception:
                    pass # Keep original if parsing fails

                # Map fields
                notif = {
                    'id': item.get('ma_thong_bao'),
                    'ma_thong_bao': item.get('ma_thong_bao'),
                    'title': item.get('tieu_de'),
                    'message': item.get('noi_dung'),
                    'type': item.get('loai', 'info'), # warning, info, success, danger
                    'is_read': item.get('da_xem', False),
                    'created_at': created_at,
                    'user_id': item.get('ma_nguoi_dung')
                }
                notifications.append(notif)
                
            return {
                'data': notifications,
                'total': len(notifications)
            }
        return {'data': [], 'total': 0}
    except Exception as e:
        print(f"Error fetching notifications: {e}")
        return {'data': [], 'total': 0}

def get_unread_count(token=None):
    """Lấy số lượng thông báo chưa đọc"""
    if not token:
        return 0
    
    # Fetch notifications and count
    result = get_notifications(limit=100, token=token)
    notifications = result.get('data', [])
    return sum(1 for n in notifications if not n.get('is_read', False))

def mark_notification_as_read(notification_id, token=None):
    """Đánh dấu thông báo đã đọc"""
    if not token:
        return None
        
    try:
        headers = {'Authorization': f'Bearer {token}'}
        resp = requests.post(_url(f'thong-bao/{notification_id}/mark-as-read'), headers=headers, timeout=5)
        
        if resp.status_code in (200, 204):
            return resp.json() if resp.content else {'id': notification_id, 'is_read': True}
    except Exception as e:
        print(f"Error marking notification as read: {e}")
        pass
        
    return {'id': notification_id, 'is_read': True}

def mark_all_as_read(token=None):
    """Đánh dấu tất cả thông báo đã đọc"""
    if not token:
        return {'message': 'Token required'}
        
    try:
        headers = {'Authorization': f'Bearer {token}'}
        requests.post(_url('thong-bao/mark-all-as-read'), headers=headers, timeout=5)
    except Exception as e:
        print(f"Error marking all as read: {e}")
        pass
        
    return {'message': 'All notifications marked as read'}

def delete_notification(notification_id, token=None):
    """Xóa thông báo"""
    if not token:
        return {'message': 'Token required'}
        
    try:
        headers = {'Authorization': f'Bearer {token}'}
        # Use DELETE /api/v1/thong-bao/{ma_thong_bao}
        requests.delete(_url(f'thong-bao/{notification_id}'), headers=headers, timeout=5)
    except Exception as e:
        print(f"Error deleting notification: {e}")
        pass
        
    return {'message': 'Notification deleted'}

def delete_all_notifications(token=None):
    """Xóa tất cả thông báo"""
    if not token:
        return {'message': 'Token required'}
        
    try:
        headers = {'Authorization': f'Bearer {token}'}
        # Use DELETE /api/v1/thong-bao/delete-all
        requests.delete(_url('thong-bao/delete-all'), headers=headers, timeout=5)
    except Exception as e:
        print(f"Error deleting all notifications: {e}")
        pass
        
    return {'message': 'All notifications deleted'}
