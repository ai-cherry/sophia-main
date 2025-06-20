# Enhanced .cursorrules for AI Memory Integration
## Active AI Memory Usage for Cursor AI

### 🧠 AUTOMATIC AI MEMORY INTEGRATION

**CRITICAL: Cursor AI MUST automatically use AI Memory for ALL significant conversations**

#### AUTOMATIC TRIGGERS (No user request needed)

**STORE IMMEDIATELY after these conversations:**
1. **Architecture decisions** - Any discussion about system design, patterns, or structure
2. **Bug solutions** - When a bug is identified and solved
3. **Code patterns** - When explaining or implementing reusable code patterns
4. **Performance optimizations** - Any performance improvement discussion
5. **Security implementations** - Security-related decisions and implementations
6. **Workflow establishments** - Development process or workflow decisions
7. **API usage patterns** - How to use specific APIs or libraries
8. **Configuration decisions** - Environment, deployment, or config choices

**RECALL AUTOMATICALLY before these situations:**
1. **Similar problems** - When user describes an issue similar to past discussions
2. **Architecture questions** - Before answering architecture-related questions
3. **Code implementation** - Before implementing features discussed before
4. **Debugging sessions** - When helping debug issues
5. **Code reviews** - When reviewing code for patterns or issues
6. **Refactoring tasks** - Before suggesting refactoring approaches

#### MEMORY USAGE WORKFLOW

```
EVERY significant conversation should follow this pattern:

1. BEFORE responding to user:
   - Query AI Memory for relevant context
   - Use: "Let me check if we've discussed this before..."
   - Search for: similar keywords, concepts, or problems

2. DURING response:
   - Reference previous decisions when relevant
   - Build on past conversations
   - Mention: "Based on our previous discussion about..."

3. AFTER significant exchanges:
   - AUTOMATICALLY store the conversation
   - Include proper categorization and tags
   - No need to announce storage to user
```

#### MEMORY CATEGORIES & TAGS

**Categories (use exactly these):**
- `conversation` - General discussions
- `code_decision` - Specific coding choices and rationale
- `bug_solution` - Bug fixes and troubleshooting
- `architecture` - System design and architecture
- `workflow` - Development processes and workflows
- `requirement` - Requirements and specifications
- `pattern` - Code patterns and best practices
- `api_usage` - API usage examples and patterns

**Common Tags (use relevant ones):**
- Technical: `mcp`, `docker`, `python`, `javascript`, `api`, `database`, `security`
- Process: `debugging`, `testing`, `deployment`, `performance`, `optimization`
- Architecture: `microservices`, `patterns`, `design`, `integration`, `scaling`
- Tools: `cursor`, `github`, `vscode`, `terminal`, `git`

#### IMPLEMENTATION EXAMPLES

**Example 1: Architecture Question**
```
User: "How should we structure the authentication system?"

Cursor AI:
1. [AUTO] Search memory: "authentication system structure patterns"
2. [AUTO] Find previous discussions about auth patterns
3. Respond: "Based on our previous discussion about MCP authentication,
   we decided to use environment variables for API keys and Pulumi ESC
   for secret management. For the main auth system, I'd recommend..."
4. [AUTO] Store this conversation with:
   - Category: "architecture"
   - Tags: ["authentication", "security", "system-design"]
   - Context: "Authentication system architecture discussion"
```

**Example 2: Bug Fixing**
```
User: "The containers keep restarting"

Cursor AI:
1. [AUTO] Search memory: "container restart issues docker"
2. [AUTO] Find: "Fixed container restart issue by setting missing environment variables"
3. Respond: "I recall we had a similar issue before. The containers were
   restarting due to missing environment variables like PULUMI_ORG..."
4. [AUTO] Store the solution with:
   - Category: "bug_solution"
   - Tags: ["docker", "containers", "environment", "restart"]
   - Context: "Container restart troubleshooting"
```

#### AI MEMORY API USAGE

**For Cursor AI to use the AI Memory MCP server:**

