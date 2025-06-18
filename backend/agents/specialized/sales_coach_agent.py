import logging
import json
import asyncio
from typing import Dict, List, Any, Optional, Type, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import uuid
import os

from ..core.crew_orchestrator import CrewOrchestrator, SophiaAgentConfig, SophiaTaskConfig
from ..core.persistent_memory import VectorPersistentMemory
from ...mcp.resource_orchestrator import SophiaResourceOrchestrator

class SalesCoachAgent:
    """Specialized agent for sales coaching"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.crew_orchestrator = CrewOrchestrator()
        self.resource_orchestrator = SophiaResourceOrchestrator()
        self.initialized = False
        self.agent_id = f"sales_coach_{uuid.uuid4().hex[:8]}"
        self.memory = None
        
    async def initialize(self):
        """Initialize the sales coach agent"""
        if self.initialized:
            return
        
        try:
            # Initialize orchestrators
            await self.crew_orchestrator.initialize()
            await self.resource_orchestrator.initialize()
            
            # Initialize memory
            self.memory = VectorPersistentMemory(
                agent_id=self.agent_id,
                memory_type="summary",
                vector_db="pinecone",
                collection="sophia_sales_coach_memory"
            )
            await self.memory.initialize()
            
            self.initialized = True
            self.logger.info("Sales Coach Agent initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Sales Coach Agent: {e}")
            raise
    
    async def analyze_call(self, call_id: str, analysis_type: str = "coaching") -> Dict[str, Any]:
        """Analyze a Gong call recording"""
        if not self.initialized:
            await self.initialize()
        
        try:
            # Execute Gong call analysis tool
            analysis_result = await self.resource_orchestrator.execute_tool(
                "gong_call_analysis",
                {
                    "call_id": call_id,
                    "analysis_type": analysis_type,
                    "include_transcript": True
                }
            )
            
            # Check for errors
            if "error" in analysis_result:
                raise ValueError(f"Error analyzing call: {analysis_result['error']}")
            
            # Create agent for call analysis
            call_analyzer_config = SophiaAgentConfig(
                name="call_analyzer",
                role="Sales Call Analyzer",
                goal="Analyze sales calls to provide actionable coaching insights",
                backstory="You are an expert sales coach with years of experience analyzing sales calls. You have a deep understanding of sales methodologies, objection handling, and relationship building techniques.",
                memory=self.memory,
                tools=["gong_call_analysis", "gong_transcript_extraction"],
                llm_config={
                    "model": "gpt-4-turbo",
                    "temperature": 0.3
                }
            )
            
            await self.crew_orchestrator.create_agent(call_analyzer_config)
            
            # Create task for call analysis
            call_analysis_task_config = SophiaTaskConfig(
                description=f"Analyze the sales call with ID {call_id} and provide detailed coaching feedback. Focus on strengths, areas for improvement, and specific actionable recommendations.",
                expected_output="A comprehensive sales coaching report with specific examples from the call, actionable recommendations, and follow-up suggestions.",
                agent_name="call_analyzer",
                context=json.dumps(analysis_result),
                async_execution=True,
                tools=["gong_call_analysis", "gong_transcript_extraction"]
            )
            
            task = await self.crew_orchestrator.create_task(call_analysis_task_config)
            
            # Find task ID
            task_id = None
            for tid, t in self.crew_orchestrator.tasks.items():
                if t == task:
                    task_id = tid
                    break
            
            if not task_id:
                raise ValueError("Failed to get task ID")
            
            # Run task
            task_result = await self.crew_orchestrator.run_task(task_id)
            
            # Process result
            coaching_report = self._process_coaching_report(task_result["result"], analysis_result)
            
            # Save to memory
            await self.memory.add_user_message(f"Request to analyze call {call_id}")
            await self.memory.add_ai_message(f"Provided coaching analysis for call {call_id}")
            
            return coaching_report
            
        except Exception as e:
            self.logger.error(f"Error in sales call analysis: {e}")
            return {
                "error": str(e),
                "call_id": call_id
            }
    
    async def create_coaching_plan(self, rep_id: str, time_period: str = "last_30_days") -> Dict[str, Any]:
        """Create a coaching plan for a sales rep based on their recent calls"""
        if not self.initialized:
            await self.initialize()
        
        try:
            # Get recent calls for the rep
            # This would typically come from a CRM query, but we'll simulate it
            recent_calls = await self._get_recent_calls(rep_id, time_period)
            
            if not recent_calls:
                return {
                    "error": "No recent calls found for this rep",
                    "rep_id": rep_id
                }
            
            # Analyze each call
            call_analyses = []
            for call in recent_calls:
                analysis = await self.analyze_call(call["call_id"], "coaching")
                if "error" not in analysis:
                    call_analyses.append(analysis)
            
            if not call_analyses:
                return {
                    "error": "Failed to analyze any calls for this rep",
                    "rep_id": rep_id
                }
            
            # Create agent for coaching plan
            coach_config = SophiaAgentConfig(
                name="sales_coach",
                role="Sales Coach",
                goal="Create personalized coaching plans for sales representatives",
                backstory="You are an experienced sales coach who specializes in developing personalized coaching plans based on call analysis. You focus on identifying patterns, strengths, and areas for improvement across multiple calls.",
                memory=self.memory,
                tools=["crm_query"],
                llm_config={
                    "model": "gpt-4-turbo",
                    "temperature": 0.4
                }
            )
            
            await self.crew_orchestrator.create_agent(coach_config)
            
            # Create task for coaching plan
            coaching_plan_task_config = SophiaTaskConfig(
                description=f"Create a comprehensive coaching plan for sales rep {rep_id} based on the analysis of their recent calls. Focus on identifying patterns, prioritizing areas for improvement, and creating actionable development steps.",
                expected_output="A detailed coaching plan with specific goals, action items, training recommendations, and a timeline for improvement.",
                agent_name="sales_coach",
                context=json.dumps({
                    "rep_id": rep_id,
                    "time_period": time_period,
                    "call_analyses": call_analyses
                }),
                async_execution=True,
                tools=["crm_query"]
            )
            
            task = await self.crew_orchestrator.create_task(coaching_plan_task_config)
            
            # Find task ID
            task_id = None
            for tid, t in self.crew_orchestrator.tasks.items():
                if t == task:
                    task_id = tid
                    break
            
            if not task_id:
                raise ValueError("Failed to get task ID")
            
            # Run task
            task_result = await self.crew_orchestrator.run_task(task_id)
            
            # Process result
            coaching_plan = self._process_coaching_plan(task_result["result"], rep_id, call_analyses)
            
            # Save to memory
            await self.memory.add_user_message(f"Request to create coaching plan for rep {rep_id}")
            await self.memory.add_ai_message(f"Provided coaching plan for rep {rep_id}")
            
            return coaching_plan
            
        except Exception as e:
            self.logger.error(f"Error creating coaching plan: {e}")
            return {
                "error": str(e),
                "rep_id": rep_id
            }
    
    async def analyze_team_performance(self, team_id: str, time_period: str = "last_30_days") -> Dict[str, Any]:
        """Analyze team performance based on call data"""
        if not self.initialized:
            await self.initialize()
        
        try:
            # Get team members
            team_members = await self._get_team_members(team_id)
            
            if not team_members:
                return {
                    "error": "No team members found",
                    "team_id": team_id
                }
            
            # Create coaching plans for each team member
            coaching_plans = []
            for member in team_members:
                plan = await self.create_coaching_plan(member["rep_id"], time_period)
                if "error" not in plan:
                    coaching_plans.append(plan)
            
            if not coaching_plans:
                return {
                    "error": "Failed to create coaching plans for any team members",
                    "team_id": team_id
                }
            
            # Create agent for team analysis
            team_analyst_config = SophiaAgentConfig(
                name="team_analyst",
                role="Sales Team Performance Analyst",
                goal="Analyze team performance and identify trends and opportunities",
                backstory="You are a sales team performance analyst who specializes in identifying team-wide trends, comparing individual performance, and recommending team-level improvements.",
                memory=self.memory,
                tools=["crm_query"],
                llm_config={
                    "model": "gpt-4-turbo",
                    "temperature": 0.3
                }
            )
            
            await self.crew_orchestrator.create_agent(team_analyst_config)
            
            # Create task for team analysis
            team_analysis_task_config = SophiaTaskConfig(
                description=f"Analyze the performance of sales team {team_id} based on individual coaching plans. Identify team-wide trends, strengths, and areas for improvement. Compare individual performance and recommend team-level training and development opportunities.",
                expected_output="A comprehensive team performance analysis with specific recommendations for team-wide improvements, training programs, and individual development paths.",
                agent_name="team_analyst",
                context=json.dumps({
                    "team_id": team_id,
                    "time_period": time_period,
                    "team_members": team_members,
                    "coaching_plans": coaching_plans
                }),
                async_execution=True,
                tools=["crm_query"]
            )
            
            task = await self.crew_orchestrator.create_task(team_analysis_task_config)
            
            # Find task ID
            task_id = None
            for tid, t in self.crew_orchestrator.tasks.items():
                if t == task:
                    task_id = tid
                    break
            
            if not task_id:
                raise ValueError("Failed to get task ID")
            
            # Run task
            task_result = await self.crew_orchestrator.run_task(task_id)
            
            # Process result
            team_analysis = self._process_team_analysis(task_result["result"], team_id, team_members, coaching_plans)
            
            # Save to memory
            await self.memory.add_user_message(f"Request to analyze team performance for team {team_id}")
            await self.memory.add_ai_message(f"Provided team performance analysis for team {team_id}")
            
            return team_analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing team performance: {e}")
            return {
                "error": str(e),
                "team_id": team_id
            }
    
    async def generate_call_summary(self, call_id: str) -> Dict[str, Any]:
        """Generate a summary of a call for sharing with stakeholders"""
        if not self.initialized:
            await self.initialize()
        
        try:
            # Execute Gong call analysis tool
            analysis_result = await self.resource_orchestrator.execute_tool(
                "gong_call_analysis",
                {
                    "call_id": call_id,
                    "analysis_type": "detailed",
                    "include_transcript": True
                }
            )
            
            # Check for errors
            if "error" in analysis_result:
                raise ValueError(f"Error analyzing call: {analysis_result['error']}")
            
            # Create agent for call summary
            summarizer_config = SophiaAgentConfig(
                name="call_summarizer",
                role="Sales Call Summarizer",
                goal="Create concise, actionable summaries of sales calls",
                backstory="You are an expert at distilling complex sales conversations into clear, actionable summaries that highlight key points, next steps, and important customer information.",
                memory=self.memory,
                tools=["gong_transcript_extraction"],
                llm_config={
                    "model": "gpt-4-turbo",
                    "temperature": 0.3
                }
            )
            
            await self.crew_orchestrator.create_agent(summarizer_config)
            
            # Create task for call summary
            summary_task_config = SophiaTaskConfig(
                description=f"Create a concise, actionable summary of the sales call with ID {call_id}. Focus on key discussion points, customer needs, objections raised, commitments made, and clear next steps.",
                expected_output="A professional call summary suitable for sharing with stakeholders, including key points, action items, and follow-up timeline.",
                agent_name="call_summarizer",
                context=json.dumps(analysis_result),
                async_execution=True,
                tools=["gong_transcript_extraction"]
            )
            
            task = await self.crew_orchestrator.create_task(summary_task_config)
            
            # Find task ID
            task_id = None
            for tid, t in self.crew_orchestrator.tasks.items():
                if t == task:
                    task_id = tid
                    break
            
            if not task_id:
                raise ValueError("Failed to get task ID")
            
            # Run task
            task_result = await self.crew_orchestrator.run_task(task_id)
            
            # Process result
            call_summary = self._process_call_summary(task_result["result"], analysis_result)
            
            # Save to memory
            await self.memory.add_user_message(f"Request to summarize call {call_id}")
            await self.memory.add_ai_message(f"Provided summary for call {call_id}")
            
            return call_summary
            
        except Exception as e:
            self.logger.error(f"Error generating call summary: {e}")
            return {
                "error": str(e),
                "call_id": call_id
            }
    
    def _process_coaching_report(self, report: str, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """Process the coaching report from the agent"""
        # Extract metadata from analysis result
        metadata = analysis_result.get("metadata", {})
        
        # Create structured coaching report
        coaching_report = {
            "call_id": analysis_result.get("call_id"),
            "call_date": metadata.get("call_date"),
            "duration_seconds": metadata.get("duration_seconds"),
            "participants": metadata.get("participants", []),
            "coaching_report": report,
            "analysis_type": analysis_result.get("analysis_type"),
            "generated_at": datetime.now().isoformat()
        }
        
        return coaching_report
    
    def _process_coaching_plan(self, plan: str, rep_id: str, call_analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process the coaching plan from the agent"""
        # Create structured coaching plan
        coaching_plan = {
            "rep_id": rep_id,
            "call_count": len(call_analyses),
            "time_period": "last_30_days",  # This would come from the actual request
            "coaching_plan": plan,
            "generated_at": datetime.now().isoformat()
        }
        
        return coaching_plan
    
    def _process_team_analysis(self, analysis: str, team_id: str, team_members: List[Dict[str, Any]], coaching_plans: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process the team analysis from the agent"""
        # Create structured team analysis
        team_analysis = {
            "team_id": team_id,
            "member_count": len(team_members),
            "time_period": "last_30_days",  # This would come from the actual request
            "team_analysis": analysis,
            "generated_at": datetime.now().isoformat()
        }
        
        return team_analysis
    
    def _process_call_summary(self, summary: str, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """Process the call summary from the agent"""
        # Extract metadata from analysis result
        metadata = analysis_result.get("metadata", {})
        
        # Create structured call summary
        call_summary = {
            "call_id": analysis_result.get("call_id"),
            "call_date": metadata.get("call_date"),
            "duration_seconds": metadata.get("duration_seconds"),
            "participants": metadata.get("participants", []),
            "summary": summary,
            "generated_at": datetime.now().isoformat()
        }
        
        return call_summary
    
    async def _get_recent_calls(self, rep_id: str, time_period: str) -> List[Dict[str, Any]]:
        """Get recent calls for a sales rep"""
        # This would typically come from a CRM query or Gong API
        # For now, we'll return mock data
        return [
            {
                "call_id": f"call_{uuid.uuid4().hex[:8]}",
                "call_date": (datetime.now() - timedelta(days=i)).isoformat(),
                "duration_seconds": 1800 + (i * 100),
                "customer": f"Customer {i+1}"
            }
            for i in range(3)  # Mock 3 recent calls
        ]
    
    async def _get_team_members(self, team_id: str) -> List[Dict[str, Any]]:
        """Get members of a sales team"""
        # This would typically come from a CRM query
        # For now, we'll return mock data
        return [
            {
                "rep_id": f"rep_{uuid.uuid4().hex[:8]}",
                "name": f"Sales Rep {i+1}",
                "role": "Account Executive",
                "experience_years": 1 + i
            }
            for i in range(5)  # Mock 5 team members
        ]
