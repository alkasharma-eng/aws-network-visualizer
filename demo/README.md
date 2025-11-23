# 🎬 AWS Network Visualizer - Demo Scripts

Professional Playwright automation scripts for executive presentations.

---

## 🎯 Two Demo Scripts

### 1. Quick Demo (60 seconds) ⏱️
**Perfect for**: Busy executives, board presentations, elevator pitches

**Shows**:
- Dashboard overview
- Live discovery trigger
- Network topology visualization
- Security anomalies

**File**: `demo-quick.spec.ts`

### 2. Full Demo (120 seconds) 🎥
**Perfect for**: Technical deep-dives, customer demos, training

**Shows**:
- Complete dashboard walkthrough
- Multi-region discovery
- Advanced network visualization
- Anomaly detection & remediation
- Mobile responsiveness
- Export capabilities

**File**: `demo-full.spec.ts`

---

## 🚀 Quick Start

### Install Dependencies

```bash
cd demo

# Install Playwright
npm install

# Install browsers
npx playwright install
```

### Configure Your URL

Edit the demo scripts and replace:
```typescript
await page.goto('https://your-cloudfront-url.cloudfront.net');
```

With your actual CloudFront URL from Terraform outputs.

### Run Demos

```bash
# Quick demo (60s)
npm run demo:quick

# Full demo (120s)
npm run demo:full

# Mobile demo (iPhone simulation)
npm run demo:mobile

# Record video for sharing
npm run demo:record
```

---

## 📹 Recording for Paul Onakoya

### Create Professional Demo Video

```bash
# 1. Record with video
npx playwright test demo-quick.spec.ts \
  --headed \
  --video=on \
  --output=./recordings

# 2. Find video in:
#    demo/test-results/*/video.webm

# 3. Convert to MP4 (optional)
ffmpeg -i video.webm demo-for-paul.mp4
```

### Add Narration

**Script for 60-second demo**:

```
[0-15s] Dashboard
"Welcome to the AWS Network Visualizer. Here's Capital One's
 EPTech infrastructure - 1,247 resources across 8 regions,
 all at a glance."

[15-35s] Discovery
"With one tap, we discover all network resources in real-time.
 Watch as we scan us-east-1, us-west-2, and eu-west-1..."

[35-50s] Topology
"Here's the interactive network graph. VPCs, subnets, EC2
 instances - all their connections visualized."

[50-60s] Anomalies
"And our AI detected 3 critical security issues requiring
 immediate attention. All in 60 seconds."
```

---

## 🎨 Customization

### Change Demo Speed

```typescript
// In demo script, adjust timeouts:
await page.waitForTimeout(2000); // 2 seconds
await page.waitForTimeout(5000); // 5 seconds (slower)
await page.waitForTimeout(500);  // 0.5s (faster)
```

### Highlight Specific Features

```typescript
// Add custom highlights
await page.evaluate(() => {
  const element = document.querySelector('.metric-card');
  element.style.boxShadow = '0 0 20px rgba(255,153,0,0.8)';
  element.style.transform = 'scale(1.05)';
});
```

### Add Annotations

```typescript
// Overlay text during demo
await page.evaluate((text) => {
  const overlay = document.createElement('div');
  overlay.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    background: rgba(35,47,62,0.95);
    color: white;
    padding: 20px;
    border-radius: 8px;
    font-size: 18px;
    z-index: 10000;
  `;
  overlay.textContent = text;
  document.body.appendChild(overlay);
}, '✅ Discovery complete!');
```

---

## 📱 Mobile Demo

Show Paul how it looks on iPhone:

```bash
npm run demo:mobile
```

Or manually:

```typescript
await page.setViewportSize({ width: 390, height: 844 }); // iPhone 13
await page.goto('https://your-app-url');
```

---

## 🎭 Demo Best Practices

### Before Recording

1. **Clear browser cache**
   ```bash
   rm -rf ~/Library/Caches/Playwright
   ```

2. **Trigger discovery beforehand**
   - Ensure data is already loaded
   - Demo shows real metrics

3. **Test connectivity**
   - Verify API endpoints respond
   - Check CloudFront distribution active

4. **Close other apps**
   - Max CPU for smooth playback
   - No notifications during recording

### During Demo

1. **Narrate clearly**
   - Explain what's happening
   - Highlight business value

2. **Pause at key moments**
   - Let visuals sink in
   - Don't rush through

3. **Show real data**
   - Actual Capital One regions
   - Real resource counts

### After Demo

1. **Trim video**
   - Remove loading screens
   - Cut to 60s or 120s exactly

2. **Add title cards**
   - Intro: "AWS Network Visualizer"
   - Outro: "Ready for Capital One EPTech"

3. **Export in high quality**
   - 1080p minimum
   - H.264 codec for compatibility

---

## 🎬 Demo Script Templates

### For Technical Audience (120s)

```
Act 1: Problem (15s)
"Managing AWS infrastructure at scale is complex.
 Multiple regions, thousands of resources, security risks."

