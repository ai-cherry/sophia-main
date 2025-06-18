"""
Sophia AI - GitHub Integration Infrastructure as Code
This module defines GitHub resources using Pulumi
"""

import pulumi
import json
from pulumi import Config
import pulumi_github as github

# Load configuration
config = Config()
env = config.require("environment")  # development, staging, or production

# Get GitHub credentials from Pulumi config (encrypted)
github_token = config.require_secret("github_token")
github_org = config.require("github_org")

# Define environment-specific configurations
repo_visibility = {
    "development": "private",
    "staging": "private",
    "production": "private"
}

# Create a GitHub repository
repo = github.Repository(f"sophia-{env}",
    name=f"sophia-{env}",
    description=f"Sophia AI - Pay Ready's AI Assistant Orchestrator ({env})",
    visibility=repo_visibility.get(env, "private"),
    has_issues=True,
    has_projects=True,
    has_wiki=True,
    is_template=False,
    allow_merge_commit=True,
    allow_squash_merge=True,
    allow_rebase_merge=True,
    delete_branch_on_merge=True,
    auto_init=True,
    gitignore_template="Python",
    license_template="mit",
    archived=False,
    topics=["ai", "orchestrator", "pay-ready", "sophia", env]
)

# Create branch protection for the main branch
branch_protection = github.BranchProtection(f"sophia-{env}-main-protection",
    repository_id=repo.node_id,
    pattern="main",
    enforce_admins=True,
    allows_deletions=False,
    allows_force_pushes=False,
    required_linear_history=True,
    required_conversation_resolution=True,
    required_status_checks=[
        github.BranchProtectionRequiredStatusCheckArgs(
            context="test",
            strict=True
        )
    ],
    required_pull_request_reviews=github.BranchProtectionRequiredPullRequestReviewsArgs(
        dismiss_stale_reviews=True,
        require_code_owner_reviews=True,
        required_approving_review_count=1
    )
)

# Create GitHub team
team = github.Team(f"sophia-{env}-team",
    name=f"sophia-{env}",
    description=f"Team responsible for Sophia AI ({env})",
    privacy="closed",
    create_default_maintainer=True
)

# Add team to repository
team_repository = github.TeamRepository(f"sophia-{env}-team-repo",
    team_id=team.id,
    repository=repo.name,
    permission="maintain"
)

# Create GitHub Actions secrets
secrets = [
    {
        "name": "SNOWFLAKE_ACCOUNT",
        "value": config.require_secret("snowflake_account")
    },
    {
        "name": "SNOWFLAKE_USER",
        "value": config.require_secret("snowflake_user")
    },
    {
        "name": "SNOWFLAKE_PASSWORD",
        "value": config.require_secret("snowflake_password")
    },
    {
        "name": "SNOWFLAKE_WAREHOUSE",
        "value": config.require_secret("snowflake_warehouse")
    },
    {
        "name": "SNOWFLAKE_DATABASE",
        "value": config.require_secret("snowflake_database")
    },
    {
        "name": "SNOWFLAKE_SCHEMA",
        "value": config.require_secret("snowflake_schema")
    },
    {
        "name": "SNOWFLAKE_ROLE",
        "value": config.require_secret("snowflake_role")
    },
    {
        "name": "GONG_API_KEY",
        "value": config.require_secret("gong_api_key")
    },
    {
        "name": "GONG_API_SECRET",
        "value": config.require_secret("gong_api_secret")
    },
    {
        "name": "VERCEL_ACCESS_TOKEN",
        "value": config.require_secret("vercel_access_token")
    },
    {
        "name": "VERCEL_TEAM_ID",
        "value": config.require_secret("vercel_team_id")
    },
    {
        "name": "VERCEL_PROJECT_ID",
        "value": config.require_secret("vercel_project_id")
    },
    {
        "name": "VERCEL_ORG_ID",
        "value": config.require_secret("vercel_org_id")
    },
    {
        "name": "ESTUARY_API_KEY",
        "value": config.require_secret("estuary_api_key")
    },
    {
        "name": "ESTUARY_API_URL",
        "value": config.require_secret("estuary_api_url")
    },
    {
        "name": "PORTKEY_API_KEY",
        "value": config.require_secret("portkey_api_key")
    },
    {
        "name": "OPENROUTER_API_KEY",
        "value": config.require_secret("openrouter_api_key")
    },
    {
        "name": "LAMBDA_LABS_API_KEY",
        "value": config.require_secret("lambda_labs_api_key")
    },
    {
        "name": "LAMBDA_LABS_JUPYTER_PASSWORD",
        "value": config.require_secret("lambda_labs_jupyter_password")
    },
    {
        "name": "AIRBYTE_API_KEY",
        "value": config.require_secret("airbyte_api_key")
    },
    {
        "name": "AIRBYTE_PASSWORD",
        "value": config.require_secret("airbyte_password")
    },
    {
        "name": "PULUMI_ACCESS_TOKEN",
        "value": config.require_secret("pulumi_access_token")
    },
    {
        "name": "SLACK_WEBHOOK_URL",
        "value": config.require_secret("slack_webhook_url")
    }
]

