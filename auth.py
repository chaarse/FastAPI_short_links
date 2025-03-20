import os
import logging
import hashlib
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Form
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import select
from passlib.context import CryptContext
from jose import JWTError, jwt

from database import new_session, UserOrm
from schemas import UserRegister, UserResponse, Token
from fastapi import HTTPException

logger = logging.getLogger(__name__)

# Настройки для JWT
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
SECRET_KEY = os.getenv("SECRET_KEY", "your_secret_key_here")

# Контекст для хэширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Схема OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token", auto_error=False)  # auto_error=False позволяет не выбрасывать ошибку, если токен отсутствует

SALT = os.getenv("SALT", "your_salt_here")

# Создаем роутер для аутентификации
auth_router = APIRouter(prefix="/auth", tags=["Аутентификация"])


def generate_user_secret_key(username: str) -> str:
    secret_key = hashlib.sha256(f"{username}{SALT}".encode()).hexdigest()
    return secret_key


class AuthService:
    @classmethod
    async def register_user(cls, user_data: UserRegister) -> UserResponse:
        """
        Регистрирует нового пользователя.
        """
        async with new_session() as session:
            try:
                # Проверяем, существует ли пользователь
                existing_user = await session.execute(select(UserOrm).where(UserOrm.username == user_data.username))
                if existing_user.scalar():
                    raise HTTPException(status_code=400, detail="Username already exists")

                # Хэшируем пароль
                hashed_password = pwd_context.hash(user_data.password)

                # Создаем нового пользователя
                user = UserOrm(username=user_data.username, password_hash=hashed_password)
                session.add(user)
                await session.flush()
                await session.commit()

                logger.info(f"User registered: {user.username}")
                return UserResponse(id=user.id, username=user.username)
            except Exception as e:
                logger.error(f"Error registering user: {e}")
                await session.rollback()
                raise HTTPException(status_code=500, detail="Internal Server Error")

    @classmethod
    async def authenticate_user(cls, username: str, password: str) -> UserOrm:
        """
        Аутентифицирует пользователя.
        """
        async with new_session() as session:
            user = await session.execute(select(UserOrm).where(UserOrm.username == username))
            user = user.scalar()
            if not user or not pwd_context.verify(password, user.password_hash):
                raise HTTPException(status_code=401, detail="Invalid username or password")
            return user

    @classmethod
    def create_access_token(cls, user: UserOrm) -> str:
        """
        Создает JWT токен для конкретного пользователя.
        """
        # Генерируем уникальный SECRET_KEY для пользователя
        user_secret_key = generate_user_secret_key(user.username)

        # Данные для токена
        to_encode = {
            "sub": user.username,  # Уникальный идентификатор пользователя
            "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        }

        return jwt.encode(to_encode, user_secret_key, algorithm=ALGORITHM)

    @classmethod
    async def get_current_user(cls, token: Optional[str] = Depends(oauth2_scheme)) -> Optional[UserResponse]:
        if token is None:
            return None  # Если токен отсутствует, возвращаем None

        try:
            # Декодируем токен
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username: str = payload.get("sub")
            if username is None:
                return None  # Если username отсутствует, возвращаем None

            # Получаем пользователя из базы данных
            async with new_session() as session:
                user = await session.execute(select(UserOrm).where(UserOrm.username == username))
                user = user.scalar()
                if user is None:
                    return None  # Если пользователь не найден, возвращаем None

                return UserResponse(id=user.id, username=user.username)
        except JWTError:
            return None  # Если токен невалиден, возвращаем None


# Эндпоинты для аутентификации
@auth_router.post("/register")
async def register(
    username: str = Form(...),  # Ввод через форму
    password: str = Form(...),  # Ввод через форму
):
    """
    Регистрирует нового пользователя (через форму).
    """
    user_data = UserRegister(username=username, password=password)
    return await AuthService.register_user(user_data)

@auth_router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await AuthService.authenticate_user(form_data.username, form_data.password)
    access_token = AuthService.create_access_token(user)
    return {"access_token": access_token, "token_type": "bearer"}


# Экспортируем функцию для использования в других модулях
get_current_user = AuthService.get_current_user