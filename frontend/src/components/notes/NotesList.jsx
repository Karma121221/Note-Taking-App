import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  IconButton,
  Menu,
  MenuItem,
  Chip,
  Stack,
  Button,
  TextField,
  InputAdornment,
  Grid,
  Alert,
  Skeleton
} from '@mui/material';
import {
  MoreVert,
  Edit,
  Delete,
  Share,
  Add,
  Search,
  Folder,
  FolderOpen,
  Note,
  CheckBox,
  CheckBoxOutlineBlank
} from '@mui/icons-material';
import { notesApi, foldersApi } from '../../services/api';
import { useAuth } from '../../contexts/AuthContext';
import InteractiveContent from './InteractiveContent';

const NotesList = ({ selectedFolder, onNoteSelect, onCreateNote, refreshTrigger }) => {
  const [notes, setNotes] = useState([]);
  const [folders, setFolders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [anchorEl, setAnchorEl] = useState(null);
  const [selectedNote, setSelectedNote] = useState(null);
  
  const { user } = useAuth();

  useEffect(() => {
    loadNotesAndFolders();
  }, [selectedFolder, refreshTrigger]);

  const loadNotesAndFolders = async () => {
    try {
      setLoading(true);
      const [notesData, foldersData] = await Promise.all([
        selectedFolder ? notesApi.getNotesByFolder(selectedFolder) : notesApi.getAllNotes(),
        foldersApi.getAllFolders()
      ]);
      setNotes(notesData);
      setFolders(foldersData);
    } catch (err) {
      setError('Failed to load notes. Please try again.');
      console.error('Error loading notes:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleMenuOpen = (event, note) => {
    setAnchorEl(event.currentTarget);
    setSelectedNote(note);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
    setSelectedNote(null);
  };

  const handleDeleteNote = async () => {
    if (!selectedNote) return;
    
    try {
      await notesApi.deleteNote(selectedNote.id);
      setNotes(notes.filter(note => note.id !== selectedNote.id));
      handleMenuClose();
    } catch (err) {
      setError('Failed to delete note.');
      console.error('Error deleting note:', err);
    }
  };

  const handleEditNote = () => {
    if (selectedNote && onNoteSelect) {
      onNoteSelect(selectedNote);
    }
    handleMenuClose();
  };

  const handleContentChange = async (noteId, newContent) => {
    try {
      const updatedNote = await notesApi.updateNote(noteId, { content: newContent });
      setNotes(notes.map(note => note.id === noteId ? { ...note, content: newContent } : note));
    } catch (err) {
      setError('Failed to update note.');
      console.error('Error updating note:', err);
    }
  };

  const filteredNotes = notes.filter(note =>
    note.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    note.content.toLowerCase().includes(searchQuery.toLowerCase()) ||
    note.tags?.some(tag => tag.name.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  const getFolderName = (folderId) => {
    const folder = folders.find(f => f.id === folderId);
    return folder ? folder.name : 'Unfiled';
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getChecklistProgress = (content) => {
    const checkboxMatches = content.match(/- \[([ x])\]/g);
    if (!checkboxMatches) return null;
    
    const total = checkboxMatches.length;
    const completed = checkboxMatches.filter(match => match.includes('[x]')).length;
    return { completed, total };
  };

  if (loading) {
    return (
      <Box sx={{ p: 3 }}>
        <Grid container spacing={2}>
          {[...Array(6)].map((_, index) => (
            <Grid key={index} xs={12} sm={6} md={4}>
              <Card>
                <CardContent>
                  <Skeleton variant="text" width="80%" height={32} />
                  <Skeleton variant="text" width="100%" height={20} sx={{ mt: 1 }} />
                  <Skeleton variant="text" width="60%" height={20} />
                  <Stack direction="row" spacing={1} sx={{ mt: 2 }}>
                    <Skeleton variant="rounded" width={60} height={24} />
                    <Skeleton variant="rounded" width={80} height={24} />
                  </Stack>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Box>
    );
  }

  return (
    <Box sx={{ p: { xs: 2, sm: 3 }, width: '100%', maxWidth: '100%' }}>
      {/* Header with search and create button */}
      <Stack 
        direction={{ xs: 'column', sm: 'row' }} 
        spacing={2} 
        alignItems={{ xs: 'stretch', sm: 'center' }} 
        sx={{ mb: 3 }}
      >
        <TextField
          fullWidth
          placeholder="Search notes..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          sx={{ flex: 1 }}
          slotProps={{
            input: {
              startAdornment: (
                <InputAdornment position="start">
                  <Search color="action" />
                </InputAdornment>
              ),
            },
          }}
        />
        {/* Only show create button for children */}
        {user?.role === 'child' && (
          <Button
            variant="contained"
            startIcon={<Add />}
            onClick={onCreateNote}
            sx={{ 
              whiteSpace: 'nowrap',
              minWidth: { xs: '100%', sm: 'auto' },
              py: 1.5,
              px: 3,
              fontSize: '0.95rem',
              fontWeight: 500,
              flex: { xs: 1, sm: 'none' }
            }}
          >
            New Note
          </Button>
        )}
      </Stack>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Notes grid */}
      {filteredNotes.length === 0 ? (
        <Box
          sx={{
            textAlign: 'center',
            py: 8,
            color: 'text.secondary'
          }}
        >
          <Note sx={{ fontSize: 48, mb: 2, opacity: 0.5 }} />
          <Typography variant="h6" gutterBottom>
            {searchQuery ? 'No notes found' : 'No notes yet'}
          </Typography>
          <Typography variant="body2">
            {searchQuery 
              ? 'Try adjusting your search terms'
              : user?.role === 'child' 
                ? 'Create your first note to get started!'
                : 'No notes to display in this view'
            }
          </Typography>
          {!searchQuery && user?.role === 'child' && (
            <Button
              variant="outlined"
              startIcon={<Add />}
              onClick={onCreateNote}
              sx={{ mt: 2 }}
            >
              Create Note
            </Button>
          )}
        </Box>
      ) : (
        <Grid container spacing={2}>
          {filteredNotes.map((note) => {
            const checklistProgress = getChecklistProgress(note.content);
            
            return (
              <Grid key={note.id} xs={12} sm={6} md={4} lg={3}>
                <Card
                  sx={{
                    height: '100%',
                    cursor: 'pointer',
                    transition: 'all 0.2s ease-in-out',
                    border: user?.role === 'parent' ? '1px solid' : 'inherit',
                    borderColor: user?.role === 'parent' ? 'info.light' : 'inherit',
                    '&:hover': {
                      transform: user?.role === 'parent' ? 'none' : 'translateY(-2px)',
                      boxShadow: user?.role === 'parent' ? '0 2px 8px rgba(0,0,0,0.1)' : '0 4px 12px rgba(0,0,0,0.15)',
                      borderColor: user?.role === 'parent' ? 'info.main' : 'inherit'
                    }
                  }}
                  onClick={() => {
                    if (onNoteSelect) {
                      onNoteSelect(note);
                    }
                  }}
                >
                  <CardContent sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                    {/* Note header */}
                    <Stack direction="row" alignItems="flex-start" spacing={1} sx={{ mb: 2 }}>
                      <Box sx={{ flexGrow: 1, minWidth: 0 }}>
                        <Typography
                          variant="h6"
                          component="h3"
                          sx={{
                            fontWeight: 600,
                            fontSize: '1.1rem',
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            whiteSpace: 'nowrap'
                          }}
                        >
                          {note.title}
                        </Typography>
                        {/* Show owner name for parents */}
                        {user?.role === 'parent' && note.owner_name && (
                          <Typography
                            variant="caption"
                            color="primary"
                            sx={{
                              fontWeight: 500,
                              fontSize: '0.7rem',
                              display: 'block',
                              mt: 0.5
                            }}
                          >
                            by {note.owner_name}
                          </Typography>
                        )}
                        {/* Read-only indicator for parents */}
                        {user?.role === 'parent' && (
                          <Typography
                            variant="caption"
                            color="info.main"
                            sx={{
                              fontWeight: 500,
                              fontSize: '0.65rem',
                              display: 'block',
                              mt: 0.5,
                              fontStyle: 'italic'
                            }}
                          >
                            Click to view (read-only)
                          </Typography>
                        )}
                      </Box>
                      
                      {user?.role === 'child' && (
                        <IconButton
                          size="small"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleMenuOpen(e, note);
                          }}
                        >
                          <MoreVert fontSize="small" />
                        </IconButton>
                      )}
                    </Stack>

                    {/* Note content preview */}
                    <Box sx={{ flexGrow: 1, mb: 2 }}>
                      <InteractiveContent
                        content={note.content}
                        onContentChange={(newContent) => handleContentChange(note.id, newContent)}
                        readOnly={user?.role !== 'child'}
                        maxLines={3}
                      />
                    </Box>

                    {/* Checklist progress */}
                    {checklistProgress && (
                      <Stack direction="row" alignItems="center" spacing={1} sx={{ mb: 2 }}>
                        {checklistProgress.completed === checklistProgress.total ? (
                          <CheckBox color="success" fontSize="small" />
                        ) : (
                          <CheckBoxOutlineBlank color="action" fontSize="small" />
                        )}
                        <Typography variant="caption" color="text.secondary">
                          {checklistProgress.completed}/{checklistProgress.total} completed
                        </Typography>
                      </Stack>
                    )}

                    {/* Tags */}
                    {note.tags && note.tags.length > 0 && (
                      <Stack direction="row" spacing={0.5} sx={{ flexWrap: 'wrap', gap: 0.5, mb: 2 }}>
                        {note.tags.slice(0, 3).map((tag) => (
                          <Chip
                            key={tag.id}
                            label={tag.name}
                            size="small"
                            variant="outlined"
                            sx={{ fontSize: '0.75rem' }}
                          />
                        ))}
                        {note.tags.length > 3 && (
                          <Chip
                            label={`+${note.tags.length - 3}`}
                            size="small"
                            variant="outlined"
                            sx={{ fontSize: '0.75rem' }}
                          />
                        )}
                      </Stack>
                    )}

                    {/* Note footer */}
                    <Stack direction="row" justifyContent="space-between" alignItems="center">
                      <Stack direction="row" alignItems="center" spacing={0.5}>
                        {note.folder_id ? <Folder fontSize="small" /> : <FolderOpen fontSize="small" />}
                        <Typography variant="caption" color="text.secondary">
                          {getFolderName(note.folder_id)}
                        </Typography>
                      </Stack>
                      <Typography variant="caption" color="text.secondary">
                        {formatDate(note.updated_at)}
                      </Typography>
                    </Stack>
                  </CardContent>
                </Card>
              </Grid>
            );
          })}
        </Grid>
      )}

      {/* Context menu */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
        onClick={(e) => e.stopPropagation()}
      >
        <MenuItem onClick={handleEditNote}>
          <Edit fontSize="small" sx={{ mr: 1 }} />
          Edit
        </MenuItem>
        <MenuItem onClick={() => handleMenuClose()}>
          <Share fontSize="small" sx={{ mr: 1 }} />
          Share
        </MenuItem>
        <MenuItem onClick={handleDeleteNote} sx={{ color: 'error.main' }}>
          <Delete fontSize="small" sx={{ mr: 1 }} />
          Delete
        </MenuItem>
      </Menu>
    </Box>
  );
};

export default NotesList;