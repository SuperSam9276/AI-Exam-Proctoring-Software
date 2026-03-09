from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
import uuid

#registration schema
class UserCreate(BaseModel):
    name: str
    email: EmailStr #validates if its a proper email format
    password: str
    role: str = "student" #default role is student
    college_id: Optional[str] = None

#login schema
class UserLogin(BaseModel):
    email: EmailStr
    password: str

#Token response schema
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role : str
    name : str

#User response schema (for returning user details without password)
class UserResponse(BaseModel):
    id: uuid.UUID
    name: str
    email: EmailStr
    role: str
    college_id: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True #allows compatibility with SQLAlchemy models
        

