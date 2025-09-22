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
          console.log('🔐 Auth check - Found existing user:', userData.email, 'Role:', userData.role);
          console.log('🔑 Family data in saved user:', {
            family_code: userData.family_code,
            family_code_expires: userData.family_code_expires,
            children: userData.children
          });

          authAxios.defaults.headers.common['Authorization'] = `Bearer ${token}`;

          // Fetch fresh family data for parents if not already present
          if (userData.role === 'parent') {
            try {
              console.log('👨‍👩‍👧‍👦 Fetching fresh family dashboard for parent...');
              const familyResponse = await authAxios.get('/family/dashboard');
              const familyData = familyResponse.data;

              console.log('📊 Family dashboard response:', familyData);

              // Update user data with family information
              const updatedUserData = {
                ...userData,
                family_code: familyData.family_code,
                family_code_expires: familyData.family_code_expires,
                children: familyData.children || []
              };

              console.log('🔄 Updated user data:', {
                family_code: updatedUserData.family_code,
                family_code_expires: updatedUserData.family_code_expires,
                children_count: updatedUserData.children?.length || 0
              });

              localStorage.setItem('user', JSON.stringify(updatedUserData));
              setUser(updatedUserData);
              console.log('✅ Parent user updated with fresh family data');
            } catch (familyError) {
              console.warn('⚠️ Failed to fetch family dashboard for existing user:', familyError.response?.data || familyError.message);
              console.warn('⚠️ Using saved user data without fresh family info');
              setUser(userData); // Still set the user even if family data fetch fails
            }
          } else {
            console.log('👶 Child user - no family data fetch needed');
            setUser(userData);
          }
        }
      } catch (error) {
        console.error('❌ Auth check failed:', error);
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
      console.log('🔐 Login attempt for:', email);
      const response = await authAxios.post('/auth/signin', {
        email,
        password,
      });

      const { access_token } = response.data;
      console.log('✅ Login successful, received token');

      // Get user info
      authAxios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      const userResponse = await authAxios.get('/auth/me');
      console.log('👤 User info fetched:', userResponse.data.email, 'Role:', userResponse.data.role);

      // Fetch family dashboard data for parents
      let familyData = null;
      if (userResponse.data.role === 'parent') {
        try {
          console.log('👨‍👩‍👧‍👦 Fetching family dashboard for parent...');
          const familyResponse = await authAxios.get('/family/dashboard');
          familyData = familyResponse.data;
          console.log('📊 Family dashboard response:', familyData);
        } catch (familyError) {
          console.warn('⚠️ Failed to fetch family dashboard:', familyError.response?.data || familyError.message);
          console.warn('⚠️ Family data will be null, user can still proceed');
        }
      } else {
        console.log('👶 Child user - no family dashboard needed');
      }

      // Merge family data with user data
      const userData = {
        ...userResponse.data,
        family_code: familyData?.family_code || null,
        family_code_expires: familyData?.family_code_expires || null,
        children: familyData?.children || []
      };

      console.log('🔄 Final user data for login:', {
        email: userData.email,
        role: userData.role,
        family_code: userData.family_code,
        family_code_expires: userData.family_code_expires,
        children_count: userData.children?.length || 0
      });

      // Save to localStorage
      localStorage.setItem('token', access_token);
      localStorage.setItem('user', JSON.stringify(userData));

      setUser(userData);
      console.log('✅ Login process completed successfully');
      return userData;
    } catch (error) {
      console.error('❌ Login failed:', error.response?.data || error.message);
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