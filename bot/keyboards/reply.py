from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

KEEP_BTN = "↩️ Оставить как было"


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👤 Моя анкета"), KeyboardButton(text="🔍 Смотреть анкеты")],
            [KeyboardButton(text="❤️ Мэтчи"), KeyboardButton(text="⚙️ Настройки")],
        ],
        resize_keyboard=True,
    )


def keep_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=KEEP_BTN)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def gender_keyboard(with_keep: bool = False) -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text="Мужчина"), KeyboardButton(text="Женщина")],
        [KeyboardButton(text="Другое")],
    ]
    if with_keep:
        rows.append([KeyboardButton(text=KEEP_BTN)])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True, one_time_keyboard=True)


def looking_for_keyboard(with_keep: bool = False) -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text="Мужчину"), KeyboardButton(text="Женщину")],
        [KeyboardButton(text="Не важно")],
    ]
    if with_keep:
        rows.append([KeyboardButton(text=KEEP_BTN)])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True, one_time_keyboard=True)


remove_keyboard = ReplyKeyboardRemove()
