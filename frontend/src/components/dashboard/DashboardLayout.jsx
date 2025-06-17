import React, { useState, useEffect } from 'react';
import { 
  DollarSign, 
  Users, 
  TrendingUp, 
  Activity,
  BarChart3,
  Building2,
  Brain,
  Zap
} from 'lucide-react';
import Header from '../design-system/navigation/Header';
import MetricCard from '../design-system/cards/MetricCard';
import GlassCard from '../design-system/cards/GlassCard';
import Button from '../design-system/buttons/Button';
import { cn } from '@/lib/utils';
import api from '../../services/api';

// Tab configuration
const TABS = [
  { id: 'overview', label: 'Overview', icon: BarChart3 },
  { id: 'strategy', label: 'Strategy', icon: Brain },
  { id: 'operations', label: 'Operations', icon: Activity },
  { id: 'insights', label: 'AI Insights', icon: Zap },
];

const DashboardLayout = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fetch metrics from backend
  useEffect(() => {
    fetchMetrics();
  }, []);

  const fetchMetrics = async () => {
    try {
      setLoading(true);
      const data = await api.getCompanyMetrics();
      setMetrics(data);
      setError(null);
    } catch (err) {
      setError(err.message);
      // Use mock data for demonstration
      setMetrics({
        revenue: { value: '$331,000', change: '+18.5%', trend: 'up' },
        customers: { value: '1,247', change: '+12.3%', trend: 'up' },
        pipeline: { value: '$2.4M', change: '+23.1%', trend: 'up' },
        healthScore: { value: '92%', change: '+5.2%', trend: 'up' },
      });
    } finally {
      setLoading(false);
    }
  };

  const renderTabContent = () => {
    switch (activeTab) {
      case 'overview':
        return <OverviewTab metrics={metrics} loading={loading} />;
      case 'strategy':
        return <StrategyTab />;
      case 'operations':
        return <OperationsTab />;
      case 'insights':
        return <InsightsTab />;
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-slate-900">
      <Header 
        title="Sophia AI Dashboard"
        user={{ name: 'Admin User', role: 'Administrator' }}
      />
      
      <main className="pt-20">
        <div className="max-w-7xl mx-auto px-6 py-8">
          {/* KPI Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <MetricCard
              title="Monthly Revenue"
              value={metrics?.revenue?.value || '—'}
              change={metrics?.revenue?.change}
              trend={metrics?.revenue?.trend}
              icon={DollarSign}
              loading={loading}
            />
            <MetricCard
              title="Active Customers"
              value={metrics?.customers?.value || '—'}
              change={metrics?.customers?.change}
              trend={metrics?.customers?.trend}
              icon={Users}
              loading={loading}
            />
            <MetricCard
              title="Pipeline Value"
              value={metrics?.pipeline?.value || '—'}
              change={metrics?.pipeline?.change}
              trend={metrics?.pipeline?.trend}
              icon={TrendingUp}
              loading={loading}
            />
            <MetricCard
              title="Health Score"
              value={metrics?.healthScore?.value || '—'}
              change={metrics?.healthScore?.change}
              trend={metrics?.healthScore?.trend}
              icon={Activity}
              loading={loading}
            />
          </div>

          {/* Tab Navigation */}
          <GlassCard padding="small" className="mb-8">
            <div className="flex space-x-1">
              {TABS.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={cn(
                    "flex items-center space-x-2 px-4 py-2 rounded-lg font-medium transition-all duration-200",
                    activeTab === tab.id
                      ? "bg-purple-600 text-white"
                      : "text-gray-400 hover:text-white hover:bg-slate-700"
                  )}
                >
                  <tab.icon className="w-4 h-4" />
                  <span>{tab.label}</span>
                </button>
              ))}
            </div>
          </GlassCard>

          {/* Tab Content */}
          {renderTabContent()}
        </div>
      </main>
    </div>
  );
};

// Overview Tab Component
const OverviewTab = ({ metrics, loading }) => {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div className="lg:col-span-2">
        <GlassCard>
          <h2 className="text-h3 font-semibold mb-6">Revenue Trend</h2>
          {/* Chart component would go here */}
          <div className="h-64 bg-slate-700 rounded-lg flex items-center justify-center">
            <p className="text-gray-400">Revenue chart visualization</p>
          </div>
        </GlassCard>
      </div>
      
      <div className="space-y-6">
        <GlassCard>
          <h3 className="text-h4 font-medium mb-4">Quick Actions</h3>
          <div className="space-y-3">
            <Button 
              variant="primary" 
              className="w-full"
              icon={BarChart3}
            >
              Generate Report
            </Button>
            <Button 
              variant="secondary" 
              className="w-full"
              icon={Building2}
            >
              Property Analysis
            </Button>
          </div>
        </GlassCard>
        
        <GlassCard>
          <h3 className="text-h4 font-medium mb-4">AI Insights</h3>
          <div className="space-y-3">
            <div className="p-3 bg-purple-900/20 border border-purple-700 rounded-lg">
              <p className="text-sm text-purple-300">
                Revenue growth is 23% above market average
              </p>
            </div>
            <div className="p-3 bg-blue-900/20 border border-blue-700 rounded-lg">
              <p className="text-sm text-blue-300">
                Customer retention improved by 15% this quarter
              </p>
            </div>
          </div>
        </GlassCard>
      </div>
    </div>
  );
};

