def test_register(client):
    # Using a random email to avoid collision if running multiple times
    import uuid
    email = f"test_{uuid.uuid4()}@example.com"
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123", "full_name": "Test User"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == email
    assert "id" in data

    # Test duplicate register
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123", "full_name": "Test User"}
    )
    assert response.status_code == 400

def test_login(client, test_user_and_token):
    user, _, _ = test_user_and_token
    response = client.post(
        "/api/v1/auth/login",
        data={"username": user.email, "password": "testpassword123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"

def test_login_incorrect(client, test_user_and_token):
    user, _, _ = test_user_and_token
    response = client.post(
        "/api/v1/auth/login",
        data={"username": user.email, "password": "wrongpassword"}
    )
    assert response.status_code == 400

def test_refresh_token(client, test_user_and_token):
    user, _, _ = test_user_and_token
    # First login to get a refresh token
    login_res = client.post(
        "/api/v1/auth/login",
        data={"username": user.email, "password": "testpassword123"}
    )
    refresh_token = login_res.json()["refresh_token"]
    
    # Use refresh token to get a new access token
    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
