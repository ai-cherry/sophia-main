/**
 * Sophia AI Dashboard Generator - Pulumi + Cursor AI Integration
 * Replaces manual Retool configuration with AI-powered infrastructure generation
 */

import * as aws from "@pulumi/aws";
import * as docker from "@pulumi/docker";
import * as pulumi from "@pulumi/pulumi";

export interface DashboardConfig {
    type: "ceo" | "knowledge" | "project";
    dataSources: string[];
    scalingRequirements?: {
        minInstances: number;
        maxInstances: number;
        targetCPU: number;
    };
    features: string[];
}

export class SophiaAIDashboard {
    public readonly url: pulumi.Output<string>;
    public readonly cluster: aws.ecs.Cluster;
    public readonly loadBalancer: aws.lb.LoadBalancer;

    constructor(name: string, config: DashboardConfig) {
        // Create VPC for dashboard infrastructure
        const vpc = new aws.ec2.Vpc(`${name}-vpc`, {
            cidrBlock: "10.0.0.0/16",
            enableDnsHostnames: true,
            enableDnsSupport: true,
            tags: {
                Name: `${name}-vpc`,
                Project: "sophia-ai",
                Environment: pulumi.getStack()
            }
        });

        // Create subnets
        const publicSubnet1 = new aws.ec2.Subnet(`${name}-public-1`, {
            vpcId: vpc.id,
            cidrBlock: "10.0.1.0/24",
            availabilityZone: "us-east-1a",
            mapPublicIpOnLaunch: true,
            tags: { Name: `${name}-public-1` }
        });

        const publicSubnet2 = new aws.ec2.Subnet(`${name}-public-2`, {
            vpcId: vpc.id,
            cidrBlock: "10.0.2.0/24",
            availabilityZone: "us-east-1b",
            mapPublicIpOnLaunch: true,
            tags: { Name: `${name}-public-2` }
        });

        const privateSubnet1 = new aws.ec2.Subnet(`${name}-private-1`, {
            vpcId: vpc.id,
            cidrBlock: "10.0.3.0/24",
            availabilityZone: "us-east-1a",
            tags: { Name: `${name}-private-1` }
        });

        const privateSubnet2 = new aws.ec2.Subnet(`${name}-private-2`, {
            vpcId: vpc.id,
            cidrBlock: "10.0.4.0/24",
            availabilityZone: "us-east-1b",
            tags: { Name: `${name}-private-2` }
        });

        // Internet Gateway
        const igw = new aws.ec2.InternetGateway(`${name}-igw`, {
            vpcId: vpc.id,
            tags: { Name: `${name}-igw` }
        });

        // Route table for public subnets
        const publicRouteTable = new aws.ec2.RouteTable(`${name}-public-rt`, {
            vpcId: vpc.id,
            routes: [{
                cidrBlock: "0.0.0.0/0",
                gatewayId: igw.id
            }],
            tags: { Name: `${name}-public-rt` }
        });

        // Associate route table with public subnets
        new aws.ec2.RouteTableAssociation(`${name}-public-1-rta`, {
            subnetId: publicSubnet1.id,
            routeTableId: publicRouteTable.id
        });

        new aws.ec2.RouteTableAssociation(`${name}-public-2-rta`, {
            subnetId: publicSubnet2.id,
            routeTableId: publicRouteTable.id
        });

        // Security group for load balancer
        const lbSecurityGroup = new aws.ec2.SecurityGroup(`${name}-lb-sg`, {
            vpcId: vpc.id,
            description: `Load balancer security group for ${name} dashboard`,
            ingress: [
                {
                    protocol: "tcp",
                    fromPort: 80,
                    toPort: 80,
                    cidrBlocks: ["0.0.0.0/0"]
                },
                {
                    protocol: "tcp",
                    fromPort: 443,
                    toPort: 443,
                    cidrBlocks: ["0.0.0.0/0"]
                }
            ],
            egress: [{
                protocol: "-1",
                fromPort: 0,
                toPort: 0,
                cidrBlocks: ["0.0.0.0/0"]
            }],
            tags: { Name: `${name}-lb-sg` }
        });

        // Security group for dashboard containers
        const dashboardSecurityGroup = new aws.ec2.SecurityGroup(`${name}-dashboard-sg`, {
            vpcId: vpc.id,
            description: `Dashboard security group for ${name}`,
            ingress: [{
                protocol: "tcp",
                fromPort: 3000,
                toPort: 3000,
                securityGroups: [lbSecurityGroup.id]
            }],
            egress: [{
                protocol: "-1",
                fromPort: 0,
                toPort: 0,
                cidrBlocks: ["0.0.0.0/0"]
            }],
            tags: { Name: `${name}-dashboard-sg` }
        });

        // Application Load Balancer
        this.loadBalancer = new aws.lb.LoadBalancer(`${name}-lb`, {
            internal: false,
            loadBalancerType: "application",
            securityGroups: [lbSecurityGroup.id],
            subnets: [publicSubnet1.id, publicSubnet2.id],
            enableDeletionProtection: false,
            tags: {
                Name: `${name}-lb`,
                Project: "sophia-ai"
            }
        });

        // Target group for dashboard
        const targetGroup = new aws.lb.TargetGroup(`${name}-tg`, {
            port: 3000,
            protocol: "HTTP",
            vpcId: vpc.id,
            targetType: "ip",
            healthCheck: {
                enabled: true,
                healthyThreshold: 2,
                interval: 30,
                matcher: "200",
                path: "/health",
                port: "traffic-port",
                protocol: "HTTP",
                timeout: 5,
                unhealthyThreshold: 2
            },
            tags: { Name: `${name}-tg` }
        });

        // Load balancer listener
        const listener = new aws.lb.Listener(`${name}-listener`, {
            loadBalancerArn: this.loadBalancer.arn,
            port: "80",
            protocol: "HTTP",
            defaultActions: [{
                type: "forward",
                targetGroupArn: targetGroup.arn
            }]
        });

        // ECS Cluster
        this.cluster = new aws.ecs.Cluster(`${name}-cluster`, {
            capacityProviders: ["FARGATE"],
            defaultCapacityProviderStrategy: [{
                capacityProvider: "FARGATE",
                weight: 1
            }],
            tags: {
                Name: `${name}-cluster`,
                Project: "sophia-ai"
            }
        });

        // IAM role for ECS task execution
        const executionRole = new aws.iam.Role(`${name}-execution-role`, {
            assumeRolePolicy: JSON.stringify({
                Version: "2012-10-17",
                Statement: [{
                    Action: "sts:AssumeRole",
                    Effect: "Allow",
                    Principal: {
                        Service: "ecs-tasks.amazonaws.com"
                    }
                }]
            })
        });

        new aws.iam.RolePolicyAttachment(`${name}-execution-role-policy`, {
            role: executionRole.name,
            policyArn: "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
        });

        // IAM role for ECS task
        const taskRole = new aws.iam.Role(`${name}-task-role`, {
            assumeRolePolicy: JSON.stringify({
                Version: "2012-10-17",
                Statement: [{
                    Action: "sts:AssumeRole",
                    Effect: "Allow",
                    Principal: {
                        Service: "ecs-tasks.amazonaws.com"
                    }
                }]
            })
        });

        // Generate dashboard-specific environment variables based on data sources
        const environmentVariables = this.generateEnvironmentVariables(config);

        // ECS Task Definition
        const taskDefinition = new aws.ecs.TaskDefinition(`${name}-task`, {
            family: `${name}-dashboard`,
            cpu: "512",
            memory: "1024",
            networkMode: "awsvpc",
            requiresCompatibilities: ["FARGATE"],
            executionRoleArn: executionRole.arn,
            taskRoleArn: taskRole.arn,
            containerDefinitions: JSON.stringify([{
                name: `${name}-dashboard`,
                image: `sophia-ai/${config.type}-dashboard:latest`,
                portMappings: [{
                    containerPort: 3000,
                    protocol: "tcp"
                }],
                environment: environmentVariables,
                logConfiguration: {
                    logDriver: "awslogs",
                    options: {
                        "awslogs-group": `/ecs/${name}-dashboard`,
                        "awslogs-region": "us-east-1",
                        "awslogs-stream-prefix": "ecs"
                    }
                },
                essential: true
            }]),
            tags: { Name: `${name}-task` }
        });

        // CloudWatch Log Group
        new aws.cloudwatch.LogGroup(`${name}-logs`, {
            name: `/ecs/${name}-dashboard`,
            retentionInDays: 30,
            tags: { Name: `${name}-logs` }
        });

        // ECS Service with auto-scaling
        const service = new aws.ecs.Service(`${name}-service`, {
            cluster: this.cluster.arn,
            taskDefinition: taskDefinition.arn,
            desiredCount: config.scalingRequirements?.minInstances || 2,
            launchType: "FARGATE",
            networkConfiguration: {
                subnets: [privateSubnet1.id, privateSubnet2.id],
                securityGroups: [dashboardSecurityGroup.id],
                assignPublicIp: false
            },
            loadBalancers: [{
                targetGroupArn: targetGroup.arn,
                containerName: `${name}-dashboard`,
                containerPort: 3000
            }],
            dependsOn: [listener],
            tags: { Name: `${name}-service` }
        });

        // Auto Scaling Target
        const scalingTarget = new aws.appautoscaling.Target(`${name}-scaling-target`, {
            maxCapacity: config.scalingRequirements?.maxInstances || 10,
            minCapacity: config.scalingRequirements?.minInstances || 2,
            resourceId: pulumi.interpolate`service/${this.cluster.name}/${service.name}`,
            scalableDimension: "ecs:service:DesiredCount",
            serviceNamespace: "ecs"
        });

        // Auto Scaling Policy
        new aws.appautoscaling.Policy(`${name}-scaling-policy`, {
            name: `${name}-cpu-scaling`,
            policyType: "TargetTrackingScaling",
            resourceId: scalingTarget.resourceId,
            scalableDimension: scalingTarget.scalableDimension,
            serviceNamespace: scalingTarget.serviceNamespace,
            targetTrackingScalingPolicyConfiguration: {
                predefinedMetricSpecification: {
                    predefinedMetricType: "ECSServiceAverageCPUUtilization"
                },
                targetValue: config.scalingRequirements?.targetCPU || 70
            }
        });

        // Data source integrations
        this.createDataSourceIntegrations(name, config.dataSources, vpc, privateSubnet1, privateSubnet2);

        // Export dashboard URL
        this.url = pulumi.interpolate`http://${this.loadBalancer.dnsName}`;
    }

