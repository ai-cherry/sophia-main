# Sophia AI Technical Architecture Design
## AI Assistant Orchestrator for Pay Ready

### Architecture Overview
Based on your strategic decisions, Sophia AI will implement a **flat-to-hierarchical evolution architecture** with **highly specialized agents**, focusing on **HubSpot + Gong.io + Slack integration** as the core business intelligence orchestrator.

---

## Core Architecture Principles

### **1. Flat Agent Network (Phase 1)**
```
                    ┌─────────────────┐
                    │   Sophia Core   │
                    │   Orchestrator  │
                    └─────────┬───────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
   ┌────▼────┐         ┌─────▼─────┐         ┌─────▼─────┐
   │ Call    │         │ CRM Sync  │         │ Slack     │
   │Analysis │         │ Agent     │         │Interface  │
   │ Agent   │         │           │         │ Agent     │
   └─────────┘         └───────────┘         └───────────┘
        │                     │                     │
   ┌────▼────┐         ┌─────▼─────┐         ┌─────▼─────┐
   │Follow-up│         │Lead Qual  │         │Notification│
   │ Agent   │         │ Agent     │         │ Agent     │
   └─────────┘         └───────────┘         └───────────┘
```

### **2. Hierarchical Evolution (Phase 4)**
```
                    ┌─────────────────┐
                    │   Sophia Core   │
                    │   Orchestrator  │
                    └─────────┬───────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
   ┌────▼────┐         ┌─────▼─────┐         ┌─────▼─────┐
   │ Sales   │         │Marketing  │         │Operations │
   │Supervisor│        │Supervisor │         │Supervisor │
   └────┬────┘         └─────┬─────┘         └─────┬─────┘
        │                    │                     │
    [Specialized]        [Specialized]         [Specialized]
    [Sales Agents]       [Marketing Agents]    [Ops Agents]
```

---

## Detailed Technical Architecture

### **1. Core Infrastructure Layer**

#### **1.1 Message Bus & Communication**
```python
# Redis-based pub/sub system for agent communication
class AgentMessageBus:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=6379,
            decode_responses=True
        )
        self.channels = {
            'agent_coordination': 'sophia:agents:coordination',
            'task_delegation': 'sophia:agents:tasks',
            'results_sharing': 'sophia:agents:results',
            'slack_interface': 'sophia:slack:messages',
            'crm_updates': 'sophia:crm:updates',
            'call_analysis': 'sophia:gong:analysis'
        }
    
    async def publish_task(self, agent_id: str, task: dict):
        """Publish task to specific agent"""
        channel = f"sophia:agent:{agent_id}:tasks"
        await self.redis_client.publish(channel, json.dumps(task))
    
    async def subscribe_to_results(self, callback):
        """Subscribe to agent results"""
        pubsub = self.redis_client.pubsub()
        await pubsub.subscribe(self.channels['results_sharing'])
        async for message in pubsub.listen():
            await callback(message)
```

#### **1.2 Agent Registry & Discovery**
```python
class AgentRegistry:
    def __init__(self):
        self.agents = {}
        self.capabilities = {}
        self.performance_metrics = {}
    
    def register_agent(self, agent_id: str, capabilities: list, 
                      endpoint: str, specialization: str):
        """Register new agent with capabilities"""
        self.agents[agent_id] = {
            'endpoint': endpoint,
            'capabilities': capabilities,
            'specialization': specialization,
            'status': 'active',
            'last_seen': datetime.now(),
            'performance_score': 1.0
        }
    
    def find_agent_for_task(self, task_type: str, context: dict = None):
        """Find best agent for specific task"""
        candidates = [
            agent_id for agent_id, agent in self.agents.items()
            if task_type in agent['capabilities'] and agent['status'] == 'active'
        ]
        
        # Sort by performance score and specialization match
        return sorted(candidates, 
                     key=lambda x: self.agents[x]['performance_score'], 
                     reverse=True)[0] if candidates else None
```

