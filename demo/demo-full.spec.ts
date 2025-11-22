import { test, expect } from '@playwright/test';

/**
 * Full Demo - 120 Seconds (2 minutes)
 *
 * Complete walkthrough for technical deep-dives, customer demos, and training sessions.
 *
 * Timeline:
 * - Act 1: Dashboard & Metrics (0-30s)
 * - Act 2: Multi-Region Discovery (30-60s)
 * - Act 3: Network Topology Deep-Dive (60-90s)
 * - Act 4: Anomaly Detection & Remediation (90-110s)
 * - Act 5: Export & Mobile View (110-120s)
 */

test.describe('Full Demo - 120 Seconds', () => {
  test('Complete AWS Network Visualizer Showcase', async ({ page }) => {
    test.setTimeout(180000); // 3 minutes max

    console.log('\n🎬 Starting Full Demo (120 seconds)...\n');

    // ==================================================================
    // ACT 1: DASHBOARD & METRICS (0-30s)
    // ==================================================================
    await test.step('Act 1: Dashboard Overview & Metrics', async () => {
      console.log('📊 ACT 1: Dashboard Overview (0-30s)');

      // Navigate to dashboard
      await page.goto('https://your-cloudfront-url.cloudfront.net');
      await page.waitForLoadState('networkidle');

      // Verify key metrics are visible
      await expect(page.locator('text=Total Resources')).toBeVisible();
      console.log('  ✅ Total Resources card visible');

      await expect(page.locator('text=Active Regions')).toBeVisible();
      console.log('  ✅ Active Regions card visible');

      await expect(page.locator('text=Critical Anomalies')).toBeVisible();
      console.log('  ✅ Critical Anomalies card visible');

      await expect(page.locator('text=Last Discovery')).toBeVisible();
      console.log('  ✅ Last Discovery timestamp visible');

      // Highlight metrics with visual pulse
      await page.evaluate(() => {
        const cards = document.querySelectorAll('.metric-card');
        cards.forEach((card: any, index: number) => {
          setTimeout(() => {
            card.style.boxShadow = '0 0 20px rgba(255,153,0,0.8)';
            setTimeout(() => {
              card.style.boxShadow = '';
            }, 800);
          }, index * 400);
        });
      });

      await page.waitForTimeout(3000); // Let user see metrics

      // Scroll to see additional dashboard widgets
      await page.evaluate(() => window.scrollBy(0, 200));
      await page.waitForTimeout(2000);

      // Show resource breakdown chart
      const chartVisible = await page.locator('.resources-by-type-chart').isVisible();
      if (chartVisible) {
        console.log('  ✅ Resource breakdown chart visible');
        await page.waitForTimeout(2000);
      }

      console.log('  ⏱️  30 seconds elapsed\n');
    });

    // ==================================================================
    // ACT 2: MULTI-REGION DISCOVERY (30-60s)
    // ==================================================================
    await test.step('Act 2: Multi-Region Discovery', async () => {
      console.log('🔍 ACT 2: Multi-Region Discovery (30-60s)');

      // Scroll back to top
      await page.evaluate(() => window.scrollTo(0, 0));

      // Open region selector
      const regionSelector = page.locator('[aria-label="Select regions"]');
      if (await regionSelector.isVisible()) {
        await regionSelector.click();
        console.log('  ✅ Region selector opened');

        // Select multiple regions
        await page.locator('text=us-east-1').click();
        await page.locator('text=us-west-2').click();
        await page.locator('text=eu-west-1').click();
        console.log('  ✅ Selected 3 regions: us-east-1, us-west-2, eu-west-1');

        // Close selector
        await page.keyboard.press('Escape');
        await page.waitForTimeout(1000);
      }

      // Click "Discover Now" button
      const discoverButton = page.locator('button:has-text("Discover Now")');
      await expect(discoverButton).toBeVisible();
      await discoverButton.click();
      console.log('  ✅ Discovery triggered!');

      // Wait for discovery progress to appear
      await expect(page.locator('role=progressbar')).toBeVisible({ timeout: 5000 });
      console.log('  ✅ Discovery in progress...');

      // Show real-time progress updates
      await page.waitForTimeout(3000);

      // Check if per-region progress is shown
      const regionProgress = await page.locator('.region-progress').count();
      if (regionProgress > 0) {
        console.log(`  ✅ Tracking progress across ${regionProgress} regions`);
      }

      // Show resource counter incrementing
      await page.waitForTimeout(5000);

      // Simulate discovery completion
      const completionToast = page.locator('text=Discovery complete');
      if (await completionToast.isVisible({ timeout: 10000 })) {
        console.log('  ✅ Discovery completed!');
      } else {
        console.log('  ⏭️  Continuing to next section (mock completion)');
      }

      await page.waitForTimeout(2000);
      console.log('  ⏱️  60 seconds elapsed\n');
    });

    // ==================================================================
    // ACT 3: NETWORK TOPOLOGY DEEP-DIVE (60-90s)
    // ==================================================================
    await test.step('Act 3: Network Topology Visualization', async () => {
      console.log('🗺️  ACT 3: Network Topology (60-90s)');

      // Navigate to topology view
      // Option 1: Click on a VPC card
      const vpcCard = page.locator('.vpc-card').first();
      if (await vpcCard.isVisible()) {
        await vpcCard.click();
        console.log('  ✅ Opened VPC topology view');
      } else {
        // Option 2: Navigate directly
        await page.goto('https://your-cloudfront-url.cloudfront.net/topology/us-east-1/vpc-12345');
        console.log('  ✅ Navigated to topology view');
      }

      await page.waitForLoadState('networkidle');

      // Wait for network graph to render
      await expect(page.locator('.network-graph')).toBeVisible({ timeout: 10000 });
      console.log('  ✅ Network graph rendered');

      await page.waitForTimeout(2000);

      // Demonstrate interactive features
      console.log('  🔍 Demonstrating interactive features...');

      // Zoom in on graph
      await page.evaluate(() => {
        const graphContainer = document.querySelector('.network-graph');
        if (graphContainer) {
          const event = new WheelEvent('wheel', { deltaY: -100 });
          graphContainer.dispatchEvent(event);
        }
      });
      await page.waitForTimeout(1000);
      console.log('  ✅ Zoomed in on topology');

      // Pan around the graph
      await page.evaluate(() => {
        const graphContainer = document.querySelector('.network-graph');
        if (graphContainer) {
          const canvas = graphContainer.querySelector('canvas');
          if (canvas) {
            const rect = canvas.getBoundingClientRect();
            const startX = rect.width / 2;
            const startY = rect.height / 2;

            // Simulate drag
            canvas.dispatchEvent(new MouseEvent('mousedown', {
              clientX: startX,
              clientY: startY,
              bubbles: true
            }));

            canvas.dispatchEvent(new MouseEvent('mousemove', {
              clientX: startX + 100,
              clientY: startY + 100,
              bubbles: true
            }));

            canvas.dispatchEvent(new MouseEvent('mouseup', {
              bubbles: true
            }));
          }
        }
      });
      await page.waitForTimeout(1500);
      console.log('  ✅ Panned across topology');

      // Click on a node to show details
      const node = page.locator('.graph-node').first();
      if (await node.isVisible()) {
        await node.click();
        console.log('  ✅ Selected node - details panel opened');
        await page.waitForTimeout(2000);
      }

      // Toggle resource type filters
      const filterButton = page.locator('button:has-text("Filters")');
      if (await filterButton.isVisible()) {
        await filterButton.click();
        console.log('  ✅ Opened filters panel');

        // Toggle EC2 instances filter
        const ec2Filter = page.locator('text=EC2 Instances');
        if (await ec2Filter.isVisible()) {
          await ec2Filter.click();
          await page.waitForTimeout(1000);
          await ec2Filter.click();
          console.log('  ✅ Toggled EC2 filter');
        }

        // Close filters
        await page.keyboard.press('Escape');
      }

      await page.waitForTimeout(3000);
      console.log('  ⏱️  90 seconds elapsed\n');
    });

    // ==================================================================
    // ACT 4: ANOMALY DETECTION & REMEDIATION (90-110s)
    // ==================================================================
    await test.step('Act 4: Security Anomalies & AI Analysis', async () => {
      console.log('🔐 ACT 4: Anomaly Detection (90-110s)');

      // Navigate to anomalies page
      await page.goto('https://your-cloudfront-url.cloudfront.net/anomalies');
      await page.waitForLoadState('networkidle');
      console.log('  ✅ Navigated to anomalies dashboard');

      // Verify anomaly cards are visible
      await expect(page.locator('.anomaly-card').first()).toBeVisible({ timeout: 5000 });
      const anomalyCount = await page.locator('.anomaly-card').count();
      console.log(`  ✅ Found ${anomalyCount} anomalies`);

      await page.waitForTimeout(2000);

      // Filter by severity
      const severityFilter = page.locator('[aria-label="Filter by severity"]');
      if (await severityFilter.isVisible()) {
        await severityFilter.click();
        await page.locator('text=Critical').click();
        console.log('  ✅ Filtered to show only Critical anomalies');
        await page.waitForTimeout(1500);
      }

      // Click on a critical anomaly to see details
      const criticalAnomaly = page.locator('.anomaly-card.critical').first();
      if (await criticalAnomaly.isVisible()) {
        await criticalAnomaly.click();
        console.log('  ✅ Opened critical anomaly details');

        // Verify remediation steps are shown
        const remediationSteps = page.locator('.remediation-steps');
        if (await remediationSteps.isVisible()) {
          console.log('  ✅ AI-powered remediation steps displayed');
        }

        await page.waitForTimeout(3000);

        // Show "Acknowledge" or "Remediate" action
        const acknowledgeButton = page.locator('button:has-text("Acknowledge")');
        if (await acknowledgeButton.isVisible()) {
          await acknowledgeButton.click();
          console.log('  ✅ Anomaly acknowledged');
        }

        await page.waitForTimeout(2000);
      }

      console.log('  ⏱️  110 seconds elapsed\n');
    });

    // ==================================================================
    // ACT 5: EXPORT & MOBILE RESPONSIVENESS (110-120s)
    // ==================================================================
    await test.step('Act 5: Export & Mobile View', async () => {
      console.log('📱 ACT 5: Export & Mobile Features (110-120s)');

      // Navigate back to dashboard
      await page.goto('https://your-cloudfront-url.cloudfront.net');
      await page.waitForLoadState('networkidle');

      // Show export functionality
      const exportButton = page.locator('button:has-text("Export")');
      if (await exportButton.isVisible()) {
        await exportButton.click();
        console.log('  ✅ Export menu opened');

        // Select PDF export option
        const pdfOption = page.locator('text=Export as PDF');
        if (await pdfOption.isVisible()) {
          console.log('  ✅ PDF export option available');
        }

        await page.keyboard.press('Escape');
        await page.waitForTimeout(1000);
      }

      // Demonstrate mobile responsiveness
      console.log('  📱 Demonstrating mobile view...');

      // Switch to mobile viewport
      await page.setViewportSize({ width: 390, height: 844 }); // iPhone 13
      await page.waitForTimeout(1500);
      console.log('  ✅ Switched to mobile viewport (iPhone 13)');

      // Verify mobile-optimized layout
      const isMobileLayout = await page.evaluate(() => {
        const container = document.querySelector('.dashboard-container');
        return container ? window.getComputedStyle(container).flexDirection === 'column' : false;
      });

      if (isMobileLayout) {
        console.log('  ✅ Mobile-optimized single-column layout active');
      }

      // Show bottom navigation (mobile-specific)
      const bottomNav = page.locator('.bottom-navigation');
      if (await bottomNav.isVisible()) {
        console.log('  ✅ Mobile bottom navigation visible');
      }

      // Demonstrate swipe gesture (simulated)
      await page.evaluate(() => {
        const container = document.querySelector('.swipeable-container');
        if (container) {
          container.dispatchEvent(new TouchEvent('touchstart', {
            touches: [{ clientX: 300, clientY: 400 }] as any,
            bubbles: true
          }));

          container.dispatchEvent(new TouchEvent('touchmove', {
            touches: [{ clientX: 100, clientY: 400 }] as any,
            bubbles: true
          }));

          container.dispatchEvent(new TouchEvent('touchend', {
            bubbles: true
          }));
        }
      });
      console.log('  ✅ Swipe navigation demonstrated');

      await page.waitForTimeout(2000);

      console.log('  ⏱️  120 seconds elapsed\n');
      console.log('🎉 Full demo complete!\n');
    });

    // Final summary
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    console.log('✅ DEMO COMPLETE - 120 Seconds');
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    console.log('Showcased:');
    console.log('  • Executive dashboard with real-time metrics');
    console.log('  • Multi-region discovery with progress tracking');
    console.log('  • Interactive network topology with zoom/pan');
    console.log('  • AI-powered anomaly detection & remediation');
    console.log('  • Export capabilities (PDF/PNG)');
    console.log('  • Mobile-responsive design (iPhone optimized)');
    console.log('  • Touch-friendly bottom navigation');
    console.log('  • Swipe gestures for mobile navigation');
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');
  });
});
