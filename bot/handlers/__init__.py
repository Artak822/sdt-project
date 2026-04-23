from aiogram import Dispatcher

from bot.handlers import start, menu, profile, search


def register_all_handlers(dp: Dispatcher) -> None:
    dp.include_router(start.router)
    dp.include_router(profile.router)
    dp.include_router(search.router)
    dp.include_router(menu.router)
