from aiogram import Dispatcher

from bot.handlers import start, menu


def register_all_handlers(dp: Dispatcher) -> None:
    dp.include_router(start.router)
    dp.include_router(menu.router)
