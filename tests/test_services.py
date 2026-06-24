"""Unit-тесты CRUD-функций с мок-сессией."""
import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from services.match_service.crud import (
    check_mutual_like,
    create_like,
    create_match,
    get_like,
    get_match,
    get_user_matches,
)
from services.match_service.models import Like, Match
from services.rating_service.crud import create_or_update_rating, get_rating
from services.rating_service.models import Rating
from services.user_service.crud import create_user, get_or_create_user, get_user, update_profile
from services.user_service.models import Profile, User


def make_session(scalar_value=None, scalars_list=None):
    """Создаёт AsyncMock-сессию с настроенным результатом execute."""
    session = AsyncMock()
    session.add = MagicMock()

    result = MagicMock()
    result.scalar_one_or_none.return_value = scalar_value
    if scalars_list is not None:
        result.scalars.return_value.all.return_value = scalars_list

    session.execute.return_value = result
    return session, result


# ---------------------------------------------------------------------------
# user_service.crud
# ---------------------------------------------------------------------------


class TestGetUser:
    @pytest.mark.asyncio
    async def test_returns_user_when_found(self):
        user = User(id=1, username="alice")
        session, _ = make_session(scalar_value=user)

        result = await get_user(session, 1)

        assert result is user

    @pytest.mark.asyncio
    async def test_returns_none_when_not_found(self):
        session, _ = make_session(scalar_value=None)

        result = await get_user(session, 999)

        assert result is None


class TestCreateUser:
    @pytest.mark.asyncio
    async def test_creates_and_returns_user(self):
        session, _ = make_session()
        session.refresh = AsyncMock()

        result = await create_user(session, 42, "bob")

        session.add.assert_called_once()
        session.commit.assert_awaited_once()
        assert result.id == 42
        assert result.username == "bob"

    @pytest.mark.asyncio
    async def test_username_can_be_none(self):
        session, _ = make_session()
        session.refresh = AsyncMock()

        result = await create_user(session, 7, None)

        assert result.username is None


class TestGetOrCreateUser:
    @pytest.mark.asyncio
    async def test_returns_existing_user(self):
        existing = User(id=1, username="alice")
        session, _ = make_session(scalar_value=existing)

        user, created = await get_or_create_user(session, 1, "alice")

        assert user is existing
        assert created is False

    @pytest.mark.asyncio
    async def test_creates_new_user(self):
        session, _ = make_session(scalar_value=None)
        session.refresh = AsyncMock()

        user, created = await get_or_create_user(session, 99, "new_user")

        assert created is True
        assert user.id == 99


class TestUpdateProfile:
    @pytest.mark.asyncio
    async def test_updates_allowed_fields(self):
        session, _ = make_session()
        session.refresh = AsyncMock()

        profile = Profile(
            id=uuid.uuid4(),
            user_id=1,
            name="Old",
            age=25,
            gender="male",
            looking_for="female",
        )

        result = await update_profile(session, profile, name="New", age=30)

        assert result.name == "New"
        assert result.age == 30

    @pytest.mark.asyncio
    async def test_skips_none_for_required_fields(self):
        session, _ = make_session()
        session.refresh = AsyncMock()

        profile = Profile(
            id=uuid.uuid4(),
            user_id=1,
            name="Alice",
            age=22,
            gender="female",
            looking_for="male",
        )

        result = await update_profile(session, profile, name=None)

        assert result.name == "Alice"


# ---------------------------------------------------------------------------
# match_service.crud
# ---------------------------------------------------------------------------


class TestGetLike:
    @pytest.mark.asyncio
    async def test_returns_like(self):
        like = Like(id=uuid.uuid4(), from_user_id=1, to_user_id=2, to_profile_id=uuid.uuid4())
        session, _ = make_session(scalar_value=like)

        result = await get_like(session, 1, 2)

        assert result is like

    @pytest.mark.asyncio
    async def test_returns_none(self):
        session, _ = make_session(scalar_value=None)

        result = await get_like(session, 1, 2)

        assert result is None


class TestCreateLike:
    @pytest.mark.asyncio
    async def test_creates_like(self):
        session, _ = make_session()
        session.refresh = AsyncMock()
        profile_id = uuid.uuid4()

        result = await create_like(session, 1, 2, profile_id)

        session.add.assert_called_once()
        session.commit.assert_awaited_once()
        assert result.from_user_id == 1
        assert result.to_user_id == 2
        assert result.to_profile_id == profile_id


