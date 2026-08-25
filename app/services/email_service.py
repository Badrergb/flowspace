import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings

logger = logging.getLogger(__name__)


def _send_email_smtp(to_email: str, subject: str, html_content: str) -> None:
    """Helper to send an email using Gmail SMTP."""
    if not settings.SMTP_EMAIL or not settings.SMTP_PASSWORD:
        logger.warning("SMTP_EMAIL or SMTP_PASSWORD is not set — emails will not be sent.")
        return

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"FlowSpace <{settings.SMTP_EMAIL}>"
        msg["To"] = to_email

        part = MIMEText(html_content, "html")
        msg.attach(part)

        # Connect to Gmail's SMTP server
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(settings.SMTP_EMAIL, settings.SMTP_PASSWORD)
        server.sendmail(settings.SMTP_EMAIL, to_email, msg.as_string())
        server.quit()
        
    except Exception as e:
        logger.error(f"Failed to send email to {to_email} via SMTP: {e}")
        # Re-raise so the calling functions can handle/log it, or just pass if we don't want to break
        raise


def send_welcome_email(to_email: str, first_name: str) -> None:
    """Send a welcome email to a newly registered user."""
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
        _send_email_smtp(
            to_email=to_email,
            subject=f"Welcome to FlowSpace, {first_name}! 🚀",
            html_content=html_body,
        )
        logger.info(f"Welcome email sent to {to_email}")
    except Exception as e:
        # Never crash registration just because email failed
        logger.error(f"Failed to send welcome email to {to_email}: {e}")


def send_birthday_email(to_email: str, first_name: str) -> None:
    """Send a happy birthday email to a user."""
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
        _send_email_smtp(
            to_email=to_email,
            subject=f"Happy Birthday, {first_name}! 🎂",
            html_content=html_body,
        )
        logger.info(f"Birthday email sent to {to_email}")
    except Exception as e:
        logger.error(f"Failed to send birthday email to {to_email}: {e}")
