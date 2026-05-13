from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.model import User
from app.schemas import UserCreate, UserLogin, TokenResponse, UserResponse
from app.auth import hash_password, verify_password, create_token, require_role, get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserResponse)

def register(user_data: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user_data.email).first() #use email to check if user already exists
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered") #if email is already in use
    
    if user_data.role not in ["student", "proctor", "admin"]:
        raise HTTPException(status_code=400, detail="Invalid role specified") #if role is not valid

    new_user = User(
        name=user_data.name,
        email=user_data.email,
        password_hash=hash_password(user_data.password), #hash the password before storing
        role=user_data.role,
        college_id=user_data.college_id or "UNKNOWN" #assign a unknown if not provided
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user) #refresh to get the new user data with ID
    return new_user

@router.post("/login", response_model=TokenResponse)
def login(credentials : UserLogin, db : Session = Depends(get_db)):
    user = db.query(User).filter(User.email == credentials.email).first() #find user by email
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password") #if email or password is incorrect
    
    token = create_token(str(user.id), user.role) #create a JWT token for the user
    return TokenResponse(access_token=token, role=user.role, name=user.name)

# get_me endpoint
@router.get("/me", response_model=UserResponse)
def get_me(current_user = Depends(get_current_user)):
    return current_user   # already a User object now — no DB query needed

# admin_only endpoint
@router.get("/admin-only")
def admin_only(admin_user = Depends(require_role("admin"))):
    return {
        "status":     "success",
        "role":       admin_user.role,
        "name":       admin_user.name,
        "email":      admin_user.email,
        "college_id": admin_user.college_id,
        "message":    f"Hello {admin_user.name}, Welcome to the Admin Panel!"
    }