class TestCheckMutualLike:
    @pytest.mark.asyncio
    async def test_mutual_like_exists(self):
        reverse_like = Like(id=uuid.uuid4(), from_user_id=2, to_user_id=1, to_profile_id=uuid.uuid4())
        session, _ = make_session(scalar_value=reverse_like)

        result = await check_mutual_like(session, 1, 2)

        assert result is True

    @pytest.mark.asyncio
    async def test_no_mutual_like(self):
        session, _ = make_session(scalar_value=None)

        result = await check_mutual_like(session, 1, 2)

        assert result is False


class TestGetMatch:
    @pytest.mark.asyncio
    async def test_returns_match_regardless_of_order(self):
        match = Match(id=uuid.uuid4(), user1_id=1, user2_id=2)
        session, _ = make_session(scalar_value=match)

        result = await get_match(session, 2, 1)

        assert result is match

    @pytest.mark.asyncio
    async def test_sorts_ids(self):
        session, _ = make_session(scalar_value=None)

        await get_match(session, 5, 3)

        session.execute.assert_awaited_once()


class TestCreateMatch:
    @pytest.mark.asyncio
    async def test_creates_match_with_sorted_ids(self):
        session = AsyncMock()
        session.add = MagicMock()
        session.refresh = AsyncMock()

        like_a = Like(id=uuid.uuid4(), from_user_id=3, to_user_id=5, to_profile_id=uuid.uuid4(), is_mutual=False)
        like_b = Like(id=uuid.uuid4(), from_user_id=5, to_user_id=3, to_profile_id=uuid.uuid4(), is_mutual=False)

        results = [like_a, like_b]
        call_count = 0

        def side_effect(*args, **kwargs):
            nonlocal call_count
            r = MagicMock()
            if call_count < len(results):
                r.scalar_one_or_none.return_value = results[call_count]
            else:
                r.scalar_one_or_none.return_value = None
            call_count += 1
            return r

        session.execute.side_effect = side_effect

        result = await create_match(session, 5, 3)

        assert result.user1_id == 3
        assert result.user2_id == 5
        assert like_a.is_mutual is True
        assert like_b.is_mutual is True


class TestGetUserMatches:
    @pytest.mark.asyncio
    async def test_returns_all_matches(self):
        matches = [
            Match(id=uuid.uuid4(), user1_id=1, user2_id=2),
            Match(id=uuid.uuid4(), user1_id=1, user2_id=3),
        ]
        session, _ = make_session(scalars_list=matches)

        result = await get_user_matches(session, 1)

        assert len(result) == 2


# ---------------------------------------------------------------------------
# rating_service.crud
# ---------------------------------------------------------------------------


class TestGetRating:
    @pytest.mark.asyncio
    async def test_returns_rating(self):
        profile_id = uuid.uuid4()
        rating = Rating(id=uuid.uuid4(), profile_id=profile_id)
        session, _ = make_session(scalar_value=rating)

        result = await get_rating(session, profile_id)

        assert result is rating

    @pytest.mark.asyncio
    async def test_returns_none_when_not_found(self):
        session, _ = make_session(scalar_value=None)

        result = await get_rating(session, uuid.uuid4())

        assert result is None


class TestCreateOrUpdateRating:
    @pytest.mark.asyncio
    async def test_creates_new_rating(self):
        session, _ = make_session(scalar_value=None)
        session.refresh = AsyncMock()
        profile_id = uuid.uuid4()

        result = await create_or_update_rating(
            session,
            profile_id,
            primary_score=Decimal("80"),
            behavioral_score=Decimal("55"),
            combined_score=Decimal("59.50"),
        )

        session.add.assert_called_once()
        assert result.primary_score == Decimal("80")

    @pytest.mark.asyncio
    async def test_updates_existing_rating(self):
        profile_id = uuid.uuid4()
        existing = Rating(
            id=uuid.uuid4(),
            profile_id=profile_id,
            primary_score=Decimal("50"),
            behavioral_score=Decimal("30"),
            combined_score=Decimal("35"),
        )
        session, _ = make_session(scalar_value=existing)
        session.refresh = AsyncMock()

        result = await create_or_update_rating(
            session,
            profile_id,
            primary_score=Decimal("90"),
            behavioral_score=Decimal("70"),
            combined_score=Decimal("71"),
        )

        session.add.assert_not_called()
        assert result.combined_score == Decimal("71")
