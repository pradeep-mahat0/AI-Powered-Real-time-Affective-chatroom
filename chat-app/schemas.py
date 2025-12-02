from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class UserCreate(BaseModel):
    username: str
    password: str

class UserOut(BaseModel):
    id: int
    username: str
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class MessageCreate(BaseModel):
    content: str

class MessageOut(BaseModel):
    id: int
    user_id: int
    content: str
    timestamp: datetime
    
    # UPDATED: Added fields to include in the API response.
    # The frontend needs to know who sent the message and its emotion.
    username: str 
    emotion: Optional[str] = None

    class Config:
        from_attributes = True

# NEW: Schema for the overall mood response
class MoodOut(BaseModel):
    mood: str

class SummaryOut(BaseModel):
    summary: str