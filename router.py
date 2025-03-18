from fastapi import APIRouter, Depends, HTTPException
from repository import LinkRepository
from schemas import SLinkAdd, SLinkResponse, UserResponse
from auth import get_current_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/links",
    tags=["Ссылки"],
)

@router.post("/shorten", response_model=SLinkResponse)
async def shorten_link(
    link_data: SLinkAdd,
    user: UserResponse = Depends(get_current_user),
) -> SLinkResponse:
    try:
        link_id = await LinkRepository.add_one(link_data, user.id)
        link = await LinkRepository.find_by_short_code(link_data.short_code)
        return link
    except Exception as e:
        logger.error(f"Error creating link: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.get("/{short_code}")
async def redirect_link(short_code: str):
    link = await LinkRepository.find_by_short_code(short_code)
    if not link:
        raise HTTPException(status_code=404, detail="Ссылка не найдена")

    await LinkRepository.increment_click_count(link.id)
    return {"url": link.original_url}

@router.delete("/{short_code}")
async def delete_link(
    short_code: str,
    user: UserResponse = Depends(get_current_user),
):
    await LinkRepository.delete_by_short_code(short_code, user.id)
    return {"ok": True}

@router.put("/{short_code}")
async def update_link(
    short_code: str,
    new_url: str,
    user: UserResponse = Depends(get_current_user),
):
    await LinkRepository.update_original_url(short_code, new_url, user.id)
    return {"ok": True}

@router.get("/{short_code}/stats", response_model=SLinkResponse)
async def link_stats(short_code: str) -> SLinkResponse:
    link = await LinkRepository.find_by_short_code(short_code)
    if not link:
        raise HTTPException(status_code=404, detail="Ссылка не найдена")
    return link

@router.get("/search", response_model=SLinkResponse)
async def search_link_by_url(original_url: str):
    link = await LinkRepository.find_by_original_url(original_url)
    if not link:
        raise HTTPException(status_code=404, detail="Ссылка не найдена")
    return link