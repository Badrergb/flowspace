import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings

logger = logging.getLogger(__name__)

MILESTONE_STREAKS = {7, 14, 21, 30, 60, 90, 180, 365}


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

        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(settings.SMTP_EMAIL, settings.SMTP_PASSWORD)
        server.sendmail(settings.SMTP_EMAIL, to_email, msg.as_string())
        server.quit()

    except Exception as e:
        logger.error(f"Failed to send email to {to_email} via SMTP: {e}")
        raise


# ─────────────────────────────────────────────
# 1. WELCOME EMAIL
# ─────────────────────────────────────────────
def send_welcome_email(to_email: str, first_name: str) -> None:
    """Send a welcome email to a newly registered user."""
    html_body = f"""
    <div style="font-family: sans-serif; color: #333; line-height: 1.8; max-width: 600px; margin: auto;">
        <h2 style="color: #6C3CE1;">Hey {first_name}, welcome to FlowSpace! 🎉</h2>
        <p>Oh wow, we are SO glad you are here! You just made one of the best decisions for yourself — and we genuinely mean that. 💜</p>
        <p>You've just taken your very first step toward building better habits, crushing your goals, and becoming the best version of yourself. And we are going to be right here cheering you on every single step of the way!</p>
        <p><strong>Here is what you can do in FlowSpace:</strong></p>
        <ul style="line-height: 2.2;">
          <li>🔥 Track daily habits and build powerful streaks</li>
          <li>💰 Monitor your finances and take control</li>
          <li>💪 Log your gym workouts and see real progress</li>
          <li>👫 Connect with accountability partners who push you forward</li>
        </ul>
        <p><strong>Quick tip:</strong> The best way to start is to log your very first habit today — even something tiny like drinking a glass of water counts! Momentum builds incredibly fast once you take that first step.</p>
        <p style="background: #f5f0ff; padding: 14px; border-radius: 8px; border-left: 4px solid #6C3CE1;">
            💬 <strong>Got any questions, feedback, or just want to say hello?</strong><br>
            Please feel free to reply directly to this email — we are real people on the other side and we would absolutely <em>love</em> to hear from you. No bots, no automated replies. Just us! 😊
        </p>
        <p>Let's make every single day count. You've got this! 🚀</p>
        <p>With so much love and excitement,<br><strong>– The FlowSpace Team 💜</strong></p>
    </div>
    """
    try:
        _send_email_smtp(
            to_email=to_email,
            subject=f"Welcome to FlowSpace, {first_name}! 🎉 We're so glad you're here",
            html_content=html_body,
        )
        logger.info(f"Welcome email sent to {to_email}")
    except Exception as e:
        logger.error(f"Failed to send welcome email to {to_email}: {e}")


# ─────────────────────────────────────────────
# 2. BIRTHDAY EMAIL
# ─────────────────────────────────────────────
def send_birthday_email(to_email: str, first_name: str) -> None:
    """Send a happy birthday email to a user."""
    html_body = f"""
    <div style="font-family: sans-serif; color: #333; line-height: 1.8; max-width: 600px; margin: auto;">
        <h2 style="color: #6C3CE1;">🎂 Happy Birthday, {first_name}! 🎉</h2>
        <p>Hey {first_name},</p>
        <p>The <strong>entire FlowSpace team</strong> wanted to stop everything we were doing today just to say — <strong>HAPPY BIRTHDAY!</strong> 🥳🎊</p>
        <p>We hope today is filled with so much joy, laughter, amazing food, and people who make you feel how truly special you are. You deserve an absolutely incredible day!</p>
        <p>Whether you're celebrating big or keeping it cozy and low-key today, just know that we are sending you so many warm wishes from our side of the screen. You have spent the past year showing up for yourself and building something amazing — and that is genuinely worth celebrating. 🌟</p>
        <p>Take today off from the grind if you need it. You've absolutely earned it. Come back tomorrow even stronger! 💪</p>
        <p>Here's to an even more wonderful, growth-filled, and happy new year of life ahead of you!</p>
        <p style="background: #f5f0ff; padding: 14px; border-radius: 8px; border-left: 4px solid #6C3CE1;">
            💬 <strong>Got a birthday wish to share, some feedback, or just want to say hi?</strong><br>
            Hit reply on this email — we genuinely read every single message and would love to hear from you on your special day! 😊
        </p>
        <p>With so much love,<br><strong>– The FlowSpace Team 💜</strong></p>
    </div>
    """
    try:
        _send_email_smtp(
            to_email=to_email,
            subject=f"🎂 Happy Birthday, {first_name}! The whole team is celebrating you today!",
            html_content=html_body,
        )
        logger.info(f"Birthday email sent to {to_email}")
    except Exception as e:
        logger.error(f"Failed to send birthday email to {to_email}: {e}")


