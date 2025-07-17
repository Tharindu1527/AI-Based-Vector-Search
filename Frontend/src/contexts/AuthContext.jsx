// Frontend/src/contexts/AuthContext.jsx - Updated with better error handling

import React, { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [loading, setLoading] = useState(true);

  // Updated API_BASE with error handling
  const API_BASE = process.env.NODE_ENV === 'production' 
    ? 'https://your-backend-domain.com' 
    : 'http://localhost:8000';

  // Enhanced API call with retry logic
  const apiCall = async (url, options = {}, retries = 3) => {
    for (let i = 0; i < retries; i++) {
      try {
        const response = await fetch(url, {
          ...options,
          headers: {
            'Content-Type': 'application/json',
            ...options.headers,
          },
        });
        
        if (response.ok) {
          return response;
        } else if (response.status >= 500 && i < retries - 1) {
          // Retry on server errors
          console.log(`API call failed, retrying... (${i + 1}/${retries})`);
          await new Promise(resolve => setTimeout(resolve, 1000 * (i + 1)));
          continue;
        } else {
          return response;
        }
      } catch (error) {
        console.error(`API call attempt ${i + 1} failed:`, error);
        if (i === retries - 1) {
          throw error;
        }
        await new Promise(resolve => setTimeout(resolve, 1000 * (i + 1)));
      }
    }
  };

  // Check if user is authenticated on app load
  useEffect(() => {
    const checkAuth = async () => {
      if (token) {
        try {
          const response = await apiCall(`${API_BASE}/auth/me`, {
            headers: {
              'Authorization': `Bearer ${token}`
            }
          });

          if (response && response.ok) {
            const userData = await response.json();
            setUser(userData);
            console.log('✅ User authenticated successfully');
          } else {
            console.log('❌ Token invalid, removing...');
            localStorage.removeItem('token');
            setToken(null);
          }
        } catch (error) {
          console.error('Auth check failed:', error);
          localStorage.removeItem('token');
          setToken(null);
        }
      }
      setLoading(false);
    };

    checkAuth();
  }, [token]);

  const login = async (email, password) => {
    try {
      console.log('🔐 Attempting login...');
      const response = await apiCall(`${API_BASE}/auth/login`, {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      });

      if (response && response.ok) {
        const data = await response.json();
        const { access_token, user: userData } = data;
        
        localStorage.setItem('token', access_token);
        setToken(access_token);
        setUser(userData);
        
        console.log('✅ Login successful');
        return { success: true };
      } else {
        const error = await response.json();
        console.log('❌ Login failed:', error.detail);
        return { success: false, error: error.detail || 'Login failed' };
      }
    } catch (error) {
      console.error('Login network error:', error);
      return { 
        success: false, 
        error: 'Network error. Please check if the backend server is running on http://localhost:8000' 
      };
    }
  };

  const register = async (username, email, password) => {
    try {
      console.log('📝 Attempting registration...');
      const response = await apiCall(`${API_BASE}/auth/register`, {
        method: 'POST',
        body: JSON.stringify({ username, email, password }),
      });

      if (response && response.ok) {
        const data = await response.json();
        const { access_token, user: userData } = data;
        
        localStorage.setItem('token', access_token);
        setToken(access_token);
        setUser(userData);
        
        console.log('✅ Registration successful');
        return { success: true };
      } else {
        const error = await response.json();
        console.log('❌ Registration failed:', error.detail);
        return { success: false, error: error.detail || 'Registration failed' };
      }
    } catch (error) {
      console.error('Registration network error:', error);
      return { 
        success: false, 
        error: 'Network error. Please check if the backend server is running on http://localhost:8000' 
      };
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
    console.log('👋 User logged out');
  };

  const value = {
    user,
    token,
    loading,
    login,
    register,
    logout,
    isAuthenticated: !!token && !!user,
    apiCall, // Expose apiCall for other components
    API_BASE // Expose API_BASE for other components
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};