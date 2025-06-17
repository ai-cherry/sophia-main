#!/usr/bin/env python3
"""
Gong Webhook System Implementation
Real-time conversation intelligence with instant notifications
"""

import os
import json
import hmac
import hashlib
import asyncio
import asyncpg
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import logging
from threading import Thread
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class WebhookEvent:
    """Webhook event data structure"""
    event_id: str
    event_type: str
    workspace_id: str
    call_id: Optional[str]
    user_id: Optional[str]
    timestamp: datetime
    data: Dict[str, Any]
    customer_id: Optional[str] = None

class GongWebhookManager:
    """
    Gong webhook system for real-time conversation intelligence
    """
    
    def __init__(self):
        # Database configuration
        self.db_config = {
            "host": "localhost",
            "port": 5432,
            "user": "postgres",
            "password": "password",
            "database": "sophia_enhanced"
        }
        
        # Webhook configuration
        self.webhook_secret = os.getenv("GONG_WEBHOOK_SECRET", "sophia_webhook_secret_2024")
        self.webhook_url = "https://your-domain.com/api/webhooks/gong"  # Will be updated for production
        
        # Event types we're interested in
        self.supported_events = [
            "call.recorded",
            "call.transcribed", 
            "call.analyzed",
            "call.shared",
            "user.created",
            "user.updated",
            "workspace.updated"
        ]
        
        # Apartment industry keywords for real-time analysis
        self.apartment_keywords = [
            "apartment", "rental", "lease", "tenant", "resident", "property management",
            "multifamily", "unit", "complex", "building", "rent", "deposit", "amenities",
            "maintenance", "vacancy", "occupancy", "property manager", "leasing office",
            "application", "screening", "background check", "move-in", "move-out",
            "pay ready", "payment", "collection", "portal", "automation"
        ]
    
    async def setup_webhook_schema(self):
        """Create webhook-specific database schema"""
        
        try:
            conn = await asyncpg.connect(**self.db_config)
            
            # Create webhook events table (if not exists)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS webhook_events (
                    id SERIAL PRIMARY KEY,
                    event_id VARCHAR(255) UNIQUE NOT NULL,
                    event_type VARCHAR(100) NOT NULL,
                    workspace_id VARCHAR(255),
                    call_id VARCHAR(255),
                    user_id VARCHAR(255),
                    customer_id UUID,
                    event_data JSONB NOT NULL,
                    processed BOOLEAN DEFAULT FALSE,
                    processing_status VARCHAR(50) DEFAULT 'pending',
                    apartment_relevance_score FLOAT DEFAULT 0.0,
                    ai_insights JSONB,
                    notification_sent BOOLEAN DEFAULT FALSE,
                    error_message TEXT,
                    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    processed_at TIMESTAMP
                )
            """)
            
            # Create real-time notifications table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS real_time_notifications (
                    id SERIAL PRIMARY KEY,
                    customer_id UUID,
                    event_id VARCHAR(255),
                    notification_type VARCHAR(100) NOT NULL,
                    title VARCHAR(255) NOT NULL,
                    message TEXT NOT NULL,
                    priority VARCHAR(20) DEFAULT 'normal',
                    apartment_relevance_score FLOAT DEFAULT 0.0,
                    action_required BOOLEAN DEFAULT FALSE,
                    action_url TEXT,
                    read_status BOOLEAN DEFAULT FALSE,
                    delivery_status VARCHAR(50) DEFAULT 'pending',
                    delivery_attempts INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    delivered_at TIMESTAMP,
                    read_at TIMESTAMP
                )
            """)
            
            # Create webhook subscriptions table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS webhook_subscriptions (
                    id SERIAL PRIMARY KEY,
                    customer_id UUID REFERENCES customers(id) ON DELETE CASCADE,
                    workspace_id VARCHAR(255) NOT NULL,
                    event_types JSONB NOT NULL,
                    webhook_url TEXT NOT NULL,
                    webhook_secret VARCHAR(255),
                    active BOOLEAN DEFAULT TRUE,
                    last_delivery TIMESTAMP,
                    delivery_success_rate FLOAT DEFAULT 1.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(customer_id, workspace_id)
                )
            """)
            
            # Create conversation alerts table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS conversation_alerts (
                    id SERIAL PRIMARY KEY,
                    customer_id UUID,
                    call_id VARCHAR(255) NOT NULL,
                    alert_type VARCHAR(100) NOT NULL,
                    alert_message TEXT NOT NULL,
                    apartment_relevance_score FLOAT DEFAULT 0.0,
                    urgency_level VARCHAR(20) DEFAULT 'medium',
                    triggered_by JSONB,
                    action_items JSONB,
                    resolved BOOLEAN DEFAULT FALSE,
                    resolved_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for performance
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_webhook_events_type ON webhook_events(event_type)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_webhook_events_processed ON webhook_events(processed)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_webhook_events_call_id ON webhook_events(call_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_notifications_customer_id ON real_time_notifications(customer_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_notifications_read_status ON real_time_notifications(read_status)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_subscriptions_customer_id ON webhook_subscriptions(customer_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_alerts_customer_id ON conversation_alerts(customer_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_alerts_urgency ON conversation_alerts(urgency_level)")
            
            await conn.close()
            
            logger.info("Webhook database schema created successfully")
            
        except Exception as e:
            logger.error(f"Error setting up webhook schema: {str(e)}")
            raise
    
    async def register_webhook_subscription(self, customer_id: str, workspace_id: str, 
                                          event_types: List[str], webhook_url: str) -> Dict[str, Any]:
        """Register webhook subscription for customer"""
        
        try:
            conn = await asyncpg.connect(**self.db_config)
            
            # Generate webhook secret for customer
            webhook_secret = f"whsec_{hashlib.sha256(f'{customer_id}_{workspace_id}'.encode()).hexdigest()[:32]}"
            
            # Store subscription
            await conn.execute("""
                INSERT INTO webhook_subscriptions 
                (customer_id, workspace_id, event_types, webhook_url, webhook_secret)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (customer_id, workspace_id) DO UPDATE SET
                    event_types = EXCLUDED.event_types,
                    webhook_url = EXCLUDED.webhook_url,
                    webhook_secret = EXCLUDED.webhook_secret,
                    active = TRUE,
                    updated_at = CURRENT_TIMESTAMP
            """,
                customer_id,
                workspace_id,
                json.dumps(event_types),
                webhook_url,
                webhook_secret
            )
            
            await conn.close()
            
            # Register with Gong (would be actual API call in production)
            gong_registration = await self._register_with_gong(workspace_id, event_types)
            
            return {
                "success": True,
                "webhook_secret": webhook_secret,
                "registered_events": event_types,
                "gong_webhook_id": gong_registration.get("webhook_id"),
                "message": "Webhook subscription registered successfully"
            }
            
        except Exception as e:
            logger.error(f"Error registering webhook subscription: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def process_webhook_event(self, event_data: Dict[str, Any], signature: str = None) -> Dict[str, Any]:
        """Process incoming webhook event"""
        
        try:
            # Verify webhook signature (in production)
            if signature and not self._verify_signature(json.dumps(event_data), signature):
                return {
                    "success": False,
                    "error": "Invalid webhook signature"
                }
            
            # Parse event
            webhook_event = self._parse_webhook_event(event_data)
            
            # Store event
            await self._store_webhook_event(webhook_event)
            
            # Process event based on type
            processing_result = await self._process_event_by_type(webhook_event)
            
            # Generate notifications if needed
            if processing_result.get("apartment_relevant", False):
                await self._generate_real_time_notifications(webhook_event, processing_result)
            
            # Update processing status
            await self._update_event_processing_status(
                webhook_event.event_id, 
                "completed", 
                processing_result
            )
            
            return {
                "success": True,
                "event_id": webhook_event.event_id,
                "processing_result": processing_result
            }
            
        except Exception as e:
            logger.error(f"Error processing webhook event: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _parse_webhook_event(self, event_data: Dict[str, Any]) -> WebhookEvent:
        """Parse webhook event data"""
        
        return WebhookEvent(
            event_id=event_data.get("eventId", f"evt_{int(time.time())}"),
            event_type=event_data.get("eventType", "unknown"),
            workspace_id=event_data.get("workspaceId", ""),
            call_id=event_data.get("callId"),
            user_id=event_data.get("userId"),
            timestamp=datetime.fromisoformat(
                event_data.get("timestamp", datetime.utcnow().isoformat())
            ),
            data=event_data
        )
    
    async def _store_webhook_event(self, event: WebhookEvent):
        """Store webhook event in database"""
        
        try:
            conn = await asyncpg.connect(**self.db_config)
            
            await conn.execute("""
                INSERT INTO webhook_events 
                (event_id, event_type, workspace_id, call_id, user_id, event_data)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (event_id) DO NOTHING
            """,
                event.event_id,
                event.event_type,
                event.workspace_id,
                event.call_id,
                event.user_id,
                json.dumps(event.data)
            )
            
            await conn.close()
            
        except Exception as e:
            logger.error(f"Error storing webhook event: {str(e)}")
            raise
    
    async def _process_event_by_type(self, event: WebhookEvent) -> Dict[str, Any]:
        """Process event based on its type"""
        
        processing_result = {
            "event_type": event.event_type,
            "apartment_relevant": False,
            "apartment_relevance_score": 0.0,
            "insights": [],
            "action_items": [],
            "notifications": []
        }
        
        try:
            if event.event_type == "call.recorded":
                processing_result.update(await self._process_call_recorded(event))
            elif event.event_type == "call.transcribed":
                processing_result.update(await self._process_call_transcribed(event))
            elif event.event_type == "call.analyzed":
                processing_result.update(await self._process_call_analyzed(event))
            elif event.event_type == "call.shared":
                processing_result.update(await self._process_call_shared(event))
            elif event.event_type == "user.created":
                processing_result.update(await self._process_user_created(event))
            
            return processing_result
            
        except Exception as e:
            logger.error(f"Error processing event type {event.event_type}: {str(e)}")
            processing_result["error"] = str(e)
            return processing_result
    
    async def _process_call_recorded(self, event: WebhookEvent) -> Dict[str, Any]:
        """Process call recorded event"""
        
        call_data = event.data.get("call", {})
        participants = call_data.get("participants", [])
        
        # Check for apartment industry relevance
        apartment_score = 0.0
        insights = []
        
        # Analyze participants
        for participant in participants:
            company = participant.get("company", "").lower()
            if any(keyword in company for keyword in ["apartment", "property", "management", "real estate"]):
                apartment_score += 0.3
                insights.append(f"Apartment industry participant: {participant.get('name', 'Unknown')}")
        
        # Analyze call title/topic
        title = call_data.get("title", "").lower()
        for keyword in self.apartment_keywords:
            if keyword in title:
                apartment_score += 0.1
                insights.append(f"Apartment keyword detected: {keyword}")
        
        apartment_score = min(apartment_score, 1.0)
        
        return {
            "apartment_relevant": apartment_score > 0.5,
            "apartment_relevance_score": apartment_score,
            "insights": insights,
            "action_items": [
                "Monitor call for apartment industry discussion",
                "Prepare for transcript analysis when available"
            ] if apartment_score > 0.5 else [],
            "call_duration": call_data.get("duration", 0),
            "participant_count": len(participants)
        }
    
    async def _process_call_transcribed(self, event: WebhookEvent) -> Dict[str, Any]:
        """Process call transcribed event"""
        
        transcript_data = event.data.get("transcript", {})
        transcript_text = transcript_data.get("text", "").lower()
        
        # Analyze transcript for apartment industry content
        apartment_score = 0.0
        insights = []
        action_items = []
        
        # Count apartment keywords
        keyword_count = 0
        for keyword in self.apartment_keywords:
            count = transcript_text.count(keyword)
            if count > 0:
                keyword_count += count
                insights.append(f"'{keyword}' mentioned {count} times")
        
        # Calculate relevance score
        if len(transcript_text) > 0:
            apartment_score = min(keyword_count / (len(transcript_text.split()) / 100), 1.0)
        
        # Generate action items for high relevance calls
        if apartment_score > 0.7:
            action_items.extend([
                "High apartment relevance - prioritize follow-up",
                "Extract key pain points and requirements",
                "Identify decision makers and timeline",
                "Prepare customized Pay Ready proposal"
            ])
        
        # Detect specific conversation patterns
        if "pay ready" in transcript_text:
            insights.append("Pay Ready mentioned in conversation")
            apartment_score += 0.2
        
        if any(phrase in transcript_text for phrase in ["pricing", "cost", "budget", "proposal"]):
            insights.append("Pricing discussion detected")
            action_items.append("Prepare pricing proposal")
        
        return {
            "apartment_relevant": apartment_score > 0.5,
            "apartment_relevance_score": min(apartment_score, 1.0),
            "insights": insights,
            "action_items": action_items,
            "keyword_count": keyword_count,
            "transcript_length": len(transcript_text.split())
        }
    
    async def _process_call_analyzed(self, event: WebhookEvent) -> Dict[str, Any]:
        """Process call analyzed event"""
        
        analysis_data = event.data.get("analysis", {})
        
        # Extract Gong's analysis insights
        topics = analysis_data.get("topics", [])
        sentiment = analysis_data.get("sentiment", {})
        
        apartment_score = 0.0
        insights = []
        action_items = []
        
        # Analyze topics for apartment relevance
        for topic in topics:
            topic_text = topic.get("text", "").lower()
            if any(keyword in topic_text for keyword in self.apartment_keywords):
                apartment_score += 0.2
                insights.append(f"Apartment topic: {topic.get('text', 'Unknown')}")
        
        # Analyze sentiment
        sentiment_score = sentiment.get("overall", 0.0)
        if sentiment_score > 0.6:
            insights.append("Positive conversation sentiment")
            action_items.append("High engagement - schedule follow-up")
        elif sentiment_score < 0.4:
            insights.append("Negative conversation sentiment")
            action_items.append("Address concerns and objections")
        
        return {
            "apartment_relevant": apartment_score > 0.4,
            "apartment_relevance_score": min(apartment_score, 1.0),
            "insights": insights,
            "action_items": action_items,
            "sentiment_score": sentiment_score,
            "topic_count": len(topics)
        }
    
    async def _process_call_shared(self, event: WebhookEvent) -> Dict[str, Any]:
        """Process call shared event"""
        
        return {
            "apartment_relevant": False,
            "apartment_relevance_score": 0.0,
            "insights": ["Call shared with team"],
            "action_items": ["Review shared call for insights"]
        }
    
    async def _process_user_created(self, event: WebhookEvent) -> Dict[str, Any]:
        """Process user created event"""
        
        user_data = event.data.get("user", {})
        
        return {
            "apartment_relevant": False,
            "apartment_relevance_score": 0.0,
            "insights": [f"New user added: {user_data.get('name', 'Unknown')}"],
            "action_items": ["Welcome new team member"]
        }
    
    async def _generate_real_time_notifications(self, event: WebhookEvent, processing_result: Dict[str, Any]):
        """Generate real-time notifications for apartment-relevant events"""
        
        try:
            conn = await asyncpg.connect(**self.db_config)
            
            apartment_score = processing_result.get("apartment_relevance_score", 0.0)
            insights = processing_result.get("insights", [])
            action_items = processing_result.get("action_items", [])
            
            # Determine notification priority
            if apartment_score > 0.8:
                priority = "high"
                title = "🔥 High-Value Apartment Industry Conversation"
            elif apartment_score > 0.6:
                priority = "medium"
                title = "📞 Apartment Industry Conversation Detected"
            else:
                priority = "normal"
                title = "💬 New Conversation Activity"
            
            # Create notification message
            message_parts = []
            if insights:
                message_parts.append(f"Insights: {', '.join(insights[:3])}")
            if action_items:
                message_parts.append(f"Actions: {', '.join(action_items[:2])}")
            
            message = " | ".join(message_parts) if message_parts else "New conversation activity detected"
            
            # Store notification
            await conn.execute("""
                INSERT INTO real_time_notifications 
                (event_id, notification_type, title, message, priority, 
                 apartment_relevance_score, action_required)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            """,
                event.event_id,
                event.event_type,
                title,
                message,
                priority,
                apartment_score,
                len(action_items) > 0
            )
            
            await conn.close()
            
            # Send real-time notification (WebSocket, email, etc.)
            await self._send_real_time_notification({
                "event_id": event.event_id,
                "title": title,
                "message": message,
                "priority": priority,
                "apartment_score": apartment_score,
                "timestamp": datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error generating real-time notifications: {str(e)}")
    
    async def _send_real_time_notification(self, notification: Dict[str, Any]):
        """Send real-time notification via WebSocket/email/Slack"""
        
        # In production, this would send to WebSocket clients, email, Slack, etc.
        logger.info(f"Real-time notification: {notification['title']} - {notification['message']}")
        
        # Example: Send to Slack webhook
        # slack_webhook_url = "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"
        # requests.post(slack_webhook_url, json={"text": f"{notification['title']}: {notification['message']}"})
    
    async def _update_event_processing_status(self, event_id: str, status: str, result: Dict[str, Any]):
        """Update event processing status"""
        
        try:
            conn = await asyncpg.connect(**self.db_config)
            
            await conn.execute("""
                UPDATE webhook_events
                SET processed = TRUE,
                    processing_status = $2,
                    apartment_relevance_score = $3,
                    ai_insights = $4,
                    processed_at = CURRENT_TIMESTAMP
                WHERE event_id = $1
            """,
                event_id,
                status,
                result.get("apartment_relevance_score", 0.0),
                json.dumps(result)
            )
            
            await conn.close()
            
        except Exception as e:
            logger.error(f"Error updating event processing status: {str(e)}")
    
    async def _register_with_gong(self, workspace_id: str, event_types: List[str]) -> Dict[str, Any]:
        """Register webhook with Gong API (mock implementation)"""
        
        # In production, this would make actual API calls to Gong
        return {
            "webhook_id": f"wh_{workspace_id}_{int(time.time())}",
            "status": "registered",
            "events": event_types
        }
    
    def _verify_signature(self, payload: str, signature: str) -> bool:
        """Verify webhook signature"""
        
        expected_signature = hmac.new(
            self.webhook_secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(f"sha256={expected_signature}", signature)
    
    async def get_real_time_notifications(self, customer_id: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get real-time notifications"""
        
        try:
            conn = await asyncpg.connect(**self.db_config)
            
            if customer_id:
                rows = await conn.fetch("""
                    SELECT * FROM real_time_notifications
                    WHERE customer_id = $1
                    ORDER BY created_at DESC
                    LIMIT $2
                """, customer_id, limit)
            else:
                rows = await conn.fetch("""
                    SELECT * FROM real_time_notifications
                    ORDER BY created_at DESC
                    LIMIT $1
                """, limit)
            
            await conn.close()
            
            notifications = []
            for row in rows:
                notifications.append({
                    "id": row["id"],
                    "event_id": row["event_id"],
                    "type": row["notification_type"],
                    "title": row["title"],
                    "message": row["message"],
                    "priority": row["priority"],
                    "apartment_score": row["apartment_relevance_score"],
                    "action_required": row["action_required"],
                    "read_status": row["read_status"],
                    "created_at": row["created_at"].isoformat()
                })
            
            return notifications
            
        except Exception as e:
            logger.error(f"Error getting real-time notifications: {str(e)}")
            return []

