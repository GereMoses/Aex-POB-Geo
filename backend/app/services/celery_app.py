"""
Celery application and shared notification tasks.

The Celery app used to be defined inside the mustering task module, so removing
mustering would have taken the whole worker with it. It lives here now, named
for what it actually is, with only the notification tasks that the attendance
product still needs — SMS, email and WhatsApp dispatch.

The drill scheduler, siren triggers and muster escalation tasks were removed
with the mustering module.
"""

import logging
import os

import requests
from celery import Celery
from celery.schedules import crontab
from sqlalchemy.orm import sessionmaker

from app.core.database import engine

logger = logging.getLogger(__name__)

_redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "apex_pob",
    broker=_redis_url,
    backend=_redis_url,
    include=[
        "app.services.celery_app",
        "app.tasks.compliance_email_celery",
    ],
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@celery_app.task(bind=True, max_retries=3)
def send_sms_notification(self, message, recipients):
    """Send SMS via generic HTTP provider (SMS_API_KEY + SMS_API_URL env vars)."""
    try:
        sms_api_key = os.getenv('SMS_API_KEY')
        sms_api_url = os.getenv('SMS_API_URL')
        if not sms_api_key or not sms_api_url:
            logger.warning("SMS not configured — set SMS_API_KEY and SMS_API_URL to enable")
            return
        logger.info(f"Sending SMS to {len(recipients)} recipients")
        for recipient in recipients:
            try:
                resp = requests.post(
                    sms_api_url,
                    json={'api_key': sms_api_key, 'to': recipient, 'message': message},
                    timeout=10,
                )
                resp.raise_for_status()
                logger.info(f"SMS sent to {recipient}")
            except Exception as exc:
                logger.error(f"SMS to {recipient} failed: {exc}")
    except Exception as e:
        logger.error(f"❌ send_sms_notification error: {e}")
        raise self.retry(exc=e, countdown=60)


@celery_app.task(bind=True, max_retries=3)
def send_email_notification(self, subject, message, recipients):
    """Send email via SMTP (SMTP_HOST / SMTP_PORT / SMTP_USER / SMTP_PASSWORD env vars)."""
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        smtp_host = os.getenv('SMTP_HOST')
        smtp_port = int(os.getenv('SMTP_PORT', '587'))
        smtp_user = os.getenv('SMTP_USER')
        smtp_pass = os.getenv('SMTP_PASSWORD')
        email_from = os.getenv('EMAIL_FROM', smtp_user)
        if not smtp_host or not smtp_user:
            logger.warning("Email not configured — set SMTP_HOST, SMTP_USER, SMTP_PASSWORD to enable")
            return
        logger.info(f"Sending email '{subject}' to {len(recipients)} recipients")
        for recipient in recipients:
            try:
                msg = MIMEMultipart('alternative')
                msg['Subject'] = subject
                msg['From'] = email_from
                msg['To'] = recipient
                msg.attach(MIMEText(message, 'plain'))
                with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
                    server.ehlo()
                    server.starttls()
                    server.login(smtp_user, smtp_pass)
                    server.sendmail(email_from, [recipient], msg.as_string())
                logger.info(f"Email sent to {recipient}")
            except Exception as exc:
                logger.error(f"Email to {recipient} failed: {exc}")
    except Exception as e:
        logger.error(f"❌ send_email_notification error: {e}")
        raise self.retry(exc=e, countdown=60)


@celery_app.task(bind=True, max_retries=3)
def send_whatsapp_notification(self, message, recipients):
    """Send WhatsApp via generic HTTP provider (WHATSAPP_API_KEY + WHATSAPP_API_URL env vars)."""
    try:
        whatsapp_api_key = os.getenv('WHATSAPP_API_KEY')
        whatsapp_api_url = os.getenv('WHATSAPP_API_URL')
        if not whatsapp_api_key or not whatsapp_api_url:
            logger.warning("WhatsApp not configured — set WHATSAPP_API_KEY and WHATSAPP_API_URL to enable")
            return
        logger.info(f"Sending WhatsApp to {len(recipients)} recipients")
        for recipient in recipients:
            try:
                resp = requests.post(
                    whatsapp_api_url,
                    json={'api_key': whatsapp_api_key, 'to': recipient, 'message': message},
                    timeout=10,
                )
                resp.raise_for_status()
                logger.info(f"WhatsApp sent to {recipient}")
            except Exception as exc:
                logger.error(f"WhatsApp to {recipient} failed: {exc}")
    except Exception as e:
        logger.error(f"❌ send_whatsapp_notification error: {e}")
        raise self.retry(exc=e, countdown=60)


celery_app.conf.beat_schedule = {
    "compliance-digest-daily": {
        "task": "app.tasks.compliance_email_celery.send_compliance_digest_task",
        "schedule": crontab(hour=6, minute=0),  # 06:00 UTC daily
        "args": (),
    },
}

celery_app.conf.timezone = "UTC"
