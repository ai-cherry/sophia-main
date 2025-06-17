"""
Sophia AI - Infrastructure as Code
Pulumi configuration for deploying to Lambda Labs and Vercel.

This script assumes:
1. A Lambda Labs instance is already provisioned and accessible via SSH.
2. Secrets are managed via Pulumi ESC and accessed through Pulumi Config.
3. The project structure includes a 'docker-compose.yml' at the root for backend services
   and a 'frontend/' directory configured for Vercel deployment.
"""

import pulumi
import pulumi_command as command
import pulumi_vercel as vercel
from pulumi import Config, Output, asset, export

# --- Configuration ---
config = Config()

# Project settings
project_name = config.get("project_name") or "sophia-ai"
environment = config.get("environment") or "production"
app_domain = config.get("app_domain") # e.g., "sophia.payready.com" - used for Vercel and backend API URL

# Lambda Labs instance configuration (assumed to be existing)
lambda_labs_instance_ip = config.require("lambda_labs_instance_ip")
lambda_labs_ssh_user = config.get("lambda_labs_ssh_user") or "ubuntu"
lambda_labs_ssh_private_key_path = config.require_secret("lambda_labs_ssh_private_key_path") # Path to local SSH private key

# Git repository for the application
git_repo_url = config.get("git_repo_url") or "https://github.com/ai-cherry/sophia-main.git" # Default to your repo
git_branch = config.get("git_branch") or "main"
app_dir_on_instance = f"/home/{lambda_labs_ssh_user}/{project_name}"

# --- Secrets to be injected into .env on Lambda Labs instance ---
# These should be configured in Pulumi ESC and mapped in Pulumi.yaml or Pulumi.<stack>.yaml
db_password = config.get_secret("POSTGRES_PASSWORD") or "sophia_pass_pulumi_default" # Default from docker-compose
app_secret_key = config.get_secret("SECRET_KEY") or "default_app_secret_key_pulumi"
admin_username = config.get_secret("ADMIN_USERNAME") or "admin_pulumi"
admin_password = config.get_secret("ADMIN_PASSWORD") or "admin_pass_pulumi"
openai_api_key = config.get_secret("OPENAI_API_KEY")
anthropic_api_key = config.get_secret("ANTHROPIC_API_KEY")
hubspot_api_key = config.get_secret("HUBSPOT_API_KEY")
gong_api_key = config.get_secret("GONG_API_KEY")
gong_api_secret = config.get_secret("GONG_API_SECRET")
slack_bot_token = config.get_secret("SLACK_BOT_TOKEN")
slack_app_token = config.get_secret("SLACK_APP_TOKEN")
slack_signing_secret = config.get_secret("SLACK_SIGNING_SECRET")
pinecone_api_key = config.get_secret("PINECONE_API_KEY")
weaviate_api_key = config.get_secret("WEAVIATE_API_KEY")
weaviate_url = config.get_secret("WEAVIATE_URL")
grafana_admin_password = config.get_secret("GRAFANA_ADMIN_PASSWORD") or "admin_grafana_pulumi"

# Construct the .env file content
# Note: Pulumi Outputs are used here to handle secret resolution.
# The actual writing of the file happens on the remote machine.
env_file_content = Output.all(
    db_password=db_password,
    app_secret_key=app_secret_key,
    admin_username=admin_username,
    admin_password=admin_password,
    openai_api_key=openai_api_key,
    anthropic_api_key=anthropic_api_key,
    hubspot_api_key=hubspot_api_key,
    gong_api_key=gong_api_key,
    gong_api_secret=gong_api_secret,
    slack_bot_token=slack_bot_token,
    slack_app_token=slack_app_token,
    slack_signing_secret=slack_signing_secret,
    pinecone_api_key=pinecone_api_key,
    weaviate_api_key=weaviate_api_key,
    weaviate_url=weaviate_url,
    grafana_admin_password=grafana_admin_password,
    app_domain=app_domain
).apply(lambda secrets: f"""
DATABASE_URL=postgresql://sophia:{secrets['db_password']}@sophia-postgres:5432/sophia_payready
REDIS_URL=redis://sophia-redis:6379
SECRET_KEY={secrets['app_secret_key']}
ADMIN_USERNAME={secrets['admin_username']}
ADMIN_PASSWORD={secrets['admin_password']}
OPENAI_API_KEY={secrets['openai_api_key']}
ANTHROPIC_API_KEY={secrets['anthropic_api_key']}
HUBSPOT_API_KEY={secrets['hubspot_api_key']}
GONG_API_KEY={secrets['gong_api_key']}
GONG_API_SECRET={secrets['gong_api_secret']}
SLACK_BOT_TOKEN={secrets['slack_bot_token']}
SLACK_APP_TOKEN={secrets['slack_app_token']}
SLACK_SIGNING_SECRET={secrets['slack_signing_secret']}
PINECONE_API_KEY={secrets['pinecone_api_key']}
WEAVIATE_API_KEY={secrets['weaviate_api_key']}
WEAVIATE_URL={secrets['weaviate_url']}
GRAFANA_ADMIN_PASSWORD={secrets['grafana_admin_password']}
# Add any other necessary environment variables here
# Example: API_URL for frontend, if different from Vercel default
# VITE_API_URL=https://{secrets['app_domain']}/api 
# (This is usually set in Vercel's settings, but can be managed here too)
""")

