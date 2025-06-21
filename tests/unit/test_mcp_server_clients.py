import importlib.util
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]

import pytest

sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "mcp-servers"))
sys.path.insert(0, str(ROOT / "mcp-servers" / "snowflake"))
from backend.integrations.pulumi_esc import SophiaESCManager

# Dynamically load modules from the mcp-servers directory which uses a hyphen in the path
sai_spec = importlib.util.spec_from_file_location(
    "sai_mcp",
    ROOT / "mcp-servers" / "sophia_ai_intelligence" / "sophia_ai_intelligence_mcp_server.py",
)
sai_mod = importlib.util.module_from_spec(sai_spec)
sai_spec.loader.exec_module(sai_mod)

sdi_spec = importlib.util.spec_from_file_location(
    "sdi_mcp",
    ROOT / "mcp-servers" / "sophia_data_intelligence" / "sophia_data_intelligence_mcp_server.py",
)
sdi_mod = importlib.util.module_from_spec(sdi_spec)
sdi_spec.loader.exec_module(sdi_mod)

si_spec = importlib.util.spec_from_file_location(
    "si_mcp",
    ROOT / "mcp-servers" / "sophia_infrastructure" / "sophia_infrastructure_mcp_server.py",
)
si_mod = importlib.util.module_from_spec(si_spec)
si_spec.loader.exec_module(si_mod)

SophiaAIIntelligenceMCPServer = sai_mod.SophiaAIIntelligenceMCPServer
SophiaDataIntelligenceMCPServer = sdi_mod.SophiaDataIntelligenceMCPServer
SophiaInfrastructureMCPServer = si_mod.SophiaInfrastructureMCPServer


def _patch_secrets(monkeypatch, mapping):
    def fake_get_secret(self, key):
        return mapping.get(key)

    monkeypatch.setattr(SophiaESCManager, "get_secret", fake_get_secret)


def test_ai_intelligence_client_init(monkeypatch):
    secrets = {
        "observability.arize_api_key": "ARIZE",
        "observability.arize_space_id": "SPACE",
        "ai_services.openrouter_api_key": "OPEN",
        "ai_services.portkey_api_key": "PORT",
        "ai_services.portkey_config_id": "CFG",
        "ai_services.huggingface_api_token": "HF",
        "ai_services.togetherai_api_key": "TOG",
    }
    _patch_secrets(monkeypatch, secrets)
    server = SophiaAIIntelligenceMCPServer()
    assert server.arize_client == {"api_key": "ARIZE", "space_id": "SPACE"}
    assert server.openrouter_client == {"api_key": "OPEN"}
    assert server.portkey_client == {"api_key": "PORT", "config_id": "CFG"}
    assert server.huggingface_client == {"api_token": "HF"}
    assert server.together_client == {"api_key": "TOG"}


def test_data_intelligence_client_init(monkeypatch):
    secrets = {
        "research_tools.apify_api_token": "APIFY",
        "research_tools.tavily_api_key": "TAVILY",
        "research_tools.zenrows_api_key": "ZEN",
        "research_tools.twingly_api_key": "TWING",
        "research_tools.phantombuster_api_key": "PHANTOM",
    }
    _patch_secrets(monkeypatch, secrets)
    server = SophiaDataIntelligenceMCPServer()
    assert server.apify_client == {"api_token": "APIFY"}
    assert server.tavily_client == {"api_key": "TAVILY"}
    assert server.zenrows_client == {"api_key": "ZEN"}
    assert server.twingly_client == {"api_key": "TWING"}
    assert server.phantombuster_client == {"api_key": "PHANTOM"}


def test_infrastructure_client_init(monkeypatch):
    secrets = {
        "infrastructure.lambda_labs.api_key": "LAMBDA",
        "infrastructure.pulumi.access_token": "PULUMI",
        "infrastructure.docker.username": "DOCKERU",
        "infrastructure.docker.token": "DOCKERT",
    }
    _patch_secrets(monkeypatch, secrets)
    server = SophiaInfrastructureMCPServer()
    assert server.lambda_client == {"api_key": "LAMBDA"}
    assert server.pulumi_client == {"access_token": "PULUMI"}
    assert server.docker_client == {"username": "DOCKERU", "token": "DOCKERT"}
