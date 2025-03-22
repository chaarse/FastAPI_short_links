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
    original_url: str  # Используем str вместо HttpUrl
    custom_alias: Optional[str] = Field(
        None,
        min_length=4,
        max_length=20,
        pattern="^[a-zA-Z0-9_-]+$",
        description="Пользовательский алиас для короткой ссылки. Должен быть уникальным."
    )
    expires_at: Optional[datetime] = Field(
        None,
        description="Дата и время истечения срока действия ссылки (формат: YYYY-MM-DDTHH:MM)."
    )

class SLinkResponse(BaseModel):
    id: int
    original_url: HttpUrl
    short_code: str
    created_at: datetime
    expires_at: datetime
    user_id: Optional[int]  # ID пользователя, создавшего ссылку
    click_count: int
    short_url: Optional[str]  # Короткий URL

    class Config:
        from_attributes = True

class SLinkStatsResponse(BaseModel):
    original_url: HttpUrl  # Оригинальный URL
    created_at: datetime   # Дата создания
    click_count: int       # Количество переходов
    last_used_at: datetime

class Token(BaseModel):
    access_token: str
    token_type: str