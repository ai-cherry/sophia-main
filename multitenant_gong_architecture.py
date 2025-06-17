#!/usr/bin/env python3
"""
Multi-tenant Gong OAuth Architecture
Scalable customer onboarding and management system
"""

import os
import json
import uuid
import asyncio
import asyncpg
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
import hashlib
import secrets
from flask import Flask, request, jsonify, session
from flask_cors import CORS
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class Customer:
    """Customer data class for multi-tenant architecture"""
    id: str
    company_name: str
    contact_email: str
    gong_workspace_id: str
    oauth_client_id: str
    oauth_client_secret: str
    subscription_tier: str  # basic, professional, enterprise
    features_enabled: List[str]
    created_at: datetime
    last_active: datetime
    status: str  # active, suspended, trial

@dataclass
class CustomerOAuthTokens:
    """OAuth tokens for customer"""
    customer_id: str
    access_token: str
    refresh_token: str
    expires_at: datetime
    scope: str
    token_type: str = "Bearer"

class MultiTenantGongManager:
    """
    Multi-tenant OAuth management for scalable customer onboarding
    """
    
    def __init__(self):
        # Database configuration
        self.db_config = {
            "host": "localhost",
            "port": 5432,
            "user": "postgres",
            "password": "password",
            "database": "sophia_enhanced"
        }
        
        # Gong OAuth configuration
        self.gong_base_url = "https://us-70092.api.gong.io"
        self.authorization_url = "https://app.gong.io/oauth2/authorize"
        self.token_url = "https://app.gong.io/oauth2/generate-customer-token"
        
        # Feature tiers
        self.feature_tiers = {
            "basic": [
                "conversation_search",
                "basic_analytics",
                "email_upload"
            ],
            "professional": [
                "conversation_search",
                "basic_analytics", 
                "email_upload",
                "conversation_transcripts",
                "interaction_statistics",
                "apartment_relevance_scoring"
            ],
            "enterprise": [
                "conversation_search",
                "basic_analytics",
                "email_upload", 
                "conversation_transcripts",
                "interaction_statistics",
                "apartment_relevance_scoring",
                "media_file_access",
                "real_time_webhooks",
                "advanced_ai_insights",
                "custom_integrations"
            ]
        }
    
    async def setup_multitenant_schema(self):
        """Create multi-tenant database schema"""
        
        try:
            conn = await asyncpg.connect(**self.db_config)
            
            # Create customers table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS customers (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    company_name VARCHAR(255) NOT NULL,
                    contact_email VARCHAR(255) UNIQUE NOT NULL,
                    gong_workspace_id VARCHAR(255),
                    oauth_client_id VARCHAR(255),
                    oauth_client_secret TEXT,
                    subscription_tier VARCHAR(50) DEFAULT 'basic',
                    features_enabled JSONB DEFAULT '[]'::jsonb,
                    api_key VARCHAR(255) UNIQUE,
                    webhook_url TEXT,
                    webhook_secret VARCHAR(255),
                    billing_info JSONB,
                    usage_stats JSONB DEFAULT '{}'::jsonb,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status VARCHAR(50) DEFAULT 'trial'
                )
            """)
            
            # Create customer OAuth tokens table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS customer_oauth_tokens (
                    id SERIAL PRIMARY KEY,
                    customer_id UUID REFERENCES customers(id) ON DELETE CASCADE,
                    access_token TEXT NOT NULL,
                    refresh_token TEXT,
                    expires_at TIMESTAMP NOT NULL,
                    scope TEXT,
                    token_type VARCHAR(50) DEFAULT 'Bearer',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(customer_id)
                )
            """)
            
            # Create customer data isolation tables
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS customer_conversations (
                    id SERIAL PRIMARY KEY,
                    customer_id UUID REFERENCES customers(id) ON DELETE CASCADE,
                    gong_call_id VARCHAR(255) NOT NULL,
                    conversation_data JSONB NOT NULL,
                    apartment_relevance_score FLOAT DEFAULT 0.0,
                    processed_features JSONB DEFAULT '[]'::jsonb,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(customer_id, gong_call_id)
                )
            """)
            
            # Create customer transcripts table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS customer_transcripts (
                    id SERIAL PRIMARY KEY,
                    customer_id UUID REFERENCES customers(id) ON DELETE CASCADE,
                    gong_call_id VARCHAR(255) NOT NULL,
                    transcript_data JSONB NOT NULL,
                    speakers JSONB,
                    apartment_keywords_count INTEGER DEFAULT 0,
                    ai_insights JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(customer_id, gong_call_id)
                )
            """)
            
            # Create customer media files table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS customer_media_files (
                    id SERIAL PRIMARY KEY,
                    customer_id UUID REFERENCES customers(id) ON DELETE CASCADE,
                    gong_call_id VARCHAR(255) NOT NULL,
                    media_url TEXT NOT NULL,
                    media_type VARCHAR(50),
                    local_file_path TEXT,
                    download_status VARCHAR(50) DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(customer_id, gong_call_id, media_url)
                )
            """)
            
            # Create customer webhooks table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS customer_webhook_events (
                    id SERIAL PRIMARY KEY,
                    customer_id UUID REFERENCES customers(id) ON DELETE CASCADE,
                    event_id VARCHAR(255) NOT NULL,
                    event_type VARCHAR(100) NOT NULL,
                    event_data JSONB NOT NULL,
                    processed BOOLEAN DEFAULT FALSE,
                    delivery_attempts INTEGER DEFAULT 0,
                    last_delivery_attempt TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(customer_id, event_id)
                )
            """)
            
            # Create customer usage tracking table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS customer_usage (
                    id SERIAL PRIMARY KEY,
                    customer_id UUID REFERENCES customers(id) ON DELETE CASCADE,
                    feature_name VARCHAR(100) NOT NULL,
                    usage_count INTEGER DEFAULT 0,
                    usage_date DATE DEFAULT CURRENT_DATE,
                    metadata JSONB,
                    UNIQUE(customer_id, feature_name, usage_date)
                )
            """)
            
            # Create indexes for performance
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_customers_email ON customers(contact_email)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_customers_status ON customers(status)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_customer_conversations_customer_id ON customer_conversations(customer_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_customer_conversations_relevance ON customer_conversations(apartment_relevance_score)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_customer_transcripts_customer_id ON customer_transcripts(customer_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_customer_media_customer_id ON customer_media_files(customer_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_customer_webhooks_customer_id ON customer_webhook_events(customer_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_customer_usage_customer_id ON customer_usage(customer_id)")
            
            await conn.close()
            
            logger.info("Multi-tenant database schema created successfully")
            
        except Exception as e:
            logger.error(f"Error setting up multi-tenant schema: {str(e)}")
            raise
    
    async def create_customer(self, company_name: str, contact_email: str, subscription_tier: str = "trial") -> Customer:
        """Create new customer account"""
        
        try:
            conn = await asyncpg.connect(**self.db_config)
            
            # Generate API key
            api_key = f"pk_{secrets.token_urlsafe(32)}"
            webhook_secret = secrets.token_urlsafe(32)
            
            # Get features for tier
            features = self.feature_tiers.get(subscription_tier, self.feature_tiers["basic"])
            
            # Insert customer
            customer_id = await conn.fetchval("""
                INSERT INTO customers 
                (company_name, contact_email, subscription_tier, features_enabled, api_key, webhook_secret, status)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING id
            """,
                company_name,
                contact_email,
                subscription_tier,
                json.dumps(features),
                api_key,
                webhook_secret,
                "trial" if subscription_tier == "trial" else "active"
            )
            
            await conn.close()
            
            # Create customer object
            customer = Customer(
                id=str(customer_id),
                company_name=company_name,
                contact_email=contact_email,
                gong_workspace_id="",
                oauth_client_id="",
                oauth_client_secret="",
                subscription_tier=subscription_tier,
                features_enabled=features,
                created_at=datetime.utcnow(),
                last_active=datetime.utcnow(),
                status="trial" if subscription_tier == "trial" else "active"
            )
            
            logger.info(f"Created customer: {company_name} ({customer_id})")
            
            return customer
            
        except Exception as e:
            logger.error(f"Error creating customer: {str(e)}")
            raise
    
    async def get_customer_by_email(self, email: str) -> Optional[Customer]:
        """Get customer by email address"""
        
        try:
            conn = await asyncpg.connect(**self.db_config)
            
            row = await conn.fetchrow("""
                SELECT id, company_name, contact_email, gong_workspace_id, oauth_client_id, 
                       oauth_client_secret, subscription_tier, features_enabled, created_at, 
                       last_active, status
                FROM customers
                WHERE contact_email = $1
            """, email)
            
            await conn.close()
            
            if row:
                return Customer(
                    id=str(row["id"]),
                    company_name=row["company_name"],
                    contact_email=row["contact_email"],
                    gong_workspace_id=row["gong_workspace_id"] or "",
                    oauth_client_id=row["oauth_client_id"] or "",
                    oauth_client_secret=row["oauth_client_secret"] or "",
                    subscription_tier=row["subscription_tier"],
                    features_enabled=json.loads(row["features_enabled"]),
                    created_at=row["created_at"],
                    last_active=row["last_active"],
                    status=row["status"]
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting customer by email: {str(e)}")
            return None
    
    async def get_customer_by_api_key(self, api_key: str) -> Optional[Customer]:
        """Get customer by API key"""
        
        try:
            conn = await asyncpg.connect(**self.db_config)
            
            row = await conn.fetchrow("""
                SELECT id, company_name, contact_email, gong_workspace_id, oauth_client_id, 
                       oauth_client_secret, subscription_tier, features_enabled, created_at, 
                       last_active, status
                FROM customers
                WHERE api_key = $1 AND status = 'active'
            """, api_key)
            
            await conn.close()
            
            if row:
                return Customer(
                    id=str(row["id"]),
                    company_name=row["company_name"],
                    contact_email=row["contact_email"],
                    gong_workspace_id=row["gong_workspace_id"] or "",
                    oauth_client_id=row["oauth_client_id"] or "",
                    oauth_client_secret=row["oauth_client_secret"] or "",
                    subscription_tier=row["subscription_tier"],
                    features_enabled=json.loads(row["features_enabled"]),
                    created_at=row["created_at"],
                    last_active=row["last_active"],
                    status=row["status"]
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting customer by API key: {str(e)}")
            return None
    
    async def update_customer_oauth_config(self, customer_id: str, gong_workspace_id: str, 
                                         oauth_client_id: str, oauth_client_secret: str):
        """Update customer OAuth configuration"""
        
        try:
            conn = await asyncpg.connect(**self.db_config)
            
            await conn.execute("""
                UPDATE customers
                SET gong_workspace_id = $2,
                    oauth_client_id = $3,
                    oauth_client_secret = $4,
                    last_active = CURRENT_TIMESTAMP
                WHERE id = $1
            """,
                uuid.UUID(customer_id),
                gong_workspace_id,
                oauth_client_id,
                oauth_client_secret
            )
            
            await conn.close()
            
            logger.info(f"Updated OAuth config for customer: {customer_id}")
            
        except Exception as e:
            logger.error(f"Error updating customer OAuth config: {str(e)}")
            raise
    
    async def store_customer_oauth_tokens(self, customer_id: str, tokens: CustomerOAuthTokens):
        """Store OAuth tokens for customer"""
        
        try:
            conn = await asyncpg.connect(**self.db_config)
            
            await conn.execute("""
                INSERT INTO customer_oauth_tokens 
                (customer_id, access_token, refresh_token, expires_at, scope, token_type)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (customer_id) DO UPDATE SET
                    access_token = EXCLUDED.access_token,
                    refresh_token = EXCLUDED.refresh_token,
                    expires_at = EXCLUDED.expires_at,
                    scope = EXCLUDED.scope,
                    token_type = EXCLUDED.token_type,
                    updated_at = CURRENT_TIMESTAMP
            """,
                uuid.UUID(customer_id),
                tokens.access_token,
                tokens.refresh_token,
                tokens.expires_at,
                tokens.scope,
                tokens.token_type
            )
            
            await conn.close()
            
        except Exception as e:
            logger.error(f"Error storing customer OAuth tokens: {str(e)}")
            raise
    
    async def get_customer_oauth_tokens(self, customer_id: str) -> Optional[CustomerOAuthTokens]:
        """Get OAuth tokens for customer"""
        
        try:
            conn = await asyncpg.connect(**self.db_config)
            
            row = await conn.fetchrow("""
                SELECT customer_id, access_token, refresh_token, expires_at, scope, token_type
                FROM customer_oauth_tokens
                WHERE customer_id = $1
            """, uuid.UUID(customer_id))
            
            await conn.close()
            
            if row:
                return CustomerOAuthTokens(
                    customer_id=str(row["customer_id"]),
                    access_token=row["access_token"],
                    refresh_token=row["refresh_token"],
                    expires_at=row["expires_at"],
                    scope=row["scope"],
                    token_type=row["token_type"]
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting customer OAuth tokens: {str(e)}")
            return None
    
    async def check_feature_access(self, customer_id: str, feature_name: str) -> bool:
        """Check if customer has access to specific feature"""
        
        try:
            conn = await asyncpg.connect(**self.db_config)
            
            features_json = await conn.fetchval("""
                SELECT features_enabled
                FROM customers
                WHERE id = $1 AND status = 'active'
            """, uuid.UUID(customer_id))
            
            await conn.close()
            
            if features_json:
                features = json.loads(features_json)
                return feature_name in features
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking feature access: {str(e)}")
            return False
    
    async def track_feature_usage(self, customer_id: str, feature_name: str, metadata: Dict = None):
        """Track feature usage for billing and analytics"""
        
        try:
            conn = await asyncpg.connect(**self.db_config)
            
            await conn.execute("""
                INSERT INTO customer_usage (customer_id, feature_name, usage_count, metadata)
                VALUES ($1, $2, 1, $3)
                ON CONFLICT (customer_id, feature_name, usage_date) DO UPDATE SET
                    usage_count = customer_usage.usage_count + 1,
                    metadata = EXCLUDED.metadata
            """,
                uuid.UUID(customer_id),
                feature_name,
                json.dumps(metadata or {})
            )
            
            await conn.close()
            
        except Exception as e:
            logger.error(f"Error tracking feature usage: {str(e)}")
    
    async def get_customer_usage_stats(self, customer_id: str, days: int = 30) -> Dict[str, Any]:
        """Get customer usage statistics"""
        
        try:
            conn = await asyncpg.connect(**self.db_config)
            
            # Get usage stats for the last N days
            rows = await conn.fetch("""
                SELECT feature_name, SUM(usage_count) as total_usage, COUNT(*) as days_used
                FROM customer_usage
                WHERE customer_id = $1 
                AND usage_date >= CURRENT_DATE - INTERVAL '%s days'
                GROUP BY feature_name
                ORDER BY total_usage DESC
            """ % days, uuid.UUID(customer_id))
            
            await conn.close()
            
            usage_stats = {}
            for row in rows:
                usage_stats[row["feature_name"]] = {
                    "total_usage": row["total_usage"],
                    "days_used": row["days_used"],
                    "avg_daily_usage": round(row["total_usage"] / max(row["days_used"], 1), 2)
                }
            
            return usage_stats
            
        except Exception as e:
            logger.error(f"Error getting customer usage stats: {str(e)}")
            return {}
    
    async def upgrade_customer_subscription(self, customer_id: str, new_tier: str):
        """Upgrade customer subscription tier"""
        
        try:
            conn = await asyncpg.connect(**self.db_config)
            
            # Get new features for tier
            new_features = self.feature_tiers.get(new_tier, self.feature_tiers["basic"])
            
            await conn.execute("""
                UPDATE customers
                SET subscription_tier = $2,
                    features_enabled = $3,
                    status = 'active',
                    last_active = CURRENT_TIMESTAMP
                WHERE id = $1
            """,
                uuid.UUID(customer_id),
                new_tier,
                json.dumps(new_features)
            )
            
            await conn.close()
            
            logger.info(f"Upgraded customer {customer_id} to {new_tier}")
            
        except Exception as e:
            logger.error(f"Error upgrading customer subscription: {str(e)}")
            raise

# Flask application for multi-tenant management
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", secrets.token_hex(32))
CORS(app, origins=["http://localhost:3000", "http://localhost:5173", "https://*.vercel.app"])

# Initialize multi-tenant manager
multitenant_manager = MultiTenantGongManager()

@app.route("/api/customers/register", methods=["POST"])
async def register_customer():
    """Register new customer"""
    
    try:
        data = request.get_json()
        
        company_name = data.get("company_name")
        contact_email = data.get("contact_email")
        subscription_tier = data.get("subscription_tier", "trial")
        
        if not company_name or not contact_email:
            return jsonify({
                "error": "Company name and contact email are required"
            }), 400
        
        # Check if customer already exists
        existing_customer = await multitenant_manager.get_customer_by_email(contact_email)
        if existing_customer:
            return jsonify({
                "error": "Customer with this email already exists"
            }), 409
        
        # Create new customer
        customer = await multitenant_manager.create_customer(
            company_name, contact_email, subscription_tier
        )
        
        return jsonify({
            "success": True,
            "customer": {
                "id": customer.id,
                "company_name": customer.company_name,
                "contact_email": customer.contact_email,
                "subscription_tier": customer.subscription_tier,
                "features_enabled": customer.features_enabled,
                "status": customer.status
            },
            "message": "Customer registered successfully"
        })
        
    except Exception as e:
        logger.error(f"Error registering customer: {str(e)}")
        return jsonify({
            "error": "Registration failed",
            "details": str(e)
        }), 500

@app.route("/api/customers/<customer_id>/oauth/setup", methods=["POST"])
async def setup_customer_oauth(customer_id):
    """Setup OAuth configuration for customer"""
    
    try:
        data = request.get_json()
        
        gong_workspace_id = data.get("gong_workspace_id")
        oauth_client_id = data.get("oauth_client_id")
        oauth_client_secret = data.get("oauth_client_secret")
        
        if not all([gong_workspace_id, oauth_client_id, oauth_client_secret]):
            return jsonify({
                "error": "All OAuth configuration fields are required"
            }), 400
        
        # Update customer OAuth configuration
        await multitenant_manager.update_customer_oauth_config(
            customer_id, gong_workspace_id, oauth_client_id, oauth_client_secret
        )
        
        return jsonify({
            "success": True,
            "message": "OAuth configuration updated successfully",
            "authorization_url": f"/api/customers/{customer_id}/oauth/authorize"
        })
        
    except Exception as e:
        logger.error(f"Error setting up customer OAuth: {str(e)}")
        return jsonify({
            "error": "OAuth setup failed",
            "details": str(e)
        }), 500

@app.route("/api/customers/<customer_id>/features")
async def get_customer_features(customer_id):
    """Get customer features and usage"""
    
    try:
        # Get customer
        conn = await asyncpg.connect(**multitenant_manager.db_config)
        
        customer_row = await conn.fetchrow("""
            SELECT subscription_tier, features_enabled, status
            FROM customers
            WHERE id = $1
        """, uuid.UUID(customer_id))
        
        await conn.close()
        
        if not customer_row:
            return jsonify({
                "error": "Customer not found"
            }), 404
        
        # Get usage stats
        usage_stats = await multitenant_manager.get_customer_usage_stats(customer_id)
        
        return jsonify({
            "customer_id": customer_id,
            "subscription_tier": customer_row["subscription_tier"],
            "features_enabled": json.loads(customer_row["features_enabled"]),
            "status": customer_row["status"],
            "usage_stats": usage_stats,
            "available_tiers": list(multitenant_manager.feature_tiers.keys())
        })
        
    except Exception as e:
        logger.error(f"Error getting customer features: {str(e)}")
        return jsonify({
            "error": "Failed to get customer features",
            "details": str(e)
        }), 500

@app.route("/api/customers/<customer_id>/upgrade", methods=["POST"])
async def upgrade_customer(customer_id):
    """Upgrade customer subscription"""
    
    try:
        data = request.get_json()
        new_tier = data.get("subscription_tier")
        
        if new_tier not in multitenant_manager.feature_tiers:
            return jsonify({
                "error": f"Invalid subscription tier: {new_tier}"
            }), 400
        
        # Upgrade customer
        await multitenant_manager.upgrade_customer_subscription(customer_id, new_tier)
        
        return jsonify({
            "success": True,
            "message": f"Customer upgraded to {new_tier}",
            "new_features": multitenant_manager.feature_tiers[new_tier]
        })
        
    except Exception as e:
        logger.error(f"Error upgrading customer: {str(e)}")
        return jsonify({
            "error": "Upgrade failed",
            "details": str(e)
        }), 500

@app.route("/api/health")
def health_check():
    """Health check endpoint"""
    
    return jsonify({
        "status": "healthy",
        "service": "Multi-tenant Gong OAuth Manager",
        "timestamp": datetime.utcnow().isoformat(),
        "features": {
            "customer_registration": "implemented",
            "oauth_management": "implemented", 
            "feature_access_control": "implemented",
            "usage_tracking": "implemented",
            "subscription_management": "implemented"
        }
    })

# Test the multi-tenant system
async def test_multitenant_system():
    """Test multi-tenant functionality"""
    
    # Setup schema
    await multitenant_manager.setup_multitenant_schema()
    
    # Create test customer
    customer = await multitenant_manager.create_customer(
        "Test Apartment Management",
        "test@apartments.com",
        "professional"
    )
    
    # Test feature access
    has_transcripts = await multitenant_manager.check_feature_access(
        customer.id, "conversation_transcripts"
    )
    
    has_webhooks = await multitenant_manager.check_feature_access(
        customer.id, "real_time_webhooks"
    )
    
    # Track usage
    await multitenant_manager.track_feature_usage(
        customer.id, "conversation_search", {"query": "apartment"}
    )
    
    # Get usage stats
    usage_stats = await multitenant_manager.get_customer_usage_stats(customer.id)
    
    return {
        "schema_created": True,
        "customer_created": customer.company_name,
        "has_transcripts": has_transcripts,
        "has_webhooks": has_webhooks,
        "usage_tracked": len(usage_stats) > 0
    }

if __name__ == "__main__":
    # Run test
    result = asyncio.run(test_multitenant_system())
    print(f"Multi-tenant test results: {json.dumps(result, indent=2)}")
    
    # Run Flask application
    app.run(host="0.0.0.0", port=5002, debug=True)

