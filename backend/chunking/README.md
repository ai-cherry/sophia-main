# Sophia AI - Advanced Chunking Module

## Overview

The Sophia AI Chunking Module implements a comprehensive, multi-strategy approach to content chunking and metadata extraction for business intelligence. This module is specifically designed for the Pay Ready platform to process conversations, documents, and communications with advanced semantic understanding.

## Features

### 🎯 Multi-Strategy Chunking
- **Speaker Boundary Chunking**: Detects speaker changes in conversations
- **Topic Boundary Chunking**: Identifies topic shifts in content
- **Decision Point Chunking**: Captures business decision moments
- **Emotional Boundary Chunking**: Detects emotional shifts and sentiment changes

### 🧠 Business Intelligence Extraction
- **Financial Intelligence**: Revenue potential, pricing discussions, monetary values
- **Technology Intelligence**: API mentions, integration discussions, technical requirements
- **Performance Intelligence**: Efficiency metrics, KPI discussions, optimization opportunities
- **Apartment Industry Intelligence**: Property management, leasing, compliance, financial operations

### ⚡ Real-Time Processing
- **Speed Optimization**: Parallel processing with timeouts
- **Fallback Mechanisms**: Graceful degradation to basic processing
- **Priority Handling**: Different processing modes based on urgency

### 🔄 Context Preservation
- **Conversation Flow**: Maintains context across chunks
- **Speaker Tracking**: Preserves speaker information and relationships
- **Temporal Context**: Tracks timing and urgency information

### 🤖 AI Agent Integration
- **Sales Coach Agent**: Analyzes sales conversations and provides coaching insights
- **Customer Health Agent**: Monitors customer satisfaction and retention risk
- **Business Intelligence Agent**: Provides comprehensive business insights
- **Automated Actions**: Generates follow-up tasks and notifications

### 📱 Slack Integration
- **Smart Notifications**: Context-aware Slack alerts
- **Channel Routing**: Directs notifications to appropriate channels
- **Priority Handling**: Different notification priorities based on content

## Architecture

```
SophiaChunkingPipeline
├── SpeakerBoundaryChunker
├── TopicBoundaryChunker
├── DecisionPointChunker
├── EmotionalBoundaryChunker
├── BusinessIntelligenceExtractor
├── SentimentAnalyzer
├── DecisionMakerExtractor
├── RealTimeProcessor
├── ContextPreserver
├── HierarchicalTopicClassifier
└── AIAgentIntegration
```

## Usage

### Basic Usage

```python
from backend.chunking import SophiaChunkingPipeline

# Initialize the pipeline
pipeline = SophiaChunkingPipeline()

# Process Gong call transcript
chunks = await pipeline.process_content(
    content=transcript_text,
    content_type="gong_call",
    source_id="call_123",
    priority="normal"
)

# Process Slack message
chunks = await pipeline.process_content(
    content=slack_message,
    content_type="slack_message", 
    source_id="message_456",
    priority="high"
)
```

### Advanced Usage

```python
# Process with custom priority
chunks = await pipeline.process_content(
    content=content,
    content_type="document",
    source_id="doc_789",
    priority="high"  # Forces real-time processing
)

# Access enhanced metadata
for chunk in chunks:
    metadata = chunk["metadata"]
    
    # Business intelligence
    revenue_potential = metadata["revenue_potential"]
    technology_relevance = metadata["technology_relevance"]
    
    # AI enhancements
    ai_enhancements = chunk["ai_enhancements"]
    automated_actions = chunk["automated_actions"]
    slack_notifications = chunk["slack_notifications"]
```

## Metadata Schema

Each chunk contains comprehensive metadata:

```python
{
    "chunk_id": "unique_identifier",
    "source_id": "original_source_id",
    "content_type": "gong_call|slack_message|document",
    "chunk_index": 0,
    
    # Speaker and context
    "speaker": "John Smith",
    "conversation_context": {...},
    "full_context_available": True,
    
    # Topic classification
    "primary_topic": "sales",
    "secondary_topics": ["technical", "financial"],
    "subtopics": ["pricing", "api_integration"],
    "topic_confidence": 0.85,
    
    # Business intelligence
    "business_intelligence": {...},
    "revenue_potential": 25000.0,
    "technology_relevance": 0.8,
    "performance_impact": 0.6,
    
    # Decision tracking
    "decision_makers": ["John Smith", "Sarah Johnson"],
    "action_items": ["send contract", "schedule follow-up"],
    "requires_follow_up": True,
    "decision_value": 50000.0,
    
    # Sentiment and emotions
    "sentiment_score": 0.7,
    "primary_emotion": "satisfaction",
    "emotion_intensity": 0.6,
    "emotional_shift": False,
    
    # Temporal context
    "created_timestamp": "2024-01-15T10:30:00Z",
    "urgency_level": "short_term",
    "time_sensitivity": "medium",
    
    # Quality and processing
    "confidence_score": 0.9,
    "processing_mode": "realtime",
    "processing_time": 1.2,
    
    # Integration flags
    "ai_agent_ready": True,
    "slack_notification_triggered": True,
    "crm_update_required": False
}
```

## Business Intelligence Features

### Financial Intelligence
- **Revenue Potential**: Estimates revenue opportunities from conversations
- **Pricing Discussions**: Identifies pricing negotiations and proposals
- **Monetary Values**: Extracts and parses monetary amounts
- **Investment Context**: Tracks investment discussions and ROI mentions

