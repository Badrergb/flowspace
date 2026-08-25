import logging
from datetime import date, datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.services.email_service import send_birthday_email, send_reengagement_email

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler(timezone="UTC")


# ─────────────────────────────────────────────
# JOB 1: Birthday Emails (daily at 09:00 UTC)
# ─────────────────────────────────────────────
def run_birthday_job() -> None:
    """
    Daily cron job: find all users whose birthday is today and
    who haven't received a wish this year, then send them a birthday email.
    """
    from app.db.database import get_db

    logger.info("Running daily birthday email job...")
    today = date.today()
    current_year = today.year

    try:
        db = get_db()
        sent_count = 0

        for doc in db.collection("users").stream():
            user = doc.to_dict()
            uid = doc.id
            email = user.get("email")
            birthday_raw = user.get("birthday")
            first_name = (user.get("full_name", "") or "").split()[0] or "there"

            if not email or not birthday_raw:
                continue

            try:
                birthday_dt = datetime.fromisoformat(birthday_raw) if isinstance(birthday_raw, str) else birthday_raw
            except (ValueError, TypeError):
                continue

            if birthday_dt.month != today.month or birthday_dt.day != today.day:
                continue

            if user.get("last_birthday_wish_year") == current_year:
                continue

            send_birthday_email(to_email=email, first_name=first_name)
            db.collection("users").document(uid).set(
                {"last_birthday_wish_year": current_year}, merge=True
            )
            sent_count += 1

        logger.info(f"Birthday job complete — {sent_count} email(s) sent.")
    except Exception as e:
        logger.error(f"Birthday job failed: {e}")


# ─────────────────────────────────────────────
# JOB 2: Re-engagement Emails (daily at 10:00 UTC)
# ─────────────────────────────────────────────
def run_reengagement_job() -> None:
    """
    Daily cron job: find users who have not logged any habit in the last 5 days
    and haven't received a re-engagement email in the last 7 days.
    """
    from app.db.database import get_db

    logger.info("Running daily re-engagement email job...")
    now = datetime.utcnow()
    five_days_ago = now - timedelta(days=5)
    seven_days_ago = now - timedelta(days=7)

    try:
        db = get_db()
        sent_count = 0

        for doc in db.collection("users").stream():
            user = doc.to_dict()
            uid = doc.id
            email = user.get("email")
            first_name = (user.get("full_name", "") or "").split()[0] or "there"

            if not email:
                continue

            # Skip if we already sent a re-engagement email in the last 7 days
            last_sent_raw = user.get("last_reengagement_sent_at")
            if last_sent_raw:
                try:
                    last_sent = datetime.fromisoformat(last_sent_raw) if isinstance(last_sent_raw, str) else last_sent_raw
                    if last_sent > seven_days_ago:
                        continue
                except (ValueError, TypeError):
                    pass

            # Check if they have any habit logs in the last 5 days
            try:
                recent_logs = (
                    db.collection("users").document(uid).collection("habit_logs")
                    .where("created_at", ">=", five_days_ago.isoformat())
                    .limit(1)
                    .get()
                )
                if recent_logs:
                    continue  # They've been active, skip them
            except Exception:
                # If habit_logs query fails, skip this user safely
                continue

            send_reengagement_email(to_email=email, first_name=first_name)
            db.collection("users").document(uid).set(
                {"last_reengagement_sent_at": now.isoformat()}, merge=True
            )
            sent_count += 1

        logger.info(f"Re-engagement job complete — {sent_count} email(s) sent.")
    except Exception as e:
        logger.error(f"Re-engagement job failed: {e}")


def start_scheduler() -> None:
    """Start the APScheduler background scheduler. Called from FastAPI lifespan."""
    scheduler.add_job(
        run_birthday_job,
        trigger=CronTrigger(hour=9, minute=0),
        id="birthday_email_job",
        replace_existing=True,
    )
    scheduler.add_job(
        run_reengagement_job,
        trigger=CronTrigger(hour=10, minute=0),
        id="reengagement_email_job",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("APScheduler started — birthday job at 09:00 UTC, re-engagement job at 10:00 UTC.")


def stop_scheduler() -> None:
    """Gracefully stop the scheduler on app shutdown."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("APScheduler stopped.")
