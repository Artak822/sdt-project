"""Unit-тесты алгоритмов рейтинга (без БД)."""
from decimal import Decimal

import pytest

from services.rating_service.algorithms import (
    calc_primary_score,
    calc_behavioral_score,
    calc_combined_score,
)


class TestCalcPrimaryScore:
    def test_full_profile_with_photo(self):
        score = calc_primary_score(
            has_name=True,
            has_age=True,
            has_gender=True,
            has_bio=True,
            has_city=True,
            has_looking_for=True,
            has_photo=True,
        )
        assert score == Decimal("100")

    def test_empty_profile_no_photo(self):
        score = calc_primary_score(
            has_name=False,
            has_age=False,
            has_gender=False,
            has_bio=False,
            has_city=False,
            has_looking_for=False,
            has_photo=False,
        )
        # completeness=0, photos=0, preferences_match=20 (нет ни gender ни looking_for)
        assert score == Decimal("20")

    def test_full_profile_no_photo(self):
        score = calc_primary_score(
            has_name=True,
            has_age=True,
            has_gender=True,
            has_bio=True,
            has_city=True,
            has_looking_for=True,
            has_photo=False,
        )
        # completeness=40, photos=0, preferences_match=40
        assert score == Decimal("80")

    def test_partial_profile_with_photo(self):
        # 3 из 6 полей = 50% → completeness=20
        score = calc_primary_score(
            has_name=True,
            has_age=True,
            has_gender=True,
            has_bio=False,
            has_city=False,
            has_looking_for=False,
            has_photo=True,
        )
        # completeness=20, photos=20, preferences_match=20 (нет looking_for)
        assert score == Decimal("60")

    def test_score_not_exceeds_100(self):
        score = calc_primary_score(
            has_name=True,
            has_age=True,
            has_gender=True,
            has_bio=True,
            has_city=True,
            has_looking_for=True,
            has_photo=True,
        )
        assert score <= Decimal("100")


class TestCalcBehavioralScore:
    def test_zero_activity(self):
        score = calc_behavioral_score(likes_received=0, matches_count=0)
        assert score == Decimal("0")

    def test_max_likes(self):
        # 15 лайков * 2 = 30 (макс)
        score = calc_behavioral_score(likes_received=15, matches_count=0)
        assert score == Decimal("30")

    def test_likes_capped_at_30(self):
        score = calc_behavioral_score(likes_received=100, matches_count=0)
        assert score == Decimal("30")

    def test_max_matches(self):
        # 5 мэтчей * 5 = 25 (макс)
        score = calc_behavioral_score(likes_received=0, matches_count=5)
        assert score == Decimal("25")

    def test_matches_capped_at_25(self):
        score = calc_behavioral_score(likes_received=0, matches_count=100)
        assert score == Decimal("25")

    def test_combined_max(self):
        score = calc_behavioral_score(likes_received=100, matches_count=100)
        assert score == Decimal("55")

    def test_score_not_exceeds_100(self):
        score = calc_behavioral_score(likes_received=999, matches_count=999)
        assert score <= Decimal("100")


class TestCalcCombinedScore:
    def test_both_zero(self):
        score = calc_combined_score(Decimal("0"), Decimal("0"))
        assert score == Decimal("0")

    def test_full_scores(self):
        score = calc_combined_score(Decimal("100"), Decimal("100"))
        # 100*0.4 + 100*0.5 = 90
        assert score == Decimal("90")

    def test_only_primary(self):
        score = calc_combined_score(Decimal("100"), Decimal("0"))
        assert score == Decimal("40")

    def test_only_behavioral(self):
        score = calc_combined_score(Decimal("0"), Decimal("100"))
        assert score == Decimal("50")

    def test_not_exceeds_100(self):
        score = calc_combined_score(Decimal("200"), Decimal("200"))
        assert score <= Decimal("100")

    def test_rounding(self):
        score = calc_combined_score(Decimal("33"), Decimal("33"))
        # 33*0.4 + 33*0.5 = 13.2 + 16.5 = 29.7
        assert score == Decimal("29.70")
