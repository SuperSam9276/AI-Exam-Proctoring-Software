from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
import redis, os, base64, asyncio, anyio
from datetime import datetime, timezone
from app.database import get_db
from app.model import ExamSession, Exam, ViolationEvents, User, StateTransition
from app.auth import require_role, get_current_user
from app.ws_manager import ws_manager
from app.penalty import (
    PENALTY_MATRIX,
    PENALTY_POINTS,
    get_state,
    STATE_ACTIONS,
    COOLDOWN_SECS,
    STREAK_WINDOWS_SECS,     
)
from app.penalty import get_combined_multiplier
from app.detection import (
    analyse_face,
    analyse_objects,
    analyse_eye_gaze,
    analyse_head_pose,
    analyse_audio,
    analyse_liveness
)
from dotenv import load_dotenv

load_dotenv()

router   = APIRouter(prefix="/session", tags=["Exam Sessions"])

# decode_responses=True — all Redis responses are strings, no .decode() needed
redis_cl = redis.from_url(
    os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    decode_responses=True
)


# ── Session Start ─────────────────────────────────────────────────

class StartSession(BaseModel):
    exam_id: str


@router.post("/start")
def start_exam_session(
    session_data: StartSession,
    current_user: User = Depends(require_role("student")),  # now returns User object
    db: Session = Depends(get_db)
):
    exam = db.query(Exam).filter(
        Exam.id == session_data.exam_id,
        Exam.is_active == True
    ).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found or not active")

    session = ExamSession(
        student_id    = current_user.id,        # fixed: was current_user["sub"]
        exam_id       = session_data.exam_id,
        penalty_score = 0,
        state         = "CLEAR"
    )

    db.add(session)
    db.commit()
    db.refresh(session)

    session_id = str(session.id)
    redis_cl.hset(f"session:{session_id}", mapping={
        "penalty_score": 0,
        "state":         "CLEAR",
        "student_id":    str(current_user.id)   # fixed: was current_user["sub"]
    })
    redis_cl.expire(f"session:{session_id}", 86400)

    return {
        "session_id":    session_id,
        "state":         "CLEAR",
        "penalty_score": 0,
        "message":       f"Exam session started for exam '{exam.title}'"
    }


# ── Session State ─────────────────────────────────────────────────

@router.get("/{session_id}/state")
def get_session_state(session_id: str):
    data = redis_cl.hgetall(f"session:{session_id}")
    if not data:
        raise HTTPException(status_code=404, detail="Session not found")

    # fixed: decode_responses=True means keys/values are already strings
    return {
        "session_id":    session_id,
        "state":         data.get("state", "CLEAR"),
        "penalty_score": int(data.get("penalty_score", 0))
    }


# ── Penalty Engine ────────────────────────────────────────────────

def process_violation(session_id: str, event_type: str, db: Session, current_user):
    """
    Shared penalty engine — called by record_violation, receive_frame, receive_audio.
    event_type must be a plain string key from PENALTY_MATRIX.
    """
    if event_type not in PENALTY_MATRIX:
        return None

    session_key  = f"session:{session_id}"
    cooldown_key = f"cooldown:{session_id}:{event_type}"
    streak_key   = f"streak:{session_id}:{event_type}"

    current_score = int(redis_cl.hget(session_key, "penalty_score") or 0)
    current_state = redis_cl.hget(session_key, "state") or "CLEAR"

    # Cooldown check
    if redis_cl.exists(cooldown_key):
        return {
            "status":        "cooldown",
            "event_type":    event_type,
            "current_state": current_state,
            "penalty_score": current_score
        }

    redis_cl.set(cooldown_key, "1", ex=COOLDOWN_SECS)

    # Streak multiplier
    streak_count = redis_cl.incr(streak_key)
    if streak_count == 1:
        redis_cl.expire(streak_key, STREAK_WINDOWS_SECS)

    multiplier     = get_combined_multiplier(streak_count, current_state)
    base_points    = PENALTY_POINTS[event_type]
    points_applied = int(base_points * multiplier)
    new_score      = current_score + points_applied
    new_state      = get_state(new_score)

    redis_cl.hset(session_key, mapping={
        "penalty_score": new_score,
        "state":         new_state
    })

    # Handle termination
    if new_state == "TERMINATED":
        session = db.query(ExamSession).filter(
            ExamSession.id == session_id
        ).first()
        if session:
            session.state         = "TERMINATED"
            session.terminated_at = datetime.now(timezone.utc)

    # Log violation
    violation = ViolationEvents(
        session_id  = session_id,
        event_type  = event_type,
        points      = points_applied,
        multiplier  = multiplier,
        score_after = new_score,
        state_after = new_state
    )
    db.add(violation)

    # Log state transition
    if new_state != current_state:
        transition = StateTransition(
            session_id       = session_id,
            from_state       = current_state,
            to_state         = new_state,
            triggering_event = event_type,
            score_at_change  = new_score
        )
        db.add(transition)

    db.commit()

    # Broadcast to invigilator dashboard
    try:
        ws_manager.broadcast_sync({
            "type":       "score_update",
            "session_id": session_id,
            "score":      new_score,
            "state":      new_state,
            "event_type": event_type,
        })
    except Exception as e:
        print(f"[ws] Broadcast error: {e}")

    actions = STATE_ACTIONS[new_state]
    return {
        "status":            "recorded",
        "event_type":        event_type,
        "base_points":       base_points,
        "multiplier":        multiplier,
        "points_applied":    points_applied,
        "new_score":         new_score,
        "new_state":         new_state,
        "student_alert":     PENALTY_MATRIX[event_type].get("student_alert"),
        "student_message":   actions["student_message"],
        "exam_paused":       actions["exam_paused"],
        "invigilator_alert": actions["invigilator_alert"],
    }


