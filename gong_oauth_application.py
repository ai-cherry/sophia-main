#!/usr/bin/env python3
"""
Gong OAuth Application Implementation
Complete OAuth 2.0 flow for enhanced Gong API access
"""

import os
import json
import base64
import secrets
import hashlib
import urllib.parse
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import requests
import asyncio
import asyncpg
from flask import Flask, request, redirect, session, jsonify, url_for
from flask_cors import CORS
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GongOAuthManager:
    """
    Complete OAuth 2.0 implementation for Gong API integration
    """
    
    def __init__(self):
        # OAuth Configuration
        self.client_id = "pay_ready_conversation_intelligence"  # Will be provided by Gong
        self.client_secret = os.getenv("GONG_OAUTH_CLIENT_SECRET", "")
        self.redirect_uri = os.getenv("GONG_OAUTH_REDIRECT_URI", "https://your-app.vercel.app/auth/gong/callback")
        
        # Gong OAuth endpoints
        self.authorization_url = "https://app.gong.io/oauth2/authorize"
        self.token_url = "https://app.gong.io/oauth2/generate-customer-token"
        self.base_api_url = "https://us-70092.api.gong.io"
        
        # Enhanced OAuth scopes for premium features
        self.scopes = [
            "api:calls:read:extensive",      # Extended call data with interaction stats
            "api:calls:read:transcript",     # Full call transcripts with speaker identification
            "api:calls:read:media-url",      # Direct access to audio/video media files
            "api:stats:interaction",         # Detailed user interaction statistics
            "api:stats:scorecards",          # Scorecard statistics and performance metrics
            "api:library:read",              # Access to call libraries and folders
            "api:settings:trackers:read",    # Keyword tracker configuration
            "api:crm:get-objects",           # CRM integration capabilities
            "api:digital-interactions:write" # Create digital interaction records
        ]
        
        # Database configuration
        self.db_config = {
            "host": "localhost",
            "port": 5432,
            "user": "postgres",
            "password": "password",
            "database": "sophia_enhanced"
        }
    
    def generate_authorization_url(self, state: str = None) -> Dict[str, str]:
        """Generate OAuth authorization URL with PKCE"""
        
        # Generate state parameter for CSRF protection
        if not state:
            state = secrets.token_urlsafe(32)
        
        # Generate PKCE code verifier and challenge
        code_verifier = secrets.token_urlsafe(32)
        code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode()).digest()
        ).decode().rstrip('=')
        
        # Build authorization parameters
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": " ".join(self.scopes),
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256"
        }
        
        # Construct authorization URL
        auth_url = f"{self.authorization_url}?{urllib.parse.urlencode(params)}"
        
        return {
            "authorization_url": auth_url,
            "state": state,
            "code_verifier": code_verifier,
            "code_challenge": code_challenge
        }
    
    async def exchange_code_for_tokens(self, authorization_code: str, code_verifier: str, state: str) -> Dict[str, Any]:
        """Exchange authorization code for access and refresh tokens"""
        
        try:
            # Prepare token exchange request
            token_data = {
                "grant_type": "authorization_code",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "code": authorization_code,
                "redirect_uri": self.redirect_uri,
                "code_verifier": code_verifier
            }
            
            # Make token exchange request
            response = requests.post(
                self.token_url,
                data=token_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=30
            )
            
            if response.status_code == 200:
                token_response = response.json()
                
                # Calculate token expiration
                expires_in = token_response.get("expires_in", 3600)
                expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
                
                # Store tokens securely
                token_data = {
                    "access_token": token_response.get("access_token"),
                    "refresh_token": token_response.get("refresh_token"),
                    "token_type": token_response.get("token_type", "Bearer"),
                    "expires_in": expires_in,
                    "expires_at": expires_at.isoformat(),
                    "scope": token_response.get("scope"),
                    "state": state,
                    "created_at": datetime.utcnow().isoformat()
                }
                
                # Store in database
                await self._store_tokens(token_data)
                
                return {
                    "success": True,
                    "tokens": token_data,
                    "message": "OAuth tokens obtained successfully"
                }
            else:
                return {
                    "success": False,
                    "error": f"Token exchange failed: {response.status_code}",
                    "details": response.text
                }
                
        except Exception as e:
            logger.error(f"Token exchange error: {str(e)}")
            return {
                "success": False,
                "error": "Token exchange failed",
                "details": str(e)
            }
    
    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh expired access token"""
        
        try:
            refresh_data = {
                "grant_type": "refresh_token",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "refresh_token": refresh_token
            }
            
            response = requests.post(
                self.token_url,
                data=refresh_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=30
            )
            
            if response.status_code == 200:
                token_response = response.json()
                
                # Calculate new expiration
                expires_in = token_response.get("expires_in", 3600)
                expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
                
                # Update token data
                updated_tokens = {
                    "access_token": token_response.get("access_token"),
                    "refresh_token": token_response.get("refresh_token", refresh_token),
                    "token_type": token_response.get("token_type", "Bearer"),
                    "expires_in": expires_in,
                    "expires_at": expires_at.isoformat(),
                    "scope": token_response.get("scope"),
                    "refreshed_at": datetime.utcnow().isoformat()
                }
                
                # Update in database
                await self._update_tokens(updated_tokens)
                
                return {
                    "success": True,
                    "tokens": updated_tokens,
                    "message": "Tokens refreshed successfully"
                }
            else:
                return {
                    "success": False,
                    "error": f"Token refresh failed: {response.status_code}",
                    "details": response.text
                }
                
        except Exception as e:
            logger.error(f"Token refresh error: {str(e)}")
            return {
                "success": False,
                "error": "Token refresh failed",
                "details": str(e)
            }
    
    async def get_valid_access_token(self) -> Optional[str]:
        """Get valid access token, refreshing if necessary"""
        
        try:
            # Get current tokens from database
            tokens = await self._get_stored_tokens()
            
            if not tokens:
                return None
            
            # Check if token is expired
            expires_at = datetime.fromisoformat(tokens["expires_at"])
            
            if datetime.utcnow() >= expires_at - timedelta(minutes=5):  # Refresh 5 minutes early
                # Token is expired or about to expire, refresh it
                refresh_result = await self.refresh_access_token(tokens["refresh_token"])
                
                if refresh_result["success"]:
                    return refresh_result["tokens"]["access_token"]
                else:
                    logger.error("Failed to refresh token")
                    return None
            else:
                # Token is still valid
                return tokens["access_token"]
                
        except Exception as e:
            logger.error(f"Error getting valid access token: {str(e)}")
            return None
    
    async def make_authenticated_request(self, endpoint: str, method: str = "GET", params: Dict = None, data: Dict = None) -> Dict[str, Any]:
        """Make authenticated request to Gong API"""
        
        try:
            # Get valid access token
            access_token = await self.get_valid_access_token()
            
            if not access_token:
                return {
                    "success": False,
                    "error": "No valid access token available",
                    "requires_reauth": True
                }
            
            # Prepare request headers
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            # Make API request
            url = f"{self.base_api_url}{endpoint}"
            
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, params=params, timeout=30)
            elif method.upper() == "POST":
                response = requests.post(url, headers=headers, json=data, timeout=30)
            else:
                return {
                    "success": False,
                    "error": f"Unsupported HTTP method: {method}"
                }
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "data": response.json(),
                    "status_code": response.status_code
                }
            elif response.status_code == 401:
                # Token might be invalid, try refreshing
                refresh_result = await self.refresh_access_token(await self._get_refresh_token())
                
                if refresh_result["success"]:
                    # Retry request with new token
                    headers["Authorization"] = f"Bearer {refresh_result['tokens']['access_token']}"
                    
                    if method.upper() == "GET":
                        response = requests.get(url, headers=headers, params=params, timeout=30)
                    elif method.upper() == "POST":
                        response = requests.post(url, headers=headers, json=data, timeout=30)
                    
                    if response.status_code == 200:
                        return {
                            "success": True,
                            "data": response.json(),
                            "status_code": response.status_code,
                            "token_refreshed": True
                        }
                
                return {
                    "success": False,
                    "error": "Authentication failed",
                    "status_code": response.status_code,
                    "requires_reauth": True
                }
            else:
                return {
                    "success": False,
                    "error": f"API request failed: {response.status_code}",
                    "details": response.text,
                    "status_code": response.status_code
                }
                
        except Exception as e:
            logger.error(f"Authenticated request error: {str(e)}")
            return {
                "success": False,
                "error": "Request failed",
                "details": str(e)
            }
    
    async def _store_tokens(self, token_data: Dict[str, Any]) -> None:
        """Store OAuth tokens in database"""
        
        try:
            conn = await asyncpg.connect(**self.db_config)
            
            # Create OAuth tokens table if it doesn't exist
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS oauth_tokens (
                    id SERIAL PRIMARY KEY,
                    client_id VARCHAR(255) NOT NULL,
                    access_token TEXT NOT NULL,
                    refresh_token TEXT,
                    token_type VARCHAR(50) DEFAULT 'Bearer',
                    expires_in INTEGER,
                    expires_at TIMESTAMP,
                    scope TEXT,
                    state VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Insert or update tokens
            await conn.execute("""
                INSERT INTO oauth_tokens (client_id, access_token, refresh_token, token_type, expires_in, expires_at, scope, state)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                ON CONFLICT (client_id) DO UPDATE SET
                    access_token = EXCLUDED.access_token,
                    refresh_token = EXCLUDED.refresh_token,
                    token_type = EXCLUDED.token_type,
                    expires_in = EXCLUDED.expires_in,
                    expires_at = EXCLUDED.expires_at,
                    scope = EXCLUDED.scope,
                    state = EXCLUDED.state,
                    updated_at = CURRENT_TIMESTAMP
            """, 
                self.client_id,
                token_data["access_token"],
                token_data.get("refresh_token"),
                token_data["token_type"],
                token_data["expires_in"],
                datetime.fromisoformat(token_data["expires_at"]),
                token_data.get("scope"),
                token_data.get("state")
            )
            
            await conn.close()
            
        except Exception as e:
            logger.error(f"Error storing tokens: {str(e)}")
            raise
    
    async def _get_stored_tokens(self) -> Optional[Dict[str, Any]]:
        """Retrieve stored OAuth tokens from database"""
        
        try:
            conn = await asyncpg.connect(**self.db_config)
            
            row = await conn.fetchrow("""
                SELECT access_token, refresh_token, token_type, expires_in, expires_at, scope, state
                FROM oauth_tokens
                WHERE client_id = $1
                ORDER BY updated_at DESC
                LIMIT 1
            """, self.client_id)
            
            await conn.close()
            
            if row:
                return {
                    "access_token": row["access_token"],
                    "refresh_token": row["refresh_token"],
                    "token_type": row["token_type"],
                    "expires_in": row["expires_in"],
                    "expires_at": row["expires_at"].isoformat(),
                    "scope": row["scope"],
                    "state": row["state"]
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving tokens: {str(e)}")
            return None
    
    async def _update_tokens(self, token_data: Dict[str, Any]) -> None:
        """Update stored OAuth tokens"""
        
        try:
            conn = await asyncpg.connect(**self.db_config)
            
            await conn.execute("""
                UPDATE oauth_tokens
                SET access_token = $2,
                    refresh_token = $3,
                    token_type = $4,
                    expires_in = $5,
                    expires_at = $6,
                    scope = $7,
                    updated_at = CURRENT_TIMESTAMP
                WHERE client_id = $1
            """,
                self.client_id,
                token_data["access_token"],
                token_data.get("refresh_token"),
                token_data["token_type"],
                token_data["expires_in"],
                datetime.fromisoformat(token_data["expires_at"]),
                token_data.get("scope")
            )
            
            await conn.close()
            
        except Exception as e:
            logger.error(f"Error updating tokens: {str(e)}")
            raise
    
    async def _get_refresh_token(self) -> Optional[str]:
        """Get refresh token from database"""
        
        try:
            tokens = await self._get_stored_tokens()
            return tokens["refresh_token"] if tokens else None
        except Exception as e:
            logger.error(f"Error getting refresh token: {str(e)}")
            return None

# Flask application for OAuth flow
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", secrets.token_hex(32))
CORS(app, origins=["http://localhost:3000", "http://localhost:5173", "https://*.vercel.app"])

# Initialize OAuth manager
oauth_manager = GongOAuthManager()

@app.route("/auth/gong/login")
def gong_login():
    """Initiate Gong OAuth flow"""
    
    try:
        # Generate authorization URL
        auth_data = oauth_manager.generate_authorization_url()
        
        # Store state and code verifier in session
        session["oauth_state"] = auth_data["state"]
        session["code_verifier"] = auth_data["code_verifier"]
        
        # Redirect to Gong authorization
        return redirect(auth_data["authorization_url"])
        
    except Exception as e:
        logger.error(f"OAuth login error: {str(e)}")
        return jsonify({
            "error": "OAuth login failed",
            "details": str(e)
        }), 500

@app.route("/auth/gong/callback")
def gong_callback():
    """Handle Gong OAuth callback"""
    
    try:
        # Get authorization code and state from callback
        authorization_code = request.args.get("code")
        state = request.args.get("state")
        error = request.args.get("error")
        
        if error:
            return jsonify({
                "error": f"OAuth authorization failed: {error}",
                "description": request.args.get("error_description")
            }), 400
        
        if not authorization_code:
            return jsonify({
                "error": "No authorization code received"
            }), 400
        
        # Verify state parameter
        if state != session.get("oauth_state"):
            return jsonify({
                "error": "Invalid state parameter"
            }), 400
        
        # Exchange code for tokens
        code_verifier = session.get("code_verifier")
        
        async def exchange_tokens():
            return await oauth_manager.exchange_code_for_tokens(
                authorization_code, code_verifier, state
            )
        
        # Run async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        token_result = loop.run_until_complete(exchange_tokens())
        loop.close()
        
        if token_result["success"]:
            # Clear session data
            session.pop("oauth_state", None)
            session.pop("code_verifier", None)
            
            # Redirect to success page
            return redirect(url_for("oauth_success"))
        else:
            return jsonify({
                "error": "Token exchange failed",
                "details": token_result.get("error")
            }), 500
            
    except Exception as e:
        logger.error(f"OAuth callback error: {str(e)}")
        return jsonify({
            "error": "OAuth callback failed",
            "details": str(e)
        }), 500

@app.route("/auth/gong/success")
def oauth_success():
    """OAuth success page"""
    
    return jsonify({
        "message": "OAuth authorization successful!",
        "status": "authenticated",
        "enhanced_features": [
            "Full conversation transcripts",
            "Audio/video media access",
            "Real-time webhook notifications",
            "Advanced interaction statistics",
            "Scorecard performance metrics"
        ],
        "next_steps": [
            "Access enhanced conversation intelligence",
            "Configure real-time webhooks",
            "Explore advanced analytics features"
        ]
    })

@app.route("/api/oauth/status")
def oauth_status():
    """Check OAuth authentication status"""
    
    async def check_status():
        tokens = await oauth_manager._get_stored_tokens()
        
        if tokens:
            # Check if token is valid
            expires_at = datetime.fromisoformat(tokens["expires_at"])
            is_expired = datetime.utcnow() >= expires_at
            
            return {
                "authenticated": True,
                "expires_at": tokens["expires_at"],
                "is_expired": is_expired,
                "scopes": tokens.get("scope", "").split() if tokens.get("scope") else [],
                "token_type": tokens.get("token_type", "Bearer")
            }
        else:
            return {
                "authenticated": False,
                "login_url": url_for("gong_login", _external=True)
            }
    
    # Run async function
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    status = loop.run_until_complete(check_status())
    loop.close()
    
    return jsonify(status)

@app.route("/api/gong/enhanced/<endpoint>")
def enhanced_gong_api(endpoint):
    """Proxy for enhanced Gong API endpoints"""
    
    async def make_request():
        # Map endpoint to actual Gong API path
        endpoint_mapping = {
            "transcripts": "/v2/calls/transcript",
            "media": "/v2/calls/media-url",
            "extensive": "/v2/calls/extensive",
            "interaction-stats": "/v2/stats/interaction",
            "scorecards": "/v2/stats/scorecards",
            "library": "/v2/library/folders"
        }
        
        api_endpoint = endpoint_mapping.get(endpoint)
        
        if not api_endpoint:
            return {
                "success": False,
                "error": f"Unknown endpoint: {endpoint}"
            }
        
        # Get request parameters
        params = dict(request.args)
        
        # Make authenticated request
        return await oauth_manager.make_authenticated_request(
            api_endpoint, "GET", params
        )
    
    # Run async function
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(make_request())
    loop.close()
    
    if result["success"]:
        return jsonify(result["data"])
    else:
        status_code = 401 if result.get("requires_reauth") else 500
        return jsonify({
            "error": result["error"],
            "details": result.get("details")
        }), status_code

@app.route("/api/health")
def health_check():
    """Health check endpoint"""
    
    return jsonify({
        "status": "healthy",
        "service": "Gong OAuth Integration",
        "timestamp": datetime.utcnow().isoformat(),
        "features": {
            "oauth_flow": "implemented",
            "token_management": "implemented",
            "enhanced_api": "implemented",
            "webhook_ready": "pending"
        }
    })

if __name__ == "__main__":
    # Run Flask application
    app.run(host="0.0.0.0", port=5001, debug=True)

