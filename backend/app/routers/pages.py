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
        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIyOGEzYWI4Ni1kNzJjLTQxMjYtYTI0Mi1jODdiMzJmODIxNDUiLCJyb2xlIjoiYWRtaW4iLCJleHAiOjE3Nzg3MjExNDZ9.swJf0N-YXW24G64OPI6WNt2tGMPDBpAmLEssiUjS0wQ",
        "questions": sample
        })

@router.get("/invigilator")
def invigilator_page(request: Request):
    return templates.TemplateResponse("invigilator.html", {
        "request": request
    })

@router.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {
        "request": request
    })