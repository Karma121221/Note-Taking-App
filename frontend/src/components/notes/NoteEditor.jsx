import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  TextField,
  Button,
  IconButton,
  Stack,
  Chip,
  Autocomplete,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Typography,
  Divider,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  Tabs,
  Tab,
  Grid
} from '@mui/material';
import {
  Save,
  Close,
  Add,
  Label,
  Folder,
  CheckBox,
  CheckBoxOutlineBlank,
  FormatBold,
  FormatItalic,
  FormatListBulleted,
  FormatListNumbered,
  Visibility,
  Edit,
  PlaylistAddCheck,
  Transform
} from '@mui/icons-material';
import { notesApi, foldersApi, tagsApi } from '../../services/api';
import InteractiveContent from './InteractiveContent';
import { useFolder } from '../../contexts/FolderContext';

const NoteEditor = ({ note, onSave, onClose, onFolderChange, open = false }) => {
  const [formData, setFormData] = useState({
    title: '',
    content: '',
    folder_id: '',
    tags: []
  });
  const [availableTags, setAvailableTags] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [createFolderDialogOpen, setCreateFolderDialogOpen] = useState(false);
  const [newFolderName, setNewFolderName] = useState('');
  const [editorTab, setEditorTab] = useState(0); // 0 = Edit, 1 = Preview

  const { folders, createFolder } = useFolder();

  useEffect(() => {
    loadInitialData();
  }, []);

  // Remove the old useEffect that was reloading on open
  // since we now use the global folder context

  useEffect(() => {
    if (note) {
      setFormData({
        title: note.title || '',
        content: note.content || '',
        folder_id: note.folder_id || '',
        tags: note.tags || []
      });
    } else {
      setFormData({
        title: '',
        content: '',
        folder_id: '',
        tags: []
      });
    }
  }, [note]);

  const loadInitialData = async () => {
    try {
      const tagsData = await tagsApi.getAllTags();
      setAvailableTags(tagsData);
    } catch (err) {
      console.error('Error loading initial data:', err);
    }
  };

  const handleChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleSave = async () => {
    if (!formData.title.trim()) {
      setError('Title is required');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const noteData = {
        title: formData.title.trim(),
        content: formData.content,
        folder_id: formData.folder_id || null,
        tags: formData.tags.map(tag => typeof tag === 'string' ? tag : tag.name || tag)
      };

      let savedNote;
      if (note?.id) {
        savedNote = await notesApi.updateNote(note.id, noteData);
      } else {
        savedNote = await notesApi.createNote(noteData);
      }

      onSave(savedNote);
    } catch (err) {
      setError('Failed to save note. Please try again.');
      console.error('Error saving note:', err);
    } finally {
      setLoading(false);
    }
  };

  const insertText = (before, after = '') => {
    const textarea = document.getElementById('note-content');
    if (!textarea) return;

    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const selectedText = formData.content.substring(start, end);
    
    const newText = formData.content.substring(0, start) + 
                   before + selectedText + after + 
                   formData.content.substring(end);
    
    handleChange('content', newText);
    
    // Restore cursor position
    setTimeout(() => {
      textarea.focus();
      textarea.setSelectionRange(start + before.length, end + before.length);
    }, 0);
  };

  const insertCheckbox = () => {
    insertText('- [ ] ');
  };

  const insertCheckboxList = () => {
    const checklistItems = [
      '- [ ] Task 1',
      '- [ ] Task 2', 
      '- [ ] Task 3'
    ];
    insertText(checklistItems.join('\n'));
  };

  const convertToChecklist = () => {
    const textarea = document.getElementById('note-content');
    if (!textarea) return;

    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const selectedText = formData.content.substring(start, end);
    
    if (selectedText) {
      // Convert selected lines to checklist
      const lines = selectedText.split('\n');
      const checklistLines = lines.map(line => {
        const trimmed = line.trim();
        if (trimmed && !trimmed.startsWith('-')) {
          return `- [ ] ${trimmed}`;
        } else if (trimmed.startsWith('- ') && !trimmed.includes('[ ]')) {
          return trimmed.replace('- ', '- [ ] ');
        }
        return line;
      });
      
      const newContent = formData.content.substring(0, start) + 
                        checklistLines.join('\n') + 
                        formData.content.substring(end);
      
      handleChange('content', newContent);
    } else {
      // If no selection, insert a single checkbox
      insertCheckbox();
    }
  };

  const insertBulletPoint = () => {
    insertText('- ');
  };

  const insertNumberedItem = () => {
    const lines = formData.content.split('\n');
    const currentLineIndex = document.getElementById('note-content')?.selectionStart || 0;
    const textBeforeCursor = formData.content.substring(0, currentLineIndex);
    const lineNumber = textBeforeCursor.split('\n').length;
    insertText(`${lineNumber}. `);
  };

  const formatSelection = (format) => {
    switch (format) {
      case 'bold':
        insertText('**', '**');
        break;
      case 'italic':
        insertText('*', '*');
        break;
      default:
        break;
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      const textarea = e.target;
      const cursorPosition = textarea.selectionStart;
      const textBeforeCursor = formData.content.substring(0, cursorPosition);
      const currentLine = textBeforeCursor.split('\n').pop();
      
      // Auto-continue checklist items
      if (currentLine.match(/^\s*-\s*\[\s*\]\s*$/)) {
        // Empty checkbox line - remove it
        e.preventDefault();
        const lines = formData.content.split('\n');
        const lineIndex = textBeforeCursor.split('\n').length - 1;
        lines[lineIndex] = '';
        handleChange('content', lines.join('\n'));
        
        // Move cursor to end of the now-empty line
        setTimeout(() => {
          const newCursorPos = cursorPosition - currentLine.length;
          textarea.setSelectionRange(newCursorPos, newCursorPos);
        }, 0);
      } else if (currentLine.match(/^\s*-\s*\[([ x])\]\s*.+/)) {
        // Checkbox with content - add new checkbox
        e.preventDefault();
        const indent = currentLine.match(/^(\s*)/)[1];
        const newLine = `\n${indent}- [ ] `;
        const newContent = formData.content.substring(0, cursorPosition) + 
                          newLine + 
                          formData.content.substring(cursorPosition);
        handleChange('content', newContent);
        
        // Move cursor to end of new checkbox
        setTimeout(() => {
          textarea.setSelectionRange(cursorPosition + newLine.length, cursorPosition + newLine.length);
        }, 0);
      } else if (currentLine.match(/^\s*-\s*.+/)) {
        // Regular bullet point - add new bullet
        e.preventDefault();
        const indent = currentLine.match(/^(\s*)/)[1];
        const newLine = `\n${indent}- `;
        const newContent = formData.content.substring(0, cursorPosition) + 
                          newLine + 
                          formData.content.substring(cursorPosition);
        handleChange('content', newContent);
        
        // Move cursor to end of new bullet
        setTimeout(() => {
          textarea.setSelectionRange(cursorPosition + newLine.length, cursorPosition + newLine.length);
        }, 0);
      }
    }
  };

  const handleTagChange = (event, newTags) => {
    handleChange('tags', newTags);
  };

  const handleCreateFolder = async () => {
    if (!newFolderName.trim()) return;

    try {
      const newFolder = await createFolder({
        name: newFolderName.trim(),
        description: ''
      });
      setFormData(prev => ({ ...prev, folder_id: newFolder.id }));
      setCreateFolderDialogOpen(false);
      setNewFolderName('');
      
      // Show success message
      setError(null);
      
      // Notify parent component about folder change
      if (onFolderChange) {
        onFolderChange();
      }
    } catch (err) {
      setError('Failed to create folder.');
      console.error('Error creating folder:', err);
    }
  };

  const handleFolderChange = (value) => {
    if (value === 'CREATE_NEW') {
      setCreateFolderDialogOpen(true);
    } else {
      handleChange('folder_id', value);
    }
  };

  if (!open) return null;

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        <Stack direction="row" alignItems="center" justifyContent="space-between">
          <Typography variant="h6">
            {note?.id ? 'Edit Note' : 'Create New Note'}
          </Typography>
          <IconButton onClick={onClose}>
            <Close />
          </IconButton>
        </Stack>
      </DialogTitle>

      <DialogContent>
        <Stack spacing={3} sx={{ mt: 1 }}>
          {error && (
            <Alert severity="error" onClose={() => setError(null)}>
              {error}
            </Alert>
          )}

          {/* Title */}
          <TextField
            fullWidth
            label="Title"
            value={formData.title}
            onChange={(e) => handleChange('title', e.target.value)}
            required
            autoFocus
          />

          {/* Folder selection */}
          <FormControl fullWidth>
            <InputLabel>Folder</InputLabel>
            <Select
              value={formData.folder_id}
              onChange={(e) => handleFolderChange(e.target.value)}
              label="Folder"
              startAdornment={<Folder sx={{ mr: 1, color: 'action.active' }} />}
            >
              <MenuItem value="">
                <em>No folder</em>
              </MenuItem>
              {folders.map((folder) => (
                <MenuItem key={folder.id} value={folder.id}>
                  {folder.name}
                </MenuItem>
              ))}
              <Divider />
              <MenuItem value="CREATE_NEW" sx={{ color: 'primary.main', fontWeight: 500 }}>
                <Add sx={{ mr: 1, fontSize: '1rem' }} />
                Create New Folder
              </MenuItem>
            </Select>
          </FormControl>

          {/* Tags */}
          <Autocomplete
            multiple
            freeSolo
            options={availableTags}
            getOptionLabel={(option) => typeof option === 'string' ? option : option.name}
            value={formData.tags}
            onChange={handleTagChange}
            renderTags={(tagValue, getTagProps) =>
              tagValue.map((option, index) => (
                <Chip
                  label={typeof option === 'string' ? option : option.name}
                  {...getTagProps({ index })}
                  key={index}
                  size="small"
                />
              ))
            }
            renderInput={(params) => (
              <TextField
                {...params}
                label="Tags"
                placeholder="Add tags..."
                helperText="Press Enter to add new tags"
              />
            )}
          />

          {/* Content editor with tabs */}
          <Box>
            <Tabs 
              value={editorTab} 
              onChange={(e, newValue) => setEditorTab(newValue)}
              sx={{ mb: 2 }}
            >
              <Tab icon={<Edit />} label="Edit" />
              <Tab icon={<Visibility />} label="Preview" />
            </Tabs>

            {editorTab === 0 ? (
              <Box>
                {/* Content editor toolbar */}
                <Paper variant="outlined" sx={{ p: 1, mb: 2 }}>
                  <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap">
                    <IconButton size="small" onClick={() => formatSelection('bold')} title="Bold">
                      <FormatBold fontSize="small" />
                    </IconButton>
                    <IconButton size="small" onClick={() => formatSelection('italic')} title="Italic">
                      <FormatItalic fontSize="small" />
                    </IconButton>
                    <Divider orientation="vertical" flexItem />
                    <IconButton size="small" onClick={insertBulletPoint} title="Bullet List">
                      <FormatListBulleted fontSize="small" />
                    </IconButton>
                    <IconButton size="small" onClick={insertNumberedItem} title="Numbered List">
                      <FormatListNumbered fontSize="small" />
                    </IconButton>
                    <Divider orientation="vertical" flexItem />
                    <IconButton size="small" onClick={insertCheckbox} title="Add Checkbox">
                      <CheckBox fontSize="small" />
                    </IconButton>
                    <IconButton size="small" onClick={insertCheckboxList} title="Add Checklist (3 items)">
                      <PlaylistAddCheck fontSize="small" />
                    </IconButton>
                    <IconButton size="small" onClick={convertToChecklist} title="Convert Selection to Checklist">
                      <Transform fontSize="small" />
                    </IconButton>
                  </Stack>
                  <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                    Tip: Press Enter after a checkbox to automatically add the next one
                  </Typography>
                </Paper>

                <TextField
                  id="note-content"
                  fullWidth
                  multiline
                  rows={12}
                  label="Content"
                  value={formData.content}
                  onChange={(e) => handleChange('content', e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Start typing your note... Use the toolbar above for formatting."
                  helperText="Supports markdown-style formatting. Use - [ ] for checkboxes, - for bullets, **bold**, *italic*. Press Enter after checkboxes to auto-continue!"
                />
              </Box>
            ) : (
              <Paper 
                variant="outlined" 
                sx={{ 
                  p: 3, 
                  minHeight: 400,
                  maxHeight: 400,
                  overflow: 'auto',
                  bgcolor: 'background.default'
                }}
              >
                {formData.content ? (
                  <InteractiveContent
                    content={formData.content}
                    readOnly={true}
                  />
                ) : (
                  <Typography color="text.secondary" fontStyle="italic">
                    Nothing to preview yet. Start typing in the Edit tab to see the preview.
                  </Typography>
                )}
              </Paper>
            )}
          </Box>
        </Stack>
      </DialogContent>

      <DialogActions sx={{ px: 3, pb: 2 }}>
        <Button onClick={onClose} variant="outlined">
          Cancel
        </Button>
        <Button
          onClick={handleSave}
          variant="contained"
          loading={loading}
          startIcon={<Save />}
          disabled={!formData.title.trim()}
        >
          {note?.id ? 'Update' : 'Create'} Note
        </Button>
      </DialogActions>

      {/* Create Folder Dialog */}
      <Dialog 
        open={createFolderDialogOpen} 
        onClose={() => {
          setCreateFolderDialogOpen(false);
          setNewFolderName('');
        }}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Create New Folder</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            fullWidth
            label="Folder Name"
            value={newFolderName}
            onChange={(e) => setNewFolderName(e.target.value)}
            onKeyPress={(e) => {
              if (e.key === 'Enter') {
                handleCreateFolder();
              }
            }}
            sx={{ mt: 1 }}
            placeholder="Enter folder name..."
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => {
            setCreateFolderDialogOpen(false);
            setNewFolderName('');
          }}>
            Cancel
          </Button>
          <Button 
            onClick={handleCreateFolder}
            variant="contained"
            disabled={!newFolderName.trim()}
            startIcon={<Add />}
          >
            Create Folder
          </Button>
        </DialogActions>
      </Dialog>
    </Dialog>
  );
};

export default NoteEditor;