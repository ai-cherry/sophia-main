"""
Sophia AI - Enhanced Security Manager
Enterprise-grade security and key management for AI assistant orchestrator

This module provides comprehensive security features including:
- API key rotation and management
- Secure credential storage
- Access control and authentication
- Security monitoring and alerting
- Compliance and audit logging
"""

import asyncio
import json
import logging
import hashlib
import secrets
import base64
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import redis.asyncio as redis
import os

logger = logging.getLogger(__name__)

class SecurityConfig:
    def __init__(self):
        self.master_key = os.getenv('SOPHIA_MASTER_KEY', '')
        self.redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        self.key_rotation_days = int(os.getenv('KEY_ROTATION_DAYS', '30'))
        self.max_failed_attempts = int(os.getenv('MAX_FAILED_ATTEMPTS', '5'))
        self.session_timeout_hours = int(os.getenv('SESSION_TIMEOUT_HOURS', '24'))
        self.audit_log_retention_days = int(os.getenv('AUDIT_LOG_RETENTION_DAYS', '90'))

class SophiaSecurityManager:
    """Enhanced security manager for Sophia AI platform"""
    
    def __init__(self, config: SecurityConfig = None):
        self.config = config or SecurityConfig()
        self.redis_client = None
        self.encryption_key = None
        self.active_sessions = {}
        self.failed_attempts = {}
        
        # Initialize encryption
        self._initialize_encryption()
    
    def _initialize_encryption(self):
        """Initialize encryption key from master key"""
        if not self.config.master_key:
            # Generate a new master key if none exists
            self.config.master_key = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode()
            logger.warning("Generated new master key - store this securely!")
        
        # Derive encryption key from master key
        master_key_bytes = self.config.master_key.encode()
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'sophia_ai_salt',  # In production, use a random salt
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(master_key_bytes))
        self.encryption_key = Fernet(key)
    
    async def start(self):
        """Start the security manager"""
        try:
            # Connect to Redis for session and key storage
            self.redis_client = redis.from_url(self.config.redis_url)
            
            # Initialize security monitoring
            await self._initialize_security_monitoring()
            
            logger.info("Sophia Security Manager started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start security manager: {str(e)}")
            raise
    
    async def stop(self):
        """Stop the security manager"""
        try:
            if self.redis_client:
                await self.redis_client.close()
            
            logger.info("Sophia Security Manager stopped")
            
        except Exception as e:
            logger.error(f"Error stopping security manager: {str(e)}")
    
    # API Key Management
    async def store_api_key(self, service_name: str, api_key: str, metadata: Dict[str, Any] = None) -> bool:
        """Securely store API key with encryption"""
        try:
            # Encrypt the API key
            encrypted_key = self.encryption_key.encrypt(api_key.encode())
            
            # Prepare key data
            key_data = {
                'encrypted_key': base64.b64encode(encrypted_key).decode(),
                'service_name': service_name,
                'created_at': datetime.now().isoformat(),
                'last_rotated': datetime.now().isoformat(),
                'rotation_due': (datetime.now() + timedelta(days=self.config.key_rotation_days)).isoformat(),
                'metadata': metadata or {},
                'usage_count': 0,
                'last_used': None
            }
            
            # Store in Redis
            key_id = f"api_key:{service_name}"
            await self.redis_client.hset(key_id, mapping={
                k: json.dumps(v) if isinstance(v, (dict, list)) else str(v)
                for k, v in key_data.items()
            })
            
            # Log the action
            await self._log_security_event('api_key_stored', {
                'service_name': service_name,
                'key_id': key_id
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to store API key for {service_name}: {str(e)}")
            return False
    
    async def get_api_key(self, service_name: str) -> Optional[str]:
        """Retrieve and decrypt API key"""
        try:
            key_id = f"api_key:{service_name}"
            key_data = await self.redis_client.hgetall(key_id)
            
            if not key_data:
                logger.warning(f"API key not found for service: {service_name}")
                return None
            
            # Decrypt the key
            encrypted_key = base64.b64decode(key_data[b'encrypted_key'])
            decrypted_key = self.encryption_key.decrypt(encrypted_key).decode()
            
            # Update usage statistics
            await self.redis_client.hincrby(key_id, 'usage_count', 1)
            await self.redis_client.hset(key_id, 'last_used', datetime.now().isoformat())
            
            # Check if rotation is due
            rotation_due = datetime.fromisoformat(key_data[b'rotation_due'].decode())
            if datetime.now() > rotation_due:
                await self._schedule_key_rotation(service_name)
            
            return decrypted_key
            
        except Exception as e:
            logger.error(f"Failed to retrieve API key for {service_name}: {str(e)}")
            return None
    
    async def rotate_api_key(self, service_name: str, new_api_key: str) -> bool:
        """Rotate API key for a service"""
        try:
            # Store the new key
            success = await self.store_api_key(service_name, new_api_key)
            
            if success:
                # Log the rotation
                await self._log_security_event('api_key_rotated', {
                    'service_name': service_name
                })
                
                logger.info(f"API key rotated successfully for {service_name}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to rotate API key for {service_name}: {str(e)}")
            return False
    
    async def list_api_keys(self) -> List[Dict[str, Any]]:
        """List all stored API keys (without revealing the actual keys)"""
        try:
            keys = []
            pattern = "api_key:*"
            
            async for key in self.redis_client.scan_iter(match=pattern):
                key_data = await self.redis_client.hgetall(key)
                
                if key_data:
                    keys.append({
                        'service_name': key_data[b'service_name'].decode(),
                        'created_at': key_data[b'created_at'].decode(),
                        'last_rotated': key_data[b'last_rotated'].decode(),
                        'rotation_due': key_data[b'rotation_due'].decode(),
                        'usage_count': int(key_data[b'usage_count']),
                        'last_used': key_data.get(b'last_used', b'').decode() or None,
                        'needs_rotation': datetime.now() > datetime.fromisoformat(key_data[b'rotation_due'].decode())
                    })
            
            return keys
            
        except Exception as e:
            logger.error(f"Failed to list API keys: {str(e)}")
            return []
    
    # Session Management
    async def create_session(self, user_id: str, user_agent: str = None, ip_address: str = None) -> Optional[str]:
        """Create a new authenticated session"""
        try:
            # Generate session token
            session_token = secrets.token_urlsafe(32)
            session_id = hashlib.sha256(session_token.encode()).hexdigest()
            
            # Session data
            session_data = {
                'user_id': user_id,
                'session_token': session_token,
                'created_at': datetime.now().isoformat(),
                'expires_at': (datetime.now() + timedelta(hours=self.config.session_timeout_hours)).isoformat(),
                'user_agent': user_agent or '',
                'ip_address': ip_address or '',
                'last_activity': datetime.now().isoformat(),
                'is_active': True
            }
            
            # Store session
            session_key = f"session:{session_id}"
            await self.redis_client.hset(session_key, mapping={
                k: json.dumps(v) if isinstance(v, (dict, list)) else str(v)
                for k, v in session_data.items()
            })
            
            # Set expiration
            await self.redis_client.expire(session_key, self.config.session_timeout_hours * 3600)
            
            # Track active session
            self.active_sessions[session_id] = session_data
            
            # Log session creation
            await self._log_security_event('session_created', {
                'user_id': user_id,
                'session_id': session_id,
                'ip_address': ip_address
            })
            
            return session_token
            
        except Exception as e:
            logger.error(f"Failed to create session for user {user_id}: {str(e)}")
            return None
    
    async def validate_session(self, session_token: str) -> Optional[Dict[str, Any]]:
        """Validate session token and return session data"""
        try:
            session_id = hashlib.sha256(session_token.encode()).hexdigest()
            session_key = f"session:{session_id}"
            
            session_data = await self.redis_client.hgetall(session_key)
            
            if not session_data:
                return None
            
            # Check if session is expired
            expires_at = datetime.fromisoformat(session_data[b'expires_at'].decode())
            if datetime.now() > expires_at:
                await self.invalidate_session(session_token)
                return None
            
            # Check if session is active
            if not json.loads(session_data[b'is_active'].decode()):
                return None
            
            # Update last activity
            await self.redis_client.hset(session_key, 'last_activity', datetime.now().isoformat())
            
            return {
                'user_id': session_data[b'user_id'].decode(),
                'session_id': session_id,
                'created_at': session_data[b'created_at'].decode(),
                'last_activity': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to validate session: {str(e)}")
            return None
    
    async def invalidate_session(self, session_token: str) -> bool:
        """Invalidate a session"""
        try:
            session_id = hashlib.sha256(session_token.encode()).hexdigest()
            session_key = f"session:{session_id}"
            
            # Mark as inactive
            await self.redis_client.hset(session_key, 'is_active', 'false')
            
            # Remove from active sessions
            if session_id in self.active_sessions:
                del self.active_sessions[session_id]
            
            # Log session invalidation
            await self._log_security_event('session_invalidated', {
                'session_id': session_id
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to invalidate session: {str(e)}")
            return False
    
    # Access Control
    async def check_permission(self, user_id: str, resource: str, action: str) -> bool:
        """Check if user has permission for specific action on resource"""
        try:
            # For single-user system, grant all permissions
            # In multi-user system, this would check role-based permissions
            
            # Log access attempt
            await self._log_security_event('permission_check', {
                'user_id': user_id,
                'resource': resource,
                'action': action,
                'granted': True
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to check permission: {str(e)}")
            return False
    
    async def record_failed_attempt(self, identifier: str, attempt_type: str = 'login') -> bool:
        """Record failed authentication attempt"""
        try:
            key = f"failed_attempts:{identifier}"
            
            # Get current attempts
            attempts = await self.redis_client.get(key)
            current_attempts = int(attempts) if attempts else 0
            
            # Increment attempts
            new_attempts = current_attempts + 1
            await self.redis_client.set(key, new_attempts, ex=3600)  # Expire in 1 hour
            
            # Check if threshold exceeded
            if new_attempts >= self.config.max_failed_attempts:
                await self._handle_security_breach(identifier, attempt_type, new_attempts)
            
            # Log failed attempt
            await self._log_security_event('failed_attempt', {
                'identifier': identifier,
                'attempt_type': attempt_type,
                'attempt_count': new_attempts
            })
            
            return new_attempts >= self.config.max_failed_attempts
            
        except Exception as e:
            logger.error(f"Failed to record failed attempt: {str(e)}")
            return False
    
    async def clear_failed_attempts(self, identifier: str) -> bool:
        """Clear failed attempts for identifier"""
        try:
            key = f"failed_attempts:{identifier}"
            await self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Failed to clear failed attempts: {str(e)}")
            return False
    
    # Security Monitoring
    async def _initialize_security_monitoring(self):
        """Initialize security monitoring and alerting"""
        try:
            # Set up monitoring tasks
            asyncio.create_task(self._monitor_key_rotations())
            asyncio.create_task(self._monitor_failed_attempts())
            asyncio.create_task(self._cleanup_expired_sessions())
            
            logger.info("Security monitoring initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize security monitoring: {str(e)}")
    
    async def _monitor_key_rotations(self):
        """Monitor and alert on keys that need rotation"""
        while True:
            try:
                keys_needing_rotation = []
                pattern = "api_key:*"
                
                async for key in self.redis_client.scan_iter(match=pattern):
                    key_data = await self.redis_client.hgetall(key)
                    
                    if key_data:
                        rotation_due = datetime.fromisoformat(key_data[b'rotation_due'].decode())
                        if datetime.now() > rotation_due:
                            service_name = key_data[b'service_name'].decode()
                            keys_needing_rotation.append(service_name)
                
                if keys_needing_rotation:
                    await self._log_security_event('keys_need_rotation', {
                        'services': keys_needing_rotation,
                        'count': len(keys_needing_rotation)
                    })
                
                # Check every hour
                await asyncio.sleep(3600)
                
            except Exception as e:
                logger.error(f"Error in key rotation monitoring: {str(e)}")
                await asyncio.sleep(3600)
    
    async def _monitor_failed_attempts(self):
        """Monitor failed authentication attempts"""
        while True:
            try:
                # This would implement real-time monitoring of failed attempts
                # and trigger alerts for suspicious activity
                
                # Check every 5 minutes
                await asyncio.sleep(300)
                
            except Exception as e:
                logger.error(f"Error in failed attempts monitoring: {str(e)}")
                await asyncio.sleep(300)
    
    async def _cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        while True:
            try:
                pattern = "session:*"
                expired_count = 0
                
                async for key in self.redis_client.scan_iter(match=pattern):
                    session_data = await self.redis_client.hgetall(key)
                    
                    if session_data:
                        expires_at = datetime.fromisoformat(session_data[b'expires_at'].decode())
                        if datetime.now() > expires_at:
                            await self.redis_client.delete(key)
                            expired_count += 1
                
                if expired_count > 0:
                    logger.info(f"Cleaned up {expired_count} expired sessions")
                
                # Check every hour
                await asyncio.sleep(3600)
                
            except Exception as e:
                logger.error(f"Error in session cleanup: {str(e)}")
                await asyncio.sleep(3600)
    
    async def _schedule_key_rotation(self, service_name: str):
        """Schedule key rotation for a service"""
        try:
            await self._log_security_event('key_rotation_scheduled', {
                'service_name': service_name,
                'scheduled_at': datetime.now().isoformat()
            })
            
            # In a production system, this would trigger an automated rotation
            # or send an alert to administrators
            
        except Exception as e:
            logger.error(f"Failed to schedule key rotation for {service_name}: {str(e)}")
    
    async def _handle_security_breach(self, identifier: str, attempt_type: str, attempt_count: int):
        """Handle potential security breach"""
        try:
            # Log security breach
            await self._log_security_event('security_breach_detected', {
                'identifier': identifier,
                'attempt_type': attempt_type,
                'attempt_count': attempt_count,
                'timestamp': datetime.now().isoformat()
            })
            
            # In production, this would:
            # - Send alerts to administrators
            # - Temporarily block the identifier
            # - Trigger additional security measures
            
            logger.warning(f"Security breach detected: {identifier} - {attempt_count} failed {attempt_type} attempts")
            
        except Exception as e:
            logger.error(f"Failed to handle security breach: {str(e)}")
    
    # Audit Logging
    async def _log_security_event(self, event_type: str, event_data: Dict[str, Any]):
        """Log security event for audit purposes"""
        try:
            event = {
                'event_type': event_type,
                'event_data': event_data,
                'timestamp': datetime.now().isoformat(),
                'event_id': secrets.token_hex(16)
            }
            
            # Store in Redis with expiration
            event_key = f"security_log:{event['event_id']}"
            await self.redis_client.set(
                event_key,
                json.dumps(event),
                ex=self.config.audit_log_retention_days * 24 * 3600
            )
            
            # Also log to application logger
            logger.info(f"Security Event: {event_type} - {json.dumps(event_data)}")
            
        except Exception as e:
            logger.error(f"Failed to log security event: {str(e)}")
    
    async def get_security_events(self, event_type: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieve security events for audit purposes"""
        try:
            events = []
            pattern = "security_log:*"
            
            async for key in self.redis_client.scan_iter(match=pattern):
                event_data = await self.redis_client.get(key)
                
                if event_data:
                    event = json.loads(event_data)
                    
                    if event_type is None or event.get('event_type') == event_type:
                        events.append(event)
                        
                        if len(events) >= limit:
                            break
            
            # Sort by timestamp (newest first)
            events.sort(key=lambda x: x['timestamp'], reverse=True)
            
            return events
            
        except Exception as e:
            logger.error(f"Failed to retrieve security events: {str(e)}")
            return []
    
    # Health Check
    async def health_check(self) -> Dict[str, Any]:
        """Perform security system health check"""
        try:
            health = {
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'components': {}
            }
            
            # Check Redis connection
            try:
                await self.redis_client.ping()
                health['components']['redis'] = 'healthy'
            except Exception:
                health['components']['redis'] = 'unhealthy'
                health['status'] = 'degraded'
            
            # Check encryption
            try:
                test_data = "test_encryption"
                encrypted = self.encryption_key.encrypt(test_data.encode())
                decrypted = self.encryption_key.decrypt(encrypted).decode()
                health['components']['encryption'] = 'healthy' if decrypted == test_data else 'unhealthy'
            except Exception:
                health['components']['encryption'] = 'unhealthy'
                health['status'] = 'degraded'
            
            # Check key storage
            try:
                keys = await self.list_api_keys()
                health['components']['key_storage'] = 'healthy'
                health['stored_keys_count'] = len(keys)
            except Exception:
                health['components']['key_storage'] = 'unhealthy'
                health['status'] = 'degraded'
            
            return health
            
        except Exception as e:
            logger.error(f"Security health check failed: {str(e)}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

# Example usage
if __name__ == "__main__":
    async def main():
        config = SecurityConfig()
        security_manager = SophiaSecurityManager(config)
        
        try:
            await security_manager.start()
            
            # Example operations
            await security_manager.store_api_key('hubspot', 'test_key_123')
            retrieved_key = await security_manager.get_api_key('hubspot')
            print(f"Retrieved key: {retrieved_key}")
            
            # Create session
            session_token = await security_manager.create_session('user_123')
            print(f"Session token: {session_token}")
            
            # Validate session
            session_data = await security_manager.validate_session(session_token)
            print(f"Session data: {session_data}")
            
            # Health check
            health = await security_manager.health_check()
            print(f"Health: {health}")
            
        finally:
            await security_manager.stop()
    
    asyncio.run(main())

