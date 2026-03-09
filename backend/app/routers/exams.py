from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime, timezone
from app.database import get_db
from app.model import Exam, User
from app.auth import get_current_user, require_role

router = APIRouter(prefix="/exams", tags=["Exams"])
class ExamCreate(BaseModel):
    name: str
    description: str = None
    date: datetime
    duration_minutes: int
    start_time: datetime

@router.post("/creation", status_code=201)
def create_exam(
    exam_data: ExamCreate, 
    current_user = Depends(require_role("admin")), 
    db: Session = Depends(get_db)
):
    exam = Exam(
        title= exam_data.name,
        description= exam_data.description,
        date= exam_data.date,
        duration_minutes= exam_data.duration_minutes,
        start_time= exam_data.start_time,  
        created_by= current_user["sub"],
        college_id= current_user.get("college_id", "UNKNOWN") #assign a default college if not provided
    )
    db.add(exam)
    db.commit()
    db.refresh(exam)
    return{
        "status": "success",
        "exam_id": str(exam.id),
        "message": f"Exam '{exam.title}' created successfully!"
    }

@router.get("/listings")
def list_exams(
    current_user = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    exams = db.query(Exam).filter(Exam.is_active == True).all() #only return exams for the user's college
    return [{
        "id": str(e.id), 
        "title": e.title, 
        "description": e.description, 
        "date": e.date, 
        "duration_minutes": e.duration_minutes, 
        "start_time": e.start_time
    }
    for e in exams
    ]
