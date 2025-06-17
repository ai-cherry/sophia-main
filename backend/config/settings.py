"""
Sophia AI - Configuration Management
Centralized configuration using environment variables and Pydantic

This module provides a unified configuration system for all Sophia AI components.
"""

from pydantic_settings import BaseSettings
from pydantic import Field, validator, ConfigDict
from typing import Optional, Dict, Any, List
import os
from pathlib import Path
from functools import lru_cache

# Determine environment
ENV = os.getenv('SOPHIA_ENV', 'development')

class DatabaseSettings(BaseSettings):
    """Database configuration"""
    postgres_host: str = Field(default="localhost", env='POSTGRES_HOST')
    postgres_port: int = Field(default=5432, env='POSTGRES_PORT')
    postgres_user: str = Field(default="sophia", env='POSTGRES_USER')
    postgres_password: str = Field(env='POSTGRES_PASSWORD')
    postgres_db: str = Field(default="sophia_payready", env='POSTGRES_DB')
    
    redis_host: str = Field(default="localhost", env='REDIS_HOST')
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
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"
    
    model_config = ConfigDict(
        env_prefix="SOPHIA_",
        extra="ignore"  # Allow extra environment variables
    )

class SecuritySettings(BaseSettings):
    """Security configuration"""
    secret_key: str = Field(default_factory=lambda: os.urandom(32).hex(), env='SECRET_KEY')
    master_key: Optional[str] = Field(default=None, env='SOPHIA_MASTER_KEY')
    jwt_algorithm: str = Field(default="HS256", env='JWT_ALGORITHM')
    jwt_expiration_hours: int = Field(default=24, env='JWT_EXPIRATION_HOURS')
    
    admin_username: str = Field(default="admin", env='ADMIN_USERNAME')
    admin_password: str = Field(env='ADMIN_PASSWORD')
    
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
    # LLM Gateway (Primary)
    llm_gateway: str = Field(default="portkey", env='LLM_GATEWAY')  # portkey or openrouter
    portkey_api_key: Optional[str] = Field(default=None, env='PORTKEY_API_KEY')
    openrouter_api_key: Optional[str] = Field(default=None, env='OPENROUTER_API_KEY')
    
    # Direct LLM APIs (used as fallbacks or directly)
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

    @property
    def has_ai_provider(self) -> bool:
        """Check if at least one AI provider is configured"""
        # Check for gateway first (preferred)
        if self.llm_gateway == "portkey" and self.portkey_api_key and self.openrouter_api_key:
            return True
        # Check for direct API keys
        return bool(self.openai_api_key or self.anthropic_api_key)
    
    @property
    def has_vector_db(self) -> bool:
        """Check if any vector database is configured"""
        return bool(self.pinecone_api_key or self.weaviate_api_key)
    
    @property
    def has_hubspot(self) -> bool:
        """Check if HubSpot is configured"""
        return bool(self.hubspot_api_key)
    
    @property
    def has_gong(self) -> bool:
        """Check if Gong is configured"""
        return bool(self.gong_api_key and self.gong_api_secret)
    
    @property
    def has_slack(self) -> bool:
        """Check if Slack is configured"""
        return bool(self.slack_bot_token and self.slack_signing_secret)

class AgentSettings(BaseSettings):
    """Agent configuration"""
    max_concurrent_agents: int = Field(default=10, env='SOPHIA_MAX_CONCURRENT_AGENTS')
    agent_timeout_seconds: int = Field(default=300, env='SOPHIA_AGENT_TIMEOUT_SECONDS')
    agent_retry_attempts: int = Field(default=3, env='SOPHIA_AGENT_RETRY_ATTEMPTS')
    
    orchestrator_port: int = Field(default=8001, env='ORCHESTRATOR_PORT')
    orchestrator_host: str = Field(default="0.0.0.0", env='ORCHESTRATOR_HOST')
    
    enable_call_analysis: bool = Field(default=True, env='SOPHIA_ENABLE_CALL_ANALYSIS')
    enable_crm_sync: bool = Field(default=True, env='SOPHIA_ENABLE_CRM_SYNC')
    enable_slack_notifications: bool = Field(default=True, env='SOPHIA_ENABLE_SLACK_NOTIFICATIONS')
    
    model_config = ConfigDict(
        env_prefix="SOPHIA_",
        extra="ignore"  # Allow extra environment variables
    )

