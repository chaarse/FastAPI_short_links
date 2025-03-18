from fastapi import APIRouter, Depends, HTTPException, Form
from repository import LinkRepository
from schemas import SLinkAdd, SLinkResponse, UserResponse
from auth import get_current_user
from typing import Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/links",
    tags=["Ссылки"],
)


@router.post("/shorten", response_model=SLinkResponse)
async def shorten_link(
    original_url: str = Form(...),  # Ввод через форму
    user: Optional[UserResponse] = Depends(get_current_user),  # Опциональная авторизация
) -> SLinkResponse:
    """
    Создает короткую ссылку для оригинального URL.
    Доступно всем (авторизованным и анонимным).
    """
    try:
        # Проверяем, существует ли ссылка с таким original_url
        existing_link = await LinkRepository.find_by_original_url(original_url)
        if existing_link:
            return SLinkResponse(
                id=existing_link.id,
                original_url=existing_link.original_url,
                short_code=existing_link.short_code,
                created_at=existing_link.created_at,
                expires_at=existing_link.expires_at,
                user_id=existing_link.user_id,
                click_count=existing_link.click_count,
            )

        # Если пользователь авторизован, используем его user_id, иначе None
        user_id = user.id if user else None
        link_data = SLinkAdd(original_url=original_url)
        link = await LinkRepository.add_one(link_data, user_id=user_id)
        return link
    except Exception as e:
        logger.error(f"Error creating link: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.get("/{short_code}")
async def redirect_link(short_code: str):
    """
    Перенаправляет на оригинальный URL по короткой ссылке.
    Доступно всем.
    """
    link = await LinkRepository.find_by_short_code(short_code)
    if not link:
        raise HTTPException(status_code=404, detail="Ссылка не найдена")

    await LinkRepository.increment_click_count(link.id)
    return {"url": link.original_url}

@router.delete("/{short_code}")
async def delete_link(
    short_code: str,
    user: UserResponse = Depends(get_current_user),  # Только авторизованные пользователи
):
    """
    Удаляет короткую ссылку.
    Доступно только авторизованным пользователям, которые создали ссылку.
    """
    link = await LinkRepository.find_by_short_code(short_code)
    if not link:
        raise HTTPException(status_code=404, detail="Ссылка не найдена")

    if link.user_id != user.id:
        raise HTTPException(status_code=403, detail="Недостаточно прав для удаления ссылки")

    await LinkRepository.delete_by_short_code(short_code, user.id)
    return {"ok": True}

@router.put("/{short_code}")
async def update_link(
    short_code: str,
    new_url: str,
    user: UserResponse = Depends(get_current_user),  # Только авторизованные пользователи
):
    """
    Обновляет оригинальный URL для короткой ссылки.
    Доступно только авторизованным пользователям, которые создали ссылку.
    """
    link = await LinkRepository.find_by_short_code(short_code)
    if not link:
        raise HTTPException(status_code=404, detail="Ссылка не найдена")

    if link.user_id != user.id:
        raise HTTPException(status_code=403, detail="Недостаточно прав для обновления ссылки")

    await LinkRepository.update_original_url(short_code, new_url, user.id)
    return {"ok": True}

@router.get("/{short_code}/stats", response_model=SLinkResponse)
async def link_stats(short_code: str) -> SLinkResponse:
    """
    Возвращает статистику по короткой ссылке.
    Доступно всем.
    """
    link = await LinkRepository.find_by_short_code(short_code)
    if not link:
        raise HTTPException(status_code=404, detail="Ссылка не найдена")
    return link