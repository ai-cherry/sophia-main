#!/usr/bin/env python3
"""
Enhanced Sophia Database Schema for Complete Gong Integration
Implements production-ready schema with all Gong data types and apartment industry intelligence
"""

import asyncio
import asyncpg
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SophiaEnhancedSchema:
    """Enhanced database schema for complete Gong integration"""
    
    def __init__(self, database_url: str = None):
        self.database_url = database_url or "postgresql://postgres:password@localhost:5432/sophia_enhanced"
        self.schema_version = "3.0"
        self.connection = None
    
    async def connect(self):
        """Connect to PostgreSQL database"""
        try:
            self.connection = await asyncpg.connect(self.database_url)
            logger.info("✅ Connected to PostgreSQL database")
            return True
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            return False
    
    async def close(self):
        """Close database connection"""
        if self.connection:
            await self.connection.close()
            logger.info("🔌 Database connection closed")
    
    async def create_enhanced_schema(self):
        """Create complete enhanced schema for Gong integration"""
        logger.info("🏗️ Creating enhanced database schema for Gong integration")
        
        # Core Gong tables
        await self.create_gong_workspaces_table()
        await self.create_gong_users_table()
        await self.create_gong_calls_table()
        await self.create_gong_participants_table()
        await self.create_gong_ai_content_table()
        await self.create_gong_trackers_table()
        await self.create_gong_tracker_occurrences_table()
        await self.create_gong_emails_table()
        await self.create_gong_webhook_events_table()
        
        # Sophia intelligence tables
        await self.create_sophia_conversation_intelligence_table()
        await self.create_sophia_apartment_analysis_table()
        await self.create_sophia_competitive_intelligence_table()
        await self.create_sophia_deal_signals_table()
        
        # Admin and management tables
        await self.create_admin_search_history_table()
        await self.create_manual_uploads_table()
        await self.create_schema_migrations_table()
        
        # Create indexes for performance
        await self.create_performance_indexes()
        
        # Record schema version
        await self.record_schema_version()
        
        logger.info("✅ Enhanced database schema created successfully")
    
    async def create_gong_workspaces_table(self):
        """Create Gong workspaces table"""
        sql = """
        CREATE TABLE IF NOT EXISTS gong_workspaces (
            workspace_id VARCHAR(255) PRIMARY KEY,
            workspace_name VARCHAR(255) NOT NULL,
            company_name VARCHAR(255),
            created_date TIMESTAMP,
            is_active BOOLEAN DEFAULT true,
            settings JSONB,
            last_sync TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        await self.connection.execute(sql)
        logger.info("📊 Created gong_workspaces table")
    
    async def create_gong_users_table(self):
        """Create Gong users table"""
        sql = """
        CREATE TABLE IF NOT EXISTS gong_users (
            user_id VARCHAR(255) PRIMARY KEY,
            workspace_id VARCHAR(255) REFERENCES gong_workspaces(workspace_id),
            email_address VARCHAR(255) NOT NULL,
            first_name VARCHAR(255),
            last_name VARCHAR(255),
            full_name VARCHAR(255),
            phone_number VARCHAR(50),
            title VARCHAR(255),
            department VARCHAR(255),
            manager_id VARCHAR(255),
            is_active BOOLEAN DEFAULT true,
            settings JSONB,
            last_activity TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        await self.connection.execute(sql)
        logger.info("👥 Created gong_users table")
    
    async def create_gong_calls_table(self):
        """Create comprehensive Gong calls table"""
        sql = """
        CREATE TABLE IF NOT EXISTS gong_calls (
            call_id VARCHAR(255) PRIMARY KEY,
            workspace_id VARCHAR(255) REFERENCES gong_workspaces(workspace_id),
            title TEXT,
            url TEXT,
            started TIMESTAMP,
            duration_seconds INTEGER,
            direction VARCHAR(50), -- Inbound, Outbound, Internal
            system VARCHAR(100), -- Gong, Zoom, Teams, etc.
            scope VARCHAR(50), -- External, Internal, All
            media VARCHAR(50), -- Video, Audio
            language VARCHAR(10),
            primary_user_id VARCHAR(255) REFERENCES gong_users(user_id),
            meeting_url TEXT,
            disposition VARCHAR(100),
            custom_data JSONB,
            context_objects JSONB,
            is_private BOOLEAN DEFAULT false,
            is_processed BOOLEAN DEFAULT false,
            processing_status VARCHAR(50) DEFAULT 'pending',
            apartment_relevance_score DECIMAL(3,2),
            business_impact_score DECIMAL(3,2),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        await self.connection.execute(sql)
        logger.info("📞 Created gong_calls table")
    
    async def create_gong_participants_table(self):
        """Create Gong call participants table"""
        sql = """
        CREATE TABLE IF NOT EXISTS gong_participants (
            participant_id VARCHAR(255) PRIMARY KEY,
            call_id VARCHAR(255) REFERENCES gong_calls(call_id) ON DELETE CASCADE,
            user_id VARCHAR(255) REFERENCES gong_users(user_id),
            email_address VARCHAR(255),
            name VARCHAR(255),
            title VARCHAR(255),
            company_name VARCHAR(255),
            phone_number VARCHAR(50),
            speaker_id VARCHAR(255),
            participation_type VARCHAR(50), -- Host, Participant, Observer
            talk_time_seconds INTEGER,
            talk_time_percentage DECIMAL(5,2),
            interaction_stats JSONB,
            is_customer BOOLEAN,
            is_internal BOOLEAN,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        await self.connection.execute(sql)
        logger.info("👤 Created gong_participants table")
    
    async def create_gong_ai_content_table(self):
        """Create Gong AI content table"""
        sql = """
        CREATE TABLE IF NOT EXISTS gong_ai_content (
            content_id VARCHAR(255) PRIMARY KEY,
            call_id VARCHAR(255) REFERENCES gong_calls(call_id) ON DELETE CASCADE,
            content_type VARCHAR(50), -- briefSummary, outline, highlights, etc.
            content_text TEXT,
            content_data JSONB,
            ai_confidence_score DECIMAL(3,2),
            processing_version VARCHAR(50),
            language VARCHAR(10),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        await self.connection.execute(sql)
        logger.info("🧠 Created gong_ai_content table")
    
    async def create_gong_trackers_table(self):
        """Create Gong trackers configuration table"""
        sql = """
        CREATE TABLE IF NOT EXISTS gong_trackers (
            tracker_id VARCHAR(255) PRIMARY KEY,
            workspace_id VARCHAR(255) REFERENCES gong_workspaces(workspace_id),
            tracker_name VARCHAR(255) NOT NULL,
            tracker_description TEXT,
            tracker_type VARCHAR(50), -- keyword, phrase, sentiment, etc.
            keywords TEXT[],
            phrases TEXT[],
            is_enabled BOOLEAN DEFAULT true,
            apartment_industry_specific BOOLEAN DEFAULT false,
            business_impact_weight DECIMAL(3,2) DEFAULT 0.5,
            created_by VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        await self.connection.execute(sql)
        logger.info("🎯 Created gong_trackers table")
    
    async def create_gong_tracker_occurrences_table(self):
        """Create Gong tracker occurrences table"""
        sql = """
        CREATE TABLE IF NOT EXISTS gong_tracker_occurrences (
            occurrence_id VARCHAR(255) PRIMARY KEY,
            call_id VARCHAR(255) REFERENCES gong_calls(call_id) ON DELETE CASCADE,
            tracker_id VARCHAR(255) REFERENCES gong_trackers(tracker_id),
            tracker_name VARCHAR(255),
            occurrence_count INTEGER DEFAULT 1,
            occurrence_timestamps JSONB,
            context_snippets JSONB,
            confidence_score DECIMAL(3,2),
            speaker_id VARCHAR(255),
            apartment_relevance DECIMAL(3,2),
            competitive_context BOOLEAN DEFAULT false,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        await self.connection.execute(sql)
        logger.info("📍 Created gong_tracker_occurrences table")
    
    async def create_gong_emails_table(self):
        """Create Gong emails table for manual uploads"""
        sql = """
        CREATE TABLE IF NOT EXISTS gong_emails (
            email_id VARCHAR(255) PRIMARY KEY,
            thread_id VARCHAR(255),
            workspace_id VARCHAR(255) REFERENCES gong_workspaces(workspace_id),
            from_email VARCHAR(255),
            to_emails TEXT[],
            cc_emails TEXT[],
            bcc_emails TEXT[],
            subject_line TEXT,
            email_body TEXT,
            email_html TEXT,
            sent_timestamp TIMESTAMP,
            received_timestamp TIMESTAMP,
            direction VARCHAR(20), -- inbound, outbound
            email_type VARCHAR(50), -- initial, reply, forward
            attachments JSONB,
            engagement_metrics JSONB,
            apartment_relevance_score DECIMAL(3,2),
            related_call_ids TEXT[],
            manual_upload BOOLEAN DEFAULT false,
            uploaded_by VARCHAR(255),
            upload_timestamp TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        await self.connection.execute(sql)
        logger.info("📧 Created gong_emails table")
    
    async def create_gong_webhook_events_table(self):
        """Create Gong webhook events table"""
        sql = """
        CREATE TABLE IF NOT EXISTS gong_webhook_events (
            event_id VARCHAR(255) PRIMARY KEY,
            webhook_type VARCHAR(100),
            call_id VARCHAR(255),
            workspace_id VARCHAR(255),
            event_timestamp TIMESTAMP,
            event_data JSONB,
            processing_status VARCHAR(50) DEFAULT 'pending',
            apartment_relevance_score DECIMAL(3,2),
            immediate_actions_triggered JSONB,
            error_message TEXT,
            retry_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        await self.connection.execute(sql)
        logger.info("🔗 Created gong_webhook_events table")
    
    async def create_sophia_conversation_intelligence_table(self):
        """Create Sophia conversation intelligence table"""
        sql = """
        CREATE TABLE IF NOT EXISTS sophia_conversation_intelligence (
            intelligence_id VARCHAR(255) PRIMARY KEY,
            call_id VARCHAR(255) REFERENCES gong_calls(call_id) ON DELETE CASCADE,
            apartment_relevance_score DECIMAL(3,2),
            business_impact_score DECIMAL(3,2),
            confidence_level DECIMAL(3,2),
            processing_version VARCHAR(50),
            ai_summary TEXT,
            key_insights JSONB,
            recommended_actions JSONB,
            sentiment_analysis JSONB,
            topic_analysis JSONB,
            conversation_quality_score DECIMAL(3,2),
            customer_satisfaction_indicators JSONB,
            deal_health_score DECIMAL(3,2),
            processing_timestamp TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        await self.connection.execute(sql)
        logger.info("🧠 Created sophia_conversation_intelligence table")
    
    async def create_sophia_apartment_analysis_table(self):
        """Create Sophia apartment industry analysis table"""
        sql = """
        CREATE TABLE IF NOT EXISTS sophia_apartment_analysis (
            analysis_id VARCHAR(255) PRIMARY KEY,
            call_id VARCHAR(255) REFERENCES gong_calls(call_id) ON DELETE CASCADE,
            property_management_context JSONB,
            apartment_terminology_count INTEGER,
            industry_relevance_factors JSONB,
            property_type_mentions JSONB, -- multifamily, single-family, etc.
            operational_challenges JSONB,
            technology_stack_mentions JSONB,
            compliance_topics JSONB,
            market_segment VARCHAR(100), -- Class A, B, C properties
            portfolio_size_indicators JSONB,
            geographic_context JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        await self.connection.execute(sql)
        logger.info("🏢 Created sophia_apartment_analysis table")
    
    async def create_sophia_competitive_intelligence_table(self):
        """Create Sophia competitive intelligence table"""
        sql = """
        CREATE TABLE IF NOT EXISTS sophia_competitive_intelligence (
            competitive_id VARCHAR(255) PRIMARY KEY,
            call_id VARCHAR(255) REFERENCES gong_calls(call_id) ON DELETE CASCADE,
            competitors_mentioned TEXT[],
            competitive_context JSONB,
            competitive_strengths JSONB,
            competitive_weaknesses JSONB,
            pricing_discussions JSONB,
            feature_comparisons JSONB,
            switching_indicators JSONB,
            competitive_threat_level VARCHAR(20), -- low, medium, high
            win_probability_impact DECIMAL(3,2),
            recommended_responses JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        await self.connection.execute(sql)
        logger.info("🏆 Created sophia_competitive_intelligence table")
    
    async def create_sophia_deal_signals_table(self):
        """Create Sophia deal signals table"""
        sql = """
        CREATE TABLE IF NOT EXISTS sophia_deal_signals (
            signal_id VARCHAR(255) PRIMARY KEY,
            call_id VARCHAR(255) REFERENCES gong_calls(call_id) ON DELETE CASCADE,
            positive_signals JSONB,
            negative_signals JSONB,
            neutral_signals JSONB,
            urgency_indicators JSONB,
            decision_timeline_mentions JSONB,
            budget_discussions JSONB,
            stakeholder_mentions JSONB,
            implementation_readiness JSONB,
            deal_progression_stage VARCHAR(50),
            win_probability DECIMAL(3,2),
            risk_factors JSONB,
            acceleration_opportunities JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        await self.connection.execute(sql)
        logger.info("📈 Created sophia_deal_signals table")
    
    async def create_admin_search_history_table(self):
        """Create admin search history table"""
        sql = """
        CREATE TABLE IF NOT EXISTS admin_search_history (
            search_id VARCHAR(255) PRIMARY KEY,
            search_query TEXT,
            search_filters JSONB,
            search_results_count INTEGER,
            search_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            user_session VARCHAR(255),
            execution_time_ms INTEGER
        );
        """
        await self.connection.execute(sql)
        logger.info("🔍 Created admin_search_history table")
    
    async def create_manual_uploads_table(self):
        """Create manual uploads tracking table"""
        sql = """
        CREATE TABLE IF NOT EXISTS manual_uploads (
            upload_id VARCHAR(255) PRIMARY KEY,
            upload_type VARCHAR(50), -- email, document, etc.
            file_name VARCHAR(255),
            file_size INTEGER,
            file_content TEXT,
            parsed_data JSONB,
            processing_status VARCHAR(50) DEFAULT 'pending',
            apartment_relevance_score DECIMAL(3,2),
            related_records JSONB,
            uploaded_by VARCHAR(255),
            upload_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            processed_timestamp TIMESTAMP,
            error_message TEXT
        );
        """
        await self.connection.execute(sql)
        logger.info("📤 Created manual_uploads table")
    
    async def create_schema_migrations_table(self):
        """Create schema migrations tracking table"""
        sql = """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            migration_id VARCHAR(255) PRIMARY KEY,
            schema_version VARCHAR(50),
            migration_description TEXT,
            migration_sql TEXT,
            applied_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            rollback_sql TEXT
        );
        """
        await self.connection.execute(sql)
        logger.info("🔄 Created schema_migrations table")
    
    async def create_performance_indexes(self):
        """Create performance-optimized indexes"""
        logger.info("⚡ Creating performance indexes")
        
        indexes = [
            # Gong calls indexes
            "CREATE INDEX IF NOT EXISTS idx_gong_calls_started ON gong_calls(started)",
            "CREATE INDEX IF NOT EXISTS idx_gong_calls_workspace ON gong_calls(workspace_id)",
            "CREATE INDEX IF NOT EXISTS idx_gong_calls_primary_user ON gong_calls(primary_user_id)",
            "CREATE INDEX IF NOT EXISTS idx_gong_calls_direction ON gong_calls(direction)",
            "CREATE INDEX IF NOT EXISTS idx_gong_calls_apartment_relevance ON gong_calls(apartment_relevance_score)",
            "CREATE INDEX IF NOT EXISTS idx_gong_calls_business_impact ON gong_calls(business_impact_score)",
            "CREATE INDEX IF NOT EXISTS idx_gong_calls_processing_status ON gong_calls(processing_status)",
            
            # Participants indexes
            "CREATE INDEX IF NOT EXISTS idx_gong_participants_call ON gong_participants(call_id)",
            "CREATE INDEX IF NOT EXISTS idx_gong_participants_email ON gong_participants(email_address)",
            "CREATE INDEX IF NOT EXISTS idx_gong_participants_company ON gong_participants(company_name)",
            
            # AI content indexes
            "CREATE INDEX IF NOT EXISTS idx_gong_ai_content_call ON gong_ai_content(call_id)",
            "CREATE INDEX IF NOT EXISTS idx_gong_ai_content_type ON gong_ai_content(content_type)",
            "CREATE INDEX IF NOT EXISTS idx_gong_ai_content_confidence ON gong_ai_content(ai_confidence_score)",
            
            # Tracker occurrences indexes
            "CREATE INDEX IF NOT EXISTS idx_tracker_occurrences_call ON gong_tracker_occurrences(call_id)",
            "CREATE INDEX IF NOT EXISTS idx_tracker_occurrences_tracker ON gong_tracker_occurrences(tracker_id)",
            "CREATE INDEX IF NOT EXISTS idx_tracker_occurrences_apartment ON gong_tracker_occurrences(apartment_relevance)",
            
            # Emails indexes
            "CREATE INDEX IF NOT EXISTS idx_gong_emails_from ON gong_emails(from_email)",
            "CREATE INDEX IF NOT EXISTS idx_gong_emails_sent ON gong_emails(sent_timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_gong_emails_thread ON gong_emails(thread_id)",
            "CREATE INDEX IF NOT EXISTS idx_gong_emails_apartment_relevance ON gong_emails(apartment_relevance_score)",
            
            # Sophia intelligence indexes
            "CREATE INDEX IF NOT EXISTS idx_sophia_intelligence_call ON sophia_conversation_intelligence(call_id)",
            "CREATE INDEX IF NOT EXISTS idx_sophia_intelligence_apartment ON sophia_conversation_intelligence(apartment_relevance_score)",
            "CREATE INDEX IF NOT EXISTS idx_sophia_intelligence_business ON sophia_conversation_intelligence(business_impact_score)",
            "CREATE INDEX IF NOT EXISTS idx_sophia_intelligence_timestamp ON sophia_conversation_intelligence(processing_timestamp)",
            
            # Competitive intelligence indexes
            "CREATE INDEX IF NOT EXISTS idx_competitive_intelligence_call ON sophia_competitive_intelligence(call_id)",
            "CREATE INDEX IF NOT EXISTS idx_competitive_intelligence_threat ON sophia_competitive_intelligence(competitive_threat_level)",
            
            # Deal signals indexes
            "CREATE INDEX IF NOT EXISTS idx_deal_signals_call ON sophia_deal_signals(call_id)",
            "CREATE INDEX IF NOT EXISTS idx_deal_signals_stage ON sophia_deal_signals(deal_progression_stage)",
            "CREATE INDEX IF NOT EXISTS idx_deal_signals_probability ON sophia_deal_signals(win_probability)",
            
            # Search and admin indexes
            "CREATE INDEX IF NOT EXISTS idx_search_history_timestamp ON admin_search_history(search_timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_manual_uploads_timestamp ON manual_uploads(upload_timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_manual_uploads_type ON manual_uploads(upload_type)",
            
            # Full-text search indexes
            "CREATE INDEX IF NOT EXISTS idx_gong_calls_title_fts ON gong_calls USING gin(to_tsvector('english', title))",
            "CREATE INDEX IF NOT EXISTS idx_gong_ai_content_fts ON gong_ai_content USING gin(to_tsvector('english', content_text))",
            "CREATE INDEX IF NOT EXISTS idx_gong_emails_subject_fts ON gong_emails USING gin(to_tsvector('english', subject_line))",
            "CREATE INDEX IF NOT EXISTS idx_gong_emails_body_fts ON gong_emails USING gin(to_tsvector('english', email_body))"
        ]
        
        for index_sql in indexes:
            try:
                await self.connection.execute(index_sql)
            except Exception as e:
                logger.warning(f"Index creation warning: {e}")
        
        logger.info("✅ Performance indexes created")
    
    async def record_schema_version(self):
        """Record current schema version"""
        migration_sql = """
        INSERT INTO schema_migrations (migration_id, schema_version, migration_description)
        VALUES ($1, $2, $3)
        ON CONFLICT (migration_id) DO UPDATE SET
            schema_version = EXCLUDED.schema_version,
            migration_description = EXCLUDED.migration_description,
            applied_timestamp = CURRENT_TIMESTAMP
        """
        
        await self.connection.execute(
            migration_sql,
            f"schema_v{self.schema_version}",
            self.schema_version,
            "Enhanced Sophia database schema for complete Gong integration"
        )
        
        logger.info(f"📝 Recorded schema version {self.schema_version}")
    
    async def get_schema_info(self):
        """Get comprehensive schema information"""
        tables_sql = """
        SELECT table_name, 
               (SELECT COUNT(*) FROM information_schema.columns 
                WHERE table_name = t.table_name AND table_schema = 'public') as column_count
        FROM information_schema.tables t
        WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
        ORDER BY table_name
        """
        
        tables = await self.connection.fetch(tables_sql)
        
        indexes_sql = """
        SELECT schemaname, tablename, indexname, indexdef
        FROM pg_indexes
        WHERE schemaname = 'public'
        ORDER BY tablename, indexname
        """
        
        indexes = await self.connection.fetch(indexes_sql)
        
        return {
            "schema_version": self.schema_version,
            "tables": [dict(row) for row in tables],
            "indexes": [dict(row) for row in indexes],
            "total_tables": len(tables),
            "total_indexes": len(indexes)
        }

async def deploy_enhanced_schema():
    """Deploy enhanced schema with comprehensive logging"""
    logger.info("🚀 Starting Enhanced Sophia Database Schema Deployment")
    
    # Database connection parameters
    db_config = {
        "host": "localhost",
        "port": 5432,
        "database": "sophia_enhanced",
        "user": "postgres",
        "password": "password"
    }
    
    database_url = f"postgresql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}"
    
    schema_manager = SophiaEnhancedSchema(database_url)
    
    try:
        # Connect to database
        connected = await schema_manager.connect()
        if not connected:
            logger.error("❌ Failed to connect to database")
            return False
        
        # Create enhanced schema
        await schema_manager.create_enhanced_schema()
        
        # Get schema information
        schema_info = await schema_manager.get_schema_info()
        
        # Log schema summary
        logger.info("📊 Schema Deployment Summary:")
        logger.info(f"   Schema Version: {schema_info['schema_version']}")
        logger.info(f"   Total Tables: {schema_info['total_tables']}")
        logger.info(f"   Total Indexes: {schema_info['total_indexes']}")
        
        logger.info("📋 Tables Created:")
        for table in schema_info['tables']:
            logger.info(f"   - {table['table_name']} ({table['column_count']} columns)")
        
        # Save schema info to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        schema_file = f'/home/ubuntu/sophia_enhanced_schema_info_{timestamp}.json'
        
        with open(schema_file, 'w') as f:
            json.dump(schema_info, f, indent=2, default=str)
        
        logger.info(f"💾 Schema information saved to: {schema_file}")
        logger.info("🎉 Enhanced Sophia Database Schema Deployment Complete!")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Schema deployment failed: {e}")
        return False
        
    finally:
        await schema_manager.close()

if __name__ == "__main__":
    asyncio.run(deploy_enhanced_schema())

