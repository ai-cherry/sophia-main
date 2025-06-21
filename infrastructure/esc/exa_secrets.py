"""Pulumi ESC Secret Manager for Exa.
"""
from infrastructure.pulumi_esc import PulumiESCManager


class ExaSecretManager(PulumiESCManager):
    def __init__(self):
        super().__init__(env_file_name="exa.env")

    async def get_api_key(self) -> str:
        return await self.get_secret("EXA_API_KEY")


exa_secret_manager = ExaSecretManager()
