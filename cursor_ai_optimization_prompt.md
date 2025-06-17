# Cursor AI Prompt: Optimize Sophia Gong.io Integration & Interactive Admin Interface

## 🎯 PROJECT CONTEXT

You are working on **Sophia**, Pay Ready's advanced business intelligence platform for the apartment industry. We have successfully implemented a foundational Gong.io integration that extracts 84 users and provides conversation intelligence, but need to optimize the setup and create an interactive admin interface for enhanced data management.

## 📊 CURRENT STATUS

### ✅ ACHIEVEMENTS
- **Live Gong API Connection**: Successfully authenticated with custom base URL (https://us-70092.api.gong.io/v2)
- **84 Users Extracted**: Complete user profiles with apartment industry relevance scoring
- **Enhanced Database Schema**: PostgreSQL with 16 tables for comprehensive conversation intelligence
- **Admin Interface Foundation**: React frontend + Flask backend with basic search functionality
- **OAuth Framework**: Prepared for enhanced data access (transcripts, media, webhooks)
- **GitHub Integration**: All code committed to https://github.com/ai-cherry/sophia-main

### 🔧 CURRENT ISSUES
1. **Gong Calls API**: Requires specific parameters (clientUniqueId, actualStart, parties, direction)
2. **Credential Management**: Need proper GitHub/Pulumi ESC integration for production
3. **Admin Interface**: Needs interactive schema mapping and data definition capabilities
4. **OAuth Implementation**: Ready for development to unlock enhanced features

## 🎯 OPTIMIZATION OBJECTIVES

### 1. **Gong.io API Optimization**
**Goal**: Fix calls API and implement comprehensive data extraction

**Current API Endpoints Available**:
- ✅ `/users` - Working (84 users extracted)
- ❌ `/calls` - Needs parameter fix
- ✅ `/workspaces` - Working (2 workspaces)
- ❌ `/library/folders` - Bad request error

**Required OAuth Scopes for Enhanced Features**:
```
api:calls:read:extensive - Enhanced call data with interaction stats
api:calls:read:transcript - Full conversation transcripts
api:calls:read:media-url - Audio/video access
api:users:read - User data (working)
api:workspaces:read - Workspace data (working)
```

**Tasks**:
- [ ] Fix calls API parameter requirements
- [ ] Implement OAuth flow for enhanced scopes
- [ ] Test extensive call data extraction
- [ ] Enable transcript and media access

### 2. **GitHub/Pulumi Credential Management**
**Goal**: Secure, automated credential management for production deployment

**Current Credentials**:
```
GONG_ACCESS_KEY: EX5L7AKSGQBOPNK66TDYVVEAKBVQ6IPK
GONG_CLIENT_SECRET: eyJhbGciOiJIUzI1NiJ9...
Base URL: https://us-70092.api.gong.io/v2
```

**Existing Infrastructure**:
- GitHub organization-level secrets
- Pulumi ESC environment configuration
- Automated deployment workflows

**Tasks**:
- [ ] Integrate Gong credentials into GitHub secrets
- [ ] Update Pulumi ESC environment with Gong configuration
- [ ] Create secure deployment pipeline
- [ ] Test credential rotation and management

### 3. **Interactive Admin Interface Enhancement**
**Goal**: Natural language interface for schema mapping and data definitions

**Current Admin Interface**:
- React frontend with conversation search
- Flask backend with PostgreSQL integration
- Basic filtering and dashboard functionality
- Manual email upload system

**Enhancement Requirements**:
- **Interactive Schema Mapping**: Visual interface for mapping Gong fields to Sophia schema
- **Natural Language Data Definitions**: Chat-like interface for defining business rules
- **Real-time Schema Updates**: Dynamic database schema modifications
- **Data Quality Monitoring**: Automated validation and quality scoring
- **Business Intelligence Configuration**: Custom apartment industry analytics

**Proposed Features**:
```
1. Schema Mapping Interface:
   - Drag-and-drop field mapping
   - Real-time preview of data transformations
   - Validation rules and data type conversion
   - Apartment industry-specific field suggestions

2. Natural Language Configuration:
   - "Map Gong call titles to apartment relevance scores"
   - "Create alerts for competitor mentions in calls"
   - "Define high-value opportunity criteria"
   - "Set up automated follow-up recommendations"

3. Interactive Data Definitions:
   - Conversational interface for business rule creation
   - Visual workflow builder for data processing
   - A/B testing for different scoring algorithms
   - Real-time impact analysis of configuration changes
```

### 4. **OAuth Implementation Strategy**
**Goal**: Unlock enhanced Gong features through OAuth app development

**OAuth Benefits**:
- **Full Transcripts**: Complete conversation transcripts with speaker identification
- **Media Access**: Direct audio/video file access for advanced analysis
- **Real-time Webhooks**: Instant notifications for new conversations
- **Enhanced Statistics**: Detailed interaction and engagement metrics
- **Multi-tenant Support**: Scalable customer onboarding

**Implementation Approach**:
- Create Gong OAuth application
- Implement authorization flow
- Build multi-tenant architecture
- Prepare for Gong marketplace submission

## 🛠️ TECHNICAL ARCHITECTURE

### Current Stack:
```
Frontend: React + Vite (localhost:5173)
Backend: Flask + asyncpg (localhost:5000)
Database: PostgreSQL (sophia_enhanced)
API Integration: Gong.io REST API
Deployment: GitHub Actions + Pulumi ESC
```

### Key Files:
```
sophia_fixed_gong_extraction.py - Main extraction script (84 users working)
sophia_admin_api/src/main.py - Flask backend API
sophia_admin_frontend/src/App.jsx - React admin interface
sophia_enhanced_schema.py - Database schema deployment
backend/config/secure_config.py - Credential management
.github/workflows/deploy-secure.yml - Deployment pipeline
```

## 🎯 CURSOR AI TASKS

### **Priority 1: Fix Gong Calls API (Immediate)**
1. **Analyze API Requirements**: Review Gong API documentation for calls endpoint parameter requirements
2. **Fix Parameter Format**: Implement proper clientUniqueId, actualStart, parties, direction parameters
3. **Test Data Extraction**: Validate conversation data extraction with apartment industry analysis
4. **Database Integration**: Ensure extracted calls populate Sophia database correctly

### **Priority 2: Interactive Admin Interface (High)**
1. **Schema Mapping Component**: Create visual interface for Gong-to-Sophia field mapping
2. **Natural Language Interface**: Implement chat-like interface for data definition configuration
3. **Real-time Updates**: Enable dynamic schema modifications without downtime
4. **Business Intelligence Dashboard**: Enhanced analytics with apartment industry insights

### **Priority 3: Credential Management (High)**
1. **GitHub Secrets Integration**: Secure Gong credentials in GitHub organization secrets
2. **Pulumi ESC Configuration**: Update environment with Gong API configuration
3. **Automated Deployment**: Create secure deployment pipeline with credential management
4. **Production Environment**: Deploy admin interface with proper security

### **Priority 4: OAuth Implementation (Medium)**
1. **Gong OAuth App**: Create OAuth application for enhanced API access
2. **Authorization Flow**: Implement secure OAuth flow with token management
3. **Enhanced Features**: Unlock transcripts, media, and webhook capabilities
4. **Multi-tenant Architecture**: Prepare for customer onboarding and scaling

## 📋 SPECIFIC IMPLEMENTATION QUESTIONS

### **Gong API Optimization**:
1. What are the exact parameter requirements for the Gong calls API?
2. How should we structure the API calls to extract maximum conversation data?
3. What's the best approach for handling API rate limits and pagination?
4. How can we optimize apartment industry relevance scoring algorithms?

### **Interactive Admin Interface**:
1. What's the best UX pattern for natural language schema mapping?
2. How should we implement real-time database schema updates safely?
3. What visualization components work best for conversation intelligence data?
4. How can we make the interface intuitive for non-technical apartment industry users?

### **Credential Management**:
1. What's the optimal GitHub/Pulumi ESC configuration for Gong credentials?
2. How should we handle credential rotation and security updates?
3. What's the best practice for environment-specific credential management?
4. How can we ensure secure deployment without exposing sensitive data?

### **OAuth Strategy**:
1. Should we prioritize OAuth app development or optimize current API access first?
2. What's the timeline and effort required for Gong marketplace submission?
3. How should we structure the multi-tenant architecture for customer onboarding?
4. What are the business benefits and ROI projections for OAuth implementation?

## 🎯 SUCCESS METRICS

### **Technical Metrics**:
- [ ] 100% Gong API endpoint functionality (currently 66% - users/workspaces working)
- [ ] Real conversation data extraction (currently 0 calls, target: 100+ calls)
- [ ] Sub-second admin interface response times
- [ ] 99.9% uptime for production deployment

### **Business Intelligence Metrics**:
- [ ] Apartment industry relevance scoring accuracy >90%
- [ ] Competitive threat detection and alerting
- [ ] Deal pipeline tracking and opportunity identification
- [ ] Customer conversation intelligence ROI demonstration

### **User Experience Metrics**:
- [ ] Intuitive schema mapping interface (non-technical user friendly)
- [ ] Natural language configuration success rate >95%
- [ ] Real-time data updates and synchronization
- [ ] Comprehensive apartment industry analytics dashboard

## 🚀 GETTING STARTED

1. **Clone Repository**: `git clone https://github.com/ai-cherry/sophia-main.git`
2. **Review Current Implementation**: Examine `sophia_fixed_gong_extraction.py` for API integration
3. **Test Admin Interface**: Run React frontend and Flask backend locally
4. **Analyze Database Schema**: Review PostgreSQL tables and apartment industry data model
5. **Plan Optimization Strategy**: Prioritize tasks based on business impact and technical complexity

## 💡 STRATEGIC CONTEXT

**Pay Ready** is a B2B technology provider for the apartment industry, selling conversation intelligence solutions to apartment owners and managers. The Sophia platform provides:

- **AI-powered conversation analysis** for apartment industry sales and success teams
- **Competitive intelligence** tracking and threat assessment
- **Deal pipeline optimization** through conversation insights
- **Automated follow-up recommendations** based on apartment industry best practices
- **Business intelligence dashboard** with apartment-specific metrics and KPIs

**Success with this Gong integration positions Pay Ready as the definitive conversation intelligence platform for the apartment industry, with potential for significant revenue growth and market leadership.**

---

**Ready to optimize Sophia's Gong.io integration and create the most sophisticated apartment industry conversation intelligence platform available!** 🏆

