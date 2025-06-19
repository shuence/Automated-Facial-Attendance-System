from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from security import get_current_active_user, is_admin, is_class_teacher
from models import UserRole, StudentInfo
import os
import json
import uuid
import shutil
from typing import List

router = APIRouter()

# Define file paths
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data_dir = os.path.join(current_dir, 'data')
USERS_FILE = os.path.join(data_dir, 'users.json')
STUDENT_IMAGES_DIR = os.path.join(data_dir, 'student_images')

# Ensure directories exist
os.makedirs(STUDENT_IMAGES_DIR, exist_ok=True)


def get_all_students():
    """Get all students from the database"""
    try:
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, 'r') as f:
                users = json.load(f)
                return [user for user in users if user.get("role") == UserRole.STUDENT]
    except Exception as e:
        print(f"Error fetching students: {e}")
    return []


def save_users(users):
    """Save users to the database file"""
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=4)


def get_student_by_id(student_id: str):
    """Get a student by ID"""
    try:
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, 'r') as f:
                users = json.load(f)
                for user in users:
                    if user.get("id") == student_id and user.get("role") == UserRole.STUDENT:
                        return user
    except Exception as e:
        print(f"Error fetching student: {e}")
    return None


@router.get("/")
async def get_students(current_user: dict = Depends(get_current_active_user)):
    """Get all students (accessible by admin, class teacher, or teacher)"""
    if current_user.get("role") not in [UserRole.ADMIN, UserRole.CLASS_TEACHER, UserRole.TEACHER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view students"
        )
    
    students = get_all_students()
    return students


@router.get("/{student_id}")
async def get_student(
    student_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    """Get a specific student by ID"""
    # Student can only access their own information
    if (current_user.get("role") == UserRole.STUDENT and 
        current_user.get("id") != student_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this student"
        )
    
    student = get_student_by_id(student_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    
    return student


@router.post("/")
async def create_student(
    student_info: StudentInfo,
    current_user: dict = Depends(get_current_active_user)
):
    """Create a new student (accessible only by admin or class teacher)"""
    if not is_admin(current_user) and not is_class_teacher(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create students"
        )
    
    # Load existing users
    with open(USERS_FILE, 'r') as f:
        users = json.load(f)
    
    # Check if student ID already exists
    for user in users:
        if (user.get("role") == UserRole.STUDENT and 
            user.get("student_info", {}).get("student_id") == student_info.student_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Student with ID {student_info.student_id} already exists"
            )
    
    # Create new student
    from security import get_password_hash
    
    student_id = str(uuid.uuid4())
    email = f"{student_info.student_id.lower()}@dietms.org"
    
    new_student = {
        "id": student_id,
        "email": email,
        "full_name": student_info.name,
        "hashed_password": get_password_hash("student123"),  # Default password
        "role": UserRole.STUDENT,
        "is_active": True,
        "created_at": datetime.datetime.now().isoformat(),
        "student_info": student_info.dict()
    }
    
    users.append(new_student)
    save_users(users)
    
    return {"message": "Student created successfully", "student_id": student_id}


@router.post("/{student_id}/upload-photo")
async def upload_student_photo(
    student_id: str,
    photo: UploadFile = File(...),
    current_user: dict = Depends(get_current_active_user)
):
    """Upload a photo for a student"""
    # Check authorization
    if (not is_admin(current_user) and 
        not is_class_teacher(current_user) and
        (current_user.get("role") != UserRole.STUDENT or current_user.get("id") != student_id)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to upload photo for this student"
        )
    
    # Check if student exists
    student = get_student_by_id(student_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    
    # Save photo
    try:
        # Create a filename based on student name (lowercase, spaces replaced with underscores)
        filename = f"{student['full_name'].lower().replace(' ', '_')}.jpg"
        file_path = os.path.join(STUDENT_IMAGES_DIR, filename)
        
        # Save the uploaded file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(photo.file, buffer)
        
        # Update student info with photo filename
        with open(USERS_FILE, 'r') as f:
            users = json.load(f)
        
        for user in users:
            if user.get("id") == student_id:
                if "student_info" not in user:
                    user["student_info"] = {}
                user["student_info"]["photo_filename"] = filename
                break
        
        save_users(users)
        
        return {"message": "Photo uploaded successfully", "filename": filename}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading photo: {str(e)}"
        )
