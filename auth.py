import os
import logging
import hashlib
from datetime import datetime
from typing import Optional, Dict

from fastapi import APIRouter, Depends, HTTPException, status, Form
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from passlib.context import CryptContext

from database import new_session, UserOrm, LinkOrm
from schemas import UserRegister, UserResponse

logger = logging.getLogger(__name__)

# Контекст для хэширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Схема OAuth2 (без токенов, просто для совместимости)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token", auto_error=False)

# Хранилище авторизованных пользователей (в памяти)
active_users: Dict[str, UserResponse] = {}

# Создаем роутер для аутентификации
auth_router = APIRouter(prefix="/auth", tags=["Аутентификация"])


def generate_user_secret_key(username: str) -> str:
    secret_key = hashlib.sha256(username.encode()).hexdigest()
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
    async def get_current_user(cls, token: Optional[str] = Depends(oauth2_scheme)) -> Optional[UserResponse]:
        """
        Получает текущего пользователя из хранилища активных пользователей.
        """
        if token is None:
            logger.debug("Токен отсутствует")
            return None

        # Ищем пользователя в хранилище активных пользователей
        user = active_users.get(token)
        if user is None:
            logger.debug(f"Пользователь с токеном {token} не найден")
            return None

        logger.debug(f"Пользователь {user.username} успешно авторизован")
        return user

    @classmethod
    async def update_user_id_for_links(cls, username: str, user_id: int):
        """
        Обновляет user_id для всех ссылок, созданных до авторизации.
        """
        async with new_session() as session:
            try:
                # Находим все ссылки, созданные до авторизации (user_id = NULL)
                query = select(LinkOrm).where(LinkOrm.user_id.is_(None))
                result = await session.execute(query)
                links = result.scalars().all()

                # Обновляем user_id для найденных ссылок
                for link in links:
                    link.user_id = user_id

                await session.commit()
                logger.info(f"Updated user_id for {len(links)} links")
            except Exception as e:
                logger.error(f"Error updating user_id for links: {e}")
                await session.rollback()
                raise HTTPException(status_code=500, detail="Internal Server Error")


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

@auth_router.post("/token")
async def login_for_access_token(
    username: str = Form(...),  # Ввод через форму
    password: str = Form(...),  # Ввод через форму
):
    """
    Аутентифицирует пользователя и возвращает токен (просто строку).
    Также обновляет user_id для всех ссылок, созданных до авторизации.
    """
    user = await AuthService.authenticate_user(username, password)
    user_response = UserResponse(id=user.id, username=user.username)

    # Генерируем "токен" (просто хэш имени пользователя)
    token = generate_user_secret_key(username)

    # Сохраняем пользователя в хранилище активных пользователей
    active_users[token] = user_response

    # Обновляем user_id для всех ссылок, созданных до авторизации
    await AuthService.update_user_id_for_links(username, user.id)

    return {"access_token": token, "token_type": "bearer"}


# Экспортируем функцию для использования в других модулях
get_current_user = AuthService.get_current_user