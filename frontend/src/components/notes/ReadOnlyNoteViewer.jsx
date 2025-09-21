import React from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Box,
  Chip,
  Stack,
  Divider,
  IconButton,
} from '@mui/material';
import {
  Close,
  Folder,
  FolderOpen,
  CheckBox,
  CheckBoxOutlineBlank,
  Person,
} from '@mui/icons-material';
import InteractiveContent from './InteractiveContent';

const ReadOnlyNoteViewer = ({ note, open, onClose }) => {
  if (!note) return null;

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

  const checklistProgress = getChecklistProgress(note.content);

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="md"
      fullWidth
      PaperProps={{
        sx: {
          maxHeight: '90vh',
          borderRadius: 2,
        }
      }}
    >
      <DialogTitle
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          pb: 1,
        }}
      >
        <Box sx={{ flexGrow: 1, minWidth: 0 }}>
          <Typography variant="h5" component="h2" sx={{ fontWeight: 600 }}>
            {note.title}
          </Typography>
          {note.owner_name && (
            <Stack direction="row" alignItems="center" spacing={0.5} sx={{ mt: 0.5 }}>
              <Person fontSize="small" color="primary" />
              <Typography variant="body2" color="primary" sx={{ fontWeight: 500 }}>
                Created by {note.owner_name}
              </Typography>
            </Stack>
          )}
        </Box>
        <IconButton onClick={onClose} sx={{ ml: 1 }}>
          <Close />
        </IconButton>
      </DialogTitle>

      <Divider />

      <DialogContent sx={{ py: 3 }}>
        <Stack spacing={3}>
          {/* Note metadata */}
          <Box>
            <Stack direction="row" spacing={2} flexWrap="wrap" alignItems="center">
              <Stack direction="row" alignItems="center" spacing={0.5}>
                {note.folder_id ? <Folder fontSize="small" /> : <FolderOpen fontSize="small" />}
                <Typography variant="body2" color="text.secondary">
                  {note.folder_id ? 'In folder' : 'Unfiled'}
                </Typography>
              </Stack>

              <Typography variant="body2" color="text.secondary">
                Created: {formatDate(note.created_at)}
              </Typography>

              <Typography variant="body2" color="text.secondary">
                Updated: {formatDate(note.updated_at)}
              </Typography>
            </Stack>
          </Box>

          {/* Checklist progress */}
          {checklistProgress && (
            <Box>
              <Stack direction="row" alignItems="center" spacing={1}>
                {checklistProgress.completed === checklistProgress.total ? (
                  <CheckBox color="success" />
                ) : (
                  <CheckBoxOutlineBlank color="action" />
                )}
                <Typography variant="body1" color="text.secondary">
                  Progress: {checklistProgress.completed}/{checklistProgress.total} completed
                  {checklistProgress.completed === checklistProgress.total && (
                    <Chip 
                      label="Complete" 
                      color="success" 
                      size="small" 
                      sx={{ ml: 1 }} 
                    />
                  )}
                </Typography>
              </Stack>
            </Box>
          )}

          {/* Tags */}
          {note.tags && note.tags.length > 0 && (
            <Box>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                Tags:
              </Typography>
              <Stack direction="row" spacing={0.5} sx={{ flexWrap: 'wrap', gap: 0.5 }}>
                {note.tags.map((tag) => (
                  <Chip
                    key={tag.id || tag}
                    label={tag.name || tag}
                    size="small"
                    variant="outlined"
                  />
                ))}
              </Stack>
            </Box>
          )}

          <Divider />

          {/* Note content */}
          <Box>
            <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>
              Content
            </Typography>
            <Box 
              sx={{ 
                border: '1px solid',
                borderColor: 'divider',
                borderRadius: 1,
                p: 2,
                backgroundColor: 'grey.50',
                maxHeight: '400px',
                overflow: 'auto',
              }}
            >
              <InteractiveContent
                content={note.content}
                readOnly={true}
                maxLines={null} // Show full content
              />
            </Box>
          </Box>
        </Stack>
      </DialogContent>

      <DialogActions sx={{ px: 3, pb: 3 }}>
        <Typography variant="body2" color="text.secondary" sx={{ flexGrow: 1 }}>
          Read-only view
        </Typography>
        <Button onClick={onClose} variant="contained">
          Close
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default ReadOnlyNoteViewer;