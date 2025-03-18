from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from datetime import datetime, timedelta
from typing import Optional

# Создаем асинхронный движок для работы с базой данных
engine = create_async_engine("sqlite+aiosqlite:///links.db")
new_session = async_sessionmaker(engine, expire_on_commit=False)

class Model(DeclarativeBase):
    pass

class UserOrm(Model):
    """
    Модель для таблицы пользователей.
    """
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(unique=True)
    password_hash: Mapped[str]

class LinkOrm(Model):
    """
    Модель для таблицы ссылок.
    """
    __tablename__ = "links"

    id: Mapped[int] = mapped_column(primary_key=True)
    original_url: Mapped[str]
    short_code: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    expires_at: Mapped[datetime] = mapped_column(default=lambda: datetime.utcnow() + timedelta(days=30))
    user_id: Mapped[Optional[int]] = mapped_column(nullable=True)
    click_count: Mapped[int] = mapped_column(default=0)

async def create_tables():
    """
    Создает таблицы в базе данных.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Model.metadata.create_all)

async def delete_tables():
    """
    Удаляет таблицы из базы данных.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Model.metadata.drop_all)
