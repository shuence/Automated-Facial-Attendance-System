# FastAPI Backend for Facial Recognition Attendance System

This is the backend API for the Multi-User Facial Recognition Attendance System, providing authenticated access for administrators, teachers, and students.

## Features

- **User Authentication**: JWT-based authentication with role-based access control
- **Student Management**: Add, update, and remove student data
- **Facial Recognition**: Process images to recognize faces and mark attendance
- **Attendance Records**: Maintain attendance history with comprehensive filtering

## User Roles

1. **Admin**: Can manage all users, students, and attendance records
2. **Class Teacher**: Can manage students and take/update attendance
3. **Teacher**: Can take attendance but has limited student management capabilities
4. **Student**: Can view their own attendance records

## API Endpoints

### Authentication

- `POST /api/auth/login`: Login with email and password
- `POST /api/auth/token`: Get access token
- `GET /api/auth/users/me`: Get current user info
- `POST /api/auth/users`: Create a new user (admin only)
- `GET /api/auth/users`: Get all users (admin only)
- `GET /api/auth/users/{user_id}`: Get user by ID
- `PUT /api/auth/users/{user_id}`: Update user
- `DELETE /api/auth/users/{user_id}`: Delete user (admin only)

### Student Management

- `POST /api/students/students`: Register a new student
- `GET /api/students/students`: Get all students
- `GET /api/students/students/{student_id}`: Get student by ID
- `PUT /api/students/students/{student_id}`: Update student
- `DELETE /api/students/students/{student_id}`: Delete student

### Attendance

- `POST /api/attendance/attendance`: Take attendance with face recognition
- `GET /api/attendance/attendance/history`: Get attendance history
- `GET /api/attendance/attendance/stats`: Get attendance statistics
- `PUT /api/attendance/attendance/{date}/{time}`: Update attendance record
- `DELETE /api/attendance/attendance/{date}/{time}`: Delete attendance record

## Getting Started

### Prerequisites

- Python 3.9+
- FastAPI
- DeepFace
- OpenCV

### Installation

1. Clone the repository
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Initialize the database with default users:

```bash
python init_db.py
```

4. Start the server:

```bash
python main.py
```

The API will be available at `http://localhost:8000`.

## Default User Accounts

After initialization, the following accounts are available:

- **Admin**: admin@example.com / admin123
- **Class Teacher**: classteacher@example.com / teacher123
- **Teacher**: teacher@example.com / teacher123
- **Student**: student@example.com / student123

## API Documentation

Once the server is running, you can access the interactive API documentation at:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Making API Requests

### Authentication

To authenticate, send a POST request to `/api/auth/login`:

```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "admin123"}'
```

Use the returned token in the Authorization header for subsequent requests:

```bash
curl -X GET "http://localhost:8000/api/students/students" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### Taking Attendance

To take attendance, send a POST request with class photos:

```bash
curl -X POST "http://localhost:8000/api/attendance/attendance" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -F "department=EXTC" \
  -F "year=TY" \
  -F "division=B" \
  -F "subject=Mini Project" \
  -F "time_slot=03:30 - 04:30" \
  -F "photos=@/path/to/class_photo.jpg"
```

## License

This project is licensed under the MIT License.
