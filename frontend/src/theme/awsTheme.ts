/**
 * AWS-Inspired Theme Configuration
 * Follows Amazon's design language for professional, executive-friendly UI
 */

import { createTheme, ThemeOptions } from '@mui/material/styles';

// AWS Color Palette
const awsColors = {
  squidInk: '#232F3E',      // AWS Primary Dark
  smile: '#FF9900',          // AWS Orange
  awsGreen: '#1D8102',
  awsRed: '#D13212',
  awsBlue: '#0073BB',
  slate: '#545B64',
  lightGray: '#FAFAFA',
  darkGray: '#16191F',
};

// Typography following AWS design
const typography = {
  fontFamily: '"Amazon Ember", "Helvetica Neue", Roboto, Arial, sans-serif',
  h1: {
    fontSize: '2.5rem',
    fontWeight: 700,
    lineHeight: 1.2,
    letterSpacing: '-0.01562em',
  },
  h2: {
    fontSize: '2rem',
    fontWeight: 600,
    lineHeight: 1.3,
  },
  h3: {
    fontSize: '1.75rem',
    fontWeight: 600,
    lineHeight: 1.4,
  },
  h4: {
    fontSize: '1.5rem',
    fontWeight: 600,
    lineHeight: 1.4,
  },
  h5: {
    fontSize: '1.25rem',
    fontWeight: 600,
    lineHeight: 1.5,
  },
  h6: {
    fontSize: '1.125rem',
    fontWeight: 600,
    lineHeight: 1.5,
  },
  subtitle1: {
    fontSize: '1rem',
    fontWeight: 500,
    lineHeight: 1.75,
  },
  subtitle2: {
    fontSize: '0.875rem',
    fontWeight: 500,
    lineHeight: 1.57,
  },
  body1: {
    fontSize: '1rem',
    lineHeight: 1.5,
  },
  body2: {
    fontSize: '0.875rem',
    lineHeight: 1.43,
  },
  button: {
    fontSize: '0.875rem',
    fontWeight: 600,
    textTransform: 'none' as const,
    letterSpacing: '0.02857em',
  },
  caption: {
    fontSize: '0.75rem',
    lineHeight: 1.66,
  },
};

// Light theme configuration
const lightThemeOptions: ThemeOptions = {
  palette: {
    mode: 'light',
    primary: {
      main: awsColors.squidInk,
      light: '#37475A',
      dark: '#161E2D',
      contrastText: '#FFFFFF',
    },
    secondary: {
      main: awsColors.smile,
      light: '#FFAC31',
      dark: '#EC7211',
      contrastText: '#FFFFFF',
    },
    success: {
      main: awsColors.awsGreen,
      light: '#2DA515',
      dark: '#146B01',
    },
    error: {
      main: awsColors.awsRed,
      light: '#DD4B28',
      dark: '#A82A0C',
    },
    warning: {
      main: awsColors.smile,
    },
    info: {
      main: awsColors.awsBlue,
      light: '#179BD7',
      dark: '#005A8E',
    },
    background: {
      default: awsColors.lightGray,
      paper: '#FFFFFF',
    },
    text: {
      primary: 'rgba(0, 0, 0, 0.87)',
      secondary: 'rgba(0, 0, 0, 0.6)',
      disabled: 'rgba(0, 0, 0, 0.38)',
    },
    divider: 'rgba(0, 0, 0, 0.12)',
  },
  typography,
  spacing: 8, // 8px grid system
  shape: {
    borderRadius: 4,
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 4,
          padding: '8px 22px',
          fontSize: '0.875rem',
          fontWeight: 600,
          boxShadow: 'none',
          '&:hover': {
            boxShadow: 'none',
          },
        },
        contained: {
          '&:hover': {
            boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
          },
        },
        sizeLarge: {
          padding: '12px 32px',
          fontSize: '1rem',
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          boxShadow: '0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24)',
          transition: 'box-shadow 0.3s ease-in-out',
          '&:hover': {
            boxShadow: '0 3px 6px rgba(0,0,0,0.16), 0 3px 6px rgba(0,0,0,0.23)',
          },
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: 16,
          fontWeight: 500,
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          boxShadow: '0 1px 3px rgba(0,0,0,0.12)',
        },
      },
    },
    MuiBottomNavigation: {
      styleOverrides: {
        root: {
          borderTop: '1px solid rgba(0,0,0,0.12)',
        },
      },
    },
  },
};

// Dark theme configuration
const darkThemeOptions: ThemeOptions = {
  palette: {
    mode: 'dark',
    primary: {
      main: awsColors.smile,
      light: '#FFAC31',
      dark: '#EC7211',
      contrastText: '#000000',
    },
    secondary: {
      main: awsColors.awsBlue,
      light: '#179BD7',
      dark: '#005A8E',
      contrastText: '#FFFFFF',
    },
    success: {
      main: awsColors.awsGreen,
      light: '#2DA515',
      dark: '#146B01',
    },
    error: {
      main: '#FF5252',
      light: '#FF6E6E',
      dark: '#C62828',
    },
    warning: {
      main: awsColors.smile,
    },
    info: {
      main: awsColors.awsBlue,
    },
    background: {
      default: '#121212',
      paper: '#1E1E1E',
    },
    text: {
      primary: '#FFFFFF',
      secondary: 'rgba(255, 255, 255, 0.7)',
      disabled: 'rgba(255, 255, 255, 0.5)',
    },
    divider: 'rgba(255, 255, 255, 0.12)',
  },
  typography,
  spacing: 8,
  shape: {
    borderRadius: 4,
  },
  components: {
    ...lightThemeOptions.components,
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          backgroundImage: 'none',
          boxShadow: '0 1px 3px rgba(0,0,0,0.3), 0 1px 2px rgba(0,0,0,0.4)',
        },
      },
    },
  },
};

export const createAWSTheme = (mode: 'light' | 'dark') => {
  return createTheme(mode === 'light' ? lightThemeOptions : darkThemeOptions);
};

export default createAWSTheme;
