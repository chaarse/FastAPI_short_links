from sqlalchemy import select, update, delete
from database import new_session, LinkOrm
from schemas import SLinkAdd, SLinkResponse
from datetime import datetime, timedelta
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class LinkRepository:
    @classmethod
    async def add_one(cls, data: SLinkAdd, user_id: Optional[int] = None) -> int:
        """
        Добавляет новую ссылку в базу данных.
        """
        async with new_session() as session:
            try:
                link_dict = data.model_dump()
                link_dict["user_id"] = user_id
                link = LinkOrm(**link_dict)
                session.add(link)
                await session.flush()
                await session.commit()
                logger.debug(f"Link created: {link}")
                return link.id
            except Exception as e:
                logger.error(f"Error adding link: {e}")
                await session.rollback()
                raise

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
    async def update_original_url(cls, short_code: str, new_url: str, user_id: int):
        """
        Обновляет оригинальный URL для ссылки.
        """
        async with new_session() as session:
            query = update(LinkOrm).where(
                (LinkOrm.short_code == short_code) & (LinkOrm.user_id == user_id)
            ).values(original_url=new_url)
            await session.execute(query)
            await session.commit()

    @classmethod
    async def increment_click_count(cls, link_id: int):
        """
        Увеличивает счетчик переходов по ссылке.
        """
        async with new_session() as session:
            query = update(LinkOrm).where(LinkOrm.id == link_id).values(click_count=LinkOrm.click_count + 1)
            await session.execute(query)
            await session.commit()