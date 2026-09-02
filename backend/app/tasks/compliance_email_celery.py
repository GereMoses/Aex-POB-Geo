"""
Celery task wrapper for the compliance email digest.
Registered in celery_app.py beat_schedule.
"""
import logging
from app.services.celery_app import celery_app
from app.tasks.compliance_email_task import send_compliance_digest

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.compliance_email_celery.send_compliance_digest_task",
                 bind=True, max_retries=2, default_retry_delay=300)
def send_compliance_digest_task(self):
    """Daily compliance digest — runs at 06:00 UTC via Celery Beat."""
    try:
        result = send_compliance_digest()
        logger.info("Compliance digest task completed: %s", result)
        return result
    except Exception as exc:
        logger.error("Compliance digest task failed: %s", exc)
        raise self.retry(exc=exc)
