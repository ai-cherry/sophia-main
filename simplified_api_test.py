#!/usr/bin/env python3
"""
Simplified Live API Test - Direct API Testing Without Database Dependencies
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import aiohttp
from slack_sdk.web.async_client import AsyncWebClient
from slack_sdk.errors import SlackApiError

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimplifiedAPITest:
    """Simplified API testing without database dependencies"""
    
    def __init__(self):
        self.test_results = {
            'start_time': datetime.now(),
            'tests_passed': 0,
            'tests_failed': 0,
            'api_responses': {},
            'data_samples': {},
            'performance_metrics': {}
        }
        
        # API credentials
        self.gong_access_key = "GONG_ACCESS_KEY_PLACEHOLDER"
        self.gong_access_key_secret = "GONG_ACCESS_KEY_SECRET_PLACEHOLDER"
        self.slack_bot_token = "SLACK_BOT_TOKEN_PLACEHOLDER"
        
        self.slack_client = AsyncWebClient(token=self.slack_bot_token)
        
    async def test_gong_api_comprehensive(self):
        """Comprehensive Gong.io API testing"""
        logger.info("🔍 Testing Gong.io API comprehensively...")
        
        try:
            start_time = time.time()
            
            async with aiohttp.ClientSession() as session:
                auth = aiohttp.BasicAuth(self.gong_access_key, self.gong_access_key_secret)
                
                # Test 1: Get users
                logger.info("  Testing users endpoint...")
                async with session.get(
                    'https://api.gong.io/v2/users',
                    auth=auth,
                    headers={'Content-Type': 'application/json'}
                ) as response:
                    
                    if response.status == 200:
                        users_data = await response.json()
                        user_count = len(users_data.get('users', []))
                        self.test_results['data_samples']['gong_users'] = user_count
                        logger.info(f"    ✅ Found {user_count} users")
                        
                        # Store sample user data
                        if users_data.get('users'):
                            sample_user = users_data['users'][0]
                            self.test_results['data_samples']['gong_user_structure'] = {
                                'id': sample_user.get('id'),
                                'emailAddress': sample_user.get('emailAddress'),
                                'firstName': sample_user.get('firstName'),
                                'lastName': sample_user.get('lastName'),
                                'active': sample_user.get('active')
                            }
                    else:
                        logger.error(f"    ❌ Users API failed: {response.status}")
                        self.test_results['tests_failed'] += 1
                        return
                
                # Test 2: Get calls with different time ranges
                logger.info("  Testing calls endpoint...")
                
                # Last 7 days
                from_date = (datetime.now() - timedelta(days=7)).isoformat()
                to_date = datetime.now().isoformat()
                
                calls_payload = {
                    "filter": {
                        "fromDateTime": from_date,
                        "toDateTime": to_date
                    },
                    "cursor": {
                        "limit": 20
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
                        self.test_results['data_samples']['gong_calls_7_days'] = call_count
                        logger.info(f"    ✅ Found {call_count} calls in last 7 days")
                        
                        # Store sample call data
                        if calls_data.get('calls'):
                            sample_call = calls_data['calls'][0]
                            self.test_results['data_samples']['gong_call_structure'] = {
                                'id': sample_call.get('id'),
                                'title': sample_call.get('title'),
                                'started': sample_call.get('started'),
                                'duration': sample_call.get('duration'),
                                'primaryUserId': sample_call.get('primaryUserId'),
                                'participants': len(sample_call.get('participants', []))
                            }
                    else:
                        logger.error(f"    ❌ Calls API failed: {calls_response.status}")
                        self.test_results['tests_failed'] += 1
                        return
                
                # Test 3: Get larger dataset (last 30 days)
                logger.info("  Testing larger dataset (30 days)...")
                
                from_date_30 = (datetime.now() - timedelta(days=30)).isoformat()
                calls_payload_30 = {
                    "filter": {
                        "fromDateTime": from_date_30,
                        "toDateTime": to_date
                    },
                    "cursor": {
                        "limit": 100
                    }
                }
                
                async with session.post(
                    'https://api.gong.io/v2/calls',
                    auth=auth,
                    headers={'Content-Type': 'application/json'},
                    json=calls_payload_30
                ) as calls_30_response:
                    
                    if calls_30_response.status == 200:
                        calls_30_data = await calls_30_response.json()
                        call_count_30 = len(calls_30_data.get('calls', []))
                        self.test_results['data_samples']['gong_calls_30_days'] = call_count_30
                        logger.info(f"    ✅ Found {call_count_30} calls in last 30 days")
                        
                        # Check for pagination
                        records = calls_30_data.get('records', {})
                        total_records = records.get('totalRecords', 0)
                        cursor_info = records.get('cursor', {})
                        
                        self.test_results['data_samples']['gong_total_records'] = total_records
                        self.test_results['data_samples']['gong_pagination_available'] = bool(cursor_info)
                        
                        logger.info(f"    📊 Total records available: {total_records}")
                        logger.info(f"    📄 Pagination available: {bool(cursor_info)}")
                        
                    else:
                        logger.error(f"    ❌ 30-day calls API failed: {calls_30_response.status}")
                
                response_time = time.time() - start_time
                self.test_results['performance_metrics']['gong_api_response_time'] = response_time
                self.test_results['api_responses']['gong_connectivity'] = 'PASSED'
                self.test_results['tests_passed'] += 1
                
                logger.info(f"  ✅ Gong API test completed in {response_time:.2f}s")
                
        except Exception as e:
            logger.error(f"❌ Gong API test failed: {e}")
            self.test_results['api_responses']['gong_connectivity'] = f'FAILED: {e}'
            self.test_results['tests_failed'] += 1
            
    async def test_slack_api_comprehensive(self):
        """Comprehensive Slack API testing"""
        logger.info("🔍 Testing Slack API comprehensively...")
        
        try:
            start_time = time.time()
            
            # Test 1: Auth test
            logger.info("  Testing authentication...")
            auth_response = await self.slack_client.auth_test()
            
            if auth_response['ok']:
                team_info = auth_response.get('team', 'Unknown')
                user_info = auth_response.get('user', 'Unknown')
                logger.info(f"    ✅ Authenticated as {user_info} in team {team_info}")
                self.test_results['data_samples']['slack_auth_info'] = {
                    'team': team_info,
                    'user': user_info,
                    'user_id': auth_response.get('user_id')
                }
            else:
                logger.error("    ❌ Authentication failed")
                self.test_results['tests_failed'] += 1
                return
            
            # Test 2: Get channels
            logger.info("  Testing channels list...")
            channels_response = await self.slack_client.conversations_list(
                types="public_channel,private_channel",
                limit=50
            )
            
            if channels_response['ok']:
                channels = channels_response['channels']
                channel_count = len(channels)
                self.test_results['data_samples']['slack_channels'] = channel_count
                logger.info(f"    ✅ Found {channel_count} channels")
                
                # Analyze channel types
                public_channels = [c for c in channels if not c.get('is_private', False)]
                private_channels = [c for c in channels if c.get('is_private', False)]
                
                self.test_results['data_samples']['slack_public_channels'] = len(public_channels)
                self.test_results['data_samples']['slack_private_channels'] = len(private_channels)
                
                logger.info(f"    📊 Public: {len(public_channels)}, Private: {len(private_channels)}")
                
                # Store sample channel data
                if channels:
                    sample_channel = channels[0]
                    self.test_results['data_samples']['slack_channel_structure'] = {
                        'id': sample_channel.get('id'),
                        'name': sample_channel.get('name'),
                        'is_private': sample_channel.get('is_private'),
                        'num_members': sample_channel.get('num_members'),
                        'created': sample_channel.get('created')
                    }
            else:
                logger.error("    ❌ Channels list failed")
                self.test_results['tests_failed'] += 1
                return
            
            # Test 3: Get messages from active channels
            logger.info("  Testing message history...")
            total_messages = 0
            
            for channel in channels[:5]:  # Test first 5 channels
                try:
                    messages_response = await self.slack_client.conversations_history(
                        channel=channel['id'],
                        limit=10
                    )
                    
                    if messages_response['ok']:
                        messages = messages_response['messages']
                        total_messages += len(messages)
                        
                        # Store sample message data from first channel with messages
                        if messages and 'slack_message_structure' not in self.test_results['data_samples']:
                            sample_message = messages[0]
                            self.test_results['data_samples']['slack_message_structure'] = {
                                'ts': sample_message.get('ts'),
                                'user': sample_message.get('user'),
                                'text': sample_message.get('text', '')[:100] + '...' if len(sample_message.get('text', '')) > 100 else sample_message.get('text', ''),
                                'type': sample_message.get('type'),
                                'thread_ts': sample_message.get('thread_ts'),
                                'reactions': len(sample_message.get('reactions', []))
                            }
                            
                except SlackApiError as e:
                    logger.warning(f"    ⚠️ Could not access channel {channel.get('name', 'unknown')}: {e}")
                    continue
            
            self.test_results['data_samples']['slack_total_messages_sampled'] = total_messages
            logger.info(f"    ✅ Sampled {total_messages} messages from accessible channels")
            
            # Test 4: Get users
            logger.info("  Testing users list...")
            users_response = await self.slack_client.users_list(limit=50)
            
            if users_response['ok']:
                users = users_response['members']
                user_count = len(users)
                active_users = [u for u in users if not u.get('deleted', False)]
                
                self.test_results['data_samples']['slack_users'] = user_count
                self.test_results['data_samples']['slack_active_users'] = len(active_users)
                
                logger.info(f"    ✅ Found {user_count} users ({len(active_users)} active)")
                
                # Store sample user data
                if active_users:
                    sample_user = active_users[0]
                    self.test_results['data_samples']['slack_user_structure'] = {
                        'id': sample_user.get('id'),
                        'name': sample_user.get('name'),
                        'real_name': sample_user.get('real_name'),
                        'is_bot': sample_user.get('is_bot'),
                        'is_admin': sample_user.get('is_admin')
                    }
            
            response_time = time.time() - start_time
            self.test_results['performance_metrics']['slack_api_response_time'] = response_time
            self.test_results['api_responses']['slack_connectivity'] = 'PASSED'
            self.test_results['tests_passed'] += 1
            
            logger.info(f"  ✅ Slack API test completed in {response_time:.2f}s")
            
        except SlackApiError as e:
            logger.error(f"❌ Slack API error: {e}")
            self.test_results['api_responses']['slack_connectivity'] = f'FAILED: {e}'
            self.test_results['tests_failed'] += 1
        except Exception as e:
            logger.error(f"❌ Slack API test failed: {e}")
            self.test_results['api_responses']['slack_connectivity'] = f'FAILED: {e}'
            self.test_results['tests_failed'] += 1
            
    async def analyze_data_integration_opportunities(self):
        """Analyze opportunities for data integration"""
        logger.info("🔍 Analyzing data integration opportunities...")
        
        analysis = {
            'gong_data_potential': {},
            'slack_data_potential': {},
            'integration_opportunities': [],
            'schema_recommendations': []
        }
        
        # Analyze Gong data potential
        gong_calls = self.test_results['data_samples'].get('gong_calls_30_days', 0)
        gong_users = self.test_results['data_samples'].get('gong_users', 0)
        gong_total = self.test_results['data_samples'].get('gong_total_records', 0)
        
        analysis['gong_data_potential'] = {
            'recent_calls': gong_calls,
            'total_users': gong_users,
            'total_available_records': gong_total,
            'estimated_monthly_volume': gong_calls * 1.2,  # Extrapolate
            'data_richness': 'HIGH' if gong_total > 1000 else 'MEDIUM' if gong_total > 100 else 'LOW'
        }
        
        # Analyze Slack data potential
        slack_channels = self.test_results['data_samples'].get('slack_channels', 0)
        slack_users = self.test_results['data_samples'].get('slack_active_users', 0)
        slack_messages = self.test_results['data_samples'].get('slack_total_messages_sampled', 0)
        
        analysis['slack_data_potential'] = {
            'active_channels': slack_channels,
            'active_users': slack_users,
            'message_sample': slack_messages,
            'estimated_daily_messages': slack_messages * 10,  # Extrapolate from sample
            'collaboration_level': 'HIGH' if slack_channels > 20 else 'MEDIUM' if slack_channels > 10 else 'LOW'
        }
        
        # Integration opportunities
        if gong_total > 0 and slack_channels > 0:
            analysis['integration_opportunities'] = [
                'Cross-platform conversation threading',
                'Customer journey mapping across Gong calls and Slack discussions',
                'Sales team collaboration analysis',
                'Deal progression tracking with team coordination',
                'Customer sentiment analysis across touchpoints',
                'Automated follow-up recommendations',
                'Team performance optimization insights'
            ]
        
        # Schema recommendations
        analysis['schema_recommendations'] = [
            'unified_contacts table with cross-platform correlation',
            'unified_interactions table with source system tracking',
            'conversation_intelligence table for AI insights',
            'cross_platform_threads table for conversation correlation',
            'business_intelligence_metrics table for KPI tracking'
        ]
        
        self.test_results['integration_analysis'] = analysis
        logger.info("  ✅ Integration analysis completed")
        
        return analysis
        
    async def generate_comprehensive_report(self):
        """Generate comprehensive test and analysis report"""
        self.test_results['end_time'] = datetime.now()
        self.test_results['total_duration'] = (
            self.test_results['end_time'] - self.test_results['start_time']
        ).total_seconds()
        
        # Calculate success rate
        total_tests = self.test_results['tests_passed'] + self.test_results['tests_failed']
        success_rate = (self.test_results['tests_passed'] / total_tests * 100) if total_tests > 0 else 0
        
        report = {
            'executive_summary': {
                'test_status': 'PASSED' if self.test_results['tests_failed'] == 0 else 'PARTIAL',
                'success_rate': f"{success_rate:.1f}%",
                'total_duration': f"{self.test_results['total_duration']:.2f}s",
                'readiness_assessment': 'PRODUCTION_READY' if success_rate >= 100 else 'NEEDS_REVIEW'
            },
            'api_connectivity_results': self.test_results['api_responses'],
            'data_availability': self.test_results['data_samples'],
            'performance_metrics': self.test_results['performance_metrics'],
            'integration_analysis': self.test_results.get('integration_analysis', {}),
            'recommendations': []
        }
        
        # Generate recommendations
        if success_rate >= 100:
            report['recommendations'].append("✅ All API connections successful - ready for production integration")
        
        gong_total = self.test_results['data_samples'].get('gong_total_records', 0)
        if gong_total > 1000:
            report['recommendations'].append(f"🚀 Rich Gong dataset available ({gong_total} records) - high value for conversation intelligence")
        
        slack_channels = self.test_results['data_samples'].get('slack_channels', 0)
        if slack_channels > 10:
            report['recommendations'].append(f"💬 Active Slack workspace ({slack_channels} channels) - excellent for team collaboration analysis")
        
        if gong_total > 0 and slack_channels > 0:
            report['recommendations'].append("🔗 Cross-platform integration highly recommended - significant business intelligence potential")
        
        # Performance recommendations
        gong_time = self.test_results['performance_metrics'].get('gong_api_response_time', 0)
        slack_time = self.test_results['performance_metrics'].get('slack_api_response_time', 0)
        
        if gong_time > 5:
            report['recommendations'].append("⚠️ Gong API response time high - implement caching strategy")
        if slack_time > 3:
            report['recommendations'].append("⚠️ Slack API response time high - optimize rate limiting")
        
        return report
        
    async def run_live_test(self):
        """Run complete live API test"""
        logger.info("🧪 Starting Sophia Live API Test...")
        
        await self.test_gong_api_comprehensive()
        await self.test_slack_api_comprehensive()
        await self.analyze_data_integration_opportunities()
        
        report = await self.generate_comprehensive_report()
        
        logger.info("🎉 Sophia Live API Test completed!")
        
        return report

async def main():
    """Main execution function"""
    test = SimplifiedAPITest()
    report = await test.run_live_test()
    
    # Save report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f'/home/ubuntu/sophia_live_api_test_{timestamp}.json'
    
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print("\n" + "="*80)
    print("🧪 SOPHIA LIVE API TEST RESULTS")
    print("="*80)
    print(f"Status: {report['executive_summary']['test_status']}")
    print(f"Success Rate: {report['executive_summary']['success_rate']}")
    print(f"Duration: {report['executive_summary']['total_duration']}")
    print(f"Readiness: {report['executive_summary']['readiness_assessment']}")
    print("\n📊 Data Availability:")
    
    data = report['data_availability']
    if 'gong_total_records' in data:
        print(f"  Gong Records: {data['gong_total_records']}")
    if 'slack_channels' in data:
        print(f"  Slack Channels: {data['slack_channels']}")
    if 'slack_active_users' in data:
        print(f"  Slack Users: {data['slack_active_users']}")
    
    print("\n🚀 Recommendations:")
    for rec in report['recommendations']:
        print(f"  {rec}")
    
    print(f"\n📄 Full report saved to: {report_file}")
    print("="*80)
    
    return report_file

if __name__ == "__main__":
    asyncio.run(main())

