import json
import firebase_admin
from firebase_admin import credentials, firestore
from app.core.config import settings

def initialize_firebase():
    if not firebase_admin._apps:
        if settings.FIREBASE_CREDENTIALS_JSON:
            try:
                raw_json = settings.FIREBASE_CREDENTIALS_JSON
                if raw_json.startswith("'") and raw_json.endswith("'"):
                    raw_json = raw_json[1:-1]
                
                cred_dict = json.loads(raw_json)
                if 'private_key' in cred_dict:
                    cred_dict['private_key'] = cred_dict['private_key'].replace('\\n', '\n')
                    
                cred = credentials.Certificate(cred_dict)
                firebase_admin.initialize_app(cred)
            except Exception as e:
                print(f"Failed to initialize Firebase Admin: {e}")
        else:
            print("FIREBASE_CREDENTIALS_JSON is not set.")

initialize_firebase()

def get_db():
    # Return a Firestore client instance
    try:
        db = firestore.client()
        yield db
    except Exception as e:
        print(f"Failed to get Firestore client: {e}")
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=f"Database connection error: {str(e)}")
