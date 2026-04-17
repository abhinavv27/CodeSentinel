from celery import Celery
from app.core.config import get_settings
from app.core.telemetry import setup_telemetry
from opentelemetry.instrumentation.celery import CeleryInstrumentor

settings = get_settings()

setup_telemetry("codesentinel-worker")
CeleryInstrumentor().instrument()

celery_app = Celery(
    "codesentinel",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_routes={
        "run_pr_review": {"queue": "reviews"},
    },
)
