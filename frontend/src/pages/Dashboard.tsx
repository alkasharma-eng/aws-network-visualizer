import React from 'react';
import ExecutiveDashboard from './ExecutiveDashboard';

/**
 * Main Dashboard Page
 *
 * Uses the ExecutiveDashboard component which provides:
 * - Mobile-first responsive design
 * - AWS-themed Material-UI components
 * - Real-time metrics
 * - Discovery controls
 * - Anomaly overview
 */
const Dashboard: React.FC = () => {
  return <ExecutiveDashboard />;
};

export default Dashboard;
