"""
Sophia AI - Call Analysis Agent
Specialized agent for analyzing sales calls and extracting business insights

This agent processes Gong.io call data to provide actionable insights for the sales team.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from ..core.base_agent import BaseAgent, AgentConfig, AgentCapability, Task, create_agent_response, validate_task_data
from ..integrations.gong.gong_integration import GongIntegration, GongConfig
from ..integrations.hubspot.hubspot_integration import HubSpotIntegration, HubSpotConfig
import openai

logger = logging.getLogger(__name__)

class CallAnalysisAgent(BaseAgent):
    """Specialized agent for analyzing sales calls and extracting insights"""
    
    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self.gong_integration = None
        self.hubspot_integration = None
        
    async def start(self):
        """Start the agent and initialize integrations"""
        await super().start()
        
        # Initialize integrations
        gong_config = GongConfig()
        self.gong_integration = GongIntegration(gong_config)
        
        hubspot_config = HubSpotConfig()
        self.hubspot_integration = HubSpotIntegration(hubspot_config)
        
        logger.info("Call Analysis Agent started with integrations")
    
    async def get_capabilities(self) -> List[AgentCapability]:
        return [
            AgentCapability(
                name="analyze_call",
                description="Analyze individual sales call for insights and recommendations",
                input_types=["call_id", "call_data"],
                output_types=["call_insights", "recommendations", "crm_updates"],
                estimated_duration=45.0
            ),
            AgentCapability(
                name="batch_call_analysis",
                description="Analyze multiple calls for trends and patterns",
                input_types=["call_list", "date_range"],
                output_types=["trend_analysis", "team_insights", "coaching_opportunities"],
                estimated_duration=120.0
            ),
            AgentCapability(
                name="call_to_crm_sync",
                description="Sync call insights to CRM system",
                input_types=["call_insights", "contact_id"],
                output_types=["crm_update_status", "follow_up_tasks"],
                estimated_duration=30.0
            ),
            AgentCapability(
                name="coaching_analysis",
                description="Identify coaching opportunities from call analysis",
                input_types=["call_data", "rep_id"],
                output_types=["coaching_recommendations", "skill_gaps", "improvement_plan"],
                estimated_duration=60.0
            )
        ]
    
    async def process_task(self, task: Task) -> Dict[str, Any]:
        """Process assigned task based on type"""
        try:
            task_type = task.task_type
            
            if task_type == "analyze_call":
                return await self._analyze_single_call(task)
            elif task_type == "batch_call_analysis":
                return await self._analyze_multiple_calls(task)
            elif task_type == "call_to_crm_sync":
                return await self._sync_call_to_crm(task)
            elif task_type == "coaching_analysis":
                return await self._analyze_for_coaching(task)
            else:
                raise ValueError(f"Unknown task type: {task_type}")
                
        except Exception as e:
            logger.error(f"Call Analysis Agent task failed: {str(e)}")
            return await create_agent_response(False, error=str(e))
    
    async def _analyze_single_call(self, task: Task) -> Dict[str, Any]:
        """Analyze a single call for insights"""
        try:
            # Validate required fields
            if not await validate_task_data(task, ['call_id']):
                raise ValueError("Missing required field: call_id")
            
            call_id = task.task_data['call_id']
            
            # Get call insights from Gong
            async with self.gong_integration:
                call_insights = await self.gong_integration.extract_call_insights(call_id)
            
            if not call_insights:
                raise ValueError(f"Could not retrieve insights for call {call_id}")
            
            # Enhance insights with business context
            enhanced_insights = await self._enhance_call_insights(call_insights)
            
            # Generate recommendations
            recommendations = await self._generate_call_recommendations(enhanced_insights)
            
            # Prepare CRM updates
            crm_updates = await self._prepare_crm_updates(enhanced_insights)
            
            result = {
                'call_id': call_id,
                'insights': enhanced_insights,
                'recommendations': recommendations,
                'crm_updates': crm_updates,
                'analysis_timestamp': datetime.now().isoformat(),
                'confidence_score': self._calculate_confidence_score(enhanced_insights)
            }
            
            # Store insights for future reference
            await self.store_business_context('call_analysis', call_id, result)
            
            return await create_agent_response(True, result)
            
        except Exception as e:
            return await create_agent_response(False, error=str(e))
    
    async def _analyze_multiple_calls(self, task: Task) -> Dict[str, Any]:
        """Analyze multiple calls for trends and patterns"""
        try:
            # Validate required fields
            if not await validate_task_data(task, ['date_range']):
                raise ValueError("Missing required field: date_range")
            
            date_range = task.task_data['date_range']
            from_date = datetime.fromisoformat(date_range['from'])
            to_date = datetime.fromisoformat(date_range['to'])
            
            # Get calls from Gong
            async with self.gong_integration:
                calls = await self.gong_integration.get_calls(from_date, to_date, limit=100)
            
            if not calls:
                return await create_agent_response(True, {'message': 'No calls found in date range'})
            
            # Analyze each call
            call_analyses = []
            for call in calls[:20]:  # Limit to 20 calls for performance
                call_id = call.get('id')
                if call_id:
                    async with self.gong_integration:
                        insights = await self.gong_integration.extract_call_insights(call_id)
                    if insights:
                        call_analyses.append(insights)
            
            # Generate trend analysis
            trend_analysis = await self._analyze_call_trends(call_analyses)
            
            # Identify team insights
            team_insights = await self._generate_team_insights(call_analyses)
            
            # Find coaching opportunities
            coaching_opportunities = await self._identify_coaching_opportunities(call_analyses)
            
            result = {
                'analysis_period': {
                    'from': from_date.isoformat(),
                    'to': to_date.isoformat()
                },
                'total_calls_analyzed': len(call_analyses),
                'trend_analysis': trend_analysis,
                'team_insights': team_insights,
                'coaching_opportunities': coaching_opportunities,
                'analysis_timestamp': datetime.now().isoformat()
            }
            
            return await create_agent_response(True, result)
            
        except Exception as e:
            return await create_agent_response(False, error=str(e))
    
    async def _sync_call_to_crm(self, task: Task) -> Dict[str, Any]:
        """Sync call insights to CRM system"""
        try:
            # Validate required fields
            if not await validate_task_data(task, ['call_insights', 'contact_email']):
                raise ValueError("Missing required fields: call_insights, contact_email")
            
            call_insights = task.task_data['call_insights']
            contact_email = task.task_data['contact_email']
            
            # Get or create contact in HubSpot
            async with self.hubspot_integration:
                contact = await self.hubspot_integration.get_contact(email=contact_email)
                
                if not contact:
                    # Create new contact
                    contact_data = {
                        'email': contact_email,
                        'firstname': call_insights.get('contact_name', '').split(' ')[0] if call_insights.get('contact_name') else '',
                        'lastname': ' '.join(call_insights.get('contact_name', '').split(' ')[1:]) if call_insights.get('contact_name') else '',
                        'company': call_insights.get('company_name', ''),
                        'lifecyclestage': 'lead'
                    }
                    contact = await self.hubspot_integration.create_contact(contact_data)
                
                if not contact:
                    raise ValueError("Failed to create or retrieve contact")
                
                contact_id = contact['id']
                
                # Create note with call insights
                note_content = self._format_call_note(call_insights)
                await self.hubspot_integration.create_note(contact_id, note_content)
                
                # Create follow-up tasks if needed
                follow_up_tasks = []
                if call_insights.get('next_steps'):
                    for next_step in call_insights['next_steps']:
                        task_result = await self.hubspot_integration.create_task(
                            contact_id,
                            f"Follow-up: {next_step}",
                            f"Based on call analysis: {next_step}",
                            datetime.now() + timedelta(days=1)
                        )
                        if task_result:
                            follow_up_tasks.append(task_result)
                
                # Update contact properties based on insights
                updates = {}
                if call_insights.get('deal_stage'):
                    updates['lifecyclestage'] = self._map_deal_stage_to_lifecycle(call_insights['deal_stage'])
                
                if call_insights.get('budget_indicators'):
                    updates['budget_confirmed'] = 'Yes'
                
                if updates:
                    await self.hubspot_integration.update_contact(contact_id, updates)
            
            result = {
                'contact_id': contact_id,
                'contact_email': contact_email,
                'note_created': True,
                'follow_up_tasks_created': len(follow_up_tasks),
                'contact_updated': bool(updates),
                'sync_timestamp': datetime.now().isoformat()
            }
            
            return await create_agent_response(True, result)
            
        except Exception as e:
            return await create_agent_response(False, error=str(e))
    
    async def _analyze_for_coaching(self, task: Task) -> Dict[str, Any]:
        """Analyze call for coaching opportunities"""
        try:
            # Validate required fields
            if not await validate_task_data(task, ['call_id', 'rep_email']):
                raise ValueError("Missing required fields: call_id, rep_email")
            
            call_id = task.task_data['call_id']
            rep_email = task.task_data['rep_email']
            
            # Get call insights
            async with self.gong_integration:
                call_insights = await self.gong_integration.extract_call_insights(call_id)
                sentiment_data = await self.gong_integration.analyze_call_sentiment(call_id)
            
            if not call_insights:
                raise ValueError(f"Could not retrieve insights for call {call_id}")
            
            # Analyze for coaching opportunities
            coaching_analysis = await self._perform_coaching_analysis(call_insights, sentiment_data)
            
            # Generate improvement plan
            improvement_plan = await self._generate_improvement_plan(coaching_analysis, rep_email)
            
            result = {
                'call_id': call_id,
                'rep_email': rep_email,
                'coaching_analysis': coaching_analysis,
                'improvement_plan': improvement_plan,
                'analysis_timestamp': datetime.now().isoformat()
            }
            
            return await create_agent_response(True, result)
            
        except Exception as e:
            return await create_agent_response(False, error=str(e))
    
    async def _enhance_call_insights(self, call_insights: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance call insights with additional business context"""
        try:
            enhanced = call_insights.copy()
            
            # Add business intelligence
            enhanced['business_intelligence'] = {
                'deal_priority': self._calculate_deal_priority(call_insights),
                'revenue_potential': self._estimate_revenue_potential(call_insights),
                'close_probability': self._estimate_close_probability(call_insights),
                'competitive_risk': self._assess_competitive_risk(call_insights),
                'urgency_score': self._calculate_urgency_score(call_insights)
            }
            
            # Add contextual recommendations
            enhanced['contextual_insights'] = {
                'industry_trends': await self._get_industry_context(call_insights),
                'similar_deals': await self._find_similar_deals(call_insights),
                'best_practices': await self._get_best_practices(call_insights)
            }
            
            return enhanced
            
        except Exception as e:
            logger.error(f"Failed to enhance call insights: {str(e)}")
            return call_insights
    
    async def _generate_call_recommendations(self, insights: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate actionable recommendations based on call insights"""
        recommendations = []
        
        try:
            # Analyze pain points for recommendations
            if insights.get('pain_points'):
                for pain_point in insights['pain_points']:
                    recommendations.append({
                        'type': 'solution_positioning',
                        'priority': 'high',
                        'action': f"Position solution to address: {pain_point}",
                        'rationale': 'Direct pain point mentioned by prospect'
                    })
            
            # Analyze objections for recommendations
            if insights.get('objections'):
                for objection in insights['objections']:
                    recommendations.append({
                        'type': 'objection_handling',
                        'priority': 'medium',
                        'action': f"Prepare response to objection: {objection}",
                        'rationale': 'Objection raised during call'
                    })
            
            # Analyze next steps
            if insights.get('next_steps'):
                for next_step in insights['next_steps']:
                    recommendations.append({
                        'type': 'follow_up',
                        'priority': 'high',
                        'action': next_step,
                        'rationale': 'Agreed next step from call'
                    })
            
            # Business intelligence recommendations
            bi = insights.get('business_intelligence', {})
            if bi.get('close_probability', 0) > 70:
                recommendations.append({
                    'type': 'acceleration',
                    'priority': 'high',
                    'action': 'Fast-track this opportunity - high close probability',
                    'rationale': f"Close probability: {bi['close_probability']}%"
                })
            
            if bi.get('competitive_risk', 'low') == 'high':
                recommendations.append({
                    'type': 'competitive_defense',
                    'priority': 'urgent',
                    'action': 'Implement competitive defense strategy',
                    'rationale': 'High competitive risk detected'
                })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Failed to generate recommendations: {str(e)}")
            return []
    
    async def _prepare_crm_updates(self, insights: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare CRM updates based on call insights"""
        try:
            updates = {
                'contact_updates': {},
                'deal_updates': {},
                'tasks_to_create': [],
                'notes_to_add': []
            }
            
            # Contact updates
            if insights.get('decision_makers'):
                updates['contact_updates']['decision_maker'] = 'Yes'
            
            if insights.get('budget_indicators'):
                updates['contact_updates']['budget_confirmed'] = 'Yes'
            
            # Deal updates
            if insights.get('deal_stage'):
                updates['deal_updates']['dealstage'] = insights['deal_stage']
            
            if insights.get('success_probability'):
                updates['deal_updates']['probability'] = insights['success_probability']
            
            # Tasks to create
            if insights.get('next_steps'):
                for next_step in insights['next_steps']:
                    updates['tasks_to_create'].append({
                        'title': f"Follow-up: {next_step}",
                        'description': f"Based on call analysis: {next_step}",
                        'due_date': (datetime.now() + timedelta(days=1)).isoformat()
                    })
            
            # Notes to add
            note_content = self._format_call_note(insights)
            updates['notes_to_add'].append({
                'content': note_content,
                'type': 'CALL'
            })
            
            return updates
            
        except Exception as e:
            logger.error(f"Failed to prepare CRM updates: {str(e)}")
            return {}
    
    def _format_call_note(self, insights: Dict[str, Any]) -> str:
        """Format call insights as CRM note"""
        note_parts = [
            f"Call Analysis - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        ]
        
        if insights.get('key_topics'):
            note_parts.append(f"Key Topics: {', '.join(insights['key_topics'])}")
        
        if insights.get('pain_points'):
            note_parts.append(f"Pain Points: {', '.join(insights['pain_points'])}")
        
        if insights.get('next_steps'):
            note_parts.append(f"Next Steps: {', '.join(insights['next_steps'])}")
        
        if insights.get('success_probability'):
            note_parts.append(f"Success Probability: {insights['success_probability']}%")
        
        return "\n".join(note_parts)
    
    def _calculate_deal_priority(self, insights: Dict[str, Any]) -> str:
        """Calculate deal priority based on insights"""
        score = 0
        
        # High-value indicators
        if insights.get('budget_indicators'):
            score += 30
        
        if insights.get('decision_makers'):
            score += 25
        
        if insights.get('urgency_level') == 'high':
            score += 20
        
        if insights.get('success_probability', 0) > 70:
            score += 25
        
        if score >= 70:
            return 'high'
        elif score >= 40:
            return 'medium'
        else:
            return 'low'
    
    def _estimate_revenue_potential(self, insights: Dict[str, Any]) -> int:
        """Estimate revenue potential from call insights"""
        # This would integrate with actual pricing models
        base_value = 50000  # Default base value
        
        # Adjust based on company size indicators
        if 'enterprise' in str(insights.get('key_topics', [])).lower():
            base_value *= 2
        
        # Adjust based on urgency
        if insights.get('urgency_level') == 'high':
            base_value *= 1.5
        
        return int(base_value)
    
    def _estimate_close_probability(self, insights: Dict[str, Any]) -> int:
        """Estimate close probability based on insights"""
        probability = insights.get('success_probability', 50)
        
        # Adjust based on additional factors
        if insights.get('budget_indicators'):
            probability += 15
        
        if insights.get('decision_makers'):
            probability += 10
        
        if insights.get('competitor_mentions'):
            probability -= 10
        
        return max(0, min(100, probability))
    
    def _assess_competitive_risk(self, insights: Dict[str, Any]) -> str:
        """Assess competitive risk level"""
        if insights.get('competitor_mentions'):
            return 'high'
        elif insights.get('objections'):
            return 'medium'
        else:
            return 'low'
    
    def _calculate_urgency_score(self, insights: Dict[str, Any]) -> int:
        """Calculate urgency score (0-100)"""
        score = 50  # Base score
        
        if insights.get('urgency_level') == 'high':
            score += 30
        elif insights.get('urgency_level') == 'medium':
            score += 15
        
        # Check for time-sensitive keywords in next steps
        next_steps = str(insights.get('next_steps', [])).lower()
        if any(word in next_steps for word in ['urgent', 'asap', 'immediately', 'this week']):
            score += 20
        
        return min(100, score)
    
    def _calculate_confidence_score(self, insights: Dict[str, Any]) -> float:
        """Calculate confidence score for the analysis"""
        score = 0.5  # Base confidence
        
        # Increase confidence based on data quality
        if insights.get('key_topics'):
            score += 0.1
        
        if insights.get('pain_points'):
            score += 0.1
        
        if insights.get('next_steps'):
            score += 0.2
        
        if insights.get('success_probability'):
            score += 0.1
        
        return min(1.0, score)
    
    async def _analyze_call_trends(self, call_analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze trends across multiple calls"""
        if not call_analyses:
            return {}
        
        trends = {
            'common_pain_points': {},
            'common_objections': {},
            'success_patterns': {},
            'average_success_probability': 0,
            'deal_stage_distribution': {},
            'urgency_trends': {}
        }
        
        total_probability = 0
        
        for analysis in call_analyses:
            # Track pain points
            for pain_point in analysis.get('pain_points', []):
                trends['common_pain_points'][pain_point] = trends['common_pain_points'].get(pain_point, 0) + 1
            
            # Track objections
            for objection in analysis.get('objections', []):
                trends['common_objections'][objection] = trends['common_objections'].get(objection, 0) + 1
            
            # Track success probability
            prob = analysis.get('success_probability', 0)
            total_probability += prob
            
            # Track deal stages
            stage = analysis.get('deal_stage', 'unknown')
            trends['deal_stage_distribution'][stage] = trends['deal_stage_distribution'].get(stage, 0) + 1
            
            # Track urgency
            urgency = analysis.get('urgency_level', 'medium')
            trends['urgency_trends'][urgency] = trends['urgency_trends'].get(urgency, 0) + 1
        
        trends['average_success_probability'] = total_probability / len(call_analyses)
        
        return trends
    
    async def _generate_team_insights(self, call_analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate team-level insights from call analyses"""
        insights = {
            'team_performance': {
                'average_call_quality': 0,
                'common_strengths': [],
                'improvement_areas': []
            },
            'market_insights': {
                'trending_topics': [],
                'emerging_pain_points': [],
                'competitive_landscape': []
            },
            'process_insights': {
                'effective_strategies': [],
                'process_gaps': []
            }
        }
        
        # This would be enhanced with actual team performance data
        insights['team_performance']['average_call_quality'] = 7.5
        insights['team_performance']['common_strengths'] = ['Discovery questions', 'Product knowledge']
        insights['team_performance']['improvement_areas'] = ['Objection handling', 'Closing techniques']
        
        return insights
    
    async def _identify_coaching_opportunities(self, call_analyses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify coaching opportunities from call analyses"""
        opportunities = []
        
        # This would analyze patterns across calls to identify coaching needs
        opportunities.append({
            'area': 'Discovery Questions',
            'frequency': 'High',
            'description': 'Reps need to ask more qualifying questions',
            'recommended_training': 'Discovery methodology workshop'
        })
        
        opportunities.append({
            'area': 'Objection Handling',
            'frequency': 'Medium',
            'description': 'Common objections not being addressed effectively',
            'recommended_training': 'Objection handling role-play sessions'
        })
        
        return opportunities
    
    async def _perform_coaching_analysis(self, call_insights: Dict[str, Any], sentiment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform detailed coaching analysis"""
        analysis = {
            'strengths': [],
            'improvement_areas': [],
            'specific_feedback': [],
            'skill_gaps': []
        }
        
        # Analyze talk ratio
        talk_ratio = sentiment_data.get('talk_ratio', 0.5)
        if talk_ratio > 0.7:
            analysis['improvement_areas'].append('Listening skills')
            analysis['specific_feedback'].append('Rep talked too much - focus on asking questions and listening')
        
        # Analyze questions asked
        questions_asked = sentiment_data.get('questions_asked', 0)
        if questions_asked < 5:
            analysis['improvement_areas'].append('Discovery questioning')
            analysis['specific_feedback'].append('Need to ask more discovery questions to understand prospect needs')
        
        # Analyze engagement
        engagement = sentiment_data.get('engagement_score', 0)
        if engagement > 0.7:
            analysis['strengths'].append('Customer engagement')
        else:
            analysis['improvement_areas'].append('Engagement techniques')
        
        return analysis
    
    async def _generate_improvement_plan(self, coaching_analysis: Dict[str, Any], rep_email: str) -> Dict[str, Any]:
        """Generate personalized improvement plan"""
        plan = {
            'rep_email': rep_email,
            'focus_areas': coaching_analysis.get('improvement_areas', []),
            'action_items': [],
            'training_recommendations': [],
            'follow_up_schedule': []
        }
        
        # Generate action items based on improvement areas
        for area in coaching_analysis.get('improvement_areas', []):
            if area == 'Discovery questioning':
                plan['action_items'].append('Practice 10 discovery questions before next call')
                plan['training_recommendations'].append('Discovery methodology training')
            elif area == 'Listening skills':
                plan['action_items'].append('Aim for 60/40 prospect/rep talk ratio in next calls')
                plan['training_recommendations'].append('Active listening workshop')
        
        return plan
    
    # Helper methods for business context
    async def _get_industry_context(self, insights: Dict[str, Any]) -> List[str]:
        """Get relevant industry context"""
        # This would integrate with industry databases
        return ['Industry trend: Increased focus on automation', 'Market condition: High demand for efficiency tools']
    
    async def _find_similar_deals(self, insights: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find similar deals for context"""
        # This would query CRM for similar deals
        return [{'deal_id': 'example', 'similarity_score': 0.85, 'outcome': 'won'}]
    
    async def _get_best_practices(self, insights: Dict[str, Any]) -> List[str]:
        """Get relevant best practices"""
        return ['Follow up within 24 hours', 'Send relevant case studies', 'Schedule technical demo']
    
    def _map_deal_stage_to_lifecycle(self, deal_stage: str) -> str:
        """Map deal stage to HubSpot lifecycle stage"""
        mapping = {
            'discovery': 'lead',
            'demo': 'marketingqualifiedlead',
            'proposal': 'salesqualifiedlead',
            'negotiation': 'opportunity',
            'closed': 'customer'
        }
        return mapping.get(deal_stage.lower(), 'lead')

# Example usage
if __name__ == "__main__":
    async def main():
        config = AgentConfig(
            agent_id="call_analysis_agent",
            agent_type="analysis",
            specialization="call_analysis"
        )
        
        agent = CallAnalysisAgent(config)
        await agent.start()
        
        # Keep running
        await asyncio.sleep(60)
        await agent.stop()
    
    asyncio.run(main())

