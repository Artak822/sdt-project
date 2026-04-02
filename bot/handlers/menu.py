import logging
from aiogram import Router, F
from aiogram.types import Message

logger = logging.getLogger(__name__)
router = Router()


@router.message(F.text == "👤 Моя анкета")
async def my_profile(message: Message) -> None:
    await message.answer("Раздел анкеты — в разработке 🚧")


@router.message(F.text == "🔍 Смотреть анкеты")
async def browse_profiles(message: Message) -> None:
    await message.answer("Поиск анкет — в разработке 🚧")


@router.message(F.text == "❤️ Мэтчи")
async def my_matches(message: Message) -> None:
    await message.answer("Мэтчи — в разработке 🚧")


@router.message(F.text == "⚙️ Настройки")
async def settings(message: Message) -> None:
    await message.answer("Настройки — в разработке 🚧")
