from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👤 Моя анкета"), KeyboardButton(text="🔍 Смотреть анкеты")],
            [KeyboardButton(text="❤️ Мэтчи"), KeyboardButton(text="⚙️ Настройки")],
        ],
        resize_keyboard=True,
    )


def gender_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Мужчина"), KeyboardButton(text="Женщина")],
            [KeyboardButton(text="Другое")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


remove_keyboard = ReplyKeyboardRemove()
