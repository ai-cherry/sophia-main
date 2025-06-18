import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import httpx
import json
from ...core.secret_manager import secret_manager

class EnhancedGongIntegration:
    """Enhanced Gong integration supporting calls + emails + meetings"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.base_url = "https://api.gong.io/v2"
        self.client = None
        
    async def setup(self):
        """Initialize HTTP client with authentication"""
        api_key = await secret_manager.get_secret("api_key", "gong")
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            timeout=30.0
        )
    
    async def get_conversations_by_date_range(self, 
                                            start_date: str, 
                                            end_date: str,
                                            conversation_types: List[str] = None) -> List[Dict[str, Any]]:
        """Get all conversations (calls + emails + meetings) for date range"""
        if conversation_types is None:
            conversation_types = ["call", "email", "meeting"]
            
        all_conversations = []
        
        for conv_type in conversation_types:
            try:
                if conv_type == "call":
                    conversations = await self._get_calls(start_date, end_date)
                elif conv_type == "email":
                    conversations = await self._get_emails(start_date, end_date)
                elif conv_type == "meeting":
                    conversations = await self._get_meetings(start_date, end_date)
                    
                # Add conversation type to each record
                for conv in conversations:
                    conv["conversation_type"] = conv_type
                    
                all_conversations.extend(conversations)
                
            except Exception as e:
                self.logger.error(f"Failed to fetch {conv_type} data: {e}")
                
        return all_conversations
    
    async def _get_calls(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Get call data with enhanced metadata"""
        response = await self.client.post("/calls", json={
            "filter": {
                "fromDateTime": start_date,
                "toDateTime": end_date
            },
            "contentSelector": {
                "includeMetadata": True,
                "includeTranscript": True,
                "includeSpotlight": True,
                "includeParticipants": True,
                "includeTrackers": True,
                "includeCrmContext": True
            }
        })
        response.raise_for_status()
        
        calls_data = response.json()
        enhanced_calls = []
        
        for call in calls_data.get("calls", []):
            # Get detailed call information
            call_detail = await self._get_call_detail(call["id"])
            enhanced_calls.append(call_detail)
            
        return enhanced_calls
    
    async def _get_emails(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Get email data with enhanced metadata"""
        response = await self.client.post("/emails", json={
            "filter": {
                "fromDateTime": start_date,
                "toDateTime": end_date
            },
            "contentSelector": {
                "includeMetadata": True,
                "includeEmailBody": True,
                "includeParticipants": True,
                "includeTrackers": True,
                "includeCrmContext": True,
                "includeSentiment": True
            }
        })
        response.raise_for_status()
        
        emails_data = response.json()
        enhanced_emails = []
        
        for email in emails_data.get("emails", []):
            # Get detailed email information
            email_detail = await self._get_email_detail(email["id"])
            enhanced_emails.append(email_detail)
            
        return enhanced_emails
    
    async def _get_meetings(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Get meeting data"""
        response = await self.client.post("/meetings", json={
            "filter": {
                "fromDateTime": start_date,
                "toDateTime": end_date
            },
            "contentSelector": {
                "includeMetadata": True,
                "includeParticipants": True,
                "includeTrackers": True,
                "includeCrmContext": True
            }
        })
        response.raise_for_status()
        
        return response.json().get("meetings", [])
    
    async def _get_call_detail(self, call_id: str) -> Dict[str, Any]:
        """Get detailed call information including transcript and spotlight"""
        response = await self.client.get(f"/calls/{call_id}")
        response.raise_for_status()
        call_data = response.json()
        
        # Get transcript if available
        try:
            transcript_response = await self.client.get(f"/calls/{call_id}/transcript")
            if transcript_response.status_code == 200:
                call_data["transcript"] = transcript_response.json()
        except Exception as e:
            self.logger.warning(f"Could not fetch transcript for call {call_id}: {e}")
            
        return call_data
    
    async def _get_email_detail(self, email_id: str) -> Dict[str, Any]:
        """Get detailed email information including body and sentiment"""
        response = await self.client.get(f"/emails/{email_id}")
        response.raise_for_status()
        return response.json()
    
    async def test_connection(self) -> bool:
        """Test Gong API connection"""
        try:
            response = await self.client.get("/users")
            return response.status_code == 200
        except Exception as e:
            self.logger.error(f"Gong connection test failed: {e}")
            return False
            
    def _extract_transcript_text(self, transcript_data: Dict[str, Any]) -> str:
        """Extract plain text from transcript JSON"""
        if not transcript_data or "transcript" not in transcript_data:
            return ""
            
        text_parts = []
        for segment in transcript_data.get("transcript", []):
            speaker = segment.get("speakerName", "Unknown")
            text = segment.get("text", "")
            text_parts.append(f"{speaker}: {text}")
            
        return "\n".join(text_parts)
