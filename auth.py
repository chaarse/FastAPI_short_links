from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from database import new_session, UserOrm
from schemas import UserRegister, UserLogin, UserResponse
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from sqlalchemy import select
import os
import logging
import hashlib

logger = logging.getLogger(__name__)

# Настройки для JWT
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Контекст для хэширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Схема OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# Соль для генерации SECRET_KEY
SALT = os.getenv("SALT", "your_salt_here")

# Создаем роутер для аутентификации
auth_router = APIRouter(prefix="/auth", tags=["Аутентификация"])

def generate_user_secret_key(username: str) -> str:
    """
    Генерирует уникальный SECRET_KEY для пользователя на основе его username и соли.
    """
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
                existing_user = await session.execute(select(UserOrm).where(UserOrm.username == user_data.username))
                if existing_user.scalar():
                    raise HTTPException(status_code=400, detail="Username already exists")

                hashed_password = pwd_context.hash(user_data.password)
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
        user_secret_key = generate_user_secret_key(user.username)
        to_encode = {
            "sub": user.username,
            "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        }
        return jwt.encode(to_encode, user_secret_key, algorithm=ALGORITHM)

    @classmethod
    async def get_current_user(cls, token: str = Depends(oauth2_scheme)) -> UserOrm:
        """
        Возвращает текущего пользователя по токену.
        """
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = jwt.decode(token, None, options={"verify_signature": False})
            username: str = payload.get("sub")
            if username is None:
                raise credentials_exception

            async with new_session() as session:
                user = await session.execute(select(UserOrm).where(UserOrm.username == username))
                user = user.scalar()
                if user is None:
                    raise credentials_exception

                user_secret_key = generate_user_secret_key(user.username)
                jwt.decode(token, user_secret_key, algorithms=[ALGORITHM])

                return user
        except JWTError as e:
            logger.error(f"JWTError: {e}")
            raise credentials_exception

@auth_router.post("/register")
async def register(user_data: UserRegister):
    return await AuthService.register_user(user_data)

@auth_router.post("/login")
async def login(user_data: UserLogin):
    user = await AuthService.authenticate_user(user_data.username, user_data.password)
    access_token = AuthService.create_access_token(user)
    return {"access_token": access_token, "token_type": "bearer"}

get_current_user = AuthService.get_current_user