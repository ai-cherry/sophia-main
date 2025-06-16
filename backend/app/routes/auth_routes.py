"""
Simple Authentication Routes for Pay Ready
Single user authentication system - simplified for owner-only access
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from datetime import datetime, timedelta
import os
import logging

auth_bp = Blueprint('auth', __name__)
logger = logging.getLogger(__name__)

# Simple single-user credentials (can be set via environment variables)
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'payready2024')
ADMIN_API_KEY = os.environ.get('ADMIN_API_KEY', 'pr_sophia_2024_secure')

@auth_bp.route('/login', methods=['POST'])
def login():
    """Simple login for Pay Ready owner"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        api_key = data.get('api_key')
        
        # Check credentials (username/password OR api_key)
        if api_key and api_key == ADMIN_API_KEY:
            # API key authentication
            access_token = create_access_token(
                identity='payready_owner',
                expires_delta=timedelta(days=30)  # Long-lived for convenience
            )
            
            return jsonify({
                "access_token": access_token,
                "user": {
                    "id": "payready_owner",
                    "username": "Pay Ready Owner",
                    "role": "admin",
                    "company": "Pay Ready",
                    "permissions": ["all"]
                },
                "expires_in": 30 * 24 * 60 * 60,  # 30 days in seconds
                "auth_method": "api_key"
            })
            
        elif username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            # Username/password authentication
            access_token = create_access_token(
                identity='payready_owner',
                expires_delta=timedelta(days=7)  # 7 days for username/password
            )
            
            return jsonify({
                "access_token": access_token,
                "user": {
                    "id": "payready_owner", 
                    "username": username,
                    "role": "admin",
                    "company": "Pay Ready",
                    "permissions": ["all"]
                },
                "expires_in": 7 * 24 * 60 * 60,  # 7 days in seconds
                "auth_method": "credentials"
            })
        else:
            return jsonify({
                "error": "Invalid credentials",
                "message": "Please check your username/password or API key"
            }), 401
            
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({
            "error": "Login failed",
            "message": "An error occurred during authentication"
        }), 500

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get current user profile"""
    try:
        current_user = get_jwt_identity()
        
        profile = {
            "id": current_user,
            "username": "Pay Ready Owner",
            "role": "admin",
            "company": "Pay Ready",
            "permissions": ["all"],
            "last_login": datetime.utcnow().isoformat(),
            "access_level": "full",
            "features": [
                "Company Performance Dashboard",
                "Strategic Planning Tools",
                "Operational Intelligence",
                "Market Research & Analysis",
                "AI-Powered Insights"
            ]
        }
        
        return jsonify(profile)
        
    except Exception as e:
        logger.error(f"Profile error: {str(e)}")
        return jsonify({
            "error": "Failed to get profile",
            "message": str(e)
        }), 500

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required()
def refresh_token():
    """Refresh access token"""
    try:
        current_user = get_jwt_identity()
        
        new_token = create_access_token(
            identity=current_user,
            expires_delta=timedelta(days=7)
        )
        
        return jsonify({
            "access_token": new_token,
            "expires_in": 7 * 24 * 60 * 60,
            "refreshed_at": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        return jsonify({
            "error": "Failed to refresh token",
            "message": str(e)
        }), 500

@auth_bp.route('/validate', methods=['GET'])
@jwt_required()
def validate_token():
    """Validate current token"""
    try:
        current_user = get_jwt_identity()
        
        return jsonify({
            "valid": True,
            "user": current_user,
            "timestamp": datetime.utcnow().isoformat(),
            "message": "Token is valid"
        })
        
    except Exception as e:
        logger.error(f"Token validation error: {str(e)}")
        return jsonify({
            "valid": False,
            "error": "Token validation failed",
            "message": str(e)
        }), 401

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """Simple logout (client-side token removal)"""
    try:
        current_user = get_jwt_identity()
        
        return jsonify({
            "message": "Logged out successfully",
            "user": current_user,
            "timestamp": datetime.utcnow().isoformat(),
            "note": "Please remove the access token from client storage"
        })
        
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        return jsonify({
            "error": "Logout failed",
            "message": str(e)
        }), 500