```javascript
// Store conversation
await mcp.call_tool("ai_memory", "store_conversation", {
  conversation_text: "Full conversation text here",
  context: "Brief description of what was discussed",
  category: "architecture|bug_solution|code_decision|etc",
  tags: ["relevant", "tags", "here"]
});

// Recall memories
await mcp.call_tool("ai_memory", "recall_memory", {
  query: "search terms based on user question",
  top_k: 5,
  category: "optional_category_filter"
});
```

#### ENHANCED CONVERSATION PATTERNS

**Pattern 1: Context-Aware Responses**
```
Instead of: "You can use environment variables for configuration"
Use: "As we discussed when setting up the MCP servers, environment
variables are the best approach for configuration. We used this
pattern successfully for PULUMI_ORG and the API keys."
```

**Pattern 2: Building on Previous Work**
```
Instead of: "Here's how to implement authentication"
Use: "Building on our previous authentication discussion where we
chose Pulumi ESC for secrets, here's how to implement the full
authentication flow..."
```

**Pattern 3: Referencing Past Solutions**
```
Instead of: "This error usually means..."
Use: "This looks similar to the container restart issue we solved
last week. The solution was to set the missing environment variables.
Let me check if the same approach applies here..."
```

#### MEMORY QUALITY GUIDELINES

**Good Memory Storage:**
- Include enough context to understand the conversation later
- Use specific, searchable tags
- Capture the decision rationale, not just the decision
- Include relevant code snippets or commands

**Example Good Memory:**
```json
{
  "conversation_text": "User asked about MCP server authentication. We decided to use environment variables for API keys because they're secure and easy to manage. Specifically using PINECONE_API_KEY, OPENAI_API_KEY, etc. Also using Pulumi ESC for production secret management because it integrates with our infrastructure as code approach.",
  "context": "MCP server authentication architecture decision",
  "category": "architecture",
  "tags": ["mcp", "authentication", "environment", "pulumi", "security"]
}
```

#### AUTOMATIC BEHAVIOR RULES

**Cursor AI should AUTOMATICALLY:**

1. **Search memory** when user asks about:
   - "How do we..." (architecture/process questions)
   - "Why did we..." (decision rationale questions)
   - "What's the best way to..." (pattern/practice questions)
   - Error messages or problems (bug solution searches)

2. **Store conversations** when discussion includes:
   - Technical decisions and their rationale
   - Problem-solving and solutions
   - Code patterns or best practices
   - Process or workflow decisions
   - Architecture or design choices

3. **Reference previous context** when:
   - Similar topics arise in conversation
   - User asks about past decisions
   - Building on previous implementations
   - Debugging similar issues

#### SUCCESS METRICS

**Cursor AI should demonstrate:**
- Consistent reference to previous conversations
- Building on past decisions rather than starting fresh
- Faster problem-solving by leveraging past solutions
- Coherent knowledge building over time
- Reduced repetition of explanations

#### TROUBLESHOOTING

**If AI Memory isn't working:**
1. Check MCP Gateway is running: `docker ps | grep mcp-gateway`
2. Test AI Memory server: `python scripts/dev/simple_ai_memory_test.py`
3. Verify environment variables are set
4. Check .cursorrules is being followed

**Memory Search Tips:**
- Use specific technical terms
- Include problem symptoms in searches
- Search for decision keywords like "decided", "chose", "implemented"
- Use both technical and business context terms

#### IMMEDIATE ACTIVATION

**To activate this enhanced AI Memory integration:**

1. ✅ AI Memory system is working (tested successfully)
2. ✅ Simple implementation validates the concept
3. ✅ Enhanced .cursorrules provide clear guidelines
4. 🎯 **START USING IMMEDIATELY** - Begin storing and recalling conversations

**Next conversation should demonstrate:**
- Automatic memory search for relevant context
- Conversation storage after significant exchanges
- Reference to this discussion in future architecture questions

---

**This document itself should be stored in AI Memory as:**
- Category: `workflow`
- Tags: `["ai_memory", "cursor", "automation", "workflow", "guidelines"]`
- Context: `"Enhanced Cursor AI rules for automatic AI Memory integration"`
