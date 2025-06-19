from fastapi import APIRouter, Depends, HTTPException, status
from security import get_current_active_user, is_admin, is_teacher
from models import UserRole
import os
import json
from datetime import datetime, timedelta
from typing import List, Optional
import pandas as pd
import calendar

router = APIRouter()

# Define file paths
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data_dir = os.path.join(current_dir, 'data')
USERS_FILE = os.path.join(data_dir, 'users.json')
ATTENDANCE_HISTORY_FILE = os.path.join(data_dir, 'attendance_history.json')
ATTENDANCE_DIR = os.path.join(data_dir, 'attendance')


def load_attendance_history():
    """Load attendance history from file"""
    if os.path.exists(ATTENDANCE_HISTORY_FILE):
        with open(ATTENDANCE_HISTORY_FILE, 'r') as f:
            return json.load(f)
    return []


def get_student_attendance(student_id: str):
    """Get attendance records for a specific student"""
    attendance_history = load_attendance_history()
    student_attendance = []
    
    for record in attendance_history:
        # Get the attendance file for this record
        attendance_file = os.path.join(ATTENDANCE_DIR, record.get("attendance_file", ""))
        if os.path.exists(attendance_file):
            try:
                # Read the CSV file
                df = pd.read_csv(attendance_file)
                
                # Find the student in this attendance record
                student_row = df[df["Student ID"] == student_id]
                if not student_row.empty:
                    present = student_row["Present"].values[0] == 1
                    
                    student_attendance.append({
                        "date": record.get("date"),
                        "subject": record.get("subject"),
                        "teacher_name": record.get("teacher_name"),
                        "present": present
                    })
            except Exception as e:
                print(f"Error reading attendance file: {e}")
    
    return student_attendance


@router.get("/student/{student_id}")
async def get_student_dashboard(
    student_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    """Get dashboard data for a specific student"""
    # Check if the user is the student or an admin/teacher
    if (current_user.get("role") == UserRole.STUDENT and 
        current_user.get("id") != student_id and
        not is_admin(current_user) and 
        not is_teacher(current_user)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this student's dashboard"
        )
    
    # Get student details
    with open(USERS_FILE, 'r') as f:
        users = json.load(f)
    
    student = None
    for user in users:
        if user.get("id") == student_id and user.get("role") == UserRole.STUDENT:
            student = user
            break
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    
    # Get student attendance
    student_info = student.get("student_info", {})
    attendance_records = get_student_attendance(student_info.get("student_id"))
    
    # Calculate attendance statistics
    today = datetime.now().date()
    this_month_records = [r for r in attendance_records 
                         if datetime.strptime(r.get("date"), "%Y-%m-%d").date().month == today.month]
    
    total_classes = len(this_month_records)
    attended_classes = sum(1 for r in this_month_records if r.get("present"))
    
    attendance_percentage = (attended_classes / total_classes * 100) if total_classes > 0 else 0
    
    # Get last 10 attendance records
    recent_attendance = sorted(attendance_records, 
                              key=lambda x: x.get("date"), 
                              reverse=True)[:10]
    
    # Group attendance by subject
    subject_attendance = {}
    for record in attendance_records:
        subject = record.get("subject")
        if subject not in subject_attendance:
            subject_attendance[subject] = {"total": 0, "present": 0}
        
        subject_attendance[subject]["total"] += 1
        if record.get("present"):
            subject_attendance[subject]["present"] += 1
    
    # Calculate percentage for each subject
    for subject in subject_attendance:
        total = subject_attendance[subject]["total"]
        present = subject_attendance[subject]["present"]
        subject_attendance[subject]["percentage"] = (present / total * 100) if total > 0 else 0
    
    return {
        "student_id": student_info.get("student_id"),
        "name": student.get("full_name"),
        "department": student_info.get("department"),
        "year": student_info.get("year"),
        "division": student_info.get("division"),
        "attendance_summary": {
            "this_month": {
                "total_classes": total_classes,
                "attended_classes": attended_classes,
                "attendance_percentage": attendance_percentage
            },
            "by_subject": subject_attendance
        },
        "recent_attendance": recent_attendance
    }


@router.get("/teacher/{teacher_id}")
async def get_teacher_dashboard(
    teacher_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    """Get dashboard data for a specific teacher"""
    # Check if the user is the teacher or an admin
    if (current_user.get("role") in [UserRole.TEACHER, UserRole.CLASS_TEACHER] and 
        current_user.get("id") != teacher_id and
        not is_admin(current_user)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this teacher's dashboard"
        )
    
    # Get teacher details
    with open(USERS_FILE, 'r') as f:
        users = json.load(f)
    
    teacher = None
    for user in users:
        if user.get("id") == teacher_id and user.get("role") in [UserRole.TEACHER, UserRole.CLASS_TEACHER]:
            teacher = user
            break
    
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher not found"
        )
    
    # Get attendance records taken by this teacher
    attendance_history = load_attendance_history()
    teacher_records = [r for r in attendance_history if r.get("teacher_id") == teacher_id]
    
    # Calculate statistics
    today = datetime.now().date()
    this_month = today.month
    this_year = today.year
    
    # Get records from this month
    this_month_records = [r for r in teacher_records 
                         if datetime.strptime(r.get("date"), "%Y-%m-%d").date().month == this_month]
    
    # Get records from last 30 days
    thirty_days_ago = today - timedelta(days=30)
    last_30_days_records = [r for r in teacher_records 
                           if datetime.strptime(r.get("date"), "%Y-%m-%d").date() >= thirty_days_ago]
    
    # Group records by subject
    subject_stats = {}
    for record in teacher_records:
        subject = record.get("subject")
        if subject not in subject_stats:
            subject_stats[subject] = {"total_sessions": 0, "total_students": 0, "present_students": 0}
        
        subject_stats[subject]["total_sessions"] += 1
        subject_stats[subject]["total_students"] += record.get("total_count", 0)
        subject_stats[subject]["present_students"] += record.get("present_count", 0)
    
    # Calculate average attendance for each subject
    for subject in subject_stats:
        total = subject_stats[subject]["total_students"]
        present = subject_stats[subject]["present_students"]
        subject_stats[subject]["average_attendance"] = (present / total * 100) if total > 0 else 0
    
    # Group by class (department, year, division)
    class_stats = {}
    for record in teacher_records:
        class_key = f"{record.get('department')}_{record.get('year')}_{record.get('division')}"
        if class_key not in class_stats:
            class_stats[class_key] = {
                "department": record.get("department"),
                "year": record.get("year"),
                "division": record.get("division"),
                "total_sessions": 0,
                "total_students": 0,
                "present_students": 0
            }
        
        class_stats[class_key]["total_sessions"] += 1
        class_stats[class_key]["total_students"] += record.get("total_count", 0)
        class_stats[class_key]["present_students"] += record.get("present_count", 0)
    
    # Calculate average attendance for each class
    for class_key in class_stats:
        total = class_stats[class_key]["total_students"]
        present = class_stats[class_key]["present_students"]
        class_stats[class_key]["average_attendance"] = (present / total * 100) if total > 0 else 0
    
    # Recent attendance sessions
    recent_sessions = sorted(teacher_records, 
                            key=lambda x: x.get("date"), 
                            reverse=True)[:10]
    
    return {
        "teacher_id": teacher.get("id"),
        "name": teacher.get("full_name"),
        "role": teacher.get("role"),
        "department": teacher.get("teacher_info", {}).get("department"),
        "summary": {
            "total_sessions": len(teacher_records),
            "this_month_sessions": len(this_month_records),
            "last_30_days_sessions": len(last_30_days_records)
        },
        "subject_stats": subject_stats,
        "class_stats": list(class_stats.values()),
        "recent_sessions": recent_sessions
    }


@router.get("/stats")
async def get_dashboard_stats(
    current_user: dict = Depends(get_current_active_user)
):
    """Get overall system statistics"""
    if not is_admin(current_user) and not is_teacher(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view system statistics"
        )
    
    # Get all users
    with open(USERS_FILE, 'r') as f:
        users = json.load(f)
    
    # Count users by role
    admin_count = sum(1 for user in users if user.get("role") == UserRole.ADMIN)
    class_teacher_count = sum(1 for user in users if user.get("role") == UserRole.CLASS_TEACHER)
    teacher_count = sum(1 for user in users if user.get("role") == UserRole.TEACHER)
    student_count = sum(1 for user in users if user.get("role") == UserRole.STUDENT)
    
    # Get attendance records
    attendance_history = load_attendance_history()
    
    # Calculate statistics
    today = datetime.now().date()
    this_month = today.month
    this_year = today.year
    
    # Get records from this month
    this_month_records = [r for r in attendance_history 
                         if datetime.strptime(r.get("date"), "%Y-%m-%d").date().month == this_month]
    
    # Monthly attendance trend (for the current year)
    monthly_trend = {}
    for month in range(1, 13):
        month_records = [r for r in attendance_history 
                        if datetime.strptime(r.get("date"), "%Y-%m-%d").date().month == month
                        and datetime.strptime(r.get("date"), "%Y-%m-%d").date().year == this_year]
        
        if month_records:
            total_students = sum(r.get("total_count", 0) for r in month_records)
            present_students = sum(r.get("present_count", 0) for r in month_records)
            avg_attendance = (present_students / total_students * 100) if total_students > 0 else 0
            
            monthly_trend[calendar.month_name[month]] = {
                "sessions": len(month_records),
                "average_attendance": avg_attendance
            }
    
    # Department-wise statistics
    department_stats = {}
    for record in attendance_history:
        dept = record.get("department")
        if dept not in department_stats:
            department_stats[dept] = {
                "total_sessions": 0,
                "total_students": 0,
                "present_students": 0
            }
        
        department_stats[dept]["total_sessions"] += 1
        department_stats[dept]["total_students"] += record.get("total_count", 0)
        department_stats[dept]["present_students"] += record.get("present_count", 0)
    
    # Calculate average attendance for each department
    for dept in department_stats:
        total = department_stats[dept]["total_students"]
        present = department_stats[dept]["present_students"]
        department_stats[dept]["average_attendance"] = (present / total * 100) if total > 0 else 0
    
    return {
        "user_counts": {
            "admin": admin_count,
            "class_teacher": class_teacher_count,
            "teacher": teacher_count,
            "student": student_count,
            "total": len(users)
        },
        "attendance_summary": {
            "total_sessions": len(attendance_history),
            "this_month_sessions": len(this_month_records),
            "department_stats": department_stats,
            "monthly_trend": monthly_trend
        }
    }
