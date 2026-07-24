from pydantic import BaseModel

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str

from typing import Optional

class TokenData(BaseModel):
    email: Optional[str] = None
