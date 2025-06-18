"""
Enhanced Crew AI Orchestrator with MCP Integration
Enables AI agents to use MCP servers as tools
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI

from backend.mcp.mcp_client import MCPClient, MCPToolWrapper

logger = logging.getLogger(__name__)


class MCPCrewOrchestrator:
    """Orchestrates CrewAI agents with MCP tool integration"""
    
    def __init__(self, mcp_gateway_url: str = "http://localhost:8090", mcp_auth_token: Optional[str] = None):
        self.mcp_client = MCPClient(mcp_gateway_url, mcp_auth_token)
        self.llm = ChatOpenAI(model="gpt-4-turbo")
        self.agents = {}
        self.tools = {}
        
    async def initialize(self):
        """Initialize MCP connection and discover tools"""
        await self.mcp_client.connect()
        
        # Create tool wrappers for all discovered tools
        for tool_key in self.mcp_client.list_tools():
            server, tool = tool_key.split(".", 1)
            wrapper = MCPToolWrapper(self.mcp_client, server, tool)
            self.tools[tool_key] = wrapper.as_langchain_tool()
            
        logger.info(f"Initialized with {len(self.tools)} MCP tools")
        
    def create_data_analyst_agent(self) -> Agent:
        """Create an agent specialized in data analysis"""
        tools = [
            self.tools.get("snowflake.execute_query"),
            self.tools.get("snowflake.list_tables"),
            self.tools.get("snowflake.describe_table"),
            self.tools.get("snowflake.get_table_sample"),
            self.tools.get("pinecone.semantic_search"),
            self.tools.get("pinecone.upsert_vectors")
        ]
        
        # Filter out None tools
        tools = [t for t in tools if t is not None]
        
        agent = Agent(
            role="Senior Data Analyst",
            goal="Analyze business data to provide actionable insights for Pay Ready",
            backstory="""You are an expert data analyst with deep knowledge of 
            SQL, data warehousing, and business intelligence. You help Pay Ready 
            understand their revenue, customer behavior, and sales performance.""",
            tools=tools,
            llm=self.llm,
            verbose=True,
            allow_delegation=False
        )
        
        self.agents["data_analyst"] = agent
        return agent
        
    def create_sales_intelligence_agent(self) -> Agent:
        """Create an agent specialized in sales intelligence"""
        tools = [
            self.tools.get("gong.get_calls"),
            self.tools.get("gong.get_call_transcript"),
            self.tools.get("hubspot.get_contacts"),
            self.tools.get("hubspot.create_deal"),
            self.tools.get("snowflake.execute_query"),
            self.tools.get("pinecone.semantic_search")
        ]
        
        tools = [t for t in tools if t is not None]
        
        agent = Agent(
            role="Sales Intelligence Specialist",
            goal="Analyze sales calls and CRM data to improve sales performance",
            backstory="""You are a sales intelligence expert who analyzes call 
            recordings, CRM data, and customer interactions to identify opportunities 
            and coach the sales team.""",
            tools=tools,
            llm=self.llm,
            verbose=True,
            allow_delegation=True
        )
        
        self.agents["sales_intelligence"] = agent
        return agent
        
    def create_project_manager_agent(self) -> Agent:
        """Create an agent specialized in project management"""
        tools = [
            self.tools.get("asana.create_task"),
            self.tools.get("asana.get_project_tasks"),
            self.tools.get("asana.update_task_status"),
            self.tools.get("hubspot.get_contacts"),
            self.tools.get("slack.send_message")
        ]
        
        tools = [t for t in tools if t is not None]
        
        agent = Agent(
            role="Project Manager",
            goal="Coordinate tasks and ensure smooth project execution",
            backstory="""You are an experienced project manager who ensures 
            tasks are properly tracked, teams are coordinated, and projects 
            deliver value on time.""",
            tools=tools,
            llm=self.llm,
            verbose=True,
            allow_delegation=False
        )
        
        self.agents["project_manager"] = agent
        return agent
        
    def create_infrastructure_engineer_agent(self) -> Agent:
        """Create an agent specialized in infrastructure management"""
        tools = [
            self.tools.get("pulumi.preview_infrastructure_change"),
            self.tools.get("pulumi.apply_with_approval"),
            self.tools.get("pulumi.rollback_deployment"),
            self.tools.get("snowflake.execute_query")
        ]
        
        tools = [t for t in tools if t is not None]
        
        agent = Agent(
            role="Infrastructure Engineer",
            goal="Manage and optimize cloud infrastructure",
            backstory="""You are a DevOps expert who manages infrastructure 
            as code, ensures system reliability, and optimizes costs.""",
            tools=tools,
            llm=self.llm,
            verbose=True,
            allow_delegation=False
        )
        
        self.agents["infrastructure_engineer"] = agent
        return agent
        
    async def execute_revenue_analysis(self, time_period: str = "last_month") -> Dict[str, Any]:
        """Execute a comprehensive revenue analysis workflow"""
        # Create agents
        data_analyst = self.create_data_analyst_agent()
        sales_agent = self.create_sales_intelligence_agent()
        
        # Define tasks
        revenue_task = Task(
            description=f"""Analyze revenue data for {time_period}:
            1. Query total revenue by product/service
            2. Identify top customers by revenue
            3. Calculate month-over-month growth
            4. Find revenue trends and anomalies
            
            Provide a detailed report with visualizations.""",
            agent=data_analyst,
            expected_output="Revenue analysis report with key metrics and insights"
        )
        
        sales_performance_task = Task(
            description=f"""Analyze sales performance for {time_period}:
            1. Review call recordings for closed deals
            2. Identify successful sales patterns
            3. Find areas for improvement
            4. Correlate call quality with deal size
            
            Provide recommendations for sales team.""",
            agent=sales_agent,
            expected_output="Sales performance analysis with coaching recommendations"
        )
        
        synthesis_task = Task(
            description="""Synthesize the revenue and sales analysis:
            1. Combine insights from both analyses
            2. Identify key business opportunities
            3. Create action items for leadership
            4. Suggest process improvements
            
            Provide executive summary with recommendations.""",
            agent=data_analyst,
            expected_output="Executive summary with actionable recommendations",
            context=[revenue_task, sales_performance_task]
        )
        
        # Create and run crew
        crew = Crew(
            agents=[data_analyst, sales_agent],
            tasks=[revenue_task, sales_performance_task, synthesis_task],
            process=Process.sequential
        )
        
        result = crew.kickoff()
        
        return {
            "analysis": result,
            "timestamp": datetime.now().isoformat(),
            "time_period": time_period
        }
        
    async def execute_customer_health_check(self, customer_id: str) -> Dict[str, Any]:
        """Execute a customer health check workflow"""
        # Create agents
        data_analyst = self.create_data_analyst_agent()
        sales_agent = self.create_sales_intelligence_agent()
        project_manager = self.create_project_manager_agent()
        
        # Define tasks
        usage_analysis_task = Task(
            description=f"""Analyze customer {customer_id} usage patterns:
            1. Query product usage metrics
            2. Identify feature adoption
            3. Check engagement trends
            4. Compare to successful customers
            
            Provide usage health score and insights.""",
            agent=data_analyst,
            expected_output="Customer usage analysis with health score"
        )
        
        interaction_analysis_task = Task(
            description=f"""Review customer {customer_id} interactions:
            1. Analyze recent support tickets
            2. Review sales call recordings
            3. Check CRM notes and activities
            4. Identify satisfaction indicators
            
            Provide interaction quality assessment.""",
            agent=sales_agent,
            expected_output="Customer interaction analysis with satisfaction indicators"
        )
        
        action_plan_task = Task(
            description=f"""Create action plan for customer {customer_id}:
            1. Based on usage and interaction analysis
            2. Create specific tasks in Asana
            3. Assign to appropriate team members
            4. Set up follow-up reminders
            
            Provide action plan with created tasks.""",
            agent=project_manager,
            expected_output="Action plan with Asana tasks created",
            context=[usage_analysis_task, interaction_analysis_task]
        )
        
        # Create and run crew
        crew = Crew(
            agents=[data_analyst, sales_agent, project_manager],
            tasks=[usage_analysis_task, interaction_analysis_task, action_plan_task],
            process=Process.sequential
        )
        
        result = crew.kickoff()
        
        return {
            "health_check": result,
            "customer_id": customer_id,
            "timestamp": datetime.now().isoformat()
        }
        
    async def execute_infrastructure_optimization(self) -> Dict[str, Any]:
        """Execute infrastructure optimization workflow"""
        # Create agents
        infra_engineer = self.create_infrastructure_engineer_agent()
        data_analyst = self.create_data_analyst_agent()
        
        # Define tasks
        cost_analysis_task = Task(
            description="""Analyze current infrastructure costs:
            1. Query cloud resource usage
            2. Identify underutilized resources
            3. Find cost optimization opportunities
            4. Calculate potential savings
            
            Provide cost analysis report.""",
            agent=data_analyst,
            expected_output="Infrastructure cost analysis with savings opportunities"
        )
        
        optimization_task = Task(
            description="""Create infrastructure optimization plan:
            1. Based on cost analysis
            2. Preview infrastructure changes
            3. Ensure no service disruption
            4. Estimate implementation effort
            
            Provide optimization plan with preview.""",
            agent=infra_engineer,
            expected_output="Infrastructure optimization plan with change preview",
            context=[cost_analysis_task]
        )
        
        # Create and run crew
        crew = Crew(
            agents=[data_analyst, infra_engineer],
            tasks=[cost_analysis_task, optimization_task],
            process=Process.sequential
        )
        
        result = crew.kickoff()
        
        return {
            "optimization_plan": result,
            "timestamp": datetime.now().isoformat()
        }
        
    async def cleanup(self):
        """Cleanup resources"""
        await self.mcp_client.close()


# Example usage
async def main():
    """Example usage of MCP Crew Orchestrator"""
    orchestrator = MCPCrewOrchestrator()
    
    try:
        # Initialize
        await orchestrator.initialize()
        
        # Run revenue analysis
        logger.info("Starting revenue analysis...")
        revenue_result = await orchestrator.execute_revenue_analysis("last_quarter")
        logger.info(f"Revenue analysis complete: {revenue_result}")
        
        # Run customer health check
        logger.info("Starting customer health check...")
        health_result = await orchestrator.execute_customer_health_check("CUST-123")
        logger.info(f"Health check complete: {health_result}")
        
    finally:
        await orchestrator.cleanup()


if __name__ == "__main__":
    asyncio.run(main()) 