import os
import json
from datetime import datetime
from security import get_password_hash
from models import Role
import uuid

# Define file paths
current_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(current_dir, 'data')
USERS_FILE = os.path.join(data_dir, 'users.json')


def initialize_users():
    """Initialize users database with default admin, teacher, and student accounts"""
    # Create data directory if it doesn't exist
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    
    # Check if users file already exists
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            users = json.load(f)
            # Only initialize if empty
            if users:
                print("Users database already contains data. Skipping initialization.")
                return
    
    # Create default users
    users = [
        # Admin user
        {
            "id": str(uuid.uuid4()),
            "email": "cordinator@dietms.org",
            "full_name": "System Administrator",
            "hashed_password": get_password_hash("admin123"),
            "role": Role.ADMIN,
            "is_active": True,
            "created_at": datetime.now().isoformat()
        },
        
        # Class teacher
        {
            "id": str(uuid.uuid4()),
            "email": "krushnamadrewar@dietms.org",
            "full_name": "Krushna Madrewar",
            "hashed_password": get_password_hash("teacher123"),
            "role": Role.CLASS_TEACHER,
            "is_active": True,
            "created_at": datetime.now().isoformat(),
            "teacher_info": {
                "department": "EXTC",
                "subjects": ["DC", "M&M", "CN"]
            }
        },
        
        # Regular teacher
        {
            "id": str(uuid.uuid4()),
            "email": "ananddeskmukh@dietms.org",
            "full_name": "Anand Deshmukh",
            "hashed_password": get_password_hash("teacher123"),
            "role": Role.TEACHER,
            "is_active": True,
            "created_at": datetime.now().isoformat(),
            "teacher_info": {
                "department": "EXTC",
                "subjects": ["ESD", "Mini Project"]
            }
        },
        
        # Students
        {
            "id": str(uuid.uuid4()),
            "email": "abhishekpathak@dietms.org",
            "full_name": "Abhishek Pathak",
            "hashed_password": get_password_hash("student123"),
            "role": Role.STUDENT,
            "is_active": True,
            "created_at": datetime.now().isoformat(),
            "student_info": {
                "name": "Abhishek Pathak",
                "student_id": "EC3230",
                "department": "EXTC",
                "year": "TY",
                "division": "B",
                "subjects": ["DC", "M&M", "CN", "ESD", "Mini Project"]
            }
        },
        {
            "id": str(uuid.uuid4()),
            "email": "shubhampitekar@dietms.org",
            "full_name": "Shubham Pitekar",
            "hashed_password": get_password_hash("student123"),
            "role": Role.STUDENT,
            "is_active": True,
            "created_at": datetime.now().isoformat(),
            "student_info": {
                "name": "Shubham Pitekar",
                "student_id": "EC3231",
                "department": "EXTC",
                "year": "TY",
                "division": "B",
                "subjects": ["DC", "M&M", "CN", "ESD", "Mini Project"]
            }
        },
        {
            "id": str(uuid.uuid4()),
            "email": "sachinlonkar@dietms.org",
            "full_name": "Sachin Lonkar",
            "hashed_password": get_password_hash("student123"),
            "role": Role.STUDENT,
            "is_active": True,
            "created_at": datetime.now().isoformat(),
            "student_info": {
                "name": "Sachin Lonkar",
                "student_id": "EC3232",
                "department": "EXTC",
                "year": "TY",
                "division": "B",
                "subjects": ["DC", "M&M", "CN", "ESD", "Mini Project"]
            }
        }
    ]
    
    # Save to file
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=4)
    
    print("Users database initialized with default accounts:")
    print("Admin: admin@example.com / admin123")
    print("Class Teacher: classteacher@example.com / teacher123")
    print("Teacher: teacher@example.com / teacher123")
    print("Student: student@example.com / student123")


if __name__ == "__main__":
    initialize_users()
