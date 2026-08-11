import sys
import os
from datetime import datetime, timedelta, timezone

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import SessionLocal
from app.models.user import User

def cleanup_unverified_users():
    """
    Deletes users who are unverified and were created more than 48 hours ago.
    This can be run as a cron job.
    """
    db = SessionLocal()
    try:
        cutoff_date = datetime.now(timezone.utc) - timedelta(hours=48)
        
        # Find all unverified users older than 48 hours
        stale_users = db.query(User).filter(
            User.is_verified == False,
            User.created_at < cutoff_date
        ).all()
        
        count = len(stale_users)
        for user in stale_users:
            db.delete(user)
            
        db.commit()
        print(f"[{datetime.now(timezone.utc).isoformat()}] Cleaned up {count} unverified user(s).")
    except Exception as e:
        print(f"Error during cleanup: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    cleanup_unverified_users()
