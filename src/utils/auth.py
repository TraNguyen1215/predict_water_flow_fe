"""
Authentication utilities
"""
import hashlib
import json
import os

USER_DATA_FILE = 'data/users.json'

def hash_password(password):
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def load_users():
    """Load users from JSON file"""
    if not os.path.exists(USER_DATA_FILE):
        os.makedirs(os.path.dirname(USER_DATA_FILE), exist_ok=True)
        with open(USER_DATA_FILE, 'w') as f:
            json.dump({}, f)
        return {}
    
    with open(USER_DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_users(users):
    """Save users to JSON file"""
    os.makedirs(os.path.dirname(USER_DATA_FILE), exist_ok=True)
    with open(USER_DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

def register_user(username, email, password):
    """Register a new user"""
    users = load_users()
    
    if username in users:
        return False, "Tên người dùng đã tồn tại"
    
    # Check if email exists
    for user_data in users.values():
        if user_data.get('email') == email:
            return False, "Email đã được sử dụng"
    
    users[username] = {
        'email': email,
        'password': hash_password(password),
        'full_name': '',
        'phone': '',
        'created_at': None
    }
    
    save_users(users)
    return True, "Đăng ký thành công"

def authenticate_user(username, password):
    """Authenticate user"""
    users = load_users()
    
    if username not in users:
        return False, "Tên người dùng không tồn tại"
    
    if users[username]['password'] != hash_password(password):
        return False, "Mật khẩu không đúng"
    
    return True, "Đăng nhập thành công"

def get_user_info(username):
    """Get user information"""
    users = load_users()
    return users.get(username, {})

def update_user_info(username, user_data):
    """Update user information"""
    users = load_users()
    
    if username not in users:
        return False, "Người dùng không tồn tại"
    
    users[username].update(user_data)
    save_users(users)
    return True, "Cập nhật thành công"
