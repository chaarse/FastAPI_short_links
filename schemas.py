from pydantic import BaseModel, Field, HttpUrl
from datetime import datetime
from typing import Optional

class UserRegister(BaseModel):
    """
    Модель для регистрации пользователя.
    """
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)

class UserLogin(BaseModel):
    """
    Модель для входа пользователя.
    """
    username: str
    password: str

class UserResponse(BaseModel):
    """
    Модель для ответа с данными пользователя.
    """
    id: int
    username: str

    class Config:
        from_attributes = True

class SLinkAdd(BaseModel):
    """
    Модель для добавления новой ссылки.
    """
    original_url: HttpUrl
    short_code: str = Field(..., min_length=3, max_length=20, pattern="^[a-zA-Z0-9_-]+$")
    expires_at: Optional[datetime] = None

class SLinkResponse(BaseModel):
    """
    Модель для ответа с данными ссылки.
    """
    id: int
    original_url: HttpUrl
    short_code: str
    created_at: datetime
    expires_at: datetime
    user_id: Optional[int]
    click_count: int

    class Config:
        from_attributes = True