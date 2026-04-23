import logging
from typing import Optional, List

import aiohttp

logger = logging.getLogger(__name__)


class ProfileAPIClient:
    def __init__(self, base_url: str, session: aiohttp.ClientSession) -> None:
        self._base = base_url.rstrip("/")
        self._session = session

    async def get_profile(self, user_id: int) -> Optional[dict]:
        try:
            async with self._session.get(f"{self._base}/profiles/user/{user_id}") as resp:
                if resp.status == 200:
                    return await resp.json()
                if resp.status == 404:
                    return None
                logger.warning("get_profile unexpected status: %d", resp.status)
        except aiohttp.ClientError as exc:
            logger.error("get_profile failed: %s", exc)
        return None

    async def create_profile(
        self,
        user_id: int,
        name: str,
        age: int,
        gender: str,
        looking_for: str,
        city: Optional[str] = None,
        bio: Optional[str] = None,
        photo_id: Optional[str] = None,
    ) -> Optional[dict]:
        payload = {
            "user_id": user_id,
            "name": name,
            "age": age,
            "gender": gender,
            "looking_for": looking_for,
            "city": city,
            "bio": bio,
            "photo_id": photo_id,
        }
        try:
            async with self._session.post(f"{self._base}/profiles/", json=payload) as resp:
                if resp.status in (200, 201):
                    return await resp.json()
                text = await resp.text()
                logger.error("create_profile failed: status=%d body=%s", resp.status, text)
        except aiohttp.ClientError as exc:
            logger.error("create_profile failed: %s", exc)
        return None

    async def update_profile(self, user_id: int, **kwargs) -> Optional[dict]:
        try:
            async with self._session.patch(
                f"{self._base}/profiles/user/{user_id}", json=kwargs
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                text = await resp.text()
                logger.error("update_profile failed: status=%d body=%s", resp.status, text)
        except aiohttp.ClientError as exc:
            logger.error("update_profile failed: %s", exc)
        return None

    async def delete_profile(self, user_id: int) -> bool:
        try:
            async with self._session.delete(
                f"{self._base}/profiles/user/{user_id}"
            ) as resp:
                return resp.status == 204
        except aiohttp.ClientError as exc:
            logger.error("delete_profile failed: %s", exc)
        return False

    async def get_feed(self, user_id: int, limit: int = 10, excluded: list[int] | None = None) -> List[dict]:
        params: dict = {"limit": limit}
        if excluded:
            params["excluded"] = ",".join(str(i) for i in excluded)
        try:
            async with self._session.get(
                f"{self._base}/profiles/feed/{user_id}", params=params
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                logger.warning("get_feed unexpected status: %d", resp.status)
        except aiohttp.ClientError as exc:
            logger.error("get_feed failed: %s", exc)
        return []