// Strategy Tab Component
const StrategyTab = () => {
  return (
    <GlassCard gradient>
      <h2 className="text-h2 font-semibold mb-6">Strategic Planning</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="space-y-4">
          <h3 className="text-h4 font-medium">Growth Opportunities</h3>
          <div className="space-y-3">
            {['Market Expansion', 'Product Development', 'Customer Acquisition'].map((item) => (
              <div key={item} className="p-4 bg-slate-800 rounded-lg hover:bg-slate-700 transition-colors cursor-pointer">
                <p className="font-medium text-white">{item}</p>
                <p className="text-sm text-gray-400 mt-1">Click to view detailed analysis</p>
              </div>
            ))}
          </div>
        </div>
        <div className="space-y-4">
          <h3 className="text-h4 font-medium">Risk Assessment</h3>
          <div className="p-4 bg-slate-800 rounded-lg">
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm text-gray-400">Overall Risk Score</span>
              <span className="text-2xl font-bold text-green-400">Low</span>
            </div>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Market Risk</span>
                <span className="text-green-400">Low</span>
              </div>
              <div className="flex justify-between text-sm">
                <span>Operational Risk</span>
                <span className="text-yellow-400">Medium</span>
              </div>
              <div className="flex justify-between text-sm">
                <span>Financial Risk</span>
                <span className="text-green-400">Low</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </GlassCard>
  );
};

// Operations Tab Component
const OperationsTab = () => {
  return (
    <div className="space-y-6">
      <GlassCard>
        <h2 className="text-h2 font-semibold mb-6">Operational Efficiency</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="text-center">
            <div className="text-3xl font-bold text-purple-400 mb-2">87%</div>
            <p className="text-sm text-gray-400">Process Automation</p>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-blue-400 mb-2">2.3h</div>
            <p className="text-sm text-gray-400">Avg Response Time</p>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-green-400 mb-2">99.9%</div>
            <p className="text-sm text-gray-400">System Uptime</p>
          </div>
        </div>
      </GlassCard>
      
      <GlassCard>
        <h3 className="text-h3 font-semibold mb-4">Active Workflows</h3>
        <div className="space-y-3">
          {['Customer Onboarding', 'Property Assessment', 'Financial Analysis'].map((workflow) => (
            <div key={workflow} className="flex items-center justify-between p-4 bg-slate-800 rounded-lg">
              <span className="font-medium">{workflow}</span>
              <div className="flex items-center space-x-3">
                <span className="text-sm text-gray-400">Running</span>
                <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
              </div>
            </div>
          ))}
        </div>
      </GlassCard>
    </div>
  );
};

// AI Insights Tab Component
const InsightsTab = () => {
  return (
    <GlassCard>
      <h2 className="text-h2 font-semibold mb-6">AI-Powered Insights</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="space-y-4">
          <h3 className="text-h4 font-medium">Predictive Analytics</h3>
          <div className="p-4 bg-gradient-to-r from-purple-900/20 to-blue-900/20 border border-purple-700 rounded-lg">
            <h4 className="font-medium text-purple-300 mb-2">Revenue Forecast</h4>
            <p className="text-2xl font-bold text-white mb-1">$425,000</p>
            <p className="text-sm text-gray-400">Projected for next month with 85% confidence</p>
          </div>
        </div>
        <div className="space-y-4">
          <h3 className="text-h4 font-medium">Recommendations</h3>
          <div className="space-y-3">
            <div className="p-3 bg-slate-800 rounded-lg">
              <p className="text-sm">
                <span className="text-yellow-400 font-medium">Action Required:</span>
                <span className="text-gray-300 ml-2">Contact high-value customers showing churn signals</span>
              </p>
            </div>
            <div className="p-3 bg-slate-800 rounded-lg">
              <p className="text-sm">
                <span className="text-green-400 font-medium">Opportunity:</span>
                <span className="text-gray-300 ml-2">Upsell potential identified for 23 accounts</span>
              </p>
            </div>
          </div>
        </div>
      </div>
    </GlassCard>
  );
};

export default DashboardLayout; 