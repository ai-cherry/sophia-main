"""
Sophia AI - Configuration Management
Centralized configuration using environment variables and Pydantic

This module provides a unified configuration system for all Sophia AI components.
"""

from pydantic_settings import BaseSettings
from pydantic import Field, validator, ConfigDict
from typing import Optional, Dict, Any
import os
from pathlib import Path

# Determine environment
ENV = os.getenv('SOPHIA_ENV', 'development')

class DatabaseSettings(BaseSettings):
    """Database configuration"""
    postgres_host: str = Field(default="150.230.47.71", env='POSTGRES_HOST')
    postgres_port: int = Field(default=5432, env='POSTGRES_PORT')
    postgres_user: str = Field(default="sophia", env='POSTGRES_USER')
    postgres_password: str = Field(default="sophia_pass", env='POSTGRES_PASSWORD')
    postgres_db: str = Field(default="sophia_payready", env='POSTGRES_DB')
    
    redis_host: str = Field(default="150.230.47.71", env='REDIS_HOST')
    redis_port: int = Field(default=6379, env='REDIS_PORT')
    redis_password: Optional[str] = Field(default=None, env='REDIS_PASSWORD')
    redis_db: int = Field(default=0, env='REDIS_DB')
    
    @property
    def postgres_url(self) -> str:
        """Generate PostgreSQL connection URL"""
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
    
    @property
    def redis_url(self) -> str:
        """Generate Redis connection URL"""
        auth = f":{self.redis_password}@" if self.redis_password else ""
        return f"redis://{auth}{self.redis_host}:{self.redis_port}/{self.redis_db}"
    
    model_config = ConfigDict(
        env_prefix="SOPHIA_",
        extra="ignore"  # Allow extra environment variables
    )

class SecuritySettings(BaseSettings):
    """Security configuration"""
    secret_key: str = Field(default="change-me-in-production", env='SECRET_KEY')
    master_key: Optional[str] = Field(default=None, env='SOPHIA_MASTER_KEY')
    jwt_algorithm: str = Field(default="HS256", env='JWT_ALGORITHM')
    jwt_expiration_hours: int = Field(default=24, env='JWT_EXPIRATION_HOURS')
    
    admin_username: str = Field(default="admin", env='ADMIN_USERNAME')
    admin_password: str = Field(default="admin123", env='ADMIN_PASSWORD')
    
    allowed_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:5000"],
        env='ALLOWED_ORIGINS'
    )
    
    @validator('secret_key')
    def validate_secret_key(cls, v):
        if v == "change-me-in-production" and ENV == "production":
            raise ValueError("Secret key must be changed in production")
        return v
    
    model_config = ConfigDict(
        env_prefix="SOPHIA_",
        extra="ignore"  # Allow extra environment variables
    )

class APIKeysSettings(BaseSettings):
    """External API keys configuration"""
    openai_api_key: Optional[str] = Field(default=None, env='OPENAI_API_KEY')
    anthropic_api_key: Optional[str] = Field(default=None, env='ANTHROPIC_API_KEY')
    
    # Vector Databases
    pinecone_api_key: Optional[str] = Field(default=None, env='PINECONE_API_KEY')
    pinecone_environment: str = Field(default="us-west1-gcp", env='PINECONE_ENVIRONMENT')
    pinecone_index_name: str = Field(default="sophia-index", env='PINECONE_INDEX_NAME')
    
    weaviate_url: Optional[str] = Field(default=None, env='WEAVIATE_URL')
    weaviate_api_key: Optional[str] = Field(default=None, env='WEAVIATE_API_KEY')
    
    # Business Integrations
    hubspot_api_key: Optional[str] = Field(default=None, env='HUBSPOT_API_KEY')
    gong_api_key: Optional[str] = Field(default=None, env='GONG_API_KEY')
    gong_api_secret: Optional[str] = Field(default=None, env='GONG_API_SECRET')
    
    slack_bot_token: Optional[str] = Field(default=None, env='SLACK_BOT_TOKEN')
    slack_app_token: Optional[str] = Field(default=None, env='SLACK_APP_TOKEN')
    slack_signing_secret: Optional[str] = Field(default=None, env='SLACK_SIGNING_SECRET')
    slack_webhook_url: Optional[str] = Field(default=None, env='SLACK_WEBHOOK_URL')
    
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"  # Allow extra environment variables
    )

