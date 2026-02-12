"""
Celery application configuration
"""

from celery import Celery
from app.core.config import settings

# Create Celery app
celery_app = Celery(
    "codevoyage",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.analysis_tasks",
    ]
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=settings.CELERY_TASK_TIMEOUT,
    task_soft_time_limit=settings.CELERY_TASK_TIMEOUT - 60,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)
