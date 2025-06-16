"""
Sophia AI - Infrastructure as Code
Pulumi configuration for Lambda Labs deployment

This module defines the infrastructure for deploying Sophia AI to production.
"""

import pulumi
import pulumi_aws as aws
import pulumi_kubernetes as k8s
from pulumi import Config, Output, export
import json

# Get configuration
config = Config()
project_name = "sophia-ai"
environment = config.get("environment") or "production"

# Get Lambda Labs configuration
lambda_labs_config = {
    "instance_type": config.get("instance_type") or "gpu.a100.1x",
    "region": config.get("region") or "us-west-1",
    "ssh_key_name": config.get("ssh_key_name") or "sophia-deploy-key"
}

# Tags for all resources
default_tags = {
    "Project": project_name,
    "Environment": environment,
    "ManagedBy": "Pulumi",
    "Company": "PayReady"
}

# Create VPC for networking isolation
vpc = aws.ec2.Vpc(
    f"{project_name}-vpc",
    cidr_block="10.0.0.0/16",
    enable_dns_hostnames=True,
    enable_dns_support=True,
    tags={**default_tags, "Name": f"{project_name}-vpc"}
)

# Create public subnet
public_subnet = aws.ec2.Subnet(
    f"{project_name}-public-subnet",
    vpc_id=vpc.id,
    cidr_block="10.0.1.0/24",
    availability_zone="us-west-1a",
    map_public_ip_on_launch=True,
    tags={**default_tags, "Name": f"{project_name}-public-subnet"}
)

# Create private subnet for databases
private_subnet = aws.ec2.Subnet(
    f"{project_name}-private-subnet",
    vpc_id=vpc.id,
    cidr_block="10.0.2.0/24",
    availability_zone="us-west-1b",
    tags={**default_tags, "Name": f"{project_name}-private-subnet"}
)

# Internet Gateway
igw = aws.ec2.InternetGateway(
    f"{project_name}-igw",
    vpc_id=vpc.id,
    tags={**default_tags, "Name": f"{project_name}-igw"}
)

# Route table for public subnet
public_route_table = aws.ec2.RouteTable(
    f"{project_name}-public-rt",
    vpc_id=vpc.id,
    routes=[{
        "cidr_block": "0.0.0.0/0",
        "gateway_id": igw.id
    }],
    tags={**default_tags, "Name": f"{project_name}-public-rt"}
)

# Associate route table with public subnet
public_route_association = aws.ec2.RouteTableAssociation(
    f"{project_name}-public-rta",
    subnet_id=public_subnet.id,
    route_table_id=public_route_table.id
)

# Security Groups
# Application security group
app_security_group = aws.ec2.SecurityGroup(
    f"{project_name}-app-sg",
    vpc_id=vpc.id,
    description="Security group for Sophia AI application",
    ingress=[
        # HTTP
        {
            "protocol": "tcp",
            "from_port": 80,
            "to_port": 80,
            "cidr_blocks": ["0.0.0.0/0"]
        },
        # HTTPS
        {
            "protocol": "tcp",
            "from_port": 443,
            "to_port": 443,
            "cidr_blocks": ["0.0.0.0/0"]
        },
        # Flask app
        {
            "protocol": "tcp",
            "from_port": 5000,
            "to_port": 5000,
            "cidr_blocks": ["0.0.0.0/0"]
        },
        # SSH (restricted)
        {
            "protocol": "tcp",
            "from_port": 22,
            "to_port": 22,
            "cidr_blocks": [config.get("admin_cidr") or "0.0.0.0/0"]
        }
    ],
    egress=[{
        "protocol": "-1",
        "from_port": 0,
        "to_port": 0,
        "cidr_blocks": ["0.0.0.0/0"]
    }],
    tags={**default_tags, "Name": f"{project_name}-app-sg"}
)

# Database security group
db_security_group = aws.ec2.SecurityGroup(
    f"{project_name}-db-sg",
    vpc_id=vpc.id,
    description="Security group for databases",
    ingress=[
        # PostgreSQL
        {
            "protocol": "tcp",
            "from_port": 5432,
            "to_port": 5432,
            "security_groups": [app_security_group.id]
        },
        # Redis
        {
            "protocol": "tcp",
            "from_port": 6379,
            "to_port": 6379,
            "security_groups": [app_security_group.id]
        }
    ],
    egress=[{
        "protocol": "-1",
        "from_port": 0,
        "to_port": 0,
        "cidr_blocks": ["0.0.0.0/0"]
    }],
    tags={**default_tags, "Name": f"{project_name}-db-sg"}
)

# RDS PostgreSQL Database
db_subnet_group = aws.rds.SubnetGroup(
    f"{project_name}-db-subnet-group",
    subnet_ids=[public_subnet.id, private_subnet.id],
    tags={**default_tags, "Name": f"{project_name}-db-subnet-group"}
)

postgres_db = aws.rds.Instance(
    f"{project_name}-postgres",
    engine="postgres",
    engine_version="15",
    instance_class="db.t3.medium",
    allocated_storage=100,
    storage_encrypted=True,
    db_name="sophia_payready",
    username="sophia",
    password=config.get_secret("db_password") or "change_me_in_production",
    vpc_security_group_ids=[db_security_group.id],
    db_subnet_group_name=db_subnet_group.name,
    backup_retention_period=7,
    backup_window="03:00-04:00",
    maintenance_window="Mon:04:00-Mon:05:00",
    skip_final_snapshot=False,
    final_snapshot_identifier=f"{project_name}-final-snapshot",
    tags={**default_tags, "Name": f"{project_name}-postgres"}
)

