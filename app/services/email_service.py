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
    <div style="font-family: sans-serif; color: #333; line-height: 1.6;">
        <p>Hey {first_name}, welcome aboard!</p>
        <p>We're so glad you're here. You've just taken the first step toward building better habits, hitting your goals, and becoming the best version of yourself — and we're excited to be part of that journey with you.</p>
        <p>Here's what you can do in FlowSpace:</p>
        <ul>
          <li>🔥 Track daily habits and build streaks</li>
          <li>💰 Monitor your finances</li>
          <li>💪 Log your gym workouts</li>
          <li>👫 Connect with accountability partners</li>
        </ul>
        <p><strong>Quick tip:</strong> the best way to start is to log your very first habit today — even something small. Momentum builds fast once you get going!</p>
        <p>Questions, feedback, or just want to say hello? Reply to this email anytime — we're a real team and we'd genuinely love to hear from you. 💜</p>
        <p>Let's make every day count.<br>– The FlowSpace Team</p>
    </div>
    """

    try:
        _send_email_smtp(
            to_email=to_email,
            subject=f"Welcome to FlowSpace, {first_name}! 🎉",
            html_content=html_body,
        )
        logger.info(f"Welcome email sent to {to_email}")
    except Exception as e:
        # Never crash registration just because email failed
        logger.error(f"Failed to send welcome email to {to_email}: {e}")


def send_birthday_email(to_email: str, first_name: str) -> None:
    """Send a happy birthday email to a user."""
    html_body = f"""
    <div style="font-family: sans-serif; color: #333; line-height: 1.6;">
        <p>Hey {first_name},</p>
        <p>The whole FlowSpace team wanted to stop by and wish you the happiest of birthdays! 🎉</p>
        <p>Whether you're celebrating big or keeping it low-key today, we hope it's a great one. You've spent the past year building habits and showing up for yourself — that's genuinely worth celebrating.</p>
        <p>Take today off from the grind if you need it. You've earned it. 🥳</p>
        <p>Here's to an even better year of growth ahead.</p>
        <p>Got a birthday wish, feedback, or just want to say hi? Hit reply — we actually read these and love hearing from you. 💜</p>
        <p>With love,<br>The FlowSpace Team</p>
    </div>
    """

    try:
        _send_email_smtp(
            to_email=to_email,
            subject=f"🎂 Happy Birthday, {first_name}!",
            html_content=html_body,
        )
        logger.info(f"Birthday email sent to {to_email}")
    except Exception as e:
        logger.error(f"Failed to send birthday email to {to_email}: {e}")

