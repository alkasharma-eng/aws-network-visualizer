import { useEffect, useState, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';

// Speech Recognition types (browser API)
interface SpeechRecognitionEvent {
  results: SpeechRecognitionResultList;
  resultIndex: number;
}

interface SpeechRecognitionResultList {
  length: number;
  item(index: number): SpeechRecognitionResult;
  [index: number]: SpeechRecognitionResult;
}

interface SpeechRecognitionResult {
  length: number;
  item(index: number): SpeechRecognitionAlternative;
  [index: number]: SpeechRecognitionAlternative;
  isFinal: boolean;
}

interface SpeechRecognitionAlternative {
  transcript: string;
  confidence: number;
}

interface SpeechRecognition extends EventTarget {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  onresult: ((event: SpeechRecognitionEvent) => void) | null;
  onerror: ((event: any) => void) | null;
  onend: (() => void) | null;
  onstart: (() => void) | null;
  start: () => void;
  stop: () => void;
  abort: () => void;
}

declare global {
  interface Window {
    SpeechRecognition: new () => SpeechRecognition;
    webkitSpeechRecognition: new () => SpeechRecognition;
  }
}

export interface VoiceCommand {
  pattern: RegExp;
  action: (matches: RegExpMatchArray) => void;
  description: string;
  examples: string[];
}

export interface UseVoiceCommandsOptions {
  enabled?: boolean;
  language?: string;
  continuous?: boolean;
  interimResults?: boolean;
  onCommand?: (transcript: string, command: string) => void;
}

export interface UseVoiceCommandsReturn {
  isListening: boolean;
  isSupported: boolean;
  transcript: string;
  confidence: number;
  error: string | null;
  startListening: () => void;
  stopListening: () => void;
  toggleListening: () => void;
  registerCommand: (name: string, command: VoiceCommand) => void;
  unregisterCommand: (name: string) => void;
  availableCommands: Record<string, VoiceCommand>;
}

export const useVoiceCommands = (
  options: UseVoiceCommandsOptions = {}
): UseVoiceCommandsReturn => {
  const {
    enabled = true,
    language = 'en-US',
    continuous = true,
    interimResults = false,
    onCommand,
  } = options;

  const navigate = useNavigate();
  const [isListening, setIsListening] = useState(false);
  const [isSupported, setIsSupported] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [confidence, setConfidence] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [availableCommands, setAvailableCommands] = useState<Record<string, VoiceCommand>>({});

  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const commandsRef = useRef<Record<string, VoiceCommand>>({});

  // Check browser support
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    setIsSupported(!!SpeechRecognition);

    if (SpeechRecognition) {
      const recognition = new SpeechRecognition();
      recognition.continuous = continuous;
      recognition.interimResults = interimResults;
      recognition.lang = language;

      recognitionRef.current = recognition;
    } else {
      console.warn('Speech Recognition API not supported in this browser');
    }
  }, [language, continuous, interimResults]);

  // Process voice command
  const processCommand = useCallback(
    (text: string) => {
      const lowerText = text.toLowerCase().trim();
      console.log('[Voice Command] Processing:', lowerText);

      // Try to match against registered commands
      for (const [name, command] of Object.entries(commandsRef.current)) {
        const matches = lowerText.match(command.pattern);
        if (matches) {
          console.log('[Voice Command] Matched:', name);
          if (onCommand) {
            onCommand(text, name);
          }
          command.action(matches);
          toast.success(`Executed: ${name}`, {
            icon: '🎤',
            position: 'bottom-right',
          });
          return true;
        }
      }

      console.log('[Voice Command] No match found');
      toast.error(`Command not recognized: "${text}"`, {
        position: 'bottom-right',
      });
      return false;
    },
    [onCommand]
  );

  // Handle recognition result
  const handleResult = useCallback(
    (event: SpeechRecognitionEvent) => {
      const result = event.results[event.resultIndex];
      const transcriptText = result[0].transcript;
      const confidenceScore = result[0].confidence;

      setTranscript(transcriptText);
      setConfidence(confidenceScore);

      if (result.isFinal) {
        console.log('[Voice Command] Final:', transcriptText, 'Confidence:', confidenceScore);
        processCommand(transcriptText);
      }
    },
    [processCommand]
  );

  // Setup recognition handlers
  useEffect(() => {
    const recognition = recognitionRef.current;
    if (!recognition || !enabled) return;

    recognition.onresult = handleResult;

    recognition.onerror = (event: any) => {
      console.error('[Voice Command] Error:', event.error);
      setError(event.error);
      setIsListening(false);

      if (event.error === 'no-speech') {
        toast.error('No speech detected. Please try again.', {
          position: 'bottom-right',
        });
      } else if (event.error === 'not-allowed') {
        toast.error('Microphone access denied. Please enable in browser settings.', {
          duration: 5000,
          position: 'bottom-right',
        });
      }
    };

    recognition.onend = () => {
      console.log('[Voice Command] Recognition ended');
      setIsListening(false);
    };

    recognition.onstart = () => {
      console.log('[Voice Command] Recognition started');
      setIsListening(true);
      setError(null);
    };

    return () => {
      if (recognition) {
        recognition.onresult = null;
        recognition.onerror = null;
        recognition.onend = null;
        recognition.onstart = null;
      }
    };
  }, [enabled, handleResult]);

  // Register default commands
  useEffect(() => {
    const defaultCommands: Record<string, VoiceCommand> = {
      showDashboard: {
        pattern: /show (dashboard|home|main)/i,
        action: () => navigate('/'),
        description: 'Navigate to the main dashboard',
        examples: ['Show dashboard', 'Show home', 'Show main'],
      },
      showTopology: {
        pattern: /show topology ([\w-]+)\s+(vpc-[\w]+)/i,
        action: (matches) => {
          const region = matches[1];
          const vpcId = matches[2];
          navigate(`/topology/${region}/${vpcId}`);
        },
        description: 'Show topology for a specific VPC',
        examples: ['Show topology us-east-1 vpc-12345', 'Show topology eu-west-1 vpc-abcde'],
      },
      showAnomalies: {
        pattern: /show (anomalies|issues|problems|alerts)/i,
        action: () => navigate('/anomalies'),
        description: 'Navigate to anomalies dashboard',
        examples: ['Show anomalies', 'Show issues', 'Show problems', 'Show alerts'],
      },
      discoverNow: {
        pattern: /discover (now|resources|network)/i,
        action: () => {
          // Trigger discovery - implementation depends on your API
          toast.success('Discovery triggered!', {
            icon: '🔍',
            position: 'bottom-right',
          });
        },
        description: 'Trigger network discovery',
        examples: ['Discover now', 'Discover resources', 'Discover network'],
      },
      switchView3D: {
        pattern: /switch to (3d|three d|three dimensional) (view|mode)/i,
        action: () => {
          // Dispatch custom event for view change
          window.dispatchEvent(new CustomEvent('voiceCommand:switchView', { detail: '3d' }));
        },
        description: 'Switch to 3D topology view',
        examples: ['Switch to 3D view', 'Switch to three D mode'],
      },
      switchView2D: {
        pattern: /switch to (2d|two d|two dimensional) (view|mode)/i,
        action: () => {
          window.dispatchEvent(new CustomEvent('voiceCommand:switchView', { detail: '2d' }));
        },
        description: 'Switch to 2D topology view',
        examples: ['Switch to 2D view', 'Switch to two D mode'],
      },
      zoomIn: {
        pattern: /zoom in|closer/i,
        action: () => {
          window.dispatchEvent(new CustomEvent('voiceCommand:zoom', { detail: 'in' }));
        },
        description: 'Zoom in on the topology',
        examples: ['Zoom in', 'Closer'],
      },
      zoomOut: {
        pattern: /zoom out|farther|further/i,
        action: () => {
          window.dispatchEvent(new CustomEvent('voiceCommand:zoom', { detail: 'out' }));
        },
        description: 'Zoom out of the topology',
        examples: ['Zoom out', 'Farther', 'Further'],
      },
      centerView: {
        pattern: /center (view|graph|topology)|reset view/i,
        action: () => {
          window.dispatchEvent(new CustomEvent('voiceCommand:center'));
        },
        description: 'Center the topology view',
        examples: ['Center view', 'Center graph', 'Reset view'],
      },
      enableDarkMode: {
        pattern: /enable dark (mode|theme)|dark mode on/i,
        action: () => {
          window.dispatchEvent(new CustomEvent('voiceCommand:theme', { detail: 'dark' }));
        },
        description: 'Enable dark mode',
        examples: ['Enable dark mode', 'Dark mode on'],
      },
      enableLightMode: {
        pattern: /enable light (mode|theme)|light mode on/i,
        action: () => {
          window.dispatchEvent(new CustomEvent('voiceCommand:theme', { detail: 'light' }));
        },
        description: 'Enable light mode',
        examples: ['Enable light mode', 'Light mode on'],
      },
      help: {
        pattern: /help|what can (you|i) (do|say)|commands/i,
        action: () => {
          window.dispatchEvent(new CustomEvent('voiceCommand:showHelp'));
        },
        description: 'Show available voice commands',
        examples: ['Help', 'What can you do', 'What can I say', 'Commands'],
      },
    };

    setAvailableCommands(defaultCommands);
    commandsRef.current = defaultCommands;
  }, [navigate]);

  const startListening = useCallback(() => {
    if (!recognitionRef.current) {
      toast.error('Voice recognition not supported', {
        position: 'bottom-right',
      });
      return;
    }

    try {
      recognitionRef.current.start();
      toast.success('Voice commands activated', {
        icon: '🎤',
        duration: 2000,
        position: 'bottom-right',
      });
    } catch (err: any) {
      console.error('[Voice Command] Start error:', err);
      if (err.message.includes('already started')) {
        // Already listening, ignore
        return;
      }
      setError(err.message);
    }
  }, []);

  const stopListening = useCallback(() => {
    if (recognitionRef.current && isListening) {
      recognitionRef.current.stop();
      toast('Voice commands deactivated', {
        icon: '🔇',
        duration: 2000,
        position: 'bottom-right',
      });
    }
  }, [isListening]);

  const toggleListening = useCallback(() => {
    if (isListening) {
      stopListening();
    } else {
      startListening();
    }
  }, [isListening, startListening, stopListening]);

  const registerCommand = useCallback((name: string, command: VoiceCommand) => {
    setAvailableCommands((prev) => ({
      ...prev,
      [name]: command,
    }));
    commandsRef.current[name] = command;
    console.log('[Voice Command] Registered:', name);
  }, []);

  const unregisterCommand = useCallback((name: string) => {
    setAvailableCommands((prev) => {
      const newCommands = { ...prev };
      delete newCommands[name];
      return newCommands;
    });
    delete commandsRef.current[name];
    console.log('[Voice Command] Unregistered:', name);
  }, []);

  return {
    isListening,
    isSupported,
    transcript,
    confidence,
    error,
    startListening,
    stopListening,
    toggleListening,
    registerCommand,
    unregisterCommand,
    availableCommands,
  };
};

export default useVoiceCommands;