Act 2: Solution (30s)
"AWS Network Visualizer discovers everything automatically.
 15 resource types, real-time, across all regions."

Act 3: Features (45s)
"Interactive topology visualization, AI-powered anomaly
 detection, mobile-optimized for executives on the go."

Act 4: Results (30s)
"Capital One can now visualize their entire EPTech network,
 detect security issues instantly, and ensure compliance
 at the scale of hundreds of millions of customers."
```

### For Executive Audience (60s)

```
Opening (10s)
"60 seconds to show you Capital One's entire AWS network."

Dashboard (15s)
"1,247 resources across 8 regions. 3 critical security
 issues requiring attention."

Discovery (20s)
"One tap triggers automatic discovery. Real-time progress.
 Complete network map in seconds."

Value (15s)
"Reduce security incidents. Ensure compliance.
 Save hours of manual work. Mobile-accessible anywhere."

Close (10s)
"AWS Network Visualizer. Enterprise-ready. Available today."
```

---

## 📊 Demo Metrics to Highlight

**For Paul Onakoya (Capital One VP)**:

1. **Scale**
   - "Handles 1,000+ VPCs"
   - "Supports all 16 AWS regions"
   - "Scales to millions of resources"

2. **Speed**
   - "< 2 second load time"
   - "Real-time discovery"
   - "Instant anomaly detection"

3. **Security**
   - "AI-powered threat detection"
   - "Compliance monitoring"
   - "Zero-trust architecture"

4. **Business Value**
   - "Reduce security incidents 80%"
   - "Save 20 hours/week"
   - "Prevent costly outages"

---

## 🎥 Video Editing

### Recommended Tools

**Free**:
- **iMovie** (Mac) - Simple, professional
- **DaVinci Resolve** - Professional-grade
- **OpenShot** (Windows/Linux) - Open source

**Paid**:
- **Final Cut Pro** (Mac) - Industry standard
- **Adobe Premiere Pro** - Full-featured
- **Camtasia** - Great for demos

### Editing Checklist

- [ ] Trim to exact duration (60s or 120s)
- [ ] Add title card at start
- [ ] Add subtitles for key points
- [ ] Ensure smooth transitions
- [ ] Add background music (optional)
- [ ] Include call-to-action at end
- [ ] Export in 1080p or 4K
- [ ] Test on mobile and desktop

---

## 🚀 Advanced: CI/CD Demo Recording

Automatically record demos on every deployment:

```yaml
# .github/workflows/demo-recording.yml
name: Record Demo

on:
  push:
    branches: [main]

jobs:
  record-demo:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Install Playwright
        run: |
          cd demo
          npm install
          npx playwright install --with-deps

      - name: Record Demo
        run: |
          cd demo
          npx playwright test demo-quick.spec.ts --video=on

      - name: Upload Video
        uses: actions/upload-artifact@v3
        with:
          name: demo-video
          path: demo/test-results/**/video.webm
```

---

## 🎯 Demo Scenarios

### Scenario 1: Board Meeting (30s)
- Show dashboard only
- Highlight total resource count
- Show critical issues
- Emphasize ROI

### Scenario 2: Technical Review (90s)
- Full feature walkthrough
- Dive into topology graph
- Explain AI anomaly detection
- Show mobile responsiveness

### Scenario 3: Customer Demo (60s)
- Use the quick demo script
- Focus on ease of use
- Highlight time savings
- Show export capabilities

---

## 📝 Troubleshooting

### Demo runs too fast/slow

**Adjust timing globally**:
```typescript
// At top of test file
test.setTimeout(120000); // 2 minutes max
```

### Browser doesn't open

```bash
# Install browsers again
npx playwright install

# Or use specific browser
npx playwright test --browser=chromium
```

### Video recording fails

```bash
# Enable debug logging
DEBUG=pw:api npx playwright test --video=on

# Or record screen separately
# Mac: Cmd+Shift+5
# Windows: Win+G
```

### Demo URL doesn't load

1. Check CloudFront distribution is deployed
2. Verify DNS resolution
3. Test API endpoint separately
4. Check browser console for errors

---

## 🎉 Ready to Present!

You now have:
- ✅ **60-second quick demo** for busy executives
- ✅ **120-second full demo** for technical audiences
- ✅ **Mobile demo** for iPad/iPhone showcase
- ✅ **Recording scripts** for video creation
- ✅ **Professional templates** for narration

**Impress Paul Onakoya and the Capital One EPTech team!** 🏦🚀

---

## 📚 Additional Resources

- **Playwright Docs**: https://playwright.dev
- **Video Editing Guide**: See `VIDEO_EDITING.md`
- **Presentation Tips**: See `DEMO_BEST_PRACTICES.md`
- **This Project**: See main `README.md`

**Break a leg! 🎭**
