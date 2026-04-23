from decimal import Decimal


def calc_primary_score(
    has_name: bool,
    has_age: bool,
    has_gender: bool,
    has_bio: bool,
    has_city: bool,
    has_looking_for: bool,
    has_photo: bool,
) -> Decimal:
    """Уровень 1: статический рейтинг (0-100) на основе заполненности анкеты."""
    fields = [has_name, has_age, has_gender, has_bio, has_city, has_looking_for]
    filled = sum(1 for f in fields if f)
    completeness_bonus = int((filled / len(fields)) * 40)
    photos_bonus = 20 if has_photo else 0
    preferences_match = 40 if (has_looking_for and has_gender) else 20
    return Decimal(str(min(100, completeness_bonus + photos_bonus + preferences_match)))


def calc_behavioral_score(likes_received: int, matches_count: int) -> Decimal:
    """Уровень 2: поведенческий рейтинг (0-100) на основе активности."""
    likes_score = min(30, likes_received * 2)
    match_score = min(25, matches_count * 5)
    return Decimal(str(min(100, likes_score + match_score)))


def calc_combined_score(primary: Decimal, behavioral: Decimal) -> Decimal:
    """Уровень 3: итоговый рейтинг (40% первичный + 50% поведенческий)."""
    combined = primary * Decimal("0.4") + behavioral * Decimal("0.5")
    return round(min(Decimal("100"), combined), 2)
