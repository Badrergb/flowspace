from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, UUID4
from app.db.database import get_db
from app.models.user import User
from app.models.device import Device
from app.api.deps import get_current_user
import uuid

router = APIRouter()

class PushTokenUpdate(BaseModel):
    device_id: UUID4
    push_token: str

@router.post("/push-token")
def update_push_token(
    payload: PushTokenUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Register or update a device's push notification token (FCM/APNs).
    """
    device = db.query(Device).filter(
        Device.id == payload.device_id,
        Device.user_id == current_user.id
    ).first()
    
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
        
    device.push_token = payload.push_token
    # Also update fcm_token for backward compatibility if it exists
    if hasattr(device, 'fcm_token'):
        device.fcm_token = payload.push_token
        
    db.commit()
    return {"status": "success"}
