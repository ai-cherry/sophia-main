#!/usr/bin/env python3
"""
Sophia Intelligence Processing Test Suite
Tests NLP, conversation intelligence, and apartment industry-specific analysis
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import sqlite3
import re
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class ConversationIntelligence:
    """Data class for conversation intelligence results"""
    sentiment_score: float
    urgency_score: float
    apartment_industry_relevance: float
    business_impact_score: float
    key_topics: List[str]
    action_items: List[str]
    competitive_mentions: List[str]
    customer_satisfaction_indicators: List[str]
    ai_summary: str

class SophiaIntelligenceProcessor:
    """Intelligence processing engine for Sophia AI"""
    
    def __init__(self):
        self.apartment_keywords = [
            'apartment', 'apartments', 'property', 'properties', 'rental', 'rentals',
            'tenant', 'tenants', 'lease', 'leasing', 'unit', 'units', 'building',
            'complex', 'portfolio', 'multifamily', 'resident', 'residents',
            'property management', 'rent collection', 'maintenance', 'vacancy',
            'occupancy', 'NOI', 'cap rate', 'rent roll', 'amenities'
        ]
        
        self.business_keywords = [
            'pricing', 'price', 'cost', 'budget', 'ROI', 'revenue', 'profit',
            'demo', 'demonstration', 'trial', 'implementation', 'integration',
            'contract', 'agreement', 'proposal', 'quote', 'decision', 'timeline',
            'features', 'benefits', 'solution', 'software', 'platform', 'system'
        ]
        
        self.urgency_keywords = [
            'urgent', 'ASAP', 'immediately', 'emergency', 'critical', 'deadline',
            'time-sensitive', 'priority', 'rush', 'escalate', 'issue', 'problem'
        ]
        
        self.positive_sentiment_keywords = [
            'excellent', 'great', 'fantastic', 'love', 'perfect', 'amazing',
            'impressed', 'satisfied', 'happy', 'pleased', 'excited', 'interested'
        ]
        
        self.negative_sentiment_keywords = [
            'terrible', 'awful', 'hate', 'disappointed', 'frustrated', 'angry',
            'concerned', 'worried', 'problem', 'issue', 'complaint', 'dissatisfied'
        ]
        
        self.competitive_companies = [
            'AppFolio', 'RentManager', 'Yardi', 'RealPage', 'Buildium', 'TenantCloud',
            'Rent Spree', 'Zego', 'Doorloop', 'Innago', 'Avail', 'Cozy', 'Zillow Rental Manager'
        ]
        
    def analyze_text_sentiment(self, text: str) -> float:
        """Analyze sentiment of text (-1 to 1)"""
        if not text:
            return 0.0
            
        text_lower = text.lower()
        positive_count = sum(1 for keyword in self.positive_sentiment_keywords if keyword in text_lower)
        negative_count = sum(1 for keyword in self.negative_sentiment_keywords if keyword in text_lower)
        
        total_words = len(text.split())
        if total_words == 0:
            return 0.0
            
        # Calculate sentiment score
        sentiment_score = (positive_count - negative_count) / max(total_words / 10, 1)
        return max(-1.0, min(1.0, sentiment_score))
        
    def analyze_urgency(self, text: str) -> float:
        """Analyze urgency level (0 to 1)"""
        if not text:
            return 0.0
            
        text_lower = text.lower()
        urgency_count = sum(1 for keyword in self.urgency_keywords if keyword in text_lower)
        
        # Check for exclamation marks and caps
        exclamation_count = text.count('!')
        caps_ratio = sum(1 for c in text if c.isupper()) / max(len(text), 1)
        
        urgency_score = (urgency_count * 0.3 + exclamation_count * 0.1 + caps_ratio * 0.2)
        return min(1.0, urgency_score)
        
    def analyze_apartment_industry_relevance(self, text: str) -> float:
        """Analyze apartment industry relevance (0 to 1)"""
        if not text:
            return 0.0
            
        text_lower = text.lower()
        apartment_count = sum(1 for keyword in self.apartment_keywords if keyword in text_lower)
        
        total_words = len(text.split())
        if total_words == 0:
            return 0.0
            
        relevance_score = apartment_count / max(total_words / 5, 1)
        return min(1.0, relevance_score)
        
    def analyze_business_impact(self, text: str) -> float:
        """Analyze business impact potential (0 to 1)"""
        if not text:
            return 0.0
            
        text_lower = text.lower()
        business_count = sum(1 for keyword in self.business_keywords if keyword in text_lower)
        
        # Look for monetary values
        money_pattern = r'\$[\d,]+|\d+k|\d+m|\d+ million|\d+ thousand'
        money_mentions = len(re.findall(money_pattern, text_lower))
        
        total_words = len(text.split())
        if total_words == 0:
            return 0.0
            
        impact_score = (business_count + money_mentions * 2) / max(total_words / 8, 1)
        return min(1.0, impact_score)
        
    def extract_key_topics(self, text: str) -> List[str]:
        """Extract key topics from text"""
        if not text:
            return []
            
        text_lower = text.lower()
        topics = []
        
        # Apartment-specific topics
        if any(keyword in text_lower for keyword in ['pricing', 'price', 'cost']):
            topics.append('pricing')
        if any(keyword in text_lower for keyword in ['demo', 'demonstration']):
            topics.append('product_demo')
        if any(keyword in text_lower for keyword in ['integration', 'implementation']):
            topics.append('technical_integration')
        if any(keyword in text_lower for keyword in ['maintenance', 'work_order']):
            topics.append('maintenance_management')
        if any(keyword in text_lower for keyword in ['rent', 'collection', 'payment']):
            topics.append('rent_collection')
        if any(keyword in text_lower for keyword in ['tenant', 'resident', 'communication']):
            topics.append('resident_communication')
        if any(keyword in text_lower for keyword in ['vacancy', 'occupancy', 'leasing']):
            topics.append('leasing_operations')
        if any(keyword in text_lower for keyword in ['reporting', 'analytics', 'dashboard']):
            topics.append('business_intelligence')
            
        return topics
        
    def extract_action_items(self, text: str) -> List[str]:
        """Extract action items from text"""
        if not text:
            return []
            
        action_items = []
        text_lower = text.lower()
        
        # Common action patterns
        if 'follow up' in text_lower or 'follow-up' in text_lower:
            action_items.append('Schedule follow-up meeting')
        if 'send' in text_lower and ('proposal' in text_lower or 'quote' in text_lower):
            action_items.append('Send pricing proposal')
        if 'demo' in text_lower and ('schedule' in text_lower or 'set up' in text_lower):
            action_items.append('Schedule product demonstration')
        if 'contract' in text_lower or 'agreement' in text_lower:
            action_items.append('Prepare contract documentation')
        if 'implementation' in text_lower or 'onboarding' in text_lower:
            action_items.append('Plan implementation timeline')
        if 'reference' in text_lower or 'case study' in text_lower:
            action_items.append('Provide customer references')
            
        return action_items
        
    def detect_competitive_mentions(self, text: str) -> List[str]:
        """Detect mentions of competitive companies"""
        if not text:
            return []
            
        text_lower = text.lower()
        mentioned_competitors = []
        
        for competitor in self.competitive_companies:
            if competitor.lower() in text_lower:
                mentioned_competitors.append(competitor)
                
        return mentioned_competitors
        
    def analyze_customer_satisfaction(self, text: str) -> List[str]:
        """Analyze customer satisfaction indicators"""
        if not text:
            return []
            
        indicators = []
        text_lower = text.lower()
        
        if any(keyword in text_lower for keyword in ['satisfied', 'happy', 'pleased']):
            indicators.append('positive_feedback')
        if any(keyword in text_lower for keyword in ['frustrated', 'disappointed', 'concerned']):
            indicators.append('negative_feedback')
        if any(keyword in text_lower for keyword in ['recommend', 'referral']):
            indicators.append('referral_potential')
        if any(keyword in text_lower for keyword in ['expand', 'additional', 'more']):
            indicators.append('expansion_opportunity')
        if any(keyword in text_lower for keyword in ['cancel', 'terminate', 'end']):
            indicators.append('churn_risk')
            
        return indicators
        
    def generate_ai_summary(self, text: str, intelligence: ConversationIntelligence) -> str:
        """Generate AI summary of conversation"""
        if not text:
            return "No content to analyze"
            
        summary_parts = []
        
        # Sentiment assessment
        if intelligence.sentiment_score > 0.3:
            summary_parts.append("Positive conversation")
        elif intelligence.sentiment_score < -0.3:
            summary_parts.append("Negative conversation")
        else:
            summary_parts.append("Neutral conversation")
            
        # Industry relevance
        if intelligence.apartment_industry_relevance > 0.7:
            summary_parts.append("highly relevant to apartment industry")
        elif intelligence.apartment_industry_relevance > 0.3:
            summary_parts.append("moderately relevant to apartment industry")
            
        # Business impact
        if intelligence.business_impact_score > 0.7:
            summary_parts.append("with high business impact potential")
        elif intelligence.business_impact_score > 0.3:
            summary_parts.append("with moderate business impact potential")
            
        # Key topics
        if intelligence.key_topics:
            summary_parts.append(f"discussing {', '.join(intelligence.key_topics[:3])}")
            
        # Urgency
        if intelligence.urgency_score > 0.5:
            summary_parts.append("requiring urgent attention")
            
        # Competitive mentions
        if intelligence.competitive_mentions:
            summary_parts.append(f"mentioning competitors: {', '.join(intelligence.competitive_mentions)}")
            
        return ". ".join(summary_parts).capitalize() + "."
        
    def process_conversation(self, text: str, title: str = "") -> ConversationIntelligence:
        """Process a conversation and return intelligence analysis"""
        full_text = f"{title} {text}".strip()
        
        # Analyze all components
        sentiment_score = self.analyze_text_sentiment(full_text)
        urgency_score = self.analyze_urgency(full_text)
        apartment_relevance = self.analyze_apartment_industry_relevance(full_text)
        business_impact = self.analyze_business_impact(full_text)
        key_topics = self.extract_key_topics(full_text)
        action_items = self.extract_action_items(full_text)
        competitive_mentions = self.detect_competitive_mentions(full_text)
        satisfaction_indicators = self.analyze_customer_satisfaction(full_text)
        
        # Create intelligence object
        intelligence = ConversationIntelligence(
            sentiment_score=sentiment_score,
            urgency_score=urgency_score,
            apartment_industry_relevance=apartment_relevance,
            business_impact_score=business_impact,
            key_topics=key_topics,
            action_items=action_items,
            competitive_mentions=competitive_mentions,
            customer_satisfaction_indicators=satisfaction_indicators,
            ai_summary=""
        )
        
        # Generate summary
        intelligence.ai_summary = self.generate_ai_summary(full_text, intelligence)
        
        return intelligence

class SophiaIntelligenceTestSuite:
    """Test suite for Sophia intelligence processing"""
    
    def __init__(self):
        self.processor = SophiaIntelligenceProcessor()
        self.test_results = {
            'start_time': datetime.now(),
            'tests_passed': 0,
            'tests_failed': 0,
            'processing_results': {},
            'performance_metrics': {},
            'sample_analyses': []
        }
        
    def create_test_conversations(self) -> List[Dict[str, str]]:
        """Create test conversations for analysis"""
        return [
            {
                'title': 'Discovery Call - Sunset Apartments',
                'content': '''
                Great call with John Smith from Sunset Apartments. They manage 250 units across 3 properties 
                and are currently using AppFolio but frustrated with their rent collection features. 
                Very interested in our automated collections and AI resident communication. 
                John mentioned they lose about $15k monthly due to late payments and manual follow-ups. 
                Excited to see a demo next week! They want to implement before their busy season.
                '''
            },
            {
                'title': 'Support Escalation - Urgent Issue',
                'content': '''
                URGENT! Customer reporting critical issue with payment processing. 
                Residents unable to pay rent online for the past 2 hours. 
                This is affecting 500+ units at Riverside Complex. 
                Customer is very frustrated and threatening to cancel contract. 
                Need immediate escalation to engineering team!
                '''
            },
            {
                'title': 'Pricing Discussion - Metro Properties',
                'content': '''
                Had a productive pricing discussion with Metro Properties. 
                They manage 1,200 units and are comparing us with RealPage and Yardi. 
                Our pricing is competitive at $2.50 per unit. 
                They love our maintenance workflow automation and resident portal features. 
                Concerned about implementation timeline - need to go live in 60 days. 
                Sending proposal tomorrow with implementation plan.
                '''
            },
            {
                'title': 'Customer Success Check-in',
                'content': '''
                Monthly check-in with Oakwood Apartments. 
                They've been using our platform for 6 months and are very satisfied. 
                Rent collection improved by 25% and maintenance response time down 40%. 
                Interested in expanding to their other 2 properties (150 additional units). 
                Great reference customer for future prospects!
                '''
            },
            {
                'title': 'Technical Integration Call',
                'content': '''
                Technical call with Pine Valley Management IT team. 
                Discussing API integration with their existing property management system. 
                Need to sync resident data, lease information, and payment history. 
                Some concerns about data security and compliance requirements. 
                Scheduled follow-up with our security team to address GDPR and SOC2 questions.
                '''
            },
            {
                'title': 'Competitive Analysis Discussion',
                'content': '''
                Prospect currently evaluating multiple solutions including Buildium and TenantCloud. 
                They like our AI features but concerned about pricing compared to Buildium. 
                Need to emphasize ROI and unique apartment industry focus. 
                Competitor analysis shows we have superior automation capabilities. 
                Preparing detailed comparison document for next meeting.
                '''
            }
        ]
        
    async def test_conversation_processing(self):
        """Test conversation processing capabilities"""
        logger.info("🧠 Testing conversation processing capabilities...")
        
        test_conversations = self.create_test_conversations()
        processing_results = []
        
        start_time = time.time()
        
        for i, conversation in enumerate(test_conversations):
            try:
                logger.info(f"  Processing conversation {i+1}: {conversation['title']}")
                
                # Process conversation
                intelligence = self.processor.process_conversation(
                    conversation['content'], 
                    conversation['title']
                )
                
                result = {
                    'title': conversation['title'],
                    'sentiment_score': intelligence.sentiment_score,
                    'urgency_score': intelligence.urgency_score,
                    'apartment_relevance': intelligence.apartment_industry_relevance,
                    'business_impact': intelligence.business_impact_score,
                    'key_topics': intelligence.key_topics,
                    'action_items': intelligence.action_items,
                    'competitive_mentions': intelligence.competitive_mentions,
                    'satisfaction_indicators': intelligence.customer_satisfaction_indicators,
                    'ai_summary': intelligence.ai_summary
                }
                
                processing_results.append(result)
                
                logger.info(f"    ✅ Processed: Sentiment={intelligence.sentiment_score:.2f}, "
                          f"Relevance={intelligence.apartment_industry_relevance:.2f}, "
                          f"Impact={intelligence.business_impact_score:.2f}")
                
            except Exception as e:
                logger.error(f"    ❌ Failed to process conversation {i+1}: {e}")
                self.test_results['tests_failed'] += 1
                continue
                
        processing_time = time.time() - start_time
        
        self.test_results['processing_results']['conversations_processed'] = len(processing_results)
        self.test_results['processing_results']['average_processing_time'] = processing_time / len(test_conversations)
        self.test_results['sample_analyses'] = processing_results
        self.test_results['performance_metrics']['total_processing_time'] = processing_time
        self.test_results['tests_passed'] += 1
        
        logger.info(f"  ✅ Processed {len(processing_results)} conversations in {processing_time:.2f}s")
        
    async def test_database_integration(self):
        """Test database integration with intelligence processing"""
        logger.info("🗄️ Testing database integration...")
        
        try:
            # Create in-memory database
            conn = sqlite3.connect(':memory:')
            cursor = conn.cursor()
            
            # Create intelligence table
            cursor.execute("""
                CREATE TABLE conversation_intelligence (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    content TEXT,
                    sentiment_score REAL,
                    urgency_score REAL,
                    apartment_industry_relevance REAL,
                    business_impact_score REAL,
                    key_topics TEXT,
                    action_items TEXT,
                    competitive_mentions TEXT,
                    customer_satisfaction_indicators TEXT,
                    ai_summary TEXT,
                    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Process and insert test data
            test_conversations = self.create_test_conversations()
            inserted_count = 0
            
            for conversation in test_conversations:
                intelligence = self.processor.process_conversation(
                    conversation['content'], 
                    conversation['title']
                )
                
                cursor.execute("""
                    INSERT INTO conversation_intelligence (
                        title, content, sentiment_score, urgency_score,
                        apartment_industry_relevance, business_impact_score,
                        key_topics, action_items, competitive_mentions,
                        customer_satisfaction_indicators, ai_summary
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    conversation['title'],
                    conversation['content'],
                    intelligence.sentiment_score,
                    intelligence.urgency_score,
                    intelligence.apartment_industry_relevance,
                    intelligence.business_impact_score,
                    json.dumps(intelligence.key_topics),
                    json.dumps(intelligence.action_items),
                    json.dumps(intelligence.competitive_mentions),
                    json.dumps(intelligence.customer_satisfaction_indicators),
                    intelligence.ai_summary
                ))
                
                inserted_count += 1
                
            # Test queries
            test_queries = [
                ("High urgency conversations", "SELECT COUNT(*) FROM conversation_intelligence WHERE urgency_score > 0.5"),
                ("Apartment relevant conversations", "SELECT COUNT(*) FROM conversation_intelligence WHERE apartment_industry_relevance > 0.7"),
                ("High business impact", "SELECT COUNT(*) FROM conversation_intelligence WHERE business_impact_score > 0.6"),
                ("Positive sentiment", "SELECT COUNT(*) FROM conversation_intelligence WHERE sentiment_score > 0.3"),
                ("Competitive mentions", "SELECT COUNT(*) FROM conversation_intelligence WHERE competitive_mentions != '[]'"),
                ("Average sentiment", "SELECT AVG(sentiment_score) FROM conversation_intelligence"),
                ("Average relevance", "SELECT AVG(apartment_industry_relevance) FROM conversation_intelligence")
            ]
            
            query_results = {}
            for query_name, query_sql in test_queries:
                cursor.execute(query_sql)
                result = cursor.fetchone()[0]
                query_results[query_name] = result
                logger.info(f"    {query_name}: {result}")
                
            conn.close()
            
            self.test_results['processing_results']['database_integration'] = {
                'status': 'SUCCESS',
                'records_inserted': inserted_count,
                'query_results': query_results
            }
            
            self.test_results['tests_passed'] += 1
            logger.info(f"  ✅ Database integration test passed - {inserted_count} records processed")
            
        except Exception as e:
            logger.error(f"  ❌ Database integration test failed: {e}")
            self.test_results['processing_results']['database_integration'] = {
                'status': 'FAILED',
                'error': str(e)
            }
            self.test_results['tests_failed'] += 1
            
    async def test_performance_benchmarks(self):
        """Test performance benchmarks for intelligence processing"""
        logger.info("⚡ Testing performance benchmarks...")
        
        # Create larger dataset for performance testing
        large_dataset = []
        base_conversations = self.create_test_conversations()
        
        # Replicate conversations to create larger dataset
        for i in range(50):  # 300 total conversations
            for conv in base_conversations:
                large_dataset.append({
                    'title': f"{conv['title']} - Iteration {i+1}",
                    'content': conv['content']
                })
                
        start_time = time.time()
        processed_count = 0
        
        for conversation in large_dataset:
            intelligence = self.processor.process_conversation(
                conversation['content'], 
                conversation['title']
            )
            processed_count += 1
            
        total_time = time.time() - start_time
        avg_time_per_conversation = total_time / processed_count
        conversations_per_second = processed_count / total_time
        
        self.test_results['performance_metrics']['large_dataset_processing'] = {
            'total_conversations': processed_count,
            'total_time': total_time,
            'avg_time_per_conversation': avg_time_per_conversation,
            'conversations_per_second': conversations_per_second
        }
        
        logger.info(f"  ✅ Processed {processed_count} conversations in {total_time:.2f}s")
        logger.info(f"  📊 Average: {avg_time_per_conversation:.4f}s per conversation")
        logger.info(f"  🚀 Throughput: {conversations_per_second:.1f} conversations/second")
        
        self.test_results['tests_passed'] += 1
        
    async def generate_intelligence_report(self):
        """Generate comprehensive intelligence processing report"""
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
                'intelligence_readiness': 'PRODUCTION_READY' if success_rate >= 100 else 'NEEDS_REVIEW'
            },
            'processing_capabilities': {
                'conversations_analyzed': self.test_results['processing_results'].get('conversations_processed', 0),
                'database_integration': self.test_results['processing_results'].get('database_integration', {}),
                'performance_metrics': self.test_results['performance_metrics']
            },
            'sample_analyses': self.test_results['sample_analyses'][:3],  # Top 3 examples
            'recommendations': []
        }
        
        # Generate recommendations
        if success_rate >= 100:
            report['recommendations'].append("✅ Intelligence processing fully operational - ready for production")
            
        perf_metrics = self.test_results['performance_metrics']
        if 'conversations_per_second' in perf_metrics.get('large_dataset_processing', {}):
            cps = perf_metrics['large_dataset_processing']['conversations_per_second']
            if cps > 10:
                report['recommendations'].append(f"🚀 High throughput achieved ({cps:.1f} conversations/sec) - excellent for real-time processing")
            elif cps > 5:
                report['recommendations'].append(f"✅ Good throughput ({cps:.1f} conversations/sec) - suitable for batch processing")
            else:
                report['recommendations'].append(f"⚠️ Low throughput ({cps:.1f} conversations/sec) - consider optimization")
                
        # Analyze sample results
        if self.test_results['sample_analyses']:
            avg_relevance = sum(a['apartment_relevance'] for a in self.test_results['sample_analyses']) / len(self.test_results['sample_analyses'])
            avg_impact = sum(a['business_impact'] for a in self.test_results['sample_analyses']) / len(self.test_results['sample_analyses'])
            
            if avg_relevance > 0.7:
                report['recommendations'].append(f"🏢 High apartment industry relevance detected ({avg_relevance:.2f}) - excellent for Pay Ready use cases")
            if avg_impact > 0.6:
                report['recommendations'].append(f"💰 High business impact potential identified ({avg_impact:.2f}) - valuable for revenue optimization")
                
        report['recommendations'].extend([
            "🔄 Implement real-time conversation processing pipeline",
            "📊 Deploy business intelligence dashboard with conversation insights",
            "🎯 Focus on apartment industry-specific terminology and use cases",
            "🤖 Integrate with Slack and Gong for automated conversation analysis"
        ])
        
        return report
        
    async def run_comprehensive_test(self):
        """Run comprehensive intelligence processing test"""
        logger.info("🧪 Starting Sophia Intelligence Processing Test...")
        
        await self.test_conversation_processing()
        await self.test_database_integration()
        await self.test_performance_benchmarks()
        
        report = await self.generate_intelligence_report()
        
        logger.info("🎉 Sophia Intelligence Processing Test completed!")
        
        return report

async def main():
    """Main execution function"""
    test_suite = SophiaIntelligenceTestSuite()
    report = await test_suite.run_comprehensive_test()
    
    # Save report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f'/home/ubuntu/sophia_intelligence_test_{timestamp}.json'
    
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print("\n" + "="*80)
    print("🧠 SOPHIA INTELLIGENCE PROCESSING TEST RESULTS")
    print("="*80)
    print(f"Status: {report['executive_summary']['test_status']}")
    print(f"Success Rate: {report['executive_summary']['success_rate']}")
    print(f"Duration: {report['executive_summary']['total_duration']}")
    print(f"Readiness: {report['executive_summary']['intelligence_readiness']}")
    
    print("\n🔍 Processing Capabilities:")
    capabilities = report['processing_capabilities']
    print(f"  Conversations Analyzed: {capabilities['conversations_analyzed']}")
    
    if 'large_dataset_processing' in capabilities['performance_metrics']:
        perf = capabilities['performance_metrics']['large_dataset_processing']
        print(f"  Throughput: {perf['conversations_per_second']:.1f} conversations/second")
        print(f"  Avg Processing Time: {perf['avg_time_per_conversation']:.4f}s per conversation")
    
    print("\n📊 Sample Analysis Results:")
    for i, analysis in enumerate(report['sample_analyses'], 1):
        print(f"  {i}. {analysis['title']}")
        print(f"     Sentiment: {analysis['sentiment_score']:.2f}, Relevance: {analysis['apartment_relevance']:.2f}")
        print(f"     Topics: {', '.join(analysis['key_topics'][:3])}")
    
    print("\n🚀 Recommendations:")
    for rec in report['recommendations']:
        print(f"  {rec}")
    
    print(f"\n📄 Full report saved to: {report_file}")
    print("="*80)
    
    return report_file

if __name__ == "__main__":
    asyncio.run(main())

