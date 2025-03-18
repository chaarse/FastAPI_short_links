import secrets
import string
from fastapi import HTTPException
from sqlalchemy import select, update, delete
from database import new_session, LinkOrm
from schemas import SLinkAdd, SLinkResponse
from datetime import datetime, timedelta
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class LinkRepository:
    @staticmethod
    def generate_short_code(length: int = 8) -> str:
        """
        Генерирует уникальный короткий код.
        """
        chars = string.ascii_letters + string.digits  # Буквы и цифры
        return ''.join(secrets.choice(chars) for _ in range(length))

    @classmethod
    async def add_one(cls, data: SLinkAdd, user_id: Optional[int] = None) -> SLinkResponse:
        """
        Добавляет новую ссылку в базу данных.
        Поддерживает использование custom_alias в качестве short_code.
        """
        async with new_session() as session:
            try:
                # Если передан custom_alias, проверяем его уникальность
                if data.custom_alias:
                    existing_link = await cls.find_by_short_code(data.custom_alias)
                    if existing_link:
                        raise HTTPException(
                            status_code=400,
                            detail="Пользовательский алиас уже занят."
                        )
                    short_code = data.custom_alias
                else:
                    # Генерируем уникальный short_code, если custom_alias не передан
                    while True:
                        short_code = cls.generate_short_code()
                        existing_link = await cls.find_by_short_code(short_code)
                        if not existing_link:
                            break

                # Создаем новую ссылку
                link = LinkOrm(
                    original_url=str(data.original_url),
                    short_code=short_code,
                    user_id=user_id,  # user_id может быть None (анонимный пользователь)
                )
                session.add(link)
                await session.flush()
                await session.commit()

                logger.debug(f"Link created: {link}")
                return SLinkResponse(
                    id=link.id,
                    original_url=link.original_url,
                    short_code=link.short_code,
                    created_at=link.created_at,
                    expires_at=link.expires_at,
                    user_id=link.user_id,
                    click_count=link.click_count,
                    short_url=None,  # Поле short_url не используется в этой ручке
                )
            except HTTPException as e:
                raise e  # Пробрасываем HTTPException
            except Exception as e:
                logger.error(f"Error adding link: {e}")
                await session.rollback()
                raise HTTPException(status_code=500, detail="Internal Server Error")

    @classmethod
    async def find_by_short_code(cls, short_code: str) -> LinkOrm:
        """
        Ищет ссылку по короткому коду.
        """
        async with new_session() as session:
            query = select(LinkOrm).where(LinkOrm.short_code == short_code)
            result = await session.execute(query)
            return result.scalars().first()

    @classmethod
    async def find_by_original_url(cls, original_url: str) -> LinkOrm:
        """
        Ищет ссылку по оригинальному URL.
        """
        async with new_session() as session:
            query = select(LinkOrm).where(LinkOrm.original_url == original_url)
            result = await session.execute(query)
            return result.scalars().first()

    @classmethod
    async def delete_by_short_code(cls, short_code: str, user_id: int):
        """
        Удаляет ссылку по короткому коду.
        """
        async with new_session() as session:
            query = delete(LinkOrm).where(
                (LinkOrm.short_code == short_code) & (LinkOrm.user_id == user_id)
            )
            await session.execute(query)
            await session.commit()

    @classmethod
    async def update_original_url(cls, short_code: str, new_url: str, user_id: int) -> LinkOrm:
        """
        Обновляет оригинальный URL для ссылки и возвращает обновленную запись.
        """
        async with new_session() as session:
            try:
                # Обновляем оригинальный URL
                query = update(LinkOrm).where(
                    (LinkOrm.short_code == short_code) & (LinkOrm.user_id == user_id)
                ).values(original_url=new_url)
                await session.execute(query)
                await session.commit()

                # Получаем обновленную запись
                updated_link = await cls.find_by_short_code(short_code)
                if not updated_link:
                    logger.error(f"Failed to fetch updated link: short_code={short_code}")
                    return None

                return updated_link
            except Exception as e:
                logger.error(f"Error updating link in database: {e}")
                await session.rollback()
                return None

    @classmethod
    async def increment_click_count(cls, link_id: int):
        """
        Увеличивает счетчик переходов по ссылке.
        """
        async with new_session() as session:
            query = update(LinkOrm).where(LinkOrm.id == link_id).values(click_count=LinkOrm.click_count + 1)
            await session.execute(query)
            await session.commit()