    private generateEnvironmentVariables(config: DashboardConfig): Array<{name: string, value: string}> {
        const baseEnv = [
            { name: "NODE_ENV", value: "production" },
            { name: "DASHBOARD_TYPE", value: config.type },
            { name: "FEATURES", value: config.features.join(",") }
        ];

        // Add data source specific environment variables
        config.dataSources.forEach(source => {
            switch (source.toLowerCase()) {
                case "gong":
                    baseEnv.push(
                        { name: "GONG_API_KEY", value: "${GONG_API_KEY}" },
                        { name: "GONG_API_URL", value: "https://api.gong.io" }
                    );
                    break;
                case "snowflake":
                    baseEnv.push(
                        { name: "SNOWFLAKE_ACCOUNT", value: "${SNOWFLAKE_ACCOUNT}" },
                        { name: "SNOWFLAKE_USERNAME", value: "${SNOWFLAKE_USERNAME}" },
                        { name: "SNOWFLAKE_PASSWORD", value: "${SNOWFLAKE_PASSWORD}" }
                    );
                    break;
                case "openai":
                    baseEnv.push(
                        { name: "OPENAI_API_KEY", value: "${OPENAI_API_KEY}" }
                    );
                    break;
                case "pinecone":
                    baseEnv.push(
                        { name: "PINECONE_API_KEY", value: "${PINECONE_API_KEY}" },
                        { name: "PINECONE_INDEX", value: "sophia-ai-index" }
                    );
                    break;
            }
        });

        return baseEnv;
    }