# ElastiCache Redis
redis_subnet_group = aws.elasticache.SubnetGroup(
    f"{project_name}-redis-subnet-group",
    subnet_ids=[public_subnet.id, private_subnet.id],
    tags={**default_tags, "Name": f"{project_name}-redis-subnet-group"}
)

redis_cluster = aws.elasticache.Cluster(
    f"{project_name}-redis",
    engine="redis",
    node_type="cache.t3.micro",
    num_cache_nodes=1,
    parameter_group_name="default.redis7",
    subnet_group_name=redis_subnet_group.name,
    security_group_ids=[db_security_group.id],
    tags={**default_tags, "Name": f"{project_name}-redis"}
)

# Lambda Labs GPU Instance (Main Application Server)
# User data script for instance initialization
user_data_script = f"""#!/bin/bash
set -e

# Update system
apt-get update
apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
usermod -aG docker ubuntu

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Install monitoring tools
apt-get install -y htop iotop nethogs

# Clone repository (replace with your actual repo)
cd /home/ubuntu
git clone https://github.com/payready/sophia-ai.git
cd sophia-ai

# Create .env file with configuration
cat > .env << EOF
SOPHIA_ENV=production
POSTGRES_HOST={postgres_db.endpoint}
POSTGRES_PORT=5432
POSTGRES_USER=sophia
POSTGRES_PASSWORD={config.get_secret("db_password") or "change_me_in_production"}
POSTGRES_DB=sophia_payready

REDIS_HOST={redis_cluster.cache_nodes[0].address}
REDIS_PORT=6379

SECRET_KEY={config.get_secret("secret_key") or "generate_a_secure_key"}
SOPHIA_MASTER_KEY={config.get_secret("master_key") or "generate_a_secure_master_key"}

# Add other environment variables as needed
EOF

# Start services
docker-compose up -d

# Setup systemd service
cat > /etc/systemd/system/sophia-ai.service << EOF
[Unit]
Description=Sophia AI Service
After=docker.service
Requires=docker.service

[Service]
Type=simple
WorkingDirectory=/home/ubuntu/sophia-ai
ExecStart=/usr/local/bin/docker-compose up
ExecStop=/usr/local/bin/docker-compose down
Restart=always
User=ubuntu

[Install]
WantedBy=multi-user.target
EOF

systemctl enable sophia-ai
systemctl start sophia-ai
"""

# Create the GPU instance
gpu_instance = aws.ec2.Instance(
    f"{project_name}-gpu-instance",
    instance_type=lambda_labs_config["instance_type"],
    ami="ami-0c55b159cbfafe1f0",  # Ubuntu 22.04 LTS
    key_name=lambda_labs_config["ssh_key_name"],
    vpc_security_group_ids=[app_security_group.id],
    subnet_id=public_subnet.id,
    user_data=user_data_script,
    root_block_device={
        "volume_size": 200,
        "volume_type": "gp3",
        "encrypted": True
    },
    tags={**default_tags, "Name": f"{project_name}-gpu-instance"}
)

# Elastic IP for consistent access
eip = aws.ec2.Eip(
    f"{project_name}-eip",
    instance=gpu_instance.id,
    tags={**default_tags, "Name": f"{project_name}-eip"}
)

# S3 Bucket for backups and artifacts
backup_bucket = aws.s3.Bucket(
    f"{project_name}-backups",
    acl="private",
    versioning={"enabled": True},
    server_side_encryption_configuration={
        "rule": {
            "apply_server_side_encryption_by_default": {
                "sse_algorithm": "AES256"
            }
        }
    },
    lifecycle_rules=[{
        "id": "expire-old-backups",
        "enabled": True,
        "transitions": [{
            "days": 30,
            "storage_class": "STANDARD_IA"
        }],
        "expiration": {"days": 90}
    }],
    tags={**default_tags, "Name": f"{project_name}-backups"}
)

# CloudWatch Log Groups
app_log_group = aws.cloudwatch.LogGroup(
    f"{project_name}-app-logs",
    retention_in_days=30,
    tags={**default_tags, "Name": f"{project_name}-app-logs"}
)

# CloudWatch Alarms
cpu_alarm = aws.cloudwatch.MetricAlarm(
    f"{project_name}-cpu-alarm",
    comparison_operator="GreaterThanThreshold",
    evaluation_periods=2,
    metric_name="CPUUtilization",
    namespace="AWS/EC2",
    period=300,
    statistic="Average",
    threshold=80,
    alarm_description="Alarm when CPU exceeds 80%",
    dimensions={"InstanceId": gpu_instance.id}
)

# Outputs
export("vpc_id", vpc.id)
export("gpu_instance_id", gpu_instance.id)
export("gpu_instance_public_ip", eip.public_ip)
export("postgres_endpoint", postgres_db.endpoint)
export("redis_endpoint", redis_cluster.cache_nodes[0].address)
export("backup_bucket", backup_bucket.id)

# Application URLs
export("app_url", Output.concat("http://", eip.public_ip, ":5000"))
export("prometheus_url", Output.concat("http://", eip.public_ip, ":9090"))
export("grafana_url", Output.concat("http://", eip.public_ip, ":3000"))

# SSH command
export("ssh_command", Output.concat("ssh -i ", lambda_labs_config["ssh_key_name"], ".pem ubuntu@", eip.public_ip)) 