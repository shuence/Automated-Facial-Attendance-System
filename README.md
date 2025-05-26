# Facial Attendance System

A Streamlit-based facial recognition attendance system for educational institutions. Teachers can easily take attendance by uploading a class photo and matching it against registered student photos.

## Features

- Upload individual student photos for registration
- Take attendance using class photos
- Select class, division, subject, and lecture period
- Automatic face detection and matching
- Export attendance records to CSV
- Real-time attendance status display

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd facial-attendance-system
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the required packages:
```bash
pip install -r requirements.txt
```

## Usage

1. Start the Streamlit application:
```bash
streamlit run app.py
```

2. Open your web browser and navigate to the URL shown in the terminal (usually http://localhost:8501)

3. Using the System:
   - First, upload individual student photos using the sidebar
   - Enter class information (Class, Division, Subject, Period)
   - Upload a class photo for taking attendance
   - Click "Take Attendance" to process
   - View and download attendance records

## Directory Structure

```
.
├── app.py              # Main Streamlit application
├── utils.py            # Utility functions
├── requirements.txt    # Python dependencies
├── data/
│   ├── student_images/ # Stored student photos
│   └── attendance/     # Attendance CSV files
```

## Notes

- Student photos should be clear, front-facing headshots
- Each student's photo should be named with their full name (e.g., "john_doe.jpg")
- Class photos should have good lighting and clear faces
- The system works best with unobstructed face views

## Dependencies

- Python 3.7+
- Streamlit
- face-recognition
- OpenCV
- pandas
- numpy
- Pillow 