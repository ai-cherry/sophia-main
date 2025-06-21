from typing import Dict, List, Optional

import yaml

# Configuration for each service
SERVICE_CONFIGS = {
    "ai-service": {
        "image": "ghcr.io/sophia/ai:latest",
        "replicas": 2,
        "cpu": "2",
        "memory": "2Gi",
        "gpu": 1,
    },
    "data-service": {
        "image": "ghcr.io/sophia/data:latest",
        "replicas": 1,
        "cpu": "1",
        "memory": "1Gi",
        "gpu": 0,
    },
    "bi-service": {
        "image": "ghcr.io/sophia/bi:latest",
        "replicas": 1,
        "cpu": "1",
        "memory": "1Gi",
        "gpu": 0,
    },
    "infra-service": {
        "image": "ghcr.io/sophia/infra:latest",
        "replicas": 1,
        "cpu": "500m",
        "memory": "512Mi",
        "gpu": 0,
    },
}


def _create_deployment(
    name: str,
    image: str,
    replicas: int,
    cpu: str,
    memory: str,
    gpu: int = 0,
) -> Dict:
    """Create a Kubernetes Deployment manifest."""
    resources = {
        "requests": {"cpu": cpu, "memory": memory},
        "limits": {"cpu": cpu, "memory": memory},
    }
    node_selector: Optional[Dict[str, str]] = None
    tolerations: Optional[List[Dict[str, str]]] = None

    if gpu:
        resources["requests"]["nvidia.com/gpu"] = str(gpu)
        resources["limits"]["nvidia.com/gpu"] = str(gpu)
        node_selector = {"lambda.labs/gpu": "true"}
        tolerations = [
            {
                "key": "nvidia.com/gpu",
                "operator": "Exists",
                "effect": "NoSchedule",
            }
        ]

    container = {
        "name": name,
        "image": image,
        "resources": resources,
        "livenessProbe": {
            "httpGet": {"path": "/healthz", "port": 80},
            "initialDelaySeconds": 10,
            "periodSeconds": 10,
        },
        "readinessProbe": {
            "httpGet": {"path": "/ready", "port": 80},
            "initialDelaySeconds": 5,
            "periodSeconds": 10,
        },
    }

    pod_spec = {
        "containers": [container],
    }
    if node_selector:
        pod_spec["nodeSelector"] = node_selector
    if tolerations:
        pod_spec["tolerations"] = tolerations

    deployment = {
        "apiVersion": "apps/v1",
        "kind": "Deployment",
        "metadata": {"name": name, "namespace": "sophia"},
        "spec": {
            "replicas": replicas,
            "selector": {"matchLabels": {"app": name}},
            "strategy": {
                "type": "RollingUpdate",
                "rollingUpdate": {"maxSurge": "25%", "maxUnavailable": "25%"},
            },
            "template": {
                "metadata": {"labels": {"app": name}},
                "spec": pod_spec,
            },
        },
    }
    return deployment


def generate_deployments() -> List[Dict]:
    """Generate manifests for all Sophia services."""
    manifests = []
    for name, cfg in SERVICE_CONFIGS.items():
        manifests.append(
            _create_deployment(
                name=name,
                image=cfg["image"],
                replicas=cfg["replicas"],
                cpu=cfg["cpu"],
                memory=cfg["memory"],
                gpu=cfg["gpu"],
            )
        )
    return manifests


def generate_yaml() -> str:
    """Return the Kubernetes manifests as a YAML string."""
    return yaml.safe_dump_all(generate_deployments())


if __name__ == "__main__":
    print(generate_yaml())
