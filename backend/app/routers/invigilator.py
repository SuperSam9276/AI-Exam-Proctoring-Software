from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
import redis, os, asyncio
from datetime import datetime, timezone
from app.penalty import STATE_FLOOR_SCORE
from app.database import get_db
from app import model
from app.auth import get_current_user
from app.ws_manager import ws_manager


router = APIRouter(prefix="/invigilator", tags=["Invigilator"])

redis_cl = redis.from_url(
    os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    decode_responses=True
)


@router.get("/sessions")
def get_active_sessions(
    db: Session = Depends(get_db),
    current_user: model.User = Depends(get_current_user)
):
    if current_user.role not in ["invigilator", "admin", "senior_admin"]:
        raise HTTPException(status_code=403, detail="Access denied")

    sessions = db.query(model.ExamSession).filter(
        model.ExamSession.state != "TERMINATED",
        model.ExamSession.terminated_at == None
    ).all()

    result = []
    for s in sessions:
        session_key = f"session:{s.id}"
        redis_data  = redis_cl.hgetall(session_key)

        score = int(redis_data.get("penalty_score", 0))
        state = redis_data.get("state", "CLEAR")

        student = db.query(model.User).filter(
            model.User.id == s.student_id
        ).first()

        exam = db.query(model.Exam).filter(
            model.Exam.id == s.exam_id
        ).first()

        last_v = db.query(model.ViolationEvents).filter(
            model.ViolationEvents.session_id == s.id
        ).order_by(
            model.ViolationEvents.detected_at.desc()
        ).first()

        result.append({
            "session_id":     str(s.id),
            "student_name":   student.name if student else "Unknown",
            "exam_title":     exam.title if exam else "Unknown",
            "score":          score,
            "state":          state,
            "last_violation": last_v.event_type if last_v else None,
            "started_at":     s.started_at.isoformat() if s.started_at else None
        })

    return result

STATE_ORDER = ["CLEAR", "CAUTION", "WARNING", "ALERT", "CRITICAL", "TERMINATED"]


class ActionPayload(BaseModel):
    reason: str = ""


@router.post("/sessions/{session_id}/resume")
async def resume_session(
    session_id: str,
    payload: ActionPayload,
    db: Session = Depends(get_db),
    current_user: model.User = Depends(get_current_user)
):
    if current_user.role not in ["invigilator", "admin", "senior_admin"]:
        raise HTTPException(status_code=403, detail="Access denied")

    session_key   = f"session:{session_id}"
    current_state = redis_cl.hget(session_key, "state") or "CLEAR"

    if current_state == "TERMINATED":
        raise HTTPException(status_code=400, detail="Cannot resume terminated session")

    # Drop one state level
    idx       = STATE_ORDER.index(current_state)
    new_state = STATE_ORDER[max(0, idx - 1)]
    new_score = STATE_FLOOR_SCORE[new_state]

    redis_cl.hset(session_key, mapping={
        "state":         new_state,
        "penalty_score": new_score
    })

    # Broadcast to dashboard
    await ws_manager.broadcast({
        "type":       "score_update",
        "session_id": session_id,
        "score":      new_score,
        "state":      new_state,
        "event_type": f"resumed_by_{current_user.full_name}"
    })

    return {"status": "resumed", "new_state": new_state, "new_score": new_score}


@router.post("/sessions/{session_id}/terminate")
async def terminate_session(
    session_id: str,
    payload: ActionPayload,
    db: Session = Depends(get_db),
    current_user: model.User = Depends(get_current_user)
):
    if current_user.role not in ["invigilator", "admin", "senior_admin"]:
        raise HTTPException(status_code=403, detail="Access denied")

    session = db.query(model.ExamSession).filter(
        model.ExamSession.id == session_id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    session.status   = "terminated"
    session.ended_at = datetime.now(timezone.utc)
    db.commit()

    session_key = f"session:{session_id}"
    redis_cl.hset(session_key, mapping={
        "state":         "TERMINATED",
        "penalty_score": 100
    })

    await ws_manager.broadcast({
        "type":       "score_update",
        "session_id": session_id,
        "score":      100,
        "state":      "TERMINATED",
        "event_type": f"terminated_by_{current_user.name}"
    })

    return {"status": "terminated"}