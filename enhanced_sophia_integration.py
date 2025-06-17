#!/usr/bin/env python3
"""
Enhanced Sophia Database Integration Implementation
Combines Slack + Gong.io data into unified conversation intelligence platform
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import asyncpg
import aiohttp
from slack_sdk.web.async_client import AsyncWebClient
from slack_sdk.errors import SlackApiError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedSophiaIntegration:
    """Enhanced integration combining Slack and Gong.io data into Sophia database"""
    
    def __init__(self):
        # Database connection
        self.db_config = {
            'host': os.getenv('POSTGRES_HOST', 'localhost'),
            'port': int(os.getenv('POSTGRES_PORT', 5432)),
            'database': os.getenv('POSTGRES_DB', 'sophia_unified'),
            'user': os.getenv('POSTGRES_USER', 'sophia'),
            'password': os.getenv('POSTGRES_PASSWORD')
        }
        
        # API credentials (from environment)
        self.gong_access_key = os.getenv('GONG_ACCESS_KEY')
        self.gong_access_key_secret = os.getenv('GONG_ACCESS_KEY_SECRET')
        self.slack_bot_token = os.getenv('SLACK_BOT_TOKEN')
        
        self.db_pool = None
        self.slack_client = None
        
    async def initialize(self):
        """Initialize database connection and API clients"""
        logger.info("Initializing enhanced Sophia integration...")
        
        # Initialize database pool
        self.db_pool = await asyncpg.create_pool(**self.db_config)
        
        # Initialize Slack client
        if self.slack_bot_token:
            self.slack_client = AsyncWebClient(token=self.slack_bot_token)
        
        logger.info("Enhanced Sophia integration initialized successfully")
    
    async def create_enhanced_schema(self):
        """Create enhanced database schema for unified intelligence"""
        logger.info("Creating enhanced database schema...")
        
        schema_sql = """
        -- Enhanced unified_interactions with Slack + Gong intelligence
        ALTER TABLE unified_interactions ADD COLUMN IF NOT EXISTS
            -- Slack-specific fields
            slack_channel_id VARCHAR(50),
            slack_thread_ts VARCHAR(50),
            slack_message_type VARCHAR(50),
            slack_reaction_count INTEGER DEFAULT 0,
            slack_reply_count INTEGER DEFAULT 0,
            slack_mention_count INTEGER DEFAULT 0,
            
            -- Gong-specific fields
            gong_call_id VARCHAR(50),
            gong_call_duration_seconds INTEGER,
            gong_call_system VARCHAR(50),
            gong_call_direction VARCHAR(20),
            gong_transcript_available BOOLEAN DEFAULT false,
            
            -- Enhanced intelligence fields
            conversation_intelligence_score DECIMAL(3,2) CHECK (conversation_intelligence_score >= 0 AND conversation_intelligence_score <= 1),
            business_impact_score DECIMAL(3,2) CHECK (business_impact_score >= 0 AND business_impact_score <= 1),
            urgency_level INTEGER CHECK (urgency_level >= 1 AND urgency_level <= 5),
            escalation_required BOOLEAN DEFAULT false,
            follow_up_priority VARCHAR(20) DEFAULT 'normal',
            
            -- Cross-platform correlation
            related_interaction_ids BIGINT[],
            conversation_thread_id VARCHAR(100),
            customer_journey_stage VARCHAR(50),
            
            -- Enhanced apartment industry context
            property_management_context JSONB,
            competitive_mentions JSONB,
            product_feature_discussions JSONB,
            pricing_discussions JSONB,
            integration_requirements JSONB,
            
            -- AI-powered insights
            key_topics_extracted TEXT[],
            action_items_identified TEXT[],
            next_best_actions TEXT[],
            risk_indicators TEXT[],
            opportunity_indicators TEXT[];
        
        -- Conversation intelligence aggregation table
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
        
        -- Slack channels with business context
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
        
        -- Slack users with Pay Ready context
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
        
        -- Slack message intelligence
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
        
        -- Performance indexes
        CREATE INDEX IF NOT EXISTS idx_conversation_intelligence_contact_date ON conversation_intelligence(primary_contact_id, conversation_start_date);
        CREATE INDEX IF NOT EXISTS idx_slack_messages_channel_timestamp ON slack_message_intelligence(channel_id, message_timestamp);
        CREATE INDEX IF NOT EXISTS idx_unified_interactions_thread ON unified_interactions(conversation_thread_id);
        CREATE INDEX IF NOT EXISTS idx_slack_channels_business_relevance ON slack_channels(business_relevance_score);
        CREATE INDEX IF NOT EXISTS idx_slack_users_role_category ON slack_users(role_category);
        """
        
        async with self.db_pool.acquire() as conn:
            await conn.execute(schema_sql)
        
        logger.info("Enhanced database schema created successfully")
    
    async def import_slack_data(self):
        """Import Slack data into enhanced schema"""
        logger.info("Starting Slack data import...")
        
        if not self.slack_client:
            logger.error("Slack client not initialized")
            return
        
        try:
            # Import channels
            await self._import_slack_channels()
            
            # Import users
            await self._import_slack_users()
            
            # Import recent messages
            await self._import_slack_messages()
            
            logger.info("Slack data import completed successfully")
            
        except Exception as e:
            logger.error(f"Slack data import failed: {str(e)}")
    
    async def _import_slack_channels(self):
        """Import Slack channels with business context"""
        logger.info("Importing Slack channels...")
        
        try:
            response = await self.slack_client.conversations_list(
                types="public_channel,private_channel",
                limit=1000
            )
            
            channels = response.get('channels', [])
            
            async with self.db_pool.acquire() as conn:
                for channel in channels:
                    # Determine business relevance
                    business_relevance = await self._calculate_channel_business_relevance(channel)
                    apartment_focus = await self._detect_apartment_industry_focus(channel)
                    
                    await conn.execute("""
                        INSERT INTO slack_channels (
                            id, name, purpose, topic, is_private, is_archived,
                            member_count, business_relevance_score, apartment_industry_focus
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                        ON CONFLICT (id) DO UPDATE SET
                            name = EXCLUDED.name,
                            purpose = EXCLUDED.purpose,
                            topic = EXCLUDED.topic,
                            is_archived = EXCLUDED.is_archived,
                            member_count = EXCLUDED.member_count,
                            business_relevance_score = EXCLUDED.business_relevance_score,
                            apartment_industry_focus = EXCLUDED.apartment_industry_focus,
                            updated_at = NOW()
                    """, 
                        channel['id'],
                        channel.get('name', ''),
                        channel.get('purpose', {}).get('value', ''),
                        channel.get('topic', {}).get('value', ''),
                        channel.get('is_private', False),
                        channel.get('is_archived', False),
                        channel.get('num_members', 0),
                        business_relevance,
                        apartment_focus
                    )
            
            logger.info(f"Imported {len(channels)} Slack channels")
            
        except SlackApiError as e:
            logger.error(f"Failed to import Slack channels: {e.response['error']}")
    
    async def _import_slack_users(self):
        """Import Slack users with Pay Ready context"""
        logger.info("Importing Slack users...")
        
        try:
            response = await self.slack_client.users_list(limit=1000)
            users = response.get('members', [])
            active_users = [u for u in users if not u.get('deleted', False)]
            
            async with self.db_pool.acquire() as conn:
                for user in active_users:
                    profile = user.get('profile', {})
                    
                    # Determine role category
                    role_category = await self._determine_user_role_category(user)
                    
                    await conn.execute("""
                        INSERT INTO slack_users (
                            id, email, real_name, display_name, title, phone,
                            role_category, is_pay_ready_employee, is_active
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                        ON CONFLICT (id) DO UPDATE SET
                            email = EXCLUDED.email,
                            real_name = EXCLUDED.real_name,
                            display_name = EXCLUDED.display_name,
                            title = EXCLUDED.title,
                            phone = EXCLUDED.phone,
                            role_category = EXCLUDED.role_category,
                            is_active = EXCLUDED.is_active,
                            updated_at = NOW()
                    """,
                        user['id'],
                        profile.get('email', ''),
                        profile.get('real_name', ''),
                        profile.get('display_name', ''),
                        profile.get('title', ''),
                        profile.get('phone', ''),
                        role_category,
                        not user.get('is_bot', False),
                        not user.get('deleted', False)
                    )
            
            logger.info(f"Imported {len(active_users)} Slack users")
            
        except SlackApiError as e:
            logger.error(f"Failed to import Slack users: {e.response['error']}")
    
    async def _import_slack_messages(self, days_back: int = 30):
        """Import recent Slack messages with intelligence analysis"""
        logger.info(f"Importing Slack messages from last {days_back} days...")
        
        # Get channels to process
        async with self.db_pool.acquire() as conn:
            channels = await conn.fetch("""
                SELECT id, name, business_relevance_score 
                FROM slack_channels 
                WHERE NOT is_archived AND business_relevance_score > 0.3
                ORDER BY business_relevance_score DESC
                LIMIT 50
            """)
        
        oldest_timestamp = (datetime.now() - timedelta(days=days_back)).timestamp()
        
        for channel in channels:
            try:
                logger.info(f"Processing messages for channel: {channel['name']}")
                
                response = await self.slack_client.conversations_history(
                    channel=channel['id'],
                    oldest=str(oldest_timestamp),
                    limit=1000
                )
                
                messages = response.get('messages', [])
                
                async with self.db_pool.acquire() as conn:
                    for message in messages:
                        if message.get('type') == 'message' and 'text' in message:
                            # Analyze message intelligence
                            intelligence = await self._analyze_message_intelligence(message)
                            
                            await conn.execute("""
                                INSERT INTO slack_message_intelligence (
                                    message_ts, channel_id, user_id, text_content,
                                    message_type, thread_ts, sentiment_score,
                                    business_relevance_score, urgency_score,
                                    customer_mentions, deal_mentions, product_mentions,
                                    competitor_mentions, apartment_industry_keywords,
                                    action_items_identified, follow_up_required,
                                    escalation_needed, message_timestamp
                                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18)
                                ON CONFLICT (message_ts, channel_id) DO NOTHING
                            """,
                                message['ts'],
                                channel['id'],
                                message.get('user', ''),
                                message.get('text', ''),
                                'message',
                                message.get('thread_ts'),
                                intelligence['sentiment_score'],
                                intelligence['business_relevance_score'],
                                intelligence['urgency_score'],
                                intelligence['customer_mentions'],
                                intelligence['deal_mentions'],
                                intelligence['product_mentions'],
                                intelligence['competitor_mentions'],
                                intelligence['apartment_keywords'],
                                intelligence['action_items'],
                                intelligence['follow_up_required'],
                                intelligence['escalation_needed'],
                                datetime.fromtimestamp(float(message['ts']))
                            )
                
                logger.info(f"Processed {len(messages)} messages for {channel['name']}")
                
            except SlackApiError as e:
                logger.error(f"Failed to import messages for channel {channel['name']}: {e.response['error']}")
    
    async def import_gong_data(self):
        """Import Gong.io data with enhanced intelligence"""
        logger.info("Starting Gong.io data import...")
        
        if not self.gong_access_key or not self.gong_access_key_secret:
            logger.error("Gong.io credentials not configured")
            return
        
        try:
            # Import calls
            await self._import_gong_calls()
            
            # Import users
            await self._import_gong_users()
            
            logger.info("Gong.io data import completed successfully")
            
        except Exception as e:
            logger.error(f"Gong.io data import failed: {str(e)}")
    
    async def _import_gong_calls(self, days_back: int = 90):
        """Import Gong calls with enhanced apartment industry analysis"""
        logger.info(f"Importing Gong calls from last {days_back} days...")
        
        base_url = "https://api.gong.io/v2"
        headers = {
            'Authorization': f'Basic {self.gong_access_key}:{self.gong_access_key_secret}',
            'Content-Type': 'application/json'
        }
        
        params = {
            'fromDateTime': (datetime.now() - timedelta(days=days_back)).isoformat(),
            'toDateTime': datetime.now().isoformat(),
            'cursor': '',
            'limit': 100
        }
        
        async with aiohttp.ClientSession() as session:
            while True:
                async with session.get(f"{base_url}/calls", headers=headers, params=params) as response:
                    if response.status != 200:
                        logger.error(f"Gong API error: {response.status}")
                        break
                    
                    data = await response.json()
                    calls = data.get('calls', [])
                    
                    if not calls:
                        break
                    
                    # Process calls
                    async with self.db_pool.acquire() as conn:
                        for call in calls:
                            # Enhanced apartment industry analysis
                            apartment_analysis = await self._analyze_apartment_context(call)
                            
                            # Store in unified_interactions
                            await conn.execute("""
                                INSERT INTO unified_interactions (
                                    contact_id, source_system, source_record_id,
                                    interaction_type, interaction_date, interaction_duration_seconds,
                                    subject_title, content_summary, gong_call_id,
                                    gong_call_duration_seconds, gong_call_direction,
                                    apartment_industry_relevance, property_management_context,
                                    competitive_mentions, conversation_intelligence_score
                                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
                                ON CONFLICT (source_system, source_record_id) DO NOTHING
                            """,
                                await self._get_or_create_contact_id(call),
                                'Gong',
                                call['id'],
                                'Call',
                                datetime.fromisoformat(call['scheduled'].replace('Z', '+00:00')),
                                call.get('actualDuration', 0),
                                call.get('title', ''),
                                call.get('purpose', ''),
                                call['id'],
                                call.get('actualDuration', 0),
                                call.get('direction', 'Unknown'),
                                apartment_analysis['industry_relevance'],
                                json.dumps(apartment_analysis['property_context']),
                                json.dumps(apartment_analysis['competitive_mentions']),
                                apartment_analysis['conversation_quality']
                            )
                    
                    logger.info(f"Processed {len(calls)} Gong calls")
                    
                    # Check for next page
                    cursor = data.get('records', {}).get('cursor')
                    if not cursor:
                        break
                    params['cursor'] = cursor
    
    async def create_conversation_threads(self):
        """Create conversation threads linking related interactions"""
        logger.info("Creating conversation threads...")
        
        async with self.db_pool.acquire() as conn:
            # Find interactions that should be grouped together
            interactions = await conn.fetch("""
                SELECT id, contact_id, interaction_date, source_system, 
                       subject_title, content_summary, gong_call_id, slack_channel_id
                FROM unified_interactions
                WHERE conversation_thread_id IS NULL
                ORDER BY contact_id, interaction_date
            """)
            
            # Group interactions by contact and temporal proximity
            thread_groups = await self._group_interactions_by_thread(interactions)
            
            # Create conversation intelligence records
            for thread_id, group in thread_groups.items():
                await self._create_conversation_intelligence_record(conn, thread_id, group)
                
                # Update interactions with thread ID
                interaction_ids = [interaction['id'] for interaction in group]
                await conn.execute("""
                    UPDATE unified_interactions 
                    SET conversation_thread_id = $1 
                    WHERE id = ANY($2)
                """, thread_id, interaction_ids)
        
        logger.info("Conversation threads created successfully")
    
    # Helper methods for intelligence analysis
    async def _calculate_channel_business_relevance(self, channel: Dict) -> float:
        """Calculate business relevance score for Slack channel"""
        # Simple heuristic based on channel name and purpose
        business_keywords = ['sales', 'support', 'customer', 'deal', 'prospect', 'client', 'revenue']
        
        name = channel.get('name', '').lower()
        purpose = channel.get('purpose', {}).get('value', '').lower()
        
        score = 0.3  # Base score
        
        for keyword in business_keywords:
            if keyword in name or keyword in purpose:
                score += 0.2
        
        return min(score, 1.0)
    
    async def _detect_apartment_industry_focus(self, channel: Dict) -> bool:
        """Detect if channel focuses on apartment industry"""
        apartment_keywords = ['apartment', 'multifamily', 'property', 'leasing', 'resident', 'unit']
        
        name = channel.get('name', '').lower()
        purpose = channel.get('purpose', {}).get('value', '').lower()
        
        return any(keyword in name or keyword in purpose for keyword in apartment_keywords)
    
    async def _determine_user_role_category(self, user: Dict) -> str:
        """Determine user role category based on profile"""
        profile = user.get('profile', {})
        title = profile.get('title', '').lower()
        
        if any(word in title for word in ['sales', 'account', 'business development']):
            return 'sales'
        elif any(word in title for word in ['support', 'success', 'implementation']):
            return 'support'
        elif any(word in title for word in ['ceo', 'cto', 'vp', 'director']):
            return 'executive'
        elif any(word in title for word in ['engineer', 'developer', 'technical']):
            return 'technical'
        else:
            return 'other'
    
    async def _analyze_message_intelligence(self, message: Dict) -> Dict:
        """Analyze Slack message for business intelligence"""
        text = message.get('text', '').lower()
        
        # Simple keyword-based analysis (would be enhanced with NLP in production)
        return {
            'sentiment_score': 0.0,  # Placeholder for sentiment analysis
            'business_relevance_score': 0.5,  # Placeholder
            'urgency_score': 0.3,  # Placeholder
            'customer_mentions': [],  # Extract customer names
            'deal_mentions': [],  # Extract deal references
            'product_mentions': [],  # Extract product mentions
            'competitor_mentions': [],  # Extract competitor mentions
            'apartment_keywords': [],  # Extract apartment industry keywords
            'action_items': [],  # Extract action items
            'follow_up_required': 'follow up' in text or 'action item' in text,
            'escalation_needed': 'urgent' in text or 'escalate' in text
        }
    
    async def _analyze_apartment_context(self, call: Dict) -> Dict:
        """Analyze Gong call for apartment industry context"""
        # Placeholder for apartment industry analysis
        return {
            'industry_relevance': 0.8,
            'property_context': {
                'portfolio_size': 'unknown',
                'property_types': [],
                'management_software': 'unknown'
            },
            'competitive_mentions': [],
            'conversation_quality': 0.7
        }
    
    async def _get_or_create_contact_id(self, call: Dict) -> int:
        """Get or create contact ID for Gong call participants"""
        # Simplified - would extract participant emails and match to contacts
        return 1  # Placeholder
    
    async def _group_interactions_by_thread(self, interactions: List) -> Dict:
        """Group interactions into conversation threads"""
        # Simplified grouping logic - would use more sophisticated correlation
        threads = {}
        current_thread_id = 1
        
        for interaction in interactions:
            thread_id = f"thread_{current_thread_id}"
            if thread_id not in threads:
                threads[thread_id] = []
            threads[thread_id].append(interaction)
            current_thread_id += 1
        
        return threads
    
    async def _create_conversation_intelligence_record(self, conn, thread_id: str, interactions: List):
        """Create conversation intelligence aggregation record"""
        if not interactions:
            return
        
        primary_contact_id = interactions[0]['contact_id']
        start_date = min(i['interaction_date'] for i in interactions)
        end_date = max(i['interaction_date'] for i in interactions)
        
        gong_count = sum(1 for i in interactions if i['source_system'] == 'Gong')
        slack_count = sum(1 for i in interactions if i['source_system'] == 'Slack')
        
        await conn.execute("""
            INSERT INTO conversation_intelligence (
                conversation_thread_id, primary_contact_id, conversation_type,
                conversation_start_date, conversation_end_date, interaction_count,
                gong_interactions_count, slack_interactions_count,
                overall_sentiment_score, engagement_level_score
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            ON CONFLICT (conversation_thread_id) DO NOTHING
        """,
            thread_id, primary_contact_id, 'mixed',
            start_date, end_date, len(interactions),
            gong_count, slack_count, 0.5, 0.6  # Placeholder scores
        )
    
    async def run_full_integration(self):
        """Run complete integration process"""
        logger.info("Starting full enhanced Sophia integration...")
        
        try:
            await self.initialize()
            await self.create_enhanced_schema()
            await self.import_slack_data()
            await self.import_gong_data()
            await self.create_conversation_threads()
            
            logger.info("Enhanced Sophia integration completed successfully!")
            
        except Exception as e:
            logger.error(f"Integration failed: {str(e)}")
            raise
        finally:
            if self.db_pool:
                await self.db_pool.close()

async def main():
    """Main execution function"""
    integration = EnhancedSophiaIntegration()
    await integration.run_full_integration()

if __name__ == "__main__":
    asyncio.run(main())

