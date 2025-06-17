import React, { useState, useEffect } from 'react';
import { Search, Filter, Calendar, Users, TrendingUp, MessageSquare, Mail, Upload, Eye, BarChart3 } from 'lucide-react';
import './App.css';

const API_BASE_URL = 'http://localhost:5000/api';

function App() {
  const [conversations, setConversations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [filters, setFilters] = useState({
    date_from: '',
    date_to: '',
    min_relevance: '',
    deal_stage: '',
    company: ''
  });
  const [dashboardStats, setDashboardStats] = useState(null);
  const [selectedConversation, setSelectedConversation] = useState(null);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [pagination, setPagination] = useState({
    offset: 0,
    limit: 20,
    total_count: 0,
    has_more: false
  });

  // Fetch dashboard stats
  const fetchDashboardStats = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/dashboard/stats`);
      const data = await response.json();
      setDashboardStats(data);
    } catch (error) {
      console.error('Error fetching dashboard stats:', error);
    }
  };

  // Search conversations
  const searchConversations = async (offset = 0) => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        q: searchQuery,
        limit: pagination.limit.toString(),
        offset: offset.toString(),
        ...Object.fromEntries(Object.entries(filters).filter(([_, v]) => v))
      });

      const response = await fetch(`${API_BASE_URL}/conversations/search?${params}`);
      const data = await response.json();
      
      if (data.conversations) {
        setConversations(data.conversations);
        setPagination({
          offset: data.offset,
          limit: data.page_size,
          total_count: data.total_count,
          has_more: data.has_more
        });
      }
    } catch (error) {
      console.error('Error searching conversations:', error);
    } finally {
      setLoading(false);
    }
  };

  // Get conversation details
  const getConversationDetails = async (callId) => {
    try {
      const response = await fetch(`${API_BASE_URL}/conversations/${callId}`);
      const data = await response.json();
      setSelectedConversation(data);
    } catch (error) {
      console.error('Error fetching conversation details:', error);
    }
  };

  // Load initial data
  useEffect(() => {
    fetchDashboardStats();
    if (activeTab === 'conversations') {
      searchConversations();
    }
  }, [activeTab]);

  // Handle search
  const handleSearch = () => {
    setPagination(prev => ({ ...prev, offset: 0 }));
    searchConversations(0);
  };

  // Handle pagination
  const handleNextPage = () => {
    const newOffset = pagination.offset + pagination.limit;
    searchConversations(newOffset);
  };

  const handlePrevPage = () => {
    const newOffset = Math.max(0, pagination.offset - pagination.limit);
    searchConversations(newOffset);
  };

  // Format score as percentage
  const formatScore = (score) => {
    return score ? `${Math.round(score * 100)}%` : 'N/A';
  };

  // Format duration
  const formatDuration = (minutes) => {
    if (!minutes) return 'N/A';
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return hours > 0 ? `${hours}h ${mins}m` : `${mins}m`;
  };

  // Dashboard component
  const Dashboard = () => (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">Sophia Conversation Intelligence</h1>
        <div className="flex items-center space-x-2 text-sm text-gray-500">
          <BarChart3 className="w-4 h-4" />
          <span>Real-time Analytics</span>
        </div>
      </div>

      {dashboardStats && (
        <>
          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center">
                <MessageSquare className="w-8 h-8 text-blue-500" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-500">Total Calls</p>
                  <p className="text-2xl font-bold text-gray-900">{dashboardStats.total_calls}</p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center">
                <Mail className="w-8 h-8 text-green-500" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-500">Total Emails</p>
                  <p className="text-2xl font-bold text-gray-900">{dashboardStats.total_emails}</p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center">
                <TrendingUp className="w-8 h-8 text-purple-500" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-500">High Relevance</p>
                  <p className="text-2xl font-bold text-gray-900">{dashboardStats.high_relevance_calls}</p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center">
                <Users className="w-8 h-8 text-orange-500" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-500">Active Users</p>
                  <p className="text-2xl font-bold text-gray-900">{dashboardStats.total_users}</p>
                </div>
              </div>
            </div>
          </div>

          {/* Recent Activity & Top Companies */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Deal Stage Distribution</h3>
              <div className="space-y-3">
                {Object.entries(dashboardStats.deal_stages || {}).map(([stage, count]) => (
                  <div key={stage} className="flex justify-between items-center">
                    <span className="text-sm text-gray-600 capitalize">{stage}</span>
                    <span className="text-sm font-medium text-gray-900">{count}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Top Companies</h3>
              <div className="space-y-3">
                {(dashboardStats.top_companies || []).slice(0, 5).map((company, index) => (
                  <div key={index} className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">{company.company}</span>
                    <span className="text-sm font-medium text-gray-900">{company.calls} calls</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );

  // Conversations component
  const Conversations = () => (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">Conversation Search</h1>
        <button
          onClick={() => setActiveTab('email-upload')}
          className="flex items-center space-x-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
        >
          <Upload className="w-4 h-4" />
          <span>Upload Email</span>
        </button>
      </div>

      {/* Search and Filters */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <input
              type="text"
              placeholder="Search conversations..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          <button
            onClick={handleSearch}
            className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 flex items-center justify-center space-x-2"
          >
            <Search className="w-4 h-4" />
            <span>Search</span>
          </button>
        </div>

        {/* Filters */}
        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4">
          <input
            type="date"
            placeholder="From Date"
            value={filters.date_from}
            onChange={(e) => setFilters(prev => ({ ...prev, date_from: e.target.value }))}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          />
          <input
            type="date"
            placeholder="To Date"
            value={filters.date_to}
            onChange={(e) => setFilters(prev => ({ ...prev, date_to: e.target.value }))}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          />
          <select
            value={filters.min_relevance}
            onChange={(e) => setFilters(prev => ({ ...prev, min_relevance: e.target.value }))}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Min Relevance</option>
            <option value="0.9">90%+</option>
            <option value="0.8">80%+</option>
            <option value="0.7">70%+</option>
            <option value="0.5">50%+</option>
          </select>
          <select
            value={filters.deal_stage}
            onChange={(e) => setFilters(prev => ({ ...prev, deal_stage: e.target.value }))}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Deal Stage</option>
            <option value="discovery">Discovery</option>
            <option value="evaluation">Evaluation</option>
            <option value="negotiation">Negotiation</option>
            <option value="closing">Closing</option>
          </select>
          <input
            type="text"
            placeholder="Company"
            value={filters.company}
            onChange={(e) => setFilters(prev => ({ ...prev, company: e.target.value }))}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      {/* Results */}
      {loading ? (
        <div className="flex justify-center items-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      ) : (
        <div className="space-y-4">
          {conversations.map((conversation) => (
            <div key={conversation.call_id} className="bg-white rounded-lg shadow p-6 hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">{conversation.title}</h3>
                  <p className="text-gray-600 mb-3 line-clamp-2">{conversation.ai_summary}</p>
                  
                  <div className="flex flex-wrap items-center gap-4 text-sm text-gray-500">
                    <span className="flex items-center">
                      <Calendar className="w-4 h-4 mr-1" />
                      {new Date(conversation.started).toLocaleDateString()}
                    </span>
                    <span>{formatDuration(conversation.duration_minutes)}</span>
                    <span className="capitalize">{conversation.direction}</span>
                    {conversation.companies.length > 0 && (
                      <span className="flex items-center">
                        <Users className="w-4 h-4 mr-1" />
                        {conversation.companies.join(', ')}
                      </span>
                    )}
                  </div>
                </div>
                
                <div className="ml-6 flex flex-col items-end space-y-2">
                  <div className="flex space-x-4 text-sm">
                    <div className="text-center">
                      <div className="text-xs text-gray-500">Relevance</div>
                      <div className="font-semibold text-blue-600">
                        {formatScore(conversation.apartment_relevance_score)}
                      </div>
                    </div>
                    <div className="text-center">
                      <div className="text-xs text-gray-500">Impact</div>
                      <div className="font-semibold text-green-600">
                        {formatScore(conversation.business_impact_score)}
                      </div>
                    </div>
                    {conversation.win_probability > 0 && (
                      <div className="text-center">
                        <div className="text-xs text-gray-500">Win Prob</div>
                        <div className="font-semibold text-purple-600">
                          {formatScore(conversation.win_probability)}
                        </div>
                      </div>
                    )}
                  </div>
                  
                  <button
                    onClick={() => getConversationDetails(conversation.call_id)}
                    className="flex items-center space-x-1 text-blue-600 hover:text-blue-800"
                  >
                    <Eye className="w-4 h-4" />
                    <span>View Details</span>
                  </button>
                </div>
              </div>
              
              {conversation.deal_stage && (
                <div className="mt-3 flex items-center space-x-2">
                  <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full capitalize">
                    {conversation.deal_stage}
                  </span>
                  {conversation.competitive_threat && conversation.competitive_threat !== 'none' && (
                    <span className="px-2 py-1 bg-red-100 text-red-800 text-xs rounded-full capitalize">
                      {conversation.competitive_threat} threat
                    </span>
                  )}
                </div>
              )}
            </div>
          ))}
          
          {/* Pagination */}
          {conversations.length > 0 && (
            <div className="flex items-center justify-between bg-white rounded-lg shadow p-4">
              <div className="text-sm text-gray-500">
                Showing {pagination.offset + 1} to {Math.min(pagination.offset + pagination.limit, pagination.total_count)} of {pagination.total_count} results
              </div>
              <div className="flex space-x-2">
                <button
                  onClick={handlePrevPage}
                  disabled={pagination.offset === 0}
                  className="px-4 py-2 border border-gray-300 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
                >
                  Previous
                </button>
                <button
                  onClick={handleNextPage}
                  disabled={!pagination.has_more}
                  className="px-4 py-2 border border-gray-300 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );

  // Email Upload component
  const EmailUpload = () => {
    const [emailData, setEmailData] = useState({
      from_email: '',
      to_emails: '',
      subject_line: '',
      email_body: ''
    });
    const [uploading, setUploading] = useState(false);

    const handleUpload = async () => {
      setUploading(true);
      try {
        const response = await fetch(`${API_BASE_URL}/emails/upload`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            ...emailData,
            to_emails: emailData.to_emails.split(',').map(email => email.trim())
          }),
        });
        
        const result = await response.json();
        if (result.success) {
          alert('Email uploaded successfully!');
          setEmailData({ from_email: '', to_emails: '', subject_line: '', email_body: '' });
        } else {
          alert('Upload failed: ' + result.error);
        }
      } catch (error) {
        alert('Upload failed: ' + error.message);
      } finally {
        setUploading(false);
      }
    };

    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold text-gray-900">Manual Email Upload</h1>
          <button
            onClick={() => setActiveTab('conversations')}
            className="text-blue-600 hover:text-blue-800"
          >
            ← Back to Conversations
          </button>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">From Email</label>
              <input
                type="email"
                value={emailData.from_email}
                onChange={(e) => setEmailData(prev => ({ ...prev, from_email: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                placeholder="sender@company.com"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">To Emails (comma-separated)</label>
              <input
                type="text"
                value={emailData.to_emails}
                onChange={(e) => setEmailData(prev => ({ ...prev, to_emails: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                placeholder="recipient1@company.com, recipient2@company.com"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Subject Line</label>
              <input
                type="text"
                value={emailData.subject_line}
                onChange={(e) => setEmailData(prev => ({ ...prev, subject_line: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                placeholder="Email subject"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Email Body</label>
              <textarea
                value={emailData.email_body}
                onChange={(e) => setEmailData(prev => ({ ...prev, email_body: e.target.value }))}
                rows={10}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                placeholder="Email content..."
              />
            </div>

            <button
              onClick={handleUpload}
              disabled={uploading || !emailData.from_email || !emailData.to_emails || !emailData.subject_line}
              className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
            >
              {uploading ? (
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
              ) : (
                <>
                  <Upload className="w-4 h-4" />
                  <span>Upload Email</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation */}
      <nav className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-bold text-gray-900">Sophia Admin</h1>
            </div>
            <div className="flex space-x-8">
              <button
                onClick={() => setActiveTab('dashboard')}
                className={`inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium ${
                  activeTab === 'dashboard'
                    ? 'border-blue-500 text-gray-900'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <BarChart3 className="w-4 h-4 mr-2" />
                Dashboard
              </button>
              <button
                onClick={() => setActiveTab('conversations')}
                className={`inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium ${
                  activeTab === 'conversations'
                    ? 'border-blue-500 text-gray-900'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <MessageSquare className="w-4 h-4 mr-2" />
                Conversations
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          {activeTab === 'dashboard' && <Dashboard />}
          {activeTab === 'conversations' && <Conversations />}
          {activeTab === 'email-upload' && <EmailUpload />}
        </div>
      </main>

      {/* Conversation Details Modal */}
      {selectedConversation && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-2xl font-bold text-gray-900">Conversation Details</h2>
                <button
                  onClick={() => setSelectedConversation(null)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ✕
                </button>
              </div>
              
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">{selectedConversation.title}</h3>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                    <div>
                      <span className="text-gray-500">Date:</span>
                      <div>{new Date(selectedConversation.started).toLocaleDateString()}</div>
                    </div>
                    <div>
                      <span className="text-gray-500">Duration:</span>
                      <div>{Math.round(selectedConversation.duration_seconds / 60)} minutes</div>
                    </div>
                    <div>
                      <span className="text-gray-500">Direction:</span>
                      <div className="capitalize">{selectedConversation.direction}</div>
                    </div>
                    <div>
                      <span className="text-gray-500">System:</span>
                      <div>{selectedConversation.system}</div>
                    </div>
                  </div>
                </div>

                {selectedConversation.intelligence && (
                  <div>
                    <h4 className="font-semibold text-gray-900 mb-2">AI Summary</h4>
                    <p className="text-gray-700">{selectedConversation.intelligence.ai_summary}</p>
                  </div>
                )}

                {selectedConversation.participants && selectedConversation.participants.length > 0 && (
                  <div>
                    <h4 className="font-semibold text-gray-900 mb-2">Participants</h4>
                    <div className="space-y-2">
                      {selectedConversation.participants.map((participant, index) => (
                        <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                          <div>
                            <div className="font-medium">{participant.name}</div>
                            <div className="text-sm text-gray-500">{participant.title} at {participant.company}</div>
                          </div>
                          <div className="text-sm text-gray-500">
                            {participant.talk_time_percentage}% talk time
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {selectedConversation.deal_signals && (
                  <div>
                    <h4 className="font-semibold text-gray-900 mb-2">Deal Signals</h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {selectedConversation.deal_signals.positive_signals.length > 0 && (
                        <div>
                          <h5 className="text-sm font-medium text-green-700 mb-1">Positive Signals</h5>
                          <ul className="text-sm text-gray-600 space-y-1">
                            {selectedConversation.deal_signals.positive_signals.map((signal, index) => (
                              <li key={index}>• {signal}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                      {selectedConversation.deal_signals.negative_signals.length > 0 && (
                        <div>
                          <h5 className="text-sm font-medium text-red-700 mb-1">Negative Signals</h5>
                          <ul className="text-sm text-gray-600 space-y-1">
                            {selectedConversation.deal_signals.negative_signals.map((signal, index) => (
                              <li key={index}>• {signal}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;

