from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
import redis, os, json
from app.database import get_db
from app.model import ExamSession, Exam
from app.auth import require_role
from dotenv import load_dotenv

load_dotenv()
router = APIRouter(prefix="/sessions", tags=["Exam Sessions"])
redis_cl = redis.from_url(os.getenv("REDIS_URL"))

# State Threshold for Cheating Detection
def get_state(score: int) -> str:
    if score <= 0:
        return "CLEAR"
    elif score <= 30:
        return "CAUTION"
    elif score <= 60:
        return "WARNING"
    elif score <= 85:
        return "ALERT"
    elif score <= 99:
        return "CRITICAL"
    else:
        return "TERMINATED"
    
class StartSession(BaseModel):
    exam_id: str

@router.post("/start")
def start_exam_session(
    session_data: StartSession, 
    current_user = Depends(require_role("student")),
    db: Session = Depends(get_db)
):
    #verify exam exists and is active
    exam= db.query(Exam).filter(Exam.id == session_data.exam_id, Exam.is_active == True).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found or not active")
    
    #create session in postgres
    session = ExamSession(
        student_id= current_user["sub"],
        exam_id= session_data.exam_id,
        penalty_score=0,
        state = "CLEAR"
        )   

    db.add(session)
    db.commit()
    db.refresh(session)

    #store live state in redis for quick updates
    session_id = str(session.id)
    redis_cl.hset(f"session:{session_id}", mapping={
        "penalty_score": 0,
        "state": "CLEAR",
        "student_id": current_user['sub'] 
    })
    redis_cl.expire(f"session:{session_id}", 86400) #expire after 24 hours to prevent stale data

    return {
        "session_id": session_id,
        "state": "CLEAR",
        "penalty_score": 0,
        "message": f"Exam session started for exam '{exam.title}'"
    }

# Get Current Session State
@router.get("/{session_id}/state")
def get_session_state(session_id: str):
    data = redis_cl.hgetall(f"session:{session_id}")
    if not data:
        raise HTTPException(status_code=404, detail="Session not found")
    return{
        "session_id": session_id,
        "state": data[b'state'].decode(),
        "penalty_score": int(data[b"penalty_score"])
    }