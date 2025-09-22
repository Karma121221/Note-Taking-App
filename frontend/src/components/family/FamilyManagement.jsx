import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  TextField,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Chip,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Grid,
  Paper,
  Divider,
  CircularProgress,
} from '@mui/material';
import {
  ContentCopy,
  Refresh,
  PersonRemove,
  Share,
  FamilyRestroom,
  Info,
} from '@mui/icons-material';
import { useAuth } from '../../contexts/AuthContext';
import { apiClient } from '../../services/api';

const FamilyManagement = () => {
  const { user } = useAuth();
  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [generateDialog, setGenerateDialog] = useState(false);
  const [expirationDays, setExpirationDays] = useState('');
  const [confirmDialog, setConfirmDialog] = useState({ open: false, childId: '', childName: '' });
  const [joinCode, setJoinCode] = useState('');
  const [joining, setJoining] = useState(false);
  const [parentInfo, setParentInfo] = useState(null);

  useEffect(() => {
    fetchData();
  }, [user]);

  const fetchData = async () => {
    try {
      setLoading(true);
      console.log('🔄 Fetching family data for user:', user?.email, 'Role:', user?.role);

      if (user?.role === 'parent') {
        console.log('👨‍👩‍👧‍👦 Parent user detected');

        // Always fetch fresh data from API to ensure we have the latest family code
        try {
          console.log('📡 Fetching family dashboard from API...');
          const response = await apiClient.get('/family/dashboard');
          console.log('📊 API dashboard response:', response.data);
          setDashboard(response.data);
        } catch (error) {
          console.error('❌ Error fetching family dashboard:', error);
          // Fallback to user object data if API fails
          console.log('📋 Using family data from user object as fallback:', {
            family_code: user.family_code,
            family_code_expires: user.family_code_expires,
            children_count: user.children?.length || 0
          });
          setDashboard({
            family_code: user.family_code || null,
            family_code_expires: user.family_code_expires || null,
            children: user.children || []
          });
        }
      } else if (user?.role === 'child') {
        console.log('👶 Child user detected, fetching parent info...');
        const response = await apiClient.get('/family/my-parent');
        console.log('👨‍👩‍👧‍👦 Parent info response:', response.data);
        setParentInfo(response.data);
      } else {
        console.warn('⚠️ Unknown user role:', user?.role);
      }
      console.log('✅ Family data fetch completed successfully');
    } catch (error) {
      console.error('❌ Error fetching family data:', error.response?.data || error.message);
      setError('Failed to load family information');
    } finally {
      setLoading(false);
    }
  };

  const generateFamilyCode = async () => {
    try {
      console.log('🔄 Generating family code...');
      const data = {};
      if (expirationDays) {
        const days = parseInt(expirationDays);
        if (days <= 0) {
          setError('Expiration days must be a positive number');
          return;
        }
        data.expires_in_days = days;
        console.log('📅 Setting expiration to', days, 'days');
      }

      console.log('📤 Sending generate-code request with data:', data);
      const response = await apiClient.post('/family/generate-code', data);
      console.log('✅ Generate code response:', response.data);

      const familyCode = response.data.family_code;
      const expiresAt = response.data.expires_at;

      if (familyCode) {
        setSuccess(`New family code generated successfully! Code: ${familyCode}`);

        // Update dashboard immediately with the generated code
        setDashboard(prevDashboard => ({
          ...prevDashboard,
          family_code: familyCode,
          family_code_expires: expiresAt
        }));

        console.log('✅ Dashboard updated with new family code:', familyCode);
      } else {
        setSuccess('New family code generated successfully!');
      }

      setGenerateDialog(false);
      setExpirationDays('');
      console.log('✅ Family code generation completed successfully');
    } catch (error) {
      console.error('❌ Failed to generate family code:', error.response?.data || error.message);

      // Provide specific error messages based on error type
      let errorMessage = 'Failed to generate family code';
      if (error.response?.status === 403) {
        errorMessage = 'Only parents can generate family codes';
      } else if (error.response?.status === 500) {
        errorMessage = 'Server error occurred. Please try again later.';
      } else if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      } else if (error.message) {
        errorMessage = `Connection error: ${error.message}`;
      }

      setError(errorMessage);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    setSuccess('Family code copied to clipboard!');
  };

  const removeChild = async (childId) => {
    try {
      await apiClient.delete(`/family/remove-child/${childId}`);
      setSuccess('Child removed from family');
      setConfirmDialog({ open: false, childId: '', childName: '' });
      fetchData();
    } catch (error) {
      setError('Failed to remove child');
    }
  };

  const joinFamily = async () => {
    try {
      setJoining(true);
      console.log('🔗 Attempting to join family with code:', joinCode);

      // Validate family code format
      if (!joinCode || joinCode.length !== 8) {
        setError('Family code must be 8 characters long');
        return;
      }

      console.log('📤 Sending join-family request...');
      const response = await apiClient.post('/family/join-family', { family_code: joinCode });
      console.log('✅ Join family response:', response.data);

      setSuccess(`Successfully joined family! Connected to ${response.data.parent_name}`);
      setJoinCode('');
      console.log('🔄 Fetching updated family data after joining...');
      await fetchData();
      console.log('✅ Family join process completed successfully');
    } catch (error) {
      console.error('❌ Failed to join family:', error.response?.data || error.message);

      // Provide specific error messages based on error type
      let errorMessage = 'Failed to join family';
      if (error.response?.status === 404) {
        errorMessage = 'Invalid family code. Please check the code and try again.';
      } else if (error.response?.status === 400) {
        errorMessage = error.response.data?.detail || 'You are already linked to a parent account';
      } else if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      } else if (error.message) {
        errorMessage = `Connection error: ${error.message}`;
      }

      setError(errorMessage);
    } finally {
      setJoining(false);
    }
  };

  const leaveFamily = async () => {
    try {
      await apiClient.post('/family/leave-family');
      setSuccess('Successfully left family');
      fetchData();
    } catch (error) {
      setError('Failed to leave family');
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight={200}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3, maxWidth: 800, mx: 'auto' }}>
      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}
      
      {success && (
        <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess('')}>
          {success}
        </Alert>
      )}

      {user?.role === 'parent' ? (
        // Parent Dashboard
        <Box>
          <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <FamilyRestroom color="primary" />
            Family Management
          </Typography>

          {/* Family Code Section */}
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Your Family Code
              </Typography>
              
              {dashboard?.family_code ? (
                <Box>
                  <Paper
                    sx={{
                      p: 2,
                      mb: 2,
                      bgcolor: 'primary.light',
                      color: 'primary.contrastText',
                      textAlign: 'center',
                    }}
                  >
                    <Typography variant="h4" fontFamily="monospace" letterSpacing={2}>
                      {dashboard.family_code}
                    </Typography>
                  </Paper>
                  
                  <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
                    <Button
                      variant="outlined"
                      startIcon={<ContentCopy />}
                      onClick={() => copyToClipboard(dashboard.family_code)}
                    >
                      Copy Code
                    </Button>
                    <Button
                      variant="outlined"
                      startIcon={<Refresh />}
                      onClick={() => setGenerateDialog(true)}
                    >
                      Generate New
                    </Button>
                    <Button
                      variant="outlined"
                      startIcon={<Share />}
                      onClick={() => {
                        const shareText = `Join my family notes with code: ${dashboard.family_code}`;
                        if (navigator.share) {
                          navigator.share({ text: shareText });
                        } else {
                          copyToClipboard(shareText);
                        }
                      }}
                    >
                      Share
                    </Button>
                  </Box>
                  
                  {dashboard.family_code_expires && (
                    <Alert severity="info" icon={<Info />}>
                      This code expires on {new Date(dashboard.family_code_expires).toLocaleDateString()}
                    </Alert>
                  )}
                </Box>
              ) : (
                <Box>
                  <Typography color="text.secondary" sx={{ mb: 2 }}>
                    No family code generated yet.
                  </Typography>
                  <Button
                    variant="contained"
                    onClick={() => setGenerateDialog(true)}
                  >
                    Generate Family Code
                  </Button>
                </Box>
              )}
            </CardContent>
          </Card>

          {/* Children Section */}
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Connected Children ({dashboard?.children?.length || 0})
              </Typography>
              
              {dashboard?.children?.length > 0 ? (
                <List>
                  {dashboard.children.map((child, index) => (
                    <React.Fragment key={child.id}>
                      <ListItem>
                        <ListItemText
                          primary={child.name}
                          secondary={
                            <Box>
                              <Typography variant="body2" color="text.secondary">
                                {child.email}
                              </Typography>
                              <Chip
                                size="small"
                                label={`Joined ${new Date(child.created_at).toLocaleDateString()}`}
                                variant="outlined"
                                sx={{ mt: 0.5 }}
                              />
                            </Box>
                          }
                        />
                        <ListItemSecondaryAction>
                          <IconButton
                            edge="end"
                            onClick={() => setConfirmDialog({
                              open: true,
                              childId: child.id,
                              childName: child.name
                            })}
                            color="error"
                          >
                            <PersonRemove />
                          </IconButton>
                        </ListItemSecondaryAction>
                      </ListItem>
                      {index < dashboard.children.length - 1 && <Divider />}
                    </React.Fragment>
                  ))}
                </List>
              ) : (
                <Alert severity="info">
                  No children connected yet. Share your family code with your children so they can join.
                </Alert>
              )}
            </CardContent>
          </Card>
        </Box>
      ) : (
        // Child Interface
        <Box>
          <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <FamilyRestroom color="primary" />
            Family Connection
          </Typography>

          {parentInfo?.parent ? (
            // Connected to Parent
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom color="success.main">
                  Connected to Parent
                </Typography>
                
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body1">
                    <strong>Parent:</strong> {parentInfo.parent.name}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {parentInfo.parent.email}
                  </Typography>
                </Box>
                
                <Alert severity="info" sx={{ mb: 2 }}>
                  Your parent can view your notes and folders but cannot modify them.
                </Alert>
                
                <Button
                  variant="outlined"
                  color="error"
                  onClick={leaveFamily}
                >
                  Leave Family
                </Button>
              </CardContent>
            </Card>
          ) : (
            // Not Connected
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Join a Family
                </Typography>
                
                <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                  Enter the family code provided by your parent to connect your accounts.
                </Typography>
                
                <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
                  <TextField
                    label="Family Code"
                    value={joinCode}
                    onChange={(e) => setJoinCode(e.target.value.toUpperCase())}
                    placeholder="Enter 8-character code"
                    sx={{ flexGrow: 1 }}
                    inputProps={{ maxLength: 8 }}
                  />
                  <Button
                    variant="contained"
                    onClick={joinFamily}
                    disabled={!joinCode.trim() || joining}
                    sx={{ minWidth: 120 }}
                  >
                    {joining ? <CircularProgress size={24} /> : 'Join'}
                  </Button>
                </Box>
                
                <Alert severity="info">
                  Ask your parent for their family code to connect your accounts.
                </Alert>
              </CardContent>
            </Card>
          )}
        </Box>
      )}

      {/* Generate Code Dialog */}
      <Dialog open={generateDialog} onClose={() => setGenerateDialog(false)}>
        <DialogTitle>Generate New Family Code</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            This will replace your current family code. Children using the old code won't be able to join.
          </Typography>
          
          <TextField
            label="Expires in (days)"
            type="number"
            value={expirationDays}
            onChange={(e) => setExpirationDays(e.target.value)}
            placeholder="Optional - leave empty for no expiration"
            fullWidth
            sx={{ mt: 1 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setGenerateDialog(false)}>Cancel</Button>
          <Button onClick={generateFamilyCode} variant="contained">
            Generate
          </Button>
        </DialogActions>
      </Dialog>

      {/* Remove Child Confirmation Dialog */}
      <Dialog open={confirmDialog.open} onClose={() => setConfirmDialog({ open: false, childId: '', childName: '' })}>
        <DialogTitle>Remove Child</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to remove <strong>{confirmDialog.childName}</strong> from your family?
            They will no longer be able to share their notes with you.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConfirmDialog({ open: false, childId: '', childName: '' })}>
            Cancel
          </Button>
          <Button
            onClick={() => removeChild(confirmDialog.childId)}
            color="error"
            variant="contained"
          >
            Remove
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default FamilyManagement;