import pytest
import uuid
from app.models.reviews import Review
from unittest.mock import patch
from app.core.config import settings

def test_create_review_success(client, test_db):
    response = client.post(
        "/api/v1/reviews",
        data={
            "name": "Alice",
            "rating": 5,
            "review_text": "Amazing!"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Alice"
    assert data["rating"] == 5
    assert data["review_text"] == "Amazing!"
    assert "id" in data
    assert "is_approved" not in data  # Ensure moderation flag is not leaked in response
    
    # Verify in DB
    review_id = uuid.UUID(data["id"])
    db_review = test_db.query(Review).filter(Review.id == review_id).first()
    assert db_review is not None
    assert db_review.is_approved is False

@patch('app.api.v1.reviews.upload_file_to_supabase')
def test_create_review_with_avatar(mock_upload, client, test_db):
    # Mock the Supabase upload to just return a constructed public URL we expect
    mock_upload.return_value = "https://mock.supabase.co/storage/v1/object/public/flowspace-media/reviews/avatars/mocked-uuid.png"
    
    # Send a file to test the avatar upload logic
    response = client.post(
        "/api/v1/reviews",
        data={
            "name": "Eve",
            "rating": 4,
            "review_text": "Good stuff with avatar!"
        },
        files={"avatar": ("avatar.png", b"fake image content", "image/png")}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Eve"
    assert data["avatar_url"] == "https://mock.supabase.co/storage/v1/object/public/flowspace-media/reviews/avatars/mocked-uuid.png"
    
    # Ensure the mock was actually called
    mock_upload.assert_called_once()
    
    # Verify DB
    review_id = uuid.UUID(data["id"])
    db_review = test_db.query(Review).filter(Review.id == review_id).first()
    assert db_review.avatar_url == data["avatar_url"]

def test_create_review_invalid_rating(client):
    response = client.post(
        "/api/v1/reviews",
        data={
            "name": "Bob",
            "rating": 6,
            "review_text": "Way too good!"
        }
    )
    # The endpoint raises HTTP 400 or 422 if we rely on FastAPI validators
    # We did a manual check that raises 400
    assert response.status_code == 400

def test_get_reviews_hides_unapproved(client, test_db):
    # Create an unapproved review
    unapproved_id = uuid.uuid4()
    r1 = Review(id=unapproved_id, name="Charlie", rating=4, review_text="Good", is_approved=False)
    
    # Create an approved review
    approved_id = uuid.uuid4()
    r2 = Review(id=approved_id, name="Dave", rating=5, review_text="Great", is_approved=True)
    
    test_db.add(r1)
    test_db.add(r2)
    test_db.commit()
    
    response = client.get("/api/v1/reviews")
    assert response.status_code == 200
    data = response.json()
    
    ids = [r["id"] for r in data]
    assert str(approved_id) in ids
    assert str(unapproved_id) not in ids

def test_get_reviews_pagination(client, test_db):
    # Insert multiple approved reviews
    for i in range(15):
        test_db.add(Review(id=uuid.uuid4(), name=f"User {i}", rating=5, review_text="Nice", is_approved=True))
    test_db.commit()
    
    # Test limit
    res1 = client.get("/api/v1/reviews?skip=0&limit=10")
    assert res1.status_code == 200
    assert len(res1.json()) == 10
    
    # Test skip
    res2 = client.get("/api/v1/reviews?skip=10&limit=10")
    assert res2.status_code == 200
    assert len(res2.json()) >= 5  # At least the remaining 5 from our insert