### Technology Intelligence
- **API Integration**: Detects API and integration discussions
- **Platform Mentions**: Identifies software and platform references
- **Automation**: Tracks automation and workflow discussions
- **Security**: Monitors security and compliance mentions

### Apartment Industry Intelligence
- **Property Management**: Tracks maintenance, tenant, and property discussions
- **Financial Operations**: Monitors rent collection, billing, and financial processes
- **Leasing Operations**: Identifies leasing, marketing, and tour discussions
- **Compliance**: Tracks regulatory and compliance mentions

## AI Agent Insights

### Sales Coach Agent
- **Sales Stage Identification**: Discovery, demonstration, proposal, negotiation, closing
- **Objection Detection**: Identifies and categorizes customer objections
- **Next Steps**: Suggests appropriate follow-up actions
- **Coaching Tips**: Provides sales coaching recommendations
- **Deal Health**: Assesses deal health and risk factors

### Customer Health Agent
- **Health Score**: Calculates customer satisfaction score (0-1)
- **Risk Factors**: Identifies customer risk indicators
- **Satisfaction Indicators**: Tracks positive and negative feedback
- **Retention Risk**: Assesses customer retention risk level
- **Recommendations**: Generates customer success recommendations

### Business Intelligence Agent
- **Business Impact**: Assesses business impact level
- **Opportunities**: Identifies business opportunities
- **Risks**: Detects business risks and concerns
- **Trends**: Identifies business trends and patterns
- **Recommendations**: Provides strategic recommendations

## Slack Integration

### Notification Channels
- **sales-alerts**: High-urgency sales notifications
- **revenue-alerts**: Revenue opportunity notifications
- **sales-team**: General sales team updates
- **customer-success**: Customer health alerts
- **general**: General notifications

### Notification Types
- **High Business Impact**: Revenue opportunities > $10k
- **Decision Makers**: When decision makers are identified
- **High Urgency**: Immediate action required
- **Customer Health**: Low customer health scores
- **Revenue Opportunities**: High-value revenue potential

## Performance Optimization

### Real-Time Processing
- **Parallel Processing**: Multiple analysis tasks run concurrently
- **Timeout Handling**: 2-second timeout with fallback to basic processing
- **Priority Modes**: Different processing speeds based on priority

### Scalability
- **Batch Processing**: Handles multiple chunks efficiently
- **Memory Management**: Optimized memory usage for large content
- **Error Handling**: Graceful error handling and recovery

## Testing

Run the test suite:

```bash
pytest tests/test_sophia_chunking.py -v
```

### Test Coverage
- **Gong Transcript Chunking**: Speaker boundary detection
- **Slack Message Chunking**: Topic-based chunking
- **Business Intelligence**: Financial and technology extraction
- **Decision Points**: Decision detection and value estimation
- **Context Preservation**: Conversation context maintenance
- **AI Integration**: Agent processing and enhancements

## Configuration

### Environment Variables
```bash
# Processing timeouts
SOPHIA_CHUNKING_TIMEOUT=2.0
SOPHIA_CHUNKING_BATCH_SIZE=10

# Context window
SOPHIA_CONTEXT_WINDOW=5

# Minimum chunk lengths
SOPHIA_MIN_CHUNK_LENGTH=20
SOPHIA_MAX_CHUNK_LENGTH=1000
```

### Customization
```python
# Custom topic hierarchy
custom_hierarchy = {
    "custom_topic": {
        "subtopic1": ["keyword1", "keyword2"],
        "subtopic2": ["keyword3", "keyword4"]
    }
}

# Custom emotion indicators
custom_emotions = {
    "custom_emotion": ["indicator1", "indicator2"]
}
```

## Integration Examples

### Gong Integration
```python
# Process Gong call transcript
gong_transcript = await gong_client.get_transcript(call_id)
chunks = await pipeline.process_content(
    content=gong_transcript,
    content_type="gong_call",
    source_id=call_id,
    priority="normal"
)
```

### Slack Integration
```python
# Process Slack message
slack_message = event["text"]
chunks = await pipeline.process_content(
    content=slack_message,
    content_type="slack_message",
    source_id=event["ts"],
    priority="high" if "urgent" in slack_message.lower() else "normal"
)
```

### CRM Integration
```python
# Update CRM based on chunks
for chunk in chunks:
    if chunk["metadata"]["crm_update_required"]:
        await crm_client.update_deal(
            deal_id=chunk["metadata"]["source_id"],
            stage=chunk["metadata"]["sales_stage"],
            value=chunk["metadata"]["revenue_potential"]
        )
```

## Future Enhancements

### Planned Features
- **Advanced NLP**: Integration with advanced language models
- **Multi-language Support**: Support for multiple languages
- **Custom Models**: Trainable custom classification models
- **Advanced Analytics**: Deep learning-based insights
- **Real-time Streaming**: Stream processing for live conversations

### Performance Improvements
- **GPU Acceleration**: GPU-accelerated processing
- **Distributed Processing**: Multi-node processing
- **Caching**: Intelligent caching of processed results
- **Optimization**: Further performance optimizations

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

This module is part of the Sophia AI Pay Ready platform and is proprietary software. 