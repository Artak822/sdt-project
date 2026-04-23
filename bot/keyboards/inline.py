from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def like_dislike_keyboard(profile_id: str, to_user_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="❤️ Лайк", callback_data=f"like:{profile_id}:{to_user_id}")
    builder.button(text="👎 Пропустить", callback_data=f"skip:{to_user_id}")
    builder.adjust(2)
    return builder.as_markup()


def edit_profile_button() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✏️ Редактировать анкету", callback_data="edit_profile")
    return builder.as_markup()


def settings_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✏️ Изменить анкету", callback_data="settings_edit")
    builder.button(text="🗑 Удалить анкету", callback_data="settings_delete")
    builder.adjust(1)
    return builder.as_markup()


def confirm_delete_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Да, удалить", callback_data="confirm_delete")
    builder.button(text="↩️ Отмена", callback_data="cancel_delete")
    builder.adjust(2)
    return builder.as_markup()


def start_registration_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Зарегистрироваться", callback_data="start_registration")
    return builder.as_markup()
