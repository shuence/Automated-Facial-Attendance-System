import os
import json
import uuid
from models import UserCreate, User, StudentInfo, TeacherInfo, UserRole
from security import get_password_hash
from typing import List, Optional, Dict, Any
from datetime import datetime

# Define file paths
current_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(current_dir, 'data')
USERS_FILE = os.path.join(data_dir, 'users.json')
STORAGE_FILE = os.path.join(data_dir, 'storage.json')
ATTENDANCE_HISTORY_FILE = os.path.join(data_dir, 'attendance_history.json')


def initialize_db():
    """Initialize database files if they don't exist"""
    # Ensure the data directory exists
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    
    # Create users file if it doesn't exist
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'w') as f:
            json.dump([], f)
    
    # Create storage file if it doesn't exist
    if not os.path.exists(STORAGE_FILE):
        with open(STORAGE_FILE, 'w') as f:
            json.dump({
                'students': [],
                'classes': [],
                'students_data': {}
            }, f)
    
    # Create attendance history file if it doesn't exist
    if not os.path.exists(ATTENDANCE_HISTORY_FILE):
        with open(ATTENDANCE_HISTORY_FILE, 'w') as f:
            json.dump([], f)


def create_admin_if_not_exists():
    """Create a default admin user if no users exist"""
    try:
        users = load_users()
        if not users:
            admin_user = {
                "id": str(uuid.uuid4()),
                "email": "admin@example.com",
                "full_name": "System Administrator",
                "hashed_password": get_password_hash("admin123"),
                "role": UserRole.ADMIN,
                "is_active": True,
                "created_at": datetime.now().isoformat()
            }
            users.append(admin_user)
            save_users(users)
            print("Default admin user created")
    except Exception as e:
        print(f"Error creating admin user: {e}")


def load_users() -> List[Dict[str, Any]]:
    """Load users from the JSON file"""
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    return []


def save_users(users: List[Dict[str, Any]]):
    """Save users to the JSON file"""
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=4)


def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Get a user by email"""
    users = load_users()
    for user in users:
        if user["email"] == email:
            return user
    return None


def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    """Get a user by ID"""
    users = load_users()
    for user in users:
        if user["id"] == user_id:
            return user
    return None


def create_user(user: UserCreate) -> Dict[str, Any]:
    """Create a new user"""
    users = load_users()
    
    # Check if user already exists
    if any(u["email"] == user.email for u in users):
        raise ValueError("User with this email already exists")
    
    # Create new user
    new_user = {
        "id": str(uuid.uuid4()),
        "email": user.email,
        "full_name": user.full_name,
        "hashed_password": get_password_hash(user.password),
        "role": user.role,
        "is_active": True,
        "created_at": datetime.now().isoformat()
    }
    
    # Add additional info based on role
    if user.role == UserRole.STUDENT:
        new_user["student_info"] = {}
    elif user.role in [UserRole.TEACHER, UserRole.CLASS_TEACHER]:
        new_user["teacher_info"] = {}
    
    users.append(new_user)
    save_users(users)
    
    # Remove hashed_password from return
    user_dict = new_user.copy()
    user_dict.pop("hashed_password")
    return user_dict


def update_user(user_id: str, user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Update an existing user"""
    users = load_users()
    for i, user in enumerate(users):
        if user["id"] == user_id:
            # Don't allow changing email to one that already exists
            if "email" in user_data and user_data["email"] != user["email"]:
                if any(u["email"] == user_data["email"] for u in users if u["id"] != user_id):
                    raise ValueError("User with this email already exists")
            
            # Update password if provided
            if "password" in user_data:
                user_data["hashed_password"] = get_password_hash(user_data.pop("password"))
            
            # Update user data
            users[i] = {**user, **user_data}
            save_users(users)
            
            # Remove hashed_password from return
            result = users[i].copy()
            if "hashed_password" in result:
                result.pop("hashed_password")
            return result
    return None


def delete_user(user_id: str) -> bool:
    """Delete a user"""
    users = load_users()
    initial_count = len(users)
    users = [user for user in users if user["id"] != user_id]
    
    if len(users) < initial_count:
        save_users(users)
        return True
    return False


def update_student_info(user_id: str, info: StudentInfo) -> Optional[Dict[str, Any]]:
    """Update student information for a user"""
    user = get_user_by_id(user_id)
    if not user or user["role"] != UserRole.STUDENT:
        return None
    
    user["student_info"] = info.dict()
    return update_user(user_id, {"student_info": info.dict()})


def update_teacher_info(user_id: str, info: TeacherInfo) -> Optional[Dict[str, Any]]:
    """Update teacher information for a user"""
    user = get_user_by_id(user_id)
    if not user or user["role"] not in [UserRole.TEACHER, UserRole.CLASS_TEACHER]:
        return None
    
    return update_user(user_id, {"teacher_info": info.dict()})


def get_all_users(role: Optional[UserRole] = None) -> List[Dict[str, Any]]:
    """Get all users, optionally filtered by role"""
    users = load_users()
    
    # Filter by role if specified
    if role:
        users = [user for user in users if user.get("role") == role]
    
    # Remove passwords from results
    for user in users:
        if "hashed_password" in user:
            user.pop("hashed_password")
    
    return users


def load_storage():
    """Load data from storage file"""
    if os.path.exists(STORAGE_FILE):
        with open(STORAGE_FILE, 'r') as f:
            return json.load(f)
    return {'students': [], 'classes': [], 'students_data': {}}


def save_storage(data):
    """Save data to storage file"""
    with open(STORAGE_FILE, 'w') as f:
        json.dump(data, f, indent=4)


def load_attendance_history():
    """Load attendance history"""
    if os.path.exists(ATTENDANCE_HISTORY_FILE):
        with open(ATTENDANCE_HISTORY_FILE, 'r') as f:
            return json.load(f)
    return []


def save_attendance_history(data):
    """Save attendance history"""
    with open(ATTENDANCE_HISTORY_FILE, 'w') as f:
        json.dump(data, f, indent=4)


# Initialize database on import
initialize_db()
create_admin_if_not_exists()
