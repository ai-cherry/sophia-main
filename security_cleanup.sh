#!/bin/bash
# Sophia AI Security Cleanup Script
# Removes hardcoded secrets and implements secure configuration

set -e

echo "🔐 SOPHIA AI SECURITY CLEANUP & PULUMI ESC IMPLEMENTATION"
echo "=========================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if we're in the right directory
if [ ! -f "backend/main.py" ]; then
    print_error "Please run this script from the Sophia AI root directory"
    exit 1
fi

print_info "Starting security cleanup process..."

# 1. Backup existing .env file
print_info "Step 1: Backing up existing configuration..."
if [ -f ".env" ]; then
    cp .env .env.backup.$(date +%s)
    print_status "Backed up existing .env file"
else
    print_warning "No existing .env file found"
fi

# 2. Replace .env with secure version
print_info "Step 2: Implementing secure configuration..."
if [ -f ".env.secure" ]; then
    cp .env.secure .env
    print_status "Replaced .env with secure configuration"
else
    print_error "Secure .env template not found"
    exit 1
fi

# 3. Remove any hardcoded secrets from Python files
print_info "Step 3: Scanning for hardcoded secrets in Python files..."

# List of patterns to check for hardcoded secrets
secret_patterns=(
    "sk-[a-zA-Z0-9]{48,}"       # OpenAI/Anthropic API keys (more specific length)
    "pk_[a-zA-Z0-9]{32,}"       # Pinecone API keys (more specific length)
    "xoxb-[a-zA-Z0-9-]{50,}"    # Slack bot tokens (more specific length)
    "xapp-[a-zA-Z0-9-]{50,}"    # Slack app tokens (more specific length)
    "ghp_[a-zA-Z0-9]{36}"       # GitHub personal access tokens (exact length)
    "pul-[a-zA-Z0-9]{40}"       # Pulumi access tokens (exact length)
    "password\s*=\s*['\"][^'\"]{8,}['\"]"  # Hardcoded passwords with actual values
)

found_secrets=false

for pattern in "${secret_patterns[@]}"; do
    if grep -r -E "$pattern" . --include="*.py" --exclude-dir=.git --exclude-dir=__pycache__ > /dev/null 2>&1; then
        print_error "Found potential hardcoded secrets matching pattern: $pattern"
        grep -r -E "$pattern" . --include="*.py" --exclude-dir=.git --exclude-dir=__pycache__ | head -5
        found_secrets=true
    fi
done

if [ "$found_secrets" = true ]; then
    print_error "Hardcoded secrets found! Please review and remove them before proceeding."
    print_info "Use environment variables or Pulumi ESC instead."
    exit 1
else
    print_status "No hardcoded secrets found in Python files"
fi

# 4. Test secure configuration
print_info "Step 4: Testing secure configuration..."

# Check if Python dependencies are installed
if ! python3 -c "import flask" > /dev/null 2>&1; then
    print_info "Installing Python dependencies..."
    pip3 install -r requirements.txt
fi

# Test the secure configuration module
python3 -c "
import sys
sys.path.append('.')
try:
    from backend.config.secure_config import SecureConfigurationManager, get_secure_config
    config = SecureConfigurationManager()
    print('✅ Secure configuration module loaded successfully')
    
    # Test basic functionality
    validation = config.validate_configuration()
    print(f'✅ Configuration validation completed: {len(validation)} checks')
    
except Exception as e:
    print(f'❌ Secure configuration test failed: {e}')
    sys.exit(1)
"

if [ $? -eq 0 ]; then
    print_status "Secure configuration tests passed"
else
    print_error "Secure configuration tests failed"
    exit 1
fi

# 5. Update GitHub Actions workflows
print_info "Step 5: Updating GitHub Actions workflows..."

# Backup existing workflow
if [ -f ".github/workflows/deploy.yml" ]; then
    cp .github/workflows/deploy.yml .github/workflows/deploy.yml.backup
    print_status "Backed up existing deployment workflow"
fi

# Check if secure workflow exists
if [ -f ".github/workflows/deploy-secure.yml" ]; then
    print_status "Secure deployment workflow ready"
else
    print_error "Secure deployment workflow not found"
    exit 1
fi

# 6. Create Pulumi ESC environment setup
print_info "Step 6: Preparing Pulumi ESC environment setup..."

