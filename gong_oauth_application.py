#!/usr/bin/env python3
"""
Gong OAuth Application Handler for Sophia AI
Manages the OAuth 2.0 flow for Gong API integration.
"""

import os
import logging
import requests
from flask import url_for, redirect # Assuming Flask context for redirect_uri

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# These should be configured via environment variables or a secure config system
GONG_CLIENT_ID = os.getenv("GONG_OAUTH_CLIENT_ID")
GONG_CLIENT_SECRET = os.getenv("GONG_OAUTH_CLIENT_SECRET")
GONG_REDIRECT_URI = os.getenv("GONG_OAUTH_REDIRECT_URI") # e.g., https://your-app.com/api/auth/gong/callback
GONG_AUTHORIZATION_URL = "https://app.gong.io/oauth2/authorize" # Check Gong docs for exact URL
GONG_TOKEN_URL = "https://app.gong.io/oauth2/token" # Check Gong docs for exact URL

# Required OAuth Scopes (as per the prompt)
REQUIRED_SCOPES = [
    "api:calls:read:extensive",
    "api:calls:read:transcript",
    "api:calls:read:media-url",
    "api:users:read",
    "api:workspaces:read"
]

class GongOAuthHandler:
    def __init__(self, client_id=None, client_secret=None, redirect_uri=None):
        self.client_id = client_id or GONG_CLIENT_ID
        self.client_secret = client_secret or GONG_CLIENT_SECRET
        self.redirect_uri = redirect_uri or GONG_REDIRECT_URI

        if not all([self.client_id, self.client_secret, self.redirect_uri]):
            logger.error("Gong OAuth client ID, secret, or redirect URI not configured.")
            # In a real app, this might raise an exception or handle differently
            # For now, we'll allow it to proceed for placeholder purposes

    def get_authorization_url(self, state: str = None) -> str:
        """
        Generates the Gong authorization URL to redirect the user to.
        """
        if not all([self.client_id, self.redirect_uri]):
            logger.error("Cannot generate authorization URL: Client ID or Redirect URI missing.")
            return "/error_oauth_misconfigured" # Placeholder error path

        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": " ".join(REQUIRED_SCOPES),
        }
        if state:
            params["state"] = state
        
        # Using requests.Request to build the URL safely
        req = requests.Request('GET', GONG_AUTHORIZATION_URL, params=params)
        prepared_req = req.prepare()
        logger.info(f"Generated Gong authorization URL: {prepared_req.url}")
        return prepared_req.url

    def exchange_code_for_tokens(self, authorization_code: str) -> dict:
        """
        Exchanges an authorization code for access and refresh tokens.
        """
        if not all([self.client_id, self.client_secret, self.redirect_uri]):
            logger.error("Cannot exchange code: Client ID, Secret or Redirect URI missing.")
            return {"error": "OAuth client misconfigured"}

        payload = {
            "grant_type": "authorization_code",
            "code": authorization_code,
            "redirect_uri": self.redirect_uri,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        try:
            response = requests.post(GONG_TOKEN_URL, data=payload)
            response.raise_for_status()  # Raises an HTTPError for bad responses (4XX or 5XX)
            tokens = response.json()
            logger.info("Successfully exchanged code for tokens.")
            # TODO: Securely store these tokens (e.g., in database, associated with a user/tenant)
            # self.store_tokens(tokens.get("access_token"), tokens.get("refresh_token"), tokens.get("expires_in"))
            return tokens
        except requests.exceptions.RequestException as e:
            logger.error(f"Error exchanging code for tokens: {e}. Response: {e.response.text if e.response else 'No response'}")
            return {"error": "Failed to exchange code for tokens", "details": str(e)}

    def refresh_access_token(self, refresh_token: str) -> dict:
        """
        Refreshes an access token using a refresh token.
        """
        if not all([self.client_id, self.client_secret]):
            logger.error("Cannot refresh token: Client ID or Secret missing.")
            return {"error": "OAuth client misconfigured"}

        payload = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        try:
            response = requests.post(GONG_TOKEN_URL, data=payload)
            response.raise_for_status()
            new_tokens = response.json()
            logger.info("Successfully refreshed access token.")
            # TODO: Securely update stored tokens
            # self.store_tokens(new_tokens.get("access_token"), new_tokens.get("refresh_token"), new_tokens.get("expires_in"))
            return new_tokens
        except requests.exceptions.RequestException as e:
            logger.error(f"Error refreshing access token: {e}. Response: {e.response.text if e.response else 'No response'}")
            return {"error": "Failed to refresh access token", "details": str(e)}

    def store_tokens(self, access_token: str, refresh_token: Optional[str], expires_in: int, user_id: str = "default_user"):
        """
        Placeholder for securely storing tokens.
        In a real application, this would interact with a database.
        """
        # This is a critical security function. Implement with care.
        # For multi-tenant, user_id or tenant_id would be crucial.
        logger.info(f"Storing tokens for user_id: {user_id} (access_token: {access_token[:10]}..., refresh_token: {refresh_token[:10] if refresh_token else 'None'}...)")
        # Example: await db.save_gong_tokens(user_id, access_token, refresh_token, expires_at)
        print(f"Placeholder: Tokens for {user_id} would be stored here.")
        # Simulating storage
        self._temp_token_storage = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_at": datetime.utcnow().timestamp() + expires_in
        }


    def get_access_token(self, user_id: str = "default_user") -> Optional[str]:
        """
        Placeholder for retrieving a stored access token.
        Should also handle token refresh if expired.
        """
        logger.info(f"Retrieving access token for user_id: {user_id}")
        # Example: token_info = await db.get_gong_tokens(user_id)
        # if token_info and token_info.expires_at > datetime.utcnow().timestamp():
        #     return token_info.access_token
        # elif token_info and token_info.refresh_token:
        #     new_tokens = self.refresh_access_token(token_info.refresh_token)
        #     return new_tokens.get("access_token")
        # return None
        
        # Simulating retrieval and refresh
        if hasattr(self, '_temp_token_storage'):
            if self._temp_token_storage['expires_at'] > datetime.utcnow().timestamp():
                return self._temp_token_storage['access_token']
            elif self._temp_token_storage.get('refresh_token'):
                logger.info("Access token expired, attempting refresh...")
                new_tokens = self.refresh_access_token(self._temp_token_storage['refresh_token'])
                if "access_token" in new_tokens:
                    self.store_tokens(new_tokens['access_token'], new_tokens.get('refresh_token'), new_tokens['expires_in'], user_id)
                    return new_tokens['access_token']
        return None

