#!/usr/bin/env python3
"""
Quick test script to verify Sophia AI setup
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def check_env():
    """Check environment configuration"""
    print("🔍 Checking environment configuration...\n")
    
    required_keys = {
        "SECRET_KEY": "Security key for sessions",
        "ADMIN_PASSWORD": "Admin login password",
        "POSTGRES_HOST": "PostgreSQL host",
        "REDIS_HOST": "Redis host"
    }
    
    ai_keys = {
        "OPENAI_API_KEY": "OpenAI API",
        "ANTHROPIC_API_KEY": "Anthropic API", 
        "PORTKEY_API_KEY": "Portkey gateway",
        "OPENROUTER_API_KEY": "OpenRouter"
    }
    
    missing = []
    configured = []
    
    # Check required keys
    print("📋 Required Configuration:")
    for key, desc in required_keys.items():
        value = os.getenv(key, "")
        if value and not value.startswith("#"):
            print(f"  ✅ {key}: {desc} - Configured")
            configured.append(key)
        else:
            print(f"  ❌ {key}: {desc} - Missing")
            missing.append(key)
    
    # Check AI providers
    print("\n🤖 AI Providers (need at least one):")
    ai_configured = False
    for key, desc in ai_keys.items():
        value = os.getenv(key, "")
        if value and not value.startswith("#"):
            print(f"  ✅ {key}: {desc} - Configured")
            configured.append(key)
            ai_configured = True
        else:
            print(f"  ⚪ {key}: {desc} - Not configured")
    
    if not ai_configured:
        print("\n⚠️  No AI provider configured!")
        missing.append("AI_PROVIDER")
    
    return missing, configured

def test_imports():
    """Test Python imports"""
    print("\n🐍 Testing Python imports...")
    try:
        from backend.config.settings import settings
        print("  ✅ Configuration module loaded")
        
        # Show enabled features
        features = settings.get_enabled_features()
        enabled = [k for k, v in features.items() if v]
        if enabled:
            print(f"  ✅ Enabled features: {', '.join(enabled)}")
        
        return True
    except Exception as e:
        print(f"  ❌ Import error: {e}")
        return False

def main():
    print("🚀 Sophia AI Setup Verification")
    print("=" * 40)
    
    # Check .env file
    if not Path(".env").exists():
        print("❌ No .env file found! Run: python3 scripts/setup_from_github.py")
        return
    
    # Check environment
    missing, configured = check_env()
    
    # Test imports
    if configured:
        imports_ok = test_imports()
    
    # Summary
    print("\n📊 Summary:")
    if not missing and imports_ok:
        print("✅ Your local environment is ready!")
        print("\nNext steps:")
        print("1. Start databases: docker-compose up -d sophia-postgres sophia-redis")
        print("2. Run the app: cd backend && python3 app/main.py")
        print("3. Access API: http://localhost:5000/api/health")
    else:
        print("⚠️  Setup incomplete!")
        print("\nTo complete setup:")
        if "SECRET_KEY" in missing:
            print("1. Generate SECRET_KEY:")
            import secrets
            print(f"   SECRET_KEY={secrets.token_hex(32)}")
        if "ADMIN_PASSWORD" in missing:
            print("2. Set ADMIN_PASSWORD to something secure")
        if "AI_PROVIDER" in missing:
            print("3. Add at least one AI provider key (OpenAI, Anthropic, or Portkey+OpenRouter)")
        print("\nEdit your .env file with actual values from your organization secrets.")
        print("Organization secrets page: https://github.com/organizations/ai-cherry/settings/secrets/actions")

if __name__ == "__main__":
    main() 