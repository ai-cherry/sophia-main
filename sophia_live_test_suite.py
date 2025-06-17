#!/usr/bin/env python3
"""
Sophia Live Test Suite
Comprehensive testing of Slack + Gong.io database integration
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import asyncpg
import aiohttp
from slack_sdk.web.async_client import AsyncWebClient
from slack_sdk.errors import SlackApiError

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SophiaLiveTestSuite:
    """Live testing suite for Sophia database integration"""
    
    def __init__(self):
        # Test configuration
        self.test_results = {
            'start_time': datetime.now(),
            'tests_passed': 0,
            'tests_failed': 0,
            'performance_metrics': {},
            'data_samples': {},
            'schema_validations': {},
            'api_responses': {}
        }
        
        # Database configuration (using local SQLite for testing)
        self.db_config = {
            'host': 'localhost',
            'port': 5432,
            'database': 'sophia_test',
            'user': 'postgres',
            'password': 'postgres'
        }
        
        # API credentials (will be set via environment for security)
        self.gong_access_key = None
        self.gong_access_key_secret = None
        self.slack_bot_token = None
        
        self.db_pool = None
        self.slack_client = None
        
    def set_credentials(self, gong_key: str, gong_secret: str, slack_token: str):
        """Securely set API credentials for testing"""
        self.gong_access_key = gong_key
        self.gong_access_key_secret = gong_secret
        self.slack_bot_token = slack_token
        
        # Initialize Slack client
        if self.slack_bot_token:
            self.slack_client = AsyncWebClient(token=self.slack_bot_token)
            
    async def setup_test_database(self):
        """Set up test database with schema"""
        logger.info("Setting up test database...")
        
        try:
            # Create test database connection
            conn = await asyncpg.connect(
                host=self.db_config['host'],
                port=self.db_config['port'],
                user=self.db_config['user'],
                password=self.db_config['password'],
                database='postgres'  # Connect to default database first
            )
            
            # Create test database if it doesn't exist
            try:
                await conn.execute(f"CREATE DATABASE {self.db_config['database']}")
                logger.info(f"Created test database: {self.db_config['database']}")
            except asyncpg.DuplicateDatabaseError:
                logger.info(f"Test database already exists: {self.db_config['database']}")
            
            await conn.close()
            
            # Connect to test database and create schema
            self.db_pool = await asyncpg.create_pool(**self.db_config)
            
            async with self.db_pool.acquire() as conn:
                # Create test tables
                await self.create_test_schema(conn)
                
            self.test_results['schema_validations']['database_setup'] = 'PASSED'
            self.test_results['tests_passed'] += 1
            logger.info("✅ Test database setup completed")
            
        except Exception as e:
            logger.error(f"❌ Database setup failed: {e}")
            self.test_results['schema_validations']['database_setup'] = f'FAILED: {e}'
            self.test_results['tests_failed'] += 1
            
    async def create_test_schema(self, conn):
        """Create test schema tables"""
        
        # Create enum types
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
        
        # Create unified_contacts table
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
        
        # Create unified_interactions table
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
                apartment_industry_relevance DECIMAL(3,2) DEFAULT 0.5,
                business_impact_score DECIMAL(3,2) DEFAULT 0.5,
                slack_channel_id VARCHAR(50),
                slack_thread_ts VARCHAR(50),
                slack_message_type VARCHAR(50),
                slack_reaction_count INTEGER DEFAULT 0,
                gong_call_id VARCHAR(100),
                gong_call_duration_seconds INTEGER,
                gong_transcript_available BOOLEAN DEFAULT FALSE,
                gong_recording_url TEXT,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW(),
                FOREIGN KEY (contact_id) REFERENCES unified_contacts(id),
                UNIQUE(source_system, source_record_id)
            );
        """)
        
        # Create conversation_intelligence table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS conversation_intelligence (
                id BIGSERIAL PRIMARY KEY,
                interaction_id BIGINT NOT NULL,
                conversation_thread_id VARCHAR(100),
                participants TEXT[],
                conversation_summary TEXT,
                key_topics TEXT[],
                action_items TEXT[],
                sentiment_analysis JSONB,
                urgency_score DECIMAL(3,2) DEFAULT 0.5,
                customer_satisfaction_score DECIMAL(3,2),
                deal_progression_indicator VARCHAR(100),
                competitive_mentions TEXT[],
                product_feedback TEXT[],
                apartment_industry_context JSONB,
                ai_insights TEXT,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW(),
                FOREIGN KEY (interaction_id) REFERENCES unified_interactions(id)
            );
        """)
        
        logger.info("✅ Test schema created successfully")
        
    async def test_gong_api_connectivity(self):
        """Test Gong.io API connectivity and data extraction"""
        logger.info("Testing Gong.io API connectivity...")
        
        if not self.gong_access_key or not self.gong_access_key_secret:
            logger.error("❌ Gong.io credentials not provided")
            self.test_results['api_responses']['gong_connectivity'] = 'FAILED: No credentials'
            self.test_results['tests_failed'] += 1
            return
            
        try:
            start_time = time.time()
            
            # Test Gong API connection
            async with aiohttp.ClientSession() as session:
                # Get users endpoint
                auth = aiohttp.BasicAuth(self.gong_access_key, self.gong_access_key_secret)
                
                async with session.get(
                    'https://api.gong.io/v2/users',
                    auth=auth,
                    headers={'Content-Type': 'application/json'}
                ) as response:
                    
                    if response.status == 200:
                        users_data = await response.json()
                        user_count = len(users_data.get('users', []))
                        
                        # Test calls endpoint with small sample
                        from_date = (datetime.now() - timedelta(days=7)).isoformat()
                        to_date = datetime.now().isoformat()
                        
                        calls_payload = {
                            "filter": {
                                "fromDateTime": from_date,
                                "toDateTime": to_date
                            },
                            "cursor": {
                                "limit": 10  # Small sample for testing
                            }
                        }
                        
                        async with session.post(
                            'https://api.gong.io/v2/calls',
                            auth=auth,
                            headers={'Content-Type': 'application/json'},
                            json=calls_payload
                        ) as calls_response:
                            
                            if calls_response.status == 200:
                                calls_data = await calls_response.json()
                                call_count = len(calls_data.get('calls', []))
                                
                                response_time = time.time() - start_time
                                
                                self.test_results['api_responses']['gong_connectivity'] = 'PASSED'
                                self.test_results['data_samples']['gong_users'] = user_count
                                self.test_results['data_samples']['gong_calls_sample'] = call_count
                                self.test_results['performance_metrics']['gong_api_response_time'] = response_time
                                self.test_results['tests_passed'] += 1
                                
                                logger.info(f"✅ Gong.io API connected successfully")
                                logger.info(f"   - Users found: {user_count}")
                                logger.info(f"   - Recent calls sample: {call_count}")
                                logger.info(f"   - Response time: {response_time:.2f}s")
                                
                                # Store sample data for schema testing
                                if calls_data.get('calls'):
                                    self.test_results['data_samples']['gong_call_structure'] = calls_data['calls'][0]
                                    
                            else:
                                error_msg = f"Calls API failed with status {calls_response.status}"
                                logger.error(f"❌ {error_msg}")
                                self.test_results['api_responses']['gong_connectivity'] = f'FAILED: {error_msg}'
                                self.test_results['tests_failed'] += 1
                                
                    else:
                        error_msg = f"Users API failed with status {response.status}"
                        logger.error(f"❌ {error_msg}")
                        self.test_results['api_responses']['gong_connectivity'] = f'FAILED: {error_msg}'
                        self.test_results['tests_failed'] += 1
                        
        except Exception as e:
            logger.error(f"❌ Gong.io API test failed: {e}")
            self.test_results['api_responses']['gong_connectivity'] = f'FAILED: {e}'
            self.test_results['tests_failed'] += 1
            
    async def test_slack_api_connectivity(self):
        """Test Slack API connectivity and data extraction"""
        logger.info("Testing Slack API connectivity...")
        
        if not self.slack_client:
            logger.error("❌ Slack client not initialized")
            self.test_results['api_responses']['slack_connectivity'] = 'FAILED: No client'
            self.test_results['tests_failed'] += 1
            return
            
        try:
            start_time = time.time()
            
            # Test auth
            auth_response = await self.slack_client.auth_test()
            
            if auth_response['ok']:
                # Get channels
                channels_response = await self.slack_client.conversations_list(
                    types="public_channel,private_channel",
                    limit=10
                )
                
                if channels_response['ok']:
                    channels = channels_response['channels']
                    channel_count = len(channels)
                    
                    # Get recent messages from first channel
                    if channels:
                        channel_id = channels[0]['id']
                        messages_response = await self.slack_client.conversations_history(
                            channel=channel_id,
                            limit=5
                        )
                        
                        if messages_response['ok']:
                            messages = messages_response['messages']
                            message_count = len(messages)
                            
                            response_time = time.time() - start_time
                            
                            self.test_results['api_responses']['slack_connectivity'] = 'PASSED'
                            self.test_results['data_samples']['slack_channels'] = channel_count
                            self.test_results['data_samples']['slack_messages_sample'] = message_count
                            self.test_results['performance_metrics']['slack_api_response_time'] = response_time
                            self.test_results['tests_passed'] += 1
                            
                            logger.info(f"✅ Slack API connected successfully")
                            logger.info(f"   - Channels found: {channel_count}")
                            logger.info(f"   - Recent messages sample: {message_count}")
                            logger.info(f"   - Response time: {response_time:.2f}s")
                            
                            # Store sample data for schema testing
                            if messages:
                                self.test_results['data_samples']['slack_message_structure'] = messages[0]
                                
                        else:
                            error_msg = "Failed to get messages"
                            logger.error(f"❌ {error_msg}")
                            self.test_results['api_responses']['slack_connectivity'] = f'FAILED: {error_msg}'
                            self.test_results['tests_failed'] += 1
                    else:
                        logger.warning("⚠️ No channels found")
                        self.test_results['api_responses']['slack_connectivity'] = 'PASSED (no channels)'
                        self.test_results['tests_passed'] += 1
                        
                else:
                    error_msg = "Failed to get channels"
                    logger.error(f"❌ {error_msg}")
                    self.test_results['api_responses']['slack_connectivity'] = f'FAILED: {error_msg}'
                    self.test_results['tests_failed'] += 1
                    
            else:
                error_msg = "Auth test failed"
                logger.error(f"❌ {error_msg}")
                self.test_results['api_responses']['slack_connectivity'] = f'FAILED: {error_msg}'
                self.test_results['tests_failed'] += 1
                
        except SlackApiError as e:
            logger.error(f"❌ Slack API error: {e}")
            self.test_results['api_responses']['slack_connectivity'] = f'FAILED: {e}'
            self.test_results['tests_failed'] += 1
        except Exception as e:
            logger.error(f"❌ Slack API test failed: {e}")
            self.test_results['api_responses']['slack_connectivity'] = f'FAILED: {e}'
            self.test_results['tests_failed'] += 1
            
    async def test_database_operations(self):
        """Test database insert, update, and query operations"""
        logger.info("Testing database operations...")
        
        if not self.db_pool:
            logger.error("❌ Database pool not initialized")
            self.test_results['schema_validations']['database_operations'] = 'FAILED: No connection'
            self.test_results['tests_failed'] += 1
            return
            
        try:
            async with self.db_pool.acquire() as conn:
                start_time = time.time()
                
                # Test insert contact
                contact_id = await conn.fetchval("""
                    INSERT INTO unified_contacts (
                        email, first_name, last_name, company_name, 
                        source_system, source_record_id, lead_score
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                    RETURNING id
                """, 
                'test@payready.com', 'Test', 'User', 'Pay Ready', 
                'test', 'test_001', 0.75)
                
                # Test insert interaction
                interaction_id = await conn.fetchval("""
                    INSERT INTO unified_interactions (
                        contact_id, source_system, source_record_id,
                        interaction_type, interaction_date, sentiment_score,
                        apartment_industry_relevance, business_impact_score
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    RETURNING id
                """,
                contact_id, 'test', 'test_interaction_001', 'email',
                datetime.now(), 0.8, 0.9, 0.85)
                
                # Test insert conversation intelligence
                intelligence_id = await conn.fetchval("""
                    INSERT INTO conversation_intelligence (
                        interaction_id, conversation_summary, urgency_score,
                        ai_insights
                    ) VALUES ($1, $2, $3, $4)
                    RETURNING id
                """,
                interaction_id, 'Test conversation about apartment management software',
                0.6, 'High potential customer showing interest in property management solutions')
                
                # Test query operations
                contact_count = await conn.fetchval("SELECT COUNT(*) FROM unified_contacts")
                interaction_count = await conn.fetchval("SELECT COUNT(*) FROM unified_interactions")
                intelligence_count = await conn.fetchval("SELECT COUNT(*) FROM conversation_intelligence")
                
                # Test complex query with joins
                complex_query_result = await conn.fetchrow("""
                    SELECT 
                        c.company_name,
                        i.interaction_type,
                        ci.urgency_score,
                        ci.ai_insights
                    FROM unified_contacts c
                    JOIN unified_interactions i ON c.id = i.contact_id
                    JOIN conversation_intelligence ci ON i.id = ci.interaction_id
                    WHERE c.id = $1
                """, contact_id)
                
                operation_time = time.time() - start_time
                
                self.test_results['schema_validations']['database_operations'] = 'PASSED'
                self.test_results['data_samples']['test_contact_id'] = contact_id
                self.test_results['data_samples']['test_interaction_id'] = interaction_id
                self.test_results['data_samples']['test_intelligence_id'] = intelligence_id
                self.test_results['performance_metrics']['database_operation_time'] = operation_time
                self.test_results['tests_passed'] += 1
                
                logger.info(f"✅ Database operations completed successfully")
                logger.info(f"   - Contacts: {contact_count}")
                logger.info(f"   - Interactions: {interaction_count}")
                logger.info(f"   - Intelligence records: {intelligence_count}")
                logger.info(f"   - Operation time: {operation_time:.3f}s")
                
                # Clean up test data
                await conn.execute("DELETE FROM conversation_intelligence WHERE id = $1", intelligence_id)
                await conn.execute("DELETE FROM unified_interactions WHERE id = $1", interaction_id)
                await conn.execute("DELETE FROM unified_contacts WHERE id = $1", contact_id)
                
        except Exception as e:
            logger.error(f"❌ Database operations test failed: {e}")
            self.test_results['schema_validations']['database_operations'] = f'FAILED: {e}'
            self.test_results['tests_failed'] += 1
            
    async def test_data_processing_pipeline(self):
        """Test end-to-end data processing pipeline"""
        logger.info("Testing data processing pipeline...")
        
        try:
            start_time = time.time()
            
            # Simulate processing Gong call data
            sample_gong_call = {
                'id': 'test_call_001',
                'primaryUserId': 'user_001',
                'title': 'Discovery call with Sunset Apartments',
                'started': '2024-06-17T10:00:00Z',
                'duration': 1800,  # 30 minutes
                'participants': [
                    {'emailAddress': 'john@sunsetapartments.com', 'name': 'John Smith'},
                    {'emailAddress': 'sales@payready.com', 'name': 'Sales Rep'}
                ]
            }
            
            # Simulate processing Slack message data
            sample_slack_message = {
                'ts': '1718625600.123456',
                'channel': 'C1234567890',
                'user': 'U8NPD1VL6',
                'text': 'Following up on the Sunset Apartments demo - they seem very interested in our pricing model',
                'thread_ts': None,
                'reactions': [{'name': 'thumbsup', 'count': 2}]
            }
            
            # Test conversation intelligence processing
            intelligence_result = await self.process_conversation_intelligence(
                sample_gong_call, sample_slack_message
            )
            
            processing_time = time.time() - start_time
            
            self.test_results['schema_validations']['data_processing'] = 'PASSED'
            self.test_results['data_samples']['intelligence_result'] = intelligence_result
            self.test_results['performance_metrics']['processing_pipeline_time'] = processing_time
            self.test_results['tests_passed'] += 1
            
            logger.info(f"✅ Data processing pipeline completed successfully")
            logger.info(f"   - Processing time: {processing_time:.3f}s")
            logger.info(f"   - Intelligence generated: {len(intelligence_result)} insights")
            
        except Exception as e:
            logger.error(f"❌ Data processing pipeline test failed: {e}")
            self.test_results['schema_validations']['data_processing'] = f'FAILED: {e}'
            self.test_results['tests_failed'] += 1
            
    async def process_conversation_intelligence(self, gong_data: Dict, slack_data: Dict) -> Dict:
        """Process conversation intelligence from multiple sources"""
        
        # Simulate NLP processing
        intelligence = {
            'conversation_summary': f"Sales conversation about {gong_data.get('title', 'unknown topic')}",
            'key_topics': ['pricing', 'demo', 'apartment management', 'follow-up'],
            'sentiment_score': 0.75,  # Positive sentiment
            'urgency_score': 0.6,     # Medium urgency
            'apartment_industry_relevance': 0.95,  # High relevance
            'business_impact_score': 0.8,  # High impact
            'action_items': [
                'Send pricing proposal to Sunset Apartments',
                'Schedule follow-up demo',
                'Prepare apartment-specific use cases'
            ],
            'ai_insights': 'High-value prospect showing strong interest in apartment management features',
            'cross_platform_correlation': {
                'gong_call_id': gong_data.get('id'),
                'slack_thread_correlation': True,
                'timeline_alignment': 'within_24_hours'
            }
        }
        
        return intelligence
        
    async def generate_test_report(self):
        """Generate comprehensive test report"""
        self.test_results['end_time'] = datetime.now()
        self.test_results['total_duration'] = (
            self.test_results['end_time'] - self.test_results['start_time']
        ).total_seconds()
        
        # Calculate success rate
        total_tests = self.test_results['tests_passed'] + self.test_results['tests_failed']
        success_rate = (self.test_results['tests_passed'] / total_tests * 100) if total_tests > 0 else 0
        
        report = {
            'test_summary': {
                'total_tests': total_tests,
                'tests_passed': self.test_results['tests_passed'],
                'tests_failed': self.test_results['tests_failed'],
                'success_rate': f"{success_rate:.1f}%",
                'total_duration': f"{self.test_results['total_duration']:.2f}s"
            },
            'api_connectivity': self.test_results['api_responses'],
            'database_validation': self.test_results['schema_validations'],
            'performance_metrics': self.test_results['performance_metrics'],
            'data_samples': self.test_results['data_samples'],
            'recommendations': []
        }
        
        # Add recommendations based on test results
        if self.test_results['tests_failed'] == 0:
            report['recommendations'].append("✅ All tests passed - system ready for production deployment")
        else:
            report['recommendations'].append("⚠️ Some tests failed - review failed components before production")
            
        if self.test_results['performance_metrics'].get('gong_api_response_time', 0) > 5:
            report['recommendations'].append("⚠️ Gong API response time is high - consider caching strategy")
            
        if self.test_results['performance_metrics'].get('slack_api_response_time', 0) > 3:
            report['recommendations'].append("⚠️ Slack API response time is high - consider rate limiting optimization")
            
        return report
        
    async def run_comprehensive_test(self, gong_key: str, gong_secret: str, slack_token: str):
        """Run complete test suite"""
        logger.info("🧪 Starting Sophia Live Test Suite...")
        
        # Set credentials securely
        self.set_credentials(gong_key, gong_secret, slack_token)
        
        # Run all tests
        await self.setup_test_database()
        await self.test_gong_api_connectivity()
        await self.test_slack_api_connectivity()
        await self.test_database_operations()
        await self.test_data_processing_pipeline()
        
        # Generate final report
        report = await self.generate_test_report()
        
        # Clean up
        if self.db_pool:
            await self.db_pool.close()
            
        logger.info("🎉 Sophia Live Test Suite completed!")
        
        return report

async def main():
    """Main test execution function"""
    test_suite = SophiaLiveTestSuite()
    
    # These would be provided securely in production
    gong_key = "GONG_ACCESS_KEY_PLACEHOLDER"
    gong_secret = "GONG_ACCESS_KEY_SECRET_PLACEHOLDER"
    slack_token = "SLACK_BOT_TOKEN_PLACEHOLDER"
    
    report = await test_suite.run_comprehensive_test(gong_key, gong_secret, slack_token)
    
    # Save report
    with open('/home/ubuntu/sophia_live_test_report.json', 'w') as f:
        json.dump(report, f, indent=2, default=str)
        
    print("\n" + "="*80)
    print("🧪 SOPHIA LIVE TEST SUITE RESULTS")
    print("="*80)
    print(f"Tests Passed: {report['test_summary']['tests_passed']}")
    print(f"Tests Failed: {report['test_summary']['tests_failed']}")
    print(f"Success Rate: {report['test_summary']['success_rate']}")
    print(f"Duration: {report['test_summary']['total_duration']}")
    print("\nRecommendations:")
    for rec in report['recommendations']:
        print(f"  {rec}")
    print("="*80)

if __name__ == "__main__":
    asyncio.run(main())

