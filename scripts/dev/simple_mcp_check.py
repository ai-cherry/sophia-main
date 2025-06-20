#!/usr/bin/env python3
"""Simple MCP Infrastructure Check
Basic health check for MCP servers and infrastructure
"""

import json
import os
import subprocess
import time
from pathlib import Path

import requests


def check_docker_status():
    """Check Docker containers status"""
    print("🐳 Checking Docker containers...")

    try:
        # Get all containers
        result = subprocess.run(
            ["docker", "ps", "-a", "--format", "json"], capture_output=True, text=True
        )

        if result.returncode != 0:
            print(f"❌ Docker command failed: {result.stderr}")
            return

        containers = []
        for line in result.stdout.strip().split("\n"):
            if line:
                try:
                    container = json.loads(line)
                    if "sophia" in container.get("Names", "") or "mcp" in container.get(
                        "Names", ""
                    ):
                        containers.append(container)
                except json.JSONDecodeError:
                    continue

        if not containers:
            print("  No MCP containers found")
            return

        print(f"  Found {len(containers)} MCP containers:")
        for container in containers:
            name = container.get("Names", "unknown")
            status = container.get("State", "unknown")
            image = container.get("Image", "unknown")

            status_icon = "✅" if status == "running" else "❌"
            print(f"    {status_icon} {name}: {status} ({image})")

            # Get logs for non-running containers
            if status != "running":
                try:
                    log_result = subprocess.run(
                        ["docker", "logs", "--tail", "10", name],
                        capture_output=True,
                        text=True,
                    )
                    if log_result.stdout:
                        print(f"      Recent logs: {log_result.stdout[:200]}...")
                except:
                    pass

    except Exception as e:
        print(f"❌ Error checking Docker: {e}")


def check_mcp_gateway():
    """Check MCP Gateway health"""
    print("\n🚪 Checking MCP Gateway...")

    gateway_url = "http://localhost:8090"

    try:
        # Health check
        response = requests.get(f"{gateway_url}/health", timeout=5)
        if response.status_code == 200:
            print("  ✅ MCP Gateway is reachable")
            try:
                data = response.json()
                print(f"      Response: {data}")
            except:
                print(f"      Response: {response.text[:100]}")
        else:
            print(f"  ❌ MCP Gateway returned {response.status_code}")

    except requests.exceptions.ConnectionError:
        print("  ❌ MCP Gateway is not reachable (connection refused)")
    except requests.exceptions.Timeout:
        print("  ❌ MCP Gateway timeout")
    except Exception as e:
        print(f"  ❌ Error checking MCP Gateway: {e}")


def check_environment_variables():
    """Check required environment variables"""
    print("\n🔐 Checking environment variables...")

    required_vars = [
        "PINECONE_API_KEY",
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "LINEAR_API_KEY",
    ]

    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"  ✅ {var}: Set (length: {len(value)})")
        else:
            print(f"  ❌ {var}: Not set")
            missing_vars.append(var)

    if missing_vars:
        print(f"\n  🚨 Missing {len(missing_vars)} required environment variables")
        print("     Consider setting them in your .env file or environment")


def check_mcp_config():
    """Check MCP configuration"""
    print("\n⚙️ Checking MCP configuration...")

    project_root = Path(__file__).parent.parent.parent
    mcp_config_path = project_root / "mcp_config.json"

    if mcp_config_path.exists():
        try:
            with open(mcp_config_path, "r") as f:
                config = json.load(f)

            servers = config.get("mcpServers", {})
            print(f"  ✅ MCP config found with {len(servers)} servers:")

            for server_name in servers.keys():
                print(f"    • {server_name}")

                # Check if server module exists
                server_config = servers[server_name]
                if server_config.get("command") == "python":
                    args = server_config.get("args", [])
                    if len(args) >= 2 and args[0] == "-m":
                        module_path = project_root / (args[1].replace(".", "/") + ".py")
                        if module_path.exists():
                            print(f"      ✅ Module exists: {module_path.name}")
                        else:
                            print(f"      ❌ Module missing: {module_path}")

        except Exception as e:
            print(f"  ❌ Error reading MCP config: {e}")
    else:
        print(f"  ❌ MCP config not found at {mcp_config_path}")


def check_external_services():
    """Check external service connectivity"""
    print("\n🌐 Checking external services...")

    services = [
        ("Pinecone", "https://api.pinecone.io"),
        ("OpenAI", "https://api.openai.com"),
        ("Anthropic", "https://api.anthropic.com"),
    ]

    for service_name, url in services:
        try:
            response = requests.get(url, timeout=5)
            print(f"  ✅ {service_name}: Reachable ({response.status_code})")
        except requests.exceptions.ConnectionError:
            print(f"  ❌ {service_name}: Connection failed")
        except requests.exceptions.Timeout:
            print(f"  ❌ {service_name}: Timeout")
        except Exception as e:
            print(f"  ❌ {service_name}: Error - {e}")


def generate_recommendations():
    """Generate quick recommendations"""
    print("\n💡 Quick Recommendations:")
    print("  1. Fix restarting containers:")
    print("     docker-compose down && docker-compose up -d")
    print("  2. Check container logs:")
    print("     docker-compose logs [service-name]")
    print("  3. Restart MCP Gateway:")
    print("     docker-compose restart mcp-gateway")
    print("  4. Set missing environment variables:")
    print("     export VARIABLE_NAME=value")
    print("  5. Test AI Memory server:")
    print("     python backend/mcp/ai_memory_mcp_server.py")


def main():
    """Main check function"""
    print("🔍 MCP INFRASTRUCTURE QUICK CHECK")
    print("=" * 50)

    check_docker_status()
    check_mcp_gateway()
    check_environment_variables()
    check_mcp_config()
    check_external_services()
    generate_recommendations()

    print(f"\n✅ Check completed at {time.strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()
