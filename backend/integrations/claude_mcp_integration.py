#!/usr/bin/env python3
"""
Claude MCP Integration for Pay Ready Sophia AI Ecosystem
Integrates Claude Max with GitHub, knowledge base, and multi-source data analysis
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
import anthropic
from dataclasses import dataclass
import requests
import base64

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ClaudeCredentials:
    """Claude API credentials and configuration"""
    api_key: str
    model: str = "claude-3-5-sonnet-20241022"
    max_tokens: int = 4096

@dataclass
class GitHubCredentials:
    """GitHub integration credentials"""
    token: Optional[str] = None
    username: str = "payready"  # Assuming based on context
    repo_name: str = "sophia-main"

class ClaudeMCPServer:
    """Claude MCP Server for Pay Ready's AI ecosystem integration"""
    
    def __init__(self, claude_creds: ClaudeCredentials, github_creds: GitHubCredentials):
        self.claude_client = anthropic.Anthropic(api_key=claude_creds.api_key)
        self.claude_creds = claude_creds
        self.github_creds = github_creds
        self.knowledge_base = {}
        self.conversation_history = []
        
    async def initialize_knowledge_base(self):
        """Initialize knowledge base with existing Sophia documentation"""
        knowledge_files = [
            "/home/ubuntu/sophia_natural_language_ai_control_system_documentation.md",
            "/home/ubuntu/natural_language_agent_control_architecture.md",
            "/home/ubuntu/sophia_deployment_status.md",
            "/home/ubuntu/comprehensive_integration_strategy.md",
            "/home/ubuntu/multi_source_data_architecture_recommendation.md"
        ]
        
        for file_path in knowledge_files:
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                    self.knowledge_base[os.path.basename(file_path)] = {
                        'content': content,
                        'last_updated': datetime.now().isoformat(),
                        'file_path': file_path,
                        'type': 'documentation'
                    }
                logger.info(f"Loaded knowledge base file: {file_path}")
            except FileNotFoundError:
                logger.warning(f"Knowledge base file not found: {file_path}")
    
    async def analyze_codebase_with_claude(self, analysis_type: str = "comprehensive") -> Dict[str, Any]:
        """Use Claude to analyze the current Sophia codebase"""
        
        # Read key files for analysis
        codebase_files = [
            "/home/ubuntu/sophia-main/backend/main.py",
            "/home/ubuntu/sophia-main/backend/agents/core/orchestrator.py",
            "/home/ubuntu/sophia-main/backend/integrations/kong_ai_gateway.py",
            "/home/ubuntu/sophia-main/backend/integrations/natural_language_processor.py",
            "/home/ubuntu/sophia-main/backend/mcp/sophia_mcp_server.py"
        ]
        
        codebase_content = {}
        for file_path in codebase_files:
            try:
                with open(file_path, 'r') as f:
                    codebase_content[file_path] = f.read()
            except FileNotFoundError:
                logger.warning(f"Codebase file not found: {file_path}")
        
        # Create comprehensive analysis prompt
        analysis_prompt = f"""
        As an expert software architect, analyze the Pay Ready Sophia AI codebase for the following:

        **ANALYSIS TYPE: {analysis_type.upper()}**

        **CODEBASE FILES:**
        {json.dumps(list(codebase_content.keys()), indent=2)}

        **KEY REQUIREMENTS:**
        1. **Multi-Source Data Integration**: Gong, Salesforce, HubSpot, Slack, Internal SQL
        2. **Natural Language Interface**: Conversational AI for business intelligence
        3. **Apartment Industry Focus**: Property management, rental industry insights
        4. **Scalable Architecture**: Microservices, API gateway, vector databases
        5. **MCP Integration**: Model Context Protocol for agent communication

        **CURRENT ARCHITECTURE COMPONENTS:**
        - Kong AI Gateway for API management
        - PostgreSQL + Redis + Pinecone + Weaviate for data storage
        - Natural Language Processor for intent recognition
        - Agent Orchestrator for task coordination
        - Lambda Labs production deployment

        **ANALYSIS FOCUS AREAS:**
        1. **Architecture Conflicts & Dependencies**
        2. **Code Quality & Refactoring Opportunities**
        3. **Integration Optimization**
        4. **Database Schema Alignment**
        5. **MCP Server Enhancement**
        6. **Performance Bottlenecks**
        7. **Security & Compliance**
        8. **Scalability Improvements**

        Please provide:
        1. **Critical Issues** requiring immediate attention
        2. **Optimization Opportunities** for performance and maintainability
        3. **Integration Recommendations** for multi-source data
        4. **MCP Strategy** for agent communication
        5. **Next Steps** prioritized by business impact

        **APARTMENT INDUSTRY CONTEXT:**
        Pay Ready sells AI technology TO apartment owners/managers. Focus on:
        - Sales intelligence and conversation analysis
        - Client health monitoring and churn prediction
        - Market intelligence for apartment industry
        - Compliance monitoring (Fair Housing, FDCPA)
        """
        
        try:
            response = await self._call_claude(analysis_prompt, codebase_content)
            
            analysis_result = {
                'analysis_type': analysis_type,
                'timestamp': datetime.now().isoformat(),
                'claude_response': response,
                'files_analyzed': list(codebase_content.keys()),
                'recommendations': self._extract_recommendations(response)
            }
            
            # Save analysis to file
            analysis_file = f"/home/ubuntu/claude_codebase_analysis_{analysis_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(analysis_file, 'w') as f:
                json.dump(analysis_result, f, indent=2)
            
            logger.info(f"Claude analysis completed and saved to: {analysis_file}")
            return analysis_result
            
        except Exception as e:
            logger.error(f"Claude analysis failed: {e}")
            return {'error': str(e)}
    
    async def interactive_data_dictionary_session(self, user_input: str) -> Dict[str, Any]:
        """Interactive session for building data dictionary with user collaboration"""
        
        # Load existing data dictionary
        try:
            with open("/home/ubuntu/data_dictionary.json", 'r') as f:
                existing_dict = json.load(f)
        except FileNotFoundError:
            existing_dict = {}
        
        # Create context-aware prompt for data dictionary building
        dictionary_prompt = f"""
        You are helping build a comprehensive data dictionary for Pay Ready's multi-source business intelligence platform.

        **CURRENT DATA SOURCES:**
        1. **Gong.io**: 13,069 calls, conversation intelligence, sales performance
        2. **Salesforce**: CRM data, deals, contacts, opportunities
        3. **HubSpot**: Marketing automation, lead generation, email campaigns
        4. **Slack**: Internal communications, team collaboration
        5. **Internal SQL**: Existing business data, customer information

        **EXISTING DATA DICTIONARY:**
        {json.dumps(existing_dict, indent=2) if existing_dict else "No existing dictionary"}

        **USER INPUT:**
        "{user_input}"

        **APARTMENT INDUSTRY CONTEXT:**
        Pay Ready sells AI technology to apartment owners and property managers. Key business entities:
        - Property Management Companies (clients)
        - Apartment Portfolios (client assets)
        - Rental Properties (client inventory)
        - Residents/Tenants (client customers)
        - Property Managers (client users)
        - Maintenance Requests (client operations)
        - Rent Collection (client revenue)
        - Compliance Requirements (Fair Housing, FDCPA)

        **TASK:**
        Based on the user input, help define or refine data dictionary fields. Consider:
        1. **Field Standardization** across all data sources
        2. **Business Context** for apartment industry
        3. **Data Types** and validation rules
        4. **Relationships** between entities
        5. **Compliance Requirements** for data handling

        Provide:
        1. **Suggested Field Definitions** with descriptions
        2. **Data Type Recommendations** (VARCHAR, INTEGER, DECIMAL, etc.)
        3. **Business Rules** for validation
        4. **Source System Mappings** (how each platform names this field)
        5. **Questions for Clarification** if needed

        Format as JSON with clear structure for easy integration.
        """
        
        try:
            response = await self._call_claude(dictionary_prompt)
            
            # Parse Claude's response and structure it
            dictionary_update = {
                'user_input': user_input,
                'timestamp': datetime.now().isoformat(),
                'claude_suggestions': response,
                'status': 'pending_user_approval'
            }
            
            # Save session for review
            session_file = f"/home/ubuntu/data_dictionary_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(session_file, 'w') as f:
                json.dump(dictionary_update, f, indent=2)
            
            return dictionary_update
            
        except Exception as e:
            logger.error(f"Data dictionary session failed: {e}")
            return {'error': str(e)}
    
    async def github_integration_analysis(self) -> Dict[str, Any]:
        """Analyze GitHub integration opportunities with Claude Max account"""
        
        github_prompt = """
        Analyze the optimal GitHub integration strategy for Pay Ready's Sophia AI ecosystem:

        **CURRENT SETUP:**
        - Claude Max account connected to GitHub
        - Sophia AI codebase in production
        - Multi-source data integration in progress
        - Natural language interface for business intelligence

        **INTEGRATION OPPORTUNITIES:**
        1. **Automated Code Review**: Claude analyzing pull requests for quality
        2. **Documentation Generation**: Auto-updating docs from code changes
        3. **Issue Analysis**: Claude helping prioritize and categorize GitHub issues
        4. **Deployment Automation**: Claude-assisted CI/CD pipeline optimization
        5. **Code Quality Monitoring**: Continuous analysis of code health

        **APARTMENT INDUSTRY FOCUS:**
        - Compliance code reviews (Fair Housing, FDCPA)
        - API integration quality for property management platforms
        - Data security and privacy compliance
        - Performance optimization for large-scale apartment data

        Provide specific recommendations for:
        1. **GitHub Actions** integration with Claude
        2. **Code Review Automation** workflows
        3. **Documentation Strategy** for multi-source integrations
        4. **Quality Assurance** processes
        5. **Deployment Pipeline** enhancements
        """
        
        try:
            response = await self._call_claude(github_prompt)
            
            github_analysis = {
                'analysis_type': 'github_integration',
                'timestamp': datetime.now().isoformat(),
                'claude_recommendations': response,
                'integration_opportunities': self._extract_github_opportunities(response)
            }
            
            # Save analysis
            analysis_file = f"/home/ubuntu/github_integration_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(analysis_file, 'w') as f:
                json.dump(github_analysis, f, indent=2)
            
            return github_analysis
            
        except Exception as e:
            logger.error(f"GitHub integration analysis failed: {e}")
            return {'error': str(e)}
    
    async def knowledge_base_integration_strategy(self) -> Dict[str, Any]:
        """Determine optimal knowledge base integration with existing Sophia system"""
        
        kb_prompt = f"""
        Design the optimal knowledge base integration strategy for Pay Ready's Sophia AI ecosystem:

        **CURRENT KNOWLEDGE BASE FILES:**
        {json.dumps(list(self.knowledge_base.keys()), indent=2)}

        **EXISTING INFRASTRUCTURE:**
        - PostgreSQL for relational data
        - Pinecone for vector embeddings
        - Weaviate for additional vector capabilities
        - Redis for caching
        - Natural language processor for intent recognition

        **INTEGRATION REQUIREMENTS:**
        1. **Multi-Source Knowledge**: Gong conversations, Salesforce data, HubSpot content, Slack messages
        2. **Semantic Search**: Natural language queries across all knowledge
        3. **Real-Time Updates**: Knowledge base updates as new data arrives
        4. **Contextual Retrieval**: Apartment industry-specific knowledge prioritization
        5. **Compliance Knowledge**: Fair Housing, FDCPA, payment processing regulations

        **BUSINESS CONTEXT:**
        Pay Ready needs to answer questions like:
        - "What are common objections from property managers about AI implementation?"
        - "How do we handle Fair Housing compliance in our AI communications?"
        - "What integration challenges do clients face with Yardi/RealPage?"
        - "Which sales techniques work best for large apartment portfolios?"

        Recommend:
        1. **Knowledge Base Architecture** (vector DB strategy, indexing)
        2. **Data Ingestion Pipeline** (how to process multi-source content)
        3. **Retrieval Strategy** (semantic search, ranking, filtering)
        4. **Update Mechanisms** (real-time vs batch processing)
        5. **Integration Points** with existing Sophia components
        """
        
        try:
            response = await self._call_claude(kb_prompt)
            
            kb_strategy = {
                'strategy_type': 'knowledge_base_integration',
                'timestamp': datetime.now().isoformat(),
                'claude_recommendations': response,
                'current_kb_files': list(self.knowledge_base.keys()),
                'integration_plan': self._extract_kb_plan(response)
            }
            
            # Save strategy
            strategy_file = f"/home/ubuntu/knowledge_base_integration_strategy_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(strategy_file, 'w') as f:
                json.dump(kb_strategy, f, indent=2)
            
            return kb_strategy
            
        except Exception as e:
            logger.error(f"Knowledge base strategy failed: {e}")
            return {'error': str(e)}
    
    async def _call_claude(self, prompt: str, context_data: Optional[Dict] = None) -> str:
        """Make API call to Claude with proper context"""
        
        # Prepare context if provided
        context_str = ""
        if context_data:
            context_str = f"\n\n**CONTEXT DATA:**\n{json.dumps(context_data, indent=2)}"
        
        full_prompt = prompt + context_str
        
        try:
            message = self.claude_client.messages.create(
                model=self.claude_creds.model,
                max_tokens=self.claude_creds.max_tokens,
                messages=[
                    {
                        "role": "user",
                        "content": full_prompt
                    }
                ]
            )
            
            response_text = message.content[0].text
            
            # Store in conversation history
            self.conversation_history.append({
                'timestamp': datetime.now().isoformat(),
                'prompt': prompt[:200] + "..." if len(prompt) > 200 else prompt,
                'response_length': len(response_text),
                'model': self.claude_creds.model
            })
            
            return response_text
            
        except Exception as e:
            logger.error(f"Claude API call failed: {e}")
            raise
    
    def _extract_recommendations(self, claude_response: str) -> List[Dict[str, Any]]:
        """Extract structured recommendations from Claude's response"""
        # This would parse Claude's response and extract actionable recommendations
        # For now, return a placeholder structure
        return [
            {
                'category': 'architecture',
                'priority': 'high',
                'description': 'Extracted from Claude response',
                'action_items': []
            }
        ]
    
    def _extract_github_opportunities(self, claude_response: str) -> List[Dict[str, Any]]:
        """Extract GitHub integration opportunities from Claude's response"""
        return [
            {
                'opportunity': 'automated_code_review',
                'implementation': 'GitHub Actions + Claude API',
                'priority': 'medium'
            }
        ]
    
    def _extract_kb_plan(self, claude_response: str) -> Dict[str, Any]:
        """Extract knowledge base integration plan from Claude's response"""
        return {
            'architecture': 'hybrid_vector_relational',
            'primary_vector_db': 'pinecone',
            'update_frequency': 'real_time',
            'search_strategy': 'semantic_with_filters'
        }

