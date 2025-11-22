import React, { useState } from 'react';
import {
  Box,
  Paper,
  IconButton,
  Tooltip,
  Typography,
  Fade,
  Chip,
  Stack,
  Collapse,
  List,
  ListItem,
  ListItemText,
  Divider,
  Alert,
  useTheme,
  alpha,
} from '@mui/material';
import {
  Mic as MicIcon,
  MicOff as MicOffIcon,
  Help as HelpIcon,
  Close as CloseIcon,
  VolumeUp as VolumeUpIcon,
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';
import { useVoiceCommands } from '../hooks/useVoiceCommands';

interface VoiceCommandPanelProps {
  enabled?: boolean;
}

const VoiceCommandPanel: React.FC<VoiceCommandPanelProps> = ({ enabled = true }) => {
  const theme = useTheme();
  const [showHelp, setShowHelp] = useState(false);
  const [showTranscript, setShowTranscript] = useState(false);

  const {
    isListening,
    isSupported,
    transcript,
    confidence,
    error,
    toggleListening,
    availableCommands,
  } = useVoiceCommands({
    enabled,
    continuous: true,
    interimResults: true,
    onCommand: (transcript, commandName) => {
      console.log(`[Voice Panel] Command executed: ${commandName} - "${transcript}"`);
      setShowTranscript(true);
      setTimeout(() => setShowTranscript(false), 3000);
    },
  });

  // Listen for help command
  React.useEffect(() => {
    const handleShowHelp = () => {
      setShowHelp(true);
    };

    window.addEventListener('voiceCommand:showHelp', handleShowHelp);
    return () => window.removeEventListener('voiceCommand:showHelp', handleShowHelp);
  }, []);

  if (!isSupported) {
    return (
      <Tooltip title="Voice commands not supported in this browser" placement="left">
        <Box
          sx={{
            position: 'fixed',
            bottom: 80,
            right: 24,
            zIndex: 1000,
          }}
        >
          <IconButton disabled size="large">
            <MicOffIcon />
          </IconButton>
        </Box>
      </Tooltip>
    );
  }

  return (
    <>
      {/* Floating Voice Button */}
      <Box
        sx={{
          position: 'fixed',
          bottom: 80,
          right: 24,
          zIndex: 1000,
          display: 'flex',
          flexDirection: 'column',
          gap: 1,
          alignItems: 'flex-end',
        }}
      >
        {/* Transcript Display */}
        <AnimatePresence>
          {showTranscript && transcript && (
            <motion.div
              initial={{ opacity: 0, x: 20, scale: 0.9 }}
              animate={{ opacity: 1, x: 0, scale: 1 }}
              exit={{ opacity: 0, x: 20, scale: 0.9 }}
              transition={{ duration: 0.2 }}
            >
              <Paper
                elevation={6}
                sx={{
                  p: 2,
                  maxWidth: 300,
                  background: alpha(theme.palette.success.main, 0.1),
                  border: `1px solid ${theme.palette.success.main}`,
                }}
              >
                <Stack spacing={1}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <VolumeUpIcon fontSize="small" color="success" />
                    <Typography variant="caption" sx={{ fontWeight: 700 }}>
                      Heard:
                    </Typography>
                  </Box>
                  <Typography variant="body2" sx={{ fontStyle: 'italic' }}>
                    "{transcript}"
                  </Typography>
                  {confidence > 0 && (
                    <Chip
                      label={`${Math.round(confidence * 100)}% confidence`}
                      size="small"
                      color="success"
                      variant="outlined"
                    />
                  )}
                </Stack>
              </Paper>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Error Display */}
        {error && (
          <Fade in timeout={300}>
            <Alert
              severity="error"
              onClose={() => {}}
              sx={{ maxWidth: 300 }}
            >
              {error}
            </Alert>
          </Fade>
        )}

        {/* Control Buttons */}
        <Paper
          elevation={6}
          sx={{
            p: 1,
            background: alpha(theme.palette.background.paper, 0.95),
            backdropFilter: 'blur(10px)',
            border: isListening ? `2px solid ${theme.palette.error.main}` : '2px solid transparent',
            transition: 'all 0.3s ease',
          }}
        >
          <Stack direction="row" spacing={1}>
            {/* Help Button */}
            <Tooltip title="Show voice commands" placement="left">
              <IconButton
                size="large"
                onClick={() => setShowHelp(!showHelp)}
                color={showHelp ? 'primary' : 'default'}
              >
                <HelpIcon />
              </IconButton>
            </Tooltip>

            {/* Microphone Button */}
            <Tooltip
              title={isListening ? 'Stop listening' : 'Start voice commands'}
              placement="left"
            >
              <IconButton
                size="large"
                onClick={toggleListening}
                sx={{
                  background: isListening
                    ? alpha(theme.palette.error.main, 0.1)
                    : alpha(theme.palette.primary.main, 0.1),
                  '&:hover': {
                    background: isListening
                      ? alpha(theme.palette.error.main, 0.2)
                      : alpha(theme.palette.primary.main, 0.2),
                  },
                  animation: isListening ? 'pulse 1.5s ease-in-out infinite' : 'none',
                  '@keyframes pulse': {
                    '0%, 100%': {
                      transform: 'scale(1)',
                      boxShadow: `0 0 0 0 ${alpha(theme.palette.error.main, 0.7)}`,
                    },
                    '50%': {
                      transform: 'scale(1.05)',
                      boxShadow: `0 0 0 10px ${alpha(theme.palette.error.main, 0)}`,
                    },
                  },
                }}
              >
                {isListening ? (
                  <MicIcon color="error" />
                ) : (
                  <MicIcon color="primary" />
                )}
              </IconButton>
            </Tooltip>
          </Stack>
        </Paper>

        {/* Status Indicator */}
        {isListening && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
          >
            <Chip
              label="Listening..."
              color="error"
              size="small"
              icon={<MicIcon />}
              sx={{
                animation: 'blink 1s ease-in-out infinite',
                '@keyframes blink': {
                  '0%, 100%': { opacity: 1 },
                  '50%': { opacity: 0.6 },
                },
              }}
            />
          </motion.div>
        )}
      </Box>

      {/* Help Panel */}
      <Collapse in={showHelp}>
        <Box
          sx={{
            position: 'fixed',
            bottom: 160,
            right: 24,
            zIndex: 999,
            maxWidth: 400,
          }}
        >
          <Paper
            elevation={8}
            sx={{
              p: 3,
              maxHeight: '70vh',
              overflow: 'auto',
              background: alpha(theme.palette.background.paper, 0.98),
              backdropFilter: 'blur(10px)',
            }}
          >
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6" sx={{ fontWeight: 700 }}>
                🎤 Voice Commands
              </Typography>
              <IconButton size="small" onClick={() => setShowHelp(false)}>
                <CloseIcon />
              </IconButton>
            </Box>

            <Alert severity="info" sx={{ mb: 2 }}>
              Click the microphone button and speak clearly. Commands are case-insensitive.
            </Alert>

            <Divider sx={{ mb: 2 }} />

            <List dense>
              {Object.entries(availableCommands).map(([name, command]) => (
                <ListItem key={name} sx={{ flexDirection: 'column', alignItems: 'flex-start', mb: 1 }}>
                  <ListItemText
                    primary={
                      <Typography variant="subtitle2" sx={{ fontWeight: 700, color: theme.palette.primary.main }}>
                        {command.description}
                      </Typography>
                    }
                    secondary={
                      <Box sx={{ mt: 0.5 }}>
                        {command.examples.map((example, idx) => (
                          <Chip
                            key={idx}
                            label={`"${example}"`}
                            size="small"
                            variant="outlined"
                            sx={{
                              mr: 0.5,
                              mb: 0.5,
                              fontSize: '0.7rem',
                              fontFamily: 'monospace',
                            }}
                          />
                        ))}
                      </Box>
                    }
                  />
                </ListItem>
              ))}
            </List>

            <Divider sx={{ my: 2 }} />

            <Typography variant="caption" color="text.secondary" sx={{ display: 'block', textAlign: 'center' }}>
              Pro Tip: Say "Help" anytime to show this panel
            </Typography>
          </Paper>
        </Box>
      </Collapse>
    </>
  );
};

export default VoiceCommandPanel;
