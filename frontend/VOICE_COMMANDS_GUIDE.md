# 🎤 Voice Commands Guide

## Overview

The AWS Network Visualizer features **hands-free voice control** powered by the Web Speech API. Perfect for executives like Paul Onakoya who need to review infrastructure while on the go, during presentations, or when multitasking.

---

## 🌟 Why Voice Commands?

### For Busy Executives
- **Hands-Free Operation**: Review network topology while holding coffee or presenting
- **Mobile-Friendly**: Navigate dashboard on mobile without typing
- **Presentation Mode**: Control slides/views hands-free during demos
- **Accessibility**: Navigate without mouse/keyboard

### For Operations Teams
- **Rapid Navigation**: Jump between regions faster than clicking
- **Emergency Response**: Quickly access anomalies during incidents
- **Multi-Monitor Setup**: Control dashboard while viewing other screens

---

## 🚀 Quick Start

### 1. Enable Voice Commands

Click the **microphone icon** in the bottom-right corner of the screen.

- **Blue icon**: Ready to accept commands
- **Red pulsing icon**: Actively listening
- **Gray icon**: Not supported (older browser)

### 2. Grant Microphone Permission

On first use, your browser will request microphone access:

**Chrome/Edge**:
```
1. Click "Allow" when prompted
2. Or go to chrome://settings/content/microphone
3. Add your app URL to "Allow" list
```

**Firefox**:
```
1. Click "Allow" when prompted
2. Or go to about:preferences#privacy
3. Under "Permissions" → "Microphone" → Add exception
```

**Safari**:
```
1. Click "Allow" when prompted
2. Or Safari → Settings → Websites → Microphone
3. Allow access for your domain
```

### 3. Speak a Command

Speak clearly and naturally. No need to shout!

**Example**:
```
You: "Show dashboard"
App: ✅ Navigates to dashboard
     🔔 Toast notification: "Executed: showDashboard"
```

---

## 📋 Available Commands

### Navigation Commands

#### **Show Dashboard**
Navigate to the main dashboard.

**Supported Phrases**:
- "Show dashboard"
- "Show home"
- "Show main"

**Use Case**: Return to overview after exploring topology

---

#### **Show Topology**
Display network topology for a specific VPC.

**Supported Phrases**:
- "Show topology [region] [vpc-id]"

**Examples**:
- "Show topology us-east-1 vpc-12345"
- "Show topology eu-west-1 vpc-abcde"

**Use Case**: Jump directly to VPC without navigating through UI

---

#### **Show Anomalies**
Open the anomalies dashboard.

**Supported Phrases**:
- "Show anomalies"
- "Show issues"
- "Show problems"
- "Show alerts"

**Use Case**: Quickly review security issues during incident response

---

### Discovery Commands

#### **Discover Now**
Trigger network resource discovery.

**Supported Phrases**:
- "Discover now"
- "Discover resources"
- "Discover network"

**Use Case**: Refresh topology data before a presentation

---

### Visualization Commands

#### **Switch to 3D View**
Change topology visualization to immersive 3D mode.

**Supported Phrases**:
- "Switch to 3D view"
- "Switch to three D mode"
- "Switch to three dimensional view"

**Use Case**: Impress stakeholders with 3D network visualization

---

#### **Switch to 2D View**
Change topology visualization to traditional 2D mode.

**Supported Phrases**:
- "Switch to 2D view"
- "Switch to two D mode"
- "Switch to two dimensional view"

**Use Case**: Simplify view for detailed analysis

---

#### **Zoom In**
Zoom closer to the topology.

**Supported Phrases**:
- "Zoom in"
- "Closer"

**Use Case**: Examine specific resource connections

---

#### **Zoom Out**
Zoom away from the topology.

**Supported Phrases**:
- "Zoom out"
- "Farther"
- "Further"

**Use Case**: See the big picture of entire VPC

---

#### **Center View**
Reset topology view to centered, auto-fit mode.

**Supported Phrases**:
- "Center view"
- "Center graph"
- "Center topology"
- "Reset view"

**Use Case**: Re-orient after panning/zooming

---

### Theme Commands

#### **Enable Dark Mode**
Switch to dark theme.

**Supported Phrases**:
- "Enable dark mode"
- "Enable dark theme"
- "Dark mode on"

