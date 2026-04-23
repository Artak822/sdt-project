import logging
from typing import Optional, List

import aiohttp

logger = logging.getLogger(__name__)


class MatchAPIClient:
    def __init__(self, base_url: str, session: aiohttp.ClientSession) -> None:
        self._base = base_url.rstrip("/")
        self._session = session

    async def create_like(
        self, from_user_id: int, to_user_id: int, to_profile_id: str
    ) -> Optional[dict]:
        payload = {
            "from_user_id": from_user_id,
            "to_user_id": to_user_id,
            "to_profile_id": to_profile_id,
        }
        try:
            async with self._session.post(f"{self._base}/likes/", json=payload) as resp:
                if resp.status in (200, 201):
                    return await resp.json()
                logger.warning("create_like unexpected status: %d", resp.status)
        except aiohttp.ClientError as exc:
            logger.error("create_like failed: %s", exc)
        return None

    async def get_matches(self, user_id: int) -> List[dict]:
        try:
            async with self._session.get(f"{self._base}/matches/{user_id}") as resp:
                if resp.status == 200:
                    return await resp.json()
                logger.warning("get_matches unexpected status: %d", resp.status)
        except aiohttp.ClientError as exc:
            logger.error("get_matches failed: %s", exc)
        return []
