from fastapi import APIRouter, HTTPException, status, Request
from pydantic import BaseModel
from typing import Optional
from firebase_admin import auth as firebase_auth
from app.core.rate_limit import limiter

router = APIRouter()


class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: Optional[str] = None


class LoginRequest(BaseModel):
    id_token: str  # Firebase ID token issued by the client SDK after sign-in


@router.post("/register")
@limiter.limit("5/minute")
def register(request: Request, data: RegisterRequest):
    """
    Creates a new user in Firebase Authentication.
    After this, the client app should use the Firebase SDK to sign in and get an ID token.
    """
    try:
        user = firebase_auth.create_user(
            email=data.email,
            password=data.password,
            display_name=data.full_name or data.email.split("@")[0],
        )
    except firebase_auth.EmailAlreadyExistsError:
        raise HTTPException(status_code=400, detail="The user with this email already exists.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "message": "User registered successfully. Please sign in via the app to get your token.",
        "uid": user.uid,
        "email": user.email,
    }


@router.post("/verify-token")
def verify_token(data: LoginRequest):
    """
    Verifies a Firebase ID token passed from the client.
    Returns basic user info. Use this to confirm a successful login.
    """
    try:
        decoded = firebase_auth.verify_id_token(data.id_token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired Firebase ID token.")

    return {
        "uid": decoded.get("uid"),
        "email": decoded.get("email"),
        "name": decoded.get("name"),
    }
