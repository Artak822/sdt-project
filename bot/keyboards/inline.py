from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def like_dislike_keyboard(profile_id: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="❤️ Лайк", callback_data=f"like:{profile_id}")
    builder.button(text="👎 Пропустить", callback_data=f"skip:{profile_id}")
    builder.adjust(2)
    return builder.as_markup()


def start_registration_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Зарегистрироваться", callback_data="start_registration")
    return builder.as_markup()
