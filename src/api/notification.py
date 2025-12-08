from datetime import datetime, timedelta

# Mock notifications data - Dữ liệu tĩnh
MOCK_NOTIFICATIONS = [
    {
        'id': 1,
        'ma_thong_bao': 1,
        'title': '⚠️ Lượng nước giảm bất thường',
        'message': 'Lưu lượng nước giảm 40% so với bình thường. Vui lòng kiểm tra hệ thống.',
        'type': 'warning',
        'is_read': False,
        'created_at': (datetime.now() - timedelta(minutes=5)).strftime('%H:%M %d/%m/%Y'),
        'user_id': None
    },
    {
        'id': 2,
        'ma_thong_bao': 2,
        'title': '🌧️ Mưa được phát hiện',
        'message': 'Cảm biến mưa đã phát hiện tín hiệu mưa.',
        'type': 'info',
        'is_read': False,
        'created_at': (datetime.now() - timedelta(minutes=15)).strftime('%H:%M %d/%m/%Y'),
        'user_id': None
    },
    {
        'id': 3,
        'ma_thong_bao': 3,
        'title': '✅ Cảm biến A1 kết nối thành công',
        'message': 'Cảm biến độ ẩm đất A1 đã kết nối thành công và sẵn sàng hoạt động.',
        'type': 'success',
        'is_read': True,
        'created_at': (datetime.now() - timedelta(hours=1)).strftime('%H:%M %d/%m/%Y'),
        'user_id': None
    },
    {
        'id': 4,
        'ma_thong_bao': 4,
        'title': '🔔 Máy bơm dừng hoạt động',
        'message': 'Máy bơm chính đã dừng lại sau 45 phút hoạt động liên tục.',
        'type': 'info',
        'is_read': True,
        'created_at': (datetime.now() - timedelta(hours=2)).strftime('%H:%M %d/%m/%Y'),
        'user_id': None
    },
    {
        'id': 5,
        'ma_thong_bao': 5,
        'title': '❌ Cảm biến B2 ngừng kết nối',
        'message': 'Cảm biến nhiệt độ B2 không phản hồi. Kiểm tra kết nối.',
        'type': 'danger',
        'is_read': True,
        'created_at': (datetime.now() - timedelta(hours=3)).strftime('%H:%M %d/%m/%Y'),
        'user_id': None
    },
    {
        'id': 6,
        'ma_thong_bao': 6,
        'title': '📊 Báo cáo hàng ngày đã sẵn sàng',
        'message': 'Báo cáo dữ liệu hàng ngày của ngày hôm qua đã được tạo.',
        'type': 'success',
        'is_read': True,
        'created_at': (datetime.now() - timedelta(hours=4)).strftime('%H:%M %d/%m/%Y'),
        'user_id': None
    }
]

def get_notifications(limit=50, offset=0, status=None, token=None):
    """Lấy danh sách thông báo (dữ liệu tĩnh)"""
    notifications = MOCK_NOTIFICATIONS[offset:offset + limit]
    return {
        'data': notifications,
        'total': len(MOCK_NOTIFICATIONS)
    }

def get_unread_count(token=None):
    """Lấy số lượng thông báo chưa đọc (dữ liệu tĩnh)"""
    return sum(1 for n in MOCK_NOTIFICATIONS if not n.get('is_read', False))

def mark_notification_as_read(notification_id, token=None):
    """Đánh dấu thông báo đã đọc (dữ liệu tĩnh)"""
    for notif in MOCK_NOTIFICATIONS:
        if notif.get('id') == notification_id or notif.get('ma_thong_bao') == notification_id:
            notif['is_read'] = True
            return notif
    return None

def mark_all_as_read(token=None):
    """Đánh dấu tất cả thông báo đã đọc (dữ liệu tĩnh)"""
    for notif in MOCK_NOTIFICATIONS:
        notif['is_read'] = True
    return {'message': 'All notifications marked as read'}

def delete_notification(notification_id, token=None):
    """Xóa thông báo (dữ liệu tĩnh)"""
    global MOCK_NOTIFICATIONS
    MOCK_NOTIFICATIONS = [n for n in MOCK_NOTIFICATIONS if n.get('id') != notification_id and n.get('ma_thong_bao') != notification_id]
    return {'message': 'Notification deleted'}

def delete_all_notifications(token=None):
    """Xóa tất cả thông báo (dữ liệu tĩnh)"""
    global MOCK_NOTIFICATIONS
    MOCK_NOTIFICATIONS = []
    return {'message': 'All notifications deleted'}
