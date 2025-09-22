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

  // Create dedicated axios instance for auth
  const baseURL = getApiBaseUrl();
  console.log('AuthContext - baseURL:', baseURL);
  
  const authAxios = axios.create({
    baseURL: baseURL,
    timeout: 10000,
    headers: {
      'Content-Type': 'application/json',
    },
  });

  // Set up axios interceptor to include token in requests
  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      authAxios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    }

    // Response interceptor to handle token expiration
    const responseInterceptor = authAxios.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          localStorage.removeItem('token');
          localStorage.removeItem('user');
          setUser(null);
          delete authAxios.defaults.headers.common['Authorization'];
        }
        return Promise.reject(error);
      }
    );

    return () => {
      authAxios.interceptors.response.eject(responseInterceptor);
    };
  }, []);

  // Check for existing authentication on mount
  useEffect(() => {
    const checkAuth = async () => {
      try {
        const token = localStorage.getItem('token');
        const savedUser = localStorage.getItem('user');

        if (token && savedUser) {
          const userData = JSON.parse(savedUser);
          authAxios.defaults.headers.common['Authorization'] = `Bearer ${token}`;

          // Fetch fresh family data for parents if not already present
          if (userData.role === 'parent' && !userData.family_code) {
            try {
              const familyResponse = await authAxios.get('/family/dashboard');
              const familyData = familyResponse.data;

              // Update user data with family information
              const updatedUserData = {
                ...userData,
                family_code: familyData.family_code,
                family_code_expires: familyData.family_code_expires,
                children: familyData.children || []
              };

              localStorage.setItem('user', JSON.stringify(updatedUserData));
              setUser(updatedUserData);
              console.log('Updated parent user with family data:', updatedUserData);
            } catch (familyError) {
              console.warn('Failed to fetch family dashboard for existing user:', familyError);
              setUser(userData); // Still set the user even if family data fetch fails
            }
          } else {
            setUser(userData);
          }
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
      const response = await authAxios.post('/auth/signin', {
        email,
        password,
      });

      const { access_token } = response.data;

      // Get user info
      authAxios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      const userResponse = await authAxios.get('/auth/me');

      // Fetch family dashboard data for parents
      let familyData = null;
      if (userResponse.data.role === 'parent') {
        try {
          const familyResponse = await authAxios.get('/family/dashboard');
          familyData = familyResponse.data;
          console.log('Family dashboard fetched:', familyData);
        } catch (familyError) {
          console.warn('Failed to fetch family dashboard:', familyError);
        }
      }

      // Merge family data with user data
      const userData = {
        ...userResponse.data,
        family_code: familyData?.family_code || null,
        family_code_expires: familyData?.family_code_expires || null,
        children: familyData?.children || []
      };

      // Save to localStorage
      localStorage.setItem('token', access_token);
      localStorage.setItem('user', JSON.stringify(userData));

      setUser(userData);
      return userData;
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

      console.log('Registering with data:', requestData);
      const response = await authAxios.post('/auth/signup', requestData);
      console.log('Registration response:', response.data);

      // Auto-login after registration - this will now fetch family data for parents
      return await login(email, password);
    } catch (error) {
      console.error('Registration failed:', error);
      throw error;
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    delete authAxios.defaults.headers.common['Authorization'];
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