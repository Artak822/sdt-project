import logging

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from bot.keyboards.inline import settings_keyboard, confirm_delete_keyboard
from bot.keyboards.reply import main_menu_keyboard
from bot.services.match_api import MatchAPIClient
from bot.services.profile_api import ProfileAPIClient

logger = logging.getLogger(__name__)
router = Router()

GENDER_DISPLAY = {"male": "Мужчина", "female": "Женщина", "other": "Другое"}


@router.message(F.text == "❤️ Мэтчи")
async def my_matches(
    message: Message, match_api: MatchAPIClient, profile_api: ProfileAPIClient
) -> None:
    matches = await match_api.get_matches(message.from_user.id)
    if not matches:
        await message.answer("У тебя пока нет мэтчей. Лайкай анкеты! 😊")
        return

    text = "❤️ <b>Твои мэтчи:</b>\n\n"
    for match in matches:
        other_id = (
            match["user2_id"] if match["user1_id"] == message.from_user.id else match["user1_id"]
        )
        profile = await profile_api.get_profile(other_id)
        if profile:
            text += f"• {profile['name']}, {profile['age']}"
            if profile.get("city"):
                text += f" — {profile['city']}"
            text += "\n"

    await message.answer(text)


@router.message(F.text == "⚙️ Настройки")
async def settings_handler(message: Message) -> None:
    await message.answer("⚙️ <b>Настройки</b>", reply_markup=settings_keyboard())


@router.callback_query(F.data == "settings_delete")
async def settings_delete(callback: CallbackQuery) -> None:
    await callback.answer()
    await callback.message.answer(
        "Ты уверен, что хочешь удалить анкету? Это действие нельзя отменить.",
        reply_markup=confirm_delete_keyboard(),
    )


@router.callback_query(F.data == "confirm_delete")
async def confirm_delete(callback: CallbackQuery, profile_api: ProfileAPIClient) -> None:
    success = await profile_api.delete_profile(callback.from_user.id)
    await callback.answer()
    if success:
        await callback.message.answer(
            "🗑 Анкета удалена. Ты можешь создать новую в разделе «👤 Моя анкета».",
            reply_markup=main_menu_keyboard(),
        )
    else:
        await callback.message.answer("Произошла ошибка. Попробуй позже.")


@router.callback_query(F.data == "cancel_delete")
async def cancel_delete(callback: CallbackQuery) -> None:
    await callback.answer("Отменено")
    await callback.message.answer("Удаление отменено.", reply_markup=main_menu_keyboard())
