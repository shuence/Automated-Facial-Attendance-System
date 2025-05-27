from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import cv2
import numpy as np
from datetime import datetime
import os
import io
from PIL import Image
import json
from deepface.DeepFace import verify, extract_faces, build_model

app = FastAPI(title="Facial Attendance System API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create necessary directories
current_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(current_dir, 'data')
base_dirs = {
    'student_images': os.path.join(data_dir, 'student_images'),
    'attendance': os.path.join(data_dir, 'attendance'),
    'temp': os.path.join(data_dir, 'temp')
}

# Ensure directories exist
for dir_path in base_dirs.values():
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

# Storage paths
STORAGE_FILE = os.path.join(data_dir, 'storage.json')
ATTENDANCE_HISTORY_FILE = os.path.join(data_dir, 'attendance_history.json')

# Pydantic models
class Student(BaseModel):
    name: str
    student_id: Optional[str] = None
    class_name: str

class AttendanceRecord(BaseModel):
    student_name: str
    status: str
    confidence: float
    photo_number: Optional[int] = None
    model: str = "ArcFace"

class AttendanceResponse(BaseModel):
    date: str
    time: str
    class_name: str
    records: List[AttendanceRecord]

def process_face(face_img):
    """Process face array to ensure correct format"""
    try:
        if isinstance(face_img, dict) and 'face' in face_img and isinstance(face_img['face'], np.ndarray):
            face_img = face_img['face']
        
        if not isinstance(face_img, np.ndarray):
            face_img = np.array(face_img)
        
        if face_img.dtype != np.uint8:
            if face_img.dtype in [np.float32, np.float64]:
                face_img = (face_img * 255).astype(np.uint8)
            else:
                face_img = face_img.astype(np.uint8)
        
        if len(face_img.shape) == 3 and face_img.shape[2] == 3:
            if not hasattr(face_img, 'color_format') or face_img.color_format != 'BGR':
                face_img = cv2.cvtColor(face_img, cv2.COLOR_RGB2BGR)
        elif len(face_img.shape) == 2:
            face_img = cv2.cvtColor(face_img, cv2.COLOR_GRAY2BGR)
        
        face_img = cv2.fastNlMeansDenoisingColored(face_img, None, 10, 10, 7, 21)
        face_img = cv2.detailEnhance(face_img, sigma_s=10, sigma_r=0.15)
            
        return face_img
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing face: {str(e)}")

def verify_face(img1_path: str, img2_path: str) -> dict:
    """Compare two face images using ArcFace"""
    try:
        img1 = cv2.imread(img1_path)
        img2 = cv2.imread(img2_path)
        
        if img1 is None or img2 is None:
            raise ValueError("Could not load images")
        
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
        
        similarity = (1 - result['distance']) * 100
        return {
            'verified': similarity >= 50,
            'similarity': similarity,
            'distance': result['distance'],
            'model': 'ArcFace'
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Face verification error: {str(e)}")

@app.post("/students/", response_model=Student)
async def register_student(
    name: str,
    student_id: Optional[str] = None,
    class_name: str = None,
    photo: UploadFile = File(...)
):
    try:
        # Save student photo
        filename = f"{name.lower().replace(' ', '_')}.jpg"
        filepath = os.path.join(base_dirs['student_images'], filename)
        
        # Read and save image
        contents = await photo.read()
        with open(filepath, "wb") as f:
            f.write(contents)
        
        # Update storage
        storage = load_storage()
        if filename not in storage['students']:
            storage['students'].append(filename)
            save_storage(storage)
        
        return {
            "name": name,
            "student_id": student_id,
            "class_name": class_name
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/attendance/", response_model=AttendanceResponse)
async def take_attendance(
    class_name: str,
    photos: List[UploadFile] = File(...)
):
    try:
        results = []
        photo_number = 1
        
        for photo in photos:
            # Save uploaded photo temporarily
            contents = await photo.read()
            temp_path = os.path.join(base_dirs['temp'], f"class_{photo_number}.jpg")
            with open(temp_path, "wb") as f:
                f.write(contents)
            
            # Detect faces
            faces = extract_faces(
                img_path=temp_path,
                enforce_detection=False,
                detector_backend='retinaface',
                align=True
            )
            
            # Process each face
            for face in faces:
                processed_face = process_face(face)
                if processed_face is not None:
                    face_path = os.path.join(base_dirs['temp'], f"face_{photo_number}.jpg")
                    cv2.imwrite(face_path, processed_face)
                    
                    # Compare with all students
                    storage = load_storage()
                    for student_file in storage['students']:
                        student_path = os.path.join(base_dirs['student_images'], student_file)
                        result = verify_face(face_path, student_path)
                        
                        if result and result['verified']:
                            student_name = os.path.splitext(student_file)[0]
                            results.append(
                                AttendanceRecord(
                                    student_name=student_name,
                                    status="Present",
                                    confidence=result['similarity'],
                                    photo_number=photo_number,
                                    model="ArcFace"
                                )
                            )
            
            photo_number += 1
        
        # Create response
        response = AttendanceResponse(
            date=datetime.now().strftime("%Y-%m-%d"),
            time=datetime.now().strftime("%H:%M:%S"),
            class_name=class_name,
            records=results
        )
        
        # Save attendance record
        save_attendance_record(response)
        
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/attendance/history")
async def get_attendance_history(
    date: Optional[str] = None,
    class_name: Optional[str] = None
):
    try:
        if os.path.exists(ATTENDANCE_HISTORY_FILE):
            with open(ATTENDANCE_HISTORY_FILE, 'r') as f:
                history = json.load(f)
            
            if date:
                history = [h for h in history if h['date'] == date]
            if class_name:
                history = [h for h in history if h['class_name'] == class_name]
            
            return history
        return []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def load_storage():
    """Load data from storage file"""
    if os.path.exists(STORAGE_FILE):
        with open(STORAGE_FILE, 'r') as f:
            return json.load(f)
    return {'students': [], 'classes': []}

def save_storage(data):
    """Save data to storage file"""
    with open(STORAGE_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def save_attendance_record(record: AttendanceResponse):
    """Save attendance record to history"""
    try:
        history = []
        if os.path.exists(ATTENDANCE_HISTORY_FILE):
            with open(ATTENDANCE_HISTORY_FILE, 'r') as f:
                history = json.load(f)
        
        history.append(record.dict())
        
        with open(ATTENDANCE_HISTORY_FILE, 'w') as f:
            json.dump(history, f, indent=4)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving attendance record: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 