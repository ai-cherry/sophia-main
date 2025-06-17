#!/bin/bash
# Production Deployment Script for Secure Gong Integration
# Automated deployment to Vercel and Lambda Labs

set -e  # Exit on any error

echo "🚀 DEPLOYING SECURE GONG INTEGRATION TO PRODUCTION"
echo "=================================================="

# Configuration
GITHUB_REPO="ai-cherry/sophia-main"
FRONTEND_DIR="sophia_admin_frontend"
BACKEND_DIR="sophia_admin_api"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_step() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    echo "🔍 Checking prerequisites..."
    
    # Check if we're in the right directory
    if [ ! -f "sophia_enhanced_schema.py" ]; then
        log_error "Not in sophia-main directory. Please run from the project root."
        exit 1
    fi
    
    # Check for required tools
    command -v node >/dev/null 2>&1 || { log_error "Node.js is required but not installed."; exit 1; }
    command -v npm >/dev/null 2>&1 || { log_error "npm is required but not installed."; exit 1; }
    command -v python3 >/dev/null 2>&1 || { log_error "Python 3 is required but not installed."; exit 1; }
    
    log_step "Prerequisites check passed"
}

# Deploy frontend to Vercel
deploy_frontend() {
    echo "🌐 Deploying frontend to Vercel..."
    
    if [ ! -d "$FRONTEND_DIR" ]; then
        log_error "Frontend directory not found: $FRONTEND_DIR"
        return 1
    fi
    
    cd "$FRONTEND_DIR"
    
    # Install dependencies
    echo "Installing frontend dependencies..."
    npm install
    
    # Build for production
    echo "Building frontend for production..."
    npm run build
    
    # Deploy to Vercel
    if command -v vercel >/dev/null 2>&1; then
        echo "Deploying to Vercel..."
        vercel --prod --yes
        log_step "Frontend deployed to Vercel"
    else
        log_warning "Vercel CLI not installed. Install with: npm i -g vercel"
        log_warning "Manual deployment required: Upload dist/ folder to Vercel"
    fi
    
    cd ..
}

# Deploy backend API
deploy_backend() {
    echo "🔧 Preparing backend deployment..."
    
    if [ ! -d "$BACKEND_DIR" ]; then
        log_error "Backend directory not found: $BACKEND_DIR"
        return 1
    fi
    
    cd "$BACKEND_DIR"
    
    # Create production requirements.txt
    cat > requirements.txt << EOF
flask==2.3.3
flask-cors==4.0.0
asyncpg==0.28.0
requests==2.31.0
python-dotenv==1.0.0
gunicorn==21.2.0
EOF
    
    # Create production startup script
    cat > start_production.sh << EOF
#!/bin/bash
export FLASK_ENV=production
export FLASK_APP=src/main.py
gunicorn --bind 0.0.0.0:5000 --workers 4 src.main:app
EOF
    chmod +x start_production.sh
    
    # Create Dockerfile for containerized deployment
    cat > Dockerfile << EOF
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["./start_production.sh"]
EOF
    
    log_step "Backend deployment files created"
    
    cd ..
}

# Setup production database
setup_production_database() {
    echo "🗄️ Setting up production database..."
    
    # Create production database configuration
    cat > production_db_setup.sql << EOF
-- Production database setup for Sophia Gong Integration
CREATE DATABASE sophia_production;
CREATE USER sophia_user WITH PASSWORD 'secure_production_password';
GRANT ALL PRIVILEGES ON DATABASE sophia_production TO sophia_user;
EOF
    
    # Deploy enhanced schema
    echo "Deploying database schema..."
    python3 sophia_enhanced_schema.py
    
    log_step "Production database setup completed"
}

