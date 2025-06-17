#!/usr/bin/env python3
"""
Sophia AI Infrastructure Test Suite
Tests all API integrations, MCP servers, and gateway functionality
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Dict, List, Any

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from backend.config.secure_config import get_secure_config
from backend.integrations.unified_gateway_orchestrator import get_gateway_orchestrator

class InfrastructureTest:
    """Test suite for Sophia AI infrastructure"""
    
    def __init__(self):
        self.config = get_secure_config()
        self.orchestrator = get_gateway_orchestrator()
        self.test_results = {
            "api_configuration": {},
            "gateway_routing": {},
            "mcp_servers": {},
            "integration_tests": {}
        }
    
    def print_header(self, title: str):
        """Print a formatted header"""
        print(f"\n{'='*60}")
        print(f"  {title}")
        print(f"{'='*60}\n")
    
    def test_api_configuration(self):
        """Test API configuration status"""
        self.print_header("API Configuration Test")
        
        api_count = self.config.get_api_count()
        print(f"Total APIs Available: {api_count['total']}")
        print(f"APIs Configured: {api_count['configured']} ({api_count['percentage']}%)")
        
        # Check critical APIs
        validation = self.config.validate_critical_apis()
        print(f"\nCritical APIs Configured: {'✅ Yes' if validation['all_configured'] else '❌ No'}")
        
        if validation['missing']:
            print(f"Missing Critical Categories: {', '.join(validation['missing'])}")
        
        # List all configured APIs
        print("\nConfigured APIs by Category:")
        available_apis = self.config.get_available_apis()
        
        categories = {
            "AI/ML": ["openai", "anthropic", "huggingface", "cohere", "replicate", "together"],
            "Gateway": ["portkey", "openrouter", "kong", "arize"],
            "Vector DB": ["pinecone", "weaviate"],
            "Business": ["hubspot", "gong", "salesforce", "looker"],
            "Property": ["yardi", "realpage", "appfolio", "entrata", "costar"],
            "Analytics": ["google analytics", "mixpanel", "amplitude", "segment"],
            "Payment": ["stripe", "paypal", "plaid"],
            "Communication": ["slack bot", "twilio"]
        }
        
        for category, apis in categories.items():
            configured = [api for api in apis if available_apis.get(api, False)]
            print(f"  {category}: {len(configured)}/{len(apis)} - {', '.join(configured) if configured else 'None'}")
        
        self.test_results["api_configuration"] = {
            "total_apis": api_count['total'],
            "configured": api_count['configured'],
            "percentage": api_count['percentage'],
            "critical_apis_ok": validation['all_configured']
        }
    
    def test_gateway_routing(self):
        """Test gateway routing functionality"""
        self.print_header("Gateway Routing Test")
        
        gateway_status = self.orchestrator.get_gateway_status()
        
        print("Configured Routes:")
        for category, count in gateway_status['configured_routes'].items():
            print(f"  {category}: {count} routes")
        
        print(f"\nTotal Routes: {gateway_status['total_routes']}")
        print(f"Active Gateways: {', '.join(gateway_status['active_gateways'])}")
        
        # Test route availability
        print("\nRoute Availability Tests:")
        test_services = ["llm", "pinecone", "hubspot", "slack", "yardi"]
        
        for service in test_services:
            routes = self.orchestrator._get_available_routes(service)
            print(f"  {service}: {'✅ Available' if routes else '❌ Not Available'} ({len(routes)} routes)")
        
        self.test_results["gateway_routing"] = gateway_status
    
    async def test_mcp_servers(self):
        """Test MCP server availability"""
        self.print_header("MCP Server Test")
        
        # Load MCP configuration
        mcp_config_path = Path("mcp_config.json")
        if mcp_config_path.exists():
            with open(mcp_config_path) as f:
                mcp_config = json.load(f)
            
            print("Configured MCP Servers:")
            for server_name, config in mcp_config.get("mcpServers", {}).items():
                print(f"  {server_name}:")
                print(f"    Command: {config.get('command')} {' '.join(config.get('args', []))}")
                print(f"    Description: {config.get('description', 'No description')}")
                
                # Check if required environment variables are set
                env_vars = config.get('env', {})
                if env_vars:
                    missing_vars = []
                    for var in env_vars:
                        if not getattr(self.config, var.lower(), None):
                            missing_vars.append(var)
                    
                    if missing_vars:
                        print(f"    Status: ❌ Missing environment variables: {', '.join(missing_vars)}")
                    else:
                        print(f"    Status: ✅ All required environment variables configured")
        else:
            print("❌ mcp_config.json not found")
        
        self.test_results["mcp_servers"] = {
            "config_exists": mcp_config_path.exists(),
            "servers": list(mcp_config.get("mcpServers", {}).keys()) if mcp_config_path.exists() else []
        }
    
    async def test_integrations(self):
        """Test specific integrations"""
        self.print_header("Integration Tests")
        
        # Test vector database connectivity
        print("Vector Database Tests:")
        if self.config.pinecone_api_key:
            print("  Pinecone: ✅ API key configured")
        else:
            print("  Pinecone: ❌ API key not configured")
        
        if self.config.weaviate_api_key:
            print("  Weaviate: ✅ API key configured")
        else:
            print("  Weaviate: ❌ API key not configured")
        
        # Test business intelligence
        print("\nBusiness Intelligence Tests:")
        bi_services = {
            "HubSpot": self.config.hubspot_api_key,
            "Gong.io": self.config.gong_api_key,
            "Salesforce": self.config.salesforce_api_key,
            "Looker": self.config.looker_api_key
        }
        
        for service, has_key in bi_services.items():
            print(f"  {service}: {'✅ Configured' if has_key else '❌ Not configured'}")
        
        # Test property management
        print("\nProperty Management Tests:")
        pm_services = {
            "Yardi": self.config.yardi_api_key,
            "RealPage": self.config.realpage_api_key,
            "AppFolio": self.config.appfolio_api_key,
            "Entrata": self.config.entrata_api_key,
            "CoStar": self.config.costar_api_key
        }
        
        for service, has_key in pm_services.items():
            print(f"  {service}: {'✅ Configured' if has_key else '❌ Not configured'}")
        
        self.test_results["integration_tests"] = {
            "vector_db": sum(1 for k in [self.config.pinecone_api_key, self.config.weaviate_api_key] if k),
            "business_intelligence": sum(1 for k in bi_services.values() if k),
            "property_management": sum(1 for k in pm_services.values() if k)
        }
    
    def generate_report(self):
        """Generate final test report"""
        self.print_header("Infrastructure Test Summary")
        
        # Overall health score
        total_tests = 0
        passed_tests = 0
        
        # API configuration score
        api_score = self.test_results["api_configuration"]["percentage"] / 100
        passed_tests += api_score
        total_tests += 1
        
        # Critical APIs score
        if self.test_results["api_configuration"]["critical_apis_ok"]:
            passed_tests += 1
        total_tests += 1
        
        # Gateway routing score
        if self.test_results["gateway_routing"]["total_routes"] > 0:
            passed_tests += 1
        total_tests += 1
        
        # MCP servers score
        if self.test_results["mcp_servers"]["config_exists"]:
            passed_tests += 1
        total_tests += 1
        
        # Calculate health score
        health_score = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        print(f"Overall Infrastructure Health: {health_score:.1f}%")
        
        # Recommendations
        print("\nRecommendations:")
        recommendations = []
        
        if not self.test_results["api_configuration"]["critical_apis_ok"]:
            recommendations.append("Configure missing critical APIs (AI provider, vector DB, business intelligence)")
        
        if self.test_results["api_configuration"]["percentage"] < 30:
            recommendations.append("Configure additional APIs to unlock more features")
        
        if self.test_results["integration_tests"]["property_management"] == 0:
            recommendations.append("Configure at least one property management API (Yardi, RealPage, etc.)")
        
        if not recommendations:
            recommendations.append("Infrastructure is well configured! Consider adding optional APIs for extended functionality.")
        
        for i, rec in enumerate(recommendations, 1):
            print(f"  {i}. {rec}")
        
        # Save detailed report
        report_path = Path("infrastructure_test_report.json")
        with open(report_path, "w") as f:
            json.dump(self.test_results, f, indent=2, default=str)
        
        print(f"\nDetailed report saved to: {report_path}")
    
    async def run_all_tests(self):
        """Run all infrastructure tests"""
        print("\n🚀 Sophia AI Infrastructure Test Suite")
        print("Testing all API integrations, gateways, and MCP servers...")
        
        # Run synchronous tests
        self.test_api_configuration()
        self.test_gateway_routing()
        
        # Run async tests
        await self.test_mcp_servers()
        await self.test_integrations()
        
        # Generate report
        self.generate_report()

async def main():
    """Main entry point"""
    tester = InfrastructureTest()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main()) 