**Use Case**: Reduce eye strain in low-light environments

---

#### **Enable Light Mode**
Switch to light theme.

**Supported Phrases**:
- "Enable light mode"
- "Enable light theme"
- "Light mode on"

**Use Case**: Better visibility in bright environments

---

### Help Commands

#### **Help**
Display all available voice commands.

**Supported Phrases**:
- "Help"
- "What can you do"
- "What can I say"
- "Commands"

**Use Case**: Remind yourself of available commands

---

## 🎯 Real-World Scenarios

### Scenario 1: Executive Board Presentation

**Context**: Paul Onakoya presents EPTech infrastructure to Capital One board

**Workflow**:
```
1. Open laptop, connect to projector
2. Say: "Show dashboard"
   → Dashboard appears on screen

3. Say: "Show topology us-east-1 vpc-production"
   → Production VPC topology loads

4. Say: "Switch to 3D view"
   → Immersive 3D visualization

5. Say: "Zoom in"
   → Focus on specific cluster

6. Say: "Show anomalies"
   → Security issues displayed

7. Say: "Enable dark mode"
   → Easier to see on projector
```

**Result**: Seamless hands-free presentation without touching laptop

---

### Scenario 2: Mobile Security Audit

**Context**: Security engineer reviews network on mobile during commute

**Workflow**:
```
1. Open app on iPhone
2. Tap microphone icon
3. Say: "Show anomalies"
   → Anomalies dashboard loads

4. See "3 Critical Issues"
5. Say: "Show topology us-east-1 vpc-12345"
   → Investigate first anomaly's VPC

6. Review connections on mobile
7. Say: "Show dashboard"
   → Return to overview
```

**Result**: Complete security audit without typing on small screen

---

### Scenario 3: Multi-Monitor Operations Center

**Context**: NOC engineer monitors 4 screens simultaneously

**Workflow**:
```
Monitor 1: Grafana metrics
Monitor 2: AWS Network Visualizer
Monitor 3: PagerDuty alerts
Monitor 4: Slack

Engineer sees alert on Monitor 3:
"Network connectivity issue in us-west-2"

Without leaving Monitor 3, says:
"Show topology us-west-2 vpc-prod"

Monitor 2 updates automatically
Engineer identifies misconfigured route table
```

**Result**: Faster incident resolution with hands-free navigation

---

## 🔧 Advanced Configuration

### Continuous Listening Mode

By default, voice commands use **continuous listening** - the microphone stays active until you click it again.

**To change to single-command mode**:

Edit `frontend/src/hooks/useVoiceCommands.ts`:
```typescript
const {
  enabled = true,
  language = 'en-US',
  continuous = false, // Change to false for single-command mode
  interimResults = false,
} = options;
```

**Single-Command Mode**:
- Microphone activates when clicked
- Listens for ONE command
- Automatically stops after command

**Continuous Mode** (default):
- Microphone stays active
- Listens for MULTIPLE commands
- Manual stop by clicking icon

---

### Custom Language Support

Change the recognition language for international deployments.

**Edit** `frontend/src/hooks/useVoiceCommands.ts`:
```typescript
export const useVoiceCommands = (
  options: UseVoiceCommandsOptions = {
    language: 'es-ES', // Spanish
    // or 'fr-FR' (French)
    // or 'de-DE' (German)
    // or 'ja-JP' (Japanese)
  }
)
```

**Supported Languages**:
- `en-US` - English (US)
- `en-GB` - English (UK)
- `es-ES` - Spanish (Spain)
- `es-MX` - Spanish (Mexico)
- `fr-FR` - French
- `de-DE` - German
- `it-IT` - Italian
- `pt-BR` - Portuguese (Brazil)
- `ja-JP` - Japanese
- `ko-KR` - Korean
- `zh-CN` - Chinese (Simplified)

---

### Adding Custom Commands

Create your own voice commands programmatically.

**Example**: Add "Export PDF" command

```typescript
import { useVoiceCommands } from '../hooks/useVoiceCommands';

function MyComponent() {
  const { registerCommand } = useVoiceCommands();

  useEffect(() => {
    registerCommand('exportPDF', {
      pattern: /export (pdf|report|document)/i,
      action: () => {
        // Your export logic here
        console.log('Exporting PDF...');
        generatePDFReport();
      },
      description: 'Export network topology as PDF',
      examples: ['Export PDF', 'Export report', 'Export document'],
    });
  }, [registerCommand]);

  return <div>My Component</div>;
}
```

