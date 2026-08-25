import logging
import resend
from app.core.config import settings

logger = logging.getLogger(__name__)


def _get_resend_client() -> bool:
    """Configure the Resend client. Returns True if API key is set."""
    if not settings.RESEND_API_KEY:
        logger.warning("RESEND_API_KEY is not set — emails will not be sent.")
        return False
    resend.api_key = settings.RESEND_API_KEY
    return True


def send_welcome_email(to_email: str, first_name: str) -> None:
    """Send a welcome email to a newly registered user."""
    if not _get_resend_client():
        return

    html_body = f"""
    <h2>Hey {first_name}, welcome aboard! 🎉</h2>
    <p>We're so excited to have you join FlowSpace. You've just taken the first step towards
    building better habits, crushing your goals, and becoming the best version of yourself.</p>
    <p>Here's what you can do in the app:</p>
    <ul>
      <li>🔥 Track daily habits and build streaks</li>
      <li>💰 Monitor your finances</li>
      <li>💪 Log your gym workouts</li>
      <li>👫 Connect with accountability partners</li>
    </ul>
    <p>Let's make every day count!</p>
    <br/>
    <p>– The FlowSpace Team</p>
    """

    try:
        resend.Emails.send({
            "from": settings.EMAIL_SENDER,
            "to": [to_email],
            "subject": f"Welcome to FlowSpace, {first_name}! 🚀",
            "html": html_body,
        })
        logger.info(f"Welcome email sent to {to_email}")
    except Exception as e:
        # Never crash registration just because email failed
        logger.error(f"Failed to send welcome email to {to_email}: {e}")


def send_birthday_email(to_email: str, first_name: str) -> None:
    """Send a happy birthday email to a user."""
    if not _get_resend_client():
        return

    html_body = f"""
    <h2>Happy Birthday, {first_name}! 🎂🎉</h2>
    <p>The entire FlowSpace team is wishing you an absolutely amazing birthday!</p>
    <p>Today is YOUR day. Take a break from the grind and celebrate how far you've come.
    You deserve it. 🥳</p>
    <p>Here's to building even more great habits in your new year of life!</p>
    <br/>
    <p>With love,</p>
    <p>– The FlowSpace Team 💜</p>
    """

    try:
        resend.Emails.send({
            "from": settings.EMAIL_SENDER,
            "to": [to_email],
            "subject": f"Happy Birthday, {first_name}! 🎂",
            "html": html_body,
        })
        logger.info(f"Birthday email sent to {to_email}")
    except Exception as e:
        logger.error(f"Failed to send birthday email to {to_email}: {e}")
