import React, { useState, useEffect } from 'react';
import { Upload, FileText, BarChart3, MapPin, Calendar, TrendingUp, AlertCircle, CheckCircle } from 'lucide-react';

const CoStarDataManager = () => {
  const [activeTab, setActiveTab] = useState('upload');
  const [uploadStatus, setUploadStatus] = useState(null);
  const [markets, setMarkets] = useState([]);
  const [importHistory, setImportHistory] = useState([]);
  const [selectedMarket, setSelectedMarket] = useState('');
  const [marketData, setMarketData] = useState(null);
  const [loading, setLoading] = useState(false);

  // Initialize database on component mount
  useEffect(() => {
    initializeDatabase();
    fetchMarkets();
    fetchImportHistory();
  }, []);

  const initializeDatabase = async () => {
    try {
      const response = await fetch('/api/costar/initialize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      const result = await response.json();
      console.log('Database initialized:', result);
    } catch (error) {
      console.error('Database initialization failed:', error);
    }
  };

  const fetchMarkets = async () => {
    try {
      const response = await fetch('/api/costar/markets');
      const result = await response.json();
      if (result.status === 'success') {
        setMarkets(result.markets);
      }
    } catch (error) {
      console.error('Failed to fetch markets:', error);
    }
  };

  const fetchImportHistory = async () => {
    try {
      const response = await fetch('/api/costar/import-status');
      const result = await response.json();
      if (result.status === 'success') {
        setImportHistory(result.imports);
      }
    } catch (error) {
      console.error('Failed to fetch import history:', error);
    }
  };

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setLoading(true);
    setUploadStatus(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('/api/costar/upload', {
        method: 'POST',
        body: formData
      });

      const result = await response.json();
      setUploadStatus(result);

      if (result.status === 'success') {
        // Refresh markets and import history
        fetchMarkets();
        fetchImportHistory();
      }
    } catch (error) {
      setUploadStatus({
        status: 'error',
        message: 'Upload failed: ' + error.message
      });
    } finally {
      setLoading(false);
    }
  };

  const fetchMarketData = async (metroArea) => {
    if (!metroArea) return;

    setLoading(true);
    try {
      const response = await fetch(`/api/costar/market/${encodeURIComponent(metroArea)}`);
      const result = await response.json();
      if (result.status === 'success') {
        setMarketData(result.data);
      }
    } catch (error) {
      console.error('Failed to fetch market data:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(value);
  };

  const formatPercentage = (value) => {
    return `${parseFloat(value).toFixed(2)}%`;
  };

  const formatNumber = (value) => {
    return new Intl.NumberFormat('en-US').format(value);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center">
              <MapPin className="h-8 w-8 text-blue-600 mr-3" />
              <div>
                <h1 className="text-2xl font-bold text-gray-900">CoStar Data Manager</h1>
                <p className="text-sm text-gray-500">Real Estate Market Intelligence for Sophia AI</p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <div className="text-sm text-gray-500">
                {markets.length} Markets • {importHistory.length} Imports
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            {[
              { id: 'upload', name: 'File Upload', icon: Upload },
              { id: 'markets', name: 'Market Data', icon: BarChart3 },
              { id: 'history', name: 'Import History', icon: FileText }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm flex items-center`}
              >
                <tab.icon className="h-5 w-5 mr-2" />
                {tab.name}
              </button>
            ))}
          </nav>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Upload Tab */}
        {activeTab === 'upload' && (
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-medium text-gray-900 mb-4">Upload CoStar Data File</h2>
              
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-6">
                <div className="text-center">
                  <Upload className="mx-auto h-12 w-12 text-gray-400" />
                  <div className="mt-4">
                    <label htmlFor="file-upload" className="cursor-pointer">
                      <span className="mt-2 block text-sm font-medium text-gray-900">
                        Drop files here or click to upload
                      </span>
                      <span className="mt-1 block text-xs text-gray-500">
                        Supports CSV, Excel, JSON, TSV files (max 50MB)
                      </span>
                    </label>
                    <input
                      id="file-upload"
                      name="file-upload"
                      type="file"
                      className="sr-only"
                      accept=".csv,.xlsx,.xls,.json,.tsv"
                      onChange={handleFileUpload}
                      disabled={loading}
                    />
                  </div>
                </div>
              </div>

              {/* Upload Status */}
              {uploadStatus && (
                <div className={`mt-4 p-4 rounded-md ${
                  uploadStatus.status === 'success' 
                    ? 'bg-green-50 border border-green-200' 
                    : 'bg-red-50 border border-red-200'
                }`}>
                  <div className="flex">
                    {uploadStatus.status === 'success' ? (
                      <CheckCircle className="h-5 w-5 text-green-400" />
                    ) : (
                      <AlertCircle className="h-5 w-5 text-red-400" />
                    )}
                    <div className="ml-3">
                      <h3 className={`text-sm font-medium ${
                        uploadStatus.status === 'success' ? 'text-green-800' : 'text-red-800'
                      }`}>
                        {uploadStatus.status === 'success' ? 'Upload Successful' : 'Upload Failed'}
                      </h3>
                      <p className={`mt-1 text-sm ${
                        uploadStatus.status === 'success' ? 'text-green-700' : 'text-red-700'
                      }`}>
                        {uploadStatus.message}
                      </p>
                      {uploadStatus.details && (
                        <div className="mt-2 text-xs text-gray-600">
                          Records imported: {uploadStatus.details.records_imported}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {loading && (
                <div className="mt-4 text-center">
                  <div className="inline-flex items-center">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                    <span className="ml-2 text-sm text-gray-600">Processing file...</span>
                  </div>
                </div>
              )}
            </div>

            {/* Upload Instructions */}
            <div className="bg-blue-50 rounded-lg p-6">
              <h3 className="text-lg font-medium text-blue-900 mb-3">CoStar Data Format Guidelines</h3>
              <div className="text-sm text-blue-800 space-y-2">
                <p><strong>Supported Columns:</strong></p>
                <ul className="list-disc list-inside ml-4 space-y-1">
                  <li>Metro Area / Market</li>
                  <li>Property Type</li>
                  <li>Total Inventory</li>
                  <li>Vacancy Rate (%)</li>
                  <li>Asking Rent (PSF)</li>
                  <li>Net Absorption</li>
                  <li>Construction Deliveries</li>
                  <li>Under Construction</li>
                  <li>Date / Period</li>
                </ul>
                <p className="mt-3"><strong>Tips:</strong></p>
                <ul className="list-disc list-inside ml-4 space-y-1">
                  <li>Column names are automatically mapped</li>
                  <li>Percentage values can include % symbol</li>
                  <li>Currency values can include $ symbol</li>
                  <li>Dates are automatically parsed</li>
                </ul>
              </div>
            </div>
          </div>
        )}

        {/* Markets Tab */}
        {activeTab === 'markets' && (
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow">
              <div className="p-6 border-b border-gray-200">
                <h2 className="text-lg font-medium text-gray-900">Market Data Explorer</h2>
                <p className="mt-1 text-sm text-gray-500">
                  Browse and analyze CoStar market data by metro area
                </p>
              </div>

              <div className="p-6">
                <div className="mb-6">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Select Metro Area
                  </label>
                  <select
                    value={selectedMarket}
                    onChange={(e) => {
                      setSelectedMarket(e.target.value);
                      fetchMarketData(e.target.value);
                    }}
                    className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="">Choose a market...</option>
                    {markets.map((market) => (
                      <option key={market.metro_area} value={market.metro_area}>
                        {market.metro_area} ({market.record_count} records)
                      </option>
                    ))}
                  </select>
                </div>

                {/* Market Data Display */}
                {marketData && (
                  <div className="space-y-6">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      {marketData.slice(0, 3).map((record, index) => (
                        <div key={index} className="bg-gray-50 rounded-lg p-4">
                          <div className="text-sm font-medium text-gray-900">
                            {record.property_type || 'All Property Types'}
                          </div>
                          <div className="mt-2 space-y-1">
                            {record.vacancy_rate && (
                              <div className="text-xs text-gray-600">
                                Vacancy: {formatPercentage(record.vacancy_rate)}
                              </div>
                            )}
                            {record.asking_rent_psf && (
                              <div className="text-xs text-gray-600">
                                Rent: {formatCurrency(record.asking_rent_psf)} PSF
                              </div>
                            )}
                            {record.total_inventory && (
                              <div className="text-xs text-gray-600">
                                Inventory: {formatNumber(record.total_inventory)} SF
                              </div>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>

                    <div className="overflow-x-auto">
                      <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                          <tr>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                              Property Type
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                              Vacancy Rate
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                              Asking Rent
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                              Inventory
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                              Date
                            </th>
                          </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                          {marketData.slice(0, 10).map((record, index) => (
                            <tr key={index}>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                {record.property_type || 'N/A'}
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                {record.vacancy_rate ? formatPercentage(record.vacancy_rate) : 'N/A'}
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                {record.asking_rent_psf ? formatCurrency(record.asking_rent_psf) : 'N/A'}
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                {record.total_inventory ? formatNumber(record.total_inventory) : 'N/A'}
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                {record.market_date ? new Date(record.market_date).toLocaleDateString() : 'N/A'}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* History Tab */}
        {activeTab === 'history' && (
          <div className="bg-white rounded-lg shadow">
            <div className="p-6 border-b border-gray-200">
              <h2 className="text-lg font-medium text-gray-900">Import History</h2>
              <p className="mt-1 text-sm text-gray-500">
                Track all CoStar data imports and their status
              </p>
            </div>

            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Date
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Filename
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Records
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Method
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {importHistory.map((record) => (
                    <tr key={record.id}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {new Date(record.created_at).toLocaleString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {record.filename || 'N/A'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {formatNumber(record.records_imported)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {record.import_method}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                          record.import_status === 'success'
                            ? 'bg-green-100 text-green-800'
                            : 'bg-red-100 text-red-800'
                        }`}>
                          {record.import_status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default CoStarDataManager;

