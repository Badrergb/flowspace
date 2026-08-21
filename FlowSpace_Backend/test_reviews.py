import asyncio
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.models.reviews import Review

def run_test():
    db: Session = SessionLocal()
    
    # 1. Create review directly or we can just query it.
    # Since the server isn't running, let's just do db operations to verify the logic.
    # Actually, we can test the fastapi client.
    from fastapi.testclient import TestClient
    from app.main import app
    
    client = TestClient(app)
    
    print("Submitting a new review via POST...")
    response = client.post(
        "/api/v1/reviews",
        data={
            "name": "Test User",
            "rating": 5,
            "review_text": "This is a great app!"
        }
    )
    assert response.status_code == 200
    review_data = response.json()
    review_id = review_data["id"]
    print(f"Created review with ID: {review_id}")
    
    print("Checking if it appears in GET (should NOT)...")
    get_res = client.get("/api/v1/reviews")
    assert get_res.status_code == 200
    reviews = get_res.json()
    found = any(r["id"] == review_id for r in reviews)
    print(f"Appears in GET: {found}")
    assert not found
    
    print("Manually approving in database...")
    db_review = db.query(Review).filter(Review.id == review_id).first()
    db_review.is_approved = True
    db.commit()
    
    print("Checking if it appears in GET now (should YES)...")
    get_res = client.get("/api/v1/reviews")
    assert get_res.status_code == 200
    reviews = get_res.json()
    found = any(r["id"] == review_id for r in reviews)
    print(f"Appears in GET: {found}")
    assert found
    
    print("Test passed successfully!")

if __name__ == "__main__":
    run_test()
