from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from typing import List, Optional
import os
import uuid
from datetime import datetime

from models import User, StudentInfo, Role
from security import get_current_active_user, is_admin, is_class_teacher
import database as db

router = APIRouter(tags=["student-management"])

# Define file paths
current_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(current_dir, 'data')
base_dirs = {
    'student_images': os.path.join(data_dir, 'student_images'),
}


@router.post("/students")
async def register_student(
    name: str = Form(...),
    student_id: str = Form(...),
    department: str = Form(...),
    year: str = Form(...),
    division: str = Form(...),
    subjects: List[str] = Form(...),
    photo: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user)
):
    """
    Register a new student
    Only admin or class teachers can register students
    """
    if not (is_admin(current_user) or is_class_teacher(current_user)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators and class teachers can register students"
        )
    
    try:
        # Save student photo
        filename = f"{name.lower().replace(' ', '_')}.jpg"
        filepath = os.path.join(base_dirs['student_images'], filename)
        
        # Read and save image
        contents = await photo.read()
        with open(filepath, "wb") as f:
            f.write(contents)
        
        # Update storage
        storage = db.load_storage()
        
        # Add to students list if not already there
        if filename not in storage['students']:
            storage['students'].append(filename)
        
        # Add to students_data
        student_data = {
            'name': name,
            'id': student_id,
            'department': department,
            'year': year,
            'division': division,
            'subjects': subjects,
            'photo': filename,
            'registered_date': datetime.now().strftime("%Y-%m-%d"),
            'registered_by': current_user.get('id')
        }
        
        # Initialize students_data if not exists
        if 'students_data' not in storage:
            storage['students_data'] = {}
        
        storage['students_data'][filename] = student_data
        db.save_storage(storage)
        
        return {
            "name": name,
            "student_id": student_id,
            "department": department,
            "year": year,
            "division": division,
            "subjects": subjects,
            "photo": filename
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/students")
async def get_students(
    department: Optional[str] = None,
    year: Optional[str] = None,
    division: Optional[str] = None,
    current_user: User = Depends(get_current_active_user)
):
    """Get list of registered students with optional filtering"""
    storage = db.load_storage()
    
    if 'students_data' not in storage:
        return []
    
    students = []
    for filename, data in storage['students_data'].items():
        # Apply filters
        if department and data.get('department') != department:
            continue
        if year and data.get('year') != year:
            continue
        if division and data.get('division') != division:
            continue
        
        # Add to results
        students.append({
            'name': data.get('name'),
            'student_id': data.get('id'),
            'department': data.get('department'),
            'year': data.get('year'),
            'division': data.get('division'),
            'subjects': data.get('subjects', []),
            'photo': filename,
            'registered_date': data.get('registered_date')
        })
    
    return students


@router.get("/students/{student_id}")
async def get_student(
    student_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific student by ID"""
    storage = db.load_storage()
    
    if 'students_data' not in storage:
        raise HTTPException(status_code=404, detail="Student not found")
    
    for filename, data in storage['students_data'].items():
        if data.get('id') == student_id:
            return {
                'name': data.get('name'),
                'student_id': data.get('id'),
                'department': data.get('department'),
                'year': data.get('year'),
                'division': data.get('division'),
                'subjects': data.get('subjects', []),
                'photo': filename,
                'registered_date': data.get('registered_date')
            }
    
    raise HTTPException(status_code=404, detail="Student not found")


@router.put("/students/{student_id}")
async def update_student(
    student_id: str,
    name: Optional[str] = Form(None),
    department: Optional[str] = Form(None),
    year: Optional[str] = Form(None),
    division: Optional[str] = Form(None),
    subjects: Optional[List[str]] = Form(None),
    photo: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update student information
    Only admin or class teachers can update students
    """
    if not (is_admin(current_user) or is_class_teacher(current_user)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators and class teachers can update students"
        )
    
    storage = db.load_storage()
    
    if 'students_data' not in storage:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Find the student
    target_filename = None
    for filename, data in storage['students_data'].items():
        if data.get('id') == student_id:
            target_filename = filename
            break
    
    if not target_filename:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Update student data
    student_data = storage['students_data'][target_filename]
    
    if name:
        student_data['name'] = name
    if department:
        student_data['department'] = department
    if year:
        student_data['year'] = year
    if division:
        student_data['division'] = division
    if subjects:
        student_data['subjects'] = subjects
    
    # Handle photo update
    if photo:
        try:
            # If name has changed, update filename
            if name and name.lower().replace(' ', '_') != target_filename.split('.')[0]:
                # Remove old file reference from students list
                if target_filename in storage['students']:
                    storage['students'].remove(target_filename)
                
                # Create new filename
                new_filename = f"{name.lower().replace(' ', '_')}.jpg"
                
                # Save new image
                contents = await photo.read()
                filepath = os.path.join(base_dirs['student_images'], new_filename)
                with open(filepath, "wb") as f:
                    f.write(contents)
                
                # Add new file to students list
                storage['students'].append(new_filename)
                
                # Copy data to new filename
                storage['students_data'][new_filename] = student_data
                storage['students_data'][new_filename]['photo'] = new_filename
                
                # Delete old entry
                del storage['students_data'][target_filename]
                target_filename = new_filename
            else:
                # Just update existing photo
                contents = await photo.read()
                filepath = os.path.join(base_dirs['student_images'], target_filename)
                with open(filepath, "wb") as f:
                    f.write(contents)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error updating photo: {str(e)}")
    
    # Save updates
    db.save_storage(storage)
    
    return {
        'name': student_data.get('name'),
        'student_id': student_data.get('id'),
        'department': student_data.get('department'),
        'year': student_data.get('year'),
        'division': student_data.get('division'),
        'subjects': student_data.get('subjects', []),
        'photo': target_filename,
        'registered_date': student_data.get('registered_date')
    }


@router.delete("/students/{student_id}")
async def delete_student(
    student_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete a student
    Only admin or class teachers can delete students
    """
    if not (is_admin(current_user) or is_class_teacher(current_user)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators and class teachers can delete students"
        )
    
    storage = db.load_storage()
    
    if 'students_data' not in storage:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Find the student
    target_filename = None
    for filename, data in storage['students_data'].items():
        if data.get('id') == student_id:
            target_filename = filename
            break
    
    if not target_filename:
        raise HTTPException(status_code=404, detail="Student not found")
    
    try:
        # Remove file from disk
        filepath = os.path.join(base_dirs['student_images'], target_filename)
        if os.path.exists(filepath):
            os.remove(filepath)
        
        # Remove from students list
        if target_filename in storage['students']:
            storage['students'].remove(target_filename)
        
        # Remove from students_data
        if target_filename in storage['students_data']:
            del storage['students_data'][target_filename]
        
        # Save changes
        db.save_storage(storage)
        
        return {"detail": "Student deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting student: {str(e)}")