# ─────────────────────────────────────────────
# 3. STREAK MILESTONE EMAIL
# ─────────────────────────────────────────────
def send_streak_milestone_email(to_email: str, first_name: str, streak: int) -> None:
    """Send a celebration email when a user hits a habit streak milestone."""
    html_body = f"""
    <div style="font-family: sans-serif; color: #333; line-height: 1.8; max-width: 600px; margin: auto;">
        <h2 style="color: #6C3CE1;">🔥 {streak} Days Strong, {first_name}! WOW!</h2>
        <p>Hey {first_name},</p>
        <p>We just saw your streak hit <strong>{streak} days</strong> and we had to stop what we were doing to say: <strong>INCREDIBLE! 🎉</strong></p>
        <p>Do you realize what you just did? You showed up for yourself <strong>{streak} days in a row.</strong> That takes serious dedication, discipline, and a whole lot of heart. You should be SO proud of yourself right now — because we certainly are! 💜</p>
        <p>Most people give up before they ever get here. But not you. You kept going even on the days when it felt hard, even when you didn't feel like it — and that is exactly what separates people who dream from people who actually <em>do</em>. You are the latter. ✨</p>
        <p>Keep that incredible energy going today! Remember — even on your busiest days, showing up for just 1% is a massive win. You've got this!</p>
        <p style="background: #f5f0ff; padding: 14px; border-radius: 8px; border-left: 4px solid #6C3CE1;">
            💬 <strong>We'd love to hear from you!</strong><br>
            Please feel free to reply to this email and tell us which habit you're most proud of keeping up — or just share how you're feeling. We read every single message and absolutely love hearing our users' stories! 😊
        </p>
        <p>Keep crushing it. We are rooting for you every single day! 🚀</p>
        <p>With so much pride and love,<br><strong>– The FlowSpace Team 💜</strong></p>
    </div>
    """
    try:
        _send_email_smtp(
            to_email=to_email,
            subject=f"🔥 {streak} Days Strong, {first_name}! You are absolutely crushing it!",
            html_content=html_body,
        )
        logger.info(f"Streak milestone ({streak}d) email sent to {to_email}")
    except Exception as e:
        logger.error(f"Failed to send streak email to {to_email}: {e}")


# ─────────────────────────────────────────────
# 4. RE-ENGAGEMENT EMAIL
# ─────────────────────────────────────────────
def send_reengagement_email(to_email: str, first_name: str) -> None:
    """Send a warm re-engagement email after 5 days of inactivity."""
    html_body = f"""
    <div style="font-family: sans-serif; color: #333; line-height: 1.8; max-width: 600px; margin: auto;">
        <h2 style="color: #6C3CE1;">Hey {first_name}, we've been thinking about you! 🌟</h2>
        <p>Hey {first_name},</p>
        <p>Sending you the warmest of greetings from the FlowSpace team! ☀️</p>
        <p>We noticed it's been a little while since you last logged a habit in the app, and we just wanted to drop in — not to pressure you, but simply to say: <strong>we are thinking about you, and we genuinely hope you're doing well!</strong> 💜</p>
        <p>Life gets busy. Schedules break. Sometimes we just need a rest. And that is <em>completely okay</em>. Please don't be hard on yourself about it — every single one of us has been there.</p>
        <p>The beautiful thing about building habits is that <strong>every day is a fresh new opportunity to start again.</strong> Yesterday doesn't matter. Tomorrow isn't here yet. All that matters is what you do today — and even the tiniest action counts.</p>
        <p>Whenever you feel ready, we will be right here waiting for you. Just open FlowSpace and check off one small thing today. Even something tiny. That's all it takes to get the momentum flowing again — and you will feel so much better for it! ✨</p>
        <p style="background: #f5f0ff; padding: 14px; border-radius: 8px; border-left: 4px solid #6C3CE1;">
            💬 <strong>Is there something in the app that's confusing or not working for you?</strong><br>
            Please feel totally free to contact us by replying directly to this email! We are real people sitting on the other side of the screen, and we genuinely want to help you succeed. No question is too small. We'd love to hear from you! 😊
        </p>
        <p>We believe in you 100%. Have a wonderful, beautiful day — and remember, we are always cheering you on! 🎉</p>
        <p>Warmly,<br><strong>– The FlowSpace Team 💜</strong></p>
    </div>
    """
    try:
        _send_email_smtp(
            to_email=to_email,
            subject=f"Hey {first_name}, we've been thinking about you! 🌟",
            html_content=html_body,
        )
        logger.info(f"Re-engagement email sent to {to_email}")
    except Exception as e:
        logger.error(f"Failed to send re-engagement email to {to_email}: {e}")
