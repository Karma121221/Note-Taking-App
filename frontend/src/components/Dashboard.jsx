import React, { useState } from 'react';
import {
  Box,
  AppBar,
  Toolbar,
  Typography,
  IconButton,
  Avatar,
  Menu,
  MenuItem,
  Divider,
  useMediaQuery
} from '@mui/material';
import {
  Brightness4,
  Brightness7,
  Logout,
  Settings,
  MenuOpen,
  FamilyRestroom
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';
import { useCustomTheme } from '../contexts/ThemeContext';
import { useTheme } from '@mui/material/styles';
import { useNavigate } from 'react-router-dom';
import Sidebar from './folders/Sidebar';
import NotesList from './notes/NotesList';
import NoteEditor from './notes/NoteEditor';
import ReadOnlyNoteViewer from './notes/ReadOnlyNoteViewer';

const Dashboard = () => {
  const { user, logout } = useAuth();
  const { mode, toggleColorMode } = useCustomTheme();
  const theme = useTheme();
  const navigate = useNavigate();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  
  const [anchorEl, setAnchorEl] = React.useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [selectedFolder, setSelectedFolder] = useState(null);
  const [selectedNote, setSelectedNote] = useState(null);
  const [editorOpen, setEditorOpen] = useState(false);
  const [viewerOpen, setViewerOpen] = useState(false); // For parent read-only view
  const [refreshNotes, setRefreshNotes] = useState(0);
  const [refreshFolders, setRefreshFolders] = useState(0);

  const handleMenuOpen = (event) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleLogout = () => {
    logout();
    handleMenuClose();
  };

  const handleFolderSelect = (folderId) => {
    setSelectedFolder(folderId);
    if (isMobile) {
      setSidebarOpen(false);
    }
  };

  const handleNoteSelect = (note) => {
    setSelectedNote(note);
    if (user?.role === 'parent') {
      // Parents get read-only view
      setViewerOpen(true);
    } else {
      // Children get edit access
      setEditorOpen(true);
    }
  };

  const handleCreateNote = () => {
    // Only children can create notes
    if (user?.role === 'child') {
      setSelectedNote(null);
      setEditorOpen(true);
    }
  };

  const handleNoteSave = (note) => {
    setEditorOpen(false);
    setSelectedNote(null);
    // Trigger refresh of notes list
    setRefreshNotes(prev => prev + 1);
  };

  const handleFolderChange = () => {
    // Trigger refresh of folders in sidebar
    setRefreshFolders(prev => prev + 1);
  };

  const handleEditorClose = () => {
    setEditorOpen(false);
    setSelectedNote(null);
  };

  const handleViewerClose = () => {
    setViewerOpen(false);
    setSelectedNote(null);
  };

  return (
    <Box sx={{ display: 'flex', height: '100vh', width: '100vw', overflow: 'hidden' }}>
      {/* Sidebar */}
      <Sidebar
        selectedFolder={selectedFolder}
        onFolderSelect={handleFolderSelect}
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        refreshTrigger={refreshFolders}
      />

      {/* Main content */}
      <Box sx={{ 
        flexGrow: 1, 
        display: 'flex', 
        flexDirection: 'column', 
        width: '100%', 
        maxWidth: '100%',
        overflow: 'hidden' 
      }}>
        {/* Header */}
        <AppBar 
          position="static" 
          elevation={0}
          sx={{ 
            borderBottom: '1px solid',
            borderColor: 'divider',
            bgcolor: 'background.paper',
            width: '100%'
          }}
        >
          <Toolbar sx={{ width: '100%', maxWidth: '100%' }}>
            {isMobile && (
              <IconButton
                edge="start"
                onClick={() => setSidebarOpen(true)}
                sx={{ mr: 2, color: 'text.primary' }}
              >
                <MenuOpen />
              </IconButton>
            )}

            <Typography 
              variant="h6" 
              component="div" 
              sx={{ 
                flexGrow: 1,
                color: 'text.primary',
                fontWeight: 600
              }}
            >
              {user?.role === 'parent' 
                ? (selectedFolder ? "Children's Notes in Folder" : "Children's Notes (Read-Only)")
                : (selectedFolder ? 'Folder Notes' : 'All Notes')
              }
            </Typography>

            <IconButton
              onClick={toggleColorMode}
              color="inherit"
              sx={{ mr: 1, color: 'text.primary' }}
            >
              {mode === 'dark' ? <Brightness7 /> : <Brightness4 />}
            </IconButton>

            <IconButton
              onClick={handleMenuOpen}
              sx={{ color: 'text.primary' }}
            >
              <Avatar sx={{ width: 32, height: 32, bgcolor: 'primary.main' }}>
                {user?.name?.charAt(0).toUpperCase() || 'U'}
              </Avatar>
            </IconButton>

            <Menu
              anchorEl={anchorEl}
              open={Boolean(anchorEl)}
              onClose={handleMenuClose}
              anchorOrigin={{
                vertical: 'bottom',
                horizontal: 'right',
              }}
              transformOrigin={{
                vertical: 'top',
                horizontal: 'right',
              }}
            >
              <MenuItem disabled>
                <Box>
                  <Typography variant="body2" fontWeight={500}>
                    {user?.name}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {user?.role?.charAt(0).toUpperCase() + user?.role?.slice(1)} Account
                  </Typography>
                </Box>
              </MenuItem>
              <Divider />
              <MenuItem onClick={() => { handleMenuClose(); navigate('/family'); }}>
                <FamilyRestroom sx={{ mr: 1 }} fontSize="small" />
                Family Management
              </MenuItem>
              <MenuItem onClick={handleMenuClose}>
                <Settings sx={{ mr: 1 }} fontSize="small" />
                Settings
              </MenuItem>
              <MenuItem onClick={handleLogout}>
                <Logout sx={{ mr: 1 }} fontSize="small" />
                Sign Out
              </MenuItem>
            </Menu>
          </Toolbar>
        </AppBar>

        {/* Notes content */}
        <Box sx={{ 
          flexGrow: 1, 
          overflow: 'auto', 
          width: '100%', 
          maxWidth: '100%',
          height: '100%'
        }}>
          <NotesList
            selectedFolder={selectedFolder}
            onNoteSelect={handleNoteSelect}
            onCreateNote={handleCreateNote}
            refreshTrigger={refreshNotes}
          />
        </Box>
      </Box>

      {/* Note Editor Dialog - Only for children */}
      {user?.role === 'child' && (
        <NoteEditor
          note={selectedNote}
          open={editorOpen}
          onSave={handleNoteSave}
          onClose={handleEditorClose}
          onFolderChange={handleFolderChange}
        />
      )}

      {/* Read-only Note Viewer - Only for parents */}
      {user?.role === 'parent' && (
        <ReadOnlyNoteViewer
          note={selectedNote}
          open={viewerOpen}
          onClose={handleViewerClose}
        />
      )}
    </Box>
  );
};

export default Dashboard;