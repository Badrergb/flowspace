import logging

logger = logging.getLogger(__name__)


def send_push_notification(push_token: str, title: str, body: str, data: dict = None):
    """
    Sends a push notification to a device via FCM using firebase-admin.
    """
    try:
        from firebase_admin import messaging
        message = messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            data=data or {},
            token=push_token,
        )
        response = messaging.send(message)
        logger.info(f"Push notification sent: {response}")
        return response
    except Exception as e:
        logger.error(f"Failed to send push notification: {e}")
        return None
