# Facial Recognition Attendance System

A modern, secure facial recognition-based attendance system with multiple user roles and comprehensive attendance tracking.

## Features

- **Multi-User System**: Admin, Class Teacher, Teacher, and Student roles with different permissions
- **Facial Recognition**: Automatically mark attendance by recognizing faces in class photos
- **Dashboard**: Statistics and analytics for teachers and students
- **Reports**: Generate and export detailed attendance reports
- **Notifications**: Send updates to specific users, roles, or classes

## Backend Setup

1. Install the required dependencies:

```bash
pip install -r requirements.txt
```

2. Initialize the database with default users:

```bash
cd backend
python init_db.py
```

3. Start the FastAPI server:

```bash
cd backend
python main.py
```

The API will be available at http://localhost:8000

## API Documentation

- Interactive API docs are available at http://localhost:8000/docs after starting the server
- See detailed API documentation in the `backend/API_DOCS.md` file

## Default Accounts

- Admin: coordinator@dietms.org / admin123
- Class Teacher: krushnamadrewar@dietms.org / teacher123
- Teacher: ananddeskmukh@dietms.org / teacher123
- Student: shubhampitekar@dietms.org / student123

## Frontend

The frontend is a React application that consumes the API endpoints:

```bash
cd frontend
npm install
npm start
```

## System Requirements

- Python 3.8 or higher
- OpenCV for facial detection
- DeepFace for facial recognition
- FastAPI for the backend API
- Node.js and npm for the frontend
