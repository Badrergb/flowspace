import logging
from datetime import date, datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.services.email_service import send_birthday_email

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler(timezone="UTC")


def run_birthday_job() -> None:
    """
    Daily cron job: find all users whose birthday is today and
    who haven't received a wish this year, then send them a birthday email.
    """
    # Import here to avoid circular imports at module load time
    from app.db.database import get_db

    logger.info("Running daily birthday email job...")

    today = date.today()
    today_month = today.month
    today_day = today.day
    current_year = today.year

    try:
        db = get_db()

        # Stream all users — Firestore doesn't support month/day queries natively
        # so we filter in Python. For large user bases, store birthday_month and
        # birthday_day as separate integer fields and query those instead.
        users_ref = db.collection("users").stream()

        sent_count = 0
        for doc in users_ref:
            user = doc.to_dict()
            uid = doc.id
            email = user.get("email")
            birthday_raw = user.get("birthday")
            full_name = user.get("full_name", "")
            first_name = full_name.split()[0] if full_name else "there"

            if not email or not birthday_raw:
                continue

            # Parse birthday — stored as ISO string e.g. "1999-05-14T00:00:00"
            try:
                if isinstance(birthday_raw, str):
                    birthday_dt = datetime.fromisoformat(birthday_raw)
                elif hasattr(birthday_raw, "month"):
                    birthday_dt = birthday_raw
                else:
                    continue
            except (ValueError, TypeError):
                continue

            # Check if today is their birthday
            if birthday_dt.month != today_month or birthday_dt.day != today_day:
                continue

            # Check we haven't already sent this year
            last_wish_year = user.get("last_birthday_wish_year")
            if last_wish_year == current_year:
                logger.info(f"Skipping {email} — birthday wish already sent in {current_year}")
                continue

            # Send the email
            send_birthday_email(to_email=email, first_name=first_name)

            # Mark the year so we don't send again
            db.collection("users").document(uid).set(
                {"last_birthday_wish_year": current_year},
                merge=True
            )
            sent_count += 1

        logger.info(f"Birthday job complete — {sent_count} email(s) sent.")

    except Exception as e:
        logger.error(f"Birthday job failed: {e}")


def start_scheduler() -> None:
    """Start the APScheduler background scheduler. Call from FastAPI lifespan."""
    # Run every day at 09:00 UTC
    scheduler.add_job(
        run_birthday_job,
        trigger=CronTrigger(hour=9, minute=0),
        id="birthday_email_job",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("APScheduler started — birthday job scheduled at 09:00 UTC daily.")


def stop_scheduler() -> None:
    """Gracefully stop the scheduler on app shutdown."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("APScheduler stopped.")
