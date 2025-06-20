#!/usr/bin/env python3
"""MCP Infrastructure Diagnostic Tool
Comprehensive analysis and fixing of MCP server issues
"""

import asyncio
import json
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

try:
    import docker
except ImportError:
    docker = None

try:
    import aiohttp
except ImportError:
    aiohttp = None

import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class MCPDiagnostic:
    def __init__(self):
        self.docker_client = None
        if docker:
            try:
                self.docker_client = docker.from_env()
            except Exception as e:
                logger.warning(f"Docker client not available: {e}")

        self.project_root = Path(__file__).parent.parent.parent
        self.mcp_config_path = self.project_root / "mcp_config.json"
        self.docker_compose_path = self.project_root / "docker-compose.yml"

        self.results = {
            "timestamp": datetime.now().isoformat(),
            "infrastructure": {},
            "containers": {},
            "network": {},
            "configuration": {},
            "recommendations": [],
        }

    async def run_full_diagnostic(self) -> Dict[str, Any]:
        """Run comprehensive MCP infrastructure diagnostic"""
        logger.info("🔍 Starting MCP Infrastructure Diagnostic...")

        # Phase 1: Infrastructure Assessment
        await self._check_docker_infrastructure()
        await self._check_container_status()
        await self._check_network_connectivity()

        # Phase 2: Configuration Validation
        await self._validate_configurations()
        await self._check_environment_variables()
        await self._validate_secrets()

        # Phase 3: Service Health Checks
        await self._check_mcp_gateway_health()
        await self._check_individual_servers()

        # Phase 4: Generate Recommendations
        await self._generate_recommendations()

        return self.results

    async def _check_docker_infrastructure(self):
        """Check Docker infrastructure status"""
        logger.info("📋 Checking Docker infrastructure...")

        try:
            if self.docker_client:
                # Check Docker daemon
                self.docker_client.ping()
                self.results["infrastructure"]["docker_daemon"] = {"status": "healthy"}

                # Check available resources
                info = self.docker_client.info()
                self.results["infrastructure"]["resources"] = {
                    "containers_running": info.get("ContainersRunning", 0),
                    "containers_total": info.get("Containers", 0),
                    "images": info.get("Images", 0),
                    "memory_total": info.get("MemTotal", 0),
                    "cpu_count": info.get("NCPU", 0),
                }
            else:
                self.results["infrastructure"]["docker_daemon"] = {
                    "status": "unavailable"
                }

            # Check Docker Compose
            result = subprocess.run(
                ["docker-compose", "--version"], capture_output=True, text=True
            )
            if result.returncode == 0:
                self.results["infrastructure"]["docker_compose"] = {
                    "status": "available",
                    "version": result.stdout.strip(),
                }
            else:
                self.results["infrastructure"]["docker_compose"] = {
                    "status": "error",
                    "error": result.stderr,
                }

        except Exception as e:
            self.results["infrastructure"]["error"] = str(e)
            logger.error(f"Docker infrastructure check failed: {e}")

    async def _check_container_status(self):
        """Check status of all MCP-related containers"""
        logger.info("🐳 Checking MCP container status...")

        try:
            if not self.docker_client:
                self.results["containers"]["error"] = "Docker client not available"
                return

            containers = self.docker_client.containers.list(all=True)
            mcp_containers = [
                c for c in containers if "sophia" in c.name or "mcp" in c.name
            ]

            for container in mcp_containers:
                container_info = {
                    "name": container.name,
                    "status": container.status,
                    "image": (
                        container.image.tags[0] if container.image.tags else "unknown"
                    ),
                    "created": container.attrs["Created"],
                    "ports": container.ports,
                    "restart_count": container.attrs["RestartCount"],
                }

                # Get container logs for diagnosis
                if container.status != "running":
                    try:
                        logs = container.logs(tail=50).decode("utf-8")
                        container_info["recent_logs"] = logs
                    except Exception as e:
                        container_info["log_error"] = str(e)

                # Check health if available
                health = container.attrs.get("State", {}).get("Health")
                if health:
                    container_info["health"] = health["Status"]
                    if health["Status"] != "healthy":
                        container_info["health_logs"] = health.get("Log", [])

                self.results["containers"][container.name] = container_info

        except Exception as e:
            self.results["containers"]["error"] = str(e)
            logger.error(f"Container status check failed: {e}")

    async def _check_network_connectivity(self):
        """Check network connectivity between containers and external services"""
        logger.info("🌐 Checking network connectivity...")

        if not aiohttp:
            self.results["network"]["error"] = (
                "aiohttp not available for network checks"
            )
            return

        try:
            # Check MCP Gateway connectivity
            gateway_url = "http://localhost:8090"
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"{gateway_url}/health", timeout=5
                    ) as response:
                        self.results["network"]["mcp_gateway"] = {
                            "status": "reachable",
                            "response_code": response.status,
                            "response_time": time.time(),
                        }
            except Exception as e:
                self.results["network"]["mcp_gateway"] = {
                    "status": "unreachable",
                    "error": str(e),
                }

            # Check external service connectivity
            external_services = [
                ("Pinecone", "https://api.pinecone.io"),
                ("OpenAI", "https://api.openai.com"),
                ("Anthropic", "https://api.anthropic.com"),
            ]

            for service_name, url in external_services:
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url, timeout=5) as response:
                            self.results["network"][service_name.lower()] = {
                                "status": "reachable",
                                "response_code": response.status,
                            }
                except Exception as e:
                    self.results["network"][service_name.lower()] = {
                        "status": "unreachable",
                        "error": str(e),
                    }

        except Exception as e:
            self.results["network"]["error"] = str(e)
            logger.error(f"Network connectivity check failed: {e}")

    async def _validate_configurations(self):
        """Validate MCP and Docker configurations"""
        logger.info("⚙️ Validating configurations...")

        try:
            # Check mcp_config.json
            if self.mcp_config_path.exists():
                with open(self.mcp_config_path, "r") as f:
                    mcp_config = json.load(f)

                self.results["configuration"]["mcp_config"] = {
                    "status": "found",
                    "servers_count": len(mcp_config.get("mcpServers", {})),
                    "servers": list(mcp_config.get("mcpServers", {}).keys()),
                }

                # Validate each server configuration
                for server_name, config in mcp_config.get("mcpServers", {}).items():
                    validation = self._validate_server_config(server_name, config)
                    self.results["configuration"][f"server_{server_name}"] = validation
            else:
                self.results["configuration"]["mcp_config"] = {
                    "status": "missing",
                    "path": str(self.mcp_config_path),
                }

            # Check docker-compose.yml
            if self.docker_compose_path.exists():
                self.results["configuration"]["docker_compose"] = {
                    "status": "found",
                    "path": str(self.docker_compose_path),
                }
            else:
                self.results["configuration"]["docker_compose"] = {
                    "status": "missing",
                    "path": str(self.docker_compose_path),
                }

        except Exception as e:
            self.results["configuration"]["error"] = str(e)
            logger.error(f"Configuration validation failed: {e}")

    def _validate_server_config(
        self, server_name: str, config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate individual server configuration"""
        validation = {"server": server_name, "issues": []}

        # Check required fields
        if "command" not in config and "uri" not in config:
            validation["issues"].append("Missing command or uri")

        # Check environment variables
        env_vars = config.get("env", {})
        for var_name, var_value in env_vars.items():
            if (
                isinstance(var_value, str)
                and var_value.startswith("${")
                and var_value.endswith("}")
            ):
                # This is an environment variable reference
                actual_var = var_value[2:-1]
                import os

                if not os.getenv(actual_var):
                    validation["issues"].append(
                        f"Missing environment variable: {actual_var}"
                    )

        # Check if server module exists (for Python servers)
        if config.get("command") == "python":
            args = config.get("args", [])
            if len(args) >= 2 and args[0] == "-m":
                module_path = args[1].replace(".", "/") + ".py"
                if not (self.project_root / module_path).exists():
                    validation["issues"].append(
                        f"Server module not found: {module_path}"
                    )

        validation["status"] = "valid" if not validation["issues"] else "invalid"
        return validation

    async def _check_environment_variables(self):
        """Check required environment variables"""
        logger.info("🔐 Checking environment variables...")

        import os

        required_vars = [
            "PINECONE_API_KEY",
            "OPENAI_API_KEY",
            "ANTHROPIC_API_KEY",
            "PULUMI_ORG",
            "RETOOL_API_TOKEN",
            "LINEAR_API_KEY",
        ]

        env_status = {}
        for var in required_vars:
            value = os.getenv(var)
            env_status[var] = {
                "present": value is not None,
                "length": len(value) if value else 0,
                "masked_value": f"{value[:4]}..." if value and len(value) > 4 else None,
            }

        self.results["configuration"]["environment_variables"] = env_status

    async def _validate_secrets(self):
        """Validate secret management setup"""
        logger.info("🔒 Validating secrets...")

        # Check Pulumi ESC setup
        try:
            result = subprocess.run(
                ["pulumi", "whoami"], capture_output=True, text=True
            )
            if result.returncode == 0:
                self.results["configuration"]["pulumi_auth"] = {
                    "status": "authenticated",
                    "user": result.stdout.strip(),
                }
            else:
                self.results["configuration"]["pulumi_auth"] = {
                    "status": "not_authenticated",
                    "error": result.stderr,
                }
        except FileNotFoundError:
            self.results["configuration"]["pulumi_auth"] = {
                "status": "pulumi_not_installed"
            }

    async def _check_mcp_gateway_health(self):
        """Check MCP Gateway health and functionality"""
        logger.info("🚪 Checking MCP Gateway health...")

        if not aiohttp:
            self.results["network"]["gateway_health"] = {
                "status": "error",
                "error": "aiohttp not available",
            }
            return

        gateway_url = "http://localhost:8090"

        try:
            async with aiohttp.ClientSession() as session:
                # Health check
                try:
                    async with session.get(
                        f"{gateway_url}/health", timeout=5
                    ) as response:
                        health_data = await response.json()
                        self.results["network"]["gateway_health"] = {
                            "status": (
                                "healthy" if response.status == 200 else "unhealthy"
                            ),
                            "response": health_data,
                        }
                except:
                    # Try plain text response
                    async with session.get(
                        f"{gateway_url}/health", timeout=5
                    ) as response:
                        health_text = await response.text()
                        self.results["network"]["gateway_health"] = {
                            "status": (
                                "healthy" if response.status == 200 else "unhealthy"
                            ),
                            "response": health_text,
                        }

                # List available servers
                try:
                    async with session.get(
                        f"{gateway_url}/servers", timeout=5
                    ) as response:
                        if response.status == 200:
                            servers_data = await response.json()
                            self.results["network"]["gateway_servers"] = servers_data
                except:
                    pass

        except Exception as e:
            self.results["network"]["gateway_health"] = {
                "status": "error",
                "error": str(e),
            }

    async def _check_individual_servers(self):
        """Check individual MCP server health"""
        logger.info("🔍 Checking individual MCP servers...")

        server_health = {}
        for container_name, container_info in self.results["containers"].items():
            if container_info["status"] == "running":
                server_health[container_name] = {
                    "container_status": "running",
                    "health_check": "pending",
                }
            else:
                server_health[container_name] = {
                    "container_status": container_info["status"],
                    "health_check": "failed",
                }

        self.results["network"]["server_health"] = server_health

    async def _generate_recommendations(self):
        """Generate recommendations based on diagnostic results"""
        logger.info("💡 Generating recommendations...")

        recommendations = []

        # Check for restarting containers
        for container_name, info in self.results["containers"].items():
            if info.get("status") in ["restarting", "exited"]:
                recommendations.append(
                    {
                        "priority": "high",
                        "category": "container",
                        "issue": f"Container {container_name} is {info['status']}",
                        "recommendation": f"Investigate logs and restart {container_name}",
                        "fix_command": f"docker-compose restart {container_name.replace('sophia-', '')}",
                    }
                )

        # Check for missing environment variables
        env_vars = self.results["configuration"].get("environment_variables", {})
        for var_name, var_info in env_vars.items():
            if not var_info["present"]:
                recommendations.append(
                    {
                        "priority": "high",
                        "category": "configuration",
                        "issue": f"Missing environment variable: {var_name}",
                        "recommendation": f"Set {var_name} environment variable",
                        "fix_command": f"export {var_name}=your_value_here",
                    }
                )

        # Check for configuration issues
        for config_key, config_info in self.results["configuration"].items():
            if isinstance(config_info, dict) and config_info.get("status") == "invalid":
                recommendations.append(
                    {
                        "priority": "medium",
                        "category": "configuration",
                        "issue": f"Invalid configuration: {config_key}",
                        "recommendation": f"Fix configuration issues in {config_key}",
                        "details": config_info.get("issues", []),
                    }
                )

        # Check for network connectivity issues
        network_info = self.results["network"]
        for service, info in network_info.items():
            if isinstance(info, dict) and info.get("status") == "unreachable":
                recommendations.append(
                    {
                        "priority": "medium",
                        "category": "network",
                        "issue": f"Cannot reach {service}",
                        "recommendation": f"Check network connectivity and {service} service status",
                        "error": info.get("error"),
                    }
                )

        self.results["recommendations"] = recommendations

    def print_summary(self):
        """Print diagnostic summary"""
        print("\n" + "=" * 80)
        print("🔍 MCP INFRASTRUCTURE DIAGNOSTIC SUMMARY")
        print("=" * 80)

        # Infrastructure status
        print("\n📋 INFRASTRUCTURE STATUS:")
        infra = self.results["infrastructure"]
        print(
            f"  Docker Daemon: {'✅' if infra.get('docker_daemon', {}).get('status') == 'healthy' else '❌'}"
        )
        print(
            f"  Docker Compose: {'✅' if infra.get('docker_compose', {}).get('status') == 'available' else '❌'}"
        )

        # Container status
        print("\n🐳 CONTAINER STATUS:")
        if self.results["containers"]:
            for name, info in self.results["containers"].items():
                status_icon = "✅" if info.get("status") == "running" else "❌"
                print(f"  {name}: {status_icon} {info.get('status', 'unknown')}")
        else:
            print("  No containers found or Docker not available")

        # Network status
        print("\n🌐 NETWORK STATUS:")
        network = self.results["network"]
        for service, info in network.items():
            if isinstance(info, dict):
                status_icon = (
                    "✅" if info.get("status") in ["healthy", "reachable"] else "❌"
                )
                print(f"  {service}: {status_icon} {info.get('status', 'unknown')}")

        # Recommendations
        print("\n💡 RECOMMENDATIONS:")
        high_priority = [
            r for r in self.results["recommendations"] if r["priority"] == "high"
        ]
        medium_priority = [
            r for r in self.results["recommendations"] if r["priority"] == "medium"
        ]

        if high_priority:
            print("  🚨 HIGH PRIORITY:")
            for rec in high_priority[:5]:  # Show top 5
                print(f"    • {rec['issue']}")
                print(f"      → {rec['recommendation']}")

        if medium_priority:
            print("  ⚠️  MEDIUM PRIORITY:")
            for rec in medium_priority[:3]:  # Show top 3
                print(f"    • {rec['issue']}")

        print(f"\n📊 Total Issues Found: {len(self.results['recommendations'])}")
        print(f"📅 Diagnostic completed at: {self.results['timestamp']}")


async def main():
    """Main diagnostic function"""
    diagnostic = MCPDiagnostic()

    try:
        results = await diagnostic.run_full_diagnostic()

        # Print summary
        diagnostic.print_summary()

        # Save detailed results
        output_file = f"mcp_diagnostic_results_{int(time.time())}.json"
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2, default=str)

        print(f"\n📄 Detailed results saved to: {output_file}")

    except KeyboardInterrupt:
        print("\n🛑 Diagnostic interrupted by user")
    except Exception as e:
        logger.error(f"Diagnostic failed: {e}")
        print(f"\n❌ Diagnostic failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())
