from fastapi import APIRouter, Depends, HTTPException, status  
from sqlalchemy.orm import Session
from pydantic import BaseModel
import redis, os, json, base64
from datetime import datetime, timedelta, timezone
from app.database import get_db
from app.model import ExamSession, Exam, ViolationEvents, User, StateTransition
from app.auth import require_role, get_current_user
from app.penalty import (
    PENALTY_MATRIX,
    PENALTY_POINTS,
    get_state,
    STATE_ACTIONS,
    COOLDOWN_SECS,
    STREAK_WINDOWS_SECS,
    DEESCALATION_MIN_INTERVAL
)
from app.penalty import get_combined_multiplier
from dotenv import load_dotenv

load_dotenv()
router = APIRouter(prefix="/session", tags=["Exam Sessions"])
redis_cl = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))

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
    print(f"Here's the Input: {session_id}")
    data = redis_cl.hgetall(f"session:{session_id}")
    if not data:
        raise HTTPException(status_code=404, detail="Session not found")
    return{
        "session_id": session_id,
        "state": data[b'state'].decode(),
        "penalty_score": int(data[b"penalty_score"])
    }
        


# receive violation event and update session state
@router.post("/{session_id}/violation_event")
def record_violation(
    session_id: str, 
    payload: dict, 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
    ):
    event_type = payload.get("event_type")
    if event_type not in PENALTY_MATRIX:
        raise HTTPException(status_code=400, detail=f"Unknown event type: {event_type}."
                            f" Valid types: {list(PENALTY_MATRIX.keys())}"
                            )
    #Loading session data from db
    session = db.query(ExamSession).filter(ExamSession.id == session_id).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session.state == "TERMINATED":
        raise HTTPException(status_code=403, detail="Session already terminated due to excessive violations")

    #load live score form redis
    score_key= f"session:{session_id}"
    state_key = f"session:{session_id}"
    cooldown_key = f"cooldown:{session_id}:{event_type}"
    streak_key = f"streak:{session_id}:{event_type}"
    deescalation_key = f"deesc:{session_id}"

    current_score = int(redis_cl.hget(score_key, "penalty_score") or 0)
    current_state = redis_cl.hget(state_key, "state").decode() if redis_cl.hget(state_key, "state") else "CLEAR"

    #cooldown check
    if redis_cl.exists(cooldown_key):
        return{
            "status": "cooldown",
            "message": f"Event '{event_type}' is in cooldown. No additional penalty applied.",
            "current_state": current_state,
            "penalty_score": current_score
        }
    
    #set cooldown
    redis_cl.set(cooldown_key, "1", ex= COOLDOWN_SECS)


    #streak multiplier check
    streak_count = redis_cl.incr(streak_key)
    multiplier = get_combined_multiplier(streak_count, current_state)

    base_point = PENALTY_POINTS[event_type]
    points_applied = int(base_point * multiplier)
    new_score = current_score + points_applied
    new_state = get_state(new_score)

    #changing score in redis
    redis_cl.hset(score_key, "penalty_score", new_score)
    redis_cl.hset(state_key, "state", new_state)
    
    #Handling Terminated State
    if new_state == "TERMINATED":
        session.state = "TERMINATED"
        session.ended_at = datetime.now(timezone.utc)
        db.commit()

    #Log violation event in postgres
    violation = ViolationEvents(
        session_id = session_id,
        event_type = event_type,
        points = points_applied,
        multiplier = multiplier,
        score_after = new_score,
        state_after = new_state
    )
    db.add(violation)
    # Log state transition if state changed
    if new_state != current_state:
        transition = StateTransition(
            session_id = session_id,
            from_state = current_state,
            to_state = new_state,
            triggering_event = event_type,
            score_at_change = new_score
        )

        db.add(transition)
    db.commit()


class FrameData(BaseModel):
    frame_data: str  # base64 encoded image data
# Recieving frames for live proctoring (optional, can be used for advanced features like real-time alerts or post-exam review)
@router.post("/{session_id}/frame")
def receive_frame(
    session_id: str, 
    frame: FrameData, 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    session = db.query(ExamSession).filter(ExamSession.id == session_id).first()
    redis_key = f"session:{session_id}"
    data = redis_cl.hgetall(redis_key)
    if not session or not data:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.state == "TERMINATED":
        raise HTTPException(status_code=403, detail="Session already terminated due to excessive violations")
    
    try:
        # Decode base64 image data
        image_data = frame.frame_data.split(",")[1] if "," in frame.frame_data else frame.frame_data
        image_bytes = base64.b64decode(image_data)
        # Here you can process the image data as needed (e.g., save to disk, run through ML model, etc.)
        # For demonstration, we'll just log the receipt of the frame
        print(f"Received frame for session {session_id} at {datetime.now(timezone.utc)}")
    
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid frame data")
    

    score = int(data.get(b"penalty_score") or 0)
    state = data.get(b"state", b"CLEAR").decode()

    print(f"Received frame for session {session_id} at {datetime.now(timezone.utc)} with current state {state} and score {score}")

    return {"status": "success", "message": "Frame received", "current_state": state, "penalty_score": score}