import os
import json
import csv
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def export_reviews_to_csv():
    # 1. Parse the Firebase credentials from .env
    firebase_creds_str = os.getenv("FIREBASE_CREDENTIALS_JSON")
    if not firebase_creds_str:
        print("Error: FIREBASE_CREDENTIALS_JSON not found in .env")
        return

    try:
        cred_dict = json.loads(firebase_creds_str)
    except json.JSONDecodeError:
        print("Error: Invalid JSON format in FIREBASE_CREDENTIALS_JSON")
        return

    # 2. Initialize Firebase Admin SDK
    if not firebase_admin._apps:
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)
    
    # 3. Connect to Firestore
    db = firestore.client()
    
    # 4. Fetch all reviews from the 'reviews' collection
    print("Fetching reviews from Firestore...")
    reviews_ref = db.collection("reviews")
    docs = reviews_ref.stream()
    
    # 5. Write to CSV (which opens in Excel)
    csv_file_path = "reviews_export.csv"
    
    headers = ["ID", "Name", "Rating", "Review Text", "Approved", "Created At"]
    count = 0
    
    with open(csv_file_path, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(headers)
        
        for doc in docs:
            data = doc.to_dict()
            writer.writerow([
                doc.id,
                data.get("name", ""),
                data.get("rating", ""),
                data.get("review_text", ""),
                data.get("is_approved", False),
                data.get("created_at", "")
            ])
            count += 1
            
    print(f"Successfully exported {count} reviews to {csv_file_path}!")

if __name__ == "__main__":
    export_reviews_to_csv()
