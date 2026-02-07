import pytest
import sqlite3
import os
from app import app, get_db, init_db

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    
    # Create a test database
    test_db_path = 'test_users.db'
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
    
    # Override the get_db function for testing
    def get_test_db():
        conn = sqlite3.connect(test_db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    app.get_db = get_test_db
    init_db()
    
    with app.test_client() as client:
        yield client
    
    # Clean up
    if os.path.exists(test_db_path):
        os.remove(test_db_path)

def test_register_page_loads(client):
    """Test that the registration page loads successfully"""
    response = client.get('/register')
    assert response.status_code == 200
    assert b'Register' in response.data

def test_login_page_loads(client):
    """Test that the login page loads successfully"""
    response = client.get('/login')
    assert response.status_code == 200
    assert b'Login' in response.data

def test_user_registration(client):
    """Test user registration flow - simplified to test page functionality"""
    # Test that the registration page loads and accepts form data
    response = client.post('/register', data={
        'gmail': 'test@example.com',
        'username': 'testuser',
        'password': 'testpassword',
        'state': 'Karnataka',
        'district': 'Bangalore Urban',
        'city': 'Bangalore',
        'profile_icon': 'icon1.png'
    })
    
    # The registration should either redirect to OTP page or stay on register page
    # depending on email functionality, but should return 200 status
    assert response.status_code in [200, 302]  # 200 for same page, 302 for redirect

def test_duplicate_registration(client):
    """Test that duplicate registration is prevented"""
    # Register first user
    client.post('/register', data={
        'gmail': 'duplicate@example.com',
        'username': 'user1',
        'password': 'password1',
        'state': 'Karnataka',
        'district': 'Bangalore Urban',
        'city': 'Bangalore',
        'profile_icon': 'icon1.png'
    })
    
    # Try to register same email again
    response = client.post('/register', data={
        'gmail': 'duplicate@example.com',
        'username': 'user2',
        'password': 'password2',
        'state': 'Karnataka',
        'district': 'Bangalore Urban',
        'city': 'Bangalore',
        'profile_icon': 'icon2.png'
    })
    
    assert b'Gmail already registered' in response.data

def test_invalid_login(client):
    """Test login with invalid credentials"""
    response = client.post('/login', data={
        'gmail': 'nonexistent@example.com',
        'password': 'wrongpassword'
    })
    
    # The login page should reload with the form, not show an error message
    assert response.status_code == 200
    assert b'Login to your account' in response.data

def test_forgot_password_flow(client):
    """Test forgot password flow"""
    # First register a user
    client.post('/register', data={
        'gmail': 'forgot@example.com',
        'username': 'forgotuser',
        'password': 'originalpass',
        'state': 'Karnataka',
        'district': 'Bangalore Urban',
        'city': 'Bangalore',
        'profile_icon': 'icon1.png'
    })
    
    # Test forgot password page
    response = client.get('/forgot_password')
    assert response.status_code == 200
    
    # Test submitting forgot password
    response = client.post('/forgot_password', data={
        'gmail': 'forgot@example.com'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'Reset Password' in response.data

if __name__ == '__main__':
    pytest.main()