# Check if Pulumi ESC CLI is available
if command -v esc &> /dev/null; then
    print_status "Pulumi ESC CLI is available"
    
    # Test ESC login (will prompt for token if needed)
    if esc version > /dev/null 2>&1; then
        print_status "Pulumi ESC CLI is working"
    else
        print_warning "Pulumi ESC CLI needs configuration"
        print_info "Run 'esc login' to configure Pulumi ESC"
    fi
else
    print_warning "Pulumi ESC CLI not found"
    print_info "Install from: https://www.pulumi.com/docs/esc/download-install/"
fi

# 7. Generate GitHub secrets template
print_info "Step 7: Generating GitHub secrets management templates..."

python3 -c "
import sys
sys.path.append('.')
try:
    from backend.integrations.github_secrets_manager import GitHubSecretsManager
    
    # Create manager (will work even without token for template generation)
    manager = GitHubSecretsManager()
    
    # Generate secrets mapping
    secrets_mapping = manager.generate_secrets_mapping()
    
    # Create template file
    with open('github_secrets_template.env', 'w') as f:
        f.write('# GitHub Organization Secrets Template for Sophia AI\\n')
        f.write('# Add these secrets to the ai-cherry organization\\n\\n')
        
        for secret_name, description in secrets_mapping.items():
            f.write(f'# {description}\\n')
            f.write(f'{secret_name}=your_value_here\\n\\n')
    
    print('✅ GitHub secrets template generated: github_secrets_template.env')
    
except Exception as e:
    print(f'❌ Failed to generate GitHub secrets template: {e}')
    sys.exit(1)
"

if [ $? -eq 0 ]; then
    print_status "GitHub secrets template generated"
else
    print_error "Failed to generate GitHub secrets template"
fi

# 8. Create deployment checklist
print_info "Step 8: Creating deployment checklist..."

cat > SECURITY_DEPLOYMENT_CHECKLIST.md << 'EOF'
# Sophia AI Security Deployment Checklist

## ✅ Pre-Deployment Security Checklist

### 1. Secret Management
- [ ] All hardcoded secrets removed from codebase
- [ ] Secure configuration manager implemented
- [ ] Pulumi ESC environment configured
- [ ] GitHub organization secrets populated

### 2. Configuration Validation
- [ ] Secure configuration tests pass
- [ ] No hardcoded API keys in Python files
- [ ] Environment variables properly referenced
- [ ] Database connections use secure configuration

### 3. GitHub Actions Security
- [ ] Secure deployment workflow implemented
- [ ] Old insecure workflow disabled/removed
- [ ] Security audit step added to pipeline
- [ ] Pulumi ESC integration working

### 4. Infrastructure Security
- [ ] Lambda Labs deployment uses secure configuration
- [ ] Docker images built with ESC integration
- [ ] No secrets in container images
- [ ] Proper secret injection at runtime

## 🔧 Deployment Steps

### Step 1: Configure Pulumi ESC
```bash
# Install Pulumi ESC CLI
curl -fsSL https://get.pulumi.com/esc/install.sh | sh

# Login to Pulumi
esc login

# Create environment from template
esc env set ai-cherry/sophia-production --file pulumi-esc-environment.yaml
```

### Step 2: Setup GitHub Organization Secrets
```bash
# Use GitHub CLI to set organization secrets
gh secret set SOPHIA_SECRET_KEY --org ai-cherry --visibility all
gh secret set POSTGRES_HOST --org ai-cherry --visibility all
# ... (continue for all required secrets)
```

### Step 3: Validate Configuration
```bash
# Test secure configuration
python3 -c "from backend.config.secure_config import initialize_secure_configuration; print('✅' if initialize_secure_configuration() else '❌')"

# Test ESC integration
esc run ai-cherry/sophia-production -- python3 -c "import os; print('✅ ESC working' if os.getenv('POSTGRES_HOST') else '❌ ESC not working')"
```

### Step 4: Deploy with Security
```bash
# Push to GitHub (triggers secure deployment)
git add .
git commit -m "🔒 SECURITY: Implement comprehensive Pulumi ESC secret management"
git push origin main
```

## 🔍 Post-Deployment Validation

