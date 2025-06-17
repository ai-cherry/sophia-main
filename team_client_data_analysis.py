#!/usr/bin/env python3
"""
Team vs Client Data Analysis and Schema Review
Analyzes Gong data to distinguish Pay Ready team members from client contacts
"""

import asyncio
import asyncpg
import json
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TeamClientAnalyzer:
    """
    Analyzes Gong data to distinguish between Pay Ready team and client contacts
    """
    
    def __init__(self):
        self.db_config = {
            "host": "localhost",
            "port": 5432,
            "user": "postgres", 
            "password": "password",
            "database": "sophia_enhanced"
        }
    
    async def analyze_user_data(self) -> dict:
        """Analyze user data to identify team vs clients"""
        
        try:
            conn = await asyncpg.connect(**self.db_config)
            
            # Get all users with their email domains
            users = await conn.fetch("""
                SELECT user_id, email_address, first_name, last_name, title, 
                       SPLIT_PART(email_address, '@', 2) as email_domain
                FROM gong_users 
                ORDER BY email_address
            """)
            
            # Analyze email domains
            domain_analysis = {}
            for user in users:
                domain = user['email_domain']
                if domain not in domain_analysis:
                    domain_analysis[domain] = {
                        'count': 0,
                        'users': [],
                        'likely_type': 'unknown'
                    }
                domain_analysis[domain]['count'] += 1
                domain_analysis[domain]['users'].append({
                    'name': f"{user['first_name']} {user['last_name']}",
                    'title': user['title'],
                    'email': user['email_address']
                })
            
            # Classify domains
            for domain, data in domain_analysis.items():
                if any(keyword in domain.lower() for keyword in ['payready', 'pay-ready']):
                    data['likely_type'] = 'pay_ready_team'
                elif any(keyword in domain.lower() for keyword in ['apartment', 'property', 'rental', 'greystar', 'bozzuto', 'maa']):
                    data['likely_type'] = 'apartment_client'
                elif data['count'] == 1:
                    data['likely_type'] = 'external_contact'
                else:
                    data['likely_type'] = 'potential_client'
            
            # Get call participation analysis
            participation_analysis = await conn.fetch("""
                SELECT u.email_address, u.first_name, u.last_name, u.title,
                       COUNT(p.call_id) as total_calls,
                       COUNT(CASE WHEN LOWER(c.title) LIKE '%pay ready%' THEN 1 END) as payready_calls,
                       COUNT(CASE WHEN LOWER(c.title) LIKE ANY(ARRAY['%apartment%', '%rental%', '%property%']) THEN 1 END) as apartment_calls
                FROM gong_users u
                LEFT JOIN gong_participants p ON u.email_address = p.email_address
                LEFT JOIN gong_calls c ON p.call_id = c.call_id
                GROUP BY u.user_id, u.email_address, u.first_name, u.last_name, u.title
                ORDER BY total_calls DESC
            """)
            
            await conn.close()
            
            return {
                "total_users": len(users),
                "domain_analysis": domain_analysis,
                "participation_analysis": [dict(row) for row in participation_analysis],
                "recommendations": {
                    "schema_improvements": [
                        "Add 'user_type' column (pay_ready_team, apartment_client, external_contact)",
                        "Add 'company_type' column (internal, apartment_client, vendor, other)",
                        "Create separate tables for team_members and client_contacts",
                        "Add 'pay_ready_employee' boolean flag"
                    ],
                    "data_classification": [
                        "Identify Pay Ready email domains for automatic team classification",
                        "Create client company mapping based on email domains",
                        "Implement role-based classification (sales, support, executive)",
                        "Add apartment industry client identification"
                    ]
                }
            }
            
        except Exception as e:
            logger.error(f"Error in analyze_user_data: {str(e)}")
            return {"error": str(e)}
    
    async def get_schema_review(self) -> dict:
        """Review current database schema and suggest improvements"""
        
        try:
            conn = await asyncpg.connect(**self.db_config)
            
            # Get current schema for all Gong tables
            tables = ['gong_users', 'gong_calls', 'gong_participants', 'gong_workspaces']
            schema_info = {}
            
            for table in tables:
                columns = await conn.fetch("""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns 
                    WHERE table_name = $1 AND table_schema = 'public'
                    ORDER BY ordinal_position
                """, table)
                
                # Get sample data
                sample = await conn.fetch(f"SELECT * FROM {table} LIMIT 3")
                
                schema_info[table] = {
                    "columns": [dict(row) for row in columns],
                    "sample_data": [dict(row) for row in sample],
                    "record_count": await conn.fetchval(f"SELECT COUNT(*) FROM {table}")
                }
            
            await conn.close()
            
            # Generate improvement suggestions
            improvements = {
                "gong_users": {
                    "missing_columns": [
                        "user_type VARCHAR(50) - 'pay_ready_team', 'apartment_client', 'external_contact'",
                        "company_name VARCHAR(255) - Extracted from email domain or manually set",
                        "company_type VARCHAR(50) - 'internal', 'apartment_client', 'vendor', 'other'",
                        "pay_ready_employee BOOLEAN - True for Pay Ready team members",
                        "apartment_relevance DECIMAL(3,2) - Relevance score for apartment industry",
                        "role_category VARCHAR(50) - 'sales', 'support', 'executive', 'client'"
                    ],
                    "index_suggestions": [
                        "CREATE INDEX idx_users_email_domain ON gong_users (SPLIT_PART(email_address, '@', 2))",
                        "CREATE INDEX idx_users_type ON gong_users (user_type)",
                        "CREATE INDEX idx_users_payready ON gong_users (pay_ready_employee)"
                    ]
                },
                "gong_calls": {
                    "missing_columns": [
                        "apartment_relevance DECIMAL(3,2) - Apartment industry relevance score",
                        "business_value INTEGER - Estimated deal value",
                        "competitive_mentions TEXT[] - Array of competitor names mentioned",
                        "call_outcome VARCHAR(100) - 'qualified', 'demo_scheduled', 'proposal', 'closed_won', etc.",
                        "sophia_insights JSONB - AI-generated insights about the call"
                    ],
                    "enhancement_opportunities": [
                        "Add full-text search on call titles",
                        "Implement automatic apartment industry keyword detection",
                        "Create call outcome tracking and pipeline analysis"
                    ]
                }
            }
            
            return {
                "current_schema": schema_info,
                "improvement_suggestions": improvements,
                "priority_actions": [
                    "1. Add user_type classification to distinguish team vs clients",
                    "2. Implement Pay Ready email domain detection",
                    "3. Add apartment industry relevance scoring",
                    "4. Create separate views for team vs client analysis",
                    "5. Implement call outcome tracking for sales pipeline"
                ]
            }
            
        except Exception as e:
            logger.error(f"Error in get_schema_review: {str(e)}")
            return {"error": str(e)}

