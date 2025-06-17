#!/usr/bin/env python3
"""
Fix Sophia Insights Generation - Handle Decimal JSON Serialization
"""

import asyncio
import asyncpg
import json
from datetime import datetime
import logging
from decimal import Decimal

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DecimalEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle Decimal types"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

async def fix_insights_generation():
    """Fix and complete Sophia insights generation"""
    
    db_config = {
        "host": "localhost",
        "port": 5432,
        "user": "postgres", 
        "password": "password",
        "database": "sophia_enhanced"
    }
    
    try:
        conn = await asyncpg.connect(**db_config)
        
        # Generate user insights with proper Decimal handling
        users = await conn.fetch("""
            SELECT u.user_id, u.first_name, u.last_name, u.title, u.role_category,
                   COUNT(p.call_id) as call_count,
                   AVG(c.duration_seconds) as avg_call_duration,
                   AVG(c.apartment_relevance) as avg_apartment_relevance
            FROM gong_users u
            LEFT JOIN gong_participants p ON u.email_address = p.email_address
            LEFT JOIN gong_calls c ON p.call_id = c.call_id
            WHERE u.pay_ready_employee = TRUE
            GROUP BY u.user_id, u.first_name, u.last_name, u.title, u.role_category
        """)
        
        for user in users:
            insights = {
                "performance_score": min(100, (user['call_count'] or 0) * 10),
                "apartment_expertise": round(float(user['avg_apartment_relevance'] or 0) * 100, 1),
                "avg_call_duration": round(float(user['avg_call_duration'] or 0) / 60, 1),
                "activity_level": "high" if (user['call_count'] or 0) > 10 else "moderate" if (user['call_count'] or 0) > 5 else "low",
                "recommendations": []
            }
            
            if float(user['avg_apartment_relevance'] or 0) > 0.8:
                insights["recommendations"].append("Apartment industry specialist - leverage for complex deals")
            if (user['call_count'] or 0) > 15:
                insights["recommendations"].append("High activity - consider for mentoring junior team members")
            if float(user['avg_call_duration'] or 0) > 3600:
                insights["recommendations"].append("Long call duration - excellent for complex negotiations")
            
            await conn.execute("""
                UPDATE gong_users 
                SET sophia_insights = $1,
                    last_activity = NOW()
                WHERE user_id = $2
            """, json.dumps(insights, cls=DecimalEncoder), user['user_id'])
        
        # Generate call insights with proper Decimal handling
        calls = await conn.fetch("""
            SELECT call_id, title, apartment_relevance, business_value, 
                   duration_seconds, call_outcome, competitive_mentions
            FROM gong_calls
            WHERE apartment_relevance > 0
        """)
        
        for call in calls:
            insights = {
                "apartment_relevance_score": round(float(call['apartment_relevance'] or 0) * 100, 1),
                "estimated_value": call['business_value'] or 0,
                "call_quality": "excellent" if (call['duration_seconds'] or 0) > 3000 else "good" if (call['duration_seconds'] or 0) > 1800 else "standard",
                "competitive_analysis": len(call['competitive_mentions'] or []) > 0,
                "key_insights": []
            }
            
            if float(call['apartment_relevance'] or 0) > 0.9:
                insights["key_insights"].append("High apartment industry relevance - priority follow-up")
            if call['competitive_mentions']:
                insights["key_insights"].append(f"Competitive mentions: {', '.join(call['competitive_mentions'])}")
            if call['call_outcome'] == 'closed_won':
                insights["key_insights"].append("Successful deal closure - analyze for best practices")
            
            await conn.execute("""
                UPDATE gong_calls 
                SET sophia_insights = $1
                WHERE call_id = $2
            """, json.dumps(insights, cls=DecimalEncoder), call['call_id'])
        
        # Get final statistics
        stats = await conn.fetchrow("""
            SELECT 
                (SELECT COUNT(*) FROM gong_users WHERE pay_ready_employee = TRUE) as payready_team,
                (SELECT COUNT(*) FROM gong_users WHERE user_type = 'apartment_client') as apartment_clients,
                (SELECT COUNT(*) FROM gong_calls WHERE apartment_relevance > 0.5) as relevant_calls,
                (SELECT COUNT(*) FROM gong_participants) as total_participants,
                (SELECT AVG(apartment_relevance) FROM gong_calls WHERE apartment_relevance > 0) as avg_relevance,
                (SELECT COUNT(*) FROM gong_calls WHERE call_outcome IS NOT NULL) as calls_with_outcomes,
                (SELECT SUM(business_value) FROM gong_calls) as total_business_value
        """)
        
        sample_users = await conn.fetch("""
            SELECT first_name, last_name, title, role_category, 
                   (sophia_insights->>'performance_score')::int as performance_score,
                   (sophia_insights->>'apartment_expertise')::float as apartment_expertise
            FROM gong_users 
            WHERE pay_ready_employee = TRUE AND sophia_insights IS NOT NULL
            ORDER BY (sophia_insights->>'performance_score')::int DESC
            LIMIT 5
        """)
        
        sample_calls = await conn.fetch("""
            SELECT title, apartment_relevance, business_value, call_outcome,
                   (sophia_insights->>'apartment_relevance_score')::float as relevance_score
            FROM gong_calls 
            WHERE apartment_relevance > 0.7 AND sophia_insights IS NOT NULL
            ORDER BY apartment_relevance DESC
            LIMIT 5
        """)
        
        await conn.close()
        
        print(f"✅ SOPHIA INSIGHTS GENERATION COMPLETE!")
        print(f"\n📊 FINAL ENHANCEMENT RESULTS:")
        print(f"   Pay Ready Team Members: {stats['payready_team']}")
        print(f"   Apartment Industry Clients: {stats['apartment_clients']}")
        print(f"   Apartment-Relevant Calls: {stats['relevant_calls']}")
        print(f"   Total Participants: {stats['total_participants']}")
        print(f"   Calls with Outcomes: {stats['calls_with_outcomes']}")
        print(f"   Average Apartment Relevance: {round(float(stats['avg_relevance']) * 100, 1)}%")
        print(f"   Total Business Value: ${stats['total_business_value']:,}")
        
        print(f"\n🏆 TOP PERFORMING TEAM MEMBERS:")
        for user in sample_users:
            print(f"   {user['first_name']} {user['last_name']} ({user['title']}) - Score: {user['performance_score']}, Apartment Expertise: {user['apartment_expertise']}%")
        
        print(f"\n🎯 HIGH-VALUE APARTMENT CALLS:")
        for call in sample_calls:
            print(f"   {call['title'][:60]}... - Relevance: {call['relevance_score']}% - Value: ${call['business_value']:,}")
        
        # Save results
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "enhancement_results": {k: float(v) if isinstance(v, Decimal) else v for k, v in dict(stats).items()},
            "top_performers": [dict(user) for user in sample_users],
            "high_value_calls": [dict(call) for call in sample_calls]
        }
        
        with open(f"sophia_insights_complete_{timestamp}.json", 'w') as f:
            json.dump(results, f, indent=2, default=str, cls=DecimalEncoder)
        
        print(f"\n💾 Results saved to: sophia_insights_complete_{timestamp}.json")
        print(f"\n🎉 CALL PARTICIPATION MAPPING AND SCHEMA ENHANCEMENT FULLY COMPLETE!")
        
        return True
        
    except Exception as e:
        logger.error(f"Error fixing insights generation: {str(e)}")
        return False

if __name__ == "__main__":
    asyncio.run(fix_insights_generation())

