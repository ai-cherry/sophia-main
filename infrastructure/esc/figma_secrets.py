"""Pulumi ESC Secret Manager for Figma.
"""
from infrastructure.pulumi_esc import PulumiESCManager


class FigmaSecretManager(PulumiESCManager):
    def __init__(self):
        super().__init__()

    async def get_api_key(self) -> str:
        return await self.get_secret("FIGMA_API_KEY")


figma_secret_manager = FigmaSecretManager()
