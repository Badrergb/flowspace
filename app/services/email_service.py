import logging
import smtplib
import html
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings

logger = logging.getLogger(__name__)

MILESTONE_STREAKS = {7, 14, 21, 30, 60, 90, 180, 365}


def _send_email_smtp(to_email: str, subject: str, text_content: str) -> None:
    """Helper to send an email using Gmail SMTP in plain text to avoid spam filters."""
    if not settings.SMTP_EMAIL or not settings.SMTP_PASSWORD:
        logger.warning("SMTP_EMAIL or SMTP_PASSWORD is not set - emails will not be sent.")
        return

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"FlowSpace <{settings.SMTP_EMAIL}>"
        msg["To"] = to_email

        part = MIMEText(text_content, "plain")
        msg.attach(part)

        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(settings.SMTP_EMAIL, settings.SMTP_PASSWORD)
        server.sendmail(settings.SMTP_EMAIL, to_email, msg.as_string())
        server.quit()

    except Exception as e:
        logger.error(f"Failed to send email to {to_email} via SMTP: {e}")
        raise


def send_welcome_email(to_email: str, first_name: str) -> None:
    """Send a plain-text welcome email to avoid spam."""
    text_body = f"""Hi {first_name},

Welcome to FlowSpace! I am so glad you joined us.

You have just taken the first step toward building better habits and organizing your productivity. 

Here is what you can do in FlowSpace:
- Track your habits and maintain daily streaks
- Organize your schedule and tasks
- Keep track of your finances

If you ever have any questions or feedback, just reply directly to this email. I read every single message.

(Important: To make sure you receive your streak reminders, please add this email address to your contacts or move it to your primary inbox).

Best,
The FlowSpace Team
"""
    try:
        _send_email_smtp(
            to_email=to_email,
            subject=f"Welcome to FlowSpace, {first_name}!",
            text_content=text_body,
        )
        logger.info(f"Welcome email sent to {to_email}")
    except Exception as e:
        logger.error(f"Failed to send welcome email: {e}")


def send_birthday_email(to_email: str, first_name: str) -> None:
    text_body = f"""Hi {first_name},

Happy Birthday! 

We noticed it is your special day and wanted to send our warmest wishes. Thank you for using FlowSpace to build your habits over the past year. Take today off to celebrate yourself!

If you have a birthday wish to share, just reply to this email.

Best,
The FlowSpace Team
"""
    try:
        _send_email_smtp(
            to_email=to_email,
            subject=f"Happy Birthday, {first_name}!",
            text_content=text_body,
        )
    except Exception as e:
        pass


def send_streak_milestone_email(to_email: str, first_name: str, streak: int) -> None:
    text_body = f"""Hi {first_name},

You just hit a {streak} day streak in FlowSpace! 

That is an incredible milestone. Most people give up early, but you showed up for {streak} days in a row. 

Keep up the great momentum today. If you want to share which habit you are most proud of, feel free to reply to this email.

Best,
The FlowSpace Team
"""
    try:
        _send_email_smtp(
            to_email=to_email,
            subject=f"Incredible: {streak} day streak, {first_name}!",
            text_content=text_body,
        )
    except Exception as e:
        pass


def send_reengagement_email(to_email: str, first_name: str) -> None:
    text_body = f"""Hi {first_name},

We noticed it has been a few days since you last logged a habit in FlowSpace. 

Life gets busy and schedules break, and that is completely fine. Whenever you are ready to jump back in, your habits are waiting for you. Every day is a fresh opportunity to start again.

If you have any questions or need help, just reply to this email. 

Best,
The FlowSpace Team
"""
    try:
        _send_email_smtp(
            to_email=to_email,
            subject=f"Checking in on your habits, {first_name}",
            text_content=text_body,
        )
    except Exception as e:
        pass

