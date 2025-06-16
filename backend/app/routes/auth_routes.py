"""
Sophia AI - Authentication Routes
JWT-based authentication for the API

This module provides authentication endpoints for the Sophia AI platform.
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity,
    get_jwt
)
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, timedelta
import logging
from typing import Dict, Any
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config.settings import settings
from security.security_manager import SophiaSecurityManager

logger = logging.getLogger(__name__)

# Create blueprint
auth_bp = Blueprint('auth', __name__)

# Initialize security manager
security_manager = SophiaSecurityManager()

@auth_bp.route('/login', methods=['POST'])
async def login():
    """Login endpoint"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'error': 'Username and password required'}), 400
        
        # For now, check against admin credentials
        # In production, this would check against a user database
        if username == settings.security.admin_username:
            if password == settings.security.admin_password:
                # Create tokens
                access_token = create_access_token(
                    identity=username,
                    additional_claims={
                        'role': 'admin',
                        'company': settings.company_name
                    }
                )
                refresh_token = create_refresh_token(identity=username)
                
                # Create session
                user_agent = request.headers.get('User-Agent', '')
                ip_address = request.remote_addr
                session_token = await security_manager.create_session(
                    username, user_agent, ip_address
                )
                
                return jsonify({
                    'access_token': access_token,
                    'refresh_token': refresh_token,
                    'session_token': session_token,
                    'user': {
                        'username': username,
                        'role': 'admin',
                        'company': settings.company_name
                    }
                }), 200
        
        # Record failed attempt
        await security_manager.record_failed_attempt(username, 'login')
        
        return jsonify({'error': 'Invalid credentials'}), 401
        
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({'error': 'Authentication failed'}), 500

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token"""
    try:
        identity = get_jwt_identity()
        access_token = create_access_token(
            identity=identity,
            additional_claims={
                'role': 'admin',  # In production, get from user DB
                'company': settings.company_name
            }
        )
        
        return jsonify({'access_token': access_token}), 200
        
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        return jsonify({'error': 'Token refresh failed'}), 500

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
async def logout():
    """Logout endpoint"""
    try:
        # Get session token if provided
        data = request.get_json() or {}
        session_token = data.get('session_token')
        
        if session_token:
            # Invalidate session
            await security_manager.invalidate_session(session_token)
        
        # In production, you might also want to blacklist the JWT
        
        return jsonify({'message': 'Logged out successfully'}), 200
        
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        return jsonify({'error': 'Logout failed'}), 500

@auth_bp.route('/validate', methods=['GET'])
@jwt_required()
async def validate_token():
    """Validate current token"""
    try:
        identity = get_jwt_identity()
        claims = get_jwt()
        
        # Validate session if session token provided
        session_token = request.headers.get('X-Session-Token')
        if session_token:
            session_data = await security_manager.validate_session(session_token)
            if not session_data:
                return jsonify({'error': 'Invalid session'}), 401
        
        return jsonify({
            'valid': True,
            'user': {
                'username': identity,
                'role': claims.get('role', 'user'),
                'company': claims.get('company', settings.company_name)
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Token validation error: {str(e)}")
        return jsonify({'error': 'Validation failed'}), 500

@auth_bp.route('/permissions', methods=['GET'])
@jwt_required()
async def get_permissions():
    """Get user permissions"""
    try:
        identity = get_jwt_identity()
        claims = get_jwt()
        role = claims.get('role', 'user')
        
        # Define role-based permissions
        permissions = {
            'admin': [
                'agents.manage',
                'integrations.manage',
                'analytics.view',
                'analytics.export',
                'settings.manage',
                'users.manage'
            ],
            'user': [
                'analytics.view',
                'integrations.use'
            ]
        }
        
        user_permissions = permissions.get(role, [])
        
        return jsonify({
            'user': identity,
            'role': role,
            'permissions': user_permissions
        }), 200
        
    except Exception as e:
        logger.error(f"Permissions error: {str(e)}")
        return jsonify({'error': 'Failed to get permissions'}), 500

@auth_bp.route('/api-keys', methods=['GET'])
@jwt_required()
async def list_api_keys():
    """List configured API keys (without revealing actual keys)"""
    try:
        identity = get_jwt_identity()
        claims = get_jwt()
        
        # Only admins can view API keys
        if claims.get('role') != 'admin':
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Get API key status
        api_keys = await security_manager.list_api_keys()
        
        return jsonify({
            'api_keys': api_keys,
            'total': len(api_keys)
        }), 200
        
    except Exception as e:
        logger.error(f"API keys list error: {str(e)}")
        return jsonify({'error': 'Failed to list API keys'}), 500

@auth_bp.route('/api-keys/<service_name>', methods=['PUT'])
@jwt_required()
async def update_api_key(service_name: str):
    """Update API key for a service"""
    try:
        identity = get_jwt_identity()
        claims = get_jwt()
        
        # Only admins can update API keys
        if claims.get('role') != 'admin':
            return jsonify({'error': 'Unauthorized'}), 403
        
        data = request.get_json()
        api_key = data.get('api_key')
        
        if not api_key:
            return jsonify({'error': 'API key required'}), 400
        
        # Store the new API key
        success = await security_manager.store_api_key(
            service_name,
            api_key,
            metadata={
                'updated_by': identity,
                'updated_at': datetime.now().isoformat()
            }
        )
        
        if success:
            logger.info(f"API key updated for {service_name} by {identity}")
            return jsonify({
                'message': f'API key updated for {service_name}',
                'service': service_name
            }), 200
        else:
            return jsonify({'error': 'Failed to update API key'}), 500
            
    except Exception as e:
        logger.error(f"API key update error: {str(e)}")
        return jsonify({'error': 'Failed to update API key'}), 500

@auth_bp.route('/security/status', methods=['GET'])
@jwt_required()
async def security_status():
    """Get security system status"""
    try:
        identity = get_jwt_identity()
        claims = get_jwt()
        
        # Only admins can view security status
        if claims.get('role') != 'admin':
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Get security health check
        health = await security_manager.health_check()
        
        return jsonify(health), 200
        
    except Exception as e:
        logger.error(f"Security status error: {str(e)}")
        return jsonify({'error': 'Failed to get security status'}), 500

# Error handlers
@auth_bp.errorhandler(401)
def unauthorized(error):
    return jsonify({'error': 'Unauthorized access'}), 401

@auth_bp.errorhandler(403)
def forbidden(error):
    return jsonify({'error': 'Forbidden'}), 403

@auth_bp.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

