from fastapi import APIRouter, Depends, HTTPException, status
from security import get_current_active_user, is_admin, is_teacher
from models import UserRole
import os
import json
from datetime import datetime
import uuid
from typing import List, Optional

router = APIRouter()

# Define file paths
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data_dir = os.path.join(current_dir, 'data')
NOTIFICATIONS_FILE = os.path.join(data_dir, 'notifications.json')
USERS_FILE = os.path.join(data_dir, 'users.json')

# Ensure notifications file exists
if not os.path.exists(NOTIFICATIONS_FILE):
    with open(NOTIFICATIONS_FILE, 'w') as f:
        json.dump([], f)


def get_users():
    """Get all users from the database"""
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    return []


def get_notifications():
    """Get all notifications"""
    if os.path.exists(NOTIFICATIONS_FILE):
        with open(NOTIFICATIONS_FILE, 'r') as f:
            return json.load(f)
    return []


def save_notifications(notifications):
    """Save notifications to file"""
    with open(NOTIFICATIONS_FILE, 'w') as f:
        json.dump(notifications, f, indent=4)


@router.get("/")
async def get_user_notifications(current_user: dict = Depends(get_current_active_user)):
    """Get notifications for the current user"""
    user_id = current_user.get("id")
    role = current_user.get("role")
    
    all_notifications = get_notifications()
    
    # Filter notifications relevant to the user
    user_notifications = []
    
    for notification in all_notifications:
        # Check if the notification is for all users
        if notification.get("target_type") == "all":
            user_notifications.append(notification)
        
        # Check if the notification is for the user's role
        elif notification.get("target_type") == "role" and notification.get("target_value") == role:
            user_notifications.append(notification)
        
        # Check if the notification is specifically for this user
        elif notification.get("target_type") == "user" and notification.get("target_value") == user_id:
            user_notifications.append(notification)
        
        # For students, check if the notification is for their class
        elif role == UserRole.STUDENT and notification.get("target_type") == "class":
            student_info = current_user.get("student_info", {})
            dept = student_info.get("department")
            year = student_info.get("year")
            div = student_info.get("division")
            
            target_class = notification.get("target_value", "")
            if target_class == f"{dept}_{year}_{div}":
                user_notifications.append(notification)
    
    # Sort by date, newest first
    user_notifications.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    
    return user_notifications


@router.post("/")
async def create_notification(
    title: str,
    message: str,
    target_type: str,
    target_value: Optional[str] = None,
    current_user: dict = Depends(get_current_active_user)
):
    """Create a new notification"""
    if not is_admin(current_user) and not is_teacher(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create notifications"
        )
    
    # Validate target type
    valid_target_types = ["all", "role", "user", "class"]
    if target_type not in valid_target_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid target_type. Must be one of: {', '.join(valid_target_types)}"
        )
    
    # Validate target value
    if target_type != "all" and not target_value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="target_value is required for the specified target_type"
        )
    
    # Validate role target
    if target_type == "role":
        valid_roles = [role.value for role in UserRole]
        if target_value not in valid_roles:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role. Must be one of: {', '.join(valid_roles)}"
            )
    
    # Validate user target
    if target_type == "user":
        users = get_users()
        user_ids = [user.get("id") for user in users]
        if target_value not in user_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user ID"
            )
    
    # Create the notification
    new_notification = {
        "id": str(uuid.uuid4()),
        "title": title,
        "message": message,
        "target_type": target_type,
        "target_value": target_value if target_type != "all" else None,
        "created_at": datetime.now().isoformat(),
        "created_by": current_user.get("id"),
        "creator_name": current_user.get("full_name")
    }
    
    # Save the notification
    notifications = get_notifications()
    notifications.append(new_notification)
    save_notifications(notifications)
    
    return {
        "message": "Notification created successfully",
        "notification_id": new_notification["id"]
    }


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    """Delete a notification"""
    if not is_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete notifications"
        )
    
    notifications = get_notifications()
    
    # Find the notification
    notification_index = -1
    for i, notification in enumerate(notifications):
        if notification.get("id") == notification_id:
            notification_index = i
            break
    
    if notification_index == -1:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    # Remove the notification
    del notifications[notification_index]
    save_notifications(notifications)
    
    return {"message": "Notification deleted successfully"}
