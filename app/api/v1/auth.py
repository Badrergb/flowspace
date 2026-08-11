from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse
from app.schemas.token import Token
from app.core.security import get_password_hash, verify_password, create_access_token
from app.core.rate_limit import limiter
from datetime import timedelta, datetime, timezone
import random
from app.core.config import settings

router = APIRouter()

@router.post("/register", response_model=UserResponse)
@limiter.limit("5/minute")
def register(request: Request, user_in: UserCreate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_in.email).first()
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this username already exists in the system.",
        )
    otp = str(random.randint(100000, 999999))
    
    user = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        avatar_url=user_in.avatar_url,
        is_verified=False,
        otp_hash=get_password_hash(otp),
        otp_expires_at=datetime.now(timezone.utc) + timedelta(minutes=10),
        otp_attempts=0
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # TODO: Use Resend or SendGrid to email `otp` to `user_in.email`
    print(f"OTP for {user_in.email} is {otp}")
    
    return user


@router.post("/login", response_model=Token)
@limiter.limit("10/minute")
def login(request: Request, db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    access_token = create_access_token(
        data={"email": user.email, "sub": str(user.id)}, expires_delta=access_token_expires
    )
    refresh_token = create_access_token(
        data={"email": user.email, "sub": str(user.id), "type": "refresh"}, expires_delta=refresh_token_expires
    )
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

@router.post("/refresh", response_model=Token)
@limiter.limit("10/minute")
def refresh_token(request: Request, payload: dict, db: Session = Depends(get_db)):
    refresh_token = payload.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=400, detail="Refresh token required")
    from jose import jwt, JWTError
    try:
        token_data = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if token_data.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        email = token_data.get("email")
        user_id = token_data.get("sub")
        if not email or not user_id:
            raise HTTPException(status_code=401, detail="Invalid token data")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
        
    user = db.query(User).filter(User.email == email).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"email": user.email, "sub": str(user.id)}, expires_delta=access_token_expires
    )
    # We can reuse the same refresh token or issue a new one. Issue a new one for rotation.
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    new_refresh_token = create_access_token(
        data={"email": user.email, "sub": str(user.id), "type": "refresh"}, expires_delta=refresh_token_expires
    )
    
    return {"access_token": access_token, "refresh_token": new_refresh_token, "token_type": "bearer"}

from pydantic import BaseModel
class VerifyOTPRequest(BaseModel):
    email: str
    code: str

class ResendOTPRequest(BaseModel):
    email: str

@router.post("/verify-otp", response_model=Token)
@limiter.limit("5/minute")
def verify_otp(request: Request, data: VerifyOTPRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if not user:
        raise HTTPException(status_code=400, detail="User not found")
        
    if user.is_verified:
        raise HTTPException(status_code=400, detail="User already verified")
        
    if user.otp_attempts >= 5:
        raise HTTPException(status_code=429, detail="Too many attempts. Please request a new code.")
        
    if not user.otp_expires_at or datetime.now(timezone.utc) > user.otp_expires_at.replace(tzinfo=timezone.utc):
        raise HTTPException(status_code=400, detail="OTP expired. Please request a new code.")
        
    if not user.otp_hash or not verify_password(data.code, user.otp_hash):
        user.otp_attempts += 1
        db.commit()
        raise HTTPException(status_code=400, detail="Invalid verification code")
        
    # Valid OTP
    user.is_verified = True
    user.otp_hash = None
    user.otp_expires_at = None
    user.otp_attempts = 0
    db.commit()
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    access_token = create_access_token(
        data={"email": user.email, "sub": str(user.id)}, expires_delta=access_token_expires
    )
    refresh_token = create_access_token(
        data={"email": user.email, "sub": str(user.id), "type": "refresh"}, expires_delta=refresh_token_expires
    )
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

@router.post("/resend-otp")
@limiter.limit("3/hour")
def resend_otp(request: Request, data: ResendOTPRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if not user:
        raise HTTPException(status_code=400, detail="User not found")
        
    if user.is_verified:
        raise HTTPException(status_code=400, detail="User already verified")
        
    otp = str(random.randint(100000, 999999))
    user.otp_hash = get_password_hash(otp)
    user.otp_expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
    user.otp_attempts = 0
    db.commit()
    
    # TODO: Use Resend or SendGrid to email `otp` to `data.email`
    print(f"Resent OTP for {data.email} is {otp}")
    
    return {"message": "OTP sent successfully"}