#### **1.3 Context Management**
```python
class ContextManager:
    def __init__(self):
        self.redis_client = redis.Redis(host=os.getenv('REDIS_HOST', 'localhost'), port=6379)
        self.postgres_client = self.get_postgres_connection()
    
    async def store_conversation_context(self, user_id: str, 
                                       conversation_id: str, context: dict):
        """Store conversation context for continuity"""
        key = f"sophia:context:{user_id}:{conversation_id}"
        await self.redis_client.setex(key, 3600, json.dumps(context))
    
    async def get_business_context(self, entity_type: str, entity_id: str):
        """Retrieve business context from CRM/databases"""
        if entity_type == 'contact':
            return await self.get_hubspot_contact_context(entity_id)
        elif entity_type == 'deal':
            return await self.get_hubspot_deal_context(entity_id)
        elif entity_type == 'call':
            return await self.get_gong_call_context(entity_id)
    
    async def update_learning_context(self, interaction_id: str, 
                                    outcome: dict, feedback: dict):
        """Update learning context based on outcomes"""
        learning_data = {
            'interaction_id': interaction_id,
            'outcome': outcome,
            'feedback': feedback,
            'timestamp': datetime.now().isoformat()
        }
        await self.store_in_postgres('learning_interactions', learning_data)
```

---

### **2. Specialized Agent Architecture**

#### **2.1 Call Analysis Agent (Gong.io Integration)**
```python
class CallAnalysisAgent:
    def __init__(self):
        self.gong_client = GongAPIClient()
        self.openai_client = OpenAI()
        self.agent_id = "call_analysis_agent"
        self.capabilities = [
            "call_transcription_analysis",
            "sentiment_analysis", 
            "key_insights_extraction",
            "next_steps_identification",
            "objection_detection"
        ]
    
    async def analyze_call(self, call_id: str):
        """Comprehensive call analysis"""
        # Get call data from Gong.io
        call_data = await self.gong_client.get_call_details(call_id)
        transcript = await self.gong_client.get_call_transcript(call_id)
        
        # AI-powered analysis
        analysis = await self.openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": self.get_analysis_prompt()},
                {"role": "user", "content": f"Transcript: {transcript}"}
            ]
        )
        
        # Extract structured insights
        insights = self.parse_analysis_results(analysis.choices[0].message.content)
        
        # Store results and trigger follow-up actions
        await self.store_call_insights(call_id, insights)
        await self.trigger_follow_up_actions(call_id, insights)
        
        return insights
    
    def get_analysis_prompt(self):
        return """
        Analyze this sales call transcript and provide:
        1. Overall sentiment (positive/neutral/negative)
        2. Key discussion points and topics covered
        3. Client objections or concerns raised
        4. Buying signals or interest indicators
        5. Recommended next steps
        6. Deal stage assessment
        7. Risk factors or red flags
        8. Coaching opportunities for the sales rep
        
        Format as structured JSON for easy processing.
        """
```

#### **2.2 CRM Sync Agent (HubSpot Integration)**
```python
class CRMSyncAgent:
    def __init__(self):
        self.hubspot_client = HubSpotAPIClient()
        self.salesforce_client = SalesforceAPIClient()  # For selective data
        self.agent_id = "crm_sync_agent"
        self.capabilities = [
            "contact_management",
            "deal_tracking",
            "activity_logging",
            "data_synchronization",
            "duplicate_detection"
        ]
    
    async def sync_call_insights_to_crm(self, call_id: str, insights: dict):
        """Sync call analysis results to HubSpot"""
        # Get associated contact/deal from call metadata
        call_metadata = await self.get_call_metadata(call_id)
        contact_id = call_metadata.get('hubspot_contact_id')
        deal_id = call_metadata.get('hubspot_deal_id')
        
        # Update contact with call insights
        if contact_id:
            await self.hubspot_client.update_contact(contact_id, {
                'last_call_sentiment': insights['sentiment'],
                'last_call_date': insights['call_date'],
                'last_call_summary': insights['summary']
            })
        
        # Update deal with progression insights
        if deal_id:
            await self.hubspot_client.update_deal(deal_id, {
                'deal_stage': insights['recommended_stage'],
                'next_steps': insights['next_steps'],
                'risk_factors': insights['risk_factors']
            })
        
        # Log activity
        await self.hubspot_client.create_activity({
            'type': 'call_analysis',
            'contact_id': contact_id,
            'deal_id': deal_id,
            'details': insights['summary'],
            'timestamp': insights['call_date']
        })
    
    async def get_selective_salesforce_data(self, criteria: dict):
        """Get specific data from Salesforce when needed"""
        # Only pull specific data types as needed
        if criteria['type'] == 'historical_deals':
            return await self.salesforce_client.query_historical_deals(criteria)
        elif criteria['type'] == 'contact_history':
            return await self.salesforce_client.get_contact_history(criteria)
```

