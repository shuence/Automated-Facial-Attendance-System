from pydantic import BaseModel, EmailStr, Field, validator, constr
from typing import Optional, List, Dict, Any, Union
from enum import Enum
from datetime import datetime, date, time


class Role(str, Enum):
    ADMIN = "admin"
    CLASS_TEACHER = "class_teacher"
    TEACHER = "teacher"
    STUDENT = "student"


class SessionType(str, Enum):
    LECTURE = "lecture"
    PRACTICAL = "practical"
    LAB = "lab"
    TUTORIAL = "tutorial"


class Department(str, Enum):
    COMP = "Computer Engineering"
    IT = "Information Technology"
    EXTC = "Electronics & Telecommunication"
    MECH = "Mechanical Engineering"
    CIVIL = "Civil Engineering"


class Year(str, Enum):
    FE = "First Year"
    SE = "Second Year"
    TE = "Third Year"
    BE = "Fourth Year"


class Division(str, Enum):
    A = "A"
    B = "B"
    C = "C"


class Day(str, Enum):
    MONDAY = "Monday"
    TUESDAY = "Tuesday"
    WEDNESDAY = "Wednesday"
    THURSDAY = "Thursday"
    FRIDAY = "Friday"
    SATURDAY = "Saturday"


class Subject(BaseModel):
    code: str
    name: str
    department: Department
    year: Year


class Lecture(BaseModel):
    subject: Subject
    teacher_id: str
    start_time: str  # Format: "HH:MM"
    end_time: str    # Format: "HH:MM"
    room: str


class Schedule(BaseModel):
    department: Department
    year: Year
    division: Division
    day: Day
    lectures: List[Lecture]


class AttendanceStatus(str, Enum):
    PRESENT = "present"
    ABSENT = "absent"
    LATE = "late"


class AttendanceRecord(BaseModel):
    student_id: str
    status: AttendanceStatus
    timestamp: datetime
    marked_by: str
    image_proof: Optional[str] = None
    location: Optional[Dict[str, float]] = None  # {latitude: float, longitude: float}


class LectureAttendance(BaseModel):
    lecture_id: str
    date: date
    teacher_id: str
    records: List[AttendanceRecord]
    

class AttendanceReport(BaseModel):
    student_id: str
    subject_code: str
    total_lectures: int
    attended_lectures: int
    percentage: float
    last_updated: datetime


class UserBase(BaseModel):
    email: EmailStr = Field(..., example="user@dietms.org")
    name: str = Field(..., min_length=2, max_length=100)
    role: Role

    class Config:
        use_enum_values = True


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)
    department: Optional[Department] = None
    year: Optional[Year] = None
    division: Optional[Division] = None
    roll_number: Optional[constr(regex=r"^EC\d{4}$")] = None
    subjects: Optional[List[Subject]] = None

    @validator('email')
    def validate_email_domain(cls, v):
        if not v.endswith('@dietms.org'):
            raise ValueError('Email must be from dietms.org domain')
        return v


class UserUpdate(UserBase):
    password: Optional[str] = None
    department: Optional[Department] = None
    year: Optional[Year] = None
    division: Optional[Division] = None
    roll_number: Optional[str] = None


class User(UserBase):
    id: str = Field(..., description="Unique user identifier")
    department: Optional[Department] = None
    year: Optional[Year] = None
    division: Optional[Division] = None
    roll_number: Optional[str] = None
    profile_image: Optional[str] = None
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        orm_mode = True


class UserLogin(BaseModel):
    email: EmailStr = Field(..., example="user@dietms.org")
    password: str = Field(..., min_length=6)

    @validator('email')
    def validate_email_domain(cls, v):
        if not v.endswith('@dietms.org'):
            raise ValueError('Email must be from dietms.org domain')
        return v


class UserResponse(BaseModel):
    id: str
    email: EmailStr
    name: str
    role: Role
    department: Optional[Department] = None
    year: Optional[Year] = None
    division: Optional[Division] = None
    is_active: bool


class Token(BaseModel):
    access_token: str
    token_type: str = Field(default="bearer")
    expires_in: int = Field(default=3600)
    user: UserResponse


class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[Role] = None
    exp: Optional[datetime] = None


