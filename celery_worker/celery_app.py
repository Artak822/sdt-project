from celery import Celery

from celery_worker.config import settings

app = Celery(
    "dating_worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["celery_worker.tasks"],
)

app.conf.beat_schedule = {
    "recalculate-behavioral-ratings": {
        "task": "celery_worker.tasks.recalculate_behavioral_ratings",
        "schedule": 600.0,
    },
    "recalculate-combined-ratings": {
        "task": "celery_worker.tasks.recalculate_combined_ratings",
        "schedule": 3600.0,
    },
}

app.conf.timezone = "UTC"