# Create GitHub Actions secrets
for secret in secrets:
    github_secret = github.ActionsSecret(f"sophia-{env}-{secret['name']}",
        repository=repo.name,
        secret_name=secret["name"],
        plaintext_value=secret["value"]
    )

# Create GitHub Actions environment secrets for environment-specific values
environment_secrets = {
    "development": [
        {
            "name": "SNOWFLAKE_WAREHOUSE_DEVELOPMENT",
            "value": config.require_secret("snowflake_warehouse_development")
        },
        {
            "name": "SNOWFLAKE_DATABASE_DEVELOPMENT",
            "value": config.require_secret("snowflake_database_development")
        },
        {
            "name": "SNOWFLAKE_SCHEMA_DEVELOPMENT",
            "value": config.require_secret("snowflake_schema_development")
        },
        {
            "name": "SNOWFLAKE_ROLE_DEVELOPMENT",
            "value": config.require_secret("snowflake_role_development")
        },
        {
            "name": "VERCEL_PROJECT_ID_DEVELOPMENT",
            "value": config.require_secret("vercel_project_id_development")
        }
    ],
    "staging": [
        {
            "name": "SNOWFLAKE_WAREHOUSE_STAGING",
            "value": config.require_secret("snowflake_warehouse_staging")
        },
        {
            "name": "SNOWFLAKE_DATABASE_STAGING",
            "value": config.require_secret("snowflake_database_staging")
        },
        {
            "name": "SNOWFLAKE_SCHEMA_STAGING",
            "value": config.require_secret("snowflake_schema_staging")
        },
        {
            "name": "SNOWFLAKE_ROLE_STAGING",
            "value": config.require_secret("snowflake_role_staging")
        },
        {
            "name": "VERCEL_PROJECT_ID_STAGING",
            "value": config.require_secret("vercel_project_id_staging")
        }
    ],
    "production": [
        {
            "name": "SNOWFLAKE_WAREHOUSE_PRODUCTION",
            "value": config.require_secret("snowflake_warehouse_production")
        },
        {
            "name": "SNOWFLAKE_DATABASE_PRODUCTION",
            "value": config.require_secret("snowflake_database_production")
        },
        {
            "name": "SNOWFLAKE_SCHEMA_PRODUCTION",
            "value": config.require_secret("snowflake_schema_production")
        },
        {
            "name": "SNOWFLAKE_ROLE_PRODUCTION",
            "value": config.require_secret("snowflake_role_production")
        },
        {
            "name": "VERCEL_PROJECT_ID_PRODUCTION",
            "value": config.require_secret("vercel_project_id_production")
        }
    ]
}

# Create GitHub Actions environment
environment = github.ActionsEnvironment(f"sophia-{env}-environment",
    repository=repo.name,
    environment=env,
    reviewers=[
        github.ActionsEnvironmentReviewersArgs(
            teams=[team.id]
        )
    ],
    deployment_branch_policy=github.ActionsEnvironmentDeploymentBranchPolicyArgs(
        protected_branches=True,
        custom_branch_policies=False
    )
)

# Create GitHub Actions environment secrets
for secret in environment_secrets.get(env, []):
    github_environment_secret = github.ActionsEnvironmentSecret(f"sophia-{env}-{secret['name']}",
        repository=repo.name,
        environment=environment.environment,
        secret_name=secret["name"],
        plaintext_value=secret["value"]
    )

# Export outputs
pulumi.export("github_repository_name", repo.name)
pulumi.export("github_repository_url", repo.html_url)
pulumi.export("github_team_name", team.name)
pulumi.export("github_environment", env)
