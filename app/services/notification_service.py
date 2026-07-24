import logging
import uuid
from sqlalchemy.orm import Session
from app.models.device import Device
import firebase_admin
from firebase_admin import messaging

logger = logging.getLogger(__name__)

def send_push_notification(db: Session, user_id: uuid.UUID, title: str, body: str, data: dict = None):
    """
    Sends a push notification to all active devices of the user via Firebase Cloud Messaging (FCM).
    """
    devices = db.query(Device).filter(
        Device.user_id == user_id,
        Device.push_token.isnot(None)
    ).all()
    
    if not devices:
        logger.info(f"No active push tokens found for user {user_id}")
        return False
        
    try:
        firebase_admin.get_app()
    except ValueError:
        logger.warning("Firebase Admin is not initialized. Cannot send push notification.")
        return False

    success_count = 0
    for device in devices:
        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                data=data if data else {},
                token=device.push_token,
            )
            response = messaging.send(message)
            logger.info(f"Successfully sent message to {device.id}: {response}")
            success_count += 1
        except messaging.UnregisteredError:
            logger.info(f"Token unregistered for device {device.id}. Removing token.")
            device.push_token = None
            db.commit()
        except Exception as e:
            logger.error(f"Error sending message to {device.id}: {e}")
            
    return success_count > 0