# Example usage (for testing purposes, typically not run directly like this)
if __name__ == "__main__":
    # Ensure GONG_OAUTH_CLIENT_ID, GONG_OAUTH_CLIENT_SECRET, GONG_OAUTH_REDIRECT_URI are set in your environment
    if not all([GONG_CLIENT_ID, GONG_CLIENT_SECRET, GONG_REDIRECT_URI]):
        print("Please set GONG_OAUTH_CLIENT_ID, GONG_OAUTH_CLIENT_SECRET, and GONG_OAUTH_REDIRECT_URI environment variables to run this example.")
    else:
        handler = GongOAuthHandler()
        auth_url = handler.get_authorization_url(state="randomstate123")
        print(f"1. Visit this URL to authorize: {auth_url}")
        
        # Simulate receiving an authorization code after user authorization
        mock_auth_code = input("2. After authorizing, paste the 'code' from the redirect URL here: ")
        if mock_auth_code:
            tokens = handler.exchange_code_for_tokens(mock_auth_code)
            print(f"3. Tokens received: {tokens}")

            if "access_token" in tokens:
                access_token = handler.get_access_token()
                print(f"4. Retrieved access token: {access_token[:20]}...")

                if tokens.get("refresh_token"):
                    # Simulate token expiration for refresh test
                    handler._temp_token_storage['expires_at'] = datetime.utcnow().timestamp() - 3600 # Expired 1 hour ago
                    print("Simulated token expiration. Attempting refresh...")
                    refreshed_access_token = handler.get_access_token()
                    if refreshed_access_token:
                         print(f"5. Refreshed access token: {refreshed_access_token[:20]}...")
                    else:
                        print("Failed to refresh token via get_access_token.")
        else:
            print("No authorization code provided. Skipping token exchange.")
