import streamlit as st
from deepface import DeepFace
import cv2
import numpy as np
import pandas as pd
from datetime import datetime
import os
from PIL import Image
import shutil

# Create necessary directories if they don't exist
os.makedirs("data/student_images", exist_ok=True)
os.makedirs("data/attendance", exist_ok=True)
os.makedirs("data/temp", exist_ok=True)

# Set page config
st.set_page_config(page_title="Facial Attendance System", layout="wide")

# Initialize session state variables
if 'attendance_df' not in st.session_state:
    st.session_state.attendance_df = pd.DataFrame(columns=[
        'Date', 'Class', 'Division', 'Subject', 'Period', 'Student_Name', 'Status'
    ])

def save_attendance():
    """Save attendance to CSV file"""
    filename = f"data/attendance/attendance_{datetime.now().strftime('%Y%m%d')}.csv"
    st.session_state.attendance_df.to_csv(filename, index=False)

def verify_face(img1_path, img2_path):
    """Verify if two faces match"""
    try:
        result = DeepFace.verify(img1_path=img1_path, img2_path=img2_path, model_name='VGG-Face')
        return result['verified']
    except Exception as e:
        return False

def main():
    st.title("Facial Attendance System")
    
    # Sidebar for class information
    with st.sidebar:
        st.header("Class Information")
        class_name = st.text_input("Class")
        division = st.text_input("Division")
        subject = st.text_input("Subject")
        period = st.selectbox("Period", list(range(1, 9)))
        
        st.header("Upload Student Images")
        student_images = st.file_uploader(
            "Upload individual student images",
            type=['jpg', 'jpeg', 'png'],
            accept_multiple_files=True
        )
        
        if student_images:
            for img in student_images:
                # Save student images
                img_path = os.path.join("data/student_images", img.name)
                with open(img_path, "wb") as f:
                    f.write(img.getbuffer())
                st.success(f"Saved {img.name}")
    
    # Main content
    st.header("Take Attendance")
    attendance_image = st.file_uploader(
        "Upload class image for attendance",
        type=['jpg', 'jpeg', 'png']
    )
    
    if attendance_image is not None:
        # Display the uploaded image
        image = Image.open(attendance_image)
        st.image(image, caption="Uploaded Image", use_column_width=True)
        
        if st.button("Take Attendance"):
            if not all([class_name, division, subject]):
                st.error("Please fill in all class information!")
                return
                
            # Process attendance
            with st.spinner("Processing attendance..."):
                # Save the attendance image temporarily
                temp_image_path = os.path.join("data/temp", "class_photo.jpg")
                image.save(temp_image_path)
                
                # Get all student images and their names
                student_files = os.listdir("data/student_images")
                present_students = set()
                
                # Detect faces in the class photo
                try:
                    faces = DeepFace.extract_faces(temp_image_path, enforce_detection=False)
                    
                    # For each detected face, compare with student photos
                    for face_obj in faces:
                        face_img = face_obj['face']
                        temp_face_path = os.path.join("data/temp", "temp_face.jpg")
                        cv2.imwrite(temp_face_path, cv2.cvtColor(face_img, cv2.COLOR_RGB2BGR))
                        
                        # Compare with each student photo
                        for student_file in student_files:
                            student_path = os.path.join("data/student_images", student_file)
                            if verify_face(temp_face_path, student_path):
                                student_name = os.path.splitext(student_file)[0]
                                present_students.add(student_name)
                                break
                
                except Exception as e:
                    st.error(f"Error processing image: {str(e)}")
                    return
                
                # Update attendance DataFrame
                current_date = datetime.now().strftime("%Y-%m-%d")
                
                # Mark all known students
                for student_file in student_files:
                    student_name = os.path.splitext(student_file)[0]
                    status = "Present" if student_name in present_students else "Absent"
                    new_record = pd.DataFrame([{
                        'Date': current_date,
                        'Class': class_name,
                        'Division': division,
                        'Subject': subject,
                        'Period': period,
                        'Student_Name': student_name,
                        'Status': status
                    }])
                    st.session_state.attendance_df = pd.concat(
                        [st.session_state.attendance_df, new_record],
                        ignore_index=True
                    )
                
                # Clean up temporary files
                shutil.rmtree("data/temp")
                os.makedirs("data/temp", exist_ok=True)
                
                # Save attendance
                save_attendance()
                st.success("Attendance marked successfully!")
    
    # Display attendance records
    if not st.session_state.attendance_df.empty:
        st.header("Attendance Records")
        st.dataframe(st.session_state.attendance_df)

if __name__ == "__main__":
    main() 