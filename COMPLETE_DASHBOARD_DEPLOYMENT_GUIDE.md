
# Sophia AI Dashboard Deployment Guide
Generated: 2025-06-20 15:59:29

## 🚀 Quick Start

### Prerequisites Status:
- ✅ Backend API
- ✅ Docker
- ✅ Docker Compose
- ✅ Environment Variables
- ✅ Python Dependencies


### MCP Server Status:


### Integration Status:
- ✅ Snowflake: Database: N/A
- ✅ Gong: Calls available: 0
- ✅ Slack: Workspace: N/A
- ✅ Pinecone: Index: N/A
- ✅ Linear: Workspace: N/A
- ✅ OpenAI:


## 📊 Dashboard URLs

### 1. CEO Dashboard
- **Purpose**: Executive command center with strategic intelligence
- **Backend URL**: http://localhost:8000
- **Key Features**:
  - Strategic Intelligence Chat
  - Client Health Portfolio
  - AI System Monitoring

### 2. Knowledge Admin Dashboard
- **Purpose**: Knowledge base management and curation
- **API Endpoint**: http://localhost:8000/api/knowledge
- **Key Features**:
  - Document Upload & Processing
  - Knowledge Curation Chat
  - Discovery Queue for insights

### 3. Project Intelligence Dashboard
- **Purpose**: Unified project management across Linear, GitHub, Asana, Slack
- **API Endpoint**: http://localhost:8000/api/project-management
- **Key Features**:
  - Portfolio Overview
  - OKR Alignment Tracking
  - Team Performance Analytics

## 🛠️ Retool Setup Instructions

### Step 1: Create Retool Apps

1. Log into Retool (https://retool.com)
2. Create three new apps:
   - "Sophia CEO Dashboard"
   - "Sophia Knowledge Admin"
   - "Sophia Project Intelligence"

### Step 2: Import Configurations

For each dashboard:
1. Open the app in Retool
2. Go to Settings → App JSON
3. Copy the contents from the respective config file:
   - CEO: `retool_ceo_dashboard_config.json`
   - Knowledge: `retool_knowledge_dashboard_config.json`
   - Project: `retool_project_dashboard_config.json`
4. Paste and save

### Step 3: Configure Resources

Each dashboard needs its API resource configured:

**CEO Dashboard:**
- Resource Name: SophiaAPI
- Base URL: http://localhost:8000
- Headers: X-Admin-Key = sophia_admin_2024

**Knowledge Admin:**
- Resource Name: KnowledgeAPI
- Base URL: http://localhost:8000/api/knowledge
- Headers: Authorization = Bearer {{ current_user.authToken }}

**Project Intelligence:**
- Resource Name: ProjectAPI
- Base URL: http://localhost:8000/api/project-management
- Headers: Authorization = Bearer {{ environment.SOPHIA_API_KEY }}

### Step 4: Environment Variables

Set these in Retool's environment settings:
- SOPHIA_API_URL = http://localhost:8000
- SOPHIA_API_KEY = sophia_admin_2024
- SOPHIA_ADMIN_KEY = sophia_admin_2024

## 🔧 Test Commands

### Test CEO Dashboard API:
```bash
# Dashboard Summary
curl -H "X-Admin-Key: sophia_admin_2024" \
     http://localhost:8000/api/retool/executive/dashboard-summary

# Strategic Chat
curl -X POST -H "X-Admin-Key: sophia_admin_2024" \
     -H "Content-Type: application/json" \
     -d '{"message": "What is our client health status?", "mode": "internal"}' \
     http://localhost:8000/api/retool/executive/strategic-chat
```

### Test Knowledge Admin API:
```bash
# Get Knowledge Stats
curl -H "Authorization: Bearer sophia_admin_2024" \
     http://localhost:8000/api/knowledge/stats

# Search Knowledge
curl -H "Authorization: Bearer sophia_admin_2024" \
     http://localhost:8000/api/knowledge/search?q=sales
```

### Test Project Management API:
```bash
# Dashboard Summary
curl -H "Authorization: Bearer sophia_admin_2024" \
     http://localhost:8000/api/project-management/dashboard/summary

# OKR Alignment
curl -H "Authorization: Bearer sophia_admin_2024" \
     http://localhost:8000/api/project-management/okr/alignment?quarter=Q1_2024
```

## 🎨 Design System

All dashboards use a consistent design system:
- **Primary Color**: #5E6AD2 (Linear purple)
- **Secondary Color**: #238636 (GitHub green)
- **Background**: #1a1a1a (Dark theme)
- **Surface**: #2a2a2a (Card backgrounds)
- **Font**: Inter, system-ui, sans-serif
- **Border Radius**: 8px
- **Spacing**: 4px, 8px, 16px, 24px, 32px

## 🚨 Troubleshooting

### Backend Connection Issues:
1. Ensure backend is running: `ps aux | grep "python.*main.py"`
2. Check backend logs: `tail -f backend/backend.log`
3. Verify port availability: `lsof -i :8000`

### MCP Server Issues:
1. Check Docker status: `docker ps`
2. View MCP logs: `docker-compose logs [server-name]`
3. Restart specific server: `docker-compose restart [server-name]`

### Integration Issues:
1. Verify environment variables are set
2. Check API keys are valid
3. Test connections individually using curl commands above

## 📈 Next Steps

1. **Customize Dashboards**: Add specific visualizations for your use case
2. **Set Up Alerts**: Configure notifications for critical metrics
3. **Add User Permissions**: Set up role-based access in Retool
4. **Enable Real-time Updates**: Configure WebSocket connections
5. **Create Custom Reports**: Build report generation capabilities

## 🔗 Useful Links

- Retool Documentation: https://docs.retool.com
- Sophia AI Docs: /docs/
- API Documentation: http://localhost:8000/docs
- Support: support@payready.com

---

**Deployment Status**: ✅ Complete
**Generated by**: Sophia AI Deployment System
