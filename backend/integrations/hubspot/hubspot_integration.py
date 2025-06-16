"""
Sophia AI - HubSpot Integration
Business CRM Integration for Pay Ready

This module provides comprehensive HubSpot integration for Sophia AI,
enabling automated CRM operations, contact management, and deal tracking.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import aiohttp
import hubspot
from hubspot.crm.contacts import SimplePublicObjectInput, ApiException
from hubspot.crm.deals import SimplePublicObjectInput as DealInput
from hubspot.crm.companies import SimplePublicObjectInput as CompanyInput
import os

logger = logging.getLogger(__name__)

class HubSpotConfig:
    def __init__(self):
        self.api_key = os.getenv('HUBSPOT_API_KEY', '')
        self.base_url = "https://api.hubapi.com"
        self.rate_limit_delay = 0.1  # 100ms between requests
        self.max_retries = 3
        self.timeout = 30

class HubSpotIntegration:
    """Comprehensive HubSpot CRM integration"""
    
    def __init__(self, config: HubSpotConfig = None):
        self.config = config or HubSpotConfig()
        self.client = hubspot.Client.create(api_key=self.config.api_key)
        self.session = None
        self.last_request_time = datetime.now()
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.config.timeout))
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def _rate_limit_delay(self):
        """Implement rate limiting to avoid API limits"""
        elapsed = (datetime.now() - self.last_request_time).total_seconds()
        if elapsed < self.config.rate_limit_delay:
            await asyncio.sleep(self.config.rate_limit_delay - elapsed)
        self.last_request_time = datetime.now()
    
    async def _make_request(self, method: str, endpoint: str, data: Dict = None, params: Dict = None) -> Dict[str, Any]:
        """Make rate-limited API request with retry logic"""
        await self._rate_limit_delay()
        
        url = f"{self.config.base_url}{endpoint}"
        headers = {
            'Authorization': f'Bearer {self.config.api_key}',
            'Content-Type': 'application/json'
        }
        
        for attempt in range(self.config.max_retries):
            try:
                async with self.session.request(
                    method, url, 
                    json=data, 
                    params=params, 
                    headers=headers
                ) as response:
                    if response.status == 429:  # Rate limited
                        retry_after = int(response.headers.get('Retry-After', 1))
                        await asyncio.sleep(retry_after)
                        continue
                    
                    response.raise_for_status()
                    return await response.json()
                    
            except Exception as e:
                if attempt == self.config.max_retries - 1:
                    logger.error(f"HubSpot API request failed after {self.config.max_retries} attempts: {str(e)}")
                    raise
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
    
    # Contact Management
    async def get_contact(self, contact_id: str = None, email: str = None) -> Optional[Dict[str, Any]]:
        """Get contact by ID or email"""
        try:
            if contact_id:
                endpoint = f"/crm/v3/objects/contacts/{contact_id}"
                params = {'properties': 'email,firstname,lastname,company,phone,lifecyclestage,createdate,lastmodifieddate'}
                return await self._make_request('GET', endpoint, params=params)
            
            elif email:
                endpoint = "/crm/v3/objects/contacts/search"
                data = {
                    "filterGroups": [{
                        "filters": [{
                            "propertyName": "email",
                            "operator": "EQ",
                            "value": email
                        }]
                    }],
                    "properties": ['email', 'firstname', 'lastname', 'company', 'phone', 'lifecyclestage', 'createdate', 'lastmodifieddate']
                }
                result = await self._make_request('POST', endpoint, data=data)
                return result.get('results', [{}])[0] if result.get('results') else None
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get contact: {str(e)}")
            return None
    
    async def create_contact(self, contact_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create new contact in HubSpot"""
        try:
            endpoint = "/crm/v3/objects/contacts"
            data = {"properties": contact_data}
            
            result = await self._make_request('POST', endpoint, data=data)
            logger.info(f"Created contact: {contact_data.get('email', 'unknown')}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to create contact: {str(e)}")
            return None
    
    async def update_contact(self, contact_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update existing contact"""
        try:
            endpoint = f"/crm/v3/objects/contacts/{contact_id}"
            data = {"properties": updates}
            
            result = await self._make_request('PATCH', endpoint, data=data)
            logger.info(f"Updated contact {contact_id}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to update contact {contact_id}: {str(e)}")
            return None
    
    async def search_contacts(self, filters: List[Dict[str, Any]], limit: int = 100) -> List[Dict[str, Any]]:
        """Search contacts with filters"""
        try:
            endpoint = "/crm/v3/objects/contacts/search"
            data = {
                "filterGroups": [{"filters": filters}],
                "properties": ['email', 'firstname', 'lastname', 'company', 'phone', 'lifecyclestage'],
                "limit": limit
            }
            
            result = await self._make_request('POST', endpoint, data=data)
            return result.get('results', [])
            
        except Exception as e:
            logger.error(f"Failed to search contacts: {str(e)}")
            return []
    
    # Deal Management
    async def get_deal(self, deal_id: str) -> Optional[Dict[str, Any]]:
        """Get deal by ID"""
        try:
            endpoint = f"/crm/v3/objects/deals/{deal_id}"
            params = {
                'properties': 'dealname,amount,dealstage,pipeline,closedate,createdate,hs_deal_stage_probability,dealtype'
            }
            return await self._make_request('GET', endpoint, params=params)
            
        except Exception as e:
            logger.error(f"Failed to get deal {deal_id}: {str(e)}")
            return None
    
    async def create_deal(self, deal_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create new deal"""
        try:
            endpoint = "/crm/v3/objects/deals"
            data = {"properties": deal_data}
            
            result = await self._make_request('POST', endpoint, data=data)
            logger.info(f"Created deal: {deal_data.get('dealname', 'unknown')}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to create deal: {str(e)}")
            return None
    
    async def update_deal(self, deal_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update existing deal"""
        try:
            endpoint = f"/crm/v3/objects/deals/{deal_id}"
            data = {"properties": updates}
            
            result = await self._make_request('PATCH', endpoint, data=data)
            logger.info(f"Updated deal {deal_id}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to update deal {deal_id}: {str(e)}")
            return None
    
    async def get_deals_by_contact(self, contact_id: str) -> List[Dict[str, Any]]:
        """Get all deals associated with a contact"""
        try:
            endpoint = f"/crm/v3/objects/contacts/{contact_id}/associations/deals"
            associations = await self._make_request('GET', endpoint)
            
            deals = []
            for assoc in associations.get('results', []):
                deal = await self.get_deal(assoc['id'])
                if deal:
                    deals.append(deal)
            
            return deals
            
        except Exception as e:
            logger.error(f"Failed to get deals for contact {contact_id}: {str(e)}")
            return []
    
    # Company Management
    async def get_company(self, company_id: str = None, domain: str = None) -> Optional[Dict[str, Any]]:
        """Get company by ID or domain"""
        try:
            if company_id:
                endpoint = f"/crm/v3/objects/companies/{company_id}"
                params = {'properties': 'name,domain,industry,city,state,country,phone,numberofemployees'}
                return await self._make_request('GET', endpoint, params=params)
            
            elif domain:
                endpoint = "/crm/v3/objects/companies/search"
                data = {
                    "filterGroups": [{
                        "filters": [{
                            "propertyName": "domain",
                            "operator": "EQ",
                            "value": domain
                        }]
                    }],
                    "properties": ['name', 'domain', 'industry', 'city', 'state', 'country', 'phone', 'numberofemployees']
                }
                result = await self._make_request('POST', endpoint, data=data)
                return result.get('results', [{}])[0] if result.get('results') else None
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get company: {str(e)}")
            return None
    
    async def create_company(self, company_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create new company"""
        try:
            endpoint = "/crm/v3/objects/companies"
            data = {"properties": company_data}
            
            result = await self._make_request('POST', endpoint, data=data)
            logger.info(f"Created company: {company_data.get('name', 'unknown')}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to create company: {str(e)}")
            return None
    
    # Activity and Engagement Tracking
    async def create_note(self, contact_id: str, note_content: str, note_type: str = "CALL") -> Optional[Dict[str, Any]]:
        """Create note/activity for contact"""
        try:
            endpoint = "/crm/v3/objects/notes"
            data = {
                "properties": {
                    "hs_note_body": note_content,
                    "hs_attachment_ids": "",
                    "hubspot_owner_id": "",
                    "hs_timestamp": datetime.now().isoformat()
                },
                "associations": [{
                    "to": {"id": contact_id},
                    "types": [{"associationCategory": "HUBSPOT_DEFINED", "associationTypeId": 202}]
                }]
            }
            
            result = await self._make_request('POST', endpoint, data=data)
            logger.info(f"Created note for contact {contact_id}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to create note for contact {contact_id}: {str(e)}")
            return None
    
    async def create_task(self, contact_id: str, task_title: str, task_body: str, due_date: datetime = None) -> Optional[Dict[str, Any]]:
        """Create task for contact"""
        try:
            endpoint = "/crm/v3/objects/tasks"
            
            task_data = {
                "hs_task_subject": task_title,
                "hs_task_body": task_body,
                "hs_task_status": "NOT_STARTED",
                "hs_task_priority": "MEDIUM",
                "hs_timestamp": datetime.now().isoformat()
            }
            
            if due_date:
                task_data["hs_task_due_date"] = due_date.isoformat()
            
            data = {
                "properties": task_data,
                "associations": [{
                    "to": {"id": contact_id},
                    "types": [{"associationCategory": "HUBSPOT_DEFINED", "associationTypeId": 204}]
                }]
            }
            
            result = await self._make_request('POST', endpoint, data=data)
            logger.info(f"Created task for contact {contact_id}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to create task for contact {contact_id}: {str(e)}")
            return None
    
    # Analytics and Reporting
    async def get_contact_analytics(self, contact_id: str) -> Dict[str, Any]:
        """Get analytics data for contact"""
        try:
            # Get contact details
            contact = await self.get_contact(contact_id)
            if not contact:
                return {}
            
            # Get associated deals
            deals = await self.get_deals_by_contact(contact_id)
            
            # Calculate analytics
            total_deal_value = sum(float(deal.get('properties', {}).get('amount', 0) or 0) for deal in deals)
            open_deals = [deal for deal in deals if deal.get('properties', {}).get('dealstage') not in ['closedwon', 'closedlost']]
            closed_won_deals = [deal for deal in deals if deal.get('properties', {}).get('dealstage') == 'closedwon']
            
            analytics = {
                'contact_id': contact_id,
                'total_deals': len(deals),
                'total_deal_value': total_deal_value,
                'open_deals': len(open_deals),
                'closed_won_deals': len(closed_won_deals),
                'win_rate': len(closed_won_deals) / len(deals) if deals else 0,
                'lifecycle_stage': contact.get('properties', {}).get('lifecyclestage'),
                'last_activity': contact.get('properties', {}).get('lastmodifieddate'),
                'created_date': contact.get('properties', {}).get('createdate')
            }
            
            return analytics
            
        except Exception as e:
            logger.error(f"Failed to get contact analytics for {contact_id}: {str(e)}")
            return {}
    
    async def get_pipeline_analytics(self, pipeline_id: str = None) -> Dict[str, Any]:
        """Get pipeline performance analytics"""
        try:
            # Get all deals in pipeline
            endpoint = "/crm/v3/objects/deals/search"
            filters = []
            if pipeline_id:
                filters.append({
                    "propertyName": "pipeline",
                    "operator": "EQ",
                    "value": pipeline_id
                })
            
            data = {
                "filterGroups": [{"filters": filters}] if filters else [],
                "properties": ['dealname', 'amount', 'dealstage', 'pipeline', 'closedate', 'createdate'],
                "limit": 1000
            }
            
            result = await self._make_request('POST', endpoint, data=data)
            deals = result.get('results', [])
            
            # Calculate analytics
            total_value = sum(float(deal.get('properties', {}).get('amount', 0) or 0) for deal in deals)
            closed_won = [deal for deal in deals if deal.get('properties', {}).get('dealstage') == 'closedwon']
            closed_lost = [deal for deal in deals if deal.get('properties', {}).get('dealstage') == 'closedlost']
            open_deals = [deal for deal in deals if deal.get('properties', {}).get('dealstage') not in ['closedwon', 'closedlost']]
            
            analytics = {
                'pipeline_id': pipeline_id,
                'total_deals': len(deals),
                'total_value': total_value,
                'closed_won_count': len(closed_won),
                'closed_won_value': sum(float(deal.get('properties', {}).get('amount', 0) or 0) for deal in closed_won),
                'closed_lost_count': len(closed_lost),
                'open_deals_count': len(open_deals),
                'open_deals_value': sum(float(deal.get('properties', {}).get('amount', 0) or 0) for deal in open_deals),
                'win_rate': len(closed_won) / (len(closed_won) + len(closed_lost)) if (closed_won or closed_lost) else 0,
                'average_deal_size': total_value / len(deals) if deals else 0
            }
            
            return analytics
            
        except Exception as e:
            logger.error(f"Failed to get pipeline analytics: {str(e)}")
            return {}
    
    # Bulk Operations
    async def bulk_update_contacts(self, updates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Bulk update multiple contacts"""
        try:
            endpoint = "/crm/v3/objects/contacts/batch/update"
            data = {"inputs": updates}
            
            result = await self._make_request('POST', endpoint, data=data)
            logger.info(f"Bulk updated {len(updates)} contacts")
            return result.get('results', [])
            
        except Exception as e:
            logger.error(f"Failed to bulk update contacts: {str(e)}")
            return []
    
    async def export_contacts(self, filters: List[Dict[str, Any]] = None, properties: List[str] = None) -> List[Dict[str, Any]]:
        """Export contacts with optional filters"""
        try:
            all_contacts = []
            after = None
            
            while True:
                endpoint = "/crm/v3/objects/contacts/search"
                data = {
                    "filterGroups": [{"filters": filters}] if filters else [],
                    "properties": properties or ['email', 'firstname', 'lastname', 'company', 'phone', 'lifecyclestage'],
                    "limit": 100
                }
                
                if after:
                    data["after"] = after
                
                result = await self._make_request('POST', endpoint, data=data)
                contacts = result.get('results', [])
                
                if not contacts:
                    break
                
                all_contacts.extend(contacts)
                
                # Check for pagination
                paging = result.get('paging', {})
                if 'next' not in paging:
                    break
                
                after = paging['next']['after']
            
            logger.info(f"Exported {len(all_contacts)} contacts")
            return all_contacts
            
        except Exception as e:
            logger.error(f"Failed to export contacts: {str(e)}")
            return []

class HubSpotWebhookHandler:
    """Handle HubSpot webhooks for real-time updates"""
    
    def __init__(self, webhook_secret: str = None):
        self.webhook_secret = webhook_secret
        self.handlers = {}
    
    def register_handler(self, event_type: str, handler_func):
        """Register handler for specific webhook event"""
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        self.handlers[event_type].append(handler_func)
    
    async def process_webhook(self, payload: Dict[str, Any], signature: str = None) -> bool:
        """Process incoming webhook"""
        try:
            # Verify signature if secret is provided
            if self.webhook_secret and signature:
                # Implement signature verification
                pass
            
            # Process each event in the payload
            for event in payload:
                event_type = event.get('subscriptionType')
                if event_type in self.handlers:
                    for handler in self.handlers[event_type]:
                        try:
                            await handler(event)
                        except Exception as e:
                            logger.error(f"Webhook handler error for {event_type}: {str(e)}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to process webhook: {str(e)}")
            return False

# Example usage and testing
if __name__ == "__main__":
    async def main():
        config = HubSpotConfig()
        
        async with HubSpotIntegration(config) as hubspot:
            # Test contact operations
            contact = await hubspot.get_contact(email="test@example.com")
            print(f"Contact: {contact}")
            
            # Test analytics
            if contact:
                analytics = await hubspot.get_contact_analytics(contact['id'])
                print(f"Analytics: {analytics}")
    
    asyncio.run(main())