# --- SSH Connection Details for Lambda Labs Instance ---
ssh_connection = command.remote.ConnectionArgs(
    host=lambda_labs_instance_ip,
    user=lambda_labs_ssh_user,
    private_key=lambda_labs_ssh_private_key_path.apply(lambda p: open(p).read())
)

# --- Setup Script for Lambda Labs Instance ---
# This script will be executed on the remote instance.
# It ensures prerequisites, clones the repo, creates .env, and starts services.
setup_script = Output.all(env_content=env_file_content, app_dir=app_dir_on_instance, repo_url=git_repo_url, branch=git_branch, ssh_user=lambda_labs_ssh_user).apply(
    lambda args: f"""
set -e
echo "--- Starting Sophia AI Setup on Lambda Labs Instance ---"

# 0. Update package list and install prerequisites
sudo apt-get update -y
sudo apt-get install -y git curl wget

# 1. Install Docker if not already present
if ! command -v docker &> /dev/null
then
    echo "Docker not found, installing..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker {args['ssh_user']}
    echo "Docker installed."
else
    echo "Docker already installed."
fi

# 2. Install Docker Compose if not already present
if ! command -v docker-compose &> /dev/null
then
    echo "Docker Compose not found, installing..."
    LATEST_COMPOSE=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep 'tag_name' | cut -d\\\" -f4)
    sudo curl -L "https://github.com/docker/compose/releases/download/${{LATEST_COMPOSE}}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    echo "Docker Compose installed."
else
    echo "Docker Compose already installed."
fi

# 3. Clone or update the application repository
echo "Cloning/updating application repository from {args['repo_url']} (branch: {args['branch']})..."
if [ -d "{args['app_dir']}/.git" ]; then
    cd {args['app_dir']}
    git fetch origin
    git reset --hard origin/{args['branch']}
    git pull origin {args['branch']}
    echo "Repository updated."
else
    git clone --branch {args['branch']} {args['repo_url']} {args['app_dir']}
    cd {args['app_dir']}
    echo "Repository cloned."
fi

# 4. Create .env file
echo "Creating .env file in {args['app_dir']}..."
cat << EOF_ENV > {args['app_dir']}/.env
{args['env_content']}
EOF_ENV
echo ".env file created."

# 5. Start services using Docker Compose
echo "Starting services with Docker Compose..."
cd {args['app_dir']}
# Ensure docker-compose can be run by current user, or use sudo if needed and configured
# For non-root user added to docker group, sudo is not needed for docker commands.
# However, docker-compose might need to be run with sudo if not installed system-wide for all users or if permissions issues arise.
# Assuming user is in docker group:
docker-compose down || true # Stop existing services if any
docker-compose pull # Pull latest images
docker-compose up -d --build # Start all services in detached mode, build if necessary
echo "Docker Compose services started."

# 6. (Optional) Setup systemd service for auto-restart (example from original script)
# This part might need adjustment based on how docker-compose is run (sudo or not)
# For simplicity, this is commented out. Manual restart or a more robust process manager might be preferred.
# echo "Setting up systemd service for sophia-ai..."
# sudo bash -c 'cat > /etc/systemd/system/sophia-ai.service << EOF_SYSTEMD
# [Unit]
# Description=Sophia AI Service
# After=docker.service network-online.target
# Requires=docker.service network-online.target
#
# [Service]
# Type=simple
# WorkingDirectory={args['app_dir']}
# ExecStart=/usr/local/bin/docker-compose up
# ExecStop=/usr/local/bin/docker-compose down
# Restart=always
# User={args['ssh_user']} # Or root if docker-compose requires sudo
# EnvironmentFile={args['app_dir']}/.env # Make .env available to systemd service
#
# [Install]
# WantedBy=multi-user.target
# EOF_SYSTEMD'
#
# sudo systemctl daemon-reload
# sudo systemctl enable sophia-ai
# sudo systemctl restart sophia-ai # Use restart to ensure it picks up changes
# echo "Systemd service sophia-ai configured and started."

echo "--- Sophia AI Setup on Lambda Labs Instance Complete ---"
"""
)

