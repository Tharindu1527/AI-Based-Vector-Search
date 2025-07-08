import React, { useState, useEffect, useRef } from 'react';
import { Search, Upload, FileText, Trash2, Brain, Zap, Database, Globe, CheckCircle, AlertCircle, Loader, Eye, ChevronDown, ChevronUp, Book, TrendingUp, ArrowRight } from 'lucide-react';

// Enhanced Search Results Component
const EnhancedSearchResults = ({ searchResults, onDocumentSelect }) => {
  const [expandedSources, setExpandedSources] = useState({});
  const [selectedTab, setSelectedTab] = useState('answer');

  const toggleSourceExpansion = (sourceId) => {
    setExpandedSources(prev => ({
      ...prev,
      [sourceId]: !prev[sourceId]
    }));
  };

  const getRelevanceColor = (category) => {
    switch (category) {
      case 'highly_relevant': return 'bg-green-100 text-green-800';
      case 'moderately_relevant': return 'bg-yellow-100 text-yellow-800';
      case 'somewhat_relevant': return 'bg-blue-100 text-blue-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getRelevanceIcon = (category) => {
    switch (category) {
      case 'highly_relevant': return <CheckCircle size={14} />;
      case 'moderately_relevant': return <AlertCircle size={14} />;
      default: return <Eye size={14} />;
    }
  };

  if (!searchResults) return null;

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      {/* Header with Search Stats */}
      <div className="flex justify-between items-center mb-6">
        <h3 className="text-lg font-semibold text-gray-900">
          Search Results
        </h3>
        <div className="flex items-center gap-4 text-sm text-gray-500">
          <span>{searchResults.total_results} chunks found</span>
          <span>•</span>
          <span>{searchResults.documents_searched || 0} documents searched</span>
          <span>•</span>
          <span className={`px-2 py-1 rounded-full text-xs font-medium ${
            searchResults.search_scope === 'all_documents' 
              ? 'bg-blue-100 text-blue-800' 
              : 'bg-purple-100 text-purple-800'
          }`}>
            {searchResults.search_scope === 'all_documents' ? 'Multi-Document' : 'Single Document'}
          </span>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="flex space-x-1 mb-6 bg-gray-100 rounded-lg p-1">
        {[
          { id: 'answer', label: 'AI Answer', icon: Search },
          { id: 'sources', label: 'Sources', icon: FileText },
          { id: 'insights', label: 'Cross-Document', icon: TrendingUp },
          { id: 'summary', label: 'Summary', icon: Book }
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setSelectedTab(tab.id)}
            className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              selectedTab === tab.id
                ? 'bg-white text-indigo-600 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            <tab.icon size={16} />
            {tab.label}
          </button>
        ))}
      </div>

      {/* AI Answer Tab */}
      {selectedTab === 'answer' && (
        <div className="bg-gradient-to-r from-indigo-50 to-purple-50 rounded-lg p-6">
          <div className="flex items-start gap-3">
            <div className="p-2 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-lg">
              <Search className="h-5 w-5 text-white" />
            </div>
            <div className="flex-1">
              <h4 className="font-semibold text-gray-900 mb-3">
                Comprehensive AI Analysis
              </h4>
              <div className="prose prose-sm max-w-none text-gray-700 leading-relaxed">
                {searchResults.answer.split('\n').map((paragraph, index) => (
                  <p key={index} className="mb-3 last:mb-0">
                    {paragraph}
                  </p>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Sources Tab */}
      {selectedTab === 'sources' && searchResults.sources && (
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <h4 className="font-semibold text-gray-900">
              Source Documents ({searchResults.sources.length})
            </h4>
            <div className="text-sm text-gray-500">
              Sorted by relevance
            </div>
          </div>
          
          {searchResults.sources.map((source, index) => (
            <div key={source.id} className="border border-gray-200 rounded-lg overflow-hidden">
              {/* Source Header */}
              <div className="bg-gray-50 px-4 py-3 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="flex items-center gap-2">
                    <FileText className="h-4 w-4 text-gray-500" />
                    <span className="font-medium text-gray-900">{source.filename}</span>
                  </div>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium flex items-center gap-1 ${getRelevanceColor(source.relevance_category)}`}>
                    {getRelevanceIcon(source.relevance_category)}
                    {(source.similarity_score * 100).toFixed(1)}% match
                  </span>
                  <span className="text-xs text-gray-500">
                    Page ~{source.estimated_page} • Chunk {source.chunk_id + 1}
                  </span>
                </div>
                
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => onDocumentSelect(source.filename)}
                    className="text-xs text-indigo-600 hover:text-indigo-800 flex items-center gap-1"
                  >
                    <Eye size={12} />
                    Search in doc
                  </button>
                  <button
                    onClick={() => toggleSourceExpansion(source.id)}
                    className="p-1 hover:bg-gray-200 rounded"
                  >
                    {expandedSources[source.id] ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                  </button>
                </div>
              </div>
              
              {/* Source Content */}
              <div className="p-4">
                <div className="text-sm text-gray-700 mb-3">
                  {expandedSources[source.id] ? source.full_text : source.text_preview}
                </div>
                
                {/* Keywords */}
                {source.keywords_found && source.keywords_found.length > 0 && (
                  <div className="flex flex-wrap gap-1 mb-3">
                    <span className="text-xs text-gray-500 mr-2">Keywords:</span>
                    {source.keywords_found.slice(0, 5).map((keyword, i) => (
                      <span key={i} className="px-2 py-1 bg-gray-100 text-gray-600 rounded text-xs">
                        {keyword}
                      </span>
                    ))}
                  </div>
                )}
                
                {/* Metadata */}
                <div className="flex items-center gap-4 text-xs text-gray-500">
                  <span>Length: {source.content_length} chars</span>
                  <span>•</span>
                  <span>Document: {source.chunk_id + 1}/{source.total_chunks_in_document} chunks</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Cross-Document Insights Tab */}
      {selectedTab === 'insights' && (
        <div className="space-y-4">
          <h4 className="font-semibold text-gray-900">Cross-Document Analysis</h4>
          
          {searchResults.cross_document_insights && searchResults.cross_document_insights.length > 0 ? (
            <div className="space-y-3">
              {searchResults.cross_document_insights.map((insight, index) => (
                <div key={index} className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <div className="flex items-start gap-3">
                    <TrendingUp className="h-5 w-5 text-blue-600 mt-0.5" />
                    <div>
                      <div className="flex items-center gap-2 mb-2">
                        <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs font-medium">
                          {insight.type.replace('_', ' ').toUpperCase()}
                        </span>
                      </div>
                      <p className="text-gray-700 text-sm mb-2">{insight.insight}</p>
                      <div className="flex items-center gap-1 text-xs text-gray-500">
                        <span>Documents:</span>
                        {insight.documents.map((doc, i) => (
                          <span key={i} className="bg-white px-2 py-1 rounded border">
                            {doc}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              <TrendingUp className="h-8 w-8 mx-auto mb-2 text-gray-400" />
              <p>Cross-document insights available when searching multiple documents</p>
            </div>
          )}
        </div>
      )}

      {/* Document Summary Tab */}
      {selectedTab === 'summary' && searchResults.document_summary && (
        <div className="space-y-6">
          <h4 className="font-semibold text-gray-900">Search Summary</h4>
          
          {/* Overview Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-blue-50 rounded-lg p-4 text-center">
              <div className="text-2xl font-bold text-blue-600">
                {searchResults.document_summary.total_documents}
              </div>
              <div className="text-sm text-blue-700">Documents</div>
            </div>
            <div className="bg-green-50 rounded-lg p-4 text-center">
              <div className="text-2xl font-bold text-green-600">
                {searchResults.document_summary.total_chunks_analyzed}
              </div>
              <div className="text-sm text-green-700">Chunks Analyzed</div>
            </div>
            <div className="bg-purple-50 rounded-lg p-4 text-center">
              <div className="text-2xl font-bold text-purple-600">
                {searchResults.document_summary.relevance_distribution?.high || 0}
              </div>
              <div className="text-sm text-purple-700">Highly Relevant</div>
            </div>
            <div className="bg-orange-50 rounded-lg p-4 text-center">
              <div className="text-2xl font-bold text-orange-600">
                {(searchResults.document_summary.relevance_distribution?.medium || 0) + 
                 (searchResults.document_summary.relevance_distribution?.low || 0)}
              </div>
              <div className="text-sm text-orange-700">Other Matches</div>
            </div>
          </div>
          
          {/* Document Details */}
          <div>
            <h5 className="font-medium text-gray-900 mb-3">Document Breakdown</h5>
            <div className="space-y-2">
              {searchResults.document_summary.documents_list?.map((doc, index) => (
                <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center gap-3">
                    <FileText className="h-4 w-4 text-gray-500" />
                    <span className="font-medium text-gray-900">{doc.filename}</span>
                  </div>
                  <div className="flex items-center gap-4 text-sm text-gray-600">
                    <span>{doc.chunks_found} chunks found</span>
                    <span className="px-2 py-1 bg-white rounded border">
                      {(doc.max_relevance * 100).toFixed(1)}% max relevance
                    </span>
                    <button
                      onClick={() => onDocumentSelect(doc.filename)}
                      className="text-indigo-600 hover:text-indigo-800 flex items-center gap-1"
                    >
                      <ArrowRight size={12} />
                      Focus
                    </button>
                  </div>
                </div>
              )) || []}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Main App Component
const SemanticSearchApp = () => {
  const [activeTab, setActiveTab] = useState('search');
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isSearching, setIsSearching] = useState(false);
  const [selectedDocument, setSelectedDocument] = useState('');
  const [maxResults, setMaxResults] = useState(10);
  const [stats, setStats] = useState(null);
  const [health, setHealth] = useState(null);
  const [notifications, setNotifications] = useState([]);
  const fileInputRef = useRef(null);

  const API_BASE = 'http://localhost:8000';

  // Add notification
  const addNotification = (message, type = 'info') => {
    const id = Date.now();
    setNotifications(prev => [...prev, { id, message, type }]);
    setTimeout(() => {
      setNotifications(prev => prev.filter(n => n.id !== id));
    }, 5000);
  };

  // Fetch documents
  const fetchDocuments = async () => {
    try {
      const response = await fetch(`${API_BASE}/documents`);
      const data = await response.json();
      setDocuments(data.indexed_documents || []);
    } catch (error) {
      addNotification('Failed to fetch documents', 'error');
    }
  };

  // Fetch stats
  const fetchStats = async () => {
    try {
      const response = await fetch(`${API_BASE}/stats`);
      const data = await response.json();
      setStats(data);
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    }
  };

  // Fetch health
  const fetchHealth = async () => {
    try {
      const response = await fetch(`${API_BASE}/health`);
      const data = await response.json();
      setHealth(data);
    } catch (error) {
      console.error('Failed to fetch health:', error);
    }
  };

  // Upload file
  const handleFileUpload = async () => {
    if (!selectedFile) return;

    setIsUploading(true);
    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const response = await fetch(`${API_BASE}/upload`, {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        const data = await response.json();
        addNotification(`Successfully uploaded: ${data.filename}`, 'success');
        setSelectedFile(null);
        fileInputRef.current.value = '';
        fetchDocuments();
        fetchStats();
      } else {
        const error = await response.json();
        addNotification(error.detail || 'Upload failed', 'error');
      }
    } catch (error) {
      addNotification('Upload failed: Network error', 'error');
    } finally {
      setIsUploading(false);
    }
  };

  // Enhanced search function
  const handleSearch = async () => {
    if (!searchQuery.trim()) return;

    setIsSearching(true);
    try {
      const url = new URL(`${API_BASE}/search`);
      url.searchParams.append('q', searchQuery);
      url.searchParams.append('max_results', maxResults.toString());
      if (selectedDocument) {
        url.searchParams.append('filename', selectedDocument);
      }

      const response = await fetch(url);
      const data = await response.json();
      setSearchResults(data);
      
      // Show success notification with search scope
      const scope = selectedDocument ? 'single document' : `${data.documents_searched || 0} documents`;
      addNotification(`Search completed across ${scope}`, 'success');
      
    } catch (error) {
      addNotification('Search failed', 'error');
    } finally {
      setIsSearching(false);
    }
  };

  // Delete document
  const handleDeleteDocument = async (filename) => {
    try {
      const response = await fetch(`${API_BASE}/documents/${filename}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        addNotification(`Deleted: ${filename}`, 'success');
        fetchDocuments();
        fetchStats();
      } else {
        addNotification('Failed to delete document', 'error');
      }
    } catch (error) {
      addNotification('Delete failed', 'error');
    }
  };

  useEffect(() => {
    fetchDocuments();
    fetchStats();
    fetchHealth();
  }, []);

  // Notification Component
  const Notification = ({ notification }) => (
    <div className={`fixed top-4 right-4 p-4 rounded-lg shadow-lg z-50 max-w-md transition-all duration-300 ${
      notification.type === 'success' ? 'bg-green-500 text-white' :
      notification.type === 'error' ? 'bg-red-500 text-white' :
      'bg-blue-500 text-white'
    }`}>
      <div className="flex items-center gap-2">
        {notification.type === 'success' && <CheckCircle size={20} />}
        {notification.type === 'error' && <AlertCircle size={20} />}
        <span>{notification.message}</span>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50">
      {/* Notifications */}
      {notifications.map(notification => (
        <Notification key={notification.id} notification={notification} />
      ))}

      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-lg">
                <Brain className="h-6 w-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">Semantic Search</h1>
                <p className="text-sm text-gray-500">AI-Powered Multi-Document Intelligence</p>
              </div>
            </div>
            
            {/* Health Status */}
            {health && (
              <div className="flex items-center gap-2">
                <div className={`w-2 h-2 rounded-full ${
                  health.status === 'healthy' ? 'bg-green-500' :
                  health.status === 'degraded' ? 'bg-yellow-500' : 'bg-red-500'
                }`}></div>
                <span className="text-sm text-gray-600 capitalize">{health.status}</span>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Navigation */}
      <nav className="bg-white border-b border-gray-200 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex space-x-8">
            {[
              { id: 'search', label: 'Search', icon: Search },
              { id: 'upload', label: 'Upload', icon: Upload },
              { id: 'documents', label: 'Documents', icon: FileText },
              { id: 'analytics', label: 'Analytics', icon: Database }
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-3 py-4 border-b-2 font-medium text-sm transition-colors ${
                  activeTab === tab.id
                    ? 'border-indigo-500 text-indigo-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <tab.icon size={16} />
                {tab.label}
              </button>
            ))}
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Enhanced Search Tab */}
        {activeTab === 'search' && (
          <div className="space-y-6">
            {/* Search Interface */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">
                Intelligent Document Search
              </h2>
              
              {/* Search Configuration */}
              <div className="mb-4 p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="font-medium text-gray-900">Search Scope</h3>
                  <span className="text-sm text-gray-500">
                    {documents.length} documents available
                  </span>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Target Documents
                    </label>
                    <select
                      value={selectedDocument}
                      onChange={(e) => setSelectedDocument(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500"
                    >
                      <option value="">🌐 Search All Documents</option>
                      {documents.map(doc => (
                        <option key={doc} value={doc}>📄 {doc}</option>
                      ))}
                    </select>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Result Depth
                    </label>
                    <select
                      value={maxResults}
                      onChange={(e) => setMaxResults(parseInt(e.target.value))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500"
                    >
                      <option value={5}>5 - Quick Overview</option>
                      <option value={10}>10 - Standard</option>
                      <option value={20}>20 - Comprehensive</option>
                      <option value={30}>30 - Deep Analysis</option>
                    </select>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Search Type
                    </label>
                    <div className="flex items-center gap-2 text-sm">
                      {selectedDocument ? (
                        <span className="px-3 py-1 bg-purple-100 text-purple-800 rounded-full">
                          Single Document
                        </span>
                      ) : (
                        <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full">
                          Multi-Document
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              </div>
              
              {/* Main Search Bar */}
              <div className="flex gap-4 mb-4">
                <div className="flex-1">
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                    placeholder={selectedDocument 
                      ? `Search within ${selectedDocument}...` 
                      : "Search across all documents for comprehensive insights..."
                    }
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-lg"
                  />
                </div>
                
                <button
                  onClick={handleSearch}
                  disabled={isSearching || !searchQuery.trim()}
                  className="px-8 py-3 bg-gradient-to-r from-indigo-500 to-purple-600 text-white rounded-lg hover:from-indigo-600 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 font-medium"
                >
                  {isSearching ? <Loader className="animate-spin" size={20} /> : <Search size={20} />}
                  {isSearching ? 'Analyzing...' : 'Search'}
                </button>
              </div>

              {/* Advanced Search Examples */}
              <div className="space-y-3">
                <h4 className="font-medium text-gray-900">Try these advanced queries:</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                  {[
                    "Compare methodologies across all research papers",
                    "What are the main conclusions from the studies?",
                    "Find contradictions or different viewpoints",
                    "Summarize key findings from all documents",
                    "How do the results vary between different approaches?",
                    "What are the common themes mentioned?"
                  ].map(example => (
                    <button
                      key={example}
                      onClick={() => setSearchQuery(example)}
                      className="text-left px-3 py-2 text-sm bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
                    >
                      {example}
                    </button>
                  ))}
                </div>
              </div>
              
              {/* Search Tips */}
              <div className="mt-4 p-3 bg-blue-50 rounded-lg">
                <h4 className="font-medium text-blue-900 mb-2">💡 Search Tips</h4>
                <ul className="text-sm text-blue-800 space-y-1">
                  <li>• Ask comparative questions to analyze multiple documents</li>
                  <li>• Use specific terms to find exact information</li>
                  <li>• Try conceptual queries to discover connections</li>
                  <li>• Select a specific document for focused analysis</li>
                </ul>
              </div>
            </div>

            {/* Enhanced Search Results */}
            {searchResults && (
              <EnhancedSearchResults 
                searchResults={searchResults}
                onDocumentSelect={(filename) => {
                  setSelectedDocument(filename);
                  addNotification(`Focused search on: ${filename}`, 'info');
                }}
              />
            )}
          </div>
        )}

        {/* Upload Tab */}
        {activeTab === 'upload' && (
          <div className="space-y-6">
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Upload Documents</h2>
              
              {/* Drop Zone */}
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-indigo-400 transition-colors">
                <Upload className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                <div className="space-y-2">
                  <p className="text-lg font-medium text-gray-900">Drop files here or click to browse</p>
                  <p className="text-gray-500">Supports PDF, DOCX, PPTX, TXT files up to 50MB</p>
                </div>
                
                <input
                  ref={fileInputRef}
                  type="file"
                  onChange={(e) => setSelectedFile(e.target.files[0])}
                  accept=".pdf,.docx,.pptx,.txt"
                  className="hidden"
                />
                
                <button
                  onClick={() => fileInputRef.current.click()}
                  className="mt-4 px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
                >
                  Choose File
                </button>
              </div>

              {/* Selected File */}
              {selectedFile && (
                <div className="mt-4 p-4 bg-gray-50 rounded-lg">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <FileText className="h-5 w-5 text-gray-500" />
                      <div>
                        <p className="font-medium text-gray-900">{selectedFile.name}</p>
                        <p className="text-sm text-gray-500">
                          {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                        </p>
                      </div>
                    </div>
                    <button
                      onClick={handleFileUpload}
                      disabled={isUploading}
                      className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 flex items-center gap-2"
                    >
                      {isUploading ? <Loader className="animate-spin" size={16} /> : <Upload size={16} />}
                      {isUploading ? 'Uploading...' : 'Upload'}
                    </button>
                  </div>
                </div>
              )}

              {/* Supported Formats */}
              <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-4">
                {[
                  { ext: 'PDF', desc: 'Portable Document Format' },
                  { ext: 'DOCX', desc: 'Microsoft Word Document' },
                  { ext: 'PPTX', desc: 'PowerPoint Presentation' },
                  { ext: 'TXT', desc: 'Plain Text File' }
                ].map(format => (
                  <div key={format.ext} className="text-center p-3 border border-gray-200 rounded-lg">
                    <div className="font-semibold text-gray-900">{format.ext}</div>
                    <div className="text-xs text-gray-500 mt-1">{format.desc}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Documents Tab */}
        {activeTab === 'documents' && (
          <div className="space-y-6">
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-lg font-semibold text-gray-900">Document Library</h2>
                <span className="text-sm text-gray-500">{documents.length} documents</span>
              </div>

              {documents.length === 0 ? (
                <div className="text-center py-8">
                  <FileText className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                  <p className="text-gray-500">No documents uploaded yet</p>
                  <button
                    onClick={() => setActiveTab('upload')}
                    className="mt-4 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
                  >
                    Upload Your First Document
                  </button>
                </div>
              ) : (
                <div className="space-y-3">
                  {documents.map(doc => (
                    <div key={doc} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50">
                      <div className="flex items-center gap-3">
                        <FileText className="h-5 w-5 text-gray-500" />
                        <div>
                          <p className="font-medium text-gray-900">{doc}</p>
                          <p className="text-sm text-gray-500">
                            {doc.split('.').pop().toUpperCase()} • Indexed
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => {
                            setSelectedDocument(doc);
                            setActiveTab('search');
                            addNotification(`Focused search on: ${doc}`, 'info');
                          }}
                          className="p-2 text-gray-500 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg"
                          title="Search in this document"
                        >
                          <Eye size={16} />
                        </button>
                        <button
                          onClick={() => handleDeleteDocument(doc)}
                          className="p-2 text-gray-500 hover:text-red-600 hover:bg-red-50 rounded-lg"
                          title="Delete document"
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Analytics Tab */}
        {activeTab === 'analytics' && (
          <div className="space-y-6">
            {/* Stats Cards */}
            {stats && (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-blue-100 rounded-lg">
                      <Database className="h-5 w-5 text-blue-600" />
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Total Vectors</p>
                      <p className="text-2xl font-bold text-gray-900">
                        {stats.pinecone_stats?.total_vectors || 0}
                      </p>
                    </div>
                  </div>
                </div>

                <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-green-100 rounded-lg">
                      <FileText className="h-5 w-5 text-green-600" />
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Documents</p>
                      <p className="text-2xl font-bold text-gray-900">{documents.length}</p>
                    </div>
                  </div>
                </div>

                <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-purple-100 rounded-lg">
                      <Brain className="h-5 w-5 text-purple-600" />
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Embedding Dim</p>
                      <p className="text-2xl font-bold text-gray-900">
                        {stats.pinecone_stats?.embedding_dimension || 384}
                      </p>
                    </div>
                  </div>
                </div>

                <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-indigo-100 rounded-lg">
                      <Globe className="h-5 w-5 text-indigo-600" />
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Index</p>
                      <p className="text-lg font-bold text-gray-900">
                        {stats.pinecone_stats?.index_name || 'N/A'}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* System Health */}
            {health && (
              <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">System Health</h3>
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-gray-600">Gemini API</span>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      health.components?.gemini_api_status === 'working' 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-red-100 text-red-800'
                    }`}>
                      {health.components?.gemini_api_status || 'Unknown'}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-gray-600">Pinecone</span>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      health.components?.pinecone_status === 'connected' 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-red-100 text-red-800'
                    }`}>
                      {health.components?.pinecone_status || 'Unknown'}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-gray-600">Embedding Model</span>
                    <span className="text-sm text-gray-500">
                      {health.components?.embedding_model || 'N/A'}
                    </span>
                  </div>
                </div>
              </div>
            )}

            {/* Advanced Analytics */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Usage Analytics</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="text-center">
                  <div className="text-3xl font-bold text-indigo-600 mb-2">
                    {searchResults ? '1' : '0'}
                  </div>
                  <p className="text-sm text-gray-600">Recent Searches</p>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold text-green-600 mb-2">
                    {documents.length}
                  </div>
                  <p className="text-sm text-gray-600">Active Documents</p>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold text-purple-600 mb-2">
                    {stats?.pinecone_stats?.total_vectors ? 
                      Math.round(stats.pinecone_stats.total_vectors / Math.max(documents.length, 1)) : 
                      0}
                  </div>
                  <p className="text-sm text-gray-600">Avg Chunks/Doc</p>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
};

export default SemanticSearchApp;