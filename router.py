from fastapi import APIRouter, Depends, HTTPException, Form, Request, Body
from fastapi.responses import RedirectResponse
from repository import LinkRepository
from schemas import SLinkAdd, SLinkResponse, UserResponse, SLinkStatsResponse
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
    request: Request,  # Добавляем request для получения базового URL
    original_url: str = Form(...),
    user: Optional[UserResponse] = Depends(get_current_user),
) -> SLinkResponse:
    """
    Создает короткую ссылку для оригинального URL.
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
                short_url=f"{request.base_url}links/{existing_link.short_code}",  # Добавляем короткую ссылку
            )

        # Если пользователь авторизован, используем его user_id, иначе None
        user_id = user.id if user else None
        link_data = SLinkAdd(original_url=original_url)
        link = await LinkRepository.add_one(link_data, user_id=user_id)
        return SLinkResponse(
            id=link.id,
            original_url=link.original_url,
            short_code=link.short_code,
            created_at=link.created_at,
            expires_at=link.expires_at,
            user_id=link.user_id,
            click_count=link.click_count,
            short_url=f"{request.base_url}links/{link.short_code}",  # Добавляем короткую ссылку
        )
    except Exception as e:
        logger.error(f"Error creating link: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.get("/{short_code}")
async def redirect_link(short_code: str):
    """
    Перенаправляет на оригинальный URL по короткой ссылке.
    """
    link = await LinkRepository.find_by_short_code(short_code)
    if not link:
        raise HTTPException(status_code=404, detail="Ссылка не найдена")

    await LinkRepository.increment_click_count(link.id)
    return RedirectResponse(url=link.original_url)

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

@router.put("/{short_code}", response_model=SLinkResponse)
async def update_link(
    short_code: str,  # short_code берется из URL
    new_url: str = Form(...),  # new_url берется из формы (x-www-form-urlencoded)
    user: UserResponse = Depends(get_current_user),
) -> SLinkResponse:
    """
    Обновляет оригинальный URL для короткой ссылки.
    Доступно только авторизованным пользователям, которые создали ссылку.
    """
    try:
        logger.debug(f"Updating link: short_code={short_code}, new_url={new_url}, user_id={user.id}")

        link = await LinkRepository.find_by_short_code(short_code)
        if not link:
            logger.warning(f"Link not found: short_code={short_code}")
            raise HTTPException(status_code=404, detail="Ссылка не найдена")

        if link.user_id != user.id:
            logger.warning(f"Permission denied: user_id={user.id}, link_user_id={link.user_id}")
            raise HTTPException(status_code=403, detail="Недостаточно прав для обновления ссылки")

        # Обновляем оригинальный URL
        updated_link = await LinkRepository.update_original_url(short_code, new_url, user.id)
        if not updated_link:
            logger.error(f"Failed to update link: short_code={short_code}")
            raise HTTPException(status_code=500, detail="Ошибка при обновлении ссылки")

        logger.info(f"Link updated: short_code={short_code}, new_url={new_url}")
        return SLinkResponse(
            id=updated_link.id,
            original_url=updated_link.original_url,
            short_code=updated_link.short_code,
            created_at=updated_link.created_at,
            expires_at=updated_link.expires_at,
            user_id=updated_link.user_id,
            click_count=updated_link.click_count,
            short_url=None,  # Поле short_url не используется в этой ручке
        )
    except Exception as e:
        logger.error(f"Error updating link: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.get("/{short_code}/stats", response_model=SLinkStatsResponse)
async def link_stats(short_code: str) -> SLinkStatsResponse:
    """
    Возвращает статистику по короткой ссылке.
    Доступно всем.
    """
    link = await LinkRepository.find_by_short_code(short_code)
    if not link:
        raise HTTPException(status_code=404, detail="Ссылка не найдена")

    return SLinkStatsResponse(
        original_url=link.original_url,
        created_at=link.created_at,
        click_count=link.click_count,
        last_used_at=link.last_used_at,  # Предполагаем, что это поле есть в модели
    )