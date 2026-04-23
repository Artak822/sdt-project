import logging

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from celery_worker.celery_app import app
from celery_worker.config import settings

logger = logging.getLogger(__name__)
_engine = create_engine(settings.DATABASE_URL)


def _session() -> Session:
    return Session(_engine)


@app.task(name="celery_worker.tasks.recalculate_behavioral_ratings")
def recalculate_behavioral_ratings() -> None:
    with _session() as session:
        rows = session.execute(text("""
            SELECT
                r.id,
                r.primary_score,
                COUNT(DISTINCT l.id)  AS likes_received,
                COUNT(DISTINCT m.id)  AS matches_count
            FROM ratings r
            LEFT JOIN profiles p  ON p.id = r.profile_id
            LEFT JOIN likes l     ON l.to_user_id = p.user_id
            LEFT JOIN matches m   ON m.user1_id = p.user_id OR m.user2_id = p.user_id
            GROUP BY r.id, r.primary_score
        """)).fetchall()

        for row in rows:
            likes = row.likes_received or 0
            matches = row.matches_count or 0
            behavioral = min(100, likes * 2 + matches * 5)
            combined = round(min(100.0, float(row.primary_score) * 0.4 + behavioral * 0.5), 2)
            session.execute(text("""
                UPDATE ratings
                SET behavioral_score = :behavioral, combined_score = :combined
                WHERE id = :id
            """), {"behavioral": behavioral, "combined": combined, "id": str(row.id)})

        session.commit()
        logger.info("Recalculated behavioral ratings for %d profiles", len(rows))


@app.task(name="celery_worker.tasks.recalculate_combined_ratings")
def recalculate_combined_ratings() -> None:
    with _session() as session:
        session.execute(text("""
            UPDATE ratings
            SET combined_score = ROUND(LEAST(100, primary_score * 0.4 + behavioral_score * 0.5), 2)
        """))
        session.commit()
        logger.info("Recalculated combined ratings")
