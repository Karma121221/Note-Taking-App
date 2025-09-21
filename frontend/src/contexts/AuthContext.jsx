import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

// Determine the API base URL based on environment
const getApiBaseUrl = () => {
  console.log('AuthContext - ENV DEV:', import.meta.env.DEV, 'PROD:', import.meta.env.PROD, 'MODE:', import.meta.env.MODE);
  console.log('AuthContext - Hostname:', typeof window !== 'undefined' ? window.location.hostname : 'SSR');

  // Check if we're in development mode or localhost
  if (import.meta.env.DEV || (typeof window !== 'undefined' && (window.location.hostname === 'localhost' || window.location.hostname.startsWith('127.')))) {
    return 'http://localhost:8000/api';
  }

  // In production (including Vercel), use the same domain but with /api path
  return '/api';
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Configure axios defaults
  const baseURL = getApiBaseUrl();
  console.log('AuthContext - baseURL:', baseURL);
  axios.defaults.baseURL = baseURL;

  // Set up axios interceptor to include token in requests
  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    }

    // Response interceptor to handle token expiration
    const responseInterceptor = axios.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          localStorage.removeItem('token');
          localStorage.removeItem('user');
          setUser(null);
          delete axios.defaults.headers.common['Authorization'];
        }
        return Promise.reject(error);
      }
    );

    return () => {
      axios.interceptors.response.eject(responseInterceptor);
    };
  }, []);

  // Check for existing authentication on mount
  useEffect(() => {
    const checkAuth = async () => {
      try {
        const token = localStorage.getItem('token');
        const savedUser = localStorage.getItem('user');

        if (token && savedUser) {
          setUser(JSON.parse(savedUser));
          axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
        }
      } catch (error) {
        console.error('Auth check failed:', error);
        localStorage.removeItem('token');
        localStorage.removeItem('user');
      } finally {
        setLoading(false);
      }
    };

    checkAuth();
  }, []);

  const login = async (email, password) => {
    try {
      const response = await axios.post('/auth/signin', {
        email,
        password,
      });

      const { access_token } = response.data;
      
      // Get user info
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      const userResponse = await axios.get('/auth/me');
      
      // Save to localStorage
      localStorage.setItem('token', access_token);
      localStorage.setItem('user', JSON.stringify(userResponse.data));
      
      setUser(userResponse.data);
      return userResponse.data;
    } catch (error) {
      console.error('Login failed:', error);
      throw error;
    }
  };

  const register = async (username, email, password, role = 'child', familyCode = '') => {
    try {
      const requestData = {
        name: username,
        email,
        password,
        role,
      };
      
      // Add family code if provided for children
      if (role === 'child' && familyCode.trim()) {
        requestData.family_code = familyCode.trim().toUpperCase();
      }
      
      const response = await axios.post('/auth/signup', requestData);

      // Auto-login after registration
      return await login(email, password);
    } catch (error) {
      console.error('Registration failed:', error);
      throw error;
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    delete axios.defaults.headers.common['Authorization'];
    setUser(null);
  };

  const value = {
    user,
    loading,
    login,
    register,
    logout,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};