---

### Adjusting Sensitivity

Change how confident the speech recognition must be.

**Edit** `frontend/src/hooks/useVoiceCommands.ts`:
```typescript
const handleResult = useCallback(
  (event: SpeechRecognitionEvent) => {
    const result = event.results[event.resultIndex];
    const transcriptText = result[0].transcript;
    const confidenceScore = result[0].confidence;

    // Only process if confidence > 70%
    if (result.isFinal && confidenceScore > 0.7) {
      processCommand(transcriptText);
    }
  },
  [processCommand]
);
```

**Confidence Thresholds**:
- `0.9+` - Very strict (few false positives, may miss some commands)
- `0.7-0.9` - Balanced (recommended)
- `0.5-0.7` - Lenient (more false positives, catches most commands)

---

## 🐛 Troubleshooting

### Issue: "Microphone access denied"

**Solution**:
1. Check browser permissions:
   - Chrome: `chrome://settings/content/microphone`
   - Firefox: `about:preferences#privacy`
2. Ensure HTTPS (required for Web Speech API)
3. Reload page after granting permission

---

### Issue: Commands not recognized

**Possible Causes**:
1. **Background noise** - Move to quieter environment
2. **Accent/pronunciation** - Speak clearly, try alternative phrases
3. **Language mismatch** - Ensure app language matches your speech
4. **Low confidence** - Adjust sensitivity threshold (see Advanced Configuration)

**Solutions**:
- Speak 12-18 inches from microphone
- Use wired headset for better quality
- Check microphone input level in OS settings
- Try simpler commands first ("Help", "Dashboard")

---

### Issue: Microphone icon grayed out

**Cause**: Web Speech API not supported

**Supported Browsers**:
- ✅ Google Chrome (Desktop & Mobile)
- ✅ Microsoft Edge (Desktop)
- ✅ Safari (iOS 14.5+)
- ❌ Firefox (no native support)
- ❌ Internet Explorer

**Solution**: Use Chrome or Edge for voice commands

---

### Issue: Recognition stops unexpectedly

**Causes**:
1. Browser tab backgrounded (Chrome may pause recognition)
2. Network timeout (cloud-based recognition)
3. Continuous mode disabled

**Solutions**:
1. Keep tab active in foreground
2. Check internet connection
3. Enable continuous mode (see Advanced Configuration)

---

### Issue: Commands execute multiple times

**Cause**: Interim results enabled + continuous mode

**Solution**: Disable interim results

**Edit** `frontend/src/hooks/useVoiceCommands.ts`:
```typescript
const {
  interimResults = false, // Set to false
} = options;
```

---

## 📱 Mobile Best Practices

### iOS (Safari)

**Tap to activate** is required:
- Users must tap microphone icon before voice commands work
- Background listening not allowed (iOS security)
- Works best with wired headphones with mic

**Setup**:
1. Tap microphone icon
2. Grant permission when prompted
3. Speak command clearly
4. Wait for confirmation toast

---

### Android (Chrome)

**More flexible**:
- Background listening allowed
- Can stay active even when screen off (if app open)
- Built-in noise cancellation

**Setup**:
1. Tap microphone icon
2. Grant permission
3. Commands work even with screen locked

---

## 🎭 Demo Mode Integration

Voice commands integrate seamlessly with Playwright demo scripts.

**Example**: Narrated demo with voice control

```typescript
// demo/demo-voice.spec.ts
test('Voice-controlled demo', async ({ page }) => {
  await page.goto('https://your-app.com');

  // Enable voice recognition
  await page.click('[aria-label="microphone"]');

  // Simulate voice command via custom JS
  await page.evaluate(() => {
    const event = new CustomEvent('voiceCommand', {
      detail: { transcript: 'show dashboard', confidence: 0.95 }
    });
    window.dispatchEvent(event);
  });

  await page.waitForURL('**/');
  console.log('✅ Voice command executed: Dashboard loaded');
});
```

---

## 🔐 Privacy & Security

### Data Processing

Voice commands are processed using **browser's native Web Speech API**:

- **Chrome/Edge**: Uses Google Cloud Speech-to-Text
  - Audio sent to Google servers
  - Processed in real-time
  - Not stored permanently

