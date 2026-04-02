import logging
from typing import Optional

import aiohttp

logger = logging.getLogger(__name__)


class UserAPIClient:
    """HTTP-клиент для взаимодействия с user_service."""

    def __init__(self, base_url: str, session: aiohttp.ClientSession) -> None:
        self._base_url = base_url.rstrip("/")
        self._session = session

    async def get_user(self, user_id: int) -> Optional[dict]:
        """Возвращает данные пользователя или None если не найден."""
        try:
            async with self._session.get(
                f"{self._base_url}/users/{user_id}"
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                if resp.status == 404:
                    return None
                logger.warning("get_user unexpected status: %d", resp.status)
                return None
        except aiohttp.ClientError as exc:
            logger.error("get_user failed: %s", exc)
            return None

    async def register_user(self, user_id: int, username: Optional[str]) -> bool:
        """Регистрирует пользователя. Возвращает True при успехе."""
        payload = {"user_id": user_id, "username": username}
        try:
            async with self._session.post(
                f"{self._base_url}/users/", json=payload
            ) as resp:
                if resp.status in (200, 201):
                    return True
                text = await resp.text()
                logger.error("register_user failed: status=%d body=%s", resp.status, text)
                return False
        except aiohttp.ClientError as exc:
            logger.error("register_user request error: %s", exc)
            return False
