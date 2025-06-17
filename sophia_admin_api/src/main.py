#!/usr/bin/env python3
"""
Sophia Admin API - Backend for Gong conversation intelligence
Provides REST API for searching and managing Gong conversation data
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import asyncpg
import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, origins="*")  # Allow all origins for development

# Database configuration
DATABASE_URL = "postgresql://postgres:password@localhost:5432/sophia_enhanced"

class SophiaDatabase:
    """Database connection and query manager"""
    
    def __init__(self):
        self.connection = None
    
    async def connect(self):
        """Connect to PostgreSQL database"""
        try:
            self.connection = await asyncpg.connect(DATABASE_URL)
            return True
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return False
    
    async def close(self):
        """Close database connection"""
        if self.connection:
            await self.connection.close()
    
    async def search_conversations(self, query: str = "", filters: Dict[str, Any] = None, 
                                 limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        """Search conversations with filters"""
        try:
            # Base query
            base_sql = """
            SELECT 
                c.call_id,
                c.title,
                c.started,
                c.duration_seconds,
                c.direction,
                c.apartment_relevance_score,
                c.business_impact_score,
                ci.ai_summary,
                ci.deal_health_score,
                ci.recommended_actions,
                aa.market_segment,
                ds.deal_progression_stage,
                ds.win_probability,
                comp.competitive_threat_level,
                array_agg(DISTINCT p.company_name) as companies,
                array_agg(DISTINCT p.name) as participants
            FROM gong_calls c
            LEFT JOIN sophia_conversation_intelligence ci ON c.call_id = ci.call_id
            LEFT JOIN sophia_apartment_analysis aa ON c.call_id = aa.call_id
            LEFT JOIN sophia_deal_signals ds ON c.call_id = ds.call_id
            LEFT JOIN sophia_competitive_intelligence comp ON c.call_id = comp.call_id
            LEFT JOIN gong_participants p ON c.call_id = p.call_id
            WHERE 1=1
            """
            
            params = []
            param_count = 0
            
            # Add search query filter
            if query:
                param_count += 1
                base_sql += f" AND (c.title ILIKE ${param_count} OR ci.ai_summary ILIKE ${param_count})"
                params.append(f"%{query}%")
            
            # Add filters
            if filters:
                if filters.get("date_from"):
                    param_count += 1
                    base_sql += f" AND c.started >= ${param_count}"
                    params.append(datetime.fromisoformat(filters["date_from"]))
                
                if filters.get("date_to"):
                    param_count += 1
                    base_sql += f" AND c.started <= ${param_count}"
                    params.append(datetime.fromisoformat(filters["date_to"]))
                
                if filters.get("min_relevance"):
                    param_count += 1
                    base_sql += f" AND c.apartment_relevance_score >= ${param_count}"
                    params.append(float(filters["min_relevance"]))
                
                if filters.get("deal_stage"):
                    param_count += 1
                    base_sql += f" AND ds.deal_progression_stage = ${param_count}"
                    params.append(filters["deal_stage"])
                
                if filters.get("company"):
                    param_count += 1
                    base_sql += f" AND EXISTS (SELECT 1 FROM gong_participants gp WHERE gp.call_id = c.call_id AND gp.company_name ILIKE ${param_count})"
                    params.append(f"%{filters['company']}%")
            
            # Group by and order
            base_sql += """
            GROUP BY c.call_id, c.title, c.started, c.duration_seconds, c.direction,
                     c.apartment_relevance_score, c.business_impact_score,
                     ci.ai_summary, ci.deal_health_score, ci.recommended_actions,
                     aa.market_segment, ds.deal_progression_stage, ds.win_probability,
                     comp.competitive_threat_level
            ORDER BY c.started DESC
            """
            
            # Add pagination
            param_count += 1
            base_sql += f" LIMIT ${param_count}"
            params.append(limit)
            
            param_count += 1
            base_sql += f" OFFSET ${param_count}"
            params.append(offset)
            
            # Execute query
            rows = await self.connection.fetch(base_sql, *params)
            
            # Get total count
            count_sql = """
            SELECT COUNT(DISTINCT c.call_id)
            FROM gong_calls c
            LEFT JOIN sophia_conversation_intelligence ci ON c.call_id = ci.call_id
            LEFT JOIN sophia_apartment_analysis aa ON c.call_id = aa.call_id
            LEFT JOIN sophia_deal_signals ds ON c.call_id = ds.call_id
            LEFT JOIN sophia_competitive_intelligence comp ON c.call_id = comp.call_id
            LEFT JOIN gong_participants p ON c.call_id = p.call_id
            WHERE 1=1
            """
            
            # Add same filters for count
            count_params = []
            count_param_count = 0
            
            if query:
                count_param_count += 1
                count_sql += f" AND (c.title ILIKE ${count_param_count} OR ci.ai_summary ILIKE ${count_param_count})"
                count_params.append(f"%{query}%")
            
            if filters:
                if filters.get("date_from"):
                    count_param_count += 1
                    count_sql += f" AND c.started >= ${count_param_count}"
                    count_params.append(datetime.fromisoformat(filters["date_from"]))
                
                if filters.get("date_to"):
                    count_param_count += 1
                    count_sql += f" AND c.started <= ${count_param_count}"
                    count_params.append(datetime.fromisoformat(filters["date_to"]))
                
                if filters.get("min_relevance"):
                    count_param_count += 1
                    count_sql += f" AND c.apartment_relevance_score >= ${count_param_count}"
                    count_params.append(float(filters["min_relevance"]))
                
                if filters.get("deal_stage"):
                    count_param_count += 1
                    count_sql += f" AND ds.deal_progression_stage = ${count_param_count}"
                    count_params.append(filters["deal_stage"])
                
                if filters.get("company"):
                    count_param_count += 1
                    count_sql += f" AND EXISTS (SELECT 1 FROM gong_participants gp WHERE gp.call_id = c.call_id AND gp.company_name ILIKE ${count_param_count})"
                    count_params.append(f"%{filters['company']}%")
            
            total_count = await self.connection.fetchval(count_sql, *count_params)
            
            # Format results
            conversations = []
            for row in rows:
                conversations.append({
                    "call_id": row["call_id"],
                    "title": row["title"],
                    "started": row["started"].isoformat() if row["started"] else None,
                    "duration_minutes": round(row["duration_seconds"] / 60) if row["duration_seconds"] else 0,
                    "direction": row["direction"],
                    "apartment_relevance_score": float(row["apartment_relevance_score"]) if row["apartment_relevance_score"] else 0,
                    "business_impact_score": float(row["business_impact_score"]) if row["business_impact_score"] else 0,
                    "ai_summary": row["ai_summary"],
                    "deal_health_score": float(row["deal_health_score"]) if row["deal_health_score"] else 0,
                    "recommended_actions": json.loads(row["recommended_actions"]) if row["recommended_actions"] else [],
                    "market_segment": row["market_segment"],
                    "deal_stage": row["deal_progression_stage"],
                    "win_probability": float(row["win_probability"]) if row["win_probability"] else 0,
                    "competitive_threat": row["competitive_threat_level"],
                    "companies": [c for c in row["companies"] if c] if row["companies"] else [],
                    "participants": [p for p in row["participants"] if p] if row["participants"] else []
                })
            
            return {
                "conversations": conversations,
                "total_count": total_count,
                "page_size": limit,
                "offset": offset,
                "has_more": (offset + limit) < total_count
            }
            
        except Exception as e:
            logger.error(f"Search conversations error: {e}")
            return {"error": str(e)}
    
    async def get_conversation_details(self, call_id: str) -> Dict[str, Any]:
        """Get detailed conversation information"""
        try:
            # Get call details
            call_sql = """
            SELECT c.*, ci.*, aa.*, ds.*, comp.*
            FROM gong_calls c
            LEFT JOIN sophia_conversation_intelligence ci ON c.call_id = ci.call_id
            LEFT JOIN sophia_apartment_analysis aa ON c.call_id = aa.call_id
            LEFT JOIN sophia_deal_signals ds ON c.call_id = ds.call_id
            LEFT JOIN sophia_competitive_intelligence comp ON c.call_id = comp.call_id
            WHERE c.call_id = $1
            """
            
            call_row = await self.connection.fetchrow(call_sql, call_id)
            if not call_row:
                return {"error": "Conversation not found"}
            
            # Get participants
            participants_sql = """
            SELECT participant_id, email_address, name, title, company_name,
                   participation_type, talk_time_percentage, is_customer, is_internal
            FROM gong_participants
            WHERE call_id = $1
            """
            
            participants_rows = await self.connection.fetch(participants_sql, call_id)
            
            # Format response
            conversation = {
                "call_id": call_row["call_id"],
                "title": call_row["title"],
                "url": call_row["url"],
                "started": call_row["started"].isoformat() if call_row["started"] else None,
                "duration_seconds": call_row["duration_seconds"],
                "direction": call_row["direction"],
                "system": call_row["system"],
                "apartment_relevance_score": float(call_row["apartment_relevance_score"]) if call_row["apartment_relevance_score"] else 0,
                "business_impact_score": float(call_row["business_impact_score"]) if call_row["business_impact_score"] else 0,
                "intelligence": {
                    "ai_summary": call_row["ai_summary"],
                    "confidence_level": float(call_row["confidence_level"]) if call_row["confidence_level"] else 0,
                    "key_insights": json.loads(call_row["key_insights"]) if call_row["key_insights"] else {},
                    "recommended_actions": json.loads(call_row["recommended_actions"]) if call_row["recommended_actions"] else [],
                    "deal_health_score": float(call_row["deal_health_score"]) if call_row["deal_health_score"] else 0
                },
                "apartment_analysis": {
                    "market_segment": call_row["market_segment"],
                    "apartment_terminology_count": call_row["apartment_terminology_count"],
                    "industry_relevance_factors": json.loads(call_row["industry_relevance_factors"]) if call_row["industry_relevance_factors"] else {}
                },
                "deal_signals": {
                    "positive_signals": json.loads(call_row["positive_signals"]) if call_row["positive_signals"] else [],
                    "negative_signals": json.loads(call_row["negative_signals"]) if call_row["negative_signals"] else [],
                    "deal_stage": call_row["deal_progression_stage"],
                    "win_probability": float(call_row["win_probability"]) if call_row["win_probability"] else 0
                },
                "competitive_intelligence": {
                    "competitors_mentioned": call_row["competitors_mentioned"] if call_row["competitors_mentioned"] else [],
                    "threat_level": call_row["competitive_threat_level"],
                    "win_probability_impact": float(call_row["win_probability_impact"]) if call_row["win_probability_impact"] else 0
                },
                "participants": [
                    {
                        "participant_id": p["participant_id"],
                        "email": p["email_address"],
                        "name": p["name"],
                        "title": p["title"],
                        "company": p["company_name"],
                        "participation_type": p["participation_type"],
                        "talk_time_percentage": float(p["talk_time_percentage"]) if p["talk_time_percentage"] else 0,
                        "is_customer": p["is_customer"],
                        "is_internal": p["is_internal"]
                    }
                    for p in participants_rows
                ]
            }
            
            return conversation
            
        except Exception as e:
            logger.error(f"Get conversation details error: {e}")
            return {"error": str(e)}
    
    async def get_dashboard_stats(self) -> Dict[str, Any]:
        """Get dashboard statistics"""
        try:
            stats = {}
            
            # Total counts
            stats["total_calls"] = await self.connection.fetchval("SELECT COUNT(*) FROM gong_calls")
            stats["total_emails"] = await self.connection.fetchval("SELECT COUNT(*) FROM gong_emails")
            stats["total_users"] = await self.connection.fetchval("SELECT COUNT(*) FROM gong_users")
            
            # Apartment relevance stats
            stats["high_relevance_calls"] = await self.connection.fetchval(
                "SELECT COUNT(*) FROM gong_calls WHERE apartment_relevance_score > 0.8"
            )
            
            stats["avg_apartment_relevance"] = await self.connection.fetchval(
                "SELECT AVG(apartment_relevance_score) FROM gong_calls WHERE apartment_relevance_score IS NOT NULL"
            )
            
            # Deal stage distribution
            deal_stages = await self.connection.fetch(
                "SELECT deal_progression_stage, COUNT(*) as count FROM sophia_deal_signals GROUP BY deal_progression_stage"
            )
            stats["deal_stages"] = {row["deal_progression_stage"]: row["count"] for row in deal_stages}
            
            # Recent activity (last 7 days)
            week_ago = datetime.utcnow() - timedelta(days=7)
            stats["recent_calls"] = await self.connection.fetchval(
                "SELECT COUNT(*) FROM gong_calls WHERE started > $1", week_ago
            )
            
            # Top companies
            top_companies = await self.connection.fetch("""
                SELECT company_name, COUNT(*) as call_count
                FROM gong_participants 
                WHERE company_name IS NOT NULL AND company_name != 'Pay Ready'
                GROUP BY company_name 
                ORDER BY call_count DESC 
                LIMIT 10
            """)
            stats["top_companies"] = [
                {"company": row["company_name"], "calls": row["call_count"]}
                for row in top_companies
            ]
            
            return stats
            
        except Exception as e:
            logger.error(f"Get dashboard stats error: {e}")
            return {"error": str(e)}

# Global database instance
db = SophiaDatabase()

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "timestamp": datetime.utcnow().isoformat()})

@app.route('/api/conversations/search', methods=['GET'])
def search_conversations():
    """Search conversations endpoint"""
    try:
        # Get query parameters
        query = request.args.get('q', '')
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        
        # Get filters
        filters = {}
        if request.args.get('date_from'):
            filters['date_from'] = request.args.get('date_from')
        if request.args.get('date_to'):
            filters['date_to'] = request.args.get('date_to')
        if request.args.get('min_relevance'):
            filters['min_relevance'] = request.args.get('min_relevance')
        if request.args.get('deal_stage'):
            filters['deal_stage'] = request.args.get('deal_stage')
        if request.args.get('company'):
            filters['company'] = request.args.get('company')
        
        # Execute search
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def run_search():
            await db.connect()
            result = await db.search_conversations(query, filters, limit, offset)
            await db.close()
            return result
        
        result = loop.run_until_complete(run_search())
        loop.close()
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Search endpoint error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/conversations/<call_id>', methods=['GET'])
def get_conversation(call_id):
    """Get conversation details endpoint"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def run_get():
            await db.connect()
            result = await db.get_conversation_details(call_id)
            await db.close()
            return result
        
        result = loop.run_until_complete(run_get())
        loop.close()
        
        if "error" in result:
            return jsonify(result), 404
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Get conversation endpoint error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/dashboard/stats', methods=['GET'])
def get_dashboard_stats():
    """Get dashboard statistics endpoint"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def run_stats():
            await db.connect()
            result = await db.get_dashboard_stats()
            await db.close()
            return result
        
        result = loop.run_until_complete(run_stats())
        loop.close()
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Dashboard stats endpoint error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/emails/upload', methods=['POST'])
def upload_email():
    """Upload email manually endpoint"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Validate required fields
        required_fields = ['from_email', 'to_emails', 'subject_line', 'email_body']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        # TODO: Implement email upload logic
        # For now, return success
        return jsonify({
            "success": True,
            "message": "Email uploaded successfully",
            "email_id": "mock_email_id"
        })
        
    except Exception as e:
        logger.error(f"Email upload endpoint error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