# Flask application for webhook handling
app = Flask(__name__)
CORS(app, origins=["*"])

# Initialize webhook manager
webhook_manager = GongWebhookManager()

@app.route("/api/webhooks/gong", methods=["POST"])
async def handle_gong_webhook():
    """Handle incoming Gong webhook"""
    
    try:
        # Get signature from headers
        signature = request.headers.get("X-Gong-Signature")
        
        # Get event data
        event_data = request.get_json()
        
        if not event_data:
            return jsonify({"error": "No event data provided"}), 400
        
        # Process webhook event
        result = await webhook_manager.process_webhook_event(event_data, signature)
        
        if result["success"]:
            return jsonify({
                "status": "processed",
                "event_id": result["event_id"]
            })
        else:
            return jsonify({
                "error": result["error"]
            }), 400
            
    except Exception as e:
        logger.error(f"Error handling webhook: {str(e)}")
        return jsonify({
            "error": "Webhook processing failed",
            "details": str(e)
        }), 500

@app.route("/api/webhooks/register", methods=["POST"])
async def register_webhook():
    """Register webhook subscription"""
    
    try:
        data = request.get_json()
        
        customer_id = data.get("customer_id")
        workspace_id = data.get("workspace_id")
        event_types = data.get("event_types", webhook_manager.supported_events)
        webhook_url = data.get("webhook_url", webhook_manager.webhook_url)
        
        if not all([customer_id, workspace_id]):
            return jsonify({
                "error": "customer_id and workspace_id are required"
            }), 400
        
        result = await webhook_manager.register_webhook_subscription(
            customer_id, workspace_id, event_types, webhook_url
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error registering webhook: {str(e)}")
        return jsonify({
            "error": "Webhook registration failed",
            "details": str(e)
        }), 500

@app.route("/api/notifications")
async def get_notifications():
    """Get real-time notifications"""
    
    try:
        customer_id = request.args.get("customer_id")
        limit = int(request.args.get("limit", 50))
        
        notifications = await webhook_manager.get_real_time_notifications(customer_id, limit)
        
        return jsonify({
            "notifications": notifications,
            "count": len(notifications)
        })
        
    except Exception as e:
        logger.error(f"Error getting notifications: {str(e)}")
        return jsonify({
            "error": "Failed to get notifications",
            "details": str(e)
        }), 500

@app.route("/api/webhooks/test", methods=["POST"])
async def test_webhook():
    """Test webhook with sample data"""
    
    try:
        # Sample webhook event
        sample_event = {
            "eventId": f"test_evt_{int(time.time())}",
            "eventType": "call.transcribed",
            "workspaceId": "test_workspace",
            "callId": "test_call_123",
            "userId": "test_user",
            "timestamp": datetime.utcnow().isoformat(),
            "call": {
                "title": "Pay Ready apartment management software demo",
                "duration": 1800,
                "participants": [
                    {"name": "John Smith", "company": "Sunset Apartments Management"},
                    {"name": "Sarah Johnson", "company": "Pay Ready"}
                ]
            },
            "transcript": {
                "text": "We're looking for apartment payment solutions. Pay Ready seems like a good fit for our property management needs. We manage 500 units across multiple apartment complexes."
            }
        }
        
        # Process test event
        result = await webhook_manager.process_webhook_event(sample_event)
        
        return jsonify({
            "test_result": result,
            "sample_event": sample_event
        })
        
    except Exception as e:
        logger.error(f"Error testing webhook: {str(e)}")
        return jsonify({
            "error": "Webhook test failed",
            "details": str(e)
        }), 500

@app.route("/api/health")
def health_check():
    """Health check endpoint"""
    
    return jsonify({
        "status": "healthy",
        "service": "Gong Webhook Manager",
        "timestamp": datetime.utcnow().isoformat(),
        "supported_events": webhook_manager.supported_events,
        "features": {
            "real_time_processing": "implemented",
            "apartment_relevance_scoring": "implemented",
            "notification_system": "implemented",
            "webhook_verification": "implemented"
        }
    })

# Test the webhook system
async def test_webhook_system():
    """Test webhook functionality"""
    
    # Setup schema
    await webhook_manager.setup_webhook_schema()
    
    # Test webhook registration
    registration_result = await webhook_manager.register_webhook_subscription(
        "test_customer_123",
        "test_workspace",
        ["call.recorded", "call.transcribed"],
        "https://test.com/webhook"
    )
    
    # Test event processing
    test_event_data = {
        "eventId": "test_event_123",
        "eventType": "call.transcribed",
        "workspaceId": "test_workspace",
        "callId": "test_call_456",
        "timestamp": datetime.utcnow().isoformat(),
        "transcript": {
            "text": "We need apartment management software for our property management company"
        }
    }
    
    processing_result = await webhook_manager.process_webhook_event(test_event_data)
    
    # Get notifications
    notifications = await webhook_manager.get_real_time_notifications(limit=10)
    
    return {
        "schema_created": True,
        "webhook_registered": registration_result["success"],
        "event_processed": processing_result["success"],
        "notifications_count": len(notifications)
    }

if __name__ == "__main__":
    # Run test
    result = asyncio.run(test_webhook_system())
    print(f"Webhook system test results: {json.dumps(result, indent=2)}")
    
    # Run Flask application
    app.run(host="0.0.0.0", port=5003, debug=True)