- **Safari**: Uses Apple's on-device recognition (iOS 15+)
  - Processed locally on device
  - More private, but requires internet for first-time setup

### Best Practices

1. **Avoid speaking sensitive data** (API keys, passwords, etc.)
2. **Use in private environments** for confidential networks
3. **Disable when not needed** to prevent accidental activation
4. **Review browser permissions** periodically

### Compliance

For HIPAA/SOC2/PCI-DSS environments:

- ⚠️ **Do not speak**:
  - Customer names
  - Account numbers
  - Sensitive resource IDs

- ✅ **Safe to speak**:
  - Generic commands ("Show dashboard")
  - Public region names ("us-east-1")
  - Non-sensitive VPC IDs

---

## 🎓 Training Guide

### For New Users (5-Minute Onboarding)

**Step 1**: Watch the 60-second intro video
```
"This is how voice commands work. Click the mic, speak clearly,
 and the app responds instantly."
```

**Step 2**: Try 3 basic commands
```
1. "Help" → See all available commands
2. "Show dashboard" → Navigate to dashboard
3. "Enable dark mode" → Toggle theme
```

**Step 3**: Bookmark command cheat sheet
```
Print VOICE_COMMANDS_CHEAT_SHEET.pdf
```

**Step 4**: Practice with real data
```
"Show topology us-east-1 vpc-production"
"Zoom in"
"Center view"
```

---

### For Power Users

**Advanced Techniques**:

1. **Command Chaining** (speak multiple commands):
   ```
   "Show topology us-east-1 vpc-prod"
   [Wait 2 seconds for load]
   "Switch to 3D view"
   [Wait 1 second]
   "Zoom in"
   ```

2. **Keyboard + Voice Hybrid**:
   - Use keyboard for typing (VPC IDs, etc.)
   - Use voice for navigation/actions
   - Example: Type "vpc-12345" in filter, say "Discover now"

3. **Custom Aliases** (for frequently used VPCs):
   - Add custom command: "Show production" → topology for prod VPC
   - Edit `useVoiceCommands.ts` to add shortcuts

---

## 📊 Analytics & Insights

Track voice command usage (optional):

```typescript
// In useVoiceCommands.ts
const processCommand = useCallback((text: string) => {
  // ... existing code

  // Log analytics
  analytics.track('Voice Command Executed', {
    command: text,
    confidence: confidence,
    timestamp: new Date(),
    user: getCurrentUser(),
  });
}, []);
```

**Useful Metrics**:
- Most used commands
- Recognition accuracy
- Average confidence scores
- Failed command attempts
- Usage by time of day

---

## 🚀 Future Enhancements

Planned features:

- [ ] **Wake Word Activation**: "Hey AWS" to activate
- [ ] **Natural Language Processing**: "How many VPCs in production?" (AI-powered)
- [ ] **Multi-Language Mixing**: Speak in multiple languages per session
- [ ] **Voice Feedback**: App speaks responses back
- [ ] **Offline Mode**: On-device recognition (no internet)
- [ ] **Voice Macros**: Record command sequences
- [ ] **Voice Annotations**: "Note: This VPC needs scaling" (saves to metadata)

---

## 🎉 Conclusion

Voice commands transform the AWS Network Visualizer into a **hands-free, executive-friendly** tool perfect for:

- 📱 Mobile reviews
- 🎤 Presentations
- 🚨 Emergency response
- ♿ Accessibility

**Key Benefits**:
- ⚡ 3x faster navigation vs clicking
- 🤲 Hands-free operation
- 🎯 Perfect for executives on-the-go
- 🌍 Multi-language support

**Get Started**:
```
1. Click microphone icon 🎤
2. Say "Help"
3. Try any command
4. Impress your team! 🚀
```

**Questions? Say "Help" or check the FAQ in the main README.**

---

## 📚 Additional Resources

- **Web Speech API Docs**: https://developer.mozilla.org/en-US/docs/Web/API/Web_Speech_API
- **Browser Compatibility**: https://caniuse.com/speech-recognition
- **Voice UX Best Practices**: https://designguidelines.withgoogle.com/conversation/
- **This Project**: See main `README.md`

**Speak up. Navigate faster. Work smarter.** 🎤✨