class AgentSettings(BaseSettings):
    """Agent configuration"""
    max_concurrent_agents: int = Field(default=10, env='MAX_CONCURRENT_AGENTS')
    agent_timeout_seconds: int = Field(default=300, env='AGENT_TIMEOUT_SECONDS')
    agent_retry_attempts: int = Field(default=3, env='AGENT_RETRY_ATTEMPTS')
    
    orchestrator_port: int = Field(default=8001, env='ORCHESTRATOR_PORT')
    orchestrator_host: str = Field(default="0.0.0.0", env='ORCHESTRATOR_HOST')
    
    enable_call_analysis: bool = Field(default=True, env='ENABLE_CALL_ANALYSIS')
    enable_crm_sync: bool = Field(default=True, env='ENABLE_CRM_SYNC')
    enable_slack_notifications: bool = Field(default=True, env='ENABLE_SLACK_NOTIFICATIONS')
    
    model_config = ConfigDict(
        env_prefix="SOPHIA_",
        extra="ignore"  # Allow extra environment variables
    )

class MonitoringSettings(BaseSettings):
    """Monitoring configuration"""
    prometheus_enabled: bool = Field(default=True, env='PROMETHEUS_ENABLED')
    prometheus_port: int = Field(default=9090, env='PROMETHEUS_PORT')
    
    grafana_enabled: bool = Field(default=True, env='GRAFANA_ENABLED')
    grafana_port: int = Field(default=3000, env='GRAFANA_PORT')
    grafana_admin_password: str = Field(default="admin", env='GRAFANA_ADMIN_PASSWORD')
    
    log_level: str = Field(default="INFO", env='LOG_LEVEL')
    log_format: str = Field(default="json", env='LOG_FORMAT')
    
    metrics_retention_hours: int = Field(default=168, env='METRICS_RETENTION_HOURS')
    alert_email: Optional[str] = Field(default=None, env='ALERT_EMAIL')
    
    model_config = ConfigDict(
        env_prefix="SOPHIA_",
        extra="ignore"  # Allow extra environment variables
    )

class ServerSettings(BaseSettings):
    """Server configuration"""
    host: str = Field(default="0.0.0.0", env='HOST')
    port: int = Field(default=5000, env='PORT')
    workers: int = Field(default=4, env='WORKERS')
    
    debug: bool = Field(default=False, env='DEBUG')
    testing: bool = Field(default=False, env='TESTING')
    
    cors_origins: list[str] = Field(
        default=["*"],
        env='CORS_ORIGINS'
    )
    
    upload_max_size_mb: int = Field(default=16, env='UPLOAD_MAX_SIZE_MB')
    request_timeout: int = Field(default=300, env='REQUEST_TIMEOUT')
    
    @validator('debug')
    def validate_debug(cls, v):
        if v and ENV == "production":
            raise ValueError("Debug mode cannot be enabled in production")
        return v
    
    model_config = ConfigDict(
        env_prefix="SOPHIA_",
        extra="ignore"  # Allow extra environment variables
    )

class FeatureFlags(BaseSettings):
    """Feature flags for gradual rollout"""
    enable_hierarchical_agents: bool = Field(default=False, env='ENABLE_HIERARCHICAL_AGENTS')
    enable_n8n_workflows: bool = Field(default=False, env='ENABLE_N8N_WORKFLOWS')
    enable_advanced_analytics: bool = Field(default=True, env='ENABLE_ADVANCED_ANALYTICS')
    enable_auto_learning: bool = Field(default=False, env='ENABLE_AUTO_LEARNING')
    enable_multi_tenant: bool = Field(default=False, env='ENABLE_MULTI_TENANT')
    
    max_api_version: str = Field(default="v1", env='MAX_API_VERSION')
    
    model_config = ConfigDict(
        env_prefix="SOPHIA_FEATURE_",
        extra="ignore"  # Allow extra environment variables
    )