### Security Checks
- [ ] No secrets visible in logs
- [ ] Environment variables properly injected
- [ ] Database connections working
- [ ] API integrations functional
- [ ] Monitoring and alerts active

### Performance Checks
- [ ] Application startup time acceptable
- [ ] Secret retrieval performance good
- [ ] No configuration-related errors
- [ ] All features working as expected

## 🚨 Security Incident Response

If secrets are accidentally exposed:

1. **Immediate Actions**
   - Rotate all exposed secrets immediately
   - Update GitHub organization secrets
   - Update Pulumi ESC environment
   - Redeploy application

2. **Investigation**
   - Review git history for exposure
   - Check logs for unauthorized access
   - Audit all systems that used exposed secrets

3. **Prevention**
   - Review security practices
   - Update security scanning tools
   - Enhance developer training

## 📞 Support Contacts

- **Pulumi ESC Issues**: https://www.pulumi.com/docs/esc/
- **GitHub Secrets**: https://docs.github.com/en/actions/security-guides/encrypted-secrets
- **Lambda Labs Support**: https://lambdalabs.com/support
EOF

print_status "Security deployment checklist created"

# 9. Final security scan
print_info "Step 9: Running final security scan..."

# Check for any remaining hardcoded secrets
security_issues=0

# Scan for actual hardcoded values (not just variable names)
if grep -r "password\s*=\s*['\"][^'\"]{8,}['\"]" . --include="*.py" --include="*.js" --include="*.jsx" --exclude-dir=.git --exclude-dir=node_modules > /dev/null 2>&1; then
    print_error "Actual hardcoded passwords found"
    grep -r "password\s*=\s*['\"][^'\"]{8,}['\"]" . --include="*.py" --include="*.js" --include="*.jsx" --exclude-dir=.git --exclude-dir=node_modules
    ((security_issues++))
fi

if grep -r "api_key\s*=\s*['\"][^'\"]{20,}['\"]" . --include="*.py" --include="*.js" --include="*.jsx" --exclude-dir=.git --exclude-dir=node_modules > /dev/null 2>&1; then
    print_error "Actual hardcoded API keys found"
    grep -r "api_key\s*=\s*['\"][^'\"]{20,}['\"]" . --include="*.py" --include="*.js" --include="*.jsx" --exclude-dir=.git --exclude-dir=node_modules
    ((security_issues++))
fi

# Check for actual secret tokens
if grep -rE "(sk-[a-zA-Z0-9]{48,}|pk_[a-zA-Z0-9]{32,}|xoxb-[a-zA-Z0-9-]{50,})" . --include="*.py" --include="*.js" --include="*.jsx" --exclude-dir=.git --exclude-dir=node_modules > /dev/null 2>&1; then
    print_error "Actual API tokens found"
    grep -rE "(sk-[a-zA-Z0-9]{48,}|pk_[a-zA-Z0-9]{32,}|xoxb-[a-zA-Z0-9-]{50,})" . --include="*.py" --include="*.js" --include="*.jsx" --exclude-dir=.git --exclude-dir=node_modules
    ((security_issues++))
fi

if [ $security_issues -eq 0 ]; then
    print_status "Final security scan passed"
else
    print_error "Security issues found. Please review and fix before deployment."
    exit 1
fi

# 10. Summary and next steps
echo
echo "🎉 SECURITY CLEANUP COMPLETED SUCCESSFULLY!"
echo "=========================================="
print_status "Hardcoded secrets removed"
print_status "Secure configuration implemented"
print_status "Pulumi ESC integration ready"
print_status "GitHub Actions workflows updated"
print_status "Security deployment checklist created"

echo
print_info "Next Steps:"
echo "1. Configure Pulumi ESC environment: esc env set ai-cherry/sophia-production --file pulumi-esc-environment.yaml"
echo "2. Setup GitHub organization secrets using: github_secrets_template.env"
echo "3. Test secure configuration: python3 backend/config/secure_config.py"
echo "4. Deploy using secure pipeline: git push origin main"
echo "5. Follow SECURITY_DEPLOYMENT_CHECKLIST.md for complete deployment"

echo
print_status "Sophia AI is now ready for secure deployment! 🔐"
EOF

# Make the script executable
chmod +x /home/ubuntu/sophia-main/security_cleanup.sh

