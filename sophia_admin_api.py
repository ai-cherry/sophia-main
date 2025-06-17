#!/usr/bin/env python3
"""
Sophia Admin API - Backend for Gong conversation intelligence
Provides REST API for searching and managing Gong conversation data
"""

from flask import Flask, request, jsonify, redirect
from flask_cors import CORS
import asyncpg
import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import os

# Attempt to import GongOAuthHandler
try:
    from gong_oauth_application import GongOAuthHandler
except ImportError:
    GongOAuthHandler = None
    logger.warning("gong_oauth_application.py not found or GongOAuthHandler could not be imported. OAuth endpoints will not function.")


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

            # Placeholder for Apartment Industry Specific Insights
            stats["apartment_insights"] = {
                "avg_lease_conversion_rate_discussed": 0.35, # Example: 35%
                "common_amenities_mentioned": ["pool", "gym", "pet-friendly", "in-unit laundry"],
                "peak_leasing_season_activity": "High (based on call volume in Spring/Summer)",
                "competitor_sentiment_score": -0.2, # Example: Slightly negative towards competitors
                "pay_ready_feature_requests": ["automated payment reminders", "integration with Yardi"]
            }
            
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

# Placeholder for schema configuration data
current_schema_config = {
    "version": "1.0",
    "last_updated": datetime.utcnow().isoformat(),
    "mappings": [
        {"gong_field": "call.title", "sophia_field": "conversations.title", "type": "string", "transformation": "direct"},
        {"gong_field": "call.duration", "sophia_field": "conversations.duration_minutes", "type": "integer", "transformation": "seconds_to_minutes"},
    ],
    "definitions": {
        "apartment_relevance_score": "Calculated based on keywords in title and participant company.",
        "deal_stage_rule": "Derived from call title keywords like 'demo', 'proposal', 'closing'."
    }
}

@app.route('/api/schema/config', methods=['GET'])
def get_schema_config():
    """Get current schema mapping and data definitions"""
    try:
        # In a real implementation, this would fetch from a database or config file
        return jsonify({
            "success": True,
            "config": current_schema_config
        })
    except Exception as e:
        logger.error(f"Get schema config error: {e}")
        return jsonify({"error": str(e), "success": False}), 500

@app.route('/api/schema/config', methods=['POST'])
def update_schema_config():
    """Update schema mapping and data definitions"""
    global current_schema_config
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided", "success": False}), 400
        
        # Basic validation (in real app, much more thorough)
        if "mappings" not in data or "definitions" not in data:
            return jsonify({"error": "Missing 'mappings' or 'definitions' in request", "success": False}), 400

        # Update the placeholder config
        current_schema_config["mappings"] = data["mappings"]
        current_schema_config["definitions"] = data["definitions"]
        current_schema_config["last_updated"] = datetime.utcnow().isoformat()
        current_schema_config["version"] = str(float(current_schema_config.get("version", "1.0")) + 0.1) # Simple version increment

        # In a real implementation, this would save to a database or config file
        # and potentially trigger schema migration or validation logic.
        
        logger.info(f"Schema config updated: {current_schema_config}")
        return jsonify({
            "success": True, 
            "message": "Schema configuration updated successfully.",
            "updated_config": current_schema_config
        })
        
    except Exception as e:
        logger.error(f"Update schema config error: {e}")
        return jsonify({"error": str(e), "success": False}), 500

@app.route('/api/schema/nl_process', methods=['POST'])
def process_natural_language_schema_query():
    """Process a natural language query for schema definition"""
    try:
        data = request.get_json()
        if not data or "query" not in data:
            return jsonify({"error": "No query provided", "success": False}), 400
        
        nl_query = data["query"]
        
        # Placeholder NLP processing logic
        # In a real app, this would involve a more sophisticated NLP model/service
        interpretation = {
            "original_query": nl_query,
            "intent": "unknown",
            "entities": [],
            "parsed_action": None,
            "confidence": 0.0
        }
        
        if "map gong call titles to apartment relevance scores" in nl_query.lower():
            interpretation["intent"] = "define_mapping_rule"
            interpretation["entities"] = [
                {"type": "source_field", "value": "Gong call titles"},
                {"type": "target_field", "value": "apartment relevance scores"}
            ]
            interpretation["parsed_action"] = {
                "action_type": "CREATE_MAPPING",
                "source": "gong.call.title",
                "target": "sophia.apartment_relevance_score",
                "transformation_hint": "keyword_based_scoring"
            }
            interpretation["confidence"] = 0.85
        elif "create alerts for competitor mentions" in nl_query.lower():
            interpretation["intent"] = "define_alert_rule"
            interpretation["entities"] = [{"type": "condition", "value": "competitor mentions"}]
            interpretation["parsed_action"] = {
                "action_type": "CREATE_ALERT",
                "trigger": "competitor_mention_in_call",
                "notification_channel": "slack" # Default or configurable
            }
            interpretation["confidence"] = 0.90
        else:
            interpretation["parsed_action"] = {"error": "Could not understand the query."}
            interpretation["confidence"] = 0.30
            
        logger.info(f"NL Query: '{nl_query}', Interpretation: {interpretation}")
        return jsonify({"success": True, "interpretation": interpretation})
        
    except Exception as e:
        logger.error(f"NL process error: {e}")
        return jsonify({"error": str(e), "success": False}), 500

