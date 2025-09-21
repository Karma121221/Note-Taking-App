import axios from 'axios';

// Determine the API base URL based on environment
const getApiBaseUrl = () => {
  console.log('ENV DEV:', import.meta.env.DEV, 'PROD:', import.meta.env.PROD, 'MODE:', import.meta.env.MODE);
  console.log('Hostname:', window.location.hostname);

  // Check if we're in development mode or localhost
  if (import.meta.env.DEV || window.location.hostname === 'localhost' || window.location.hostname.startsWith('127.')) {
    return 'http://localhost:8000/api';
  }

  // In production (including Vercel), use the same domain but with /api path
  return '/api';
};

const API_BASE_URL = getApiBaseUrl();

// Set up axios defaults
axios.defaults.baseURL = API_BASE_URL;

// Add token to requests if available
const token = localStorage.getItem('token');
if (token) {
  axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
}

// Auth API
export const authApi = {
  // Sign up a new user
  signup: async (userData) => {
    const response = await axios.post('/auth/signup', userData);
    return response.data;
  },

  // Sign in user
  signin: async (credentials) => {
    const response = await axios.post('/auth/signin', credentials);
    return response.data;
  },

  // Get current user info
  getCurrentUser: async () => {
    const response = await axios.get('/auth/me');
    return response.data;
  },

  // Refresh token
  refreshToken: async () => {
    const response = await axios.post('/auth/refresh');
    return response.data;
  }
};

// Notes API
export const notesApi = {
  // Get all notes for the current user
  getAllNotes: async () => {
    const response = await axios.get('/notes/');
    return response.data;
  },

  // Get notes by folder
  getNotesByFolder: async (folderId) => {
    const response = await axios.get(`/notes/?folder_id=${folderId}`);
    return response.data;
  },

  // Get a specific note
  getNote: async (noteId) => {
    const response = await axios.get(`/notes/${noteId}`);
    return response.data;
  },

  // Create a new note
  createNote: async (noteData) => {
    const response = await axios.post('/notes/', noteData);
    return response.data;
  },

  // Update a note
  updateNote: async (noteId, noteData) => {
    const response = await axios.put(`/notes/${noteId}`, noteData);
    return response.data;
  },

  // Delete a note
  deleteNote: async (noteId) => {
    const response = await axios.delete(`/notes/${noteId}`);
    return response.data;
  },

  // Search notes
  searchNotes: async (query) => {
    const response = await axios.get(`/notes/search?q=${encodeURIComponent(query)}`);
    return response.data;
  }
};

// Folders API
export const foldersApi = {
  // Get all folders for the current user
  getAllFolders: async () => {
    const response = await axios.get('/folders/');
    return response.data;
  },

  // Get a specific folder
  getFolder: async (folderId) => {
    const response = await axios.get(`/folders/${folderId}`);
    return response.data;
  },

  // Create a new folder
  createFolder: async (folderData) => {
    const response = await axios.post('/folders/', folderData);
    return response.data;
  },

  // Update a folder
  updateFolder: async (folderId, folderData) => {
    const response = await axios.put(`/folders/${folderId}`, folderData);
    return response.data;
  },

  // Delete a folder
  deleteFolder: async (folderId) => {
    const response = await axios.delete(`/folders/${folderId}`);
    return response.data;
  }
};

// Tags API
export const tagsApi = {
  // Get all tags for the current user
  getAllTags: async () => {
    const response = await axios.get('/tags/');
    return response.data;
  }
};