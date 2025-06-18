"""
Sophia AI - Vercel Deployment Infrastructure as Code
This module defines Vercel deployment resources using Pulumi
"""

import pulumi
import pulumi_vercel as vercel
from pulumi import Config

# Load configuration
config = Config()
env = config.require("environment")  # development, staging, or production

# Get Vercel credentials from Pulumi config (encrypted)
vercel_token = config.require_secret("vercel_token")
vercel_team_id = config.get("vercel_team_id")

# Define environment-specific configurations
project_names = {
    "development": "sophia-dev",
    "staging": "sophia-staging",
    "production": "sophia"
}

domains = {
    "development": "dev.sophia.payready.com",
    "staging": "staging.sophia.payready.com",
    "production": "sophia.payready.com"
}

# Create a Vercel project
project = vercel.Project("sophia_project",
    name=project_names.get(env, project_names["development"]),
    framework="nextjs",
    git_repository={
        "type": "github",
        "repo": "payready/sophia-frontend",
        "production_branch": "main" if env == "production" else env
    },
    environment=[
        vercel.ProjectEnvironmentArgs(
            key="NODE_ENV",
            value=env,
            target=["production", "preview", "development"]
        ),
        vercel.ProjectEnvironmentArgs(
            key="NEXT_PUBLIC_API_URL",
            value=f"https://api-{env}.sophia.payready.com",
            target=["production", "preview", "development"]
        )
    ],
    team_id=vercel_team_id
)

# Create a Vercel domain
domain = vercel.Domain("sophia_domain",
    name=domains.get(env, domains["development"]),
    project_id=project.id,
    team_id=vercel_team_id
)

# Create a Vercel deployment
deployment = vercel.Deployment("sophia_deployment",
    project_id=project.id,
    production=True,
    team_id=vercel_team_id,
    opts=pulumi.ResourceOptions(depends_on=[project, domain])
)

# Export outputs
pulumi.export("vercel_project_name", project.name)
pulumi.export("vercel_domain", domain.name)
pulumi.export("vercel_deployment_url", deployment.url)
