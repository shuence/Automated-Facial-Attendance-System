import streamlit as st
import requests
import pandas as pd
from datetime import datetime
from PIL import Image
import io
import json

# Configure Streamlit
st.set_page_config(
    page_title="Facial Attendance System",
    page_icon="📸",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API endpoint
API_URL = "http://localhost:8000"

# Custom CSS
st.markdown("""
<style>
    .main {
        padding: 0rem 1rem;
    }
    .stButton>button {
        width: 100%;
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
    .stat-card {
        text-align: center;
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #ffffff;
        border: 1px solid #dee2e6;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

def main():
    st.sidebar.title("📸 Navigation")
    page = st.sidebar.radio("", ["Home", "Student Management", "Take Attendance", "Attendance History"])
    
    if page == "Home":
        show_home()
    elif page == "Student Management":
        show_student_management()
    elif page == "Take Attendance":
        show_attendance()
    elif page == "Attendance History":
        show_attendance_history()

def show_home():
    st.title("👋 Welcome to Facial Attendance System")
    st.write("A modern, AI-powered attendance tracking solution")
    
    # Get statistics from API
    try:
        history = requests.get(f"{API_URL}/attendance/history").json()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            <div class="stat-card">
                <h3>Total Sessions</h3>
                <h2>{}</h2>
            </div>
            """.format(len(history)), unsafe_allow_html=True)
        
        with col2:
            today = datetime.now().strftime("%Y-%m-%d")
            today_sessions = len([h for h in history if h['date'] == today])
            st.markdown("""
            <div class="stat-card">
                <h3>Today's Sessions</h3>
                <h2>{}</h2>
            </div>
            """.format(today_sessions), unsafe_allow_html=True)
        
        with col3:
            total_students = len(set([r['student_name'] for h in history for r in h['records']]))
            st.markdown("""
            <div class="stat-card">
                <h3>Total Students</h3>
                <h2>{}</h2>
            </div>
            """.format(total_students), unsafe_allow_html=True)

        # Show recent attendance preview
        st.subheader("📊 Recent Attendance Preview")
        if history:
            # Get most recent session
            latest_session = history[-1]
            
            # Create DataFrame for attendance display
            df = pd.DataFrame(latest_session['records'])
            
            # Add color coding based on status
            def color_status(val):
                if val == 'Present':
                    return 'background-color: #28a745; color: white'
                return 'background-color: #dc3545; color: white'
            
            # Style the DataFrame
            styled_df = df.style.applymap(color_status, subset=['status'])
            
            # Display session info
            st.write(f"Latest Session: {latest_session['class_name']} - {latest_session['date']} {latest_session['time']}")
            
            # Display styled attendance table
            st.dataframe(styled_df, use_container_width=True)
        else:
            st.info("No attendance records found")
    
    except Exception as e:
        st.error(f"Error fetching statistics: {str(e)}")

def show_student_management():
    st.title("👥 Student Management")
    
    # Student registration form
    with st.form("student_registration"):
        st.write("Register New Student")
        name = st.text_input("Student Name")
        student_id = st.text_input("Student ID (Optional)")
        class_name = st.text_input("Class")
        photo = st.file_uploader("Upload Photo", type=['jpg', 'jpeg', 'png'])
        
        if st.form_submit_button("Register"):
            if name and photo and class_name:
                try:
                    files = {'photo': ('photo.jpg', photo.getvalue(), 'image/jpeg')}
                    data = {
                        'name': name,
                        'student_id': student_id,
                        'class_name': class_name
                    }
                    
                    response = requests.post(
                        f"{API_URL}/students/",
                        data=data,
                        files=files
                    )
                    
                    if response.status_code == 200:
                        st.success("Student registered successfully!")
                    else:
                        st.error(f"Error: {response.text}")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
            else:
                st.error("Please fill in all required fields")

def show_attendance():
    st.title("📸 Take Attendance")
    
    with st.form("attendance_form"):
        class_name = st.text_input("Class Name")
        photos = st.file_uploader(
            "Upload Class Photos",
            type=['jpg', 'jpeg', 'png'],
            accept_multiple_files=True
        )
        
        if st.form_submit_button("Take Attendance"):
            if class_name and photos:
                try:
                    files = [
                        ('photos', (f'photo_{i}.jpg', photo.getvalue(), 'image/jpeg'))
                        for i, photo in enumerate(photos)
                    ]
                    
                    data = {'class_name': class_name}
                    
                    with st.spinner("Processing attendance..."):
                        response = requests.post(
                            f"{API_URL}/attendance/",
                            data=data,
                            files=files
                        )
                        
                        if response.status_code == 200:
                            result = response.json()
                            
                            # Display results
                            st.success("Attendance processed successfully!")
                            
                            # Statistics
                            total = len(result['records'])
                            present = len([r for r in result['records'] if r['status'] == 'Present'])
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                st.metric("Total Students", total)
                            with col2:
                                st.metric("Present", present)
                            
                            # Detailed results
                            df = pd.DataFrame(result['records'])
                            st.dataframe(df)
                        else:
                            st.error(f"Error: {response.text}")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
            else:
                st.error("Please fill in all required fields")

def show_attendance_history():
    st.title("📊 Attendance History")
    
    # Filters
    col1, col2 = st.columns(2)
    with col1:
        date = st.date_input("Select Date")
    with col2:
        class_name = st.text_input("Class Name")
    
    if st.button("Search"):
        try:
            params = {}
            if date:
                params['date'] = date.strftime("%Y-%m-%d")
            if class_name:
                params['class_name'] = class_name
            
            response = requests.get(f"{API_URL}/attendance/history", params=params)
            
            if response.status_code == 200:
                history = response.json()
                
                if history:
                    for record in history:
                        st.markdown(f"""
                        <div style="padding: 1rem; margin: 0.5rem 0; border-radius: 0.5rem; background-color: #f8f9fa; border: 1px solid #dee2e6;">
                            <h4>{record['class_name']} - {record['date']} {record['time']}</h4>
                            <p>Total Records: {len(record['records'])}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Show detailed records
                        df = pd.DataFrame(record['records'])
                        st.dataframe(df)
                else:
                    st.info("No records found")
        except Exception as e:
            st.error(f"Error fetching history: {str(e)}")

if __name__ == "__main__":
    main() 