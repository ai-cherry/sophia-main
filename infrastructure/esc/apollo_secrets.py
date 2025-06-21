"""Pulumi ESC Secret Manager for Apollo.io.
"""
from infrastructure.pulumi_esc import PulumiESCManager


class ApolloSecretManager(PulumiESCManager):
    def __init__(self):
        super().__init__()

    async def get_api_key(self) -> str:
        return await self.get_secret("APOLLO_API_KEY")


apollo_secret_manager = ApolloSecretManager()
