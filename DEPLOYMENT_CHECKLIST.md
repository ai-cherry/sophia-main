# Sophia AI - Production Deployment Checklist

## 📋 Pre-Deployment Requirements

### 1. API Keys Configuration
You need to configure the following API keys in your `.env` file:

#### Required API Keys:
- [ ] **OPENAI_API_KEY** - Get from https://platform.openai.com/api-keys
- [ ] **HUBSPOT_API_KEY** - Get from HubSpot Settings > Integrations > API Key
- [ ] **GONG_API_KEY** - Get from Gong.io Settings > API
- [ ] **GONG_API_SECRET** - Get from Gong.io Settings > API
- [ ] **SLACK_BOT_TOKEN** - Get from https://api.slack.com/apps (starts with xoxb-)
- [ ] **SLACK_SIGNING_SECRET** - Get from Slack App Settings > Basic Information

#### Optional but Recommended:
- [ ] **ANTHROPIC_API_KEY** - For Claude AI integration
- [ ] **PINECONE_API_KEY** - Already configured in env.example
- [ ] **WEAVIATE_API_KEY** - For Weaviate vector database

### 2. Security Configuration
- [ ] Generate new **SECRET_KEY** (run: `python -c "import secrets; print(secrets.token_urlsafe(64))"`)
- [ ] Generate new **SOPHIA_MASTER_KEY** (same command as above)
- [ ] Change **ADMIN_PASSWORD** from default 'admin123'

### 3. Database Setup
- [ ] Verify PostgreSQL connection (150.230.47.71:5432)
- [ ] Verify Redis connection (150.230.47.71:6379)
- [ ] Run database migrations

## 🚀 Deployment Steps

### Step 1: Configure Environment
```bash
# Edit your .env file with all required API keys
nano .env

# Or use the configuration helper
python3 scripts/configure_deployment.py
```

### Step 2: Install Dependencies
```bash
# Install Python dependencies
make install

# Or manually:
pip install -r requirements.txt
cd frontend && pnpm install
```

### Step 3: Database Setup
```bash
# Run database migrations
make db-migrate

# Verify database connection
python -c "
import psycopg2
conn = psycopg2.connect(
    host='150.230.47.71',
    port=5432,
    user='sophia',
    password='sophia_pass',
    database='sophia_payready'
)
print('✅ PostgreSQL connected!')
conn.close()
"
```

### Step 4: Run Tests
```bash
# Run all tests to ensure everything is working
make test

# Or run specific tests
pytest tests/test_auth.py -v
```

### Step 5: Local Verification
```bash
# Start in development mode to verify
make dev

# Test endpoints:
# - Frontend: http://localhost:3000
# - Backend: http://localhost:5000
# - Health: http://localhost:5000/health
```

### Step 6: Production Configuration
```bash
# Set environment to production
export SOPHIA_ENV=production

# Update .env file:
# SOPHIA_ENV=production
```

### Step 7: Docker Deployment (Option A)
```bash
# Build Docker images
make docker-build

# Start containers
make docker-up

# Verify containers are running
docker ps
```

### Step 8: Lambda Labs Deployment (Option B)
```bash
# Configure Pulumi
cd infrastructure
pulumi login
pulumi stack init sophia-production

# Set configuration
pulumi config set aws:region us-west-1
pulumi config set instance_type gpu.a100.1x
pulumi config set db_password <secure_password> --secret
pulumi config set secret_key <your_secret_key> --secret

# Deploy infrastructure
pulumi up --yes

# Note the outputs:
# - app_url
# - ssh_command
# - monitoring urls
```

### Step 9: Post-Deployment Verification
```bash
# Check application health
curl https://your-domain.com/health

# Test authentication
curl -X POST https://your-domain.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"your_password"}'

# Check monitoring
# - Prometheus: https://your-domain.com:9090
# - Grafana: https://your-domain.com:3000
```

## 🔒 Security Checklist

- [ ] All default passwords changed
- [ ] SSL/TLS certificates configured
- [ ] Firewall rules configured
- [ ] API rate limiting enabled
- [ ] Audit logging enabled
- [ ] Backup strategy implemented

## 📊 Monitoring Setup

### Configure Alerts
- [ ] Set up CPU usage alerts (>80%)
- [ ] Set up memory usage alerts (>90%)
- [ ] Set up disk space alerts (>85%)
- [ ] Configure application error alerts
- [ ] Set up API response time alerts (>2s)

### Configure Dashboards
- [ ] Import Grafana dashboards
- [ ] Set up business metrics dashboard
- [ ] Configure agent performance dashboard
- [ ] Create system health dashboard

## 🔄 Backup & Recovery

- [ ] Configure automated PostgreSQL backups
- [ ] Set up Redis persistence
- [ ] Configure S3 backup bucket
- [ ] Test restore procedure
- [ ] Document recovery process

## 📝 Documentation

- [ ] Update API documentation
- [ ] Create user guide
- [ ] Document deployment process
- [ ] Create runbook for common issues
- [ ] Update team wiki

## ✅ Final Checks

- [ ] All tests passing
- [ ] All integrations connected
- [ ] Monitoring active
- [ ] Backups configured
- [ ] Team trained on new system
- [ ] Support channels established

## 🚨 Rollback Plan

If issues occur during deployment:

1. **Immediate Rollback**
   ```bash
   # Docker
   docker-compose down
   docker-compose -f docker-compose.backup.yml up -d
   
   # Pulumi
   pulumi destroy --yes
   pulumi stack select sophia-previous
   pulumi up --yes
   ```

2. **Database Rollback**
   ```bash
   # Restore from backup
   pg_restore -h 150.230.47.71 -U sophia -d sophia_payready backup.sql
   ```

3. **Communication**
   - Notify team via Slack
   - Update status page
   - Document issues for post-mortem

## 📞 Support Contacts

- **Technical Lead**: [Your Name]
- **DevOps**: [DevOps Contact]
- **On-Call**: [On-Call Phone]
- **Escalation**: [Manager Contact]

---

**Remember**: Take your time, test thoroughly, and don't hesitate to ask for help if needed! 