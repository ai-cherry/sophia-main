// API Service Layer for Sophia AI
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5001/api';

class ApiService {
  constructor() {
    this.baseURL = API_BASE_URL;
    this.token = localStorage.getItem('auth_token');
  }

  // Helper method for API requests
  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const config = {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    };

    // Add auth token if available
    if (this.token) {
      config.headers['Authorization'] = `Bearer ${this.token}`;
    }

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        throw new Error(`API Error: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('API Request failed:', error);
      throw error;
    }
  }

  // Authentication
  async login(email, password) {
    const response = await this.request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    
    if (response.token) {
      this.token = response.token;
      localStorage.setItem('auth_token', response.token);
    }
    
    return response;
  }

  async logout() {
    this.token = null;
    localStorage.removeItem('auth_token');
  }

  // Company Metrics
  async getCompanyMetrics() {
    return this.request('/company/metrics');
  }

  async getRevenueData(period = 'monthly') {
    return this.request(`/company/revenue?period=${period}`);
  }

  async getCustomerMetrics() {
    return this.request('/company/customers');
  }

  async getHealthScore() {
    return this.request('/company/health-score');
  }

  // Strategy
  async getStrategyInsights() {
    return this.request('/strategy/insights');
  }

  async getGrowthOpportunities() {
    return this.request('/strategy/growth-opportunities');
  }

  async getMarketAnalysis() {
    return this.request('/strategy/market-analysis');
  }

  // Operations
  async getOperationalMetrics() {
    return this.request('/operations/metrics');
  }

  async getWorkflows() {
    return this.request('/operations/workflows');
  }

  async getSystemStatus() {
    return this.request('/operations/status');
  }

  // AI Insights
  async getAIInsights() {
    return this.request('/ai/insights');
  }

  async getPredictions() {
    return this.request('/ai/predictions');
  }

  async getRecommendations() {
    return this.request('/ai/recommendations');
  }

  // Property Management
  async getPropertyData() {
    return this.request('/property/units');
  }

  async searchUnits(filters) {
    return this.request('/property/search', {
      method: 'POST',
      body: JSON.stringify(filters),
    });
  }

  // Knowledge Base
  async searchKnowledge(query) {
    return this.request('/knowledge/search', {
      method: 'POST',
      body: JSON.stringify({ query }),
    });
  }

  async getKnowledgeStats() {
    return this.request('/knowledge/stats');
  }
}

// Export singleton instance
export default new ApiService(); 