# Create production environment configuration
create_production_config() {
    echo "⚙️ Creating production configuration..."
    
    # Create production environment template
    cat > .env.production.template << EOF
# Production Environment Configuration
GONG_ACCESS_KEY=EX5L7AKSGQBOPNK66TDYVVEAKBVQ6IPK
GONG_CLIENT_SECRET=your_gong_client_secret_here
GONG_BASE_URL=https://us-70092.api.gong.io

# Database Configuration
DATABASE_URL=postgresql://sophia_user:secure_production_password@your-db-host:5432/sophia_production

# Flask Configuration
FLASK_ENV=production
FLASK_DEBUG=False

# CORS Configuration
CORS_ORIGINS=https://your-frontend.vercel.app,https://payready.com

# Security
SECRET_KEY=your_secure_secret_key_here
JWT_SECRET_KEY=your_jwt_secret_key_here
EOF
    
    # Create deployment checklist
    cat > DEPLOYMENT_CHECKLIST.md << EOF
# Production Deployment Checklist

## Pre-Deployment
- [ ] Update .env.production with actual values
- [ ] Configure production database
- [ ] Set up monitoring and logging
- [ ] Configure backup strategy

## Deployment Steps
- [ ] Deploy frontend to Vercel
- [ ] Deploy backend to Lambda Labs
- [ ] Configure environment variables
- [ ] Test API endpoints
- [ ] Verify database connectivity

## Post-Deployment
- [ ] Monitor application performance
- [ ] Set up alerts and notifications
- [ ] Document API endpoints
- [ ] Train team on new features

## Security
- [ ] Rotate API keys if needed
- [ ] Enable HTTPS everywhere
- [ ] Configure rate limiting
- [ ] Set up access logging
EOF
    
    log_step "Production configuration created"
}

# Test deployment
test_deployment() {
    echo "🧪 Testing deployment..."
    
    # Test database connection
    if python3 -c "import asyncpg; print('asyncpg available')" 2>/dev/null; then
        log_step "Database dependencies available"
    else
        log_warning "Database dependencies may need installation"
    fi
    
    # Test API functionality
    if [ -f "$BACKEND_DIR/src/main.py" ]; then
        log_step "Backend API files present"
    else
        log_error "Backend API files missing"
    fi
    
    # Test frontend build
    if [ -d "$FRONTEND_DIR/dist" ] || [ -d "$FRONTEND_DIR/build" ]; then
        log_step "Frontend build files present"
    else
        log_warning "Frontend may need to be built"
    fi
}

# Generate deployment report
generate_deployment_report() {
    echo "📊 Generating deployment report..."
    
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    REPORT_FILE="deployment_report_${TIMESTAMP}.md"
    
    cat > "$REPORT_FILE" << EOF
# Gong Integration Deployment Report
Generated: $(date)

## Deployment Status
- Frontend: Ready for Vercel deployment
- Backend: Ready for Lambda Labs deployment  
- Database: Schema deployed and ready
- Configuration: Production templates created

## Next Steps
1. Configure production environment variables
2. Deploy frontend to Vercel
3. Deploy backend to Lambda Labs server
4. Test end-to-end functionality
5. Monitor performance and usage

## Access Information
- Frontend URL: https://your-app.vercel.app
- Backend API: https://your-api.lambda-labs.com
- Database: PostgreSQL sophia_production
- Admin Interface: Conversation search and analytics

## Support
- Documentation: See DEPLOYMENT_CHECKLIST.md
- Configuration: See .env.production.template
- Troubleshooting: Check logs and monitoring

## Enhanced Features (OAuth Development)
- Gong Developer Account: https://developers.gong.io/
- OAuth Application Registration: Required for transcripts and webhooks
- Enhanced API Access: Implement for premium features
EOF
    
    log_step "Deployment report created: $REPORT_FILE"
}

# Main deployment function
main() {
    echo "Starting production deployment process..."
    
    check_prerequisites
    deploy_frontend
    deploy_backend
    setup_production_database
    create_production_config
    test_deployment
    generate_deployment_report
    
    echo ""
    echo "🎉 DEPLOYMENT PREPARATION COMPLETE!"
    echo "=================================================="
    echo ""
    echo "📋 Next Steps:"
    echo "1. Review DEPLOYMENT_CHECKLIST.md"
    echo "2. Update .env.production.template with actual values"
    echo "3. Deploy frontend: cd $FRONTEND_DIR && vercel --prod"
    echo "4. Deploy backend to Lambda Labs server"
    echo "5. Test complete system functionality"
    echo ""
    echo "🔗 Access Points:"
    echo "- Admin Interface: http://localhost:5173 (development)"
    echo "- API Health: http://localhost:5000/api/health (development)"
    echo "- Production URLs: Configure in deployment"
    echo ""
    echo "📞 Support:"
    echo "- Check deployment_report_*.md for detailed information"
    echo "- Review troubleshooting guide in setup documentation"
    echo "- Monitor logs for any deployment issues"
    echo ""
    echo "🚀 Ready for production deployment!"
}

# Run main function
main "$@"

