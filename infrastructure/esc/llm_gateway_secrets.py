"""Pulumi ESC Secret Manager for LLM Gateway services like Portkey and OpenRouter.
"""
from infrastructure.pulumi_esc import PulumiESCManager


class LLMGatewaySecretManager(PulumiESCManager):
    """Handles getting and setting API keys for LLM gateways."""

    def __init__(self):
        super().__init__()

    async def get_portkey_api_key(self) -> str:
        """Retrieves the Portkey API key."""
        return await self.get_secret("PORTKEY_API_KEY")

    async def get_openrouter_api_key(self) -> str:
        """Retrieves the OpenRouter API key."""
        return await self.get_secret("OPENROUTER_API_KEY")


llm_gateway_secret_manager = LLMGatewaySecretManager()
