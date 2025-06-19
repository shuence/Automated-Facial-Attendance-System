# Facial Recognition Attendance System API Documentation

## Overview

This API provides endpoints for a facial recognition-based attendance system with user authentication and management features. The system supports multiple user roles (admin, class teacher, teacher, student) with different permission levels.

## Authentication

### Login

```
POST /api/auth/login
```

Request Body:
```json
{
  "email": "user@example.com",
  "password": "userpassword"
}
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "user@example.com",
  "full_name": "User Name",
  "role": "teacher"
}
```

### OAuth2 Token (for programmatic access)

```
POST /api/auth/token
```

Form Data:
- username: user@example.com
- password: userpassword

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

## Student Management

### Get All Students

```
GET /api/students/
```

Headers:
- Authorization: Bearer {token}

Response: List of student objects

### Get Student by ID

```
GET /api/students/{student_id}
```

Headers:
- Authorization: Bearer {token}

Response: Student object

### Create New Student

```
POST /api/students/
```

Headers:
- Authorization: Bearer {token}

Request Body:
```json
{
  "name": "Student Name",
  "student_id": "ST1234",
  "department": "EXTC",
  "year": "TY",
  "division": "B",
  "subjects": ["DC", "CN", "ESD"]
}
```

Response:
```json
{
  "message": "Student created successfully",
  "student_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

### Upload Student Photo

```
POST /api/students/{student_id}/upload-photo
```

Headers:
- Authorization: Bearer {token}

Form Data:
- photo: (file upload)

Response:
```json
{
  "message": "Photo uploaded successfully",
  "filename": "student_name.jpg"
}
```

## Teacher Management

### Get All Teachers

```
GET /api/teachers/
```

Headers:
- Authorization: Bearer {token}

Response: List of teacher objects

### Get Teacher by ID

```
GET /api/teachers/{teacher_id}
```

Headers:
- Authorization: Bearer {token}

Response: Teacher object

### Create New Teacher

```
POST /api/teachers/
```

Headers:
- Authorization: Bearer {token}

Request Body:
```json
{
  "email": "teacher@example.com",
  "full_name": "Teacher Name",
  "is_class_teacher": true,
  "teacher_info": {
    "department": "EXTC",
    "subjects": ["DC", "CN"]
  }
}
```

Response:
```json
{
  "message": "Teacher created successfully",
  "teacher_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

## Attendance Management

### Take Attendance with Facial Recognition

```
POST /api/attendance/take
```

Headers:
- Authorization: Bearer {token}

Form Data:
- department: EXTC
- year: TY
- division: B
- subject: DC
- photo: (class photo file upload)

Response:
```json
{
  "message": "Attendance taken successfully",
  "date": "2025-06-19",
  "attendance_data": [
    {
      "student_id": "ST1234",
      "name": "Student Name",
      "present": true
    },
    ...
  ],
  "recognized_students": [
    {
      "student_id": "ST1234",
      "name": "Student Name",
      "confidence": 0.85
    },
    ...
  ],
  "record_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

### Manual Attendance Entry

```
POST /api/attendance/manual
```

Headers:
- Authorization: Bearer {token}

Request Body:
```json
{
  "department": "EXTC",
  "year": "TY",
  "division": "B",
  "subject": "DC",
  "attendance_data": [
    {
      "student_id": "ST1234",
      "name": "Student Name",
      "present": true
    },
    ...
  ]
}
```

Response:
```json
{
  "message": "Attendance recorded successfully",
  "date": "2025-06-19",
  "record_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

### Get Attendance History

```
GET /api/attendance/history
```

Query Parameters:
- department (optional): Filter by department
- year (optional): Filter by year of study
- division (optional): Filter by division
- start_date (optional): Filter by start date (YYYY-MM-DD)
- end_date (optional): Filter by end date (YYYY-MM-DD)

Headers:
- Authorization: Bearer {token}

Response: List of attendance record objects

## Dashboard

### Get Student Dashboard

```
GET /api/dashboard/student/{student_id}
```

Headers:
- Authorization: Bearer {token}

Response: Student dashboard data including attendance statistics

### Get Teacher Dashboard

```
GET /api/dashboard/teacher/{teacher_id}
```

Headers:
- Authorization: Bearer {token}

Response: Teacher dashboard data including classes and attendance statistics

### Get System Statistics

```
GET /api/dashboard/stats
```

Headers:
- Authorization: Bearer {token}

Response: System-wide statistics

## Reports

### Get Monthly Report

```
GET /api/reports/monthly
```

Query Parameters:
- month: Month number (1-12)
- year: Year (e.g., 2025)
- department (optional): Filter by department
- year_of_study (optional): Filter by year of study
- division (optional): Filter by division

Headers:
- Authorization: Bearer {token}

Response: Monthly attendance report

### Get Student Report

```
GET /api/reports/student
```

Query Parameters:
- student_id: Student ID
- start_date (optional): Filter by start date (YYYY-MM-DD)
- end_date (optional): Filter by end date (YYYY-MM-DD)
- subject (optional): Filter by subject

Headers:
- Authorization: Bearer {token}

Response: Detailed student attendance report

### Export Attendance Report as CSV

```
GET /api/reports/export/csv
```

Query Parameters:
- department: Department
- year: Year of study
- division: Division
- start_date (optional): Filter by start date (YYYY-MM-DD)
- end_date (optional): Filter by end date (YYYY-MM-DD)
- subject (optional): Filter by subject

Headers:
- Authorization: Bearer {token}

Response: CSV file download

## Notifications

### Get User Notifications

```
GET /api/notifications/
```

Headers:
- Authorization: Bearer {token}

Response: List of notifications for the current user

### Create Notification

```
POST /api/notifications/
```

Headers:
- Authorization: Bearer {token}

Request Body:
```json
{
  "title": "Class Canceled",
  "message": "The DC class scheduled for tomorrow is canceled.",
  "target_type": "class",
  "target_value": "EXTC_TY_B"
}
```

Response:
```json
{
  "message": "Notification created successfully",
  "notification_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

### Delete Notification

```
DELETE /api/notifications/{notification_id}
```

Headers:
- Authorization: Bearer {token}

Response:
```json
{
  "message": "Notification deleted successfully"
}
```

## Admin

### Get All Users

```
GET /api/admin/users
```

Query Parameters:
- role (optional): Filter by role

Headers:
- Authorization: Bearer {token}

Response: List of user objects

### Create User

```
POST /api/admin/users
```

Headers:
- Authorization: Bearer {token}

Request Body:
```json
{
  "email": "user@example.com",
  "full_name": "User Name",
  "password": "userpassword",
  "role": "teacher"
}
```

Response:
```json
{
  "message": "User created successfully",
  "user_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

### Deactivate User

```
PUT /api/admin/users/{user_id}/deactivate
```

Headers:
- Authorization: Bearer {token}

Response:
```json
{
  "message": "User deactivated successfully"
}
```

### Activate User

```
PUT /api/admin/users/{user_id}/activate
```

Headers:
- Authorization: Bearer {token}

Response:
```json
{
  "message": "User activated successfully"
}
```

### Delete User

```
DELETE /api/admin/users/{user_id}
```

Headers:
- Authorization: Bearer {token}

Response:
```json
{
  "message": "User deleted successfully"
}
```
