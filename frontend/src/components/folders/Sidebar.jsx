import React, { useState, useEffect } from 'react';
import {
  Box,
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  IconButton,
  Typography,
  Divider,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Menu,
  MenuItem,
  Stack,
  Chip
} from '@mui/material';
import {
  Folder,
  FolderOpen,
  Add,
  MoreVert,
  Edit,
  Delete,
  Note,
  Label,
  AllInclusive
} from '@mui/icons-material';
import { foldersApi, tagsApi } from '../../services/api';
import { useAuth } from '../../contexts/AuthContext';
import { useFolder } from '../../contexts/FolderContext';

const DRAWER_WIDTH = 280;

const Sidebar = ({ selectedFolder, onFolderSelect, open, onClose, refreshTrigger }) => {
  const [tags, setTags] = useState([]);
  const [loading, setLoading] = useState(true);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [editingFolder, setEditingFolder] = useState(null);
  const [folderName, setFolderName] = useState('');
  const [menuAnchor, setMenuAnchor] = useState(null);
  const [selectedFolderForMenu, setSelectedFolderForMenu] = useState(null);
  
  const { user } = useAuth();
  const { folders, createFolder, updateFolder, deleteFolder } = useFolder();

  useEffect(() => {
    loadTags();
  }, [refreshTrigger]);

  const loadTags = async () => {
    try {
      setLoading(true);
      const tagsData = await tagsApi.getAllTags();
      setTags(tagsData);
    } catch (err) {
      console.error('Error loading tags:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateFolder = async () => {
    if (!folderName.trim()) return;

    try {
      await createFolder({
        name: folderName.trim(),
        description: ''
      });
      setCreateDialogOpen(false);
      setFolderName('');
    } catch (err) {
      console.error('Error creating folder:', err);
    }
  };

  const handleUpdateFolder = async () => {
    if (!folderName.trim() || !editingFolder) return;

    try {
      await updateFolder(editingFolder.id, {
        name: folderName.trim(),
        description: editingFolder.description
      });
      setEditingFolder(null);
      setFolderName('');
    } catch (err) {
      console.error('Error updating folder:', err);
    }
  };

  const handleDeleteFolder = async (folder) => {
    try {
      await deleteFolder(folder.id);
      if (selectedFolder === folder.id) {
        onFolderSelect(null);
      }
      handleMenuClose();
    } catch (err) {
      console.error('Error deleting folder:', err);
    }
  };

  const handleMenuOpen = (event, folder) => {
    event.stopPropagation();
    setMenuAnchor(event.currentTarget);
    setSelectedFolderForMenu(folder);
  };

  const handleMenuClose = () => {
    setMenuAnchor(null);
    setSelectedFolderForMenu(null);
  };

  const handleEditFolder = () => {
    setEditingFolder(selectedFolderForMenu);
    setFolderName(selectedFolderForMenu.name);
    handleMenuClose();
  };

  const sidebarContent = (
    <Box sx={{ width: DRAWER_WIDTH, height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <Box sx={{ p: 2, borderBottom: '1px solid', borderColor: 'divider' }}>
        <Typography variant="h6" fontWeight={600}>
          My Notes
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {user?.username}
        </Typography>
      </Box>

      <Box sx={{ flexGrow: 1, overflow: 'auto' }}>
        {/* All Notes */}
        <List sx={{ py: 0 }}>
          <ListItemButton
            selected={selectedFolder === null}
            onClick={() => onFolderSelect(null)}
            sx={{
              py: 1.5,
              '&.Mui-selected': {
                bgcolor: 'primary.50',
                borderRight: '3px solid',
                borderColor: 'primary.main',
                '& .MuiListItemIcon-root': {
                  color: 'primary.main'
                },
                '& .MuiListItemText-primary': {
                  fontWeight: 600,
                  color: 'primary.main'
                }
              }
            }}
          >
            <ListItemIcon>
              <AllInclusive />
            </ListItemIcon>
            <ListItemText 
              primary="All Notes" 
              primaryTypographyProps={{ fontWeight: selectedFolder === null ? 600 : 400 }}
            />
          </ListItemButton>
        </List>

        <Divider />

        {/* Folders Section */}
        <Box sx={{ p: 2, pb: 1 }}>
          <Stack direction="row" alignItems="center" justifyContent="space-between">
            <Typography variant="subtitle2" fontWeight={600} color="text.secondary">
              {user?.role === 'parent' ? "CHILDREN'S FOLDERS" : "FOLDERS"}
            </Typography>
            {user?.role === 'child' && (
              <IconButton
                size="small"
                onClick={() => setCreateDialogOpen(true)}
                sx={{ color: 'text.secondary' }}
              >
                <Add fontSize="small" />
              </IconButton>
            )}
          </Stack>
          {user?.role === 'parent' && (
            <Typography variant="caption" color="info.main" sx={{ fontStyle: 'italic', fontSize: '0.7rem' }}>
              Read-only view
            </Typography>
          )}
        </Box>

        <List sx={{ py: 0, px: 1 }}>
          {folders.map((folder) => (
            <ListItem key={folder.id} disablePadding>
              <ListItemButton
                selected={selectedFolder === folder.id}
                onClick={() => onFolderSelect(folder.id)}
                sx={{
                  borderRadius: 1,
                  mx: 1,
                  '&.Mui-selected': {
                    bgcolor: 'primary.50',
                    '& .MuiListItemIcon-root': {
                      color: 'primary.main'
                    },
                    '& .MuiListItemText-primary': {
                      fontWeight: 600,
                      color: 'primary.main'
                    }
                  }
                }}
              >
                <ListItemIcon>
                  {selectedFolder === folder.id ? <FolderOpen /> : <Folder />}
                </ListItemIcon>
                <ListItemText 
                  primary={folder.name}
                  secondary={user?.role === 'parent' && folder.owner_name ? `by ${folder.owner_name}` : null}
                  primaryTypographyProps={{ 
                    fontWeight: selectedFolder === folder.id ? 600 : 400,
                    noWrap: true
                  }}
                  secondaryTypographyProps={{
                    fontSize: '0.7rem',
                    color: 'primary.main',
                    fontWeight: 500,
                    noWrap: true
                  }}
                />
                {user?.role === 'child' && (
                  <IconButton
                    size="small"
                    onClick={(e) => handleMenuOpen(e, folder)}
                    sx={{ opacity: 0.7 }}
                  >
                    <MoreVert fontSize="small" />
                  </IconButton>
                )}
              </ListItemButton>
            </ListItem>
          ))}
        </List>

        <Divider sx={{ my: 2 }} />

        {/* Tags Section */}
        <Box sx={{ p: 2, pb: 1 }}>
          <Typography variant="subtitle2" fontWeight={600} color="text.secondary">
            TAGS
          </Typography>
        </Box>

        <Box sx={{ px: 2, pb: 2 }}>
          <Stack direction="row" spacing={0.5} sx={{ flexWrap: 'wrap', gap: 0.5 }}>
            {tags.slice(0, 10).map((tag) => (
              <Chip
                key={tag.id}
                label={tag.name}
                size="small"
                variant="outlined"
                icon={<Label />}
                onClick={() => {
                  // TODO: Filter by tag
                }}
                sx={{ fontSize: '0.75rem' }}
              />
            ))}
            {tags.length > 10 && (
              <Chip
                label={`+${tags.length - 10} more`}
                size="small"
                variant="outlined"
                sx={{ fontSize: '0.75rem' }}
              />
            )}
          </Stack>
        </Box>
      </Box>

      {/* Footer */}
      <Box sx={{ p: 2, borderTop: '1px solid', borderColor: 'divider' }}>
        <Stack direction="row" alignItems="center" spacing={1}>
          <Note color="action" fontSize="small" />
          <Typography variant="body2" color="text.secondary">
            {folders.length} folders • {tags.length} tags
          </Typography>
        </Stack>
      </Box>

      {/* Folder menu */}
      <Menu
        anchorEl={menuAnchor}
        open={Boolean(menuAnchor)}
        onClose={handleMenuClose}
      >
        <MenuItem onClick={handleEditFolder}>
          <Edit fontSize="small" sx={{ mr: 1 }} />
          Edit
        </MenuItem>
        <MenuItem 
          onClick={() => handleDeleteFolder(selectedFolderForMenu)}
          sx={{ color: 'error.main' }}
        >
          <Delete fontSize="small" sx={{ mr: 1 }} />
          Delete
        </MenuItem>
      </Menu>

      {/* Create/Edit folder dialog */}
      <Dialog 
        open={createDialogOpen || Boolean(editingFolder)} 
        onClose={() => {
          setCreateDialogOpen(false);
          setEditingFolder(null);
          setFolderName('');
        }}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          {editingFolder ? 'Edit Folder' : 'Create New Folder'}
        </DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            fullWidth
            label="Folder Name"
            value={folderName}
            onChange={(e) => setFolderName(e.target.value)}
            onKeyPress={(e) => {
              if (e.key === 'Enter') {
                editingFolder ? handleUpdateFolder() : handleCreateFolder();
              }
            }}
            sx={{ mt: 1 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => {
            setCreateDialogOpen(false);
            setEditingFolder(null);
            setFolderName('');
          }}>
            Cancel
          </Button>
          <Button 
            onClick={editingFolder ? handleUpdateFolder : handleCreateFolder}
            variant="contained"
            disabled={!folderName.trim()}
          >
            {editingFolder ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );

  return (
    <>
      {/* Desktop drawer */}
      <Drawer
        variant="permanent"
        sx={{
          display: { xs: 'none', md: 'block' },
          width: DRAWER_WIDTH,
          flexShrink: 0,
          '& .MuiDrawer-paper': {
            width: DRAWER_WIDTH,
            boxSizing: 'border-box',
            position: 'relative',
            height: '100%'
          },
        }}
      >
        {sidebarContent}
      </Drawer>

      {/* Mobile drawer */}
      <Drawer
        variant="temporary"
        open={open}
        onClose={onClose}
        sx={{
          display: { xs: 'block', md: 'none' },
          '& .MuiDrawer-paper': {
            width: DRAWER_WIDTH,
            boxSizing: 'border-box',
          },
        }}
      >
        {sidebarContent}
      </Drawer>
    </>
  );
};

export default Sidebar;