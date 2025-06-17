#!/usr/bin/env python3
"""
Enhanced Sophia Database Schema Deployment
Fixed version with proper SQL syntax
"""

import asyncio
import asyncpg
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def deploy_enhanced_schema():
    """Deploy enhanced database schema with proper SQL syntax"""
    
    # Database connection
    db_config = {
        'host': os.getenv('POSTGRES_HOST', 'localhost'),
        'port': int(os.getenv('POSTGRES_PORT', 5432)),
        'database': os.getenv('POSTGRES_DB', 'sophia_unified'),
        'user': os.getenv('POSTGRES_USER', 'sophia'),
        'password': os.getenv('POSTGRES_PASSWORD', 'sophia_secure_password')
    }
    
    logger.info("Connecting to database...")
    conn = await asyncpg.connect(**db_config)
    
    try:
        logger.info("Creating base tables...")
        
        # Create enum types first
        await conn.execute("""
            DO $$ BEGIN
                CREATE TYPE deal_stage_enum AS ENUM (
                    'lead', 'qualified', 'proposal', 'negotiation', 
                    'closed_won', 'closed_lost', 'on_hold'
                );
            EXCEPTION
                WHEN duplicate_object THEN null;
            END $$;
        """)
        
        # Create unified_contacts table if not exists
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS unified_contacts (
                id BIGSERIAL PRIMARY KEY,
                email VARCHAR(255) UNIQUE,
                first_name VARCHAR(100),
                last_name VARCHAR(100),
                company_name VARCHAR(200),
                title VARCHAR(200),
                phone VARCHAR(50),
                source_system VARCHAR(50) NOT NULL,
                source_record_id VARCHAR(100) NOT NULL,
                apartment_portfolio_size INTEGER,
                property_management_software VARCHAR(100),
                annual_revenue_estimated DECIMAL(15,2),
                employee_count_estimated INTEGER,
                customer_segment VARCHAR(100),
                lead_score DECIMAL(3,2) CHECK (lead_score >= 0 AND lead_score <= 1),
                engagement_level VARCHAR(50) DEFAULT 'unknown',
                last_interaction_date TIMESTAMPTZ,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW(),
                UNIQUE(source_system, source_record_id)
            );
        """)
        
        # Create unified_interactions table if not exists
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS unified_interactions (
                id BIGSERIAL PRIMARY KEY,
                contact_id BIGINT NOT NULL,
                source_system VARCHAR(50) NOT NULL,
                source_record_id VARCHAR(100) NOT NULL,
                interaction_type VARCHAR(50) NOT NULL,
                interaction_date TIMESTAMPTZ NOT NULL,
                interaction_duration_seconds INTEGER,
                subject_title VARCHAR(500),
                content_summary TEXT,
                sentiment_score DECIMAL(3,2) CHECK (sentiment_score >= -1 AND sentiment_score <= 1),
                apartment_industry_relevance DECIMAL(3,2) DEFAULT 0.5 CHECK (apartment_industry_relevance >= 0 AND apartment_industry_relevance <= 1),
                business_impact_score DECIMAL(3,2) DEFAULT 0.5 CHECK (business_impact_score >= 0 AND business_impact_score <= 1),
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW(),
                FOREIGN KEY (contact_id) REFERENCES unified_contacts(id),
                UNIQUE(source_system, source_record_id)
            );
        """)
        
        logger.info("Adding enhanced columns to unified_interactions...")
        
        # Add columns one by one to avoid syntax issues
        enhanced_columns = [
            "ADD COLUMN IF NOT EXISTS slack_channel_id VARCHAR(50)",
            "ADD COLUMN IF NOT EXISTS slack_thread_ts VARCHAR(50)",
            "ADD COLUMN IF NOT EXISTS slack_message_type VARCHAR(50)",
            "ADD COLUMN IF NOT EXISTS slack_reaction_count INTEGER DEFAULT 0",
            "ADD COLUMN IF NOT EXISTS slack_reply_count INTEGER DEFAULT 0",
            "ADD COLUMN IF NOT EXISTS slack_mention_count INTEGER DEFAULT 0",
            "ADD COLUMN IF NOT EXISTS gong_call_id VARCHAR(50)",
            "ADD COLUMN IF NOT EXISTS gong_call_duration_seconds INTEGER",
            "ADD COLUMN IF NOT EXISTS gong_call_system VARCHAR(50)",
            "ADD COLUMN IF NOT EXISTS gong_call_direction VARCHAR(20)",
            "ADD COLUMN IF NOT EXISTS gong_transcript_available BOOLEAN DEFAULT false",
            "ADD COLUMN IF NOT EXISTS conversation_intelligence_score DECIMAL(3,2)",
            "ADD COLUMN IF NOT EXISTS urgency_level INTEGER",
            "ADD COLUMN IF NOT EXISTS escalation_required BOOLEAN DEFAULT false",
            "ADD COLUMN IF NOT EXISTS follow_up_priority VARCHAR(20) DEFAULT 'normal'",
            "ADD COLUMN IF NOT EXISTS related_interaction_ids BIGINT[]",
            "ADD COLUMN IF NOT EXISTS conversation_thread_id VARCHAR(100)",
            "ADD COLUMN IF NOT EXISTS customer_journey_stage VARCHAR(50)",
            "ADD COLUMN IF NOT EXISTS property_management_context JSONB",
            "ADD COLUMN IF NOT EXISTS competitive_mentions JSONB",
            "ADD COLUMN IF NOT EXISTS product_feature_discussions JSONB",
            "ADD COLUMN IF NOT EXISTS pricing_discussions JSONB",
            "ADD COLUMN IF NOT EXISTS integration_requirements JSONB",
            "ADD COLUMN IF NOT EXISTS key_topics_extracted TEXT[]",
            "ADD COLUMN IF NOT EXISTS action_items_identified TEXT[]",
            "ADD COLUMN IF NOT EXISTS next_best_actions TEXT[]",
            "ADD COLUMN IF NOT EXISTS risk_indicators TEXT[]",
            "ADD COLUMN IF NOT EXISTS opportunity_indicators TEXT[]"
        ]
        
        for column_def in enhanced_columns:
            await conn.execute(f"ALTER TABLE unified_interactions {column_def}")
        
        logger.info("Creating conversation intelligence table...")
        
        # Create conversation intelligence aggregation table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS conversation_intelligence (
                id BIGSERIAL PRIMARY KEY,
                conversation_thread_id VARCHAR(100) NOT NULL,
                primary_contact_id BIGINT NOT NULL,
                conversation_type VARCHAR(50) NOT NULL,
                conversation_start_date TIMESTAMPTZ NOT NULL,
                conversation_end_date TIMESTAMPTZ,
                total_duration_seconds INTEGER,
                interaction_count INTEGER DEFAULT 0,
                gong_interactions_count INTEGER DEFAULT 0,
                slack_interactions_count INTEGER DEFAULT 0,
                salesforce_activities_count INTEGER DEFAULT 0,
                hubspot_activities_count INTEGER DEFAULT 0,
                overall_sentiment_score DECIMAL(3,2) CHECK (overall_sentiment_score >= -1 AND overall_sentiment_score <= 1),
                engagement_level_score DECIMAL(3,2) CHECK (engagement_level_score >= 0 AND engagement_level_score <= 1),
                satisfaction_score DECIMAL(3,2) CHECK (satisfaction_score >= 0 AND satisfaction_score <= 1),
                success_probability_score DECIMAL(3,2) CHECK (success_probability_score >= 0 AND success_probability_score <= 1),
                churn_risk_score DECIMAL(3,2) CHECK (churn_risk_score >= 0 AND churn_risk_score <= 1),
                deal_value_estimated DECIMAL(12,2),
                deal_stage deal_stage_enum,
                customer_segment VARCHAR(100),
                property_portfolio_context JSONB,
                conversation_summary TEXT,
                key_outcomes TEXT[],
                identified_pain_points TEXT[],
                proposed_solutions TEXT[],
                competitive_landscape JSONB,
                predicted_next_actions TEXT[],
                recommended_follow_ups TEXT[],
                escalation_recommendations TEXT[],
                expansion_opportunities TEXT[],
                last_analyzed_at TIMESTAMPTZ DEFAULT NOW(),
                analysis_confidence_score DECIMAL(3,2) DEFAULT 0.8,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW(),
                FOREIGN KEY (primary_contact_id) REFERENCES unified_contacts(id),
                UNIQUE(conversation_thread_id)
            );
        """)
        
        logger.info("Creating Slack-specific tables...")
        
        # Slack channels table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS slack_channels (
                id VARCHAR(50) PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                purpose TEXT,
                topic TEXT,
                is_private BOOLEAN DEFAULT false,
                is_archived BOOLEAN DEFAULT false,
                member_count INTEGER DEFAULT 0,
                channel_type VARCHAR(50),
                business_relevance_score DECIMAL(3,2) DEFAULT 0.5,
                apartment_industry_focus BOOLEAN DEFAULT false,
                message_volume_daily_avg INTEGER DEFAULT 0,
                engagement_score DECIMAL(3,2) DEFAULT 0.5,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW()
            );
        """)
        
        # Slack users table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS slack_users (
                id VARCHAR(50) PRIMARY KEY,
                email VARCHAR(255),
                real_name VARCHAR(200),
                display_name VARCHAR(200),
                title VARCHAR(200),
                phone VARCHAR(50),
                department VARCHAR(100),
                role_category VARCHAR(50),
                is_pay_ready_employee BOOLEAN DEFAULT true,
                manager_slack_id VARCHAR(50),
                message_volume_daily_avg INTEGER DEFAULT 0,
                response_time_avg_minutes INTEGER,
                collaboration_score DECIMAL(3,2) DEFAULT 0.5,
                expertise_areas TEXT[],
                is_active BOOLEAN DEFAULT true,
                last_activity_date TIMESTAMPTZ,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW(),
                FOREIGN KEY (manager_slack_id) REFERENCES slack_users(id)
            );
        """)
        
        # Slack message intelligence table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS slack_message_intelligence (
                id BIGSERIAL PRIMARY KEY,
                message_ts VARCHAR(50) NOT NULL,
                channel_id VARCHAR(50) NOT NULL,
                user_id VARCHAR(50) NOT NULL,
                text_content TEXT,
                message_type VARCHAR(50),
                thread_ts VARCHAR(50),
                sentiment_score DECIMAL(3,2) CHECK (sentiment_score >= -1 AND sentiment_score <= 1),
                business_relevance_score DECIMAL(3,2) CHECK (business_relevance_score >= 0 AND business_relevance_score <= 1),
                urgency_score DECIMAL(3,2) CHECK (urgency_score >= 0 AND urgency_score <= 1),
                customer_mentions TEXT[],
                deal_mentions TEXT[],
                product_mentions TEXT[],
                competitor_mentions TEXT[],
                apartment_industry_keywords TEXT[],
                action_items_identified TEXT[],
                follow_up_required BOOLEAN DEFAULT false,
                escalation_needed BOOLEAN DEFAULT false,
                related_gong_call_ids VARCHAR(50)[],
                related_salesforce_records VARCHAR(50)[],
                message_timestamp TIMESTAMPTZ NOT NULL,
                analyzed_at TIMESTAMPTZ DEFAULT NOW(),
                FOREIGN KEY (channel_id) REFERENCES slack_channels(id),
                FOREIGN KEY (user_id) REFERENCES slack_users(id),
                UNIQUE(message_ts, channel_id)
            );
        """)
        
        logger.info("Creating performance indexes...")
        
        # Performance indexes
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_conversation_intelligence_contact_date ON conversation_intelligence(primary_contact_id, conversation_start_date)",
            "CREATE INDEX IF NOT EXISTS idx_slack_messages_channel_timestamp ON slack_message_intelligence(channel_id, message_timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_unified_interactions_thread ON unified_interactions(conversation_thread_id)",
            "CREATE INDEX IF NOT EXISTS idx_slack_channels_business_relevance ON slack_channels(business_relevance_score)",
            "CREATE INDEX IF NOT EXISTS idx_slack_users_role_category ON slack_users(role_category)",
            "CREATE INDEX IF NOT EXISTS idx_unified_interactions_contact_date ON unified_interactions(contact_id, interaction_date)",
            "CREATE INDEX IF NOT EXISTS idx_unified_interactions_source ON unified_interactions(source_system, source_record_id)",
            "CREATE INDEX IF NOT EXISTS idx_slack_message_intelligence_timestamp ON slack_message_intelligence(message_timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_conversation_intelligence_thread ON conversation_intelligence(conversation_thread_id)"
        ]
        
        for index_sql in indexes:
            await conn.execute(index_sql)
        
        logger.info("Enhanced database schema deployed successfully!")
        
    except Exception as e:
        logger.error(f"Schema deployment failed: {str(e)}")
        raise
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(deploy_enhanced_schema())

