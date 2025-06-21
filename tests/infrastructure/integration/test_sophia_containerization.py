import os
import sys

import pytest
import yaml

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))
from infrastructure.sophia_containerization import generate_deployments, generate_yaml


@pytest.mark.integration
class TestSophiaContainerization:
    def test_manifest_generation(self):
        manifests = generate_deployments()
        assert len(manifests) == 4
        names = {m["metadata"]["name"] for m in manifests}
        assert names == {"ai-service", "data-service", "bi-service", "infra-service"}

        for m in manifests:
            spec = m["spec"]
            template = spec["template"]
            pod = template["spec"]
            container = pod["containers"][0]

            # check resources
            assert "resources" in container
            assert "requests" in container["resources"]
            assert "limits" in container["resources"]
            assert "cpu" in container["resources"]["requests"]
            assert "memory" in container["resources"]["requests"]

            # check health probes
            assert "livenessProbe" in container
            assert "readinessProbe" in container

            # check rolling update strategy
            strategy = spec.get("strategy", {})
            assert strategy.get("type") == "RollingUpdate"
            assert "rollingUpdate" in strategy

    def test_yaml_output(self):
        text = generate_yaml()
        docs = list(yaml.safe_load_all(text))
        assert len(docs) == 4
        assert isinstance(docs[0], dict)
