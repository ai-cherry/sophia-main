#!/usr/bin/env python3
"""
Quick Setup Script for Secure Gong Integration
Automated setup and validation of the complete Gong integration
"""

import os
import subprocess
import json
import requests
import base64
from datetime import datetime
import sys

class GongIntegrationSetup:
    """
    Automated setup and validation for secure Gong integration
    """
    
    def __init__(self):
        self.setup_results = {
            "timestamp": datetime.utcnow().isoformat(),
            "steps_completed": [],
            "errors": [],
            "warnings": [],
            "next_actions": []
        }
        
        # Configuration
        self.github_repo = "ai-cherry/sophia-main"
        self.required_secrets = [
            "GONG_ACCESS_KEY",
            "GONG_CLIENT_SECRET"
        ]
        
        self.gong_credentials = {
            "access_key": "EX5L7AKSGQBOPNK66TDYVVEAKBVQ6IPK",
            "client_secret": "eyJhbGciOiJIUzI1NiJ9.eyJleHAiOjIwNjU1NDc5ODksImFjY2Vzc0tleSI6IkVYNUw3QUtTR1FCT1BOSzY2VERZVlZFQUtCVlE2SVBLIn0.djgpFaMkt94HJHYHKbymM2D5aj_tQNJMV3aY_rwOSTY",
            "base_url": "https://us-70092.api.gong.io"
        }
    
    def log_step(self, step_name: str, success: bool = True, details: str = ""):
        """Log setup step completion"""
        status = "✅" if success else "❌"
        print(f"{status} {step_name}")
        if details:
            print(f"   {details}")
        
        self.setup_results["steps_completed"].append({
            "step": step_name,
            "success": success,
            "details": details,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        if not success:
            self.setup_results["errors"].append(f"{step_name}: {details}")
    
    def check_prerequisites(self):
        """Check system prerequisites"""
        print("\n🔍 CHECKING PREREQUISITES")
        print("=" * 40)
        
        # Check Python version
        python_version = sys.version_info
        if python_version.major >= 3 and python_version.minor >= 8:
            self.log_step("Python 3.8+ installed", True, f"Version: {python_version.major}.{python_version.minor}")
        else:
            self.log_step("Python 3.8+ required", False, f"Current: {python_version.major}.{python_version.minor}")
        
        # Check required packages
        required_packages = ["requests", "asyncpg", "flask", "flask-cors"]
        for package in required_packages:
            try:
                __import__(package.replace("-", "_"))
                self.log_step(f"Package {package} installed", True)
            except ImportError:
                self.log_step(f"Package {package} missing", False, f"Run: pip install {package}")
        
        # Check PostgreSQL
        try:
            result = subprocess.run(["psql", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                self.log_step("PostgreSQL installed", True, result.stdout.strip())
            else:
                self.log_step("PostgreSQL not found", False, "Install PostgreSQL")
        except FileNotFoundError:
            self.log_step("PostgreSQL not found", False, "Install PostgreSQL")
        
        # Check Git
        try:
            result = subprocess.run(["git", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                self.log_step("Git installed", True, result.stdout.strip())
            else:
                self.log_step("Git not found", False, "Install Git")
        except FileNotFoundError:
            self.log_step("Git not found", False, "Install Git")
    
    def validate_gong_credentials(self):
        """Validate Gong API credentials"""
        print("\n🔐 VALIDATING GONG CREDENTIALS")
        print("=" * 40)
        
        try:
            # Create authorization header
            credentials = f"{self.gong_credentials['access_key']}:{self.gong_credentials['client_secret']}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()
            
            headers = {
                'Authorization': f'Basic {encoded_credentials}',
                'Content-Type': 'application/json'
            }
            
            # Test users endpoint
            response = requests.get(
                f"{self.gong_credentials['base_url']}/v2/users",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                user_count = len(data.get('users', []))
                self.log_step("Gong API authentication", True, f"Access to {user_count} users")
                
                # Test calls endpoint
                response = requests.get(
                    f"{self.gong_credentials['base_url']}/v2/calls",
                    headers=headers,
                    params={"fromDateTime": "2024-01-01T00:00:00Z", "toDateTime": "2024-12-31T23:59:59Z"},
                    timeout=30
                )
                
                if response.status_code == 200:
                    calls_data = response.json()
                    call_count = len(calls_data.get('calls', []))
                    self.log_step("Gong calls access", True, f"Access to {call_count} calls")
                else:
                    self.log_step("Gong calls access", False, f"Status: {response.status_code}")
                
            else:
                self.log_step("Gong API authentication", False, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_step("Gong API validation", False, str(e))
    
    def setup_database(self):
        """Setup PostgreSQL database"""
        print("\n🗄️ SETTING UP DATABASE")
        print("=" * 40)
        
        try:
            # Start PostgreSQL service
            result = subprocess.run(["sudo", "service", "postgresql", "start"], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                self.log_step("PostgreSQL service started", True)
            else:
                self.log_step("PostgreSQL service start", False, result.stderr)
            
            # Create database
            result = subprocess.run(["sudo", "-u", "postgres", "createdb", "sophia_enhanced"], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                self.log_step("Database sophia_enhanced created", True)
            elif "already exists" in result.stderr:
                self.log_step("Database sophia_enhanced exists", True, "Already created")
            else:
                self.log_step("Database creation", False, result.stderr)
            
            # Deploy schema
            if os.path.exists("sophia_enhanced_schema.py"):
                result = subprocess.run(["python3", "sophia_enhanced_schema.py"], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    self.log_step("Database schema deployed", True)
                else:
                    self.log_step("Schema deployment", False, result.stderr)
            else:
                self.log_step("Schema file not found", False, "sophia_enhanced_schema.py missing")
                
        except Exception as e:
            self.log_step("Database setup", False, str(e))
    
    def test_api_integration(self):
        """Test API integration components"""
        print("\n🧪 TESTING API INTEGRATION")
        print("=" * 40)
        
        # Test enhanced Gong API tester
        if os.path.exists("enhanced_gong_api_tester.py"):
            try:
                result = subprocess.run(["python3", "enhanced_gong_api_tester.py"], 
                                      capture_output=True, text=True, timeout=60)
                if result.returncode == 0:
                    self.log_step("Enhanced API testing", True, "All endpoints tested")
                else:
                    self.log_step("Enhanced API testing", False, result.stderr)
            except subprocess.TimeoutExpired:
                self.log_step("Enhanced API testing", False, "Timeout after 60 seconds")
            except Exception as e:
                self.log_step("Enhanced API testing", False, str(e))
        else:
            self.log_step("API tester not found", False, "enhanced_gong_api_tester.py missing")
        
        # Test Flask API (if running)
        try:
            response = requests.get("http://localhost:5000/api/health", timeout=5)
            if response.status_code == 200:
                self.log_step("Flask API health check", True, "API responding")
            else:
                self.log_step("Flask API health check", False, f"Status: {response.status_code}")
        except requests.exceptions.RequestException:
            self.log_step("Flask API not running", False, "Start with: python sophia_admin_api/src/main.py")
        
        # Test React frontend (if running)
        try:
            response = requests.get("http://localhost:5173", timeout=5)
            if response.status_code == 200:
                self.log_step("React frontend health check", True, "Frontend responding")
            else:
                self.log_step("React frontend health check", False, f"Status: {response.status_code}")
        except requests.exceptions.RequestException:
            self.log_step("React frontend not running", False, "Start with: cd sophia_admin_frontend && npm run dev")
    
    def check_github_integration(self):
        """Check GitHub integration status"""
        print("\n🔗 CHECKING GITHUB INTEGRATION")
        print("=" * 40)
        
        # Check if we're in a git repository
        try:
            result = subprocess.run(["git", "status"], capture_output=True, text=True)
            if result.returncode == 0:
                self.log_step("Git repository status", True, "In git repository")
                
                # Check remote origin
                result = subprocess.run(["git", "remote", "get-url", "origin"], 
                                      capture_output=True, text=True)
                if "sophia-main" in result.stdout:
                    self.log_step("GitHub repository", True, "Connected to sophia-main")
                else:
                    self.log_step("GitHub repository", False, f"Remote: {result.stdout.strip()}")
                
                # Check for workflow files
                if os.path.exists(".github/workflows/deploy-secure-gong.yml"):
                    self.log_step("GitHub Actions workflow", True, "deploy-secure-gong.yml found")
                else:
                    self.log_step("GitHub Actions workflow", False, "deploy-secure-gong.yml missing")
                    
            else:
                self.log_step("Git repository", False, "Not in a git repository")
                
        except Exception as e:
            self.log_step("GitHub integration check", False, str(e))
    
    def generate_next_actions(self):
        """Generate recommended next actions"""
        print("\n🎯 RECOMMENDED NEXT ACTIONS")
        print("=" * 40)
        
        # Analyze setup results
        errors = self.setup_results["errors"]
        
        if not errors:
            print("✅ Setup completed successfully!")
            next_actions = [
                "Deploy Flask API: cd sophia_admin_api && python src/main.py",
                "Deploy React frontend: cd sophia_admin_frontend && npm run dev",
                "Test admin interface: http://localhost:5173",
                "Begin OAuth app development for enhanced features"
            ]
        else:
            print("⚠️ Setup completed with issues. Address the following:")
            next_actions = []
            
            if any("PostgreSQL" in error for error in errors):
                next_actions.append("Install and configure PostgreSQL")
            
            if any("Package" in error for error in errors):
                next_actions.append("Install missing Python packages: pip install -r requirements.txt")
            
            if any("Gong API" in error for error in errors):
                next_actions.append("Verify Gong API credentials and permissions")
            
            if any("Database" in error for error in errors):
                next_actions.append("Fix database configuration and schema deployment")
        
        # OAuth development recommendations
        next_actions.extend([
            "Create Gong developer account: https://developers.gong.io/",
            "Register OAuth application for enhanced features",
            "Implement transcript and media access capabilities",
            "Set up real-time webhook infrastructure"
        ])
        
        self.setup_results["next_actions"] = next_actions
        
        for i, action in enumerate(next_actions, 1):
            print(f"   {i}. {action}")
    
    def save_setup_report(self):
        """Save detailed setup report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"gong_integration_setup_report_{timestamp}.json"
        
        with open(report_file, 'w') as f:
            json.dump(self.setup_results, f, indent=2)
        
        print(f"\n📁 Setup report saved: {report_file}")
        return report_file
    
    def run_complete_setup(self):
        """Run complete setup and validation"""
        print("🚀 GONG INTEGRATION SETUP & VALIDATION")
        print("=" * 50)
        
        # Run all setup steps
        self.check_prerequisites()
        self.validate_gong_credentials()
        self.setup_database()
        self.test_api_integration()
        self.check_github_integration()
        self.generate_next_actions()
        
        # Save report
        report_file = self.save_setup_report()
        
        # Summary
        total_steps = len(self.setup_results["steps_completed"])
        successful_steps = sum(1 for step in self.setup_results["steps_completed"] if step["success"])
        
        print(f"\n📊 SETUP SUMMARY")
        print(f"   Total steps: {total_steps}")
        print(f"   Successful: {successful_steps}")
        print(f"   Failed: {total_steps - successful_steps}")
        print(f"   Success rate: {(successful_steps/total_steps*100):.1f}%")
        
        if successful_steps == total_steps:
            print("\n🎉 Setup completed successfully! Ready for production deployment.")
        else:
            print(f"\n⚠️ Setup completed with {total_steps - successful_steps} issues. Review next actions above.")
        
        return self.setup_results

def main():
    """Main execution function"""
    setup = GongIntegrationSetup()
    results = setup.run_complete_setup()
    return results

if __name__ == "__main__":
    main()

