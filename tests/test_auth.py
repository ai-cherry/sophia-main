"""
Sophia AI - Authentication Tests
Test suite for authentication functionality

This module tests the authentication endpoints and security features.
"""

import pytest
import json
from datetime import datetime


from backend.app.main import app
from backend.config.settings import settings


@pytest.fixture
def client():
    """Create test client"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def auth_headers(client):
    """Get authentication headers"""
    response = client.post('/api/auth/login', json={
        'username': settings.security.admin_username,
        'password': settings.security.admin_password
    })
    data = json.loads(response.data)
    return {
        'Authorization': f"Bearer {data['access_token']}"
    }


class TestAuthentication:
    """Test authentication endpoints"""
    
    def test_login_success(self, client):
        """Test successful login"""
        response = client.post('/api/auth/login', json={
            'username': settings.security.admin_username,
            'password': settings.security.admin_password
        })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'access_token' in data
        assert 'refresh_token' in data
        assert data['user']['username'] == settings.security.admin_username
    
    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials"""
        response = client.post('/api/auth/login', json={
            'username': 'invalid',
            'password': 'wrong'
        })
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_login_missing_fields(self, client):
        """Test login with missing fields"""
        response = client.post('/api/auth/login', json={
            'username': settings.security.admin_username
        })
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_protected_endpoint_without_token(self, client):
        """Test accessing protected endpoint without token"""
        response = client.get('/api/auth/validate')
        
        assert response.status_code == 401
    
    def test_protected_endpoint_with_token(self, client, auth_headers):
        """Test accessing protected endpoint with valid token"""
        response = client.get('/api/auth/validate', headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['valid'] is True
    
    def test_token_refresh(self, client):
        """Test token refresh"""
        # First login
        login_response = client.post('/api/auth/login', json={
            'username': settings.security.admin_username,
            'password': settings.security.admin_password
        })
        login_data = json.loads(login_response.data)
        
        # Refresh token
        refresh_response = client.post('/api/auth/refresh', headers={
            'Authorization': f"Bearer {login_data['refresh_token']}"
        })
        
        assert refresh_response.status_code == 200
        refresh_data = json.loads(refresh_response.data)
        assert 'access_token' in refresh_data
    
    def test_logout(self, client, auth_headers):
        """Test logout"""
        response = client.post('/api/auth/logout', headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'message' in data
    
    def test_get_permissions(self, client, auth_headers):
        """Test getting user permissions"""
        response = client.get('/api/auth/permissions', headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'permissions' in data
        assert isinstance(data['permissions'], list)
        assert data['role'] == 'admin'
    
    def test_api_keys_list(self, client, auth_headers):
        """Test listing API keys"""
        response = client.get('/api/auth/api-keys', headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'api_keys' in data
        assert isinstance(data['api_keys'], list)


class TestSecurity:
    """Test security features"""
    
    def test_jwt_required_decorator(self, client):
        """Test JWT required decorator"""
        endpoints = [
            '/api/auth/validate',
            '/api/auth/permissions',
            '/api/company/overview',
            '/api/strategy/growth-opportunities'
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 401
    
    def test_cors_headers(self, client):
        """Test CORS headers"""
        response = client.options('/api/auth/login')
        
        # Check if CORS headers are present
        assert 'Access-Control-Allow-Origin' in response.headers
    
    def test_rate_limiting(self, client):
        """Test rate limiting (if implemented)"""
        # Make multiple rapid requests
        responses = []
        for _ in range(10):
            response = client.post('/api/auth/login', json={
                'username': 'test',
                'password': 'test'
            })
            responses.append(response.status_code)
        
        # Check if any were rate limited (429)
        # This depends on rate limiting implementation
        assert all(status in [401, 429] for status in responses)


if __name__ == '__main__':
    pytest.main([__file__]) 