#### **2.3 Slack Interface Agent**
```python
class SlackInterfaceAgent:
    def __init__(self):
        self.slack_client = SlackBoltApp()
        self.openai_client = OpenAI()
        self.agent_id = "slack_interface_agent"
        self.capabilities = [
            "natural_language_processing",
            "intent_recognition",
            "response_generation",
            "proactive_notifications",
            "command_processing"
        ]
    
    async def process_user_query(self, user_id: str, message: str, channel: str):
        """Process natural language query from Slack"""
        # Understand user intent
        intent = await self.recognize_intent(message)
        
        # Get relevant context
        context = await self.get_user_context(user_id)
        business_context = await self.get_relevant_business_context(intent, context)
        
        # Generate response
        response = await self.generate_response(intent, message, business_context)
        
        # Execute any required actions
        if intent['requires_action']:
            await self.execute_action(intent['action'], intent['parameters'])
        
        # Send response to Slack
        await self.slack_client.client.chat_postMessage(
            channel=channel,
            text=response['text'],
            blocks=response.get('blocks', [])
        )
    
    async def send_proactive_notification(self, notification_type: str, 
                                        data: dict, target_users: list):
        """Send proactive notifications to relevant team members"""
        message = await self.format_notification(notification_type, data)
        
        for user_id in target_users:
            channel = await self.get_user_dm_channel(user_id)
            await self.slack_client.client.chat_postMessage(
                channel=channel,
                text=message['text'],
                blocks=message.get('blocks', [])
            )
    
    def setup_slack_commands(self):
        """Setup Slack slash commands"""
        @self.slack_client.command("/sophia-deals")
        async def handle_deals_command(ack, command):
            await ack()
            deals = await self.get_deals_summary(command['text'])
            await self.send_deals_summary(command['channel_id'], deals)
        
        @self.slack_client.command("/sophia-calls")
        async def handle_calls_command(ack, command):
            await ack()
            calls = await self.get_recent_calls_analysis(command['text'])
            await self.send_calls_analysis(command['channel_id'], calls)
```

---

### **3. Integration Layer Architecture**

#### **3.1 HubSpot Integration**
```python
class HubSpotIntegration:
    def __init__(self):
        self.api_key = os.getenv('HUBSPOT_API_KEY')
        self.base_url = "https://api.hubapi.com"
        self.rate_limiter = RateLimiter(100, 10)  # 100 requests per 10 seconds
    
    async def get_contact_details(self, contact_id: str):
        """Get comprehensive contact information"""
        async with self.rate_limiter:
            response = await self.make_request(
                f"/crm/v3/objects/contacts/{contact_id}",
                params={
                    'properties': [
                        'firstname', 'lastname', 'email', 'phone',
                        'company', 'jobtitle', 'lifecyclestage',
                        'last_call_date', 'last_call_sentiment'
                    ]
                }
            )
            return response
    
    async def get_deal_pipeline(self, deal_stage: str = None):
        """Get deals in pipeline with optional stage filter"""
        params = {
            'properties': [
                'dealname', 'amount', 'dealstage', 'closedate',
                'pipeline', 'hubspot_owner_id'
            ]
        }
        if deal_stage:
            params['filters'] = [
                {'propertyName': 'dealstage', 'operator': 'EQ', 'value': deal_stage}
            ]
        
        async with self.rate_limiter:
            response = await self.make_request("/crm/v3/objects/deals/search", 
                                             method="POST", json=params)
            return response
    
    async def create_task(self, task_data: dict):
        """Create follow-up task in HubSpot"""
        async with self.rate_limiter:
            response = await self.make_request("/crm/v3/objects/tasks", 
                                             method="POST", json=task_data)
            return response
```

