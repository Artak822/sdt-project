import logging
from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery

from bot.keyboards.inline import start_registration_keyboard
from bot.keyboards.reply import main_menu_keyboard
from bot.services.user_api import UserAPIClient
from bot.services.publisher import publish_user_register

logger = logging.getLogger(__name__)
router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, user_api: UserAPIClient) -> None:
    user_id = message.from_user.id
    username = message.from_user.username

    # Проверяем, зарегистрирован ли пользователь
    existing_user = await user_api.get_user(user_id)

    if existing_user:
        await message.answer(
            f"С возвращением, {message.from_user.first_name}! 👋",
            reply_markup=main_menu_keyboard(),
        )
        return

    # Новый пользователь — предлагаем регистрацию
    await message.answer(
        "👋 Привет! Это бот для знакомств.\n\n"
        "Здесь ты можешь найти интересных людей рядом с тобой. "
        "Для начала нужно зарегистрироваться и заполнить анкету.\n\n"
        "Нажми кнопку ниже, чтобы начать 👇",
        reply_markup=start_registration_keyboard(),
    )


@router.callback_query(F.data == "start_registration")
async def process_registration(callback: CallbackQuery, user_api: UserAPIClient) -> None:
    user_id = callback.from_user.id
    username = callback.from_user.username

    # Регистрируем пользователя
    success = await user_api.register_user(user_id, username)

    if not success:
        logger.error("Failed to register user: id=%d", user_id)
        await callback.answer("Произошла ошибка. Попробуй позже.", show_alert=True)
        return

    # Публикуем событие в RabbitMQ (не блокируем регистрацию если MQ недоступен)
    try:
        await publish_user_register(user_id, username)
    except Exception as exc:
        logger.warning("Failed to publish user.register event: %s", exc)

    logger.info("User registered: id=%d, username=%s", user_id, username)

    await callback.answer()
    await callback.message.edit_text(
        f"✅ Отлично, {callback.from_user.first_name}! Ты зарегистрирован.\n\n"
        "Теперь заполни анкету, чтобы тебя могли найти другие пользователи. "
        "Для этого нажми 👤 Моя анкета в меню.",
    )
    await callback.message.answer(
        "Выбери действие:", reply_markup=main_menu_keyboard()
    )
