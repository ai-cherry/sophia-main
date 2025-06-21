"""Pulumi ESC Secret Manager for Pinecone.
"""
from infrastructure.pulumi_esc import PulumiESCManager


class PineconeSecretManager(PulumiESCManager):
    """Handles getting and setting Pinecone secrets via Pulumi ESC."""

    def __init__(self):
        super().__init__()

    async def get_pinecone_api_key(self) -> str:
        """Retrieves the Pinecone API key."""
        return await self.get_secret("PINECONE_API_KEY")


pinecone_secret_manager = PineconeSecretManager()

# Example of how to run this to set the secret
# This would typically be in a separate admin script.
if __name__ == "__main__":
    import os

    from dotenv import load_dotenv

    load_dotenv()

    # This script is for demonstration. In a real scenario, you would
    # have a secure way to provide the secret value.
    api_key_from_env = os.getenv("PINECONE_API_KEY_TO_SET")

    if not api_key_from_env:
        print(
            "Please set PINECONE_API_KEY_TO_SET in your .env file to run this example."
        )
    else:
        print(
            f"Setting Pinecone API key in Pulumi ESC environment '{ENVIRONMENT_NAME}'..."
        )
        manager = PineconeSecretManager()
        # Note: Running this with `pulumi up` would actually create the secret.
        # This python script defines the resource, but doesn't execute the creation.
        # To make this work directly, you'd use the Pulumi Automation API.
        print(
            "Pulumi resource definition created. Run `pulumi up` in this directory to apply."
        )

        # For direct execution via Python (requires Pulumi Automation API setup)
        # from pulumi.automation import LocalWorkspace, Stack, create_or_select_stack
        #
        # async def run_pulumi():
        #    stack = create_or_select_stack(stack_name=PULUMI_STACK, project_name=PULUMI_PROJECT, work_dir=".")
        #    stack.set_config("pulumiservice:organization", {"value": PULUMI_ORG})
        #    await stack.up()
        #
        # asyncio.run(run_pulumi())
