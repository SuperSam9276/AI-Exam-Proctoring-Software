from fastapi import APIRouter, Request
from app.config import templates

router = APIRouter(tags=["Pages"])

@router.get("/exam/{session_id}")
def exam_page(request: Request, session_id: str):
    #sample question data - in real implementation, fetch from database
    sample= [
        {
        "text": "What is 2 + 2?",
        "options": ["3", "4", "5", "6"]
        },
        {
        "text": "What is the time complexity of a binary search?",
        "options": ["O(1)", "O(log n)", "O(n)", "O(n log n)"]
        },
        {
        "text": "What is the capital of France?",
        "options": ["Berlin", "Madrid", "Paris", "Rome"]
        }
    ]
    return templates.TemplateResponse("exam_template.html", {
        "request": request, 
        "exam_title": "Computer Science 101 - Midterm",
        "user_name": "John Doe",
        "duration_minutes": 10,
        "session_id": session_id,
        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIwMGY0ZDBiNS03NjlhLTRmOTQtODExMC1hNmI3NmIzMmUzYTQiLCJyb2xlIjoiYWRtaW4iLCJleHAiOjE3NzcyODYzNDh9.H2RgIFVoi4NwuEuGMyR0vcwtm2dO0J6BELw1Z2wf6lE",
        "questions": sample
        })

