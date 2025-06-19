from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import JSONResponse
from security import get_current_active_user, is_teacher
from models import UserRole
import os
import json
import uuid
import shutil
from datetime import datetime
import cv2
import numpy as np
import io
from PIL import Image
from typing import List, Optional
import base64

# Import face recognition functions
try:
    from deepface import DeepFace
except ImportError:
    # If not installed, we'll show appropriate error messages when functions are called
    pass

router = APIRouter()

# Define file paths
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data_dir = os.path.join(current_dir, 'data')
USERS_FILE = os.path.join(data_dir, 'users.json')
ATTENDANCE_DIR = os.path.join(data_dir, 'attendance')
STUDENT_IMAGES_DIR = os.path.join(data_dir, 'student_images')
TEMP_DIR = os.path.join(data_dir, 'temp')
ATTENDANCE_HISTORY_FILE = os.path.join(data_dir, 'attendance_history.json')

# Ensure directories exist
for directory in [ATTENDANCE_DIR, STUDENT_IMAGES_DIR, TEMP_DIR]:
    os.makedirs(directory, exist_ok=True)

# Initialize attendance history file if it doesn't exist
if not os.path.exists(ATTENDANCE_HISTORY_FILE):
    with open(ATTENDANCE_HISTORY_FILE, 'w') as f:
        json.dump([], f)


def get_students_by_class(department, year, division):
    """Get students filtered by department, year, and division"""
    try:
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, 'r') as f:
                users = json.load(f)
                students = []
                for user in users:
                    if user.get("role") == UserRole.STUDENT:
                        student_info = user.get("student_info", {})
                        if (student_info.get("department") == department and
                            student_info.get("year") == year and
                            student_info.get("division") == division):
                            students.append(user)
                return students
    except Exception as e:
        print(f"Error fetching students: {e}")
    return []


def save_attendance_record(record):
    """Save attendance record to history file"""
    try:
        with open(ATTENDANCE_HISTORY_FILE, 'r') as f:
            history = json.load(f)
        
        history.append(record)
        
        with open(ATTENDANCE_HISTORY_FILE, 'w') as f:
            json.dump(history, f, indent=4)
            
        return True
    except Exception as e:
        print(f"Error saving attendance record: {e}")
        return False


def save_attendance_to_csv(attendance_data, department, year, division, date):
    """Save attendance data to a CSV file"""
    filename = f"attendance_{department}_{year}_{division}_{date}.csv"
    file_path = os.path.join(ATTENDANCE_DIR, filename)
    
    header = "Student ID,Name,Present\n"
    rows = []
    
    for student in attendance_data:
        student_id = student.get("student_id", "")
        name = student.get("name", "")
        present = "1" if student.get("present", False) else "0"
        rows.append(f"{student_id},{name},{present}")
    
    with open(file_path, 'w') as f:
        f.write(header)
        f.write("\n".join(rows))
    
    return filename


def recognize_faces(image_bytes, confidence_threshold=0.5):
    """
    Recognize faces in an image by comparing with student photos
    Returns a list of recognized student IDs
    """
    try:
        # Check if DeepFace is available
        if 'DeepFace' not in globals():
            raise ImportError("DeepFace module not installed")
        
        # Load the image
        image = Image.open(io.BytesIO(image_bytes))
        image_np = np.array(image)
        
        # Convert to BGR for OpenCV
        if len(image_np.shape) == 3 and image_np.shape[2] == 3:
            image_np = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)
        
        # Save temporary image
        temp_img_path = os.path.join(TEMP_DIR, "class_photo.jpg")
        cv2.imwrite(temp_img_path, image_np)
        
        # Get all student images for comparison
        recognized_students = []
        
        # Check all student photos in the directory
        student_photos = [f for f in os.listdir(STUDENT_IMAGES_DIR) if f.endswith(('.jpg', '.jpeg', '.png'))]
        
        for photo in student_photos:
            student_img_path = os.path.join(STUDENT_IMAGES_DIR, photo)
            
            try:
                # Compare the images using DeepFace
                result = DeepFace.verify(
                    img1_path=temp_img_path,
                    img2_path=student_img_path,
                    enforce_detection=False,
                    model_name="VGG-Face"
                )
                
                if result["verified"] and result.get("distance", 1.0) < confidence_threshold:
                    # Get student ID from photo name
                    student_name = os.path.splitext(photo)[0].replace('_', ' ')
                    
                    # Find the student by name in users.json
                    with open(USERS_FILE, 'r') as f:
                        users = json.load(f)
                        
                    for user in users:
                        if (user.get("role") == UserRole.STUDENT and 
                            user.get("full_name", "").lower() == student_name):
                            recognized_students.append({
                                "student_id": user.get("student_info", {}).get("student_id"),
                                "name": user.get("full_name"),
                                "confidence": 1.0 - result.get("distance", 0)
                            })
                            break
                    
            except Exception as e:
                print(f"Error comparing with {photo}: {e}")
        
        return recognized_students
    
    except ImportError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Face recognition module not available. Please install deepface."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error recognizing faces: {str(e)}"
        )