class MonitoringSettings(BaseSettings):
    """Monitoring configuration"""
    prometheus_enabled: bool = Field(default=False, env='SOPHIA_PROMETHEUS_ENABLED')
    prometheus_port: int = Field(default=9090, env='PROMETHEUS_PORT')
    
    grafana_enabled: bool = Field(default=False, env='SOPHIA_GRAFANA_ENABLED')
    grafana_port: int = Field(default=3000, env='GRAFANA_PORT')
    grafana_admin_password: str = Field(env='GRAFANA_ADMIN_PASSWORD')
    
    log_level: str = Field(default="INFO", env='SOPHIA_LOG_LEVEL')
    log_format: str = Field(default="json", env='SOPHIA_LOG_FORMAT')
    
    metrics_retention_hours: int = Field(default=168, env='SOPHIA_METRICS_RETENTION_HOURS')
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
        default=["http://localhost:3000", "http://localhost:5000"],
        env='CORS_ORIGINS'
    )
    
    upload_max_size_mb: int = Field(default=16)
    request_timeout: int = Field(default=300)
    
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
    enable_hierarchical_agents: bool = Field(default=False)
    enable_n8n_workflows: bool = Field(default=False)
    enable_advanced_analytics: bool = Field(default=True)
    enable_auto_learning: bool = Field(default=False)
    enable_multi_tenant: bool = Field(default=False)
    
    max_api_version: str = Field(default="v1")
    
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
        """Validate critical settings and return warnings"""
        warnings = []
        
        # Check for at least one AI provider
        if not self.api_keys.has_ai_provider:
            warnings.append("No AI provider configured (OpenAI or Anthropic). AI features will be disabled.")
        
        # Production-specific warnings
        if self.is_production:
            if self.security.secret_key == "change-me-in-production":
                warnings.append("Secret key must be changed in production!")
            
            if not self.security.admin_password:
                warnings.append("Admin password must be set in production!")
            
            if len(self.security.secret_key) < 32:
                warnings.append("SECRET_KEY should be at least 32 characters in production")
        
        # Feature dependency warnings
        if self.agents.enable_call_analysis and not self.api_keys.has_gong:
            warnings.append("Call analysis enabled but Gong API not configured")
        
        if self.agents.enable_crm_sync and not self.api_keys.has_hubspot:
            warnings.append("CRM sync enabled but HubSpot API not configured")
        
        if self.agents.enable_slack_notifications and not self.api_keys.has_slack:
            warnings.append("Slack notifications enabled but Slack API not configured")
        
        return warnings
    
    def get_enabled_features(self) -> Dict[str, bool]:
        """Get a summary of enabled features based on available API keys"""
        return {
            "ai_enabled": self.api_keys.has_ai_provider,
            "vector_search": self.api_keys.has_vector_db,
            "hubspot_integration": self.api_keys.has_hubspot,
            "gong_integration": self.api_keys.has_gong,
            "slack_integration": self.api_keys.has_slack,
            "call_analysis": self.agents.enable_call_analysis and self.api_keys.has_gong,
            "crm_sync": self.agents.enable_crm_sync and self.api_keys.has_hubspot,
            "notifications": self.agents.enable_slack_notifications and self.api_keys.has_slack,
            "monitoring": self.monitoring.prometheus_enabled,
            "advanced_analytics": self.features.enable_advanced_analytics,
        }
    
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

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    settings = Settings()
    
    # Log configuration warnings
    warnings = settings.validate_production_settings()
    if warnings:
        import logging
        logger = logging.getLogger(__name__)
        for warning in warnings:
            logger.warning(f"Configuration warning: {warning}")
    
    # Log enabled features
    features = settings.get_enabled_features()
    enabled = [k for k, v in features.items() if v]
    if enabled:
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Enabled features: {', '.join(enabled)}")
    
    return settings

# Singleton instance
settings = get_settings()

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