async def setup_claude_mcp_integration():
    """Main function to set up Claude MCP integration for Pay Ready"""
    
    # Initialize Claude credentials
    claude_creds = ClaudeCredentials(
        api_key="***REMOVED***"
    )
    
    # Initialize GitHub credentials (token would need to be provided)
    github_creds = GitHubCredentials()
    
    # Create MCP server
    mcp_server = ClaudeMCPServer(claude_creds, github_creds)
    
    # Initialize knowledge base
    await mcp_server.initialize_knowledge_base()
    
    # Run comprehensive analysis
    logger.info("Starting comprehensive codebase analysis with Claude...")
    codebase_analysis = await mcp_server.analyze_codebase_with_claude("comprehensive")
    
    # Analyze GitHub integration opportunities
    logger.info("Analyzing GitHub integration opportunities...")
    github_analysis = await mcp_server.github_integration_analysis()
    
    # Design knowledge base integration strategy
    logger.info("Designing knowledge base integration strategy...")
    kb_strategy = await mcp_server.knowledge_base_integration_strategy()
    
    # Return comprehensive results
    return {
        'mcp_server': mcp_server,
        'codebase_analysis': codebase_analysis,
        'github_analysis': github_analysis,
        'knowledge_base_strategy': kb_strategy,
        'knowledge_base_files': len(mcp_server.knowledge_base)
    }

if __name__ == "__main__":
    result = asyncio.run(setup_claude_mcp_integration())
    print(f"Claude MCP integration setup complete: {len(result)} components initialized")

