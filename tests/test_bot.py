"""Unit-тесты логики матчинга (match_service.logic)."""
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.match_service.models import Like, Match


class TestProcessLike:
    @pytest.mark.asyncio
    async def test_returns_existing_like_with_match(self):
        from services.match_service.logic import process_like

        session = AsyncMock()
        existing_like = Like(id=uuid.uuid4(), from_user_id=1, to_user_id=2, to_profile_id=uuid.uuid4())
        existing_match = Match(id=uuid.uuid4(), user1_id=1, user2_id=2)

        with (
            patch("services.match_service.logic.get_like", return_value=existing_like),
            patch("services.match_service.logic.get_match", return_value=existing_match),
        ):
            like, is_mutual, match = await process_like(session, 1, 2, uuid.uuid4())

        assert like is existing_like
        assert is_mutual is True
        assert match is existing_match

    @pytest.mark.asyncio
    async def test_returns_existing_like_without_match(self):
        from services.match_service.logic import process_like

        session = AsyncMock()
        existing_like = Like(id=uuid.uuid4(), from_user_id=1, to_user_id=2, to_profile_id=uuid.uuid4())

        with (
            patch("services.match_service.logic.get_like", return_value=existing_like),
            patch("services.match_service.logic.get_match", return_value=None),
        ):
            like, is_mutual, match = await process_like(session, 1, 2, uuid.uuid4())

        assert like is existing_like
        assert is_mutual is False
        assert match is None

    @pytest.mark.asyncio
    async def test_creates_like_without_mutual(self):
        from services.match_service.logic import process_like

        session = AsyncMock()
        new_like = Like(id=uuid.uuid4(), from_user_id=1, to_user_id=2, to_profile_id=uuid.uuid4())

        with (
            patch("services.match_service.logic.get_like", return_value=None),
            patch("services.match_service.logic.create_like", return_value=new_like),
            patch("services.match_service.logic.check_mutual_like", return_value=False),
        ):
            like, is_mutual, match = await process_like(session, 1, 2, uuid.uuid4())

        assert like is new_like
        assert is_mutual is False
        assert match is None

    @pytest.mark.asyncio
    async def test_creates_match_on_mutual_like(self):
        from services.match_service.logic import process_like

        session = AsyncMock()
        new_like = Like(id=uuid.uuid4(), from_user_id=1, to_user_id=2, to_profile_id=uuid.uuid4())
        new_match = Match(id=uuid.uuid4(), user1_id=1, user2_id=2)

        with (
            patch("services.match_service.logic.get_like", return_value=None),
            patch("services.match_service.logic.create_like", return_value=new_like),
            patch("services.match_service.logic.check_mutual_like", return_value=True),
            patch("services.match_service.logic.get_match", return_value=None),
            patch("services.match_service.logic.create_match", return_value=new_match),
        ):
            like, is_mutual, match = await process_like(session, 1, 2, uuid.uuid4())

        assert is_mutual is True
        assert match is new_match

    @pytest.mark.asyncio
    async def test_returns_existing_match_on_repeated_mutual(self):
        from services.match_service.logic import process_like

        session = AsyncMock()
        new_like = Like(id=uuid.uuid4(), from_user_id=1, to_user_id=2, to_profile_id=uuid.uuid4())
        existing_match = Match(id=uuid.uuid4(), user1_id=1, user2_id=2)

        with (
            patch("services.match_service.logic.get_like", return_value=None),
            patch("services.match_service.logic.create_like", return_value=new_like),
            patch("services.match_service.logic.check_mutual_like", return_value=True),
            patch("services.match_service.logic.get_match", return_value=existing_match),
        ):
            like, is_mutual, match = await process_like(session, 1, 2, uuid.uuid4())

        assert match is existing_match