#### **3.2 Gong.io Integration**
```python
class GongIntegration:
    def __init__(self):
        self.api_key = os.getenv('GONG_API_KEY')
        self.base_url = "https://api.gong.io/v2"
        self.rate_limiter = RateLimiter(50, 60)  # 50 requests per minute
    
    async def get_recent_calls(self, days: int = 7):
        """Get recent calls for analysis"""
        from_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        async with self.rate_limiter:
            response = await self.make_request("/calls", params={
                'fromDateTime': from_date,
                'contentSelector': {
                    'exposedFields': {
                        'parties': True,
                        'content': True,
                        'context': True
                    }
                }
            })
            return response
    
    async def get_call_transcript(self, call_id: str):
        """Get call transcript for analysis"""
        async with self.rate_limiter:
            response = await self.make_request(f"/calls/{call_id}/transcript")
            return response
    
    async def get_call_analytics(self, call_id: str):
        """Get Gong's built-in analytics for a call"""
        async with self.rate_limiter:
            response = await self.make_request(f"/calls/{call_id}/analytics")
            return response
```

---

### **4. Data Architecture & Storage**

#### **4.1 Database Schema Design**
```sql
-- Core agent coordination tables
CREATE TABLE agent_registry (
    agent_id VARCHAR(50) PRIMARY KEY,
    agent_type VARCHAR(50) NOT NULL,
    capabilities JSONB NOT NULL,
    endpoint VARCHAR(255) NOT NULL,
    status VARCHAR(20) DEFAULT 'active',
    performance_score DECIMAL(3,2) DEFAULT 1.0,
    created_at TIMESTAMP DEFAULT NOW(),
    last_seen TIMESTAMP DEFAULT NOW()
);

CREATE TABLE agent_tasks (
    task_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id VARCHAR(50) REFERENCES agent_registry(agent_id),
    task_type VARCHAR(50) NOT NULL,
    task_data JSONB NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    result JSONB
);

-- Business intelligence tables
CREATE TABLE call_analysis (
    call_id VARCHAR(100) PRIMARY KEY,
    gong_call_id VARCHAR(100) UNIQUE,
    hubspot_contact_id VARCHAR(50),
    hubspot_deal_id VARCHAR(50),
    call_date TIMESTAMP NOT NULL,
    duration_minutes INTEGER,
    sentiment VARCHAR(20),
    key_insights JSONB,
    next_steps JSONB,
    risk_factors JSONB,
    coaching_notes JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE crm_sync_log (
    sync_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_system VARCHAR(50) NOT NULL,
    target_system VARCHAR(50) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id VARCHAR(100) NOT NULL,
    sync_type VARCHAR(20) NOT NULL, -- 'create', 'update', 'delete'
    sync_data JSONB,
    status VARCHAR(20) DEFAULT 'pending',
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);

-- Learning and optimization tables
CREATE TABLE interaction_history (
    interaction_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(50) NOT NULL,
    channel VARCHAR(50) NOT NULL, -- 'slack', 'admin_interface'
    query_text TEXT,
    intent VARCHAR(100),
    response_text TEXT,
    user_feedback INTEGER, -- 1-5 rating
    outcome_success BOOLEAN,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE business_context (
    context_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type VARCHAR(50) NOT NULL, -- 'contact', 'deal', 'company'
    entity_id VARCHAR(100) NOT NULL,
    context_data JSONB NOT NULL,
    last_updated TIMESTAMP DEFAULT NOW(),
    UNIQUE(entity_type, entity_id)
);
```

