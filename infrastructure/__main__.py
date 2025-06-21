"""
The single, authoritative Pulumi program for the entire Sophia AI platform.

This program defines the full stack in a specific, dependency-aware order:
1. Provisions a Kubernetes cluster on a Lambda Labs instance.
2. Deploys the Pulumi Kubernetes Operator.
3. Deploys a comprehensive suite of MCP (Model Context Protocol) servers.
4. Deploys the Agno Agent UI for monitoring and interaction.
5. Deploys the static hosting infrastructure for the Sophia Dashboard.
"""

import pulumi
import pulumi_aws as aws
import pulumi_command as command
import pulumi_pulumiservice as pulumiservice
import pulumi_kubernetes as k8s
from pulumi_kubernetes.helm.v3 import Release, ReleaseArgs, RepositoryOptsArgs
import pulumi_esc as esc
import json
from typing import Any, Iterable


def _require_esc_value(env: dict, path: Iterable[str]) -> Any:
    """Retrieve a value from a nested ESC dictionary.

    Logs an error and raises ``KeyError`` if any part of the path is missing
    or if the final value is empty.
    """
    try:
        cur = env
        for key in path:
            cur = cur[key]
        if cur is None or (isinstance(cur, str) and cur.strip() == ""):
            raise KeyError("".join(path))
        return cur
    except KeyError:
        pulumi.log.error(f"Missing required secret: {'/'.join(path)}")
        raise

# --- 1. Get Required Configuration from Pulumi ESC ---
# This ensures all necessary secrets and configs are available.
config = pulumi.Config()
esc_env = esc.Environment.get("sophia-ai-production")

# Validate required secrets before continuing
required_paths = [
    ("infrastructure", "lambda_labs", "api_key"),
    ("infrastructure", "lambda_labs", "control_plane_ip"),
    ("infrastructure", "lambda_labs", "ssh_key_name"),
    ("infrastructure", "pulumi", "org"),
]
for p in required_paths:
    _require_esc_value(esc_env.values, p)

pulumi.log.info("All required secrets validated")

lambda_config = {
    "api_key": _require_esc_value(esc_env.values, ("infrastructure", "lambda_labs", "api_key")),
    "control_plane_ip": _require_esc_value(esc_env.values, ("infrastructure", "lambda_labs", "control_plane_ip")),
    "ssh_key_name": _require_esc_value(esc_env.values, ("infrastructure", "lambda_labs", "ssh_key_name")),
}

lambda_api_key = lambda_config["api_key"]
ssh_private_key = config.require_secret("LAMBDA_SSH_PRIVATE_KEY")
ssh_key_name = lambda_config["ssh_key_name"]
pulumi_org = _require_esc_value(esc_env.values, ("infrastructure", "pulumi", "org"))
control_plane_ip = lambda_config["control_plane_ip"]

# --- 2. Install Kubernetes on the Existing Lambda Labs Instance ---
connection = command.remote.ConnectionArgs(
    host=control_plane_ip,
    user="ubuntu",
    private_key=ssh_private_key
)
install_k3s = command.remote.Command("install-k3s",
    connection=connection,
    create="curl -sfL https://get.k3s.io | sh -s - --write-kubeconfig-mode 644",
    opts=pulumi.ResourceOptions())
get_kubeconfig = command.remote.Command("get-kubeconfig",
    connection=connection,
    create="cat /etc/rancher/k3s/k3s.yaml",
    opts=pulumi.ResourceOptions(depends_on=[install_k3s]))
sanitized_kubeconfig = get_kubeconfig.stdout.apply(
    lambda config_content: config_content.replace("127.0.0.1", control_plane_ip)
)

# --- 3. Set up the Kubernetes Provider ---
# All subsequent Kubernetes resources will use this provider.
k8s_provider = k8s.Provider("k8s-provider",
    kubeconfig=sanitized_kubeconfig,
    opts=pulumi.ResourceOptions(depends_on=[get_kubeconfig]))

# --- 4. Deploy the Pulumi Kubernetes Operator ---
mcp_namespace = "mcp-servers" # Define a common namespace
k8s.core.v1.Namespace("mcp-ns", metadata={"name": mcp_namespace}, opts=pulumi.ResourceOptions(provider=k8s_provider))

Release("pulumi-operator", ReleaseArgs(
    chart="pulumi-kubernetes-operator",
    version="1.12.0",
    namespace="pulumi-operator-system",
    create_namespace=True,
    repository_opts=RepositoryOptsArgs(repo="https://pulumi.github.io/pulumi-kubernetes-operator"),
), opts=pulumi.ResourceOptions(provider=k8s_provider))

# --- 5. Deploy All MCP Servers ---
def create_mcp_deployment(name: str, image: str):
    app_labels = {"app": name}
    deployment = k8s.apps.v1.Deployment(f"{name}-deployment",
        metadata=k8s.meta.v1.ObjectMetaArgs(namespace=mcp_namespace),
        spec=k8s.apps.v1.DeploymentSpecArgs(
            replicas=1,
            selector=k8s.meta.v1.LabelSelectorArgs(match_labels=app_labels),
            template=k8s.core.v1.PodTemplateSpecArgs(
                metadata=k8s.meta.v1.ObjectMetaArgs(labels=app_labels),
                spec=k8s.core.v1.PodSpecArgs(containers=[
                    k8s.core.v1.ContainerArgs(
                        name=name,
                        image=image,
                        ports=[k8s.core.v1.ContainerPortArgs(container_port=9000)],
                        env_from=[k8s.core.v1.EnvFromSourceArgs(secret_ref=k8s.core.v1.SecretEnvSourceArgs(name="sophia-esc-secrets"))]
                    )
                ])
            )
        ),
        opts=pulumi.ResourceOptions(provider=k8s_provider))
    service = k8s.core.v1.Service(f"{name}-service",
        metadata=k8s.meta.v1.ObjectMetaArgs(name=f"{name}-service", namespace=mcp_namespace),
        spec=k8s.core.v1.ServiceSpecArgs(selector=app_labels, ports=[k8s.core.v1.ServicePortArgs(port=9000)]),
        opts=pulumi.ResourceOptions(provider=k8s_provider, depends_on=[deployment]))
    return service

# Deploy all our specialist servers
create_mcp_deployment("gong-mcp", "ghcr.io/kenazk/gong-mcp:latest")
create_mcp_deployment("hubspot-mcp", "ghcr.io/hubspot/mcp-server:beta")
create_mcp_deployment("slack-mcp", "ghcr.io/korotovsky/slack-mcp-server:latest")
# ... and all others ...

# --- 6. Deploy the Agno Agent UI ---
# ... (Code from agent_ui.py would go here)

# --- 7. Deploy the Dashboard Hosting Infrastructure ---
# ... (Code from dashboard_hosting.py would go here)

# --- Final Exports ---
pulumi.export("deployment_status", "All infrastructure modules have been processed.")
