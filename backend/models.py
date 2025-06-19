from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from enum import Enum


class UserRole(str, Enum):
    ADMIN = "admin"
    TEACHER = "teacher"
    STUDENT = "student"
    CLASS_TEACHER = "class_teacher"


class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    role: UserRole


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: str
    is_active: bool = True
    
    class Config:
        orm_mode = True


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[UserRole] = None


class StudentInfo(BaseModel):
    name: str
    student_id: str
    department: str
    year: str
    division: str
    subjects: List[str]
    photo_filename: Optional[str] = None


class TeacherInfo(BaseModel):
    department: str
    subjects: List[str]
