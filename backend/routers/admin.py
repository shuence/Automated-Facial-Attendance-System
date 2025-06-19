from fastapi import APIRouter, Depends, HTTPException, status
from security import get_current_active_user, is_admin
from models import UserRole, UserCreate
import os
import json
import uuid
from datetime import datetime
from typing import List, Optional

router = APIRouter()

# Define file paths
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data_dir = os.path.join(current_dir, 'data')
USERS_FILE = os.path.join(data_dir, 'users.json')


def get_all_users():
    """Get all users from the database"""
    try:
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error fetching users: {e}")
    return []


def save_users(users):
    """Save users to the database file"""
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=4)


@router.get("/users")
async def get_users(
    role: Optional[str] = None,
    current_user: dict = Depends(get_current_active_user)
):
    """Get all users with optional role filter (admin only)"""
    if not is_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view all users"
        )
    
    users = get_all_users()
    
    if role:
        users = [user for user in users if user.get("role") == role]
    
    return users


@router.get("/users/{user_id}")
async def get_user(
    user_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    """Get a specific user by ID (admin only)"""
    if not is_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view user details"
        )
    
    users = get_all_users()
    for user in users:
        if user.get("id") == user_id:
            return user
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="User not found"
    )


@router.post("/users")
async def create_user(
    user_data: UserCreate,
    current_user: dict = Depends(get_current_active_user)
):
    """Create a new user (admin only)"""
    if not is_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create users"
        )
    
    # Load existing users
    users = get_all_users()
    
    # Check if email already exists
    for user in users:
        if user.get("email") == user_data.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User with email {user_data.email} already exists"
            )
    
    # Create new user
    from security import get_password_hash
    
    user_id = str(uuid.uuid4())
    
    new_user = {
        "id": user_id,
        "email": user_data.email,
        "full_name": user_data.full_name,
        "hashed_password": get_password_hash(user_data.password),
        "role": user_data.role,
        "is_active": True,
        "created_at": datetime.now().isoformat()
    }
    
    users.append(new_user)
    save_users(users)
    
    return {"message": "User created successfully", "user_id": user_id}


@router.put("/users/{user_id}/deactivate")
async def deactivate_user(
    user_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    """Deactivate a user (admin only)"""
    if not is_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to deactivate users"
        )
    
    # Load existing users
    users = get_all_users()
    
    for i, user in enumerate(users):
        if user.get("id") == user_id:
            users[i]["is_active"] = False
            save_users(users)
            return {"message": "User deactivated successfully"}
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="User not found"
    )


@router.put("/users/{user_id}/activate")
async def activate_user(
    user_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    """Activate a user (admin only)"""
    if not is_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to activate users"
        )
    
    # Load existing users
    users = get_all_users()
    
    for i, user in enumerate(users):
        if user.get("id") == user_id:
            users[i]["is_active"] = True
            save_users(users)
            return {"message": "User activated successfully"}
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="User not found"
    )


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    """Delete a user (admin only)"""
    if not is_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete users"
        )
    
    # Load existing users
    users = get_all_users()
    
    # Find and remove the user
    for i, user in enumerate(users):
        if user.get("id") == user_id:
            del users[i]
            save_users(users)
            return {"message": "User deleted successfully"}
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="User not found"
    )


@router.get("/stats")
async def get_system_stats(current_user: dict = Depends(get_current_active_user)):
    """Get system statistics (admin only)"""
    if not is_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view system statistics"
        )
    
    # Load all users
    users = get_all_users()
    
    # Count users by role
    admin_count = sum(1 for user in users if user.get("role") == UserRole.ADMIN)
    class_teacher_count = sum(1 for user in users if user.get("role") == UserRole.CLASS_TEACHER)
    teacher_count = sum(1 for user in users if user.get("role") == UserRole.TEACHER)
    student_count = sum(1 for user in users if user.get("role") == UserRole.STUDENT)
    
    # Load attendance history
    attendance_history_file = os.path.join(data_dir, 'attendance_history.json')
    attendance_count = 0
    if os.path.exists(attendance_history_file):
        try:
            with open(attendance_history_file, 'r') as f:
                attendance_history = json.load(f)
                attendance_count = len(attendance_history)
        except Exception:
            pass
    
    return {
        "user_counts": {
            "admin": admin_count,
            "class_teacher": class_teacher_count,
            "teacher": teacher_count,
            "student": student_count,
            "total": len(users)
        },
        "attendance_records": attendance_count
    }
