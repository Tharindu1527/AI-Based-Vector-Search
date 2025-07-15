// Frontend/src/App.jsx
import React, { useState, useEffect, useRef } from 'react';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import AuthForm from './components/Auth';
import { 
  Search, 
  Upload, 
  FileText, 
  Trash2, 
  Brain, 
  Database, 
  CheckCircle, 
  AlertCircle, 
  Loader, 
  Eye, 
  ChevronDown, 
  ChevronUp, 
  Book, 
  TrendingUp, 
  Plus, 
  Edit, 
  FolderPlus, 
  Folder, 
  Settings, 
  X, 
  MessageSquare,
  BarChart3,
  History,
  User,
  Menu,
  ArrowRight,
  AtSign,
  Send,
  Sparkles,
  LogOut
} from 'lucide-react';

// Enhanced Search Results Component (same as before but with auth)
const EnhancedSearchResults = ({ searchResults, onDocumentSelect, spaces }) => {
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
      case 'highly_relevant': return 'bg-emerald-100 text-emerald-800';
      case 'moderately_relevant': return 'bg-amber-100 text-amber-800';
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

  const getSpaceName = (spaceId) => {
    const space = spaces.find(s => s.id === spaceId);
    return space ? space.name : spaceId;
  };

  const formatAIResponse = (text) => {
    if (!text) return '';
    
    let formatted = text
      .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
      .replace(/\*([^*]+)\*/g, '<em>$1</em>')
      .replace(/\*{3,}/g, '')
      .replace(/^\*+\s*/, '')
      .replace(/\s*\*+$/, '')
      .replace(/\*{2,}/g, '');
    
    const paragraphs = formatted.split('\n').filter(p => p.trim());
    
    return paragraphs.map((paragraph, index) => {
      let cleanParagraph = paragraph
        .trim()
        .replace(/^\*+\s*/, '')
        .replace(/\s*\*+$/, '')
        .replace(/\s+/g, ' ');
      
      return (
        <div key={index} className="mb-4 last:mb-0">
          <p 
            className="text-gray-700 leading-relaxed"
            dangerouslySetInnerHTML={{ __html: cleanParagraph }}
          />
        </div>
      );
    });
  };

  if (!searchResults) return null;

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 mb-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center p-6 border-b border-gray-100">
        <h3 className="text-lg font-semibold text-gray-900 mb-2 sm:mb-0">
          Search Results
        </h3>
        <div className="flex flex-wrap items-center gap-2 text-sm text-gray-500">
          <span className="bg-gray-100 px-2 py-1 rounded-full">{searchResults.total_results} chunks</span>
          <span className="bg-blue-100 px-2 py-1 rounded-full text-blue-700">{searchResults.spaces_searched || 0} spaces</span>
          <span className="bg-green-100 px-2 py-1 rounded-full text-green-700">{searchResults.documents_searched || 0} documents</span>
        </div>
      </div>

      <div className="flex border-b border-gray-100 px-6">
        {[
          { id: 'answer', label: 'AI Answer', icon: Sparkles, count: null },
          { id: 'sources', label: 'Sources', icon: FileText, count: searchResults.sources?.length || 0 },
          { id: 'insights', label: 'Insights', icon: TrendingUp, count: searchResults.cross_document_insights?.length || 0 },
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setSelectedTab(tab.id)}
            className={`flex items-center gap-2 px-4 py-3 border-b-2 text-sm font-medium transition-colors ${
              selectedTab === tab.id
                ? 'border-indigo-500 text-indigo-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <tab.icon size={16} />
            {tab.label}
            {tab.count !== null && (
              <span className="bg-gray-100 text-gray-600 px-2 py-1 rounded-full text-xs">
                {tab.count}
              </span>
            )}
          </button>
        ))}
      </div>

      <div className="p-6">
        {selectedTab === 'answer' && (
          <div className="bg-gradient-to-br from-indigo-50 via-white to-purple-50 rounded-xl p-6 border border-indigo-100">
            <div className="flex items-start gap-4">
              <div className="flex-shrink-0">
                <div className="p-3 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-xl shadow-lg">
                  <Sparkles className="h-6 w-6 text-white" />
                </div>
              </div>
              <div className="flex-1 min-w-0">
                <h4 className="font-semibold text-gray-900 mb-4 text-lg">
                  AI Analysis
                </h4>
                <div className="prose prose-sm max-w-none">
                  {formatAIResponse(searchResults.answer)}
                </div>
              </div>
            </div>
          </div>
        )}

        {selectedTab === 'sources' && searchResults.sources && (
          <div className="space-y-4">
            {searchResults.sources.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <FileText className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                <p>No sources found for this query</p>
              </div>
            ) : (
              searchResults.sources.map((source, index) => (
                <div key={source.id} className="border border-gray-200 rounded-xl overflow-hidden hover:shadow-md transition-shadow">
                  <div className="bg-gray-50 px-4 py-3 flex items-center justify-between">
                    <div className="flex items-center gap-3 flex-1 min-w-0">
                      <div className="flex items-center gap-2 min-w-0">
                        <Folder className="h-4 w-4 text-gray-500 flex-shrink-0" />
                        <span className="text-sm text-gray-600 truncate">{getSpaceName(source.space_id)}</span>
                        <span className="text-gray-400">→</span>
                        <FileText className="h-4 w-4 text-gray-500 flex-shrink-0" />
                        <span className="font-medium text-gray-900 truncate">{source.filename}</span>
                      </div>
                      <span className={`px-3 py-1 rounded-full text-xs font-medium flex items-center gap-1 flex-shrink-0 ${getRelevanceColor(source.relevance_category)}`}>
                        {getRelevanceIcon(source.relevance_category)}
                        {(source.similarity_score * 100).toFixed(1)}%
                      </span>
                    </div>
                    
                    <div className="flex items-center gap-2 flex-shrink-0">
                      <button
                        onClick={() => onDocumentSelect(source.filename, source.space_id)}
                        className="text-xs text-indigo-600 hover:text-indigo-800 flex items-center gap-1 px-2 py-1 rounded hover:bg-indigo-50"
                      >
                        <Eye size={12} />
                        Focus
                      </button>
                      <button
                        onClick={() => toggleSourceExpansion(source.id)}
                        className="p-1 hover:bg-gray-200 rounded"
                      >
                        {expandedSources[source.id] ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                      </button>
                    </div>
                  </div>
                  
                  <div className="p-4">
                    <div className="text-sm text-gray-700 leading-relaxed">
                      {expandedSources[source.id] ? source.full_text : source.text_preview}
                    </div>
                    
                    <div className="flex items-center gap-4 mt-3 text-xs text-gray-500">
                      <span>Page ~{source.estimated_page || 1}</span>
                      <span>•</span>
                      <span>Chunk {source.chunk_id + 1}/{source.total_chunks_in_document}</span>
                      <span>•</span>
                      <span>{source.content_length} characters</span>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {selectedTab === 'insights' && (
          <div className="space-y-4">
            {searchResults.cross_document_insights && searchResults.cross_document_insights.length > 0 ? (
              <div className="space-y-3">
                {searchResults.cross_document_insights.map((insight, index) => (
                  <div key={index} className="bg-blue-50 border border-blue-200 rounded-xl p-4">
                    <div className="flex items-start gap-3">
                      <TrendingUp className="h-5 w-5 text-blue-600 mt-0.5 flex-shrink-0" />
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-xs font-medium">
                            {insight.type.replace('_', ' ').toUpperCase()}
                          </span>
                        </div>
                        <p className="text-gray-700 text-sm leading-relaxed">{insight.insight}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-12 text-gray-500">
                <TrendingUp className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                <p className="text-lg font-medium mb-2">No Cross-Space Insights</p>
                <p className="text-sm">Insights are generated when searching across multiple spaces with related content.</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

// Space Management Modal (same as before)
const SpaceModal = ({ isOpen, onClose, space, onSave, mode = 'create' }) => {
  const [formData, setFormData] = useState({
    name: space?.name || '',
    description: space?.description || ''
  });
  const [errors, setErrors] = useState({});

  useEffect(() => {
    if (space) {
      setFormData({
        name: space.name || '',
        description: space.description || ''
      });
    }
  }, [space]);

  const handleSubmit = (e) => {
    e.preventDefault();
    const newErrors = {};

    if (!formData.name.trim()) {
      newErrors.name = 'Space name is required';
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    onSave(formData);
    setFormData({ name: '', description: '' });
    setErrors({});
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-md">
        <div className="flex justify-between items-center p-6 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">
            {mode === 'create' ? 'Create New Space' : 'Edit Space'}
          </h3>
          <button
            onClick={onClose}
            className="p-1 hover:bg-gray-100 rounded-lg"
          >
            <X size={20} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Space Name
            </label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent ${
                errors.name ? 'border-red-500' : 'border-gray-300'
              }`}
              placeholder="e.g., Medical Documents, Legal Files"
            />
            {errors.name && <p className="text-red-500 text-xs mt-1">{errors.name}</p>}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Description (Optional)
            </label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              rows={3}
              placeholder="Brief description of this space..."
            />
          </div>

          <div className="flex gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="flex-1 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
            >
              {mode === 'create' ? 'Create Space' : 'Save Changes'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// Updated Sidebar Component with user info
const Sidebar = ({ activeTab, setActiveTab, spaces, onCreateSpace, isMobileOpen, setIsMobileOpen, user, onLogout }) => {
  const sidebarItems = [
    { id: 'search', label: 'New Chat', icon: MessageSquare, shortcut: '⌘N' },
    { id: 'spaces', label: 'Spaces', icon: Folder, shortcut: '⌘S' },
    { id: 'analytics', label: 'Analytics', icon: BarChart3, shortcut: '⌘A' },
    { id: 'upload', label: 'Upload', icon: Upload, shortcut: '⌘U' },
    { id: 'history', label: 'History', icon: History, shortcut: '⌘H' },
  ];

  const bottomItems = [
    { id: 'settings', label: 'Settings', icon: Settings },
  ];

  return (
    <>
      {isMobileOpen && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
          onClick={() => setIsMobileOpen(false)}
        />
      )}
      
      <div className={`fixed left-0 top-0 h-screen w-64 bg-gray-900 text-white flex flex-col z-50 transform transition-transform duration-300 ease-in-out ${
        isMobileOpen ? 'translate-x-0' : '-translate-x-full'
      } lg:translate-x-0`}>
        <div className="flex items-center justify-between p-4 border-b border-gray-700">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-xl shadow-lg">
              <Brain className="h-6 w-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold">Beecok</h1>
              <p className="text-xs text-gray-400">AI-Powered Search</p>
            </div>
          </div>
          <button
            onClick={() => setIsMobileOpen(false)}
            className="lg:hidden p-1 hover:bg-gray-700 rounded-lg transition-colors"
          >
            <X size={20} />
          </button>
        </div>

        {/* User Info */}
        <div className="p-4 border-b border-gray-700">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-indigo-600 rounded-full flex items-center justify-center">
              <User className="h-5 w-5 text-white" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-white truncate">{user?.username}</p>
              <p className="text-xs text-gray-400 truncate">{user?.email}</p>
            </div>
          </div>
        </div>

        <div className="flex-1 flex flex-col overflow-hidden">
          <div className="p-4 space-y-1">
            {sidebarItems.map(item => (
              <button
                key={item.id}
                onClick={() => {
                  setActiveTab(item.id);
                  setIsMobileOpen(false);
                }}
                className={`w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-left transition-all duration-200 group ${
                  activeTab === item.id
                    ? 'bg-indigo-600 text-white shadow-lg'
                    : 'text-gray-300 hover:text-white hover:bg-gray-700'
                }`}
              >
                <div className="flex items-center gap-3">
                  <item.icon size={20} />
                  <span className="font-medium">{item.label}</span>
                </div>
                <span className={`text-xs opacity-50 group-hover:opacity-100 transition-opacity ${
                  activeTab === item.id ? 'opacity-100' : ''
                }`}>
                  {item.shortcut}
                </span>
              </button>
            ))}
          </div>

          <div className="px-4 flex-1 overflow-hidden">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wide">Recent Spaces</h3>
              <button
                onClick={onCreateSpace}
                className="p-1.5 hover:bg-gray-700 rounded-lg transition-colors group"
                title="Create new space"
              >
                <Plus size={16} className="group-hover:scale-110 transition-transform" />
              </button>
            </div>
            <div className="space-y-1 overflow-y-auto max-h-48">
              {spaces.slice(0, 5).map(space => (
                <button
                  key={space.id}
                  onClick={() => {
                    setActiveTab('spaces');
                    setIsMobileOpen(false);
                  }}
                  className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-left hover:bg-gray-700 transition-colors group"
                >
                  <Folder className="h-4 w-4 text-gray-400 group-hover:scale-110 transition-transform flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <span className="text-sm text-gray-300 truncate block">{space.name}</span>
                    <span className="text-xs text-gray-500">{space.document_count} docs</span>
                  </div>
                </button>
              ))}
              {spaces.length === 0 && (
                <div className="text-center py-4 text-gray-500 text-sm">
                  No spaces yet
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="p-4 border-t border-gray-700">
          <div className="space-y-1">
            {bottomItems.map(item => (
              <button
                key={item.id}
                onClick={() => {
                  setActiveTab(item.id);
                  setIsMobileOpen(false);
                }}
                className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-left transition-all duration-200 ${
                  activeTab === item.id
                    ? 'bg-indigo-600 text-white shadow-lg'
                    : 'text-gray-300 hover:text-white hover:bg-gray-700'
                }`}
              >
                <item.icon size={20} />
                <span className="font-medium">{item.label}</span>
              </button>
            ))}
            
            {/* Logout Button */}
            <button
              onClick={onLogout}
              className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-left transition-all duration-200 text-gray-300 hover:text-white hover:bg-red-600"
            >
              <LogOut size={20} />
              <span className="font-medium">Logout</span>
            </button>
          </div>
        </div>
      </div>
    </>
  );
};

// Main authenticated app component
const AuthenticatedApp = () => {
  const { user, logout } = useAuth();
  const [activeTab, setActiveTab] = useState('search');
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState(null);
  const [spaces, setSpaces] = useState([]);
  const [selectedSpaces, setSelectedSpaces] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [selectedSpace, setSelectedSpace] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [isSearching, setIsSearching] = useState(false);
  const [maxResults, setMaxResults] = useState(10);
  const [stats, setStats] = useState(null);
  const [health, setHealth] = useState(null);
  const [notifications, setNotifications] = useState([]);
  const [spaceModal, setSpaceModal] = useState({ isOpen: false, mode: 'create', space: null });
  const [isMobileOpen, setIsMobileOpen] = useState(false);
  
  const [showSpaceSelector, setShowSpaceSelector] = useState(false);
  const [spaceSearchQuery, setSpaceSearchQuery] = useState('');
  const [highlightedSpaceIndex, setHighlightedSpaceIndex] = useState(0);
  const [selectedSpaceInQuery, setSelectedSpaceInQuery] = useState(null);
  
  const fileInputRef = useRef(null);
  const searchInputRef = useRef(null);

  const API_BASE = 'http://localhost:8000';

  // Add notification
  const addNotification = (message, type = 'info') => {
    const id = Date.now();
    setNotifications(prev => [...prev, { id, message, type }]);
    setTimeout(() => {
      setNotifications(prev => prev.filter(n => n.id !== id));
    }, 5000);
  };

  // API call helper with auth
  const apiCall = async (url, options = {}) => {
    const token = localStorage.getItem('token');
    return fetch(url, {
      ...options,
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });
  };

  // Fetch spaces
  const fetchSpaces = async () => {
    try {
      const response = await apiCall(`${API_BASE}/spaces`);
      if (response.ok) {
        const data = await response.json();
        setSpaces(data.spaces || []);
      } else {
        addNotification('Failed to fetch spaces', 'error');
      }
    } catch (error) {
      addNotification('Failed to fetch spaces', 'error');
    }
  };

  // Create space
  const handleCreateSpace = async (spaceData) => {
    try {
      const response = await apiCall(`${API_BASE}/spaces`, {
        method: 'POST',
        body: JSON.stringify(spaceData),
      });

      if (response.ok) {
        addNotification(`Space "${spaceData.name}" created successfully`, 'success');
        fetchSpaces();
        setSpaceModal({ isOpen: false, mode: 'create', space: null });
      } else {
        const error = await response.json();
        addNotification(error.detail || 'Failed to create space', 'error');
      }
    } catch (error) {
      addNotification('Failed to create space', 'error');
    }
  };

  // Update space
  const handleUpdateSpace = async (spaceData) => {
    try {
      const response = await apiCall(`${API_BASE}/spaces/${spaceModal.space.id}`, {
        method: 'PUT',
        body: JSON.stringify(spaceData),
      });

      if (response.ok) {
        addNotification(`Space updated successfully`, 'success');
        fetchSpaces();
        setSpaceModal({ isOpen: false, mode: 'create', space: null });
      } else {
        const error = await response.json();
        addNotification(error.detail || 'Failed to update space', 'error');
      }
    } catch (error) {
      addNotification('Failed to update space', 'error');
    }
  };

  // Delete space
  const handleDeleteSpace = async (spaceId, spaceName) => {
    if (!confirm(`Are you sure you want to delete "${spaceName}" and all its documents?`)) {
      return;
    }

    try {
      const response = await apiCall(`${API_BASE}/spaces/${spaceId}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        addNotification(`Space "${spaceName}" deleted successfully`, 'success');
        fetchSpaces();
        fetchStats();
      } else {
        addNotification('Failed to delete space', 'error');
      }
    } catch (error) {
      addNotification('Failed to delete space', 'error');
    }
  };

  // Upload file to space
  const handleFileUpload = async () => {
    if (!selectedFile || !selectedSpace) {
      addNotification('Please select both a file and a space', 'error');
      return;
    }

    setIsUploading(true);
    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE}/spaces/${selectedSpace}/upload`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        body: formData,
      });

      if (response.ok) {
        const data = await response.json();
        addNotification(`Successfully uploaded to ${data.document.space_name}`, 'success');
        setSelectedFile(null);
        setSelectedSpace('');
        fileInputRef.current.value = '';
        fetchSpaces();
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

  // Handle search
  const handleSearch = async () => {
    if (!searchQuery.trim()) return;

    setIsSearching(true);
    try {
      const url = new URL(`${API_BASE}/search`);
      
      let actualQuery = searchQuery;
      let searchSpaces = [];
      
      if (selectedSpaceInQuery) {
        searchSpaces = [selectedSpaceInQuery.id];
        actualQuery = searchQuery.replace(`@${selectedSpaceInQuery.name}`, '').trim();
      }
      
      url.searchParams.append('q', actualQuery);
      url.searchParams.append('max_results', maxResults.toString());
      
      if (searchSpaces.length > 0) {
        url.searchParams.append('space_ids', searchSpaces.join(','));
      }

      const response = await apiCall(url.toString());
      if (response.ok) {
        const data = await response.json();
        setSearchResults(data);
        
        const scope = searchSpaces.length > 0 ? 
          `space "${selectedSpaceInQuery.name}"` : 
          'all spaces';
        addNotification(`Search completed in ${scope}`, 'success');
      } else {
        const error = await response.json();
        addNotification(error.detail || 'Search failed', 'error');
      }
      
    } catch (error) {
      addNotification('Search failed', 'error');
    } finally {
      setIsSearching(false);
    }
  };

  // Handle search input change
  const handleSearchInputChange = (e) => {
    const value = e.target.value;
    setSearchQuery(value);

    const atIndex = value.lastIndexOf('@');
    if (atIndex !== -1 && atIndex === value.length - 1) {
      setShowSpaceSelector(true);
      setSpaceSearchQuery('');
      setHighlightedSpaceIndex(0);
    } else if (atIndex !== -1 && atIndex < value.length - 1) {
      const searchAfterAt = value.substring(atIndex + 1);
      if (!selectedSpaceInQuery) {
        setShowSpaceSelector(true);
        setSpaceSearchQuery(searchAfterAt);
      }
    } else {
      setShowSpaceSelector(false);
      if (!value.includes('@')) {
        setSelectedSpaceInQuery(null);
      }
    }
  };

  // Handle space selection from dropdown
  const handleSpaceSelect = (space) => {
    const atIndex = searchQuery.lastIndexOf('@');
    const beforeAt = searchQuery.substring(0, atIndex);
    const newQuery = beforeAt + `@${space.name} `;
    setSearchQuery(newQuery);
    setSelectedSpaceInQuery(space);
    setShowSpaceSelector(false);
    searchInputRef.current?.focus();
  };

  // Handle keyboard navigation for space selector
  const handleKeyDown = (e) => {
    if (showSpaceSelector) {
      const filteredSpaces = spaces.filter(space => 
        space.name.toLowerCase().includes(spaceSearchQuery.toLowerCase())
      );

      if (e.key === 'ArrowDown') {
        e.preventDefault();
        setHighlightedSpaceIndex(prev => 
          prev < filteredSpaces.length - 1 ? prev + 1 : 0
        );
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        setHighlightedSpaceIndex(prev => 
          prev > 0 ? prev - 1 : filteredSpaces.length - 1
        );
      } else if (e.key === 'Enter' && filteredSpaces[highlightedSpaceIndex]) {
        e.preventDefault();
        handleSpaceSelect(filteredSpaces[highlightedSpaceIndex]);
      } else if (e.key === 'Escape') {
        setShowSpaceSelector(false);
      }
    } else if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSearch();
    }
  };

  // Delete document from space
  const handleDeleteDocument = async (documentId, spaceId) => {
    try {
      const response = await apiCall(`${API_BASE}/spaces/${spaceId}/documents/${documentId}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        addNotification(`Document deleted successfully`, 'success');
        fetchSpaces();
        fetchStats();
      } else {
        addNotification('Failed to delete document', 'error');
      }
    } catch (error) {
      addNotification('Delete failed', 'error');
    }
  };

  // Fetch stats
  const fetchStats = async () => {
    try {
      const response = await apiCall(`${API_BASE}/stats`);
      if (response.ok) {
        const data = await response.json();
        setStats(data);
      } else {
        setStats(null);
      }
    } catch (error) {
      setStats(null);
    }
  };

  // Fetch health
  const fetchHealth = async () => {
    try {
      const response = await fetch(`${API_BASE}/health`);
      if (response.ok) {
        const data = await response.json();
        setHealth(data);
      } else {
        setHealth({ status: 'unhealthy' });
      }
    } catch (error) {
      setHealth(null);
    }
  };

  useEffect(() => {
    fetchSpaces();
    fetchStats();
    fetchHealth();
  }, []);

  // Space Selection Dropdown Component
  const SpaceSelector = ({ isVisible }) => {
    if (!isVisible) return null;

    const filteredSpaces = spaces.filter(space => 
      space.name.toLowerCase().includes(spaceSearchQuery.toLowerCase())
    );

    return (
      <div className="absolute bottom-full left-0 right-0 bg-white border border-gray-200 rounded-xl shadow-xl mb-2 max-h-60 overflow-y-auto z-50">
        <div className="p-3">
          <div className="text-xs text-gray-500 mb-3 px-2 font-medium">Select a space to search:</div>
          {filteredSpaces.map((space, index) => (
            <button
              key={space.id}
              onClick={() => handleSpaceSelect(space)}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg hover:bg-gray-50 transition-colors ${
                index === highlightedSpaceIndex ? 'bg-indigo-50 border border-indigo-200' : ''
              }`}
            >
              <Folder className="w-4 h-4 text-gray-500 flex-shrink-0" />
              <div className="flex-1 text-left min-w-0">
                <div className="font-medium text-gray-900 truncate">{space.name}</div>
                <div className="text-xs text-gray-500">{space.document_count} documents</div>
              </div>
            </button>
          ))}
          {filteredSpaces.length === 0 && (
            <div className="text-center py-8 text-gray-500 text-sm">
              No spaces found matching "{spaceSearchQuery}"
            </div>
          )}
        </div>
      </div>
    );
  };

  // Notification Component
  const Notification = ({ notification }) => (
    <div className={`fixed top-4 right-4 p-4 rounded-xl shadow-lg z-50 max-w-md transition-all duration-300 transform ${
      notification.type === 'success' ? 'bg-emerald-500 text-white' :
      notification.type === 'error' ? 'bg-red-500 text-white' :
      'bg-blue-500 text-white'
    }`}>
      <div className="flex items-center gap-3">
        {notification.type === 'success' && <CheckCircle size={20} />}
        {notification.type === 'error' && <AlertCircle size={20} />}
        <span className="font-medium">{notification.message}</span>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* Notifications */}
      {notifications.map(notification => (
        <Notification key={notification.id} notification={notification} />
      ))}

      {/* Space Modal */}
      <SpaceModal
        isOpen={spaceModal.isOpen}
        onClose={() => setSpaceModal({ isOpen: false, mode: 'create', space: null })}
        space={spaceModal.space}
        onSave={spaceModal.mode === 'create' ? handleCreateSpace : handleUpdateSpace}
        mode={spaceModal.mode}
      />

      {/* Sidebar */}
      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        spaces={spaces}
        user={user}
        onCreateSpace={() => setSpaceModal({ isOpen: true, mode: 'create', space: null })}
        onLogout={logout}
        isMobileOpen={isMobileOpen}
        setIsMobileOpen={setIsMobileOpen}
      />

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0 lg:ml-64">
        {/* Mobile Header */}
        <div className="lg:hidden bg-white border-b border-gray-200 p-4 flex items-center justify-between sticky top-0 z-30">
          <button
            onClick={() => setIsMobileOpen(true)}
            className="p-2 hover:bg-gray-100 rounded-xl transition-colors"
          >
            <Menu size={24} />
          </button>
          <div className="flex items-center gap-2">
            <Brain className="h-6 w-6 text-indigo-600" />
            <span className="font-bold text-gray-900">Beecok</span>
          </div>
          <div className="w-10" />
        </div>

        {/* Search Interface */}
        {activeTab === 'search' && (
          <div className="flex-1 flex flex-col min-h-0">
            <div className="flex-1 overflow-y-auto p-4 lg:p-6">
              {searchResults && (
                <EnhancedSearchResults 
                  searchResults={searchResults}
                  spaces={spaces}
                  onDocumentSelect={(filename, spaceId) => {
                    setSelectedSpaces([spaceId]);
                    addNotification(`Focused search on: ${filename}`, 'info');
                  }}
                />
              )}
              
              {!searchResults && (
                <div className="flex items-center justify-center min-h-full py-12">
                  <div className="text-center max-w-2xl mx-auto">
                    <div className="mb-8">
                      <div className="mx-auto w-24 h-24 bg-gradient-to-br from-indigo-100 to-purple-100 rounded-full flex items-center justify-center mb-6">
                        <Brain className="h-12 w-12 text-indigo-600" />
                      </div>
                      <h2 className="text-3xl font-bold text-gray-900 mb-4">Welcome back, {user?.username}!</h2>
                      <p className="text-lg text-gray-600 mb-8">
                        Your AI-powered semantic search assistant. Start by typing a question or use @spacename to search within specific spaces.
                      </p>
                    </div>
                    
                    <div className="space-y-4">
                      <h3 className="text-lg font-semibold text-gray-900">Try these examples:</h3>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                        {[
                          "What are the key findings in my research?",
                          "@Medical what are the side effects?",
                          "Compare methodologies across documents",
                          "Summarize the main conclusions",
                          "Find contradictions between documents",
                          "What are common themes in all files?"
                        ].map(example => (
                          <button
                            key={example}
                            onClick={() => setSearchQuery(example)}
                            className="text-left px-4 py-3 text-sm bg-white border border-gray-200 rounded-xl hover:bg-gray-50 hover:border-indigo-300 transition-all duration-200 shadow-sm hover:shadow-md"
                          >
                            <div className="flex items-center gap-2">
                              <Search className="h-4 w-4 text-gray-400" />
                              <span>{example}</span>
                            </div>
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Search Input */}
            <div className="border-t border-gray-200 bg-white p-4 lg:p-6 sticky bottom-0">
              <div className="max-w-4xl mx-auto">
                <div className="relative">
                  <div className="flex items-center bg-white border border-gray-300 rounded-2xl shadow-sm focus-within:ring-2 focus-within:ring-indigo-500 focus-within:border-transparent hover:shadow-md transition-shadow">
                    {selectedSpaceInQuery && (
                      <div className="flex items-center gap-2 px-4 py-3 bg-gradient-to-r from-indigo-50 to-purple-50 rounded-l-2xl border-r border-gray-200">
                        <Folder className="h-4 w-4 text-indigo-600" />
                        <span className="text-sm font-medium text-indigo-700">
                          {selectedSpaceInQuery.name}
                        </span>
                        <button
                          onClick={() => {
                            setSelectedSpaceInQuery(null);
                            setSearchQuery(searchQuery.replace(`@${selectedSpaceInQuery.name}`, '').trim());
                          }}
                          className="p-1 hover:bg-indigo-100 rounded-full transition-colors"
                        >
                          <X size={14} />
                        </button>
                      </div>
                    )}
                    
                    <input
                      ref={searchInputRef}
                      type="text"
                      value={searchQuery}
                      onChange={handleSearchInputChange}
                      onKeyDown={handleKeyDown}
                      placeholder={selectedSpaceInQuery ? "Ask a question..." : "Search across all spaces or type @ to select a space..."}
                      className="flex-1 px-4 py-4 text-lg border-none rounded-2xl focus:outline-none placeholder-gray-400"
                    />
                    
                    <div className="flex items-center gap-2 px-4">
                      {isSearching ? (
                        <div className="p-2">
                          <Loader className="animate-spin h-5 w-5 text-indigo-600" />
                        </div>
                      ) : (
                        <button
                          onClick={handleSearch}
                          disabled={!searchQuery.trim()}
                          className="p-2 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 hover:scale-105"
                        >
                          <Send size={20} />
                        </button>
                      )}
                    </div>
                  </div>

                  <SpaceSelector isVisible={showSpaceSelector} />

                  <div className="mt-3 flex flex-wrap items-center gap-4 text-xs text-gray-500">
                    <div className="flex items-center gap-1">
                      <AtSign size={12} />
                      <span>Use @ to search in specific spaces</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <span>⏎</span>
                      <span>Press Enter to search</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Other Tab Content */}
        {activeTab !== 'search' && (
          <div className="flex-1 overflow-y-auto p-4 lg:p-6">
            {/* Spaces Tab */}
            {activeTab === 'spaces' && (
              <div className="space-y-6">
                <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                  <div>
                    <h2 className="text-3xl font-bold text-gray-900">Your Document Spaces</h2>
                    <p className="text-gray-600 mt-1">Organize your documents into themed collections</p>
                  </div>
                  <button
                    onClick={() => setSpaceModal({ isOpen: true, mode: 'create', space: null })}
                    className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 transition-colors shadow-lg hover:shadow-xl"
                  >
                    <Plus size={18} />
                    Create Space
                  </button>
                </div>

                {spaces.length === 0 ? (
                  <div className="text-center py-16 bg-white rounded-2xl border-2 border-dashed border-gray-300">
                    <FolderPlus className="mx-auto h-16 w-16 text-gray-400 mb-6" />
                    <h3 className="text-xl font-medium text-gray-900 mb-2">No spaces yet</h3>
                    <p className="text-gray-500 mb-6 max-w-md mx-auto">Create your first space to organize documents and enable powerful AI search across your content.</p>
                    <button
                      onClick={() => setSpaceModal({ isOpen: true, mode: 'create', space: null })}
                      className="px-6 py-3 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 transition-colors shadow-lg"
                    >
                      Create Your First Space
                    </button>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                    {spaces.map(space => (
                      <div key={space.id} className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6 hover:shadow-lg transition-all duration-200 hover:-translate-y-1">
                        <div className="flex items-start justify-between mb-4">
                          <div className="flex items-center gap-3 min-w-0 flex-1">
                            <Folder className="h-5 w-5 text-indigo-600 flex-shrink-0" />
                            <h3 className="font-semibold text-gray-900 truncate">{space.name}</h3>
                          </div>
                          <div className="flex items-center gap-1">
                            <button
                              onClick={() => setSpaceModal({ isOpen: true, mode: 'edit', space })}
                              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                              title="Edit space"
                            >
                              <Edit size={14} />
                            </button>
                            <button
                              onClick={() => handleDeleteSpace(space.id, space.name)}
                              className="p-2 hover:bg-red-100 text-red-600 rounded-lg transition-colors"
                              title="Delete space"
                            >
                              <Trash2 size={14} />
                            </button>
                          </div>
                        </div>

                        {space.description && (
                          <p className="text-sm text-gray-600 mb-4 line-clamp-2">{space.description}</p>
                        )}

                        <div className="grid grid-cols-2 gap-4 mb-6">
                          <div className="text-center p-4 bg-gray-50 rounded-xl">
                            <div className="text-2xl font-bold text-gray-900">{space.document_count}</div>
                            <div className="text-xs text-gray-500 font-medium">Documents</div>
                          </div>
                          <div className="text-center p-4 bg-gray-50 rounded-xl">
                            <div className="text-2xl font-bold text-gray-900">
                              {(space.total_size_bytes / 1024 / 1024).toFixed(1)}MB
                            </div>
                            <div className="text-xs text-gray-500 font-medium">Storage</div>
                          </div>
                        </div>

                        <div className="flex gap-2 mb-4">
                          <button
                            onClick={() => {
                              setSelectedSpaceInQuery(space);
                              setSearchQuery(`@${space.name} `);
                              setActiveTab('search');
                            }}
                            className="flex-1 px-3 py-2 bg-indigo-50 text-indigo-700 rounded-xl hover:bg-indigo-100 text-sm font-medium transition-colors"
                          >
                            Search
                          </button>
                          <button
                            onClick={() => {
                              setSelectedSpace(space.id);
                              setActiveTab('upload');
                            }}
                            className="flex-1 px-3 py-2 bg-emerald-50 text-emerald-700 rounded-xl hover:bg-emerald-100 text-sm font-medium transition-colors"
                          >
                            Upload
                          </button>
                        </div>

                        {space.documents && space.documents.length > 0 && (
                          <div className="pt-4 border-t border-gray-100">
                            <div className="flex items-center justify-between mb-3">
                              <span className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Recent Files</span>
                              <span className="text-xs text-gray-400">{space.documents.length} total</span>
                            </div>
                            <div className="space-y-2">
                              {space.documents.slice(0, 3).map(doc => (
                                <div key={doc.id} className="flex items-center justify-between text-xs group">
                                  <div className="flex items-center gap-2 min-w-0 flex-1">
                                    <FileText className="h-3 w-3 text-gray-400 flex-shrink-0" />
                                    <span className="text-gray-700 truncate">{doc.original_file_name}</span>
                                  </div>
                                  <button
                                    onClick={() => handleDeleteDocument(doc.id, space.id)}
                                    className="p-1 hover:bg-red-100 text-red-500 rounded opacity-0 group-hover:opacity-100 transition-all flex-shrink-0"
                                  >
                                    <Trash2 size={10} />
                                  </button>
                                </div>
                              ))}
                              {space.documents.length > 3 && (
                                <div className="text-xs text-gray-400 text-center pt-1">
                                  +{space.documents.length - 3} more files
                                </div>
                              )}
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Upload Tab */}
            {activeTab === 'upload' && (
              <div className="space-y-6">
                <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6 lg:p-8">
                  <h2 className="text-2xl font-bold text-gray-900 mb-2">Upload Documents</h2>
                  <p className="text-gray-600 mb-6">Add new documents to your spaces for AI-powered search</p>
                  
                  <div className="mb-8">
                    <label className="block text-sm font-semibold text-gray-700 mb-3">
                      Select Target Space
                    </label>
                    <select
                      value={selectedSpace}
                      onChange={(e) => setSelectedSpace(e.target.value)}
                      className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-lg"
                    >
                      <option value="">Choose a space...</option>
                      {spaces.map(space => (
                        <option key={space.id} value={space.id}>
                          {space.name} ({space.document_count} documents)
                        </option>
                      ))}
                    </select>
                    {spaces.length === 0 && (
                      <p className="text-sm text-gray-500 mt-2">
                        No spaces available. 
                        <button 
                          onClick={() => setActiveTab('spaces')}
                          className="text-indigo-600 hover:text-indigo-800 ml-1 font-medium"
                        >
                          Create a space first
                        </button>
                      </p>
                    )}
                  </div>
                  
                  <div className="border-2 border-dashed border-gray-300 rounded-2xl p-12 text-center hover:border-indigo-400 transition-colors bg-gray-50 hover:bg-indigo-50">
                    <Upload className="mx-auto h-16 w-16 text-gray-400 mb-6" />
                    <div className="space-y-2 mb-6">
                      <p className="text-xl font-semibold text-gray-900">Drop files here or click to browse</p>
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
                      className="px-8 py-3 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 transition-colors shadow-lg hover:shadow-xl"
                    >
                      Choose Files
                    </button>
                  </div>

                  {(selectedFile || selectedSpace) && (
                    <div className="mt-6 p-6 bg-gray-50 rounded-xl">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {selectedSpace && (
                          <div>
                            <p className="text-sm font-semibold text-gray-700 mb-2">Target Space:</p>
                            <div className="flex items-center gap-3 p-3 bg-white rounded-lg border">
                              <Folder className="h-5 w-5 text-indigo-600" />
                              <span className="text-gray-900 font-medium">
                                {spaces.find(s => s.id === selectedSpace)?.name || 'Unknown Space'}
                              </span>
                            </div>
                          </div>
                        )}
                        
                        {selectedFile && (
                          <div>
                            <p className="text-sm font-semibold text-gray-700 mb-2">Selected File:</p>
                            <div className="flex items-center gap-3 p-3 bg-white rounded-lg border">
                              <FileText className="h-5 w-5 text-gray-500" />
                              <div className="flex-1 min-w-0">
                                <span className="text-gray-900 font-medium truncate block">{selectedFile.name}</span>
                                <span className="text-sm text-gray-500">
                                  {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                                </span>
                              </div>
                            </div>
                          </div>
                        )}
                      </div>
                      
                      {selectedFile && selectedSpace && (
                        <button
                          onClick={handleFileUpload}
                          disabled={isUploading}
                          className="mt-6 w-full px-6 py-3 bg-emerald-600 text-white rounded-xl hover:bg-emerald-700 disabled:opacity-50 flex items-center justify-center gap-3 font-medium shadow-lg transition-all"
                        >
                          {isUploading ? <Loader className="animate-spin" size={20} /> : <Upload size={20} />}
                          {isUploading ? 'Uploading and Processing...' : 'Upload to Space'}
                        </button>
                      )}
                    </div>
                  )}

                  <div className="mt-8 grid grid-cols-2 md:grid-cols-4 gap-4">
                    {[
                      { ext: 'PDF', desc: 'Portable Document', icon: '📄' },
                      { ext: 'DOCX', desc: 'Word Document', icon: '📝' },
                      { ext: 'PPTX', desc: 'PowerPoint', icon: '📊' },
                      { ext: 'TXT', desc: 'Plain Text', icon: '📋' }
                    ].map(format => (
                      <div key={format.ext} className="text-center p-4 border border-gray-200 rounded-xl hover:bg-gray-50 transition-colors">
                        <div className="text-2xl mb-2">{format.icon}</div>
                        <div className="font-semibold text-gray-900">{format.ext}</div>
                        <div className="text-xs text-gray-500 mt-1">{format.desc}</div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Analytics Tab */}
            {activeTab === 'analytics' && (
              <div className="space-y-6">
                <div>
                  <h2 className="text-3xl font-bold text-gray-900 mb-2">Your Analytics</h2>
                  <p className="text-gray-600">Monitor your document spaces and search performance</p>
                </div>

                {(!stats || !health) && (
                  <div className="bg-amber-50 border border-amber-200 rounded-xl p-4">
                    <div className="flex items-center gap-3">
                      <AlertCircle className="h-5 w-5 text-amber-600" />
                      <div>
                        <h3 className="font-medium text-amber-800">Connection Issue</h3>
                        <p className="text-sm text-amber-700">
                          Unable to load analytics data. Please check your connection.
                        </p>
                      </div>
                    </div>
                  </div>
                )}

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                  <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6 hover:shadow-lg transition-shadow">
                    <div className="flex items-center gap-4">
                      <div className="p-3 bg-blue-100 rounded-xl">
                        <Folder className="h-6 w-6 text-blue-600" />
                      </div>
                      <div>
                        <p className="text-sm font-medium text-gray-600">Your Spaces</p>
                        <p className="text-3xl font-bold text-gray-900">
                          {stats?.user_stats?.spaces_count ?? spaces.length}
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6 hover:shadow-lg transition-shadow">
                    <div className="flex items-center gap-4">
                      <div className="p-3 bg-emerald-100 rounded-xl">
                        <FileText className="h-6 w-6 text-emerald-600" />
                      </div>
                      <div>
                        <p className="text-sm font-medium text-gray-600">Your Documents</p>
                        <p className="text-3xl font-bold text-gray-900">
                          {stats?.user_stats?.documents_count ?? spaces.reduce((total, space) => total + (space.document_count || 0), 0)}
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6 hover:shadow-lg transition-shadow">
                    <div className="flex items-center gap-4">
                      <div className="p-3 bg-purple-100 rounded-xl">
                        <MessageSquare className="h-6 w-6 text-purple-600" />
                      </div>
                      <div>
                        <p className="text-sm font-medium text-gray-600">Chat Sessions</p>
                        <p className="text-3xl font-bold text-gray-900">
                          {stats?.user_stats?.chats_count ?? 0}
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6 hover:shadow-lg transition-shadow">
                    <div className="flex items-center gap-4">
                      <div className="p-3 bg-amber-100 rounded-xl">
                        <Database className="h-6 w-6 text-amber-600" />
                      </div>
                      <div>
                        <p className="text-sm font-medium text-gray-600">Storage Used</p>
                        <p className="text-2xl font-bold text-gray-900">
                          {stats?.user_stats ? 
                            `${(stats.user_stats.total_storage_bytes / 1024 / 1024).toFixed(1)}MB` :
                            spaces.length > 0 ? 
                              `${(spaces.reduce((total, space) => total + (space.total_size_bytes || 0), 0) / 1024 / 1024).toFixed(1)}MB` :
                              '0MB'
                          }
                        </p>
                      </div>
                    </div>
                  </div>
                </div>

                {spaces.length > 0 && (
                  <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
                    <h3 className="text-xl font-semibold text-gray-900 mb-6">Your Space Analytics</h3>
                    <div className="space-y-4">
                      {spaces.map((space, index) => {
                        const maxSize = Math.max(...spaces.map(s => s.total_size_bytes || 0));
                        const percentage = maxSize > 0 ? ((space.total_size_bytes || 0) / maxSize) * 100 : 0;
                        
                        return (
                          <div key={index} className="flex items-center justify-between p-4 bg-gray-50 rounded-xl hover:bg-gray-100 transition-colors">
                            <div className="flex items-center gap-4">
                              <Folder className="h-5 w-5 text-indigo-600" />
                              <div>
                                <span className="font-semibold text-gray-900">{space.name}</span>
                                <div className="text-sm text-gray-500">
                                  {space.document_count} documents • {((space.total_size_bytes || 0) / 1024 / 1024).toFixed(1)}MB
                                </div>
                              </div>
                            </div>
                            <div className="flex items-center gap-4">
                              <div className="w-32 bg-gray-200 rounded-full h-3">
                                <div 
                                  className="h-3 rounded-full transition-all duration-500 bg-indigo-600"
                                  style={{ width: `${Math.max(5, percentage)}%` }}
                                ></div>
                              </div>
                              <span className="text-sm font-medium text-gray-700 w-12 text-right">
                                {percentage.toFixed(0)}%
                              </span>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}

                <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
                  <h3 className="text-xl font-semibold text-gray-900 mb-6">System Health</h3>
                  <div className="space-y-4">
                    <div className="flex items-center justify-between p-4 bg-gray-50 rounded-xl">
                      <div className="flex items-center gap-3">
                        <Sparkles className="h-5 w-5 text-purple-600" />
                        <span className="font-medium text-gray-900">Gemini AI</span>
                      </div>
                      <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                        health?.components?.gemini_api_status === 'working' 
                          ? 'bg-emerald-100 text-emerald-800' 
                          : 'bg-red-100 text-red-800'
                      }`}>
                        {health?.components?.gemini_api_status === 'working' ? 'Online' : 'Offline'}
                      </span>
                    </div>
                    <div className="flex items-center justify-between p-4 bg-gray-50 rounded-xl">
                      <div className="flex items-center gap-3">
                        <Database className="h-5 w-5 text-blue-600" />
                        <span className="font-medium text-gray-900">Vector Database</span>
                      </div>
                      <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                        health?.components?.pinecone_status === 'connected' 
                          ? 'bg-emerald-100 text-emerald-800' 
                          : 'bg-red-100 text-red-800'
                      }`}>
                        {health?.components?.pinecone_status === 'connected' ? 'Connected' : 'Disconnected'}
                      </span>
                    </div>
                    <div className="flex items-center justify-between p-4 bg-gray-50 rounded-xl">
                      <div className="flex items-center gap-3">
                        <User className="h-5 w-5 text-green-600" />
                        <span className="font-medium text-gray-900">User Authentication</span>
                      </div>
                      <span className="px-3 py-1 bg-emerald-100 text-emerald-800 rounded-full text-sm font-medium">
                        Active
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Settings Tab */}
            {activeTab === 'settings' && (
              <div className="space-y-6">
                <div>
                  <h2 className="text-3xl font-bold text-gray-900 mb-2">Settings</h2>
                  <p className="text-gray-600">Customize your Beecok experience</p>
                </div>

                <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
                  <div className="space-y-8">
                    {/* Profile Section */}
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900 mb-4">Profile Information</h3>
                      <div className="space-y-6">
                        <div className="flex items-center space-x-6 mb-8">
                          <div className="h-24 w-24 bg-gradient-to-br from-indigo-100 to-purple-100 rounded-full flex items-center justify-center">
                            <User className="h-12 w-12 text-indigo-600" />
                          </div>
                          <div>
                            <h4 className="text-xl font-semibold text-gray-900">{user?.username}</h4>
                            <p className="text-gray-500">{user?.email}</p>
                            <p className="text-sm text-gray-400 mt-1">
                              Member since {new Date(user?.created_at || Date.now()).toLocaleDateString()}
                            </p>
                          </div>
                        </div>
                        
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                              Username
                            </label>
                            <input
                              type="text"
                              value={user?.username || ''}
                              readOnly
                              className="w-full px-4 py-3 border border-gray-300 rounded-xl bg-gray-50 text-gray-600"
                            />
                          </div>
                          
                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                              Email Address
                            </label>
                            <input
                              type="email"
                              value={user?.email || ''}
                              readOnly
                              className="w-full px-4 py-3 border border-gray-300 rounded-xl bg-gray-50 text-gray-600"
                            />
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Search Settings */}
                    <div className="border-t border-gray-200 pt-8">
                      <h3 className="text-lg font-semibold text-gray-900 mb-4">Search Preferences</h3>
                      <div className="space-y-6">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">
                            Default Search Results
                          </label>
                          <select
                            value={maxResults}
                            onChange={(e) => setMaxResults(parseInt(e.target.value))}
                            className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                          >
                            <option value={5}>5 - Quick Overview</option>
                            <option value={10}>10 - Standard</option>
                            <option value={20}>20 - Comprehensive</option>
                            <option value={30}>30 - Deep Analysis</option>
                          </select>
                        </div>
                      </div>
                    </div>

                    {/* About */}
                    <div className="border-t border-gray-200 pt-8">
                      <h3 className="text-lg font-semibold text-gray-900 mb-4">About Beecok</h3>
                      <div className="space-y-4">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                          <div>
                            <h4 className="font-medium text-gray-900 mb-2">Version Information</h4>
                            <div className="text-sm text-gray-600 space-y-1">
                              <p>Version: 2.0.0</p>
                              <p>Release: January 2025</p>
                              <p>Build: Latest with Authentication</p>
                            </div>
                          </div>
                          <div>
                            <h4 className="font-medium text-gray-900 mb-2">Technology Stack</h4>
                            <div className="text-sm text-gray-600 space-y-1">
                              <p>Frontend: React + Tailwind CSS</p>
                              <p>Backend: FastAPI + Python</p>
                              <p>Database: MongoDB</p>
                              <p>AI: Google Gemini + Pinecone</p>
                            </div>
                          </div>
                        </div>
                        <div className="p-4 bg-gray-50 rounded-xl">
                          <p className="text-sm text-gray-700">
                            Beecok v2.0 is an AI-powered semantic search platform with user authentication that helps you organize, search, 
                            and analyze your documents with advanced natural language understanding.
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* History Tab */}
            {activeTab === 'history' && (
              <div className="space-y-6">
                <div>
                  <h2 className="text-3xl font-bold text-gray-900 mb-2">Search History</h2>
                  <p className="text-gray-600">Review your past searches and results</p>
                </div>
                <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-12">
                  <div className="text-center">
                    <History className="h-16 w-16 mx-auto mb-6 text-gray-400" />
                    <h3 className="text-xl font-semibold text-gray-900 mb-2">Search History Coming Soon</h3>
                    <p className="text-gray-500 max-w-md mx-auto">
                      We're working on adding search history functionality to help you track and revisit your previous queries.
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

// Main App wrapper with authentication
const App = () => {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
};

// App content component that uses auth context
const AppContent = () => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return <AuthForm />;
  }

  return <AuthenticatedApp />;
};

export default App;