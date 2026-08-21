import logging
import uuid
from sqlalchemy.orm import Session
from app.models.device import Device

logger = logging.getLogger(__name__)

def send_push_notification(db: Session, user_id: uuid.UUID, title: str, body: str, data: dict = None):
    """
    Sends a push notification to all active devices of the user.
    This is a stub implementation until real FCM/APNs certificates are provided.
    """
    devices = db.query(Device).filter(
        Device.user_id == user_id,
        Device.push_token.isnot(None)
    ).all()
    
    if not devices:
        logger.info(f"No active push tokens found for user {user_id}")
        return False
        
    for device in devices:
        # TODO: Integrate with firebase_admin.messaging (FCM) or PyAPNs here
        logger.info(f"STUB: Sending push notification to {device.id} ({device.device_name})")
        logger.info(f"  Token: {device.push_token}")
        logger.info(f"  Title: {title}")
        logger.info(f"  Body: {body}")
        if data:
            logger.info(f"  Data: {data}")
            
    return True
