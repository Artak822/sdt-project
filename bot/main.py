import asyncio
import logging

import aiohttp
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config import settings
from bot.handlers import register_all_handlers
from bot.services.publisher import connect_rabbitmq, close_rabbitmq
from bot.services.user_api import UserAPIClient

logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    bot = Bot(
        token=settings.TELEGRAM_BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())
    register_all_handlers(dp)

    # HTTP-сессия для user_service
    http_session = aiohttp.ClientSession()
    user_api = UserAPIClient(settings.USER_SERVICE_URL, http_session)

    # Прокидываем зависимости через workflow_data
    dp["user_api"] = user_api

    # Подключение к RabbitMQ
    await connect_rabbitmq()

    logger.info("Bot started")
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await close_rabbitmq()
        await http_session.close()
        await bot.session.close()
        logger.info("Bot stopped")


if __name__ == "__main__":
    asyncio.run(main())
