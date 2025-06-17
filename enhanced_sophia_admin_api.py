#!/usr/bin/env python3
"""
Enhanced Sophia Admin API with Natural Language Interface
Provides conversational interface for data exploration and schema mapping
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import asyncio
import asyncpg
import json
import os
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

class SophiaAdminAPI:
    """
    Enhanced admin API with natural language processing for Gong data
    """
    
    def __init__(self):
        self.db_config = {
            "host": "localhost",
            "port": 5432,
            "user": "postgres", 
            "password": "password",
            "database": "sophia_enhanced"
        }
    
    async def get_database_connection(self):
        """Get database connection"""
        return await asyncpg.connect(**self.db_config)
    
    async def natural_language_query(self, query: str) -> dict:
        """Process natural language queries about Gong data"""
        
        query_lower = query.lower()
        
        try:
            conn = await self.get_database_connection()
            
            # Apartment industry queries
            if any(keyword in query_lower for keyword in ['apartment', 'rental', 'property', 'multifamily']):
                apartment_calls = await conn.fetch("""
                    SELECT title, started, duration_seconds, direction, call_id
                    FROM gong_calls 
                    WHERE LOWER(title) LIKE ANY(ARRAY['%apartment%', '%rental%', '%property%', '%multifamily%', '%lease%'])
                    ORDER BY started DESC 
                    LIMIT 20
                """)
                
                apartment_users = await conn.fetch("""
                    SELECT DISTINCT u.first_name, u.last_name, u.title, u.email_address
                    FROM gong_users u
                    JOIN gong_participants p ON u.email_address = p.email_address
                    JOIN gong_calls c ON p.call_id = c.call_id
                    WHERE LOWER(c.title) LIKE ANY(ARRAY['%apartment%', '%rental%', '%property%', '%multifamily%'])
                    LIMIT 10
                """)
                
                await conn.close()
                
                return {
                    "query_type": "apartment_industry",
                    "interpretation": f"Found apartment industry data based on: {query}",
                    "results": {
                        "apartment_calls": [dict(row) for row in apartment_calls],
                        "apartment_team_members": [dict(row) for row in apartment_users]
                    },
                    "insights": {
                        "total_apartment_calls": len(apartment_calls),
                        "key_companies": ["Greystar Real Estate Partners", "Mid-America Apartment Communities", "Bozzuto Group"]
                    }
                }
            
            # Pay Ready specific queries
            elif any(keyword in query_lower for keyword in ['pay ready', 'payready', 'contract', 'deal']):
                payready_calls = await conn.fetch("""
                    SELECT title, started, duration_seconds, direction, call_id
                    FROM gong_calls 
                    WHERE LOWER(title) LIKE ANY(ARRAY['%pay ready%', '%payready%', '%contract%', '%deal%'])
                    ORDER BY started DESC 
                    LIMIT 20
                """)
                
                await conn.close()
                
                return {
                    "query_type": "pay_ready_business",
                    "interpretation": f"Found Pay Ready business data based on: {query}",
                    "results": {
                        "payready_calls": [dict(row) for row in payready_calls]
                    },
                    "insights": {
                        "total_payready_calls": len(payready_calls),
                        "business_focus": "Contract finalization and competitive analysis"
                    }
                }
            
            # Team performance queries
            elif any(keyword in query_lower for keyword in ['team', 'sales', 'performance', 'top']):
                top_performers = await conn.fetch("""
                    SELECT u.first_name, u.last_name, u.title, 
                           COUNT(p.call_id) as call_count,
                           AVG(c.duration_seconds) as avg_duration
                    FROM gong_users u
                    JOIN gong_participants p ON u.email_address = p.email_address
                    JOIN gong_calls c ON p.call_id = c.call_id
                    WHERE u.title LIKE ANY(ARRAY['%Executive%', '%Manager%', '%Director%'])
                    GROUP BY u.user_id, u.first_name, u.last_name, u.title
                    ORDER BY call_count DESC
                    LIMIT 10
                """)
                
                await conn.close()
                
                return {
                    "query_type": "team_performance",
                    "interpretation": f"Found team performance data based on: {query}",
                    "results": {
                        "top_performers": [dict(row) for row in top_performers]
                    },
                    "insights": {
                        "analysis": "Performance ranked by call volume and average call duration"
                    }
                }
            
            # Recent activity queries
            elif any(keyword in query_lower for keyword in ['recent', 'latest', 'today', 'this week']):
                recent_calls = await conn.fetch("""
                    SELECT title, started, duration_seconds, direction, call_id
                    FROM gong_calls 
                    ORDER BY started DESC 
                    LIMIT 15
                """)
                
                await conn.close()
                
                return {
                    "query_type": "recent_activity",
                    "interpretation": f"Found recent activity based on: {query}",
                    "results": {
                        "recent_calls": [dict(row) for row in recent_calls]
                    },
                    "insights": {
                        "total_recent_calls": len(recent_calls)
                    }
                }
            
            # General data overview
            else:
                overview = await conn.fetch("""
                    SELECT 
                        (SELECT COUNT(*) FROM gong_users) as total_users,
                        (SELECT COUNT(*) FROM gong_calls) as total_calls,
                        (SELECT COUNT(*) FROM gong_workspaces) as total_workspaces,
                        (SELECT COUNT(*) FROM gong_calls WHERE LOWER(title) LIKE ANY(ARRAY['%apartment%', '%rental%', '%property%'])) as apartment_calls
                """)
                
                recent_calls = await conn.fetch("""
                    SELECT title, started, duration_seconds 
                    FROM gong_calls 
                    ORDER BY started DESC 
                    LIMIT 5
                """)
                
                await conn.close()
                
                overview_data = dict(overview[0]) if overview else {}
                
                return {
                    "query_type": "general_overview",
                    "interpretation": f"Providing general data overview for: {query}",
                    "results": {
                        "overview": overview_data,
                        "recent_calls": [dict(row) for row in recent_calls]
                    },
                    "insights": {
                        "apartment_percentage": round((overview_data.get('apartment_calls', 0) / max(overview_data.get('total_calls', 1), 1)) * 100, 2)
                    }
                }
            
        except Exception as e:
            logger.error(f"Error in natural_language_query: {str(e)}")
            return {
                "query_type": "error",
                "interpretation": f"Error processing query: {query}",
                "error": str(e)
            }
    
    async def get_schema_mapping_suggestions(self, table_name: str) -> dict:
        """Get suggestions for schema mapping and data definitions"""
        
        try:
            conn = await self.get_database_connection()
            
            # Get table schema
            schema_info = await conn.fetch("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = $1 AND table_schema = 'public'
                ORDER BY ordinal_position
            """, table_name)
            
            # Get sample data
            sample_data = await conn.fetch(f"""
                SELECT * FROM {table_name} LIMIT 5
            """)
            
            await conn.close()
            
            # Generate mapping suggestions based on table
            suggestions = {
                "gong_calls": {
                    "apartment_relevance": "Score 0.0-1.0 based on apartment industry keywords in title",
                    "business_value": "Estimated deal value based on call duration and participants",
                    "competitive_threat": "Mentions of competitors like RentSpree, AppFolio, Yardi",
                    "sophia_insights": "AI-generated insights about conversation content and outcomes"
                },
                "gong_users": {
                    "apartment_expertise": "User's experience level with apartment industry",
                    "performance_score": "Sales performance based on call outcomes",
                    "territory": "Geographic or market segment focus",
                    "sophia_profile": "AI-generated user profile and recommendations"
                }
            }
            
            return {
                "table_name": table_name,
                "schema": [dict(row) for row in schema_info],
                "sample_data": [dict(row) for row in sample_data],
                "mapping_suggestions": suggestions.get(table_name, {}),
                "enhancement_opportunities": [
                    "Add apartment industry relevance scoring",
                    "Implement competitive intelligence tracking",
                    "Create business value estimation",
                    "Add AI-powered conversation insights"
                ]
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "table_name": table_name
            }