async def main():
    """Main function to analyze team vs client data and review schema"""
    
    analyzer = TeamClientAnalyzer()
    
    print("🔍 ANALYZING TEAM VS CLIENT DATA...")
    user_analysis = await analyzer.analyze_user_data()
    
    if "error" not in user_analysis:
        print(f"✅ User analysis complete!")
        print(f"📊 DOMAIN ANALYSIS:")
        
        for domain, data in user_analysis["domain_analysis"].items():
            print(f"   {domain}: {data['count']} users ({data['likely_type']})")
            if data['likely_type'] == 'pay_ready_team':
                print(f"      🏢 Potential Pay Ready team members:")
                for user in data['users'][:3]:
                    print(f"         - {user['name']} ({user['title']})")
        
        print(f"\n👥 TOP PARTICIPANTS BY CALL VOLUME:")
        for participant in user_analysis["participation_analysis"][:10]:
            print(f"   {participant['first_name']} {participant['last_name']}: {participant['total_calls']} calls")
            print(f"      Pay Ready calls: {participant['payready_calls']}, Apartment calls: {participant['apartment_calls']}")
    
    print("\n🏗️ REVIEWING DATABASE SCHEMA...")
    schema_review = await analyzer.get_schema_review()
    
    if "error" not in schema_review:
        print(f"✅ Schema review complete!")
        print(f"📋 CURRENT TABLES:")
        
        for table, info in schema_review["current_schema"].items():
            print(f"   {table}: {info['record_count']} records, {len(info['columns'])} columns")
        
        print(f"\n🎯 PRIORITY IMPROVEMENTS:")
        for action in schema_review["priority_actions"]:
            print(f"   {action}")
    
    # Save results (without sensitive data)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    results_file = f"team_client_analysis_{timestamp}.json"
    
    # Remove sensitive email addresses from results
    sanitized_results = {
        "timestamp": datetime.utcnow().isoformat(),
        "analysis_summary": {
            "total_users": user_analysis.get("total_users", 0),
            "domain_count": len(user_analysis.get("domain_analysis", {})),
            "recommendations": user_analysis.get("recommendations", {})
        },
        "schema_review": {
            "tables_analyzed": list(schema_review.get("current_schema", {}).keys()),
            "improvement_suggestions": schema_review.get("improvement_suggestions", {}),
            "priority_actions": schema_review.get("priority_actions", [])
        }
    }
    
    with open(results_file, 'w') as f:
        json.dump(sanitized_results, f, indent=2, default=str)
    
    print(f"\n💾 Sanitized results saved to: {results_file}")
    
    print(f"\n❓ CLARIFICATION QUESTIONS FOR USER:")
    print(f"1. What email domains do Pay Ready team members use? (@payready.com, @payready.ai, etc.)")
    print(f"2. Can you provide names of key Pay Ready team members to verify our classification?")
    print(f"3. Should we create separate tables for internal team vs external clients?")
    print(f"4. Do you want to track call outcomes and sales pipeline stages?")
    print(f"5. Should we implement automatic apartment industry client identification?")

if __name__ == "__main__":
    asyncio.run(main())