#### **4.2 Vector Database Configuration**
```python
class VectorDatabaseManager:
    def __init__(self):
        self.pinecone_client = self.setup_pinecone()
        self.weaviate_client = self.setup_weaviate()
        
    def setup_pinecone(self):
        """Configure Pinecone for business intelligence search"""
        pinecone.init(
            api_key=os.getenv("PINECONE_API_KEY"),
            environment=os.getenv("PINECONE_ENVIRONMENT", "us-west1-gcp")
        )
        
        # Create indexes for different data types
        indexes = {
            'call-insights': {
                'dimension': 1536,  # OpenAI embedding dimension
                'metric': 'cosine',
                'metadata_config': {
                    'indexed': ['call_date', 'sentiment', 'deal_stage', 'contact_id']
                }
            },
            'business-context': {
                'dimension': 1536,
                'metric': 'cosine',
                'metadata_config': {
                    'indexed': ['entity_type', 'last_updated', 'importance_score']
                }
            }
        }
        
        return pinecone
    
    def setup_weaviate(self):
        """Configure Weaviate for contextual business search"""
        client = weaviate.Client(
            url=os.getenv("WEAVIATE_URL"),
            auth_client_secret=weaviate.AuthApiKey(
                api_key=os.getenv("WEAVIATE_API_KEY")
            )
        )
        
        # Define schema for business entities
        schema = {
            "classes": [
                {
                    "class": "CallInsight",
                    "properties": [
                        {"name": "content", "dataType": ["text"]},
                        {"name": "sentiment", "dataType": ["string"]},
                        {"name": "callDate", "dataType": ["date"]},
                        {"name": "contactId", "dataType": ["string"]},
                        {"name": "dealId", "dataType": ["string"]},
                        {"name": "keyTopics", "dataType": ["string[]"]},
                        {"name": "nextSteps", "dataType": ["text"]},
                        {"name": "riskFactors", "dataType": ["string[]"]}
                    ]
                },
                {
                    "class": "BusinessContext",
                    "properties": [
                        {"name": "content", "dataType": ["text"]},
                        {"name": "entityType", "dataType": ["string"]},
                        {"name": "entityId", "dataType": ["string"]},
                        {"name": "importance", "dataType": ["number"]},
                        {"name": "lastUpdated", "dataType": ["date"]}
                    ]
                }
            ]
        }
        
        return client
```

---

### **5. Performance & Scaling Architecture**

#### **5.1 Caching Strategy**
```python
class CacheManager:
    def __init__(self):
        self.redis_client = redis.Redis(host=os.getenv('REDIS_HOST', 'localhost'), port=6379)
        self.cache_ttl = {
            'crm_data': 300,      # 5 minutes
            'call_analysis': 3600, # 1 hour
            'user_context': 1800,  # 30 minutes
            'business_insights': 900 # 15 minutes
        }
    
    async def get_cached_crm_data(self, entity_type: str, entity_id: str):
        """Get cached CRM data with fallback to API"""
        cache_key = f"crm:{entity_type}:{entity_id}"
        cached_data = await self.redis_client.get(cache_key)
        
        if cached_data:
            return json.loads(cached_data)
        
        # Fallback to API call
        fresh_data = await self.fetch_from_crm(entity_type, entity_id)
        await self.redis_client.setex(
            cache_key, 
            self.cache_ttl['crm_data'], 
            json.dumps(fresh_data)
        )
        return fresh_data
    
    async def invalidate_cache(self, pattern: str):
        """Invalidate cache entries matching pattern"""
        keys = await self.redis_client.keys(pattern)
        if keys:
            await self.redis_client.delete(*keys)
```

#### **5.2 Load Balancing & Scaling**
```python
class AgentLoadBalancer:
    def __init__(self):
        self.agent_registry = AgentRegistry()
        self.performance_monitor = PerformanceMonitor()
    
    async def route_task(self, task_type: str, task_data: dict):
        """Route task to best available agent"""
        # Get available agents for task type
        candidates = self.agent_registry.get_agents_by_capability(task_type)
        
        # Filter by current load and performance
        available_agents = []
        for agent_id in candidates:
            load = await self.performance_monitor.get_agent_load(agent_id)
            performance = await self.performance_monitor.get_agent_performance(agent_id)
            
            if load < 0.8 and performance > 0.7:  # Load < 80%, Performance > 70%
                available_agents.append({
                    'agent_id': agent_id,
                    'load': load,
                    'performance': performance,
                    'score': performance * (1 - load)  # Combined score
                })
        
        # Route to best available agent
        if available_agents:
            best_agent = max(available_agents, key=lambda x: x['score'])
            return await self.send_task_to_agent(best_agent['agent_id'], task_data)
        else:
            # Queue task for later processing
            return await self.queue_task(task_type, task_data)
```

---

### **6. Security & Monitoring Architecture**