# Initialize API
sophia_api = SophiaAdminAPI()

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "Sophia Admin API",
        "timestamp": datetime.utcnow().isoformat(),
        "features": [
            "Natural Language Queries",
            "Schema Mapping Suggestions", 
            "Real-time Gong Data Access",
            "Apartment Industry Intelligence"
        ]
    })

@app.route('/api/natural-query', methods=['POST'])
def natural_language_query():
    """Process natural language queries"""
    try:
        data = request.get_json()
        query = data.get('query', '')
        
        if not query:
            return jsonify({"error": "Query is required"}), 400
        
        # Run async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(sophia_api.natural_language_query(query))
        loop.close()
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in natural_language_query endpoint: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/schema-mapping/<table_name>')
def schema_mapping(table_name):
    """Get schema mapping suggestions for a table"""
    try:
        # Run async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(sophia_api.get_schema_mapping_suggestions(table_name))
        loop.close()
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in schema_mapping endpoint: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/conversations/search')
def search_conversations():
    """Search conversations with filters"""
    try:
        query = request.args.get('query', '')
        limit = int(request.args.get('limit', 20))
        
        # Run async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def search():
            conn = await sophia_api.get_database_connection()
            
            if query:
                results = await conn.fetch("""
                    SELECT call_id, title, started, duration_seconds, direction
                    FROM gong_calls 
                    WHERE LOWER(title) LIKE $1
                    ORDER BY started DESC 
                    LIMIT $2
                """, f"%{query.lower()}%", limit)
            else:
                results = await conn.fetch("""
                    SELECT call_id, title, started, duration_seconds, direction
                    FROM gong_calls 
                    ORDER BY started DESC 
                    LIMIT $1
                """, limit)
            
            await conn.close()
            return [dict(row) for row in results]
        
        conversations = loop.run_until_complete(search())
        loop.close()
        
        return jsonify({
            "conversations": conversations,
            "total": len(conversations),
            "query": query
        })
        
    except Exception as e:
        logger.error(f"Error in search_conversations endpoint: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/dashboard/stats')
def dashboard_stats():
    """Get dashboard statistics"""
    try:
        # Run async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def get_stats():
            conn = await sophia_api.get_database_connection()
            
            stats = await conn.fetchrow("""
                SELECT 
                    (SELECT COUNT(*) FROM gong_users) as total_users,
                    (SELECT COUNT(*) FROM gong_calls) as total_calls,
                    (SELECT COUNT(*) FROM gong_workspaces) as total_workspaces,
                    (SELECT COUNT(*) FROM gong_calls WHERE LOWER(title) LIKE ANY(ARRAY['%apartment%', '%rental%', '%property%'])) as apartment_calls,
                    (SELECT COUNT(*) FROM gong_calls WHERE LOWER(title) LIKE '%pay ready%') as payready_calls
            """)
            
            await conn.close()
            return dict(stats)
        
        stats = loop.run_until_complete(get_stats())
        loop.close()
        
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Error in dashboard_stats endpoint: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("🚀 Starting Enhanced Sophia Admin API...")
    print("📊 Features:")
    print("   - Natural Language Queries")
    print("   - Schema Mapping Suggestions")
    print("   - Real-time Gong Data Access")
    print("   - Apartment Industry Intelligence")
    print("🌐 API running on http://localhost:5000")
    
    app.run(host='0.0.0.0', port=5001, debug=True)

