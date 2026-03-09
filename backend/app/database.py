from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

load_dotenv() #load the .env file

Database_URL= os.getenv("DATABASE_URL") 

engine = create_engine(Database_URL) #create the engine using the database URL from the .env file

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine) #Each Request will have its own database session

Base= declarative_base() #Base class for all database models

#dependency to get the database session for each request
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