# --- Execute Setup Script on Lambda Labs Instance ---
# This command resource will run the setup_script on the remote instance.
# It depends on the env_file_content being resolved.
lambda_setup = command.remote.Command(
    "lambda-instance-setup",
    connection=ssh_connection,
    create=setup_script,
    # update=setup_script, # Optionally re-run on updates. Be careful with state.
    opts=pulumi.ResourceOptions(depends_on=[env_file_content.is_secret_sentinel]) # Ensure env_content is ready
)

# --- Vercel Frontend Deployment ---
# Assumes 'frontend' directory is at the root of your Git repository.
# Reads vercel.json for build settings.
try:
    with open("../vercel.json") as f: # Adjust path if infrastructure dir is not a direct child of root
        vercel_config_json = json.load(f)
except FileNotFoundError:
    pulumi.log.warn("vercel.json not found at ../vercel.json. Skipping Vercel deployment.")
    vercel_config_json = None
    sophia_frontend_project = None
    frontend_deployment = None
    frontend_url = Output.secret("Vercel deployment skipped")

if vercel_config_json:
    # Vercel Project
    sophia_frontend_project = vercel.Project(f"{project_name}-frontend",
        name=f"{project_name}-frontend-{environment}",
        framework=vercel_config_json.get("framework", "vite"),
        build_command=vercel_config_json.get("buildCommand"),
        output_directory=vercel_config_json.get("outputDirectory"),
        root_directory="frontend", # Assuming frontend code is in 'frontend/' directory at repo root
        environment_variables=[
            vercel.ProjectEnvironmentArgs(
                key="VITE_API_URL",
                value=Output.concat("https://", app_domain, "/api") if app_domain else lambda_labs_instance_ip.apply(lambda ip: f"http://{ip}:5001/api"), # Port 5001 from docker-compose sophia-app
                target=["production", "preview", "development"]
            ),
            # Add other Vercel environment variables here if needed
        ],
        git_repository=vercel.ProjectGitRepositoryArgs(
            type="github",
            repo=git_repo_url.apply(lambda url: url.replace("https://github.com/", "")), # e.g., "ai-cherry/sophia-main"
            # production_branch=git_branch # Deploy specific branch to production
        ),
        # serverless_function_region="sfo1" # Example, if you have serverless functions
    )

    # Trigger a deployment (optional, Vercel usually deploys on commit to production_branch)
    # For explicit deployment control:
    # frontend_deployment = vercel.Deployment(f"{project_name}-frontend-deployment",
    #     project_id=sophia_frontend_project.id,
    #     ref=git_branch, # Deploy from this git ref
    #     production=True, # Mark as production deployment
    #     opts=pulumi.ResourceOptions(depends_on=[sophia_frontend_project, lambda_setup]) # Deploy after backend is up
    # )
    # frontend_url = frontend_deployment.url

    # If relying on Vercel's Git integration, the project URL is more relevant
    # The primary domain will be configured in Vercel UI or via vercel.ProjectDomain
    if app_domain:
        project_domain = vercel.ProjectDomain(f"{project_name}-frontend-domain",
            project_id=sophia_frontend_project.id,
            domain=app_domain,
            # redirect_to_www=True # Optional
        )
        frontend_url = project_domain.domain.apply(lambda d: f"https://{d}")
    else:
        # Vercel assigns a default URL if no custom domain
        frontend_url = sophia_frontend_project.aliases.apply(
            lambda aliases: f"https://{aliases[0]}" if aliases and len(aliases) > 0 else "Vercel URL not available yet"
        )


# --- Outputs ---
export("lambda_labs_instance_ip", lambda_labs_instance_ip)
export("lambda_setup_stdout", lambda_setup.stdout) # Output of the setup script
export("application_backend_base_url", lambda_labs_instance_ip.apply(lambda ip: f"http://{ip}:5001")) # sophia-app port from docker-compose
export("prometheus_url_on_lambda", lambda_labs_instance_ip.apply(lambda ip: f"http://{ip}:9091")) # Prometheus port from docker-compose
export("grafana_url_on_lambda", lambda_labs_instance_ip.apply(lambda ip: f"http://{ip}:3001")) # Grafana port from docker-compose

if sophia_frontend_project:
    export("vercel_frontend_project_id", sophia_frontend_project.id)
    export("vercel_frontend_url", frontend_url)

pulumi.log.info("To apply these changes, run 'pulumi up'.")
pulumi.log.info("Ensure your Pulumi stack configuration (Pulumi.<stack>.yaml) has values for:")
pulumi.log.info("  'lambda_labs_instance_ip'")
pulumi.log.info("  'lambda_labs_ssh_private_key_path' (secret)")
pulumi.log.info("  'app_domain' (optional, for Vercel custom domain)")
pulumi.log.info("And all required application secrets (e.g., POSTGRES_PASSWORD, OPENAI_API_KEY, etc.) are set in Pulumi ESC.")
