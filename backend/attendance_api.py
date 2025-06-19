from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form, BackgroundTasks
from typing import List, Optional, Dict, Any
from datetime import datetime
import cv2
import numpy as np
import os
import io
from PIL import Image
import json

from models import User, UserRole
from security import get_current_active_user, is_admin, is_teacher
import database as db
from deepface.DeepFace import verify, extract_faces

router = APIRouter(tags=["attendance"])

# Define file paths
current_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(current_dir, 'data')
base_dirs = {
    'student_images': os.path.join(data_dir, 'student_images'),
    'attendance': os.path.join(data_dir, 'attendance'),
    'temp': os.path.join(data_dir, 'temp')
}

# Ensure directories exist
for dir_path in base_dirs.values():
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)


def process_face(face_img):
    """Process face array to ensure correct format"""
    try:
        if isinstance(face_img, dict) and 'face' in face_img and isinstance(face_img['face'], np.ndarray):
            face_img = face_img['face']
        
        if not isinstance(face_img, np.ndarray):
            face_img = np.array(face_img)
        
        if face_img.dtype != np.uint8:
            if face_img.dtype in [np.float32, np.float64]:
                face_img = (face_img * 255).astype(np.uint8)
            else:
                face_img = face_img.astype(np.uint8)
        
        if len(face_img.shape) == 3 and face_img.shape[2] == 3:
            if not hasattr(face_img, 'color_format') or face_img.color_format != 'BGR':
                face_img = cv2.cvtColor(face_img, cv2.COLOR_RGB2BGR)
        elif len(face_img.shape) == 2:
            face_img = cv2.cvtColor(face_img, cv2.COLOR_GRAY2BGR)
        
        face_img = cv2.fastNlMeansDenoisingColored(face_img, None, 10, 10, 7, 21)
        face_img = cv2.detailEnhance(face_img, sigma_s=10, sigma_r=0.15)
            
        return face_img
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing face: {str(e)}")


def verify_face(img1_path: str, img2_path: str) -> dict:
    """Compare two face images using ArcFace"""
    try:
        img1 = cv2.imread(img1_path)
        img2 = cv2.imread(img2_path)
        
        if img1 is None or img2 is None:
            raise ValueError("Could not load images")
        
        result = verify(
            img1_path=img1_path,
            img2_path=img2_path,
            model_name='ArcFace',
            detector_backend='retinaface',
            enforce_detection=False,
            distance_metric='cosine',
            align=True,
            normalization='base'
        )
        
        similarity = (1 - result['distance']) * 100
        return {
            'verified': similarity >= 50,
            'similarity': similarity,
            'distance': result['distance'],
            'model': 'ArcFace'
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Face verification error: {str(e)}")


@router.post("/attendance")
async def take_attendance(
    department: str = Form(...),
    year: str = Form(...),
    division: str = Form(...),
    subject: str = Form(...),
    time_slot: str = Form(...),
    photos: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_active_user)
):
    """
    Take attendance using face recognition
    Only teachers or admins can take attendance
    """
    if not (is_admin(current_user) or is_teacher(current_user)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators and teachers can take attendance"
        )
    
    try:
        results = []
        all_students = []
        photo_number = 1
        
        # Load all students
        storage = db.load_storage()
        if 'students_data' in storage:
            for filename, data in storage['students_data'].items():
                # Filter by class info
                if (data.get('department') == department and 
                    data.get('year') == year and 
                    data.get('division') == division and
                    subject in data.get('subjects', [])):
                    
                    all_students.append({
                        'name': data.get('name'),
                        'student_id': data.get('id'),
                        'filename': filename
                    })
        
        # Process each uploaded photo
        for photo in photos:
            # Save uploaded photo temporarily
            contents = await photo.read()
            temp_path = os.path.join(base_dirs['temp'], f"class_{photo_number}.jpg")
            with open(temp_path, "wb") as f:
                f.write(contents)
            
            # Detect faces
            faces = extract_faces(
                img_path=temp_path,
                enforce_detection=False,
                detector_backend='retinaface',
                align=True
            )
            
            # Process each face in the photo
            face_idx = 0
            for face in faces:
                processed_face = process_face(face)
                if processed_face is not None:
                    face_path = os.path.join(base_dirs['temp'], f"face_{photo_number}_{face_idx}.jpg")
                    cv2.imwrite(face_path, processed_face)
                    
                    # Compare with all students
                    for student in all_students:
                        student_path = os.path.join(base_dirs['student_images'], student['filename'])
                        result = verify_face(face_path, student_path)
                        
                        if result and result['verified']:
                            # Check if student already marked as present with higher confidence
                            existing_result = next((r for r in results if r['student_name'] == student['name']), None)
                            
                            if existing_result is None or result['similarity'] > existing_result['confidence']:
                                # If this is a better match, replace or add
                                if existing_result:
                                    results.remove(existing_result)
                                
                                results.append({
                                    'student_name': student['name'],
                                    'student_id': student['student_id'],
                                    'status': 'Present',
                                    'confidence': result['similarity'],
                                    'photo_number': photo_number,
                                    'face_number': face_idx,
                                    'model': 'ArcFace',
                                    'manually_corrected': False
                                })
                
                face_idx += 1
            
            photo_number += 1
        
        # Add absent students
        present_student_ids = [r['student_id'] for r in results]
        for student in all_students:
            if student['student_id'] not in present_student_ids:
                results.append({
                    'student_name': student['name'],
                    'student_id': student['student_id'],
                    'status': 'Absent',
                    'confidence': 0.0,
                    'model': 'ArcFace',
                    'manually_corrected': False
                })
        
        # Create attendance record
        attendance_record = {
            'date': datetime.now().strftime("%Y-%m-%d"),
            'time': datetime.now().strftime("%H:%M:%S"),
            'department': department,
            'year': year,
            'division': division,
            'subject': subject,
            'time_slot': time_slot,
            'records': results,
            'taken_by': current_user.get('id')
        }
        
        # Save attendance record
        attendance_history = db.load_attendance_history()
        attendance_history.append(attendance_record)
        db.save_attendance_history(attendance_history)
        
        return attendance_record
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/attendance/history")
async def get_attendance_history(
    date: Optional[str] = None,
    department: Optional[str] = None,
    year: Optional[str] = None,
    division: Optional[str] = None,
    subject: Optional[str] = None,
    current_user: User = Depends(get_current_active_user)
):
    """Get attendance history with optional filtering"""
    attendance_history = db.load_attendance_history()
    
    # Apply filters
    filtered_history = attendance_history
    
    if date:
        filtered_history = [h for h in filtered_history if h.get('date') == date]
    if department:
        filtered_history = [h for h in filtered_history if h.get('department') == department]
    if year:
        filtered_history = [h for h in filtered_history if h.get('year') == year]
    if division:
        filtered_history = [h for h in filtered_history if h.get('division') == division]
    if subject:
        filtered_history = [h for h in filtered_history if h.get('subject') == subject]
    
    return filtered_history


