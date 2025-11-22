import React, { useState, useMemo } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import {
  Box,
  AppBar,
  Toolbar,
  Typography,
  IconButton,
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemButton,
  Divider,
  useTheme,
  useMediaQuery,
  Fab,
  Tooltip,
  Switch,
  FormControlLabel,
  alpha,
  CssBaseline,
  ThemeProvider,
  createTheme,
} from '@mui/material';
import {
  Menu as MenuIcon,
  Dashboard as DashboardIcon,
  Visibility as ViewIcon,
  Warning as WarningIcon,
  Brightness4 as DarkModeIcon,
  Brightness7 as LightModeIcon,
  CloudQueue as CloudIcon,
} from '@mui/icons-material';
import { Toaster } from 'react-hot-toast';
import { motion } from 'framer-motion';
import VoiceCommandPanel from './VoiceCommandPanel';
import { createAWSTheme } from '../theme/awsTheme';

const Layout: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const systemTheme = useMediaQuery('(prefers-color-scheme: dark)');

  const [drawerOpen, setDrawerOpen] = useState(false);
  const [themeMode, setThemeMode] = useState<'light' | 'dark'>(
    (localStorage.getItem('themeMode') as 'light' | 'dark') || (systemTheme ? 'dark' : 'light')
  );

  const isMobile = useMediaQuery('(max-width:768px)');

  // Create theme based on mode
  const theme = useMemo(() => createAWSTheme(themeMode), [themeMode]);

  // Navigation items
  const navigationItems = [
    {
      text: 'Dashboard',
      icon: <DashboardIcon />,
      path: '/',
    },
    {
      text: 'Anomalies',
      icon: <WarningIcon />,
      path: '/anomalies',
    },
  ];

  const toggleTheme = () => {
    const newMode = themeMode === 'light' ? 'dark' : 'light';
    setThemeMode(newMode);
    localStorage.setItem('themeMode', newMode);
  };

  const toggleDrawer = (open: boolean) => () => {
    setDrawerOpen(open);
  };

  const handleNavigation = (path: string) => {
    navigate(path);
    setDrawerOpen(false);
  };

  // Listen for voice command theme changes
  React.useEffect(() => {
    const handleThemeCommand = (event: any) => {
      const mode = event.detail;
      setThemeMode(mode);
      localStorage.setItem('themeMode', mode);
    };

    window.addEventListener('voiceCommand:theme', handleThemeCommand);
    return () => window.removeEventListener('voiceCommand:theme', handleThemeCommand);
  }, []);

  const drawerContent = (
    <Box
      sx={{ width: 280, pt: 2 }}
      role="presentation"
    >
      <Box sx={{ px: 2, mb: 3, display: 'flex', alignItems: 'center', gap: 1 }}>
        <CloudIcon sx={{ fontSize: 32, color: '#FF9900' }} />
        <Typography variant="h6" sx={{ fontWeight: 700 }}>
          AWS Network Viz
        </Typography>
      </Box>

      <Divider />

      <List>
        {navigationItems.map((item) => (
          <ListItem key={item.text} disablePadding>
            <ListItemButton
              selected={location.pathname === item.path}
              onClick={() => handleNavigation(item.path)}
              sx={{
                '&.Mui-selected': {
                  background: alpha(theme.palette.primary.main, 0.1),
                  borderRight: `4px solid ${theme.palette.primary.main}`,
                },
              }}
            >
              <ListItemIcon sx={{ color: location.pathname === item.path ? theme.palette.primary.main : 'inherit' }}>
                {item.icon}
              </ListItemIcon>
              <ListItemText
                primary={item.text}
                primaryTypographyProps={{
                  fontWeight: location.pathname === item.path ? 700 : 400,
                }}
              />
            </ListItemButton>
          </ListItem>
        ))}
      </List>

      <Divider sx={{ my: 2 }} />

      <Box sx={{ px: 2 }}>
        <FormControlLabel
          control={
            <Switch
              checked={themeMode === 'dark'}
              onChange={toggleTheme}
              icon={<LightModeIcon />}
              checkedIcon={<DarkModeIcon />}
            />
          }
          label={
            <Typography variant="body2">
              {themeMode === 'dark' ? 'Dark Mode' : 'Light Mode'}
            </Typography>
          }
        />
      </Box>
    </Box>
  );

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box sx={{ display: 'flex', minHeight: '100vh' }}>
        {/* App Bar */}
        <AppBar
          position="fixed"
          elevation={2}
          sx={{
            zIndex: theme.zIndex.drawer + 1,
            background: theme.palette.mode === 'dark'
              ? alpha('#232F3E', 0.95)
              : alpha('#232F3E', 1),
            backdropFilter: 'blur(10px)',
          }}
        >
          <Toolbar>
            <IconButton
              edge="start"
              color="inherit"
              aria-label="menu"
              onClick={toggleDrawer(true)}
              sx={{ mr: 2 }}
            >
              <MenuIcon />
            </IconButton>

            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5 }}
              style={{ display: 'flex', alignItems: 'center', gap: 8, flexGrow: 1 }}
            >
              <CloudIcon sx={{ fontSize: 28, color: '#FF9900' }} />
              <Typography variant="h6" component="div" sx={{ fontWeight: 700, color: 'white' }}>
                AWS Network Visualizer
              </Typography>
            </motion.div>

            {!isMobile && (
              <Tooltip title={themeMode === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode'}>
                <IconButton color="inherit" onClick={toggleTheme}>
                  {themeMode === 'dark' ? <LightModeIcon /> : <DarkModeIcon />}
                </IconButton>
              </Tooltip>
            )}
          </Toolbar>
        </AppBar>

        {/* Navigation Drawer */}
        <Drawer
          anchor="left"
          open={drawerOpen}
          onClose={toggleDrawer(false)}
        >
          {drawerContent}
        </Drawer>

        {/* Main Content */}
        <Box
          component="main"
          sx={{
            flexGrow: 1,
            p: 0,
            mt: 8,
            minHeight: 'calc(100vh - 64px)',
            background: theme.palette.background.default,
          }}
        >
          <motion.div
            key={location.pathname}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.3 }}
          >
            <Outlet />
          </motion.div>
        </Box>

        {/* Voice Command Panel */}
        <VoiceCommandPanel enabled={true} />

        {/* Toast Notifications */}
        <Toaster
          position="top-right"
          toastOptions={{
            duration: 3000,
            style: {
              background: theme.palette.background.paper,
              color: theme.palette.text.primary,
              borderRadius: '8px',
              boxShadow: theme.shadows[8],
            },
            success: {
              iconTheme: {
                primary: theme.palette.success.main,
                secondary: 'white',
              },
            },
            error: {
              iconTheme: {
                primary: theme.palette.error.main,
                secondary: 'white',
              },
            },
          }}
        />
      </Box>
    </ThemeProvider>
  );
};

export default Layout;