@router.get("/history")
async def get_attendance_history(
    department: Optional[str] = None,
    year: Optional[str] = None,
    division: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: dict = Depends(get_current_active_user)
):
    """Get attendance history with optional filters"""
    if current_user.get("role") not in [UserRole.ADMIN, UserRole.TEACHER, UserRole.CLASS_TEACHER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view attendance history"
        )
    
    try:
        with open(ATTENDANCE_HISTORY_FILE, 'r') as f:
            history = json.load(f)
        
        # Apply filters
        filtered_history = history
        
        if department:
            filtered_history = [h for h in filtered_history if h.get("department") == department]
            
        if year:
            filtered_history = [h for h in filtered_history if h.get("year") == year]
            
        if division:
            filtered_history = [h for h in filtered_history if h.get("division") == division]
            
        if start_date:
            filtered_history = [h for h in filtered_history if h.get("date", "") >= start_date]
            
        if end_date:
            filtered_history = [h for h in filtered_history if h.get("date", "") <= end_date]
        
        return filtered_history
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching attendance history: {str(e)}"
        )


@router.post("/take")
async def take_attendance(
    department: str,
    year: str,
    division: str,
    subject: str,
    photo: UploadFile = File(...),
    current_user: dict = Depends(get_current_active_user)
):
    """Take attendance using facial recognition"""
    if not is_teacher(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to take attendance"
        )
    
    try:
        # Read the uploaded image
        image_bytes = await photo.read()
        
        # Recognize faces in the image
        recognized_students = recognize_faces(image_bytes)
        
        # Get all students in the class
        class_students = get_students_by_class(department, year, division)
        
        # Create attendance data
        today = datetime.now().strftime("%Y-%m-%d")
        attendance_data = []
        
        recognized_ids = [student["student_id"] for student in recognized_students]
        
        for student in class_students:
            student_info = student.get("student_info", {})
            student_id = student_info.get("student_id")
            
            attendance_data.append({
                "student_id": student_id,
                "name": student.get("full_name"),
                "present": student_id in recognized_ids
            })
        
        # Save attendance to CSV
        csv_filename = save_attendance_to_csv(attendance_data, department, year, division, today)
        
        # Save attendance record to history
        record = {
            "id": str(uuid.uuid4()),
            "date": today,
            "department": department,
            "year": year,
            "division": division,
            "subject": subject,
            "teacher_id": current_user.get("id"),
            "teacher_name": current_user.get("full_name"),
            "attendance_file": csv_filename,
            "present_count": sum(1 for student in attendance_data if student["present"]),
            "total_count": len(attendance_data)
        }
        
        save_attendance_record(record)
        
        return {
            "message": "Attendance taken successfully",
            "date": today,
            "attendance_data": attendance_data,
            "recognized_students": recognized_students,
            "record_id": record["id"]
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error taking attendance: {str(e)}"
        )


@router.post("/manual")
async def manual_attendance(
    department: str,
    year: str,
    division: str,
    subject: str,
    attendance_data: List[dict],
    current_user: dict = Depends(get_current_active_user)
):
    """Manually take attendance"""
    if not is_teacher(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to take attendance"
        )
    
    try:
        # Validate attendance data
        for item in attendance_data:
            if "student_id" not in item or "present" not in item:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid attendance data format"
                )
        
        # Save attendance to CSV
        today = datetime.now().strftime("%Y-%m-%d")
        csv_filename = save_attendance_to_csv(attendance_data, department, year, division, today)
        
        # Save attendance record to history
        record = {
            "id": str(uuid.uuid4()),
            "date": today,
            "department": department,
            "year": year,
            "division": division,
            "subject": subject,
            "teacher_id": current_user.get("id"),
            "teacher_name": current_user.get("full_name"),
            "attendance_file": csv_filename,
            "present_count": sum(1 for student in attendance_data if student["present"]),
            "total_count": len(attendance_data),
            "is_manual": True
        }
        
        save_attendance_record(record)
        
        return {
            "message": "Attendance recorded successfully",
            "date": today,
            "record_id": record["id"]
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error recording attendance: {str(e)}"
        )