    private createDataSourceIntegrations(
        name: string,
        dataSources: string[],
        vpc: aws.ec2.Vpc,
        subnet1: aws.ec2.Subnet,
        subnet2: aws.ec2.Subnet
    ) {
        dataSources.forEach(source => {
            // Create Lambda functions for each data source integration
            const integrationFunction = new aws.lambda.Function(`${name}-${source}-integration`, {
                runtime: aws.lambda.Runtime.NodeJS18dX,
                code: new pulumi.asset.AssetArchive({
                    ".": new pulumi.asset.FileArchive(`./integrations/${source}`)
                }),
                handler: "index.handler",
                environment: {
                    variables: {
                        [`${source.toUpperCase()}_API_KEY`]: pulumi.secret(`\${${source.toUpperCase()}_API_KEY}`)
                    }
                },
                vpcConfig: {
                    subnetIds: [subnet1.id, subnet2.id],
                    securityGroupIds: [] // Add appropriate security groups
                },
                tags: {
                    Name: `${name}-${source}-integration`,
                    Project: "sophia-ai",
                    DataSource: source
                }
            });

            // Create API Gateway for each integration
            new aws.apigateway.RestApi(`${name}-${source}-api`, {
                name: `${name}-${source}-integration`,
                description: `API Gateway for ${source} integration`,
                tags: {
                    Name: `${name}-${source}-api`,
                    Project: "sophia-ai"
                }
            });
        });
    }
}

// Export the dashboard class for use in other modules
export { SophiaAIDashboard as default };
