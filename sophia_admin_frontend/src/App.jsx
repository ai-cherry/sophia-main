import React, { useState, useEffect } from 'react';
import { Search, Users, TrendingUp, MessageSquare, BarChart3, Calendar, Eye } from 'lucide-react';

const API_BASE_URL = 'http://localhost:5001';

function App() {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [dashboardStats, setDashboardStats] = useState(null);

  // Fetch dashboard stats
  const fetchDashboardStats = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/stats`);
      const data = await response.json();
      setDashboardStats(data);
    } catch (error) {
      console.error('Error fetching dashboard stats:', error);
    }
  };

  // Search function
  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/search`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query: searchQuery }),
      });
      const data = await response.json();
      setSearchResults(data);
    } catch (error) {
      console.error('Error searching:', error);
    } finally {
      setLoading(false);
    }
  };

  // Quick search functions
  const quickSearch = (query) => {
    setSearchQuery(query);
    setTimeout(() => handleSearch(), 100);
  };

  // Load initial data
  useEffect(() => {
    fetchDashboardStats();
  }, []);

  // Format currency
  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  // Format percentage
  const formatPercentage = (value) => {
    return `${Math.round(value * 100)}%`;
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-4">
              <BarChart3 className="w-8 h-8 text-blue-600" />
              <h1 className="text-xl font-bold text-gray-900">Sophia Conversation Intelligence</h1>
            </div>
            <div className="text-sm text-gray-500">
              Apartment Industry Analytics
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Dashboard Stats */}
        {dashboardStats && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center">
                <MessageSquare className="w-8 h-8 text-blue-500" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-500">Total Conversations</p>
                  <p className="text-2xl font-bold text-gray-900">{dashboardStats.total_calls}</p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center">
                <Users className="w-8 h-8 text-green-500" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-500">Pay Ready Team</p>
                  <p className="text-2xl font-bold text-gray-900">{dashboardStats.pay_ready_team_count}</p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center">
                <TrendingUp className="w-8 h-8 text-purple-500" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-500">Total Business Value</p>
                  <p className="text-2xl font-bold text-gray-900">{formatCurrency(dashboardStats.total_business_value)}</p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center">
                <BarChart3 className="w-8 h-8 text-orange-500" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-500">Avg Apartment Relevance</p>
                  <p className="text-2xl font-bold text-gray-900">{formatPercentage(dashboardStats.avg_apartment_relevance)}</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Search Interface */}
        <div className="bg-white rounded-lg shadow p-6 mb-8">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Natural Language Search</h2>
          
          <div className="flex space-x-4 mb-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
              <input
                type="text"
                placeholder="Ask anything about your conversations..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            <button
              onClick={handleSearch}
              disabled={loading}
              className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center space-x-2"
            >
              {loading ? (
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
              ) : (
                <Search className="w-4 h-4" />
              )}
              <span>Search</span>
            </button>
          </div>

          {/* Quick Search Buttons */}
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => quickSearch('Show me Pay Ready team members')}
              className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm hover:bg-blue-200"
            >
              Pay Ready Team
            </button>
            <button
              onClick={() => quickSearch('Greystar calls')}
              className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm hover:bg-green-200"
            >
              Greystar Conversations
            </button>
            <button
              onClick={() => quickSearch('Top performers')}
              className="px-3 py-1 bg-purple-100 text-purple-800 rounded-full text-sm hover:bg-purple-200"
            >
              Top Performers
            </button>
            <button
              onClick={() => quickSearch('High value deals')}
              className="px-3 py-1 bg-orange-100 text-orange-800 rounded-full text-sm hover:bg-orange-200"
            >
              High Value Deals
            </button>
          </div>
        </div>

        {/* Search Results */}
        {searchResults && (
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Search Results</h3>
            <p className="text-gray-600 mb-6">{searchResults.summary}</p>

            {/* Team Members Results */}
            {searchResults.users && searchResults.users.length > 0 && (
              <div className="mb-8">
                <h4 className="text-md font-medium text-gray-900 mb-4">Team Members</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {searchResults.users.map((user, index) => (
                    <div key={index} className="border border-gray-200 rounded-lg p-4">
                      <div className="flex items-center space-x-3 mb-3">
                        <div className="w-10 h-10 bg-blue-500 rounded-full flex items-center justify-center text-white font-semibold">
                          {user.first_name?.[0]}{user.last_name?.[0]}
                        </div>
                        <div>
                          <h5 className="font-medium text-gray-900">{user.name}</h5>
                          <p className="text-sm text-gray-500">{user.email_address}</p>
                        </div>
                      </div>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span className="text-gray-500">Calls:</span>
                          <span className="font-medium">{user.call_count}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-500">Total Value:</span>
                          <span className="font-medium">{formatCurrency(user.total_value)}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-500">Performance:</span>
                          <span className="font-medium">{user.performance_score}/100</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Conversation Results */}
            {searchResults.calls && searchResults.calls.length > 0 && (
              <div>
                <h4 className="text-md font-medium text-gray-900 mb-4">Conversations</h4>
                <div className="space-y-4">
                  {searchResults.calls.map((call, index) => (
                    <div key={index} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <h5 className="font-medium text-gray-900 mb-2">{call.title}</h5>
                          <div className="flex flex-wrap items-center gap-4 text-sm text-gray-500 mb-3">
                            <span className="flex items-center">
                              <Calendar className="w-4 h-4 mr-1" />
                              {new Date(call.started).toLocaleDateString()}
                            </span>
                            <span>{call.duration_minutes} min</span>
                            {call.companies.length > 0 && (
                              <span className="flex items-center">
                                <Users className="w-4 h-4 mr-1" />
                                {call.companies.join(', ')}
                              </span>
                            )}
                          </div>
                          {call.participants.length > 0 && (
                            <div className="text-sm text-gray-600 mb-2">
                              Participants: {call.participants.join(', ')}
                            </div>
                          )}
                        </div>
                        
                        <div className="ml-6 flex flex-col items-end space-y-2">
                          <div className="flex space-x-4 text-sm">
                            <div className="text-center">
                              <div className="text-xs text-gray-500">Relevance</div>
                              <div className="font-semibold text-blue-600">
                                {formatPercentage(call.apartment_relevance)}
                              </div>
                            </div>
                            <div className="text-center">
                              <div className="text-xs text-gray-500">Value</div>
                              <div className="font-semibold text-green-600">
                                {formatCurrency(call.business_value)}
                              </div>
                            </div>
                            {call.success_probability > 0 && (
                              <div className="text-center">
                                <div className="text-xs text-gray-500">Success</div>
                                <div className="font-semibold text-purple-600">
                                  {formatPercentage(call.success_probability)}
                                </div>
                              </div>
                            )}
                          </div>
                          
                          {call.call_outcome && (
                            <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full capitalize">
                              {call.call_outcome.replace('_', ' ')}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Recent Activity */}
        {dashboardStats && dashboardStats.recent_calls && (
          <div className="bg-white rounded-lg shadow p-6 mt-8">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Activity</h3>
            <div className="space-y-4">
              {dashboardStats.recent_calls.map((call, index) => (
                <div key={index} className="flex items-center justify-between py-3 border-b border-gray-100 last:border-b-0">
                  <div>
                    <h5 className="font-medium text-gray-900">{call.title}</h5>
                    <p className="text-sm text-gray-500">
                      {call.account_executive} • {new Date(call.started).toLocaleDateString()}
                    </p>
                  </div>
                  <div className="flex items-center space-x-4 text-sm">
                    <span className="text-blue-600">{formatPercentage(call.apartment_relevance)}</span>
                    <span className="text-green-600">{formatCurrency(call.business_value)}</span>
                    <span className="px-2 py-1 bg-gray-100 text-gray-800 rounded-full capitalize">
                      {call.call_outcome.replace('_', ' ')}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;

