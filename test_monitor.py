import os
import json
from google.oauth2 import service_account
from google.cloud import monitoring_v3
from app.core.config import settings

def test_monitoring():
    raw_json = settings.FIREBASE_CREDENTIALS_JSON
    if raw_json.startswith("'") and raw_json.endswith("'"):
        raw_json = raw_json[1:-1]
    cred_dict = json.loads(raw_json)
    if 'private_key' in cred_dict:
        cred_dict['private_key'] = cred_dict['private_key'].replace('\\n', '\n')
        
    project_id = cred_dict.get('project_id')
    creds = service_account.Credentials.from_service_account_info(cred_dict)
    client = monitoring_v3.MetricServiceClient(credentials=creds)
    project_name = f"projects/{project_id}"
    
    print("Testing Monitoring API...")
    try:
        # Just list some metric descriptors to see if we have access
        results = client.list_metric_descriptors(name=project_name)
        count = 0
        for r in results:
            count += 1
            if count > 5:
                break
        print(f"Successfully accessed monitoring API! Found metrics.")
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    test_monitoring()