#### **6.1 Security Implementation**
```python
class SecurityManager:
    def __init__(self):
        self.jwt_secret = os.getenv('JWT_SECRET_KEY')
        self.api_keys = self.load_encrypted_api_keys()
    
    def generate_user_token(self, user_id: str, permissions: list):
        """Generate JWT token for user authentication"""
        payload = {
            'user_id': user_id,
            'permissions': permissions,
            'exp': datetime.utcnow() + timedelta(hours=24),
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, self.jwt_secret, algorithm='HS256')
    
    def validate_api_access(self, endpoint: str, user_permissions: list):
        """Validate user access to specific endpoints"""
        endpoint_permissions = {
            '/admin/*': ['admin_access'],
            '/agents/*/config': ['agent_management'],
            '/crm/*': ['crm_access'],
            '/slack/*': ['slack_access']
        }
        
        required_permissions = endpoint_permissions.get(endpoint, [])
        return any(perm in user_permissions for perm in required_permissions)
    
    async def audit_log(self, user_id: str, action: str, resource: str, result: str):
        """Log all user actions for audit trail"""
        audit_entry = {
            'user_id': user_id,
            'action': action,
            'resource': resource,
            'result': result,
            'timestamp': datetime.utcnow().isoformat(),
            'ip_address': self.get_client_ip()
        }
        await self.store_audit_log(audit_entry)
```

#### **6.2 Monitoring & Alerting**
```python
class MonitoringSystem:
    def __init__(self):
        self.prometheus_client = PrometheusClient()
        self.alert_manager = AlertManager()
        
    def setup_metrics(self):
        """Setup Prometheus metrics for agent monitoring"""
        self.metrics = {
            'agent_response_time': Histogram(
                'sophia_agent_response_time_seconds',
                'Agent response time in seconds',
                ['agent_id', 'task_type']
            ),
            'agent_success_rate': Counter(
                'sophia_agent_success_total',
                'Total successful agent operations',
                ['agent_id', 'task_type']
            ),
            'crm_sync_operations': Counter(
                'sophia_crm_sync_total',
                'Total CRM sync operations',
                ['source', 'target', 'status']
            ),
            'slack_interactions': Counter(
                'sophia_slack_interactions_total',
                'Total Slack interactions',
                ['interaction_type', 'success']
            )
        }
    
    async def check_agent_health(self):
        """Monitor agent health and performance"""
        for agent_id in self.agent_registry.get_all_agents():
            try:
                response_time = await self.ping_agent(agent_id)
                self.metrics['agent_response_time'].labels(
                    agent_id=agent_id, task_type='health_check'
                ).observe(response_time)
                
                if response_time > 5.0:  # Alert if response time > 5 seconds
                    await self.alert_manager.send_alert(
                        f"Agent {agent_id} slow response: {response_time}s"
                    )
                    
            except Exception as e:
                await self.alert_manager.send_alert(
                    f"Agent {agent_id} health check failed: {str(e)}"
                )
```

---

## Deployment Architecture

### **Lambda Labs Server Configuration**
```yaml
# Recommended Lambda Labs instance configuration
Instance Type: GPU Cloud (for AI processing)
CPU: 8+ cores
RAM: 32GB+
GPU: 1x RTX 4090 (for local AI processing if needed)
Storage: 500GB SSD
Network: High-bandwidth for API integrations

# Docker Compose for Sophia AI
version: '3.8'
services:
  sophia-core:
    build: ./sophia-core
    ports:
      - "8000:8000"
    environment:
      - REDIS_URL=redis://redis:6379
      - POSTGRES_URL=postgresql://sophia_admin@postgres:5432/sophia_payready
      - HUBSPOT_API_KEY=${HUBSPOT_API_KEY}
      - GONG_API_KEY=${GONG_API_KEY}
      - SLACK_BOT_TOKEN=${SLACK_BOT_TOKEN}
    depends_on:
      - redis
      - postgres
  
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
  
  postgres:
    image: postgres:14
    environment:
      - POSTGRES_DB=sophia_payready
      - POSTGRES_USER=sophia_admin
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml

volumes:
  redis_data:
  postgres_data:
```

This technical architecture provides a robust, scalable foundation for Sophia AI's evolution into your company's AI assistant orchestrator, with specific focus on the HubSpot + Gong.io + Slack integration that will deliver immediate business value.

