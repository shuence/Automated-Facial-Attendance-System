import streamlit as st
from deepface.DeepFace import verify, extract_faces, build_model
import cv2
import numpy as np
import pandas as pd
from datetime import datetime
import os
from PIL import Image, ImageEnhance
import shutil
import io
import base64
import json
import time

# Configure Streamlit
st.set_page_config(
    page_title="Facial Attendance System",
    page_icon="📸",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main {
        padding: 0rem 1rem;
    }
    .stButton>button {
        width: 100%;
    }
    .stProgress .st-bo {
        background-color: #00ff00;
    }
    .success-text {
        color: #28a745;
    }
    .warning-text {
        color: #ffc107;
    }
    .error-text {
        color: #dc3545;
    }
    .info-card {
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
    }
    .stat-card {
        text-align: center;
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #ffffff;
        border: 1px solid #dee2e6;
        margin: 0.5rem 0;
    }
    .header-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1rem;
    }
    .student-card {
        padding: 0.5rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        background-color: #ffffff;
        border: 1px solid #dee2e6;
    }
    .match-card {
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .match-high {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
    }
    .match-medium {
        background-color: #fff3cd;
        border: 1px solid #ffeeba;
    }
    .match-low {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
    }
</style>
""", unsafe_allow_html=True)

# Create necessary directories with proper Windows path handling
current_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(current_dir, 'data').replace('/', '\\')
base_dirs = {
    'student_images': os.path.join(data_dir, 'student_images').replace('/', '\\'),
    'attendance': os.path.join(data_dir, 'attendance').replace('/', '\\'),
    'temp': os.path.join(data_dir, 'temp').replace('/', '\\')
}

# Storage paths
STORAGE_FILE = os.path.join(data_dir, 'storage.json').replace('/', '\\')
ATTENDANCE_HISTORY_FILE = os.path.join(data_dir, 'attendance_history.json').replace('/', '\\')

def initialize_storage():
    """Initialize storage files and directories"""
    try:
        # Create base directories if they don't exist
        for dir_path in base_dirs.values():
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
        
        # Initialize storage file if it doesn't exist
        if not os.path.exists(STORAGE_FILE):
            initial_storage = {
                'students': [],
                'students_data': {},
                'settings': {
                    'confidence_threshold': 95,
                    'medium_confidence': 85,
                    'show_low_confidence': False,
                    'default_model': 'ArcFace',
                    'backup_model': 'VGG-Face',
                    'dark_mode': False
                }
            }
            save_storage(initial_storage)
        
        # Initialize attendance history file if it doesn't exist
        if not os.path.exists(ATTENDANCE_HISTORY_FILE):
            with open(ATTENDANCE_HISTORY_FILE, 'w') as f:
                json.dump([], f)
    
    except Exception as e:
        st.error(f"Error initializing storage: {str(e)}")

def load_storage():
    """Load data from storage file"""
    try:
        if os.path.exists(STORAGE_FILE):
            with open(STORAGE_FILE, 'r') as f:
                data = json.load(f)
                # Ensure all required keys exist
                if 'students' not in data:
                    data['students'] = []
                if 'students_data' not in data:
                    data['students_data'] = {}
                if 'settings' not in data:
                    data['settings'] = {
                        'confidence_threshold': 40,
                        'medium_confidence': 85,
                        'show_low_confidence': False,
                        'default_model': 'VGG-Face',
                        'backup_model': 'ArcFace',
                        'dark_mode': False
                    }
                return data
        return {
            'students': [],
            'students_data': {},
            'settings': {
                'confidence_threshold': 95,
                'medium_confidence': 85,
                'show_low_confidence': False,
                'default_model':   'VGG-Face',
                'backup_model': 'ArcFace',
                'dark_mode': False
            }
        }
    except Exception as e:
        st.error(f"Error loading storage: {str(e)}")
        return {
            'students': [],
            'students_data': {},
            'settings': {
                'confidence_threshold': 95,
                'medium_confidence': 85,
                'show_low_confidence': False,
                'default_model': 'ArcFace',
                'backup_model': 'VGG-Face',
                'dark_mode': False
            }
        }

# Call initialize_storage at startup
initialize_storage()

# Initialize session states at the top level
if 'storage' not in st.session_state:
    st.session_state.storage = load_storage()
if 'student_files' not in st.session_state:
    st.session_state.student_files = st.session_state.storage.get('students', [])
if 'students_data' not in st.session_state:
    st.session_state.students_data = st.session_state.storage.get('students_data', {})
if 'settings' not in st.session_state:
    st.session_state.settings = st.session_state.storage.get('settings', {
        'confidence_threshold': 40,
        'medium_confidence': 85,
        'show_low_confidence': False,
        'default_model': 'VGG-Face',
        'backup_model': 'ArcFace',
        'dark_mode': False
    })
if 'page' not in st.session_state:
    st.session_state.page = "Home"

# Initialize class-related session states with defaults
if 'departments' not in st.session_state:
    st.session_state.departments = ["EXTC", "CSE", "AIML", "MECH", "CIVIL"]
if 'years' not in st.session_state:
    st.session_state.years = ["FY", "SY", "TY", "Final Year"]
if 'divisions' not in st.session_state:
    st.session_state.divisions = ["A", "B", "C"]
if 'subjects' not in st.session_state:
    st.session_state.subjects = [
        "AWP", "DC", "M&M", "CN", "ESD", 
        "M&M Lab", "DC Lab", "Mini Project",
        "Mentor Mentee", "Seminar"
    ]

# Initialize default selections
if 'default_department' not in st.session_state:
    st.session_state.default_department = "EXTC"
if 'default_year' not in st.session_state:
    st.session_state.default_year = "TY"
if 'default_division' not in st.session_state:
    st.session_state.default_division = "B"

# Initialize class info for attendance history
if 'class_info' not in st.session_state:
    st.session_state.class_info = [
        {
            'name': f"{dept} {year} {div}"
            for dept in st.session_state.departments
            for year in st.session_state.years
            for div in st.session_state.divisions
        }
    ]

def normalize_path(path):
    """Convert path separators to Windows style"""
    return os.path.normpath(path).replace('/', '\\')

def pil_to_cv2(pil_image):
    """Convert PIL Image to OpenCV format"""
    if pil_image.mode != 'RGB':
        pil_image = pil_image.convert('RGB')
    numpy_image = np.array(pil_image)
    opencv_image = cv2.cvtColor(numpy_image, cv2.COLOR_RGB2BGR)
    return opencv_image

def save_image(image_data, filepath):
    """Save image data to file"""
    try:
        img = Image.open(io.BytesIO(image_data))
        if img.mode != 'RGB':
            img = img.convert('RGB')
        cv2_img = pil_to_cv2(img)
        cv2.imwrite(normalize_path(filepath), cv2_img)
        return True
    except Exception as e:
        st.error(f"Error saving image: {str(e)}")
        return False

def process_face(face_img):
    """Process face array to ensure correct format"""
    try:
        # Handle dictionary output from DeepFace
        if isinstance(face_img, dict) and 'face' in face_img and isinstance(face_img['face'], np.ndarray):
            face_img = face_img['face']
        
        # Convert to numpy array if not already
        if not isinstance(face_img, np.ndarray):
            face_img = np.array(face_img)
        
        # Ensure correct data type
        if face_img.dtype != np.uint8:
            if face_img.dtype == np.float32 or face_img.dtype == np.float64:
                face_img = (face_img * 255).astype(np.uint8)
            else:
                face_img = face_img.astype(np.uint8)
        
        # Ensure correct color format (BGR for OpenCV)
        if len(face_img.shape) == 3 and face_img.shape[2] == 3:
            # Check if already in BGR format
            if not hasattr(face_img, 'color_format') or face_img.color_format != 'BGR':
                face_img = cv2.cvtColor(face_img, cv2.COLOR_RGB2BGR)
        elif len(face_img.shape) == 2:
            # If grayscale, convert to BGR
            face_img = cv2.cvtColor(face_img, cv2.COLOR_GRAY2BGR)
            
        return face_img
    except Exception as e:
        st.error(f"Error processing face: {str(e)}")
        return None

def capture_from_webcam():
    """Capture photo from webcam"""
    st.write("📸 Webcam Preview")
    
    # Create a placeholder for the webcam feed
    video_placeholder = st.empty()
    
    # Initialize webcam state if not exists
    if 'webcam_active' not in st.session_state:
        st.session_state.webcam_active = False
    if 'cap' not in st.session_state:
        st.session_state.cap = None
    
    try:
        # Initialize webcam if not already initialized
        if not st.session_state.webcam_active:
            st.session_state.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)  # Try DirectShow backend
            if not st.session_state.cap.isOpened():
                st.error("❌ Could not access webcam. Please check your camera settings.")
                return None
            st.session_state.webcam_active = True
            # Add a delay to allow camera to warm up
            time.sleep(2)
        
        # Create buttons for capture with unique keys
        col1, col2 = st.columns(2)
        capture_button = col1.button("📸 Capture Photo", key="webcam_capture_btn")
        stop_button = col2.button("🛑 Stop Camera", key="webcam_stop_btn")
        
        if stop_button:
            if st.session_state.cap is not None:
                st.session_state.cap.release()
            st.session_state.webcam_active = False
            st.session_state.cap = None
            return None
        
        if st.session_state.webcam_active and st.session_state.cap is not None:
            ret, frame = st.session_state.cap.read()
            if ret:
                # Convert BGR to RGB
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                # Display the frame
                video_placeholder.image(rgb_frame, channels="RGB", use_container_width=True)
            
            if capture_button:
                # Capture one more frame
                ret, frame = st.session_state.cap.read()
                if ret:
                    # Convert BGR to RGB
                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    # Convert to PIL Image
                    img = Image.fromarray(rgb_frame)
                    # Convert to bytes
                    img_byte_arr = io.BytesIO()
                    img.save(img_byte_arr, format='JPEG')
                    img_byte_arr = img_byte_arr.getvalue()
                    
                    # Clean up webcam resources
                    st.session_state.cap.release()
                    st.session_state.webcam_active = False
                    st.session_state.cap = None
                    
                    st.success("✅ Photo captured successfully!")
                    return img_byte_arr
    
    except Exception as e:
        st.error(f"Webcam error: {str(e)}")
        if st.session_state.cap is not None:
            st.session_state.cap.release()
        st.session_state.webcam_active = False
        st.session_state.cap = None
    
    return None

def verify_face(img1_path, img2_path, model_name='ArcFace'):
    """Compare two face images with enhanced accuracy"""
    try:
        # Use ArcFace model for verification
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
        
        # Convert cosine similarity to percentage
        similarity = (1 - result['distance']) * 100
        
        return {
            'verified': similarity >= 40,  # Lower threshold to 40%
            'similarity': similarity,
            'distance': result['distance'],
            'model': 'ArcFace'
        }
    except Exception as e:
        st.error(f"Face verification error: {str(e)}")
        return None

def process_image_upload(uploaded_file, show_preview=True, preview_size=(100, 100)):
    """Process and manipulate uploaded image"""
    try:
        # Read image
        image = Image.open(uploaded_file)
        
        if show_preview:
            # Create columns for image preview and controls
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Show image preview with smaller size
                preview = image.copy()
                preview.thumbnail(preview_size, Image.Resampling.LANCZOS)
                st.image(preview, use_container_width=False, caption=f"Preview: {uploaded_file.name}")
            
            with col2:
                # Show edit button
                if st.button("✏️ Edit Image", key=f"edit_{uploaded_file.name}"):
                    # Image manipulation controls
                    st.markdown("##### Image Controls")
                    
                    # Rotation with label
                    rotation = st.slider(
                        "Rotation Angle",
                        -180, 180, 0,
                        key=f"rotate_{uploaded_file.name}",
                        help="Adjust image rotation"
                    )
                    if rotation != 0:
                        image = image.rotate(rotation, expand=True)
                    
                    # Brightness and Contrast with labels
                    brightness = st.slider(
                        "Brightness",
                        0.5, 1.5, 1.0, 0.1,
                        key=f"bright_{uploaded_file.name}",
                        help="Adjust brightness"
                    )
                    contrast = st.slider(
                        "Contrast",
                        0.5, 1.5, 1.0, 0.1,
                        key=f"contrast_{uploaded_file.name}",
                        help="Adjust contrast"
                    )
                    
                    if brightness != 1.0 or contrast != 1.0:
                        enhancer = ImageEnhance.Brightness(image)
                        image = enhancer.enhance(brightness)
                        enhancer = ImageEnhance.Contrast(image)
                        image = enhancer.enhance(contrast)
                    
                    # Reset button
                    if st.button("Reset", key=f"reset_{uploaded_file.name}"):
                        image = Image.open(uploaded_file)
        
        # Convert to bytes for storage
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format=image.format or 'JPEG')
        return img_byte_arr.getvalue()
        
    except Exception as e:
        st.error(f"Error processing image: {str(e)}")
        return None

def select_class(class_info):
    st.session_state.selected_class = class_info
    st.rerun()

def main():
    # Sidebar Navigation
    st.sidebar.title("📸 Navigation")
    st.session_state.page = st.sidebar.radio("", ["Home", "Student Management", "Take Attendance", "Attendance History", "Settings"])
    
    if st.session_state.page == "Home":
        show_home_page()
    elif st.session_state.page == "Student Management":
        show_student_management()
    elif st.session_state.page == "Take Attendance":
        show_attendance_page()
    elif st.session_state.page == "Attendance History":
        show_attendance_history()
    elif st.session_state.page == "Settings":
        show_settings()

def show_home_page():
    """Display the home page with statistics and recent attendance"""
    st.title("👋 Welcome to Facial Attendance System")
    st.write("A modern, AI-powered attendance tracking solution")
    
    # Statistics
    col1, col2, col3 = st.columns(3)
    
    total_students = len(st.session_state.student_files)
    
    # Calculate total unique class combinations from student data
    unique_classes = set()
    for student_data in st.session_state.students_data.values():
        if isinstance(student_data, dict):
            class_key = (
                student_data.get('department', ''),
                student_data.get('year', ''),
                student_data.get('division', '')
            )
            if all(class_key):  # Only add if all components exist
                unique_classes.add(class_key)
    total_classes = len(unique_classes)
    
    # Load and process attendance history
    attendance_history = load_attendance_history() or []
    
    # Count unique sessions based on date, department, year, division combinations
    unique_sessions = set()
    for record in attendance_history:
        if isinstance(record, dict):
            session_key = (
                record.get('date', ''),
                record.get('department', ''),
                record.get('year', ''),
                record.get('division', '')
            )
            if all(session_key):  # Only add if all components exist
                unique_sessions.add(session_key)
    total_sessions = len(unique_sessions)
    
    with col1:
        st.markdown(f"""
        <div class="stat-card">
            <h3>Total Students</h3>
            <h2>{total_students}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="stat-card">
            <h3>Total Classes</h3>
            <h2>{total_classes}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="stat-card">
            <h3>Total Sessions</h3>
            <h2>{total_sessions}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    # Recent Activity
    st.subheader("📊 Recent Attendance")
    if attendance_history:
        # Convert the records to a format that can be displayed
        recent_records = []
        for record in attendance_history[-5:]:  # Show last 5 sessions
            if isinstance(record, dict):
                # Create a simplified record for display
                display_record = {
                    'Date': record.get('date', ''),
                    'Time': record.get('time', ''),
                    'Department': record.get('department', ''),
                    'Year': record.get('year', ''),
                    'Division': record.get('division', ''),
                    'Subject': record.get('subject', ''),
                    'Present': sum(1 for r in record.get('records', []) if r.get('status') == 'Present'),
                    'Total': len(record.get('records', []))
                }
                recent_records.append(display_record)
        
        if recent_records:
            df = pd.DataFrame(recent_records)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No valid attendance records to display")
    else:
        st.info("No attendance records found")
    
    # Quick Actions
    st.markdown("### 🚀 Quick Actions")
    
    # Use columns for better layout
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="action-card" style="padding: 1.5rem; text-align: center; border-radius: 0.5rem; background-color: #f8f9fa; border: 1px solid #dee2e6; cursor: pointer;" onclick="document.querySelector('[data-value=\'Take Attendance\']').click()">
            <h4>📝 Take Attendance</h4>
            <p style="font-size: 0.9rem;">Record attendance for a class</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("📝 Take Attendance", key="take_attendance_btn"):
            st.session_state.page = "Take Attendance"
            st.rerun()
    
    with col2:
        st.markdown("""
        <div class="action-card" style="padding: 1.5rem; text-align: center; border-radius: 0.5rem; background-color: #f8f9fa; border: 1px solid #dee2e6; cursor: pointer;" onclick="document.querySelector('[data-value=\'Student Management\']').click()">
            <h4>👥 Manage Students</h4>
            <p style="font-size: 0.9rem;">Add or remove students</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("👥 Manage Students", key="manage_students_btn"):
            st.session_state.page = "Student Management"
            st.rerun()
    
    with col3:
        st.markdown("""
        <div class="action-card" style="padding: 1.5rem; text-align: center; border-radius: 0.5rem; background-color: #f8f9fa; border: 1px solid #dee2e6; cursor: pointer;" onclick="document.querySelector('[data-value=\'Attendance History\']').click()">
            <h4>📊 View History</h4>
            <p style="font-size: 0.9rem;">Check attendance records</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("📊 View History", key="view_history_btn"):
            st.session_state.page = "Attendance History"
            st.rerun()
    
    # System Status
    st.markdown("### 🔧 System Status")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div style="padding: 1rem; border-radius: 0.5rem; background-color: #ffffff; border: 1px solid #dee2e6;">
            <h4>Recognition Model</h4>
            <p>Primary: {}</p>
            <p>Backup: {}</p>
            <p>Confidence Threshold: {}%</p>
        </div>
        """.format(
            st.session_state.settings['default_model'],
            st.session_state.settings['backup_model'],
            st.session_state.settings['confidence_threshold']
        ), unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="padding: 1rem; border-radius: 0.5rem; background-color: #ffffff; border: 1px solid #dee2e6;">
            <h4>Storage Status</h4>
            <p>Student Images: {} files</p>
            <p>Classes: {} registered</p>
            <p>Attendance Records: {} sessions</p>
        </div>
        """.format(
            total_students,
            total_classes,
            total_sessions
        ), unsafe_allow_html=True)

def show_student_management():
    st.markdown("""
    <div class="header-container">
        <h1>👥 Student Management</h1>
        <p class="subtitle">Add, edit, or remove student records</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Register New Student Section
    st.markdown("""
    <div class="info-card">
        <h3>📝 Register New Student</h3>
        <p>Enter student details and upload a clear face photo</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Basic Information with improved layout
    col1, col2 = st.columns(2)
    with col1:
        student_name = st.text_input("Full Name", help="Enter student's full name")
    with col2:
        student_id = st.text_input("Roll No", help="Enter student's roll number")
    
    # Academic Information with better organization
    st.markdown("### 📚 Academic Details")
    col1, col2, col3 = st.columns(3)
    with col1:
        department = st.selectbox(
            "Branch",
            st.session_state.departments,
            index=st.session_state.departments.index(st.session_state.default_department),
            help="Select student's branch"
        )
    with col2:
        year = st.selectbox(
            "Year",
            st.session_state.years,
            index=st.session_state.years.index(st.session_state.default_year),
            help="Select student's year"
        )
    with col3:
        division = st.selectbox(
            "Division",
            st.session_state.divisions,
            index=st.session_state.divisions.index(st.session_state.default_division),
            help="Select student's division"
        )
    
    # Subject Selection with improved UI
    st.markdown("### 📖 Subject Enrollment")
    
    # Initialize session state for subject selection
    if 'selected_all_subjects' not in st.session_state:
        st.session_state.selected_all_subjects = False
    if 'selected_subjects' not in st.session_state:
        st.session_state.selected_subjects = []
    
    col1, col2 = st.columns([1, 3])
    with col1:
        select_all = st.checkbox(
            "Select All Subjects",
            value=st.session_state.selected_all_subjects,
            help="Quick select all available subjects"
        )
    
    # Update based on Select All
    if select_all != st.session_state.selected_all_subjects:
        st.session_state.selected_all_subjects = select_all
        st.session_state.selected_subjects = st.session_state.subjects.copy() if select_all else []
    
    # Show multiselect with current selection
    selected_subjects = st.multiselect(
        "Enrolled Subjects",
        st.session_state.subjects,
        default=st.session_state.selected_subjects,
        help="Select the subjects this student is enrolled in"
    )
    
    # Update session state
    st.session_state.selected_subjects = selected_subjects
    if len(selected_subjects) == len(st.session_state.subjects):
        st.session_state.selected_all_subjects = True
    elif len(selected_subjects) < len(st.session_state.subjects):
        st.session_state.selected_all_subjects = False
    
    # Photo Upload with improved preview
    st.markdown("### 📸 Student Photo")
    col1, col2 = st.columns([3, 1])
    with col1:
        student_photo = st.file_uploader(
            "Upload a clear face photo",
            type=['jpg', 'jpeg', 'png'],
            key='student_photo',
            help="Upload a clear, front-facing photo"
        )
    with col2:
        show_preview = st.checkbox("Show Preview", value=True, help="Toggle photo preview")
    
    if student_photo and show_preview:
        preview_size = (150, 150)  # Larger preview
        preview = Image.open(student_photo)
        preview.thumbnail(preview_size, Image.Resampling.LANCZOS)
        st.image(preview, use_container_width=False, caption="Photo Preview")
    
    # Register button with validation
    if st.button("📝 Register Student", type="primary", help="Click to register the student"):
        if not all([student_name, student_id, student_photo, selected_subjects]):
            st.error("❌ Please fill in all required fields and upload a photo")
        else:
            try:
                filename = f"{student_name.lower().replace(' ', '_')}.jpg"
                filepath = os.path.join(base_dirs['student_images'], filename)
                
                if save_image(student_photo.getvalue(), filepath):
                    if filename not in st.session_state.student_files:
                        student_data = {
                            'name': student_name,
                            'id': student_id,
                            'department': department,
                            'year': year,
                            'division': division,
                            'subjects': selected_subjects,
                            'photo': filename,
                            'registered_date': datetime.now().strftime("%Y-%m-%d")
                        }
                        
                        if 'students_data' not in st.session_state.storage:
                            st.session_state.storage['students_data'] = {}
                        
                        st.session_state.storage['students_data'][filename] = student_data
                        st.session_state.student_files.append(filename)
                        st.session_state.storage['students'] = st.session_state.student_files
                        save_storage(st.session_state.storage)
                        st.success("✅ Student registered successfully!")
                        
                        # Clear the form
                        st.session_state.selected_subjects = []
                        st.session_state.selected_all_subjects = False
                        st.rerun()
                    else:
                        st.warning("⚠️ Student already registered")
            except Exception as e:
                st.error(f"❌ Error registering student: {str(e)}")
    
    # Registered Students Section with improved search and filters
    st.markdown("""
    <div class="info-card" style="margin-top: 2rem;">
        <h3>📋 Registered Students</h3>
        <p>View and manage existing student records</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Enhanced search and filters
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        search = st.text_input("🔍 Search Students", help="Search by name or roll number")
    with col2:
        filter_by = st.selectbox(
            "Filter By",
            ["All", "Branch", "Year", "Division"],
            help="Choose filter category"
        )
    with col3:
        if filter_by == "Branch":
            filter_value = st.selectbox(
                "Select Branch",
                st.session_state.departments,
                help="Filter by specific branch"
            )
        elif filter_by != "All":
            filter_values = {
                "Year": st.session_state.years,
                "Division": st.session_state.divisions
            }
            filter_value = st.selectbox(
                f"Select {filter_by}",
                filter_values.get(filter_by, []),
                help=f"Filter by specific {filter_by.lower()}"
            )
    
    # Display students in an enhanced grid
    if 'students_data' in st.session_state.storage:
        for file, student_data in st.session_state.storage['students_data'].items():
            filter_match = (
                filter_by == "All" or
                (filter_by == "Branch" and student_data.get('department', '') == filter_value) or
                (filter_by == "Year" and student_data.get('year', '') == filter_value) or
                (filter_by == "Division" and student_data.get('division', '') == filter_value)
            )
            
            search_match = (
                search.lower() in student_data['name'].lower() or
                search.lower() in student_data['id'].lower() or
                not search
            )
            
            if search_match and filter_match:
                with st.expander(f"👤 {student_data['name']} (Roll No: {student_data['id']})"):
                    col1, col2, col3 = st.columns([2, 2, 1])
                    
                    with col1:
                        st.markdown("**Academic Details**")
                        st.write(f"🏫 Branch: {student_data['department']}")
                        st.write(f"📚 Year: {student_data['year']}")
                        st.write(f"🎓 Division: {student_data['division']}")
                    
                    with col2:
                        st.markdown("**Enrolled Subjects**")
                        for subject in student_data['subjects']:
                            st.write(f"📖 {subject}")
                    
                    with col3:
                        st.markdown("**Actions**")
                        if st.button("🗑️ Remove", key=f"remove_{file}", help="Remove student record"):
                            try:
                                photo_path = os.path.join(base_dirs['student_images'], file)
                                if os.path.exists(photo_path):
                                    os.remove(photo_path)
                                
                                st.session_state.student_files.remove(file)
                                del st.session_state.storage['students_data'][file]
                                st.session_state.storage['students'] = st.session_state.student_files
                                save_storage(st.session_state.storage)
                                st.success("✅ Student removed successfully")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Error removing student: {str(e)}")
    else:
        st.info("ℹ️ No students registered yet")

def show_attendance_page():
    st.markdown("""
    <div class="header-container">
        <h1>📸 Take Attendance</h1>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize session states
    if 'class_images' not in st.session_state:
        st.session_state.class_images = []
    if 'attendance_results' not in st.session_state:
        st.session_state.attendance_results = []
    if 'processing_complete' not in st.session_state:
        st.session_state.processing_complete = False
    if 'manual_corrections' not in st.session_state:
        st.session_state.manual_corrections = {}
    if 'current_attendance_info' not in st.session_state:
        st.session_state.current_attendance_info = {
            'department': None,
            'year': None,
            'division': None,
            'subject': None,
            'time_slot': None
        }
    
    # Class Information
    st.markdown("### 📚 Class Information")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        department = st.selectbox("Department", st.session_state.departments, 
                                index=st.session_state.departments.index(st.session_state.default_department))
        st.session_state.current_attendance_info['department'] = department
    with col2:
        year = st.selectbox("Year", st.session_state.years,
                           index=st.session_state.years.index(st.session_state.default_year))
        st.session_state.current_attendance_info['year'] = year
    with col3:
        division = st.selectbox("Division", st.session_state.divisions,
                              index=st.session_state.divisions.index(st.session_state.default_division))
        st.session_state.current_attendance_info['division'] = division
    
    # Subject and Time Selection
    st.markdown("### ⏰ Subject and Time")
    col1, col2 = st.columns(2)
    
    with col1:
        subject = st.selectbox("Subject", st.session_state.subjects)
        st.session_state.current_attendance_info['subject'] = subject
    
    with col2:
        time_slots = [
            "10:15 - 11:15", "11:15 - 12:15",
            "01:15 - 02:15", "02:15 - 03:15",
            "03:30 - 04:30", "04:30 - 05:30"
        ]
        time_slot = st.selectbox("Time Slot", time_slots)
        st.session_state.current_attendance_info['time_slot'] = time_slot
    
    # Photo Upload Section
    st.markdown("""
    <div class="info-card">
        <h3>📷 Class Photos</h3>
        <p>Upload photos of the class to mark attendance. Multiple photos can be uploaded to ensure all students are captured.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Method selection
    method = st.radio("Choose Method", ["Upload Photos", "Use Webcam"], key="attendance_method")
    
    if method == "Upload Photos":
        show_preview = st.checkbox("Show Photo Previews", value=False, key="upload_preview_checkbox")
        uploaded_files = st.file_uploader(
            "Upload class photos",
            type=['jpg', 'jpeg', 'png'],
            accept_multiple_files=True,
            key='class_photos_upload'
        )
        
        if uploaded_files:
            if show_preview:
                st.markdown("### 📸 Image Preview and Controls")
                processed_images = []
                
                for idx, uploaded_file in enumerate(uploaded_files):
                    st.markdown(f"#### Processing: {uploaded_file.name}")
                    processed_image = process_image_upload(uploaded_file, show_preview=show_preview)
                    if processed_image:
                        processed_images.append(processed_image)
                
                st.session_state.class_images = processed_images
            else:
                # Just process without preview
                st.session_state.class_images = [
                    process_image_upload(file, show_preview=False)
                    for file in uploaded_files
                    if process_image_upload(file, show_preview=False)
                ]
            
            # Clear photos button
            if st.button("🗑️ Clear Photos", key="clear_uploaded_photos_btn"):
                st.session_state.class_images = []
                st.session_state.processing_complete = False
                st.session_state.attendance_results = []
                st.session_state.manual_corrections = {}
                st.rerun()
    
    else:  # Webcam method
        photo = capture_from_webcam()
        if photo:
            show_preview = st.checkbox("Show Photo Preview", value=False, key="webcam_preview_checkbox")
            if show_preview:
                st.markdown("### 📸 Image Preview and Controls")
            processed_image = process_image_upload(io.BytesIO(photo), show_preview=show_preview)
            if processed_image:
                st.session_state.class_images = [processed_image]
                
                # Clear photo button for webcam
                if st.button("🗑️ Clear Photo", key="clear_webcam_photo_btn"):
                    st.session_state.class_images = []
                    st.session_state.processing_complete = False
                    st.session_state.attendance_results = []
                    st.session_state.manual_corrections = {}
                    st.rerun()
    
    # Display uploaded photos with smaller previews
    if st.session_state.class_images:
        st.markdown("### 📸 Uploaded Photos")
        photo_cols = st.columns(min(4, len(st.session_state.class_images)))
        for idx, img_data in enumerate(st.session_state.class_images):
            with photo_cols[idx % 4]:
                try:
                    if isinstance(img_data, bytes):
                        img = Image.open(io.BytesIO(img_data))
                    else:
                        img = Image.open(img_data)
                    
                    # Create smaller preview
                    preview_size = (100, 100)  # Smaller preview size
                    preview = img.copy()
                    preview.thumbnail(preview_size, Image.Resampling.LANCZOS)
                    st.image(preview, caption=f"Photo {idx + 1}", use_container_width=False)
                except Exception as e:
                    st.error(f"Error displaying image {idx + 1}")
        
        # Process Photos button
        if not st.session_state.processing_complete:
            if st.button("📝 Process Photos", type="primary", key="process_photos_btn"):
                if not all([department, year, division, subject]):
                    st.error("Please fill in all class information!")
                    return
                
                if not st.session_state.student_files:
                    st.error("No students registered in the system!")
                    return
                
                try:
                    all_results = []
                    all_attempts = {}
                    
                    # Create a progress container
                    progress_container = st.container()
                    with progress_container:
                        st.markdown("### 📸 Processing Photos")
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        # Process each photo
                        total_photos = len(st.session_state.class_images)
                        
                        for idx, img_data in enumerate(st.session_state.class_images):
                            # Update progress
                            progress = (idx + 1) / total_photos
                            progress_bar.progress(progress)
                            status_text.text(f"Processing photo {idx + 1} of {total_photos} ({int(progress * 100)}%)")
                            
                            try:
                                if isinstance(img_data, bytes):
                                    img_bytes = img_data
                                else:
                                    img_bytes = img_data.getvalue()
                                
                                class_photo_path = normalize_path(os.path.join(base_dirs['temp'], f"class_{idx}.jpg"))
                                if save_image(img_bytes, class_photo_path):
                                    results, attempts = process_attendance_image(
                                        class_photo_path,
                                        department,
                                        year,
                                        division,
                                        subject,
                                        idx + 1
                                    )
                                    
                                    if results:
                                        all_results.extend(results)
                                    
                                    # Merge attempts
                                    for student, matches in attempts.items():
                                        if student not in all_attempts:
                                            all_attempts[student] = []
                                        all_attempts[student].extend(matches)
                            except Exception as e:
                                st.error(f"Error processing photo {idx + 1}: {str(e)}")
                                continue
                        
                        # Clear progress display after completion
                        progress_bar.empty()
                        status_text.empty()
                        st.success("✅ Processing complete!")
                    
                    # Process results and create records
                    attendance_records = []
                    for student_file in st.session_state.student_files:
                        student_name = os.path.splitext(student_file)[0]
                        
                        # Find best match across all results
                        student_matches = [r for r in all_results if r['student_name'] == student_name]
                        best_match = max(student_matches, key=lambda x: x['similarity']) if student_matches else None
                        
                        # Get all attempts for analysis
                        attempts = all_attempts.get(student_name, [])
                        best_attempt = max(attempts, key=lambda x: x['similarity']) if attempts else None
                        
                        # Mark as present if best match is above threshold
                        is_present = False
                        if best_attempt:
                            is_present = best_attempt['similarity'] >= 40
                        
                        analysis = {
                            'total_attempts': len(attempts),
                            'best_match': best_attempt['similarity'] if best_attempt else 0,
                            'photos_appeared': len(set(a['photo_number'] for a in attempts)) if attempts else 0,
                            'faces_matched': len(set(a['face_number'] for a in attempts)) if attempts else 0,
                            'best_model': best_attempt['model'] if best_attempt else None
                        }
                        
                        record = {
                            'Student_Name': student_name.replace('_', ' ').title(),
                            'Status': 'Present' if is_present else 'Absent',
                            'Confidence': f"{analysis['best_match']:.1f}%" if best_attempt else "0%",
                            'Photo_Number': best_match['photo_number'] if best_match else None,
                            'Model': best_match['model'] if best_match else analysis['best_model'],
                            'Analysis': analysis
                        }
                        
                        attendance_records.append(record)
                    
                    st.session_state.attendance_results = attendance_records
                    st.session_state.processing_complete = True
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Error during attendance processing: {str(e)}")
                    st.session_state.processing_complete = False
    
    # Display results and controls
    if st.session_state.attendance_results:
        # Display attendance results with class info
        display_attendance_results(
            st.session_state.attendance_results,
            department=st.session_state.current_attendance_info['department'],
            year=st.session_state.current_attendance_info['year'],
            division=st.session_state.current_attendance_info['division']
        )
        
        # Save and Reset controls
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Confirm and Save Attendance", type="primary", key="save_attendance_btn"):
                if all(st.session_state.current_attendance_info.values()):
                    save_attendance_records(
                        st.session_state.attendance_results,
                        st.session_state.current_attendance_info['department'],
                        st.session_state.current_attendance_info['year'],
                        st.session_state.current_attendance_info['division'],
                        st.session_state.current_attendance_info['subject'],
                        st.session_state.current_attendance_info['time_slot']
                    )
                    st.success("✅ Attendance saved successfully!")
                    
                    # Clear session
                    st.session_state.class_images = []
                    st.session_state.attendance_results = []
                    st.session_state.processing_complete = False
                    st.session_state.manual_corrections = {}
                    st.session_state.current_attendance_info = {
                        'department': None,
                        'year': None,
                        'division': None,
                        'subject': None,
                        'time_slot': None
                    }
                    st.rerun()
                else:
                    st.error("Please fill in all class information before saving!")
        
        with col2:
            if st.button("🔄 Reset All", key="reset_attendance_btn"):
                if st.session_state.get('confirm_reset', False):
                    # Clear all states
                    st.session_state.class_images = []
                    st.session_state.attendance_results = []
                    st.session_state.processing_complete = False
                    st.session_state.manual_corrections = {}
                    st.session_state.current_attendance_info = {
                        'department': None,
                        'year': None,
                        'division': None,
                        'subject': None,
                        'time_slot': None
                    }
                    st.rerun()
                else:
                    st.session_state.confirm_reset = True
                    st.warning("⚠️ Click again to confirm reset")

def process_attendance_image(image_path, department, year, division, subject, photo_number):
    """Process a single class photo for attendance"""
    try:
        # Extract faces from the image
        faces = extract_faces(
            img_path=image_path,
            enforce_detection=False,
            detector_backend='retinaface',
            align=True
        )
        
        if not faces:
            st.warning(f"No faces detected in photo {photo_number}!")
            return [], {}
        
        st.info(f"Found {len(faces)} faces in photo {photo_number}")
        
        # Create columns for displaying detected faces
        cols = st.columns(6)  # More columns for smaller previews
        for idx, face in enumerate(faces):
            with cols[idx % 6]:
                try:
                    face_img = process_face(face)
                    if face_img is not None:
                        # Convert to PIL for resizing
                        pil_face = Image.fromarray(cv2.cvtColor(face_img, cv2.COLOR_BGR2RGB))
                        pil_face.thumbnail((100, 100))  # Smaller face previews
                        st.image(pil_face, caption=f"Face {idx + 1}", use_container_width=True)
                except Exception as e:
                    st.error(f"Error displaying face {idx + 1}")
        
        # Process faces
        results = []
        attempted_matches = {}
        
        # Create progress bar
        progress_text = st.empty()
        progress_bar = st.progress(0)
        
        # Create a placeholder for live results
        results_placeholder = st.empty()
        current_results = []
        
        for idx, face in enumerate(faces):
            processed_face = process_face(face)
            if processed_face is not None:
                face_path = normalize_path(os.path.join(base_dirs['temp'], f"face_{photo_number}_{idx}.jpg"))
                if cv2.imwrite(face_path, processed_face):
                    face_matches = []
                    
                    # Update progress
                    progress_text.text(f"Checking face {idx + 1} of {len(faces)}")
                    
                    for student_file in st.session_state.student_files:
                        student_path = normalize_path(os.path.join(base_dirs['student_images'], student_file))
                        result = verify_face(face_path, student_path)
                        
                        if result:
                            student_name = os.path.splitext(student_file)[0]
                            similarity = result['similarity']
                            
                            # Track all attempts
                            if student_name not in attempted_matches:
                                attempted_matches[student_name] = []
                            
                            attempted_matches[student_name].append({
                                'similarity': similarity,
                                'photo_number': photo_number,
                                'face_number': idx + 1,
                                'model': result['model']
                            })
                            
                            if similarity >= 40:  # Lower threshold
                                face_matches.append({
                                    'student_name': student_name,
                                    'similarity': similarity,
                                    'model': result['model'],
                                    'status': 'Present',
                                    'confidence': f"{similarity:.1f}%",
                                    'photo_number': photo_number,
                                    'face_number': idx + 1
                                })
                    
                    # Add best match for this face
                    if face_matches:
                        best_match = max(face_matches, key=lambda x: x['similarity'])
                        results.append(best_match)
                        current_results.append(best_match)
                        
                        # Update live results with smaller cards
                        with results_placeholder.container():
                            st.markdown("#### Current Matches")
                            for match in current_results:
                                st.markdown(f"""
                                <div style="padding: 0.25rem; border-radius: 0.25rem; background-color: #d4edda; margin: 0.25rem 0; font-size: 0.9em;">
                                    {match['student_name'].replace('_', ' ').title()} - {match['confidence']}
                                </div>
                                """, unsafe_allow_html=True)
            
            # Update progress
            progress_bar.progress((idx + 1) / len(faces))
        
        # Clear progress indicators but keep results
        progress_text.empty()
        progress_bar.empty()
        
        return results, attempted_matches
    except Exception as e:
        st.error(f"Error processing photo {photo_number}: {str(e)}")
        return [], {}

def save_attendance_records(records, department, year, division, subject, time_slot):
    """Save attendance records with persistence"""
    try:
        # Load existing records
        history = load_attendance_history() if os.path.exists(ATTENDANCE_HISTORY_FILE) else []
        
        # Create attendance session record
        session_record = {
            'date': datetime.now().strftime("%Y-%m-%d"),
            'time': datetime.now().strftime("%H:%M:%S"),
            'department': department,
            'year': year,
            'division': division,
            'subject': subject,
            'time_slot': time_slot,
            'records': []
        }
        
        # Process each student record
        for record in records:
            student_record = {
                'student_name': record['Student_Name'],
                'status': record['Status'],
                'confidence': record['Confidence'],
                'model': record['Model'],
                'manually_corrected': record.get('Manually_Corrected', False)
            }
            session_record['records'].append(student_record)
        
        # Add new session record
        history.append(session_record)
        
        # Save updated history
        with open(ATTENDANCE_HISTORY_FILE, 'w') as f:
            json.dump(history, f, indent=4)
        
        # Save/Update master CSV
        master_csv_path = os.path.join(
            base_dirs['attendance'], 
            f'attendance_{department}_{year}_{division}.csv'
        )
        
        # Create or update master CSV
        df = pd.DataFrame({
            'Date': session_record['date'],
            'Time': session_record['time'],
            'Department': department,
            'Year': year,
            'Division': division,
            'Subject': subject,
            'Time_Slot': time_slot,
            'Student_Name': [r['student_name'] for r in session_record['records']],
            'Status': [r['status'] for r in session_record['records']],
            'Confidence': [r['confidence'] for r in session_record['records']],
            'Model': [r['model'] for r in session_record['records']],
            'Manually_Corrected': [r['manually_corrected'] for r in session_record['records']]
        })
        
        # If master CSV exists, append to it
        if os.path.exists(master_csv_path):
            existing_df = pd.read_csv(master_csv_path)
            df = pd.concat([existing_df, df], ignore_index=True)
        
        # Save master CSV
        df.to_csv(master_csv_path, index=False)
        
        return True
    except Exception as e:
        st.error(f"Error saving attendance records: {str(e)}")
        return False

def display_attendance_results(records, department=None, year=None, division=None):
    """Display attendance results with enhanced visualization and manual correction"""
    st.markdown("""
    <div class="info-card">
        <h3>📊 Attendance Results</h3>
        <p>Review and correct attendance records if needed</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Create DataFrame for better analysis
    df = pd.DataFrame(records)
    
    # Initialize session state for real-time counters if not exists
    if 'total_count' not in st.session_state:
        st.session_state.total_count = len(records)
    if 'present_count' not in st.session_state:
        st.session_state.present_count = len(df[df['Status'] == 'Present'])
    if 'absent_count' not in st.session_state:
        st.session_state.absent_count = st.session_state.total_count - st.session_state.present_count
    if 'avg_confidence' not in st.session_state:
        st.session_state.avg_confidence = df['Confidence'].str.rstrip('%').astype(float).mean()
    
    # Create placeholders for live updates
    st.markdown("### 📈 Live Status")
    metrics_container = st.container()
    
    # Function to update metrics display
    def update_metrics():
        with metrics_container:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric(
                    "Total Students",
                    st.session_state.total_count
                )
            with col2:
                st.metric(
                    "Present",
                    st.session_state.present_count,
                    f"{(st.session_state.present_count/st.session_state.total_count*100):.1f}%"
                )
            with col3:
                st.metric(
                    "Absent",
                    st.session_state.absent_count,
                    f"{(st.session_state.absent_count/st.session_state.total_count*100):.1f}%"
                )
            with col4:
                st.metric(
                    "Avg Confidence",
                    f"{st.session_state.avg_confidence:.1f}%"
                )
    
    # Initial metrics display
    update_metrics()
    
    # Real-time status chart
    st.markdown("### 📊 Real-time Status Distribution")
    chart_container = st.container()
    
    def update_chart():
        with chart_container:
            # Create data for pie chart
            chart_data = pd.DataFrame({
                'Status': ['Present', 'Absent'],
                'Count': [st.session_state.present_count, st.session_state.absent_count]
            })
            
            # Calculate percentages
            total = chart_data['Count'].sum()
            chart_data['Percentage'] = chart_data['Count'] / total * 100
            
            # Create columns for chart and legend
            col1, col2 = st.columns([3, 1])
            
            with col1:
                # Create pie chart
                fig = {
                    'data': [{
                        'values': chart_data['Count'],
                        'labels': chart_data['Status'],
                        'type': 'pie',
                        'marker': {
                            'colors': ['#28a745', '#dc3545']
                        },
                        'textinfo': 'percent',
                        'hoverinfo': 'label+value'
                    }],
                    'layout': {
                        'showlegend': False,
                        'height': 200,
                        'margin': {'t': 0, 'b': 0, 'l': 0, 'r': 0}
                    }
                }
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Create legend with counts
                st.markdown("""
                <div style="margin-top: 30px;">
                    <div style="color: #28a745; margin-bottom: 10px;">
                        ⬤ Present: {:.1f}%
                    </div>
                    <div style="color: #dc3545;">
                        ⬤ Absent: {:.1f}%
                    </div>
                </div>
                """.format(
                    chart_data[chart_data['Status'] == 'Present']['Percentage'].iloc[0],
                    chart_data[chart_data['Status'] == 'Absent']['Percentage'].iloc[0]
                ), unsafe_allow_html=True)
    
    # Initial chart display
    update_chart()
    
    # Filters for better accessibility
    st.markdown("### 🔍 Filters")
    col1, col2, col3 = st.columns(3)
    with col1:
        status_filter = st.selectbox("Filter by Status", ["All", "Present", "Absent"])
    with col2:
        confidence_filter = st.selectbox("Filter by Confidence", ["All", "High (>85%)", "Medium (60-85%)", "Low (<60%)"])
    with col3:
        name_search = st.text_input("Search by Name")
    
    # Apply filters
    filtered_df = df.copy()
    if status_filter != "All":
        filtered_df = filtered_df[filtered_df['Status'] == status_filter]
    
    if confidence_filter != "All":
        confidence_values = filtered_df['Confidence'].str.rstrip('%').astype(float)
        if confidence_filter == "High (>85%)":
            filtered_df = filtered_df[confidence_values >= 85]
        elif confidence_filter == "Medium (60-85%)":
            filtered_df = filtered_df[(confidence_values >= 60) & (confidence_values < 85)]
        else:
            filtered_df = filtered_df[confidence_values < 60]
    
    if name_search:
        filtered_df = filtered_df[filtered_df['Student_Name'].str.lower().str.contains(name_search.lower())]
    
    # Detailed Results Table with Manual Correction
    st.markdown("### 📋 Attendance Preview")
    
    # Create containers for each student with status-based styling
    for idx, row in filtered_df.iterrows():
        status_color = "#d4edda" if row['Status'] == 'Present' else "#f8d7da"
        status_icon = "✅" if row['Status'] == 'Present' else "❌"
        confidence_value = float(row['Confidence'].strip('%'))
        confidence_color = (
            "#28a745" if confidence_value >= 85 else 
            "#ffc107" if confidence_value >= 60 else 
            "#dc3545"
        )
        
        # Create a unique key for each student's correction
        correction_key = f"correction_{row['Student_Name']}"
        
        st.markdown(f"""
        <div style="padding: 1rem; border-radius: 0.5rem; background-color: {status_color}; margin: 0.75rem 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div style="flex: 3;">
                    <strong style="font-size: 1.2em;">{row['Student_Name']}</strong>
                </div>
                <div style="flex: 2; text-align: center;">
                    <span style="padding: 0.5rem 1rem; border-radius: 0.25rem; background-color: white; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                        {status_icon} {row['Status']}
                    </span>
                </div>
                <div style="flex: 2; text-align: center;">
                    <span style="color: {confidence_color}; font-weight: bold;">
                        {row['Confidence']}
                    </span>
                </div>
                <div style="flex: 2; text-align: right;">
                    <span style="color: #666; font-size: 0.9em;">
                        {row['Model']}
                    </span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Manual correction controls
        col1, col2 = st.columns([3, 1])
        with col1:
            new_status = st.radio(
                "Correct Status",
                ["Present", "Absent"],
                horizontal=True,
                key=correction_key,
                index=0 if row['Status'] == 'Present' else 1
            )
        with col2:
            if st.button("Update", key=f"update_{correction_key}"):
                # Update the status in the DataFrame
                old_status = df.loc[idx, 'Status']
                df.loc[idx, 'Status'] = new_status
                df.loc[idx, 'Manually_Corrected'] = True
                
                # Update session state counters
                if old_status != new_status:
                    if new_status == 'Present':
                        st.session_state.present_count += 1
                        st.session_state.absent_count -= 1
                    else:
                        st.session_state.present_count -= 1
                        st.session_state.absent_count += 1
                
                # Update average confidence
                st.session_state.avg_confidence = df['Confidence'].str.rstrip('%').astype(float).mean()
                
                # Update the records in session state
                for record in st.session_state.attendance_results:
                    if record['Student_Name'] == row['Student_Name']:
                        record['Status'] = new_status
                        record['Manually_Corrected'] = True
                        break
                
                # Update displays
                update_metrics()
                update_chart()
                
                st.success(f"✅ Updated {row['Student_Name']}'s status to {new_status}")
    
    # Download options
    st.markdown("### ⬇️ Export Results")
    col1, col2 = st.columns(2)
    
    # Create filename with class info
    filename = "attendance"
    if department and year and division:
        filename = f"attendance_{department}_{year}_{division}"
    filename += f"_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    with col1:
        st.download_button(
            label="📥 Download All Results",
            data=df.to_csv(index=False),
            file_name=filename,
            mime="text/csv",
            help="Download complete attendance records"
        )
    with col2:
        st.download_button(
            label="📥 Download Filtered Results",
            data=filtered_df.to_csv(index=False),
            file_name=f"filtered_{filename}",
            mime="text/csv",
            help="Download currently filtered attendance records"
        )

def show_attendance_history():
    st.markdown("""
    <div class="header-container">
        <h1>📊 Attendance History</h1>
    </div>
    """, unsafe_allow_html=True)
    
    # Filters
    st.markdown("### 🔍 Filter Records")
    
    # Date filter
    date_filter = st.date_input("Select Date", key="history_date_filter")
    
    # Class filters - match take attendance schema
    col1, col2, col3 = st.columns(3)
    
    with col1:
        department_filter = st.selectbox(
            "Department",
            ["All"] + st.session_state.departments,
            key="history_department_filter"
        )
    
    with col2:
        year_filter = st.selectbox(
            "Year",
            ["All"] + st.session_state.years,
            key="history_year_filter"
        )
    
    with col3:
        division_filter = st.selectbox(
            "Division",
            ["All"] + st.session_state.divisions,
            key="history_division_filter"
        )
    
    # Additional filters
    col1, col2 = st.columns(2)
    with col1:
        subject_filter = st.selectbox(
            "Subject",
            ["All"] + st.session_state.subjects,
            key="history_subject_filter"
        )
    with col2:
        status_filter = st.selectbox(
            "Attendance Status",
            ["All", "Present", "Absent"],
            key="history_status_filter"
        )
    
    # Load and filter history
    history = load_attendance_history()
    if history:
        # Convert the nested records into a flat DataFrame
        flattened_records = []
        for session in history:
            base_record = {
                'date': session.get('date', ''),
                'time': session.get('time', ''),
                'department': session.get('department', ''),
                'year': session.get('year', ''),
                'division': session.get('division', ''),
                'subject': session.get('subject', ''),
                'time_slot': session.get('time_slot', '')
            }
            
            # Add individual student records
            for record in session.get('records', []):
                student_record = base_record.copy()
                student_record.update({
                    'student_name': record.get('student_name', ''),
                    'status': record.get('status', ''),
                    'confidence': record.get('confidence', ''),
                    'manually_corrected': record.get('manually_corrected', False)
                })
                flattened_records.append(student_record)
        
        df = pd.DataFrame(flattened_records)
        
        # Apply filters
        if date_filter:
            df = df[df['date'] == date_filter.strftime("%Y-%m-%d")]
        
        if department_filter != "All":
            df = df[df['department'] == department_filter]
        
        if year_filter != "All":
            df = df[df['year'] == year_filter]
        
        if division_filter != "All":
            df = df[df['division'] == division_filter]
        
        if subject_filter != "All":
            df = df[df['subject'] == subject_filter]
        
        if status_filter != "All":
            df = df[df['status'] == status_filter]
        
        if len(df) > 0:
            # Display statistics
            st.markdown("### 📊 Attendance Summary")
            
            total = len(df)
            present = len(df[df['status'] == 'Present'])
            absent = total - present
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Students", total)
            with col2:
                st.metric("Present", present)
            with col3:
                st.metric("Absent", absent)
            
            # Group by date and class to show sessions
            st.markdown("### 📅 Attendance Sessions")
            
            sessions = df.groupby([
                'date', 'time', 'department', 'year', 
                'division', 'subject', 'time_slot'
            ]).agg({
                'student_name': 'count',
                'status': lambda x: sum(x == 'Present')
            }).reset_index()
            
            sessions.columns = [
                'Date', 'Time', 'Department', 'Year', 
                'Division', 'Subject', 'Time Slot',
                'Total Students', 'Present'
            ]
            sessions['Absent'] = sessions['Total Students'] - sessions['Present']
            
            # Sort by date and time
            sessions = sessions.sort_values(['Date', 'Time'], ascending=[False, False])
            
            st.dataframe(
                sessions,
                use_container_width=True,
                hide_index=True
            )
            
            # Display detailed records
            st.markdown("### 👥 Student Records")
            
            # Prepare detailed view
            detailed_view = df[[
                'date', 'time', 'department', 'year', 'division', 
                'subject', 'time_slot', 'student_name', 'status', 
                'confidence', 'manually_corrected'
            ]].copy()
            
            detailed_view.columns = [
                'Date', 'Time', 'Department', 'Year', 'Division', 
                'Subject', 'Time Slot', 'Student Name', 'Status', 
                'Confidence', 'Manually Corrected'
            ]
            
            # Sort by date, time, and student name
            detailed_view = detailed_view.sort_values(
                ['Date', 'Time', 'Student Name'],
                ascending=[False, False, True]
            )
            
            # Apply styling
            def style_dataframe(df):
                return df.style.apply(
                    lambda x: ['background-color: #d4edda' if v == 'Present' else 'background-color: #f8d7da' for v in x],
                    subset=['Status']
                ).apply(
                    lambda x: ['color: #dc3545' if v else '' for v in x],
                    subset=['Manually Corrected']
                )
            
            styled_df = style_dataframe(detailed_view)
            st.dataframe(
                styled_df,
                use_container_width=True,
                hide_index=True
            )
            
            # Export options
            st.markdown("### 💾 Export Options")
            col1, col2 = st.columns(2)
            
            with col1:
                csv = detailed_view.to_csv(index=False)
                st.download_button(
                    "⬇️ Download Detailed Records",
                    data=csv,
                    file_name=f"attendance_records_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            
            with col2:
                if st.button("🗑️ Clear History"):
                    if st.session_state.get('confirm_delete', False):
                        delete_attendance_history()
                        st.success("History cleared successfully!")
                        st.rerun()
                    else:
                        st.session_state.confirm_delete = True
                        st.warning("⚠️ Click again to confirm deletion")
        else:
            st.info("No records found matching the selected filters.")
    else:
        st.info("No attendance records found.")

def show_settings():
    st.markdown("""
    <div class="header-container">
        <h1>⚙️ Settings</h1>
    </div>
    """, unsafe_allow_html=True)
    
    # Face Recognition Settings
    st.markdown("""
    <div class="info-card">
        <h3>🎯 Face Recognition Settings</h3>
    </div>
    """, unsafe_allow_html=True)
    
    confidence_threshold = st.slider(
        "Confidence Threshold (%)",
        min_value=40,
        max_value=100,
        value=st.session_state.settings['confidence_threshold']
    )
    
    medium_confidence = st.slider(
        "Medium Confidence Threshold (%)",
        min_value=40,
        max_value=confidence_threshold,
        value=st.session_state.settings['medium_confidence']
    )
    
    show_low_confidence = st.checkbox(
        "Show Low Confidence Matches",
        value=st.session_state.settings['show_low_confidence']
    )
    
    # Model Settings
    st.markdown("""
    <div class="info-card">
        <h3>🤖 Model Settings</h3>
    </div>
    """, unsafe_allow_html=True)
    
    default_model = st.selectbox(
        "Default Recognition Model",
        ["ArcFace", "VGG-Face"],
        index=0 if st.session_state.settings['default_model'] == 'ArcFace' else 1
    )
    
    # UI Settings
    st.markdown("""
    <div class="info-card">
        <h3>🎨 UI Settings</h3>
    </div>
    """, unsafe_allow_html=True)
    
    dark_mode = st.checkbox(
        "Dark Mode",
        value=st.session_state.settings['dark_mode']
    )
    
    # Save Settings
    if st.button("💾 Save Settings", type="primary"):
        st.session_state.settings.update({
            'confidence_threshold': confidence_threshold,
            'medium_confidence': medium_confidence,
            'show_low_confidence': show_low_confidence,
            'default_model': default_model,
            'dark_mode': dark_mode
        })
        save_storage(st.session_state.storage)
        st.success("✅ Settings saved successfully!")

def save_storage(data):
    """Save data to storage file"""
    try:
        with open(STORAGE_FILE, 'w') as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        st.error(f"Error saving storage: {str(e)}")

def load_attendance_history():
    """Load attendance history"""
    if os.path.exists(ATTENDANCE_HISTORY_FILE):
        try:
            with open(ATTENDANCE_HISTORY_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            st.error(f"Error loading attendance history: {str(e)}")
    return []

def delete_attendance_history():
    """Delete attendance history file"""
    try:
        if os.path.exists(ATTENDANCE_HISTORY_FILE):
            os.remove(ATTENDANCE_HISTORY_FILE)
            return True
    except Exception as e:
        st.error(f"Error deleting attendance history: {str(e)}")
    return False

if __name__ == "__main__":
    main()