@router.get("/attendance/stats")
async def get_attendance_stats(
    department: Optional[str] = None,
    year: Optional[str] = None,
    division: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: User = Depends(get_current_active_user)
):
    """Get attendance statistics"""
    attendance_history = db.load_attendance_history()
    
    # Apply filters
    filtered_history = attendance_history
    
    if department:
        filtered_history = [h for h in filtered_history if h.get('department') == department]
    if year:
        filtered_history = [h for h in filtered_history if h.get('year') == year]
    if division:
        filtered_history = [h for h in filtered_history if h.get('division') == division]
    if start_date:
        filtered_history = [h for h in filtered_history if h.get('date', '') >= start_date]
    if end_date:
        filtered_history = [h for h in filtered_history if h.get('date', '') <= end_date]
    
    # Calculate statistics
    if not filtered_history:
        return {"detail": "No attendance records found"}
    
    # Compile student attendance stats
    student_stats = {}
    total_sessions = len(filtered_history)
    
    for record in filtered_history:
        for student in record.get('records', []):
            student_id = student.get('student_id')
            student_name = student.get('student_name')
            
            if student_id not in student_stats:
                student_stats[student_id] = {
                    'student_id': student_id,
                    'student_name': student_name,
                    'present': 0,
                    'absent': 0,
                    'total': 0
                }
            
            student_stats[student_id]['total'] += 1
            
            if student.get('status') == 'Present':
                student_stats[student_id]['present'] += 1
            else:
                student_stats[student_id]['absent'] += 1
    
    # Calculate percentages
    for student_id, stats in student_stats.items():
        if stats['total'] > 0:
            stats['attendance_percentage'] = (stats['present'] / stats['total']) * 100
        else:
            stats['attendance_percentage'] = 0
    
    # Compile session stats
    session_stats = []
    for record in filtered_history:
        present_count = sum(1 for s in record.get('records', []) if s.get('status') == 'Present')
        total_count = len(record.get('records', []))
        attendance_percentage = (present_count / total_count) * 100 if total_count > 0 else 0
        
        session_stats.append({
            'date': record.get('date'),
            'time': record.get('time'),
            'subject': record.get('subject'),
            'time_slot': record.get('time_slot'),
            'present': present_count,
            'total': total_count,
            'attendance_percentage': attendance_percentage
        })
    
    return {
        'total_sessions': total_sessions,
        'student_stats': list(student_stats.values()),
        'session_stats': session_stats
    }


@router.put("/attendance/{date}/{time}")
async def update_attendance(
    date: str,
    time: str,
    updates: List[Dict[str, Any]],
    current_user: User = Depends(get_current_active_user)
):
    """
    Update attendance records
    Only teachers or admins can update attendance
    """
    if not (is_admin(current_user) or is_teacher(current_user)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators and teachers can update attendance"
        )
    
    attendance_history = db.load_attendance_history()
    
    # Find the specific attendance record
    for i, record in enumerate(attendance_history):
        if record.get('date') == date and record.get('time') == time:
            # Apply updates
            for update in updates:
                student_id = update.get('student_id')
                status = update.get('status')
                
                if not student_id or not status:
                    continue
                
                # Find the student in the records
                for j, student_record in enumerate(record.get('records', [])):
                    if student_record.get('student_id') == student_id:
                        # Update the record
                        attendance_history[i]['records'][j]['status'] = status
                        attendance_history[i]['records'][j]['manually_corrected'] = True
                        break
            
            # Save changes
            db.save_attendance_history(attendance_history)
            return {"detail": "Attendance updated successfully"}
    
    raise HTTPException(status_code=404, detail="Attendance record not found")


@router.delete("/attendance/{date}/{time}")
async def delete_attendance(
    date: str,
    time: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete an attendance record
    Only admins can delete attendance records
    """
    if not is_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can delete attendance records"
        )
    
    attendance_history = db.load_attendance_history()
    
    # Find and remove the record
    initial_count = len(attendance_history)
    attendance_history = [
        record for record in attendance_history 
        if not (record.get('date') == date and record.get('time') == time)
    ]
    
    if len(attendance_history) < initial_count:
        db.save_attendance_history(attendance_history)
        return {"detail": "Attendance record deleted successfully"}
    
    raise HTTPException(status_code=404, detail="Attendance record not found")
