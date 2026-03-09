import  bcrypt
import jwt
import os
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv

load_dotenv() # Load environment variables from .env file
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256" 

security = HTTPBearer() # For handling bearer token authentication

# Hash the password using bcrypt
def hash_password(password: str) -> str:
    salt = bcrypt.gensalt() # Generate a random salt
    return bcrypt.hashpw(password.encode(), salt).decode() # Hash the password and return as string

# Verify the password against the hashed version
def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode()) # Check if the password matches the hash

# Create a JWT token for the user(available for 8 hours)
def create_token(user_id: str, role: str) -> str:
    payload = {
        "sub": user_id,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(hours=8) # Token expires in 8 hours
    }

    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM) # Encode the token with the secret key

#decodes and verify the token 
def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM]) # Decode the token
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired") # Token expired
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token") # Token is invalid

# FastAPI dependency to get the current user from the token
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    return decode_token(token) # Decode the token and return the user information

#requires a specific role to access the endpoint
def require_role(*roles):
    def checker(user = Depends(get_current_user)):
        if user["role"] not in roles:
            raise HTTPException(status_code=403, detail="Forbidden: Insufficient permissions") # User does not have the required role
        return user
    return checker
