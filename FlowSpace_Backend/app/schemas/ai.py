from pydantic import BaseModel
from typing import List, Dict

class CategorizeRequest(BaseModel):
    transactions: List[str]

class CategorizeResponse(BaseModel):
    categories: Dict[str, str]

class ChatRequest(BaseModel):
    query: str

class ChatResponse(BaseModel):
    response: str

class WeeklyReviewResponse(BaseModel):
    review: str
