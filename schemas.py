from pydantic import BaseModel, Field, HttpUrl
from datetime import datetime
from typing import Optional

class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str

    class Config:
        from_attributes = True

class SLinkAdd(BaseModel):
    original_url: HttpUrl  # Только оригинальная ссылка

class SLinkResponse(BaseModel):
    id: int
    original_url: HttpUrl
    short_code: str
    created_at: datetime
    expires_at: datetime
    user_id: Optional[int]
    click_count: int
    short_url: str  # Добавляем короткую ссылку

    class Config:
        from_attributes = True