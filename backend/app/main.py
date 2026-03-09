from fastapi import FastAPI
from app.database import engine, Base
from app.routers import auth, exams, session
from app.model import User

#create the database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI Proctoring API",
    description="Backend for AI Proctoring Software",
    version="1.0.0"
)

app.include_router(auth.router) #include the authentication router for handling user registration and login
app.include_router(exams.router) #include the exams router for handling exam creation and listing
app.include_router(session.router) #include the session router for handling exam sessions and cheating detection

@app.get("/")
def root():
    return {
        "message": "Welcome to the AI Proctoring API!",
        "status": "API is running successfully.",
        "version": "1.0.0"
        }