class Settings(BaseSettings):
    """Main settings aggregator"""
    # Environment
    environment: str = Field(default="development", env='SOPHIA_ENV')
    app_name: str = Field(default="Sophia AI - Pay Ready Assistant", env='APP_NAME')
    company_name: str = Field(default="Pay Ready", env='COMPANY_NAME')
    
    # Sub-configurations
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    api_keys: APIKeysSettings = Field(default_factory=APIKeysSettings)
    agents: AgentSettings = Field(default_factory=AgentSettings)
    monitoring: MonitoringSettings = Field(default_factory=MonitoringSettings)
    server: ServerSettings = Field(default_factory=ServerSettings)
    features: FeatureFlags = Field(default_factory=FeatureFlags)
    
    # Paths
    base_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent.parent)
    data_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent.parent / "data")
    logs_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent.parent / "logs")
    temp_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent.parent / "temp")
    
    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.environment.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.environment.lower() == "development"
    
    @property
    def is_testing(self) -> bool:
        """Check if running in test mode"""
        return self.environment.lower() == "test" or self.server.testing
    
    def validate_production_settings(self):
        """Validate critical settings for production"""
        if not self.is_production:
            return
        
        errors = []
        
        # Check critical API keys
        if not self.api_keys.openai_api_key:
            errors.append("OpenAI API key is required in production")
        
        if not self.api_keys.hubspot_api_key:
            errors.append("HubSpot API key is required in production")
        
        if not self.api_keys.gong_api_key:
            errors.append("Gong API key is required in production")
        
        if not self.api_keys.slack_bot_token:
            errors.append("Slack bot token is required in production")
        
        # Check security settings
        if self.security.secret_key == "change-me-in-production":
            errors.append("Secret key must be changed in production")
        
        if self.security.admin_password == "admin123":
            errors.append("Admin password must be changed in production")
        
        if errors:
            raise ValueError("Production validation failed:\n" + "\n".join(errors))
    
    def get_api_key(self, service: str) -> Optional[str]:
        """Get API key for a service"""
        service_map = {
            'openai': self.api_keys.openai_api_key,
            'anthropic': self.api_keys.anthropic_api_key,
            'pinecone': self.api_keys.pinecone_api_key,
            'weaviate': self.api_keys.weaviate_api_key,
            'hubspot': self.api_keys.hubspot_api_key,
            'gong': self.api_keys.gong_api_key,
            'slack': self.api_keys.slack_bot_token
        }
        return service_map.get(service.lower())
    
    def to_dict(self, include_secrets: bool = False) -> Dict[str, Any]:
        """Convert settings to dictionary"""
        data = self.dict()
        
        if not include_secrets:
            # Remove sensitive information
            if 'api_keys' in data:
                for key in data['api_keys']:
                    if 'key' in key or 'token' in key or 'secret' in key:
                        data['api_keys'][key] = "***REDACTED***"
            
            if 'security' in data:
                data['security']['secret_key'] = "***REDACTED***"
                data['security']['master_key'] = "***REDACTED***"
                data['security']['admin_password'] = "***REDACTED***"
            
            if 'database' in data:
                data['database']['postgres_password'] = "***REDACTED***"
                data['database']['redis_password'] = "***REDACTED***"
        
        return data
    
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"  # Allow extra environment variables
    )

# Singleton instance
settings = Settings()

# Validate production settings on import if in production
if settings.is_production:
    settings.validate_production_settings()

# Create required directories
settings.data_dir.mkdir(exist_ok=True)
settings.logs_dir.mkdir(exist_ok=True)
settings.temp_dir.mkdir(exist_ok=True)

# Export commonly used settings
DATABASE_URL = settings.database.postgres_url
REDIS_URL = settings.database.redis_url
SECRET_KEY = settings.security.secret_key
DEBUG = settings.server.debug

# For Flask compatibility
class Config:
    """Flask-compatible configuration class"""
    SECRET_KEY = settings.security.secret_key
    JWT_SECRET_KEY = settings.security.secret_key
    JWT_ALGORITHM = settings.security.jwt_algorithm
    JWT_ACCESS_TOKEN_EXPIRES = settings.security.jwt_expiration_hours * 3600
    
    SQLALCHEMY_DATABASE_URI = settings.database.postgres_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    REDIS_URL = settings.database.redis_url
    
    DEBUG = settings.server.debug
    TESTING = settings.server.testing
    
    # Add other Flask-specific settings as needed

if __name__ == "__main__":
    # Test configuration loading
    print(f"Environment: {settings.environment}")
    print(f"Database URL: {settings.database.postgres_url}")
    print(f"Redis URL: {settings.database.redis_url}")
    print(f"API Keys configured: {list(settings.api_keys.dict().keys())}")
    print(f"Features enabled: {[k for k, v in settings.features.dict().items() if v]}")
    
    # Print non-sensitive configuration
    import json
    print("\nFull configuration (secrets redacted):")
    print(json.dumps(settings.to_dict(), indent=2)) 