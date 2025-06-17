import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import { 
  Search, 
  Plus, 
  FileText, 
  BarChart3, 
  Settings, 
  Database,
  Brain,
  BookOpen,
  Tags,
  Upload,
  Filter,
  Eye,
  Edit,
  Trash2,
  Save,
  X,
  CheckCircle,
  AlertCircle,
  Clock,
  Users,
  TrendingUp,
  Zap
} from 'lucide-react';
import { Button } from '@/components/ui/button.jsx';
import { Input } from '@/components/ui/input.jsx';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx';
import { Badge } from '@/components/ui/badge.jsx';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs.jsx';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select.jsx';
import { Textarea } from '@/components/ui/textarea.jsx';
import { Label } from '@/components/ui/label.jsx';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog.jsx';
import { Alert, AlertDescription } from '@/components/ui/alert.jsx';
import './App.css';

// Mock data for demonstration
const mockDocuments = [
  {
    id: 'company_mission',
    title: 'Pay Ready Mission Statement',
    content: 'Pay Ready is dedicated to revolutionizing payment processing...',
    contentType: 'company_core',
    status: 'published',
    tags: ['mission', 'values', 'company'],
    createdAt: '2024-01-15',
    updatedAt: '2024-01-20',
    createdBy: 'admin',
    version: 2
  },
  {
    id: 'product_catalog',
    title: 'Product & Service Catalog',
    content: 'Our comprehensive suite of payment solutions includes...',
    contentType: 'products_services',
    status: 'published',
    tags: ['products', 'services', 'catalog'],
    createdAt: '2024-01-10',
    updatedAt: '2024-01-18',
    createdBy: 'admin',
    version: 3
  },
  {
    id: 'sales_process',
    title: 'Sales Process Documentation',
    content: 'Our sales process follows a structured approach...',
    contentType: 'sales_marketing',
    status: 'draft',
    tags: ['sales', 'process', 'workflow'],
    createdAt: '2024-01-22',
    updatedAt: '2024-01-22',
    createdBy: 'admin',
    version: 1
  }
];

const mockStats = {
  totalDocuments: 47,
  publishedDocuments: 42,
  draftDocuments: 5,
  totalSearches: 1247,
  avgResponseTime: '185ms',
  knowledgeCoverage: 87
};

const contentTypes = [
  { value: 'company_core', label: 'Company Core', color: 'bg-blue-100 text-blue-800' },
  { value: 'products_services', label: 'Products & Services', color: 'bg-green-100 text-green-800' },
  { value: 'operations', label: 'Operations', color: 'bg-purple-100 text-purple-800' },
  { value: 'data_dictionary', label: 'Data Dictionary', color: 'bg-orange-100 text-orange-800' },
  { value: 'sales_marketing', label: 'Sales & Marketing', color: 'bg-pink-100 text-pink-800' },
  { value: 'customer_success', label: 'Customer Success', color: 'bg-cyan-100 text-cyan-800' },
  { value: 'financial', label: 'Financial', color: 'bg-yellow-100 text-yellow-800' },
  { value: 'strategic', label: 'Strategic', color: 'bg-indigo-100 text-indigo-800' },
  { value: 'technology', label: 'Technology', color: 'bg-gray-100 text-gray-800' },
  { value: 'vendors_partners', label: 'Vendors & Partners', color: 'bg-red-100 text-red-800' }
];

// Navigation Component
function Navigation() {
  const location = useLocation();
  
  const navItems = [
    { path: '/', label: 'Documents', icon: FileText },
    { path: '/analytics', label: 'Analytics', icon: BarChart3 },
    { path: '/search', label: 'Search', icon: Search },
    { path: '/settings', label: 'Settings', icon: Settings }
  ];

  return (
    <nav className="bg-white border-b border-gray-200 px-6 py-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-8">
          <div className="flex items-center space-x-2">
            <Brain className="h-8 w-8 text-blue-600" />
            <h1 className="text-xl font-bold text-gray-900">Sophia AI Knowledge Base</h1>
          </div>
          <div className="flex space-x-6">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-blue-100 text-blue-700'
                      : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                  }`}
                >
                  <Icon className="h-4 w-4" />
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </div>
        </div>
        <div className="flex items-center space-x-4">
          <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">
            <CheckCircle className="h-3 w-3 mr-1" />
            Connected
          </Badge>
        </div>
      </div>
    </nav>
  );
}

// Document Card Component
function DocumentCard({ document, onEdit, onDelete, onView }) {
  const contentType = contentTypes.find(ct => ct.value === document.contentType);
  const statusColor = document.status === 'published' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800';

  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <CardTitle className="text-lg font-semibold text-gray-900 mb-1">
              {document.title}
            </CardTitle>
            <CardDescription className="text-sm text-gray-600 line-clamp-2">
              {document.content.substring(0, 120)}...
            </CardDescription>
          </div>
          <div className="flex space-x-1 ml-4">
            <Button variant="ghost" size="sm" onClick={() => onView(document)}>
              <Eye className="h-4 w-4" />
            </Button>
            <Button variant="ghost" size="sm" onClick={() => onEdit(document)}>
              <Edit className="h-4 w-4" />
            </Button>
            <Button variant="ghost" size="sm" onClick={() => onDelete(document)}>
              <Trash2 className="h-4 w-4 text-red-500" />
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent className="pt-0">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Badge className={contentType?.color || 'bg-gray-100 text-gray-800'}>
              {contentType?.label || document.contentType}
            </Badge>
            <Badge className={statusColor}>
              {document.status}
            </Badge>
          </div>
          <div className="text-xs text-gray-500">
            v{document.version} • {document.updatedAt}
          </div>
        </div>
        <div className="flex flex-wrap gap-1 mt-2">
          {document.tags.slice(0, 3).map((tag) => (
            <Badge key={tag} variant="outline" className="text-xs">
              {tag}
            </Badge>
          ))}
          {document.tags.length > 3 && (
            <Badge variant="outline" className="text-xs">
              +{document.tags.length - 3}
            </Badge>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

// Document Editor Component
function DocumentEditor({ document, onSave, onCancel }) {
  const [formData, setFormData] = useState({
    title: document?.title || '',
    content: document?.content || '',
    contentType: document?.contentType || 'company_core',
    status: document?.status || 'draft',
    tags: document?.tags?.join(', ') || ''
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    const updatedDocument = {
      ...document,
      ...formData,
      tags: formData.tags.split(',').map(tag => tag.trim()).filter(tag => tag),
      updatedAt: new Date().toISOString().split('T')[0]
    };
    onSave(updatedDocument);
  };

  return (
    <div className="space-y-6">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <Label htmlFor="title">Title</Label>
          <Input
            id="title"
            value={formData.title}
            onChange={(e) => setFormData({ ...formData, title: e.target.value })}
            placeholder="Document title"
            required
          />
        </div>
        
        <div className="grid grid-cols-2 gap-4">
          <div>
            <Label htmlFor="contentType">Content Type</Label>
            <Select value={formData.contentType} onValueChange={(value) => setFormData({ ...formData, contentType: value })}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {contentTypes.map((type) => (
                  <SelectItem key={type.value} value={type.value}>
                    {type.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          
          <div>
            <Label htmlFor="status">Status</Label>
            <Select value={formData.status} onValueChange={(value) => setFormData({ ...formData, status: value })}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="draft">Draft</SelectItem>
                <SelectItem value="review">Review</SelectItem>
                <SelectItem value="published">Published</SelectItem>
                <SelectItem value="archived">Archived</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
        
        <div>
          <Label htmlFor="tags">Tags (comma-separated)</Label>
          <Input
            id="tags"
            value={formData.tags}
            onChange={(e) => setFormData({ ...formData, tags: e.target.value })}
            placeholder="tag1, tag2, tag3"
          />
        </div>
        
        <div>
          <Label htmlFor="content">Content</Label>
          <Textarea
            id="content"
            value={formData.content}
            onChange={(e) => setFormData({ ...formData, content: e.target.value })}
            placeholder="Document content..."
            rows={12}
            required
          />
        </div>
        
        <div className="flex space-x-2">
          <Button type="submit">
            <Save className="h-4 w-4 mr-2" />
            Save Document
          </Button>
          <Button type="button" variant="outline" onClick={onCancel}>
            <X className="h-4 w-4 mr-2" />
            Cancel
          </Button>
        </div>
      </form>
    </div>
  );
}

// Documents Page
function DocumentsPage() {
  const [documents, setDocuments] = useState(mockDocuments);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('all');
  const [filterStatus, setFilterStatus] = useState('all');
  const [editingDocument, setEditingDocument] = useState(null);
  const [viewingDocument, setViewingDocument] = useState(null);
  const [isCreating, setIsCreating] = useState(false);

  const filteredDocuments = documents.filter(doc => {
    const matchesSearch = doc.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         doc.content.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         doc.tags.some(tag => tag.toLowerCase().includes(searchTerm.toLowerCase()));
    const matchesType = filterType === 'all' || doc.contentType === filterType;
    const matchesStatus = filterStatus === 'all' || doc.status === filterStatus;
    return matchesSearch && matchesType && matchesStatus;
  });

  const handleSaveDocument = (document) => {
    if (document.id) {
      setDocuments(docs => docs.map(d => d.id === document.id ? document : d));
    } else {
      const newDocument = {
        ...document,
        id: `doc_${Date.now()}`,
        createdAt: new Date().toISOString().split('T')[0],
        createdBy: 'admin',
        version: 1
      };
      setDocuments(docs => [...docs, newDocument]);
    }
    setEditingDocument(null);
    setIsCreating(false);
  };

  const handleDeleteDocument = (document) => {
    if (confirm(`Are you sure you want to delete "${document.title}"?`)) {
      setDocuments(docs => docs.filter(d => d.id !== document.id));
    }
  };

  if (editingDocument || isCreating) {
    return (
      <div className="p-6">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">
            {isCreating ? 'Create New Document' : 'Edit Document'}
          </h2>
          <DocumentEditor
            document={editingDocument}
            onSave={handleSaveDocument}
            onCancel={() => {
              setEditingDocument(null);
              setIsCreating(false);
            }}
          />
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-bold text-gray-900">Knowledge Base Documents</h2>
          <Button onClick={() => setIsCreating(true)}>
            <Plus className="h-4 w-4 mr-2" />
            New Document
          </Button>
        </div>
        
        <div className="flex space-x-4 mb-4">
          <div className="flex-1">
            <Input
              placeholder="Search documents..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full"
            />
          </div>
          <Select value={filterType} onValueChange={setFilterType}>
            <SelectTrigger className="w-48">
              <SelectValue placeholder="Filter by type" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Types</SelectItem>
              {contentTypes.map((type) => (
                <SelectItem key={type.value} value={type.value}>
                  {type.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select value={filterStatus} onValueChange={setFilterStatus}>
            <SelectTrigger className="w-32">
              <SelectValue placeholder="Status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Status</SelectItem>
              <SelectItem value="draft">Draft</SelectItem>
              <SelectItem value="review">Review</SelectItem>
              <SelectItem value="published">Published</SelectItem>
              <SelectItem value="archived">Archived</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredDocuments.map((document) => (
          <DocumentCard
            key={document.id}
            document={document}
            onEdit={setEditingDocument}
            onDelete={handleDeleteDocument}
            onView={setViewingDocument}
          />
        ))}
      </div>

      {filteredDocuments.length === 0 && (
        <div className="text-center py-12">
          <BookOpen className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No documents found</h3>
          <p className="text-gray-600 mb-4">
            {searchTerm || filterType !== 'all' || filterStatus !== 'all'
              ? 'Try adjusting your search or filters'
              : 'Get started by creating your first document'}
          </p>
          <Button onClick={() => setIsCreating(true)}>
            <Plus className="h-4 w-4 mr-2" />
            Create Document
          </Button>
        </div>
      )}

      {/* Document Viewer Dialog */}
      <Dialog open={!!viewingDocument} onOpenChange={() => setViewingDocument(null)}>
        <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{viewingDocument?.title}</DialogTitle>
            <DialogDescription>
              {contentTypes.find(ct => ct.value === viewingDocument?.contentType)?.label} • 
              Version {viewingDocument?.version} • 
              Updated {viewingDocument?.updatedAt}
            </DialogDescription>
          </DialogHeader>
          <div className="mt-4">
            <div className="prose max-w-none">
              <pre className="whitespace-pre-wrap font-sans text-sm">
                {viewingDocument?.content}
              </pre>
            </div>
            <div className="flex flex-wrap gap-2 mt-4">
              {viewingDocument?.tags.map((tag) => (
                <Badge key={tag} variant="outline">
                  {tag}
                </Badge>
              ))}
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}

// Analytics Page
function AnalyticsPage() {
  return (
    <div className="p-6">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Knowledge Base Analytics</h2>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Documents</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{mockStats.totalDocuments}</div>
            <p className="text-xs text-muted-foreground">
              +3 from last month
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Published</CardTitle>
            <CheckCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{mockStats.publishedDocuments}</div>
            <p className="text-xs text-muted-foreground">
              {mockStats.draftDocuments} in draft
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Searches</CardTitle>
            <Search className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{mockStats.totalSearches}</div>
            <p className="text-xs text-muted-foreground">
              +12% from last week
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Response Time</CardTitle>
            <Zap className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{mockStats.avgResponseTime}</div>
            <p className="text-xs text-muted-foreground">
              -15ms from last week
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Content Distribution</CardTitle>
            <CardDescription>Documents by content type</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {contentTypes.slice(0, 6).map((type, index) => (
                <div key={type.value} className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <div className={`w-3 h-3 rounded-full ${type.color.split(' ')[0]}`} />
                    <span className="text-sm font-medium">{type.label}</span>
                  </div>
                  <span className="text-sm text-gray-600">{Math.floor(Math.random() * 10) + 1}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Recent Activity</CardTitle>
            <CardDescription>Latest knowledge base updates</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center space-x-3">
                <div className="w-2 h-2 bg-green-500 rounded-full" />
                <div className="flex-1">
                  <p className="text-sm font-medium">Product Catalog updated</p>
                  <p className="text-xs text-gray-600">2 hours ago</p>
                </div>
              </div>
              <div className="flex items-center space-x-3">
                <div className="w-2 h-2 bg-blue-500 rounded-full" />
                <div className="flex-1">
                  <p className="text-sm font-medium">New sales process document</p>
                  <p className="text-xs text-gray-600">1 day ago</p>
                </div>
              </div>
              <div className="flex items-center space-x-3">
                <div className="w-2 h-2 bg-yellow-500 rounded-full" />
                <div className="flex-1">
                  <p className="text-sm font-medium">Mission statement reviewed</p>
                  <p className="text-xs text-gray-600">3 days ago</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

// Search Page
function SearchPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    
    setIsSearching(true);
    // Simulate API call
    setTimeout(() => {
      const results = mockDocuments.filter(doc => 
        doc.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        doc.content.toLowerCase().includes(searchQuery.toLowerCase()) ||
        doc.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()))
      ).map(doc => ({
        ...doc,
        score: Math.random() * 0.3 + 0.7 // Mock relevance score
      }));
      setSearchResults(results);
      setIsSearching(false);
    }, 1000);
  };

  return (
    <div className="p-6">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Knowledge Base Search</h2>
      
      <div className="max-w-2xl mx-auto mb-8">
        <div className="flex space-x-2">
          <Input
            placeholder="Search the knowledge base..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
            className="flex-1"
          />
          <Button onClick={handleSearch} disabled={isSearching}>
            <Search className="h-4 w-4 mr-2" />
            {isSearching ? 'Searching...' : 'Search'}
          </Button>
        </div>
      </div>

      {searchResults.length > 0 && (
        <div className="max-w-4xl mx-auto">
          <p className="text-sm text-gray-600 mb-4">
            Found {searchResults.length} results for "{searchQuery}"
          </p>
          <div className="space-y-4">
            {searchResults.map((result) => (
              <Card key={result.id}>
                <CardContent className="pt-6">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h3 className="text-lg font-semibold text-gray-900 mb-2">
                        {result.title}
                      </h3>
                      <p className="text-gray-600 mb-3">
                        {result.content.substring(0, 200)}...
                      </p>
                      <div className="flex items-center space-x-4">
                        <Badge className={contentTypes.find(ct => ct.value === result.contentType)?.color}>
                          {contentTypes.find(ct => ct.value === result.contentType)?.label}
                        </Badge>
                        <span className="text-sm text-gray-500">
                          Relevance: {(result.score * 100).toFixed(0)}%
                        </span>
                        <span className="text-sm text-gray-500">
                          Updated: {result.updatedAt}
                        </span>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}

      {searchQuery && searchResults.length === 0 && !isSearching && (
        <div className="text-center py-12">
          <Search className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No results found</h3>
          <p className="text-gray-600">
            Try different keywords or check your spelling
          </p>
        </div>
      )}
    </div>
  );
}

// Settings Page
function SettingsPage() {
  return (
    <div className="p-6">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Knowledge Base Settings</h2>
      
      <Tabs defaultValue="general" className="space-y-6">
        <TabsList>
          <TabsTrigger value="general">General</TabsTrigger>
          <TabsTrigger value="search">Search</TabsTrigger>
          <TabsTrigger value="integrations">Integrations</TabsTrigger>
          <TabsTrigger value="backup">Backup</TabsTrigger>
        </TabsList>
        
        <TabsContent value="general" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>General Settings</CardTitle>
              <CardDescription>Configure basic knowledge base settings</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label htmlFor="kb-name">Knowledge Base Name</Label>
                <Input id="kb-name" defaultValue="Pay Ready Knowledge Base" />
              </div>
              <div>
                <Label htmlFor="auto-save">Auto-save Interval (minutes)</Label>
                <Input id="auto-save" type="number" defaultValue="5" />
              </div>
              <div>
                <Label htmlFor="max-versions">Maximum Versions per Document</Label>
                <Input id="max-versions" type="number" defaultValue="10" />
              </div>
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="search" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Search Configuration</CardTitle>
              <CardDescription>Configure search and vector database settings</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <Alert>
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>
                  Vector databases are connected and operational. Response time: {mockStats.avgResponseTime}
                </AlertDescription>
              </Alert>
              <div>
                <Label htmlFor="search-threshold">Search Similarity Threshold</Label>
                <Input id="search-threshold" type="number" step="0.1" defaultValue="0.7" />
              </div>
              <div>
                <Label htmlFor="max-results">Maximum Search Results</Label>
                <Input id="max-results" type="number" defaultValue="20" />
              </div>
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="integrations" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>External Integrations</CardTitle>
              <CardDescription>Configure connections to external systems</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between p-4 border rounded-lg">
                <div>
                  <h4 className="font-medium">Notion Integration</h4>
                  <p className="text-sm text-gray-600">Sync content from Notion workspace</p>
                </div>
                <Badge variant="outline">Not Connected</Badge>
              </div>
              <div className="flex items-center justify-between p-4 border rounded-lg">
                <div>
                  <h4 className="font-medium">SharePoint Integration</h4>
                  <p className="text-sm text-gray-600">Import documents from SharePoint</p>
                </div>
                <Badge variant="outline">Not Connected</Badge>
              </div>
              <div className="flex items-center justify-between p-4 border rounded-lg">
                <div>
                  <h4 className="font-medium">Slack Integration</h4>
                  <p className="text-sm text-gray-600">Enable knowledge base queries from Slack</p>
                </div>
                <Badge className="bg-green-100 text-green-800">Connected</Badge>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="backup" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Backup & Export</CardTitle>
              <CardDescription>Manage knowledge base backups and exports</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label>Automatic Backup</Label>
                <div className="flex items-center space-x-2 mt-2">
                  <input type="checkbox" defaultChecked />
                  <span className="text-sm">Enable daily backups</span>
                </div>
              </div>
              <div className="flex space-x-2">
                <Button>
                  <Upload className="h-4 w-4 mr-2" />
                  Create Backup
                </Button>
                <Button variant="outline">
                  Export All Documents
                </Button>
              </div>
              <div>
                <h4 className="font-medium mb-2">Recent Backups</h4>
                <div className="space-y-2">
                  <div className="flex items-center justify-between p-2 bg-gray-50 rounded">
                    <span className="text-sm">backup_2024_01_22.json</span>
                    <span className="text-xs text-gray-600">2 days ago</span>
                  </div>
                  <div className="flex items-center justify-between p-2 bg-gray-50 rounded">
                    <span className="text-sm">backup_2024_01_21.json</span>
                    <span className="text-xs text-gray-600">3 days ago</span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

// Main App Component
function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        <Navigation />
        <Routes>
          <Route path="/" element={<DocumentsPage />} />
          <Route path="/analytics" element={<AnalyticsPage />} />
          <Route path="/search" element={<SearchPage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;

