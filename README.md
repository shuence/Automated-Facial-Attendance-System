# Multi-User Facial Recognition Attendance System

A modern, secure facial recognition attendance system built with Next.js, React, FastAPI, and advanced computer vision techniques. This system provides automated classroom attendance with anti-spoofing protection using digital cameras.

[![Next.js](https://img.shields.io/badge/Next.js-13.0+-000000?style=for-the-badge&logo=next.js)](https://nextjs.org/)
[![React](https://img.shields.io/badge/React-18.0+-61DAFB?style=for-the-badge&logo=react)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.68.0+-009688?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![TypeScript](https://img.shields.io/badge/TypeScript-4.0+-007ACC?style=for-the-badge&logo=typescript)](https://www.typescriptlang.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-13.0+-336791?style=for-the-badge&logo=postgresql)](https://www.postgresql.org/)

## Overview

This system leverages modern web technologies and advanced computer vision techniques to automate classroom attendance using facial recognition. Built with a focus on security, scalability, and user experience, it features real-time processing, anti-spoofing measures, and comprehensive attendance management.

## Key Features

### Security & Anti-Spoofing

- Liveness detection to prevent photo/video spoofing
- Face depth analysis for 3D face verification
- Texture analysis to detect printed photos
- Encrypted data transmission and storage

### Core Functionality

- Upload individual student photos for registration
- Take attendance using class photos
- Select class, division, subject, and lecture period
- Automatic face detection and matching
- Export attendance records to CSV
- Real-time attendance status display

## Installation

### Prerequisites

- Node.js 16.0+
- Python 3.9+
- PostgreSQL 13.0+
- Git

### Frontend Setup

1. Clone and install frontend dependencies:

```bash
git clone <repository-url>
cd facial-attendance-system/frontend
npm install
```

2.Configure environment variables:

```bash
cp .env.example .env.local
# Edit .env.local with your settings
```

### Backend Setup

1. Set up Python environment:

```bash
cd ../backend
python -m venv venv
.\venv\Scripts\activate  # On Windows
pip install -r requirements.txt
```

2.Configure backend environment:

```bash
cp .env.example .env
# Edit .env with your database and API settings
```

3.Initialize database:

```bash
alembic upgrade head
```

## Usage

1. Start the Streamlit application:

```bash
streamlit run app.py
```

2.Open your web browser and navigate to the URL shown in the terminal (usually <http://localhost:8501>)

3.Using the System:

- First, upload individual student photos using the sidebar
- Enter class information (Class, Division, Subject, Period)
- Upload a class photo for taking attendance
- Click "Take Attendance" to process
- View and download attendance records

## Project Structure

```bash
.
├── frontend/                # Next.js frontend application
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── pages/         # Next.js pages
│   │   ├── styles/        # CSS and styling
│   │   └── utils/         # Helper functions
│   ├── public/            # Static assets
│   └── package.json       # Frontend dependencies
│
├── backend/               # FastAPI backend
│   ├── app/
│   │   ├── api/          # API endpoints
│   │   ├── core/         # Core functionality
│   │   ├── models/       # Database models
│   │   └── services/     # Business logic
│   ├── tests/            # Backend tests
│   └── requirements.txt   # Python dependencies
│
└── data/                 # Data storage
    ├── student_images/   # Student photos
    └── attendance/       # Attendance records
```

## Technologies Used

### Frontend Dependencies

- Next.js 13.0+
- React 18.0+
- TypeScript 4.0+
- Material-UI / Tailwind CSS
- React Query
- Socket.io-client
- Axios

### Backend Dependencies

- Python 3.9+
- FastAPI
- SQLAlchemy
- PostgreSQL
- face-recognition
- OpenCV
- numpy
- PyJWT
- uvicorn
- Redis
- Celery

## Development Guidelines

1. **Code Quality**
   - Follow TypeScript best practices
   - Use ESLint and Prettier
   - Follow PEP 8 for Python code
   - Write unit tests

2. **Security**
   - Implement proper authentication
   - Validate all inputs
   - Use environment variables
   - Follow security best practices

3. **Performance**
   - Optimize image processing
   - Implement caching
   - Use proper indexing
   - Monitor API performance