# OAuth Routes
if GongOAuthHandler:
    gong_oauth_handler = GongOAuthHandler()

    @app.route('/api/auth/gong/login', methods=['GET'])
    def gong_oauth_login():
        """
        Redirects the user to Gong's OAuth authorization page.
        """
        if not gong_oauth_handler.client_id or not gong_oauth_handler.redirect_uri:
            return jsonify({"error": "Gong OAuth is not configured properly on the server.", "success": False}), 500
        
        # Generate a state parameter for CSRF protection (optional but recommended)
        # For simplicity, a fixed state or no state is used here. In production, generate and validate a unique state.
        state = "csrf_token_placeholder" # Replace with actual CSRF token logic
        authorization_url = gong_oauth_handler.get_authorization_url(state=state)
        
        if authorization_url == "/error_oauth_misconfigured":
             return jsonify({"error": "Gong OAuth is not configured properly on the server (URL generation failed).", "success": False}), 500
        
        # Store state in session if using it for validation: session['oauth_state'] = state
        return redirect(authorization_url)

    @app.route('/api/auth/gong/callback', methods=['GET'])
    def gong_oauth_callback():
        """
        Handles the callback from Gong after user authorization.
        Exchanges the authorization code for tokens.
        """
        error = request.args.get('error')
        if error:
            error_description = request.args.get('error_description', 'No description provided.')
            logger.error(f"Gong OAuth error: {error} - {error_description}")
            return jsonify({"error": f"Gong OAuth failed: {error}", "description": error_description, "success": False}), 400

        authorization_code = request.args.get('code')
        returned_state = request.args.get('state')

        # Validate state parameter for CSRF protection (if used)
        # expected_state = session.pop('oauth_state', None)
        # if not returned_state or returned_state != expected_state:
        #     logger.error("OAuth state mismatch. Possible CSRF attack.")
        #     return jsonify({"error": "Invalid OAuth state.", "success": False}), 400
            
        if not authorization_code:
            logger.error("No authorization code received from Gong.")
            return jsonify({"error": "Authorization code missing in callback.", "success": False}), 400

        tokens = gong_oauth_handler.exchange_code_for_tokens(authorization_code)

        if "error" in tokens:
            logger.error(f"Failed to exchange Gong auth code for tokens: {tokens.get('details', tokens['error'])}")
            return jsonify({"error": "Failed to obtain Gong tokens.", "details": tokens.get('details'), "success": False}), 500
        
        # At this point, tokens are successfully retrieved.
        # Securely store them (e.g., associated with the logged-in user or tenant).
        # For this placeholder, we'll just log and return them.
        # A real app would likely redirect the user to a success page or their dashboard.
        gong_oauth_handler.store_tokens(
            access_token=tokens.get("access_token"),
            refresh_token=tokens.get("refresh_token"),
            expires_in=tokens.get("expires_in", 3600), # Default to 1 hour if not provided
            # user_id=current_user.id # Example: associate with a logged-in user
        )
        
        logger.info(f"Gong OAuth successful. Tokens obtained (details omitted for security).")
        # In a real app, you might redirect to a frontend page:
        # return redirect(url_for('frontend_success_page', status='gong_auth_success'))
        return jsonify({
            "success": True,
            "message": "Gong OAuth successful. Tokens obtained and stored (placeholder).",
            "access_token_type": tokens.get("token_type"),
            "access_token_expires_in": tokens.get("expires_in"),
            # Do NOT return access_token or refresh_token directly to the client here for security reasons
            # unless it's a specific flow that requires it (e.g. SPA immediately using it).
            # Typically, the server stores them and uses them for API calls on behalf of the user.
        })
else:
    logger.warning("GongOAuthHandler not available. Gong OAuth endpoints are disabled.")


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
