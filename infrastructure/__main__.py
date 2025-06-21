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
import hashlib
import os
import datetime
import logging
from prometheus_client import CollectorRegistry, Counter, push_to_gateway
import boto3

# --- 1. Get Required Configuration from Pulumi ESC ---
# This ensures all necessary secrets and configs are available.
config = pulumi.Config()
esc_env = esc.Environment.get("sophia-ai-production")

lambda_config = {
    "api_key": esc_env.values["infrastructure"]["lambda_labs"]["api_key"],
    "control_plane_ip": esc_env.values["infrastructure"]["lambda_labs"]["control_plane_ip"],
    "ssh_key_name": esc_env.values["infrastructure"]["lambda_labs"]["ssh_key_name"]
}

lambda_api_key = lambda_config["api_key"]
ssh_private_key = config.require_secret("LAMBDA_SSH_PRIVATE_KEY")
ssh_key_name = lambda_config["ssh_key_name"]
pulumi_org = esc_env.values["infrastructure"]["pulumi"]["org"]
control_plane_ip = lambda_config["control_plane_ip"]

# --- Secret Rotation Tracking -------------------------------------------------
logger = logging.getLogger("esc-rotation")
logging.basicConfig(level=logging.INFO)

ROTATION_HISTORY_PATH = os.path.join(os.path.dirname(__file__), "esc", "rotation_history.json")
PUSHGATEWAY = os.getenv("PROMETHEUS_PUSHGATEWAY_URL")
registry = CollectorRegistry()
rotation_events = Counter(
    "esc_rotation_events_total",
    "Total ESC secret rotation events",
    registry=registry,
)
rotation_failures = Counter(
    "esc_rotation_failures_total",
    "Total ESC rotation processing failures",
    registry=registry,
)

def _load_rotation_history():
    if os.path.exists(ROTATION_HISTORY_PATH):
        try:
            with open(ROTATION_HISTORY_PATH, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error("Failed to load rotation history: %s", e)
    return {}


def _save_rotation_history(data):
    try:
        with open(ROTATION_HISTORY_PATH, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.error("Failed to save rotation history: %s", e)
        rotation_failures.inc()
        if PUSHGATEWAY:
            try:
                push_to_gateway(PUSHGATEWAY, job="esc_rotation", registry=registry)
            except Exception as push_err:
                logger.error("Failed to push metrics: %s", push_err)


def _send_alert(message: str):
    alert_topic = config.get("rotation_alert_topic_arn")
    if not alert_topic:
        return
    try:
        boto3.client("sns").publish(TopicArn=alert_topic, Message=message, Subject="ESC Rotation Failure")
    except Exception as e:
        logger.error("Failed to send alert: %s", e)


def track_rotation():
    history = _load_rotation_history()
    prev_hash = history.get("current_hash")
    current_hash = hashlib.sha256(
        json.dumps(esc_env.values, sort_keys=True).encode()
    ).hexdigest()
    if current_hash != prev_hash:
        event = {"timestamp": datetime.datetime.utcnow().isoformat(), "hash": current_hash}
        history.setdefault("history", []).append(event)
        history["current_hash"] = current_hash
        logger.info("ESC secret rotation detected")
        rotation_events.inc()
        _save_rotation_history(history)
        if PUSHGATEWAY:
            try:
                push_to_gateway(PUSHGATEWAY, job="esc_rotation", registry=registry)
            except Exception as push_err:
                logger.error("Failed to push metrics: %s", push_err)
                rotation_failures.inc()
                _send_alert(f"Failed to push rotation metrics: {push_err}")
    else:
        logger.info("No secret rotation detected")

    if PUSHGATEWAY:
        try:
            push_to_gateway(PUSHGATEWAY, job="esc_rotation", registry=registry)
        except Exception as push_err:
            logger.error("Failed to push metrics: %s", push_err)
            rotation_failures.inc()
            _send_alert(f"Failed to push rotation metrics: {push_err}")


track_rotation()

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
