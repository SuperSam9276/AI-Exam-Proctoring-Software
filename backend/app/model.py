from sqlalchemy import Column, String, DateTime, Enum, Integer, ForeignKey, Boolean, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
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

    session= relationship("ExamSession", back_populates="student", foreign_keys="ExamSession.student_id") #relationship to exam sessions for students


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

    session = relationship("ExamSession", back_populates="exam") #relationship to exam sessions for this exam


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

    exam = relationship("Exam", back_populates="session") #relationship to the exam being taken
    transition = relationship("StateTransition", back_populates="session", cascade="all, delete-orphan") #relationship to state transitions for this session
    student = relationship("User", back_populates="session", foreign_keys=[student_id]) #relationship to the student taking the exam
    violation = relationship("ViolationEvents", back_populates="session", cascade="all, delete-orphan") #relationship to violation events for this session


class ViolationEvents(Base):
    __tablename__ = "violation_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default= uuid.uuid4) #unique ID for each violation event
    session_id = Column(UUID(as_uuid=True), ForeignKey(("exam_sessions.id"), ondelete= "CASCADE"), nullable=False) #which exam session this violation belongs to
    event_type = Column(String(100), nullable=False) #type of violation (e.g., "Face Not Detected", "Multiple Faces Detected", "Suspicious Sound Detected")
    points = Column(Integer, default=0, nullable = False) #points assigned for this violation (used for penalty scoring)
    multiplier = Column(Float, default=1.0, nullable= False) #multiplier for the violation points (e.g., repeat offenses may have higher multipliers)
    score_after = Column(Integer, nullable=False) #the penalty score after applying this violation
    state_after = Column(String(50), nullable=False, default="Clear") #the state of the exam session after this violation (e.g., "Clear", "Warning", "Flagged", "Terminated")
    detected_at = Column(DateTime(timezone=True), default=now_utc) #when the violation was detected
    session = relationship("ExamSession", back_populates="violation") #relationship to the exam session this violation belongs to

class StateTransition(Base):
    __tablename__ = "state_transitions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4) #unique ID for each state transition rule
    session_id= Column(UUID(as_uuid=True), ForeignKey("exam_sessions.id", ondelete="CASCADE"), nullable=False) #which exam session this state transition belongs to
    from_state = Column(String(50), nullable=False) #the state before the transition (e.g., "Clear", "Warning", "Flagged")
    to_state = Column(String(50), nullable=False) #the state after the transition (e.g., "Warning", "Flagged", "Terminated")
    triggering_event = Column(String(100), nullable=False) #the event that triggered this state transition (e.g., "Face Not Detected", "Multiple Faces Detected")
    score_at_change = Column(Integer, nullable= False) #the penalty score at the time of state change
    changed_at = Column(DateTime(timezone=True), default=now_utc) #when the state transition occurred
    
    session = relationship("ExamSession", back_populates="transition") #relationship to the exam session this state transition belongs to
    