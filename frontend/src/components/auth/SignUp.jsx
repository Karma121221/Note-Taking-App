import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  TextField,
  Button,
  Typography,
  Alert,
  InputAdornment,
  IconButton,
  Link,
  Divider,
  Stack,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  FormHelperText
} from '@mui/material';
import {
  Visibility,
  VisibilityOff,
  Email,
  Lock,
  Person,
  PersonAdd,
  Group,
  FamilyRestroom
} from '@mui/icons-material';
import { useAuth } from '../../contexts/AuthContext';
import { useNavigate, Link as RouterLink } from 'react-router-dom';

const SignUp = () => {
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
    role: 'child',
    familyCode: ''
  });
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);
  
  const { register } = useAuth();
  const navigate = useNavigate();

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: ''
      }));
    }
  };

  const validateForm = () => {
    const newErrors = {};

    if (!formData.username.trim()) {
      newErrors.username = 'Username is required';
    } else if (formData.username.length < 3) {
      newErrors.username = 'Username must be at least 3 characters';
    }

    if (!formData.email.trim()) {
      newErrors.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = 'Please enter a valid email';
    }

    if (!formData.password) {
      newErrors.password = 'Password is required';
    } else if (formData.password.length < 6) {
      newErrors.password = 'Password must be at least 6 characters';
    }

    if (!formData.confirmPassword) {
      newErrors.confirmPassword = 'Please confirm your password';
    } else if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = 'Passwords do not match';
    }

    return newErrors;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setErrors({});

    const validationErrors = validateForm();
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      setLoading(false);
      return;
    }

    try {
      await register(formData.username, formData.email, formData.password, formData.role, formData.familyCode);
      navigate('/dashboard');
    } catch (error) {
      if (error.response?.data?.detail) {
        if (typeof error.response.data.detail === 'string') {
          setErrors({ general: error.response.data.detail });
        } else {
          // Handle validation errors from backend
          const backendErrors = {};
          if (error.response.data.detail.includes('email')) {
            backendErrors.email = 'Email already exists';
          }
          if (error.response.data.detail.includes('username')) {
            backendErrors.username = 'Username already exists';
          }
          setErrors(backendErrors);
        }
      } else {
        setErrors({ general: 'An error occurred during registration. Please try again.' });
      }
    } finally {
      setLoading(false);
    }
  };

  const togglePasswordVisibility = () => {
    setShowPassword(!showPassword);
  };

  const toggleConfirmPasswordVisibility = () => {
    setShowConfirmPassword(!showConfirmPassword);
  };

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        bgcolor: 'background.default',
        p: { xs: 1, sm: 2 },
        width: '100%'
      }}
    >
      <Card
        variant="outlined"
        sx={{
          maxWidth: { xs: '100%', sm: 480 },
          width: '100%',
          mx: 'auto',
          boxShadow: { xs: 'none', sm: '0 4px 12px rgba(0,0,0,0.1)' },
          border: '1px solid',
          borderColor: 'divider',
          borderRadius: 2
        }}
      >
        <CardContent sx={{ p: { xs: 3, sm: 4 } }}>
          <Stack spacing={3}>
            <Box textAlign="center">
              <Typography variant="h4" component="h1" fontWeight={600}>
                Create Account
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                Start organizing your notes today
              </Typography>
            </Box>

            {errors.general && (
              <Alert severity="error" sx={{ mb: 2 }}>
                {errors.general}
              </Alert>
            )}

            <Box component="form" onSubmit={handleSubmit}>
              <Stack spacing={3}>
                <TextField
                  fullWidth
                  name="username"
                  label="Username"
                  value={formData.username}
                  onChange={handleChange}
                  error={!!errors.username}
                  helperText={errors.username}
                  required
                  slotProps={{
                    input: {
                      startAdornment: (
                        <InputAdornment position="start">
                          <Person color="action" />
                        </InputAdornment>
                      ),
                    },
                  }}
                />

                <TextField
                  fullWidth
                  name="email"
                  label="Email"
                  type="email"
                  value={formData.email}
                  onChange={handleChange}
                  error={!!errors.email}
                  helperText={errors.email}
                  required
                  slotProps={{
                    input: {
                      startAdornment: (
                        <InputAdornment position="start">
                          <Email color="action" />
                        </InputAdornment>
                      ),
                    },
                  }}
                />

                <FormControl fullWidth required error={!!errors.role}>
                  <InputLabel>Account Type</InputLabel>
                  <Select
                    name="role"
                    value={formData.role}
                    onChange={handleChange}
                    label="Account Type"
                    startAdornment={
                      <InputAdornment position="start">
                        <Group color="action" />
                      </InputAdornment>
                    }
                  >
                    <MenuItem value="child">Child - Can create and edit notes</MenuItem>
                    <MenuItem value="parent">Parent - Can view children's notes</MenuItem>
                  </Select>
                  {errors.role && (
                    <FormHelperText>{errors.role}</FormHelperText>
                  )}
                </FormControl>

                {formData.role === 'child' && (
                  <TextField
                    fullWidth
                    name="familyCode"
                    label="Family Code (Optional)"
                    value={formData.familyCode}
                    onChange={handleChange}
                    error={!!errors.familyCode}
                    helperText={errors.familyCode || 'Enter your parent\'s family code to connect automatically'}
                    placeholder="Enter 8-character code"
                    slotProps={{
                      input: {
                        startAdornment: (
                          <InputAdornment position="start">
                            <FamilyRestroom color="action" />
                          </InputAdornment>
                        ),
                      },
                    }}
                    inputProps={{ maxLength: 8 }}
                  />
                )}

                <TextField
                  fullWidth
                  name="password"
                  label="Password"
                  type={showPassword ? 'text' : 'password'}
                  value={formData.password}
                  onChange={handleChange}
                  error={!!errors.password}
                  helperText={errors.password || 'Minimum 6 characters'}
                  required
                  slotProps={{
                    input: {
                      startAdornment: (
                        <InputAdornment position="start">
                          <Lock color="action" />
                        </InputAdornment>
                      ),
                      endAdornment: (
                        <InputAdornment position="end">
                          <IconButton
                            aria-label="toggle password visibility"
                            onClick={togglePasswordVisibility}
                            edge="end"
                          >
                            {showPassword ? <VisibilityOff /> : <Visibility />}
                          </IconButton>
                        </InputAdornment>
                      ),
                    },
                  }}
                />

                <TextField
                  fullWidth
                  name="confirmPassword"
                  label="Confirm Password"
                  type={showConfirmPassword ? 'text' : 'password'}
                  value={formData.confirmPassword}
                  onChange={handleChange}
                  error={!!errors.confirmPassword}
                  helperText={errors.confirmPassword}
                  required
                  slotProps={{
                    input: {
                      startAdornment: (
                        <InputAdornment position="start">
                          <Lock color="action" />
                        </InputAdornment>
                      ),
                      endAdornment: (
                        <InputAdornment position="end">
                          <IconButton
                            aria-label="toggle confirm password visibility"
                            onClick={toggleConfirmPasswordVisibility}
                            edge="end"
                          >
                            {showConfirmPassword ? <VisibilityOff /> : <Visibility />}
                          </IconButton>
                        </InputAdornment>
                      ),
                    },
                  }}
                />

                <Button
                  type="submit"
                  fullWidth
                  variant="contained"
                  loading={loading}
                  loadingPosition="start"
                  startIcon={<PersonAdd />}
                  sx={{
                    py: 1.5,
                    fontSize: '1rem',
                    fontWeight: 500
                  }}
                >
                  Create Account
                </Button>
              </Stack>
            </Box>

            <Divider sx={{ my: 2 }}>
              <Typography variant="body2" color="text.secondary">
                Already have an account?
              </Typography>
            </Divider>

            <Box textAlign="center">
              <Link
                component={RouterLink}
                to="/signin"
                variant="body2"
                sx={{
                  textDecoration: 'none',
                  fontWeight: 500,
                  '&:hover': {
                    textDecoration: 'underline'
                  }
                }}
              >
                Sign in instead
              </Link>
            </Box>
          </Stack>
        </CardContent>
      </Card>
    </Box>
  );
};

export default SignUp;