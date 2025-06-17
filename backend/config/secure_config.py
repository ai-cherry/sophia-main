"""
Sophia AI - Secure Configuration Management
Centralized configuration that pulls from environment variables and Pulumi ESC
"""

import os
from typing import Optional, Dict, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class SecureAPIConfig:
    """Secure API configuration management"""
    
    # AI/ML Services
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    huggingface_api_key: Optional[str] = None
    cohere_api_key: Optional[str] = None
    replicate_api_key: Optional[str] = None
    together_api_key: Optional[str] = None
    
    # Gateway Services
    portkey_api_key: Optional[str] = None
    openrouter_api_key: Optional[str] = None
    kong_access_token: Optional[str] = None
    arize_api_key: Optional[str] = None
    
    # Business Intelligence
    hubspot_api_key: Optional[str] = None
    gong_access_key: Optional[str] = None
    gong_client_secret: Optional[str] = None
    salesforce_api_key: Optional[str] = None
    looker_api_key: Optional[str] = None
    
    # Apartment Industry APIs
    yardi_api_key: Optional[str] = None
    yardi_api_secret: Optional[str] = None
    realpage_api_key: Optional[str] = None
    appfolio_api_key: Optional[str] = None
    entrata_api_key: Optional[str] = None
    costar_api_key: Optional[str] = None
    
    # Vector Databases
    pinecone_api_key: Optional[str] = None
    pinecone_environment: str = "us-west-2"
    weaviate_url: Optional[str] = None
    weaviate_api_key: Optional[str] = None
    
    # Communication
    slack_bot_token: Optional[str] = None
    slack_app_token: Optional[str] = None
    slack_signing_secret: Optional[str] = None
    twilio_account_sid: Optional[str] = None
    twilio_auth_token: Optional[str] = None
    
    # Analytics
    google_analytics_key: Optional[str] = None
    mixpanel_api_key: Optional[str] = None
    amplitude_api_key: Optional[str] = None
    segment_write_key: Optional[str] = None
    
    # Payment Processing
    stripe_api_key: Optional[str] = None
    stripe_webhook_secret: Optional[str] = None
    paypal_client_id: Optional[str] = None
    paypal_client_secret: Optional[str] = None
    plaid_client_id: Optional[str] = None
    plaid_secret: Optional[str] = None
    
    # Infrastructure
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    gcp_credentials_json: Optional[str] = None
    azure_subscription_id: Optional[str] = None
    lambda_labs_api_key: Optional[str] = None
    
    # Monitoring
    datadog_api_key: Optional[str] = None
    datadog_app_key: Optional[str] = None
    sentry_dsn: Optional[str] = None
    new_relic_api_key: Optional[str] = None
    
    # Development Tools
    github_token: Optional[str] = None
    gitlab_token: Optional[str] = None
    jira_api_token: Optional[str] = None
    linear_api_key: Optional[str] = None
    notion_api_key: Optional[str] = None
    
    @classmethod
    def from_environment(cls) -> 'SecureAPIConfig':
        """Load configuration from environment variables"""
        config = cls()
        
        # Map environment variables to config attributes
        env_mapping = {
            # AI/ML Services
            'OPENAI_API_KEY': 'openai_api_key',
            'ANTHROPIC_API_KEY': 'anthropic_api_key',
            'HUGGINGFACE_API_KEY': 'huggingface_api_key',
            'COHERE_API_KEY': 'cohere_api_key',
            'REPLICATE_API_KEY': 'replicate_api_key',
            'TOGETHER_API_KEY': 'together_api_key',
            
            # Gateway Services
            'PORTKEY_API_KEY': 'portkey_api_key',
            'OPENROUTER_API_KEY': 'openrouter_api_key',
            'KONG_ACCESS_TOKEN': 'kong_access_token',
            'ARIZE_API_KEY': 'arize_api_key',
            
            # Business Intelligence
            'HUBSPOT_API_KEY': 'hubspot_api_key',
            'GONG_ACCESS_KEY': 'gong_access_key',
            'GONG_CLIENT_SECRET': 'gong_client_secret',
            'SALESFORCE_API_KEY': 'salesforce_api_key',
            'LOOKER_API_KEY': 'looker_api_key',
            
            # Apartment Industry
            'YARDI_API_KEY': 'yardi_api_key',
            'YARDI_API_SECRET': 'yardi_api_secret',
            'REALPAGE_API_KEY': 'realpage_api_key',
            'APPFOLIO_API_KEY': 'appfolio_api_key',
            'ENTRATA_API_KEY': 'entrata_api_key',
            'COSTAR_API_KEY': 'costar_api_key',
            
            # Vector Databases
            'PINECONE_API_KEY': 'pinecone_api_key',
            'PINECONE_ENVIRONMENT': 'pinecone_environment',
            'WEAVIATE_URL': 'weaviate_url',
            'WEAVIATE_API_KEY': 'weaviate_api_key',
            
            # Communication
            'SLACK_BOT_TOKEN': 'slack_bot_token',
            'SLACK_APP_TOKEN': 'slack_app_token',
            'SLACK_SIGNING_SECRET': 'slack_signing_secret',
            'TWILIO_ACCOUNT_SID': 'twilio_account_sid',
            'TWILIO_AUTH_TOKEN': 'twilio_auth_token',
            
            # Analytics
            'GOOGLE_ANALYTICS_KEY': 'google_analytics_key',
            'MIXPANEL_API_KEY': 'mixpanel_api_key',
            'AMPLITUDE_API_KEY': 'amplitude_api_key',
            'SEGMENT_WRITE_KEY': 'segment_write_key',
            
            # Payment Processing
            'STRIPE_API_KEY': 'stripe_api_key',
            'STRIPE_WEBHOOK_SECRET': 'stripe_webhook_secret',
            'PAYPAL_CLIENT_ID': 'paypal_client_id',
            'PAYPAL_CLIENT_SECRET': 'paypal_client_secret',
            'PLAID_CLIENT_ID': 'plaid_client_id',
            'PLAID_SECRET': 'plaid_secret',
            
            # Infrastructure
            'AWS_ACCESS_KEY_ID': 'aws_access_key_id',
            'AWS_SECRET_ACCESS_KEY': 'aws_secret_access_key',
            'GCP_CREDENTIALS_JSON': 'gcp_credentials_json',
            'AZURE_SUBSCRIPTION_ID': 'azure_subscription_id',
            'LAMBDA_LABS_API_KEY': 'lambda_labs_api_key',
            
            # Monitoring
            'DATADOG_API_KEY': 'datadog_api_key',
            'DATADOG_APP_KEY': 'datadog_app_key',
            'SENTRY_DSN': 'sentry_dsn',
            'NEW_RELIC_API_KEY': 'new_relic_api_key',
            
            # Development Tools
            'GITHUB_TOKEN': 'github_token',
            'GITLAB_TOKEN': 'gitlab_token',
            'JIRA_API_TOKEN': 'jira_api_token',
            'LINEAR_API_KEY': 'linear_api_key',
            'NOTION_API_KEY': 'notion_api_key',
        }
        
        # Load from environment
        for env_var, attr_name in env_mapping.items():
            value = os.getenv(env_var)
            if value:
                setattr(config, attr_name, value)
        
        return config
    
    def get_available_apis(self) -> Dict[str, bool]:
        """Get a dictionary of which APIs are configured"""
        available = {}
        for attr_name in dir(self):
            if not attr_name.startswith('_') and attr_name.endswith('_key'):
                value = getattr(self, attr_name)
                api_name = attr_name.replace('_api_key', '').replace('_', ' ').title()
                available[api_name] = bool(value)
        return available
    
    def get_api_count(self) -> Dict[str, int]:
        """Get count of configured vs total APIs"""
        total = 0
        configured = 0
        
        for attr_name in dir(self):
            if not attr_name.startswith('_') and (attr_name.endswith('_key') or attr_name.endswith('_token')):
                total += 1
                if getattr(self, attr_name):
                    configured += 1
        
        return {
            'total': total,
            'configured': configured,
            'percentage': round((configured / total) * 100, 2) if total > 0 else 0
        }
    
    def validate_critical_apis(self) -> Dict[str, Any]:
        """Validate that critical APIs are configured"""
        critical_apis = {
            'ai_provider': any([
                self.openai_api_key,
                self.anthropic_api_key,
                self.portkey_api_key and self.openrouter_api_key
            ]),
            'vector_database': any([
                self.pinecone_api_key,
                self.weaviate_api_key
            ]),
            'business_intelligence': any([
                self.hubspot_api_key,
                self.gong_api_key,
                self.salesforce_api_key
            ]),
            'monitoring': any([
                self.datadog_api_key,
                self.sentry_dsn,
                self.new_relic_api_key
            ])
        }
        
        all_critical_configured = all(critical_apis.values())
        
        return {
            'all_configured': all_critical_configured,
            'critical_apis': critical_apis,
            'missing': [k for k, v in critical_apis.items() if not v]
        }

# Global instance
_secure_config: Optional[SecureAPIConfig] = None

def get_secure_config() -> SecureAPIConfig:
    """Get or create the secure configuration singleton"""
    global _secure_config
    if _secure_config is None:
        _secure_config = SecureAPIConfig.from_environment()
        
        # Log configuration status
        api_count = _secure_config.get_api_count()
        logger.info(f"Secure configuration loaded: {api_count['configured']}/{api_count['total']} APIs configured ({api_count['percentage']}%)")
        
        # Validate critical APIs
        validation = _secure_config.validate_critical_apis()
        if not validation['all_configured']:
            logger.warning(f"Missing critical API categories: {validation['missing']}")
    
    return _secure_config 