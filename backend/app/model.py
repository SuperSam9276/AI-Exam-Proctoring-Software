from sqlalchemy import Column, String, DateTime, Enum, Integer, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base
from datetime import datetime, timezone
import uuid

def now_utc():
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4) #unique ID for each user

    #user details
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False) #hashed password for security

    #role controls what they can access 
    role = Column(
        Enum("student", "proctor", "admin", name="user_roles"), 
        nullable =False,
        default="student"
    )

    #Which college they belong to (multi- tenant support)
    college_id = Column(String(100), nullable=False)

    created_at = Column(DateTime(timezone=True), default=now_utc) #when the user was created

class Exam(Base):
    __tablename__ = "exams"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4) #unique ID for each exam
    title = Column(String(250), nullable=False) #name of the exam
    description = Column(String(500), nullable=True) #optional description of the exam
    college_id = Column(String(100), nullable=False, index=True) #which college this exam belongs to (multi-tenant support)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)#who created the exam
    date = Column(DateTime, nullable=False) #when the exam is scheduled
    duration_minutes = Column(Integer, nullable=False) #duration of the exam in minutes
    is_active = Column(Boolean, default=True) #whether the exam is active or archived
    start_time = Column(DateTime(timezone=True), nullable=False) #when the exam starts
    created_at = Column(DateTime(timezone=True), default=now_utc) #when the exam was created

class ExamSession(Base):
    __tablename__ = "exam_sessions"
    id = Column(UUID(as_uuid=True), primary_key=True, default= uuid.uuid4) #unique ID for each exam session
    student_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)#which student is taking the exam
    exam_id = Column(UUID(as_uuid=True), ForeignKey("exams.id"), nullable= False)#which exam is being taken
    penalty_score = Column(Integer, default=0) #penalty score for any cheating detected
    state = Column(String(50), nullable=False, default="Clear")
    started_at = Column(DateTime(timezone=True), default=now_utc) #when the exam session started
    terminated_at = Column(DateTime(timezone=True), nullable=True) #when the exam session ended (null if still active)
    is_active = Column(Boolean, default= True) #whether the exam session is active or completed/terminated