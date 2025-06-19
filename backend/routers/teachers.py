from fastapi import APIRouter, Depends, HTTPException, status
from security import get_current_active_user, is_admin
from models import UserRole, TeacherInfo
import os
import json
import uuid
from datetime import datetime
from typing import List

router = APIRouter()

# Define file paths
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data_dir = os.path.join(current_dir, 'data')
USERS_FILE = os.path.join(data_dir, 'users.json')


def get_all_teachers():
    """Get all teachers from the database"""
    try:
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, 'r') as f:
                users = json.load(f)
                return [user for user in users if user.get("role") in [UserRole.TEACHER, UserRole.CLASS_TEACHER]]
    except Exception as e:
        print(f"Error fetching teachers: {e}")
    return []


def save_users(users):
    """Save users to the database file"""
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=4)


def get_teacher_by_id(teacher_id: str):
    """Get a teacher by ID"""
    try:
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, 'r') as f:
                users = json.load(f)
                for user in users:
                    if user.get("id") == teacher_id and user.get("role") in [UserRole.TEACHER, UserRole.CLASS_TEACHER]:
                        return user
    except Exception as e:
        print(f"Error fetching teacher: {e}")
    return None


@router.get("/")
async def get_teachers(current_user: dict = Depends(get_current_active_user)):
    """Get all teachers (accessible by admin or teachers)"""
    if current_user.get("role") not in [UserRole.ADMIN, UserRole.CLASS_TEACHER, UserRole.TEACHER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view teachers"
        )
    
    teachers = get_all_teachers()
    return teachers


@router.get("/{teacher_id}")
async def get_teacher(
    teacher_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    """Get a specific teacher by ID"""
    # Teachers can only access their own information unless they're admin
    if (not is_admin(current_user) and 
        current_user.get("role") in [UserRole.TEACHER, UserRole.CLASS_TEACHER] and 
        current_user.get("id") != teacher_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this teacher"
        )
    
    teacher = get_teacher_by_id(teacher_id)
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher not found"
        )
    
    return teacher


@router.post("/")
async def create_teacher(
    teacher_info: TeacherInfo,
    is_class_teacher: bool = False,
    email: str = None,
    full_name: str = None,
    current_user: dict = Depends(get_current_active_user)
):
    """Create a new teacher (accessible only by admin)"""
    if not is_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create teachers"
        )
    
    if not email or not full_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email and full name are required"
        )
    
    # Load existing users
    with open(USERS_FILE, 'r') as f:
        users = json.load(f)
    
    # Check if email already exists
    for user in users:
        if user.get("email") == email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User with email {email} already exists"
            )
    
    # Create new teacher
    from security import get_password_hash
    
    teacher_id = str(uuid.uuid4())
    
    new_teacher = {
        "id": teacher_id,
        "email": email,
        "full_name": full_name,
        "hashed_password": get_password_hash("teacher123"),  # Default password
        "role": UserRole.CLASS_TEACHER if is_class_teacher else UserRole.TEACHER,
        "is_active": True,
        "created_at": datetime.now().isoformat(),
        "teacher_info": teacher_info.dict()
    }
    
    users.append(new_teacher)
    save_users(users)
    
    return {"message": "Teacher created successfully", "teacher_id": teacher_id}
