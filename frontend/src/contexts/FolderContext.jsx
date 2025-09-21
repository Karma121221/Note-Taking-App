import React, { createContext, useContext, useState, useEffect } from 'react';
import { foldersApi } from '../services/api';

const FolderContext = createContext();

export const useFolder = () => {
  const context = useContext(FolderContext);
  if (!context) {
    throw new Error('useFolder must be used within a FolderProvider');
  }
  return context;
};

export const FolderProvider = ({ children }) => {
  const [folders, setFolders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Load folders on mount
  useEffect(() => {
    loadFolders();
  }, []);

  const loadFolders = async () => {
    try {
      setLoading(true);
      setError(null);
      const foldersData = await foldersApi.getAllFolders();
      setFolders(foldersData);
    } catch (err) {
      setError('Failed to load folders');
      console.error('Error loading folders:', err);
    } finally {
      setLoading(false);
    }
  };

  const createFolder = async (folderData) => {
    try {
      const newFolder = await foldersApi.createFolder(folderData);
      setFolders(prev => [...prev, newFolder]);
      return newFolder;
    } catch (err) {
      setError('Failed to create folder');
      console.error('Error creating folder:', err);
      throw err;
    }
  };

  const updateFolder = async (folderId, folderData) => {
    try {
      const updatedFolder = await foldersApi.updateFolder(folderId, folderData);
      setFolders(prev => prev.map(folder => 
        folder.id === folderId ? updatedFolder : folder
      ));
      return updatedFolder;
    } catch (err) {
      setError('Failed to update folder');
      console.error('Error updating folder:', err);
      throw err;
    }
  };

  const deleteFolder = async (folderId) => {
    try {
      await foldersApi.deleteFolder(folderId);
      setFolders(prev => prev.filter(folder => folder.id !== folderId));
    } catch (err) {
      setError('Failed to delete folder');
      console.error('Error deleting folder:', err);
      throw err;
    }
  };

  const refreshFolders = () => {
    loadFolders();
  };

  const value = {
    folders,
    loading,
    error,
    createFolder,
    updateFolder,
    deleteFolder,
    refreshFolders,
    setError
  };

  return (
    <FolderContext.Provider value={value}>
      {children}
    </FolderContext.Provider>
  );
};

export default FolderContext;