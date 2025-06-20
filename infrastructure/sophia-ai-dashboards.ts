/**
 * Sophia AI Dashboards - Main Deployment
 * Uses AI-powered dashboard generation instead of manual Retool configuration
 */

import { SophiaAIDashboard } from './ai-dashboard-generator';
import * as pulumi from '@pulumi/pulumi';

// Configuration
const config = new pulumi.Config();
const environment = pulumi.getStack();

// CEO Dashboard - Executive Intelligence
const ceoDashboard = new SophiaAIDashboard('ceo-dashboard', {
    type: 'ceo',
    dataSources: ['gong', 'snowflake', 'openai', 'hubspot'],
    features: [
        'revenue-analytics',
        'sales-performance',
        'ai-insights',
        'real-time-alerts',
        'predictive-analytics',
        'executive-summary'
    ],
    scalingRequirements: {
        minInstances: 2,
        maxInstances: 8,
        targetCPU: 60
    }
});

// Knowledge Admin Dashboard - Content Management
const knowledgeDashboard = new SophiaAIDashboard('knowledge-dashboard', {
    type: 'knowledge',
    dataSources: ['pinecone', 'openai', 'slack', 'github'],
    features: [
        'content-management',
        'knowledge-search',
        'ai-content-generation',
        'usage-analytics',
        'quality-metrics',
        'admin-controls'
    ],
    scalingRequirements: {
        minInstances: 1,
        maxInstances: 5,
        targetCPU: 70
    }
});

// Project Intelligence Dashboard - Development Insights
const projectDashboard = new SophiaAIDashboard('project-dashboard', {
    type: 'project',
    dataSources: ['github', 'linear', 'pulumi', 'vercel'],
    features: [
        'project-tracking',
        'deployment-status',
        'code-analytics',
        'team-performance',
        'infrastructure-monitoring',
        'ai-recommendations'
    ],
    scalingRequirements: {
        minInstances: 1,
        maxInstances: 6,
        targetCPU: 75
    }
});

// Export dashboard URLs and information
export const dashboards = {
    ceo: {
        url: ceoDashboard.url,
        cluster: ceoDashboard.cluster.name,
        type: 'Executive Intelligence Dashboard'
    },
    knowledge: {
        url: knowledgeDashboard.url,
        cluster: knowledgeDashboard.cluster.name,
        type: 'Knowledge Management Dashboard'
    },
    project: {
        url: projectDashboard.url,
        cluster: projectDashboard.cluster.name,
        type: 'Project Intelligence Dashboard'
    }
};

export const deploymentInfo = {
    environment,
    timestamp: new Date().toISOString(),
    dashboardCount: 3,
    totalDataSources: ['gong', 'snowflake', 'openai', 'hubspot', 'pinecone', 'slack', 'github', 'linear', 'pulumi', 'vercel'],
    aiFeatures: [
        'Natural Language Queries',
        'Predictive Analytics',
        'Automated Insights',
        'Real-time Recommendations',
        'Intelligent Alerting'
    ]
};

// Output key information
export const sophiaAIDashboardSummary = pulumi.all([
    ceoDashboard.url,
    knowledgeDashboard.url,
    projectDashboard.url
]).apply(([ceoUrl, knowledgeUrl, projectUrl]) => ({
    message: `🎉 Sophia AI Dashboards Successfully Deployed!`,
    dashboards: {
        ceo: `http://${ceoUrl}`,
        knowledge: `http://${knowledgeUrl}`,
        project: `http://${projectUrl}`
    },
    features: [
        '✅ AI-Powered Infrastructure Generation',
        '✅ Auto-scaling Based on Usage',
        '✅ Real-time Data Integration',
        '✅ Natural Language Queries',
        '✅ Predictive Analytics',
        '✅ Enterprise Security',
        '✅ Cost Optimization'
    ],
    nextSteps: [
        '1. Configure data source API keys',
        '2. Set up monitoring and alerting',
        '3. Configure user access and permissions',
        '4. Enable AI features and training',
        '5. Customize dashboard themes and layouts'
    ]
}));