class StudentInfo(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    student_id: constr(regex=r"^EC\d{4}$")
    department: Department
    year: Year
    division: Division
    subjects: List[Subject]
    photo_filename: Optional[str] = None
    attendance_percentage: Optional[float] = Field(default=0.0, ge=0.0, le=100.0)
    total_classes: Optional[int] = Field(default=0, ge=0)
    classes_attended: Optional[int] = Field(default=0, ge=0)
    
    class Config:
        use_enum_values = True


class TeacherInfo(BaseModel):
    department: Department
    subjects: List[Subject]
    is_class_teacher: bool = False
    assigned_classes: List[str] = []
    total_sessions: Optional[int] = Field(default=0, ge=0)
    
    class Config:
        use_enum_values = True


class ClassBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    department: Department
    year: Year
    division: Division
    subjects: List[Subject]
    
    class Config:
        use_enum_values = True


class ClassCreate(ClassBase):
    class_teacher_id: Optional[str] = None


class Class(ClassBase):
    id: str
    teachers: List[Dict[str, Any]]
    created_at: datetime

    class Config:
        orm_mode = True


class AttendanceRecord(BaseModel):
    id: str = Field(..., description="Unique attendance record identifier")
    date: date = Field(..., description="Date of attendance")
    class_id: str = Field(..., description="Class identifier")
    subject: Subject
    teacher_id: str = Field(..., description="Teacher who took attendance")
    students: Dict[str, bool] = Field(..., description="Student IDs mapped to their attendance status")
    session_type: SessionType
    start_time: time
    end_time: time
    note: Optional[str] = Field(None, max_length=500)
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_locked: bool = Field(default=False, description="Whether attendance can be modified")

    class Config:
        use_enum_values = True


class AttendanceCreate(BaseModel):
    class_id: str
    date: date = Field(..., description="Date of attendance")
    subject: Subject
    session_type: SessionType
    attendance: Dict[str, bool] = Field(..., description="Student IDs mapped to their attendance status")
    start_time: time = Field(..., description="Session start time")
    end_time: time = Field(..., description="Session end time")
    note: Optional[str] = Field(None, max_length=500)

    class Config:
        use_enum_values = True


class AttendanceUpdate(BaseModel):
    attendance: Dict[str, bool]
    note: Optional[str] = Field(None, max_length=500)


class SubjectAttendance(BaseModel):
    name: Subject
    total_classes: int = Field(..., ge=0)
    attended_classes: int = Field(..., ge=0)
    percentage: float = Field(..., ge=0.0, le=100.0)
    last_attendance: Optional[date] = None
    attendance_dates: List[date] = []

    @validator('percentage')
    def validate_percentage(cls, v):
        return round(v, 2)

    @validator('attended_classes')
    def validate_attended_classes(cls, v, values):
        if 'total_classes' in values and v > values['total_classes']:
            raise ValueError('Attended classes cannot be more than total classes')
        return v

    class Config:
        use_enum_values = True


class SubjectStats(BaseModel):
    subject: Subject
    total_classes: int = Field(..., ge=0)
    attended_classes: int = Field(..., ge=0)
    percentage: float = Field(..., ge=0.0, le=100.0)
    last_class: Optional[date] = None
    upcoming_class: Optional[date] = None
    
    class Config:
        use_enum_values = True


class AttendanceStats(BaseModel):
    date: date
    subject: Subject
    status: bool
    teacher: str
    note: Optional[str] = None


class MonthlyTrend(BaseModel):
    month: str
    attendance_percentage: float = Field(..., ge=0.0, le=100.0)
    total_classes: int = Field(..., ge=0)
    attended_classes: int = Field(..., ge=0)


class StudentDashboard(BaseModel):
    overall_attendance: float = Field(..., ge=0.0, le=100.0)
    total_classes: int = Field(..., ge=0)
    classes_attended: int = Field(..., ge=0)
    subjects: List[SubjectStats]
    recent_attendance: List[AttendanceStats]
    monthly_trend: List[MonthlyTrend]
    upcoming_sessions: List[ScheduleSession]
    warnings: List[str] = []

    class Config:
        use_enum_values = True


class TeacherSession(BaseModel):
    id: str
    time: str
    subject: Subject
    class_name: str
    room: str
    is_practical: bool
    batch: Optional[str] = None
    attendance_taken: bool = False


class TeacherStats(BaseModel):
    total_sessions: int = Field(..., ge=0)
    this_week_sessions: int = Field(..., ge=0)
    avg_attendance: float = Field(..., ge=0.0, le=100.0)
    total_students: int = Field(..., ge=0)


class TeacherDashboard(BaseModel):
    subjects: List[Subject]
    today_schedule: List[TeacherSession]
    stats: TeacherStats
    subject_stats: List[SubjectStats]
    recent_sessions: List[AttendanceRecord]
    upcoming_sessions: List[ScheduleSession]

    class Config:
        use_enum_values = True


class TimeSlot(BaseModel):
    start_time: time
    end_time: time

    @validator('end_time')
    def validate_end_time(cls, v, values):
        if 'start_time' in values and v <= values['start_time']:
            raise ValueError('End time must be after start time')
        return v


class ScheduleSession(BaseModel):
    id: str = Field(..., description="Unique session identifier")
    day: Day
    time_slot: TimeSlot
    duration: int = Field(..., ge=30, le=180, description="Duration in minutes")
    type: SessionType
    subject: Subject
    room: str = Field(..., min_length=2, max_length=10)
    batch: Optional[str] = Field(None, regex=r"^[A-C][1-3]$")
    teacher_id: str
    class_id: str
    is_recurring: bool = True
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    
    class Config:
        use_enum_values = True


class ScheduleCreate(BaseModel):
    day: Day
    start_time: time
    duration: int = Field(..., ge=30, le=180)
    type: SessionType
    subject: Subject
    room: str = Field(..., min_length=2, max_length=10)
    batch: Optional[str] = Field(None, regex=r"^[A-C][1-3]$")
    is_recurring: bool = True
    start_date: Optional[date] = None
    end_date: Optional[date] = None

    class Config:
        use_enum_values = True


class ScheduleFilter(BaseModel):
    department: Optional[Department] = None
    year: Optional[Year] = None
    division: Optional[Division] = None
    subject: Optional[Subject] = None
    teacher_id: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    session_type: Optional[SessionType] = None


class DepartmentStats(BaseModel):
    department: Department
    students: int = Field(..., ge=0)
    teachers: int = Field(..., ge=0)
    classes: int = Field(..., ge=0)
    avg_attendance: float = Field(..., ge=0.0, le=100.0)

    class Config:
        use_enum_values = True


class AdminStats(BaseModel):
    total_students: int = Field(..., ge=0)
    total_teachers: int = Field(..., ge=0)
    class_teachers: int = Field(..., ge=0)
    departments: int = Field(..., ge=0)
    active_users: int = Field(..., ge=0)


class AttendanceOverview(BaseModel):
    average: float = Field(..., ge=0.0, le=100.0)
    below_threshold: int = Field(..., ge=0)
    trend: List[Dict[str, Union[str, float]]]


class SystemMetrics(BaseModel):
    active_sessions: int = Field(..., ge=0)
    today_attendance: int = Field(..., ge=0)
    total_classes: int = Field(..., ge=0)
    api_requests: int = Field(..., ge=0)
    storage_usage: float = Field(..., ge=0.0)
    last_backup: Optional[datetime] = None


class ActivityLog(BaseModel):
    timestamp: datetime
    action: str
    user: str
    details: str
    ip_address: Optional[str] = None


class AdminDashboard(BaseModel):
    stats: AdminStats
    department_stats: List[DepartmentStats]
    attendance: AttendanceOverview
    recent_activity: List[ActivityLog]
    system: SystemMetrics

    class Config:
        use_enum_values = True


class ReportType(str, Enum):
    DEPARTMENT = "department"
    YEAR = "year"
    SUBJECT = "subject"
    TEACHER = "teacher"
    DAILY = "daily"


class SystemReport(BaseModel):
    type: ReportType
    start_date: date
    end_date: date
    data: List[Dict[str, Any]]
    generated_at: datetime = Field(default_factory=datetime.now)
    generated_by: str

    class Config:
        use_enum_values = True


class NotificationType(str, Enum):
    ATTENDANCE_REMINDER = "attendance_reminder"
    LOW_ATTENDANCE = "low_attendance"
    CLASS_CANCELLED = "class_cancelled"
    CLASS_RESCHEDULED = "class_rescheduled"
    SYSTEM = "system"


class Notification(BaseModel):
    id: str
    type: NotificationType
    title: str
    message: str
    recipients: List[str]  # List of user IDs
    created_at: datetime
    read_by: List[str] = Field(default_factory=list)  # List of user IDs who have read
    link: Optional[str] = None  # Optional link to relevant page/resource


class SystemSettings(BaseModel):
    min_attendance_percentage: float = 75.0
    late_threshold_minutes: int = 10
    attendance_reminder_time: str = "08:00"  # Format: "HH:MM"
    allow_facial_recognition: bool = True
    max_class_size: int = 80
    default_semester_start: str  # Format: "YYYY-MM-DD"
    default_semester_end: str    # Format: "YYYY-MM-DD"
    working_days: List[Day]
    maintenance_mode: bool = False

    @validator('min_attendance_percentage')
    def validate_attendance_percentage(cls, v):
        if not 0 <= v <= 100:
            raise ValueError('Attendance percentage must be between 0 and 100')
        return v

    @validator('late_threshold_minutes')
    def validate_late_threshold(cls, v):
        if not 0 <= v <= 60:
            raise ValueError('Late threshold must be between 0 and 60 minutes')
        return v
