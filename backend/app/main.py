from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.database import engine, Base
from app.routers import auth, exams, session, pages
from app.model import User
from app.decay import start_decay_thread


#create the database tables
Base.metadata.create_all(bind=engine)

# Start the decay thread
start_decay_thread()

app = FastAPI(
    title="AI Proctoring API",
    description="Backend for AI Proctoring Software",
    version="1.0.0"
)

app.mount("/static", StaticFiles(directory="C:\\Swayam\\Codes\\Proctoring Software\\frontend\\static"), name="static") #serve static files (e.g., CSS, JS)




app.include_router(auth.router) #include the authentication router for handling user registration and login
app.include_router(exams.router) #include the exams router for handling exam creation and listing
app.include_router(session.router) #include the session router for handling exam sessions and cheating detection
app.include_router(pages.router) #include the pages router for serving HTML pages (e.g., exam page)

@app.get("/")
def root():
    return {
        "message": "Welcome to the AI Proctoring API!",
        "status": "API is running successfully.",
        "version": "1.0.0"
        }