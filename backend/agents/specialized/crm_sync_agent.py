"""
Sophia AI - CRM Sync Agent
Specialized agent for synchronizing data between systems and maintaining CRM accuracy

This agent handles data synchronization between Gong.io, HubSpot, and other business systems.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from ..core.base_agent import BaseAgent, AgentConfig, AgentCapability, Task, create_agent_response, validate_task_data
from ..integrations.hubspot.hubspot_integration import HubSpotIntegration, HubSpotConfig
from ..integrations.gong.gong_integration import GongIntegration, GongConfig

logger = logging.getLogger(__name__)

class CRMSyncAgent(BaseAgent):
    """Specialized agent for CRM data synchronization and maintenance"""
    
    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self.hubspot_integration = None
        self.gong_integration = None
        
    async def start(self):
        """Start the agent and initialize integrations"""
        await super().start()
        
        # Initialize integrations
        hubspot_config = HubSpotConfig()
        self.hubspot_integration = HubSpotIntegration(hubspot_config)
        
        gong_config = GongConfig()
        self.gong_integration = GongIntegration(gong_config)
        
        logger.info("CRM Sync Agent started with integrations")
    
    async def get_capabilities(self) -> List[AgentCapability]:
        return [
            AgentCapability(
                name="sync_call_to_crm",
                description="Sync call data and insights to CRM system",
                input_types=["call_data", "contact_info"],
                output_types=["sync_status", "crm_updates"],
                estimated_duration=30.0
            ),
            AgentCapability(
                name="update_deal_stage",
                description="Update deal stage based on call outcomes",
                input_types=["deal_id", "call_insights"],
                output_types=["deal_update_status"],
                estimated_duration=15.0
            ),
            AgentCapability(
                name="create_follow_up_tasks",
                description="Create follow-up tasks based on call analysis",
                input_types=["call_insights", "contact_id"],
                output_types=["tasks_created"],
                estimated_duration=20.0
            ),
            AgentCapability(
                name="data_quality_check",
                description="Check and improve CRM data quality",
                input_types=["contact_list"],
                output_types=["quality_report", "cleanup_suggestions"],
                estimated_duration=60.0
            )
        ]
    
    async def process_task(self, task: Task) -> Dict[str, Any]:
        """Process assigned task based on type"""
        try:
            task_type = task.task_type
            
            if task_type == "sync_call_to_crm":
                return await self._sync_call_to_crm(task)
            elif task_type == "update_deal_stage":
                return await self._update_deal_stage(task)
            elif task_type == "create_follow_up_tasks":
                return await self._create_follow_up_tasks(task)
            elif task_type == "data_quality_check":
                return await self._perform_data_quality_check(task)
            else:
                raise ValueError(f"Unknown task type: {task_type}")
                
        except Exception as e:
            logger.error(f"CRM Sync Agent task failed: {str(e)}")
            return await create_agent_response(False, error=str(e))
    
    async def _sync_call_to_crm(self, task: Task) -> Dict[str, Any]:
        """Sync call data to CRM system"""
        try:
            # Validate required fields
            if not await validate_task_data(task, ['call_data', 'contact_email']):
                raise ValueError("Missing required fields: call_data, contact_email")
            
            call_data = task.task_data['call_data']
            contact_email = task.task_data['contact_email']
            
            # Get or create contact
            async with self.hubspot_integration:
                contact = await self.hubspot_integration.get_contact(email=contact_email)
                
                if not contact:
                    # Extract contact info from call data
                    contact_info = self._extract_contact_info(call_data)
                    contact_info['email'] = contact_email
                    contact = await self.hubspot_integration.create_contact(contact_info)
                
                if not contact:
                    raise ValueError("Failed to create or retrieve contact")
                
                contact_id = contact['id']
                
                # Create call note
                note_content = self._format_call_note(call_data)
                note_result = await self.hubspot_integration.create_note(contact_id, note_content)
                
                # Update contact properties
                contact_updates = self._prepare_contact_updates(call_data)
                update_result = None
                if contact_updates:
                    update_result = await self.hubspot_integration.update_contact(contact_id, contact_updates)
                
                # Create or update deal if applicable
                deal_result = None
                if call_data.get('deal_related', True):
                    deal_result = await self._handle_deal_sync(contact_id, call_data)
            
            result = {
                'contact_id': contact_id,
                'contact_email': contact_email,
                'note_created': bool(note_result),
                'contact_updated': bool(update_result),
                'deal_handled': bool(deal_result),
                'sync_timestamp': datetime.now().isoformat()
            }
            
            return await create_agent_response(True, result)
            
        except Exception as e:
            return await create_agent_response(False, error=str(e))
    
    async def _update_deal_stage(self, task: Task) -> Dict[str, Any]:
        """Update deal stage based on call insights"""
        try:
            # Validate required fields
            if not await validate_task_data(task, ['deal_id', 'call_insights']):
                raise ValueError("Missing required fields: deal_id, call_insights")
            
            deal_id = task.task_data['deal_id']
            call_insights = task.task_data['call_insights']
            
            # Determine new deal stage
            new_stage = self._determine_deal_stage(call_insights)
            
            # Update deal in HubSpot
            async with self.hubspot_integration:
                deal_updates = {
                    'dealstage': new_stage,
                    'last_activity_date': datetime.now().isoformat()
                }
                
                # Add probability if available
                if call_insights.get('success_probability'):
                    deal_updates['probability'] = call_insights['success_probability']
                
                # Add close date estimate if available
                if call_insights.get('estimated_close_date'):
                    deal_updates['closedate'] = call_insights['estimated_close_date']
                
                update_result = await self.hubspot_integration.update_deal(deal_id, deal_updates)
            
            result = {
                'deal_id': deal_id,
                'new_stage': new_stage,
                'updates_applied': deal_updates,
                'update_successful': bool(update_result),
                'update_timestamp': datetime.now().isoformat()
            }
            
            return await create_agent_response(True, result)
            
        except Exception as e:
            return await create_agent_response(False, error=str(e))
    
    async def _create_follow_up_tasks(self, task: Task) -> Dict[str, Any]:
        """Create follow-up tasks based on call analysis"""
        try:
            # Validate required fields
            if not await validate_task_data(task, ['call_insights', 'contact_id']):
                raise ValueError("Missing required fields: call_insights, contact_id")
            
            call_insights = task.task_data['call_insights']
            contact_id = task.task_data['contact_id']
            
            tasks_created = []
            
            async with self.hubspot_integration:
                # Create tasks for next steps
                if call_insights.get('next_steps'):
                    for next_step in call_insights['next_steps']:
                        task_data = {
                            'title': f"Follow-up: {next_step}",
                            'description': f"Based on call analysis: {next_step}",
                            'due_date': self._calculate_due_date(next_step),
                            'priority': self._determine_task_priority(next_step)
                        }
                        
                        task_result = await self.hubspot_integration.create_task(
                            contact_id,
                            task_data['title'],
                            task_data['description'],
                            task_data['due_date']
                        )
                        
                        if task_result:
                            tasks_created.append(task_result)
                
                # Create tasks for objections to address
                if call_insights.get('objections'):
                    for objection in call_insights['objections']:
                        task_data = {
                            'title': f"Address objection: {objection}",
                            'description': f"Prepare response to objection raised: {objection}",
                            'due_date': datetime.now() + timedelta(days=1),
                            'priority': 'high'
                        }
                        
                        task_result = await self.hubspot_integration.create_task(
                            contact_id,
                            task_data['title'],
                            task_data['description'],
                            task_data['due_date']
                        )
                        
                        if task_result:
                            tasks_created.append(task_result)
                
                # Create reminder tasks for high-priority deals
                if call_insights.get('deal_priority') == 'high':
                    reminder_task = await self.hubspot_integration.create_task(
                        contact_id,
                        "High-priority deal check-in",
                        "Check in on high-priority opportunity",
                        datetime.now() + timedelta(days=3)
                    )
                    
                    if reminder_task:
                        tasks_created.append(reminder_task)
            
            result = {
                'contact_id': contact_id,
                'tasks_created': len(tasks_created),
                'task_details': tasks_created,
                'creation_timestamp': datetime.now().isoformat()
            }
            
            return await create_agent_response(True, result)
            
        except Exception as e:
            return await create_agent_response(False, error=str(e))
    
    async def _perform_data_quality_check(self, task: Task) -> Dict[str, Any]:
        """Perform data quality check on CRM data"""
        try:
            # This would be a comprehensive data quality analysis
            quality_issues = []
            cleanup_suggestions = []
            
            async with self.hubspot_integration:
                # Get recent contacts for analysis
                contacts = await self.hubspot_integration.get_recent_contacts(limit=100)
                
                for contact in contacts:
                    issues = self._analyze_contact_quality(contact)
                    if issues:
                        quality_issues.extend(issues)
                
                # Generate cleanup suggestions
                cleanup_suggestions = self._generate_cleanup_suggestions(quality_issues)
            
            result = {
                'contacts_analyzed': len(contacts) if 'contacts' in locals() else 0,
                'quality_issues_found': len(quality_issues),
                'quality_issues': quality_issues[:10],  # Limit for response size
                'cleanup_suggestions': cleanup_suggestions,
                'analysis_timestamp': datetime.now().isoformat()
            }
            
            return await create_agent_response(True, result)
            
        except Exception as e:
            return await create_agent_response(False, error=str(e))
    
    def _extract_contact_info(self, call_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract contact information from call data"""
        contact_info = {}
        
        # Extract name
        if call_data.get('participants'):
            for participant in call_data['participants']:
                if not participant.get('is_internal', False):
                    name_parts = participant.get('name', '').split(' ')
                    if name_parts:
                        contact_info['firstname'] = name_parts[0]
                        if len(name_parts) > 1:
                            contact_info['lastname'] = ' '.join(name_parts[1:])
                    break
        
        # Extract company
        if call_data.get('company_name'):
            contact_info['company'] = call_data['company_name']
        
        # Set lifecycle stage
        contact_info['lifecyclestage'] = 'lead'
        
        # Extract phone if available
        if call_data.get('phone_number'):
            contact_info['phone'] = call_data['phone_number']
        
        return contact_info
    
    def _format_call_note(self, call_data: Dict[str, Any]) -> str:
        """Format call data as CRM note"""
        note_parts = [
            f"Call Summary - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        ]
        
        if call_data.get('duration'):
            note_parts.append(f"Duration: {call_data['duration']} minutes")
        
        if call_data.get('key_topics'):
            note_parts.append(f"Key Topics: {', '.join(call_data['key_topics'])}")
        
        if call_data.get('pain_points'):
            note_parts.append(f"Pain Points: {', '.join(call_data['pain_points'])}")
        
        if call_data.get('next_steps'):
            note_parts.append(f"Next Steps: {', '.join(call_data['next_steps'])}")
        
        if call_data.get('outcome'):
            note_parts.append(f"Outcome: {call_data['outcome']}")
        
        return "\n".join(note_parts)
    
    def _prepare_contact_updates(self, call_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare contact property updates based on call data"""
        updates = {}
        
        # Update last contact date
        updates['lastcontacted'] = datetime.now().isoformat()
        
        # Update lifecycle stage if progressed
        if call_data.get('deal_stage'):
            lifecycle_stage = self._map_deal_stage_to_lifecycle(call_data['deal_stage'])
            updates['lifecyclestage'] = lifecycle_stage
        
        # Update lead source if first contact
        if call_data.get('is_first_contact'):
            updates['hs_lead_source'] = 'Sales Call'
        
        # Update notes about interests
        if call_data.get('interests'):
            updates['notes_last_contacted'] = f"Interested in: {', '.join(call_data['interests'])}"
        
        return updates
    
    async def _handle_deal_sync(self, contact_id: str, call_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Handle deal creation or update based on call data"""
        try:
            async with self.hubspot_integration:
                # Check if contact has existing deals
                existing_deals = await self.hubspot_integration.get_contact_deals(contact_id)
                
                if existing_deals:
                    # Update existing deal
                    deal_id = existing_deals[0]['id']
                    deal_updates = {
                        'last_activity_date': datetime.now().isoformat()
                    }
                    
                    if call_data.get('deal_stage'):
                        deal_updates['dealstage'] = call_data['deal_stage']
                    
                    if call_data.get('deal_value'):
                        deal_updates['amount'] = call_data['deal_value']
                    
                    return await self.hubspot_integration.update_deal(deal_id, deal_updates)
                
                else:
                    # Create new deal
                    deal_data = {
                        'dealname': f"Deal - {call_data.get('company_name', 'Unknown Company')}",
                        'dealstage': call_data.get('deal_stage', 'appointmentscheduled'),
                        'amount': call_data.get('deal_value', 50000),  # Default value
                        'closedate': (datetime.now() + timedelta(days=30)).isoformat(),
                        'pipeline': 'default'
                    }
                    
                    deal = await self.hubspot_integration.create_deal(deal_data)
                    
                    if deal:
                        # Associate deal with contact
                        await self.hubspot_integration.associate_deal_contact(deal['id'], contact_id)
                    
                    return deal
        
        except Exception as e:
            logger.error(f"Failed to handle deal sync: {str(e)}")
            return None
    
    def _determine_deal_stage(self, call_insights: Dict[str, Any]) -> str:
        """Determine appropriate deal stage based on call insights"""
        # Map call outcomes to deal stages
        if call_insights.get('outcome') == 'demo_scheduled':
            return 'presentationscheduled'
        elif call_insights.get('outcome') == 'proposal_requested':
            return 'decisionmakerboughtin'
        elif call_insights.get('outcome') == 'contract_discussion':
            return 'contractsent'
        elif call_insights.get('next_steps'):
            # If there are next steps, move to qualified
            return 'qualifiedtobuy'
        else:
            # Default to appointment scheduled
            return 'appointmentscheduled'
    
    def _calculate_due_date(self, next_step: str) -> datetime:
        """Calculate appropriate due date for a next step"""
        next_step_lower = next_step.lower()
        
        # Urgent items
        if any(word in next_step_lower for word in ['urgent', 'asap', 'today']):
            return datetime.now() + timedelta(hours=4)
        
        # This week items
        elif any(word in next_step_lower for word in ['this week', 'soon', 'quickly']):
            return datetime.now() + timedelta(days=2)
        
        # Demo or meeting items
        elif any(word in next_step_lower for word in ['demo', 'meeting', 'call']):
            return datetime.now() + timedelta(days=3)
        
        # Default
        else:
            return datetime.now() + timedelta(days=1)
    
    def _determine_task_priority(self, next_step: str) -> str:
        """Determine task priority based on next step content"""
        next_step_lower = next_step.lower()
        
        if any(word in next_step_lower for word in ['urgent', 'asap', 'critical']):
            return 'high'
        elif any(word in next_step_lower for word in ['demo', 'proposal', 'contract']):
            return 'high'
        elif any(word in next_step_lower for word in ['follow up', 'check in']):
            return 'medium'
        else:
            return 'medium'
    
    def _analyze_contact_quality(self, contact: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze contact data quality"""
        issues = []
        
        # Check for missing required fields
        if not contact.get('email'):
            issues.append({
                'contact_id': contact.get('id'),
                'issue_type': 'missing_email',
                'severity': 'high',
                'description': 'Contact missing email address'
            })
        
        if not contact.get('firstname') and not contact.get('lastname'):
            issues.append({
                'contact_id': contact.get('id'),
                'issue_type': 'missing_name',
                'severity': 'medium',
                'description': 'Contact missing name information'
            })
        
        if not contact.get('company'):
            issues.append({
                'contact_id': contact.get('id'),
                'issue_type': 'missing_company',
                'severity': 'medium',
                'description': 'Contact missing company information'
            })
        
        # Check for stale data
        last_activity = contact.get('lastactivitydate')
        if last_activity:
            last_activity_date = datetime.fromisoformat(last_activity.replace('Z', '+00:00'))
            if (datetime.now() - last_activity_date.replace(tzinfo=None)).days > 90:
                issues.append({
                    'contact_id': contact.get('id'),
                    'issue_type': 'stale_data',
                    'severity': 'low',
                    'description': 'No activity in over 90 days'
                })
        
        return issues
    
    def _generate_cleanup_suggestions(self, quality_issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate cleanup suggestions based on quality issues"""
        suggestions = []
        
        # Group issues by type
        issue_counts = {}
        for issue in quality_issues:
            issue_type = issue['issue_type']
            issue_counts[issue_type] = issue_counts.get(issue_type, 0) + 1
        
        # Generate suggestions
        for issue_type, count in issue_counts.items():
            if issue_type == 'missing_email':
                suggestions.append({
                    'suggestion_type': 'data_enrichment',
                    'priority': 'high',
                    'description': f'Enrich {count} contacts with missing email addresses',
                    'action': 'Use data enrichment service or manual research'
                })
            
            elif issue_type == 'missing_company':
                suggestions.append({
                    'suggestion_type': 'data_completion',
                    'priority': 'medium',
                    'description': f'Complete company information for {count} contacts',
                    'action': 'Research and update company fields'
                })
            
            elif issue_type == 'stale_data':
                suggestions.append({
                    'suggestion_type': 'data_cleanup',
                    'priority': 'low',
                    'description': f'Review {count} contacts with stale data',
                    'action': 'Archive inactive contacts or re-engage'
                })
        
        return suggestions
    
    def _map_deal_stage_to_lifecycle(self, deal_stage: str) -> str:
        """Map deal stage to lifecycle stage"""
        mapping = {
            'appointmentscheduled': 'lead',
            'qualifiedtobuy': 'marketingqualifiedlead',
            'presentationscheduled': 'salesqualifiedlead',
            'decisionmakerboughtin': 'opportunity',
            'contractsent': 'opportunity',
            'closedwon': 'customer',
            'closedlost': 'other'
        }
        return mapping.get(deal_stage, 'lead')

# Example usage
if __name__ == "__main__":
    async def main():
        config = AgentConfig(
            agent_id="crm_sync_agent",
            agent_type="integration",
            specialization="crm_sync"
        )
        
        agent = CRMSyncAgent(config)
        await agent.start()
        
        # Keep running
        await asyncio.sleep(60)
        await agent.stop()
    
    asyncio.run(main())