# ── Violation Event Endpoint ──────────────────────────────────────

@router.post("/{session_id}/violation_event")
def record_violation(
    session_id:   str,
    payload:      dict,
    current_user: User = Depends(get_current_user),
    db:           Session = Depends(get_db)
):
    event_type = payload.get("event_type")
    if not event_type:
        raise HTTPException(status_code=400, detail="event_type is required")

    session = db.query(ExamSession).filter(
        ExamSession.id == session_id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.state == "TERMINATED":
        raise HTTPException(status_code=400, detail="Session already terminated")

    result = process_violation(session_id, event_type, db, current_user)
    if result is None:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown event type: {event_type}. "
                   f"Valid types: {list(PENALTY_MATRIX.keys())}"
        )

    return result


# ── Frame Endpoint ────────────────────────────────────────────────

class FrameData(BaseModel):
    frame_data: str   # base64 encoded JPEG


@router.post("/{session_id}/frame")
def receive_frame(
    session_id:   str,
    frame:        FrameData,
    current_user: User = Depends(get_current_user),
    db:           Session = Depends(get_db)
):
    session = db.query(ExamSession).filter(
        ExamSession.id == session_id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.state == "TERMINATED":
        raise HTTPException(status_code=400, detail="Session already terminated")

    # Run detections
    all_violations = []


    face_violations   = analyse_face(frame.frame_data, session_id)
    gaze_violations   = analyse_eye_gaze(frame.frame_data)
    head_violations   = analyse_head_pose(frame.frame_data)
    object_violations = analyse_objects(frame.frame_data)
    all_violations    = face_violations + gaze_violations + head_violations + object_violations
   

    print(f"[frame] {session_id}: {all_violations}")

   
    for event_type in all_violations:
        process_violation(session_id, event_type, db, current_user)

    session_key   = f"session:{session_id}"
    current_score = int(redis_cl.hget(session_key, "penalty_score") or 0)
    current_state = redis_cl.hget(session_key, "state") or "CLEAR"

    
    print(f"[frame] {session_id} | state: {current_state} | score: {current_score}")

    return {
        "received":      True,
        "violations":    all_violations,
        "current_state": current_state,
        "penalty_score": current_score
    }


#-------------Liveness Endpoint----------------------------
class LivenessIn(BaseModel):
    frame_data: str


@router.post("/{session_id}/liveness")
def receive_liveness(
    session_id: str,
    frame: LivenessIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    session = db.query(ExamSession).filter(
        ExamSession.id == session_id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    all_violations = analyse_liveness(frame.frame_data, session_id)

    for event_type in all_violations:
        process_violation(session_id, event_type, db, user)

    return {
        "received":         True,
        "violations_found": all_violations
    }



# ── Audio Endpoint ────────────────────────────────────────────────

class AudioIn(BaseModel):
    audio_data: str   # base64 encoded raw PCM bytes


@router.post("/{session_id}/audio")
def receive_audio(
    session_id:   str,
    audio:        AudioIn,
    current_user: User = Depends(get_current_user),
    db:           Session = Depends(get_db)
):
    session = db.query(ExamSession).filter(
        ExamSession.id == session_id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    try:
        audio_bytes = base64.b64decode(audio.audio_data)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid audio data")

    violations = analyse_audio(audio_bytes)
    print(f"[audio] {session_id}: {violations}")

    # fixed: call process_violation directly with plain string, not record_violation
    for event_type in violations:
        process_violation(session_id, event_type, db, current_user)

    return {
        "received":        True,
        "violations_found": violations
    }


# ── Active Session Lookup ─────────────────────────────────────────

@router.get("/my-active")
def get_my_active_session(
    current_user: User = Depends(get_current_user),
    db:           Session = Depends(get_db)
):
    session = db.query(ExamSession).filter(
        ExamSession.student_id == current_user.id,
        ExamSession.state      != "TERMINATED",
        ExamSession.terminated_at == None
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="No active session found")

    return {
        "session_id": str(session.id),
        "exam_id":    str(session.exam_id),
        "state":      session.state
    }