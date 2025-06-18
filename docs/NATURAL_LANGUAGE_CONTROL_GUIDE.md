# SOPHIA AI System - Natural Language Control Guide

## Overview

This guide outlines the natural language control capabilities of the SOPHIA AI System, enabling users to interact with and control the system using conversational language rather than traditional interfaces.

## Table of Contents

1. [Introduction](#introduction)
2. [Architecture](#architecture)
3. [Command Structure](#command-structure)
4. [Supported Commands](#supported-commands)
5. [Context Awareness](#context-awareness)
6. [User Permissions](#user-permissions)
7. [Implementation](#implementation)
8. [Best Practices](#best-practices)
9. [Troubleshooting](#troubleshooting)
10. [Examples](#examples)

## Introduction

The Natural Language Control (NLC) system allows users to interact with SOPHIA using conversational language, making the system more accessible and intuitive. Users can issue commands, ask questions, and control various aspects of the system without needing to learn a specific syntax or interface.

Key benefits include:

- **Intuitive Interaction**: Users can communicate with the system in their own words
- **Reduced Learning Curve**: Minimal training required to use the system
- **Increased Efficiency**: Faster access to information and functionality
- **Flexibility**: Commands can be phrased in multiple ways
- **Accessibility**: Makes the system usable for non-technical users

## Architecture

The Natural Language Control system consists of several components:

1. **Intent Recognition**: Identifies the user's intention from natural language input
2. **Entity Extraction**: Extracts relevant entities (names, dates, etc.) from the input
3. **Context Management**: Maintains conversation context for follow-up commands
4. **Command Execution**: Translates recognized intents into system actions
5. **Response Generation**: Creates natural language responses to commands

```
┌─────────────────────────────────────────────────────┐
│               Natural Language Control               │
│                                                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │    Intent   │  │   Entity    │  │   Context   │  │
│  │ Recognition │  │ Extraction  │  │ Management  │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  │
│                                                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │   Command   │  │  Response   │  │ Conversation│  │
│  │  Execution  │  │ Generation  │  │   History   │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  │
│                                                     │
└─────────────────────────────────────────────────────┘
         │               │               │
         ▼               ▼               ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│  SOPHIA     │  │  External   │  │   System    │
│  Agents     │  │  Systems    │  │   Actions   │
└─────────────┘  └─────────────┘  └─────────────┘
```

## Command Structure

While natural language commands don't require a specific syntax, they generally follow this pattern:

```
[Action] [Object] [Parameters] [Constraints]
```

Examples:
- "Show me sales data for Q2 2025"
  - Action: Show
  - Object: Sales data
  - Parameters: Q2 2025
  
- "Schedule a meeting with the client success team tomorrow at 2pm"
  - Action: Schedule
  - Object: Meeting
  - Parameters: Client success team, tomorrow, 2pm

- "Analyze the last 5 Gong calls with customer XYZ and summarize key issues"
  - Action: Analyze
  - Object: Gong calls
  - Parameters: Last 5, customer XYZ
  - Constraints: Summarize key issues

## Supported Commands

The NLC system supports the following command categories:

### 1. Data Retrieval

Commands for retrieving and displaying data:

- "Show me [data type] for [time period]"
- "Find [information] about [entity]"
- "Get the latest [data type]"
- "Display [metric] for [entity]"
- "Search for [query] in [data source]"

### 2. Analysis

Commands for analyzing data and generating insights:

- "Analyze [data] for [patterns/trends]"
- "Compare [entity A] with [entity B]"
- "Identify issues in [data source]"
- "Predict [outcome] based on [data]"
- "Summarize [information]"

### 3. Communication

Commands for communication and notifications:

- "Send [message] to [recipient]"
- "Notify [team] about [event]"
- "Schedule [meeting] with [participants]"
- "Create alert for [condition]"
- "Share [information] with [recipient]"

### 4. System Control

Commands for controlling system behavior:

- "Configure [setting] to [value]"
- "Enable/Disable [feature]"
- "Set [parameter] to [value]"
- "Update [component]"
- "Restart [service]"

### 5. Agent Interaction

Commands for interacting with specialized agents:

- "Ask Sales Coach to [task]"
- "Have Client Health Agent analyze [client]"
- "Tell Research Agent to find [information]"
- "Request Business Strategy Agent to [task]"
- "Instruct HR Agent to [task]"

## Context Awareness

The NLC system maintains context throughout a conversation, allowing for more natural interactions:

### Contextual References

Users can use pronouns and references to previously mentioned entities:

- User: "Show me sales data for Acme Corp"
- SOPHIA: *displays sales data*
- User: "Now compare it with their data from last year"
- SOPHIA: *understands "it" refers to sales data and "their" refers to Acme Corp*

### Conversation History

The system maintains a history of the conversation, allowing it to understand references to previous commands and results:

- User: "Who are our top 5 clients by revenue?"
- SOPHIA: *lists top 5 clients*
- User: "Send a summary of this to the sales team"
- SOPHIA: *understands "this" refers to the list of top 5 clients*

### Multi-turn Interactions

Complex tasks can be accomplished through multiple turns of conversation:

- User: "I need to prepare for my meeting with Acme Corp"
- SOPHIA: "What information would you like about Acme Corp?"
- User: "Their recent support tickets and sales history"
- SOPHIA: *provides requested information*
- User: "Any red flags I should be aware of?"
- SOPHIA: *analyzes the data for potential issues*

## User Permissions

The NLC system enforces user permissions to ensure security:

### Permission Levels

- **View**: Can retrieve and view data
- **Analyze**: Can perform analysis on data
- **Communicate**: Can send messages and notifications
- **Configure**: Can change system settings
- **Admin**: Has full access to all commands

### Permission Enforcement

When a user issues a command, the system:

1. Identifies the required permission level for the command
2. Checks if the user has the necessary permissions
3. Executes the command or returns an error message

### Permission Examples

- "Show me sales data" - Requires View permission
- "Analyze customer churn" - Requires Analyze permission
- "Send report to team" - Requires Communicate permission
- "Update agent configuration" - Requires Configure permission
- "Add new user" - Requires Admin permission

## Implementation

The NLC system is implemented using the following components:

### 1. NL Command Agent

The NL Command Agent (`backend/agents/nl_command_agent.py`) is responsible for:

- Parsing natural language input
- Identifying intents and entities
- Maintaining conversation context
- Routing commands to appropriate handlers

```python
class NLCommandAgent(BaseAgent):
    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self.intent_recognizer = IntentRecognizer()
        self.entity_extractor = EntityExtractor()
        self.context_manager = ContextManager()
        self.command_router = CommandRouter()
        
    async def execute_task(self, task: Task) -> TaskResult:
        try:
            # Parse natural language input
            nl_input = task.input.get("text", "")
            
            # Recognize intent
            intent = self.intent_recognizer.recognize(nl_input)
            
            # Extract entities
            entities = self.entity_extractor.extract(nl_input)
            
            # Update context
            context = self.context_manager.update(task.context, intent, entities)
            
            # Route command
            result = await self.command_router.route(intent, entities, context)
            
            return TaskResult(
                status="success",
                output=result,
                context=context
            )
        except Exception as e:
            logger.error(f"Error executing NL command: {e}")
            return TaskResult(
                status="error",
                output={"error": str(e)},
                context=task.context
            )
```

### 2. Intent Recognition

The Intent Recognizer identifies the user's intention from natural language input:

```python
class IntentRecognizer:
    def __init__(self):
        self.model = self._load_model()
        
    def _load_model(self):
        # Load intent recognition model
        # This could be a fine-tuned language model
        pass
        
    def recognize(self, text: str) -> Intent:
        # Recognize intent from text
        intent_type = self._classify_intent_type(text)
        action = self._extract_action(text)
        object_type = self._extract_object(text)
        
        return Intent(
            type=intent_type,
            action=action,
            object=object_type
        )
```

### 3. Entity Extraction

The Entity Extractor identifies relevant entities in the user's input:

```python
class EntityExtractor:
    def __init__(self):
        self.model = self._load_model()
        
    def _load_model(self):
        # Load entity extraction model
        # This could be a named entity recognition model
        pass
        
    def extract(self, text: str) -> List[Entity]:
        # Extract entities from text
        entities = []
        
        # Extract dates, times, names, etc.
        dates = self._extract_dates(text)
        times = self._extract_times(text)
        names = self._extract_names(text)
        
        # Add extracted entities to list
        entities.extend(dates)
        entities.extend(times)
        entities.extend(names)
        
        return entities
```

### 4. Context Management

The Context Manager maintains conversation context:

```python
class ContextManager:
    def __init__(self):
        self.max_history = 10
        
    def update(self, current_context: Dict, intent: Intent, entities: List[Entity]) -> Dict:
        # Update context with new intent and entities
        new_context = current_context.copy()
        
        # Add current intent to history
        if "intent_history" not in new_context:
            new_context["intent_history"] = []
        
        new_context["intent_history"].append(intent)
        
        # Limit history size
        if len(new_context["intent_history"]) > self.max_history:
            new_context["intent_history"] = new_context["intent_history"][-self.max_history:]
        
        # Update entity references
        self._update_entity_references(new_context, entities)
        
        return new_context
        
    def _update_entity_references(self, context: Dict, entities: List[Entity]):
        # Update entity references in context
        # This allows resolving pronouns and references
        pass
```

### 5. Command Routing

The Command Router directs commands to the appropriate handlers:

```python
class CommandRouter:
    def __init__(self):
        self.handlers = self._register_handlers()
        
    def _register_handlers(self) -> Dict[str, CommandHandler]:
        # Register command handlers
        return {
            "data_retrieval": DataRetrievalHandler(),
            "analysis": AnalysisHandler(),
            "communication": CommunicationHandler(),
            "system_control": SystemControlHandler(),
            "agent_interaction": AgentInteractionHandler()
        }
        
    async def route(self, intent: Intent, entities: List[Entity], context: Dict) -> Dict:
        # Route command to appropriate handler
        handler = self._get_handler(intent)
        
        if handler:
            return await handler.handle(intent, entities, context)
        else:
            raise ValueError(f"No handler found for intent: {intent.type}")
            
    def _get_handler(self, intent: Intent) -> CommandHandler:
        # Get appropriate handler for intent
        return self.handlers.get(intent.type)
```

## Best Practices

### For Users

1. **Be Specific**: Provide specific details in your commands
2. **Use Natural Language**: Speak or type as you normally would
3. **Provide Context**: Include relevant context in your commands
4. **Use Follow-up Questions**: Ask for clarification if needed
5. **Learn from Examples**: Study example commands to understand capabilities

### For Developers

1. **Train with Real Data**: Use real user queries to train the NLC system
2. **Handle Ambiguity**: Implement clarification dialogs for ambiguous commands
3. **Provide Feedback**: Give clear feedback when commands are not understood
4. **Optimize for Common Commands**: Ensure high accuracy for frequently used commands
5. **Continuously Improve**: Regularly update the system based on user interactions

## Troubleshooting

### Common Issues

#### 1. Command Not Recognized

If a command is not recognized:

1. Try rephrasing the command
2. Use more specific language
3. Break complex commands into simpler ones
4. Check if the command is supported

#### 2. Incorrect Intent Recognition

If the system misinterprets your intent:

1. Be more explicit about the action you want to perform
2. Provide additional context
3. Use keywords that clearly indicate your intent

#### 3. Entity Extraction Errors

If the system fails to extract entities correctly:

1. Use more specific entity names
2. Provide additional identifying information
3. Format dates, times, and numbers clearly

#### 4. Context Confusion

If the system loses track of context:

1. Explicitly reference entities by name
2. Restart the conversation if necessary
3. Provide complete information in each command

## Examples

### Data Retrieval Examples

```
"Show me sales data for Q2 2025"
"Find all clients in the healthcare industry"
"Get the latest support tickets for Acme Corp"
"Display revenue by region for the last 6 months"
"Search for mentions of product X in customer feedback"
```

### Analysis Examples

```
"Analyze customer churn for enterprise clients"
"Compare performance of team A and team B"
"Identify bottlenecks in the sales pipeline"
"Predict revenue for Q3 based on current trends"
"Summarize the key points from yesterday's client calls"
```

### Communication Examples

```
"Send a summary of this report to the sales team"
"Notify the support team about the issue with client X"
"Schedule a follow-up meeting with Acme Corp next week"
"Create an alert for any clients with satisfaction below 70%"
"Share these insights with the executive team"
```

### System Control Examples

```
"Configure notification preferences to only send high priority alerts"
"Enable automatic reporting for all client accounts"
"Set default analysis period to 90 days"
"Update the sales coach agent with the latest training data"
"Restart the integration with Salesforce"
```

### Agent Interaction Examples

```
"Ask Sales Coach to analyze my last call with Acme Corp"
"Have Client Health Agent check the status of our top 10 accounts"
"Tell Research Agent to find information about competitor X's new product"
"Request Business Strategy Agent to identify growth opportunities in the healthcare sector"
"Instruct HR Agent to summarize team performance reviews"
```

### Multi-turn Conversation Example

```
User: "I need to prepare for my meeting with Acme Corp tomorrow"

SOPHIA: "I can help you prepare for your meeting with Acme Corp. What specific information would you like to know?"

User: "First, show me their account status"

SOPHIA: "Acme Corp is a Tier 1 client with an active enterprise subscription ($250,000/year). Their renewal is due in 3 months. Their account health score is 85/100 (Good)."

User: "Any recent support issues?"

SOPHIA: "In the last 30 days, Acme Corp has submitted 5 support tickets:
1. API integration issue (Resolved)
2. User access problem (Resolved)
3. Data import failure (In Progress)
4. Custom report request (Pending)
5. Feature request for mobile app (Under Review)"

User: "What about their usage patterns?"

SOPHIA: "Acme Corp has 120 active users (up 15% from last quarter). Their most used features are:
1. Analytics Dashboard (78% of users)
2. Custom Reports (65% of users)
3. Data Integration (42% of users)

Their usage has increased 23% compared to the same period last year."

User: "Great. Can you prepare a summary of this information and send it to me and the account team?"

SOPHIA: "I've prepared a summary of Acme Corp's account status, support issues, and usage patterns. Would you like to review it before I send it to you and the account team?"

User: "Yes, show me the summary"

SOPHIA: *displays summary*

User: "Looks good. Send it out and add a note that we should discuss the pending support tickets during the meeting."

SOPHIA: "I've sent the summary to you and the account team with a note about discussing the pending support tickets during the meeting."
```

## Conclusion

The Natural Language Control system provides an intuitive and powerful way to interact with the SOPHIA AI System. By understanding user intent, maintaining conversation context, and executing commands across various domains, it enables users to accomplish complex tasks using natural language.

As the system continues to evolve, it will become even more capable of understanding nuanced commands and handling complex scenarios, further enhancing the user experience and productivity.
