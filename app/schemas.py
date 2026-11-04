from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

class RegisterRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    invite_code: str = Field(min_length=1)

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class ReservationRequest(BaseModel):
    room_id: str
    title: str = Field(min_length=1, max_length=100)
    note: str = Field(default="", max_length=500)
    start_at: datetime
    end_at: datetime