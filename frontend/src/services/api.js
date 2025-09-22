import axios from 'axios';

// Determine the API base URL based on environment
const getApiBaseUrl = () => {
  console.log('API Service - ENV DEV:', import.meta.env.DEV, 'PROD:', import.meta.env.PROD, 'MODE:', import.meta.env.MODE);
  console.log('API Service - Hostname:', window.location.hostname);

  // Check if we're in development mode or localhost
  if (import.meta.env.DEV || window.location.hostname === 'localhost' || window.location.hostname.startsWith('127.')) {
    return 'http://localhost:8000/api';
  }

  // In production (including Vercel), use the same domain but with /api path
  return '/api';
};

const API_BASE_URL = getApiBaseUrl();

// Create dedicated API instance
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor to include token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
      console.log('🔑 API Request Interceptor - Adding token to:', config.url);
    } else {
      console.warn('⚠️ API Request Interceptor - No token found for:', config.url);
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      // Optionally redirect to login
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authApi = {
  // Sign up a new user
  signup: async (userData) => {
    const response = await apiClient.post('/auth/signup', userData);
    return response.data;
  },

  // Sign in user
  signin: async (credentials) => {
    const response = await apiClient.post('/auth/signin', credentials);
    return response.data;
  },

  // Get current user info
  getCurrentUser: async () => {
    const response = await apiClient.get('/auth/me');
    return response.data;
  },

  // Refresh token
  refreshToken: async () => {
    const response = await apiClient.post('/auth/refresh');
    return response.data;
  }
};

// Notes API
export const notesApi = {
  // Get all notes for the current user
  getAllNotes: async () => {
    const response = await apiClient.get('/notes/');
    return response.data;
  },

  // Get notes by folder
  getNotesByFolder: async (folderId) => {
    const response = await apiClient.get(`/notes/?folder_id=${folderId}`);
    return response.data;
  },

  // Get a specific note
  getNote: async (noteId) => {
    const response = await apiClient.get(`/notes/${noteId}`);
    return response.data;
  },

  // Create a new note
  createNote: async (noteData) => {
    const response = await apiClient.post('/notes/', noteData);
    return response.data;
  },

  // Update a note
  updateNote: async (noteId, noteData) => {
    const response = await apiClient.put(`/notes/${noteId}`, noteData);
    return response.data;
  },

  // Delete a note
  deleteNote: async (noteId) => {
    const response = await apiClient.delete(`/notes/${noteId}`);
    return response.data;
  },

  // Search notes
  searchNotes: async (query) => {
    const response = await apiClient.get(`/notes/search?q=${encodeURIComponent(query)}`);
    return response.data;
  }
};

// Folders API
export const foldersApi = {
  // Get all folders for the current user
  getAllFolders: async () => {
    const response = await apiClient.get('/folders/');
    return response.data;
  },

  // Get a specific folder
  getFolder: async (folderId) => {
    const response = await apiClient.get(`/folders/${folderId}`);
    return response.data;
  },

  // Create a new folder
  createFolder: async (folderData) => {
    const response = await apiClient.post('/folders/', folderData);
    return response.data;
  },

  // Update a folder
  updateFolder: async (folderId, folderData) => {
    const response = await apiClient.put(`/folders/${folderId}`, folderData);
    return response.data;
  },

  // Delete a folder
  deleteFolder: async (folderId) => {
    const response = await apiClient.delete(`/folders/${folderId}`);
    return response.data;
  }
};

// Tags API
export const tagsApi = {
  // Get all tags for the current user
  getAllTags: async () => {
    const response = await apiClient.get('/tags/');
    return response.data;
  }
};

// Export the base apiClient for direct use
export { apiClient };
