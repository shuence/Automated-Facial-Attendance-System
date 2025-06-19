from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
import pandas as pd
import io
import os
import json
from datetime import datetime, timedelta
from typing import List, Optional
from security import get_current_active_user, is_admin, is_teacher
from models import UserRole

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


def get_users():
    """Get all users from the database"""
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    return []


def get_students():
    """Get all students from the database"""
    users = get_users()
    return [user for user in users if user.get("role") == UserRole.STUDENT]


@router.get("/monthly")
async def get_monthly_report(
    month: int = Query(..., description="Month (1-12)"),
    year: int = Query(..., description="Year (e.g., 2025)"),
    department: Optional[str] = None,
    year_of_study: Optional[str] = None,
    division: Optional[str] = None,
    current_user: dict = Depends(get_current_active_user)
):
    """Generate a monthly attendance report"""
    if not is_admin(current_user) and not is_teacher(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access attendance reports"
        )
    
    # Validate month and year
    if month < 1 or month > 12:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid month. Must be between 1 and 12."
        )
    
    # Get attendance records for the specified month and year
    attendance_history = load_attendance_history()
    
    target_month_start = datetime(year, month, 1).strftime("%Y-%m-%d")
    if month == 12:
        target_month_end = datetime(year + 1, 1, 1) - timedelta(days=1)
    else:
        target_month_end = datetime(year, month + 1, 1) - timedelta(days=1)
    target_month_end = target_month_end.strftime("%Y-%m-%d")
    
    # Filter records for the specified month
    filtered_records = [r for r in attendance_history 
                       if r.get("date") >= target_month_start and r.get("date") <= target_month_end]
    
    # Apply additional filters if provided
    if department:
        filtered_records = [r for r in filtered_records if r.get("department") == department]
    
    if year_of_study:
        filtered_records = [r for r in filtered_records if r.get("year") == year_of_study]
    
    if division:
        filtered_records = [r for r in filtered_records if r.get("division") == division]
    
    if not filtered_records:
        return {"message": "No attendance records found for the specified criteria"}
    
    # Collect all attendance data
    all_data = []
    
    for record in filtered_records:
        attendance_file = os.path.join(ATTENDANCE_DIR, record.get("attendance_file", ""))
        if os.path.exists(attendance_file):
            try:
                df = pd.read_csv(attendance_file)
                
                # Add additional information from the record
                df["Date"] = record.get("date")
                df["Subject"] = record.get("subject")
                df["Teacher"] = record.get("teacher_name")
                df["Department"] = record.get("department")
                df["Year"] = record.get("year")
                df["Division"] = record.get("division")
                
                all_data.append(df)
            except Exception as e:
                print(f"Error reading attendance file: {e}")
    
    if not all_data:
        return {"message": "No valid attendance data found for the specified criteria"}
    
    # Combine all data
    combined_df = pd.concat(all_data, ignore_index=True)
    
    # Group by student and calculate attendance statistics
    student_stats = combined_df.groupby(["Student ID", "Name"]).agg(
        total_classes=("Present", "count"),
        present_count=("Present", "sum")
    ).reset_index()
    
    # Calculate attendance percentage
    student_stats["Attendance Percentage"] = (student_stats["present_count"] / student_stats["total_classes"] * 100).round(2)
    
    # Rename columns
    student_stats = student_stats.rename(columns={
        "total_classes": "Total Classes",
        "present_count": "Classes Attended"
    })
    
    # Prepare response data
    result = {
        "month": month,
        "year": year,
        "department": department,
        "year_of_study": year_of_study,
        "division": division,
        "total_records": len(filtered_records),
        "student_attendance": student_stats.to_dict(orient="records")
    }
    
    return result


@router.get("/student")
async def get_student_report(
    student_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    subject: Optional[str] = None,
    current_user: dict = Depends(get_current_active_user)
):
    """Generate a report for a specific student"""
    # Check if the user is the student, an admin, or a teacher
    if (current_user.get("role") == UserRole.STUDENT):
        # Find student's ID
        student_info = current_user.get("student_info", {})
        if student_info.get("student_id") != student_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Students can only access their own reports"
            )
    elif not is_admin(current_user) and not is_teacher(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access student reports"
        )
    
    # Find the student in the database
    students = get_students()
    student = None
    
    for s in students:
        if s.get("student_info", {}).get("student_id") == student_id:
            student = s
            break
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    
    # Get attendance records
    attendance_history = load_attendance_history()
    
    # Collect all attendance data for this student
    all_data = []
    
    for record in attendance_history:
        # Apply date filters if provided
        if start_date and record.get("date") < start_date:
            continue
        
        if end_date and record.get("date") > end_date:
            continue
        
        # Apply subject filter if provided
        if subject and record.get("subject") != subject:
            continue
        
        attendance_file = os.path.join(ATTENDANCE_DIR, record.get("attendance_file", ""))
        if os.path.exists(attendance_file):
            try:
                df = pd.read_csv(attendance_file)
                
                # Filter for this student
                student_row = df[df["Student ID"] == student_id]
                
                if not student_row.empty:
                    # Add additional information from the record
                    student_row = student_row.copy()
                    student_row["Date"] = record.get("date")
                    student_row["Subject"] = record.get("subject")
                    student_row["Teacher"] = record.get("teacher_name")
                    student_row["Department"] = record.get("department")
                    student_row["Year"] = record.get("year")
                    student_row["Division"] = record.get("division")
                    
                    all_data.append(student_row)
            except Exception as e:
                print(f"Error reading attendance file: {e}")
    
    if not all_data:
        return {
            "message": "No attendance records found for this student",
            "student_id": student_id,
            "name": student.get("full_name")
        }
    
    # Combine all data
    combined_df = pd.concat(all_data, ignore_index=True)
    
    # Calculate overall statistics
    total_classes = len(combined_df)
    classes_attended = combined_df["Present"].sum()
    attendance_percentage = (classes_attended / total_classes * 100) if total_classes > 0 else 0
    
    # Group by subject
    subject_stats = combined_df.groupby("Subject").agg(
        total_classes=("Present", "count"),
        present_count=("Present", "sum")
    ).reset_index()
    
    # Calculate subject-wise attendance percentage
    subject_stats["attendance_percentage"] = (subject_stats["present_count"] / subject_stats["total_classes"] * 100).round(2)
    
    # Group by date for detailed attendance
    date_stats = combined_df[["Date", "Subject", "Present"]].copy()
    date_stats["Status"] = date_stats["Present"].apply(lambda x: "Present" if x == 1 else "Absent")
    date_stats = date_stats.drop("Present", axis=1)
    
    # Return the results
    return {
        "student_id": student_id,
        "name": student.get("full_name"),
        "department": student.get("student_info", {}).get("department"),
        "year": student.get("student_info", {}).get("year"),
        "division": student.get("student_info", {}).get("division"),
        "overall_stats": {
            "total_classes": total_classes,
            "classes_attended": int(classes_attended),
            "attendance_percentage": round(attendance_percentage, 2)
        },
        "subject_stats": subject_stats.to_dict(orient="records"),
        "detailed_attendance": date_stats.to_dict(orient="records")
    }


@router.get("/export/csv")
async def export_attendance_report_csv(
    department: str,
    year: str,
    division: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    subject: Optional[str] = None,
    current_user: dict = Depends(get_current_active_user)
):
    """Export attendance report as CSV"""
    if not is_admin(current_user) and not is_teacher(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to export attendance reports"
        )
    
    # Get attendance records
    attendance_history = load_attendance_history()
    
    # Filter records
    filtered_records = [r for r in attendance_history 
                       if r.get("department") == department and 
                       r.get("year") == year and 
                       r.get("division") == division]
    
    if start_date:
        filtered_records = [r for r in filtered_records if r.get("date") >= start_date]
    
    if end_date:
        filtered_records = [r for r in filtered_records if r.get("date") <= end_date]
    
    if subject:
        filtered_records = [r for r in filtered_records if r.get("subject") == subject]
    
    if not filtered_records:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No attendance records found for the specified criteria"
        )
    
    # Collect all attendance data
    all_data = []
    
    for record in filtered_records:
        attendance_file = os.path.join(ATTENDANCE_DIR, record.get("attendance_file", ""))
        if os.path.exists(attendance_file):
            try:
                df = pd.read_csv(attendance_file)
                
                # Add additional information from the record
                df["Date"] = record.get("date")
                df["Subject"] = record.get("subject")
                df["Teacher"] = record.get("teacher_name")
                
                all_data.append(df)
            except Exception as e:
                print(f"Error reading attendance file: {e}")
    
    if not all_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No valid attendance data found for the specified criteria"
        )
    
    # Combine all data
    combined_df = pd.concat(all_data, ignore_index=True)
    
    # Create a pivot table with dates as columns and students as rows
    pivot_df = pd.pivot_table(
        combined_df,
        values="Present",
        index=["Student ID", "Name"],
        columns=["Date", "Subject"],
        aggfunc="first",
        fill_value="A"
    )
    
    # Convert 1s to P (Present) and 0s to A (Absent)
    pivot_df = pivot_df.applymap(lambda x: "P" if x == 1 else "A")
    
    # Reset index to make Student ID and Name regular columns
    pivot_df = pivot_df.reset_index()
    
    # Create a buffer to hold the CSV data
    buffer = io.StringIO()
    pivot_df.to_csv(buffer, index=False)
    buffer.seek(0)
    
    # Generate filename
    filename = f"attendance_report_{department}_{year}_{division}"
    if subject:
        filename += f"_{subject}"
    if start_date:
        filename += f"_from_{start_date}"
    if end_date:
        filename += f"_to_{end_date}"
    filename += ".csv"
    
    # Return the CSV file as a downloadable attachment
    return StreamingResponse(
        buffer,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
