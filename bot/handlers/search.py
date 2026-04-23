import logging
from typing import Optional

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from bot.keyboards.inline import like_dislike_keyboard
from bot.keyboards.reply import main_menu_keyboard
from bot.services.match_api import MatchAPIClient
from bot.services.profile_api import ProfileAPIClient
from bot.services.publisher import publish_user_like
from bot.services.redis_cache import (
    get_next_profile_user_id, push_profile_user_ids,
    get_cached_profile, cache_profile, mark_seen, get_seen_ids,
)

logger = logging.getLogger(__name__)
router = Router()

GENDER_DISPLAY = {"male": "Мужчина", "female": "Женщина", "other": "Другое"}


async def _get_next_profile(user_id: int, profile_api: ProfileAPIClient) -> Optional[dict]:
    # Сначала пробуем взять из Redis-очереди, пропуская устаревшие ID
    while True:
        target_user_id = await get_next_profile_user_id(user_id)
        if target_user_id is None:
            break

        profile = await get_cached_profile(target_user_id)
        if profile:
            return profile

        profile = await profile_api.get_profile(target_user_id)
        if profile:
            return profile
        # ID устарел — берём следующий из очереди

    # Очередь пуста — загружаем новую порцию из API, исключая уже просмотренных
    seen = await get_seen_ids(user_id)
    profiles = await profile_api.get_feed(user_id, excluded=seen)
    if not profiles:
        return None

    for p in profiles:
        await cache_profile(p["user_id"], p)

    if len(profiles) > 1:
        await push_profile_user_ids(user_id, [p["user_id"] for p in profiles[1:]])

    return profiles[0]


async def _send_profile(target: Message, profile: dict) -> None:
    profile_id = profile["id"]
    to_user_id = profile["user_id"]
    keyboard = like_dislike_keyboard(profile_id, to_user_id)

    text = f"<b>{profile['name']}, {profile['age']}</b>\n"
    text += f"Пол: {GENDER_DISPLAY.get(profile['gender'], profile['gender'])}\n"
    if profile.get("city"):
        text += f"Город: {profile['city']}\n"
    if profile.get("bio"):
        text += f"\n{profile['bio']}"

    if profile.get("photo_id"):
        await target.answer_photo(profile["photo_id"], caption=text, reply_markup=keyboard)
    else:
        await target.answer(text, reply_markup=keyboard)


@router.message(F.text == "🔍 Смотреть анкеты")
async def browse_profiles(message: Message, profile_api: ProfileAPIClient) -> None:
    profile = await _get_next_profile(message.from_user.id, profile_api)
    if not profile:
        await message.answer("Пока нет анкет для показа. Загляни позже 😔")
        return
    await _send_profile(message, profile)


@router.callback_query(F.data.startswith("like:"))
async def handle_like(
    callback: CallbackQuery, profile_api: ProfileAPIClient, match_api: MatchAPIClient
) -> None:
    _, profile_id, to_user_id_str = callback.data.split(":", 2)
    to_user_id = int(to_user_id_str)
    from_user_id = callback.from_user.id

    await mark_seen(from_user_id, to_user_id)

    result = await match_api.create_like(
        from_user_id=from_user_id,
        to_user_id=to_user_id,
        to_profile_id=profile_id,
    )

    try:
        await publish_user_like(from_user_id, to_user_id, profile_id)
    except Exception as exc:
        logger.warning("Failed to publish user.like: %s", exc)

    await callback.answer("❤️")

    if result and result.get("is_match"):
        await callback.message.answer("🎉 Это мэтч! Вы понравились друг другу!")

    profile = await _get_next_profile(from_user_id, profile_api)
    if not profile:
        await callback.message.answer("Больше анкет нет. Загляни позже 😔", reply_markup=main_menu_keyboard())
        return
    await _send_profile(callback.message, profile)


@router.callback_query(F.data.startswith("skip:"))
async def handle_skip(callback: CallbackQuery, profile_api: ProfileAPIClient) -> None:
    _, to_user_id_str = callback.data.split(":", 1)
    await mark_seen(callback.from_user.id, int(to_user_id_str))
    await callback.answer("👎")
    profile = await _get_next_profile(callback.from_user.id, profile_api)
    if not profile:
        await callback.message.answer("Больше анкет нет. Загляни позже 😔", reply_markup=main_menu_keyboard())
        return
    await _send_profile(callback.message, profile)
