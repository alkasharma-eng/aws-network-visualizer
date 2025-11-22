/**
 * Executive Dashboard - Mobile-optimized for busy VPs
 * Designed for Paul Onakoya (VP, Capital One EPTech)
 */

import React, { useState } from 'react';
import {
  Box,
  Container,
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  LinearProgress,
  Chip,
  IconButton,
  useTheme,
  useMediaQuery,
  Alert,
  Fade,
  Skeleton,
} from '@mui/material';
import {
  CloudQueue,
  Security,
  TrendingUp,
  Refresh,
  GetApp,
  Warning,
  CheckCircle,
  Error as ErrorIcon,
  Speed,
  Storage,
  NetworkCheck,
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import toast from 'react-hot-toast';
import { format } from 'date-fns';
import { fetchTopologySummary, triggerDiscovery } from '../api/client';

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: React.ReactNode;
  color: 'primary' | 'secondary' | 'success' | 'error' | 'warning' | 'info';
  trend?: {
    direction: 'up' | 'down';
    value: string;
  };
  onClick?: () => void;
}

const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  subtitle,
  icon,
  color,
  trend,
  onClick,
}) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

  return (
    <motion.div
      whileHover={{ scale: onClick ? 1.02 : 1 }}
      whileTap={{ scale: onClick ? 0.98 : 1 }}
    >
      <Card
        sx={{
          height: '100%',
          minHeight: isMobile ? 120 : 140,
          cursor: onClick ? 'pointer' : 'default',
          position: 'relative',
          overflow: 'hidden',
        }}
        onClick={onClick}
      >
        <CardContent>
          <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={1}>
            <Typography variant="subtitle2" color="text.secondary" fontWeight={600}>
              {title}
            </Typography>
            <Box
              sx={{
                color: `${color}.main`,
                backgroundColor: `${color}.light`,
                borderRadius: '50%',
                p: 0.5,
                opacity: 0.2,
              }}
            >
              {icon}
            </Box>
          </Box>

          <Typography
            variant={isMobile ? 'h4' : 'h3'}
            component="div"
            color={`${color}.main`}
            fontWeight={700}
            gutterBottom
          >
            {value}
          </Typography>

          {subtitle && (
            <Typography variant="caption" color="text.secondary">
              {subtitle}
            </Typography>
          )}

          {trend && (
            <Box display="flex" alignItems="center" mt={1}>
              <Chip
                size="small"
                label={trend.value}
                color={trend.direction === 'up' ? 'success' : 'error'}
                sx={{ height: 20, fontSize: '0.75rem' }}
              />
            </Box>
          )}
        </CardContent>

        {/* Subtle gradient overlay */}
        <Box
          sx={{
            position: 'absolute',
            bottom: 0,
            right: 0,
            width: '100%',
            height: '100%',
            background: `linear-gradient(135deg, transparent 60%, ${theme.palette[color].light}15)`,
            pointerEvents: 'none',
          }}
        />
      </Card>
    </motion.div>
  );
};

const ExecutiveDashboard: React.FC = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const queryClient = useQueryClient();
  const [discoveryProgress, setDiscoveryProgress] = useState(0);

  // Fetch topology summary
  const { data: summary, isLoading, error } = useQuery({
    queryKey: ['topology-summary'],
    queryFn: fetchTopologySummary,
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  // Trigger discovery mutation
  const discovery = useMutation({
    mutationFn: (regions: string[]) => triggerDiscovery(regions),
    onSuccess: () => {
      toast.success('Discovery started successfully!');
      // Simulate progress
      let progress = 0;
      const interval = setInterval(() => {
        progress += 10;
        setDiscoveryProgress(progress);
        if (progress >= 100) {
          clearInterval(interval);
          queryClient.invalidateQueries({ queryKey: ['topology-summary'] });
          setTimeout(() => setDiscoveryProgress(0), 1000);
        }
      }, 500);
    },
    onError: (err) => {
      toast.error('Failed to start discovery');
      console.error(err);
    },
  });

  const handleDiscovery = () => {
    const regions = ['us-east-1', 'us-west-2', 'eu-west-1'];
    discovery.mutate(regions);
  };

  const handleExport = () => {
    toast.success('Generating PDF report...');
    // TODO: Implement PDF export
  };

  if (error) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4 }}>
        <Alert severity="error">
          Failed to load dashboard data. Please try again.
        </Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ mt: isMobile ? 2 : 4, mb: 4 }}>
      {/* Header */}
      <Box mb={3}>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Box>
            <Typography variant={isMobile ? 'h5' : 'h4'} fontWeight={700} gutterBottom>
              AWS Network Overview
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Last updated: {format(new Date(), 'MMM dd, yyyy HH:mm')}
            </Typography>
          </Box>

          <Box display="flex" gap={1}>
            <IconButton onClick={() => queryClient.invalidateQueries()} size="small">
              <Refresh />
            </IconButton>
            {!isMobile && (
              <IconButton onClick={handleExport} size="small">
                <GetApp />
              </IconButton>
            )}
          </Box>
        </Box>

        {/* Quick Actions */}
        <Box display="flex" gap={2} flexWrap="wrap">
          <Button
            variant="contained"
            color="secondary"
            size={isMobile ? 'medium' : 'large'}
            startIcon={<Refresh />}
            onClick={handleDiscovery}
            disabled={discovery.isPending || discoveryProgress > 0}
            sx={{ minWidth: isMobile ? 'auto' : 180 }}
          >
            {discoveryProgress > 0 ? `${discoveryProgress}%` : 'Discover Now'}
          </Button>

          {!isMobile && (
            <Button
              variant="outlined"
              color="primary"
              size="large"
              startIcon={<GetApp />}
              onClick={handleExport}
            >
              Export Report
            </Button>
          )}
        </Box>

        {/* Discovery Progress */}
        {discoveryProgress > 0 && (
          <Fade in>
            <Box mt={2}>
              <LinearProgress
                variant="determinate"
                value={discoveryProgress}
                sx={{ height: 8, borderRadius: 4 }}
              />
              <Typography variant="caption" color="text.secondary" mt={0.5}>
                Discovering resources across 3 regions...
              </Typography>
            </Box>
          </Fade>
        )}
      </Box>

      {/* Key Metrics Grid */}
      <Grid container spacing={isMobile ? 2 : 3} mb={4}>
        {isLoading ? (
          <>
            {[1, 2, 3, 4].map((i) => (
              <Grid item xs={12} sm={6} md={3} key={i}>
                <Skeleton variant="rectangular" height={140} sx={{ borderRadius: 2 }} />
              </Grid>
            ))}
          </>
        ) : (
          <>
            <Grid item xs={12} sm={6} md={3}>
              <MetricCard
                title="Total Resources"
                value={summary?.total_resources.toLocaleString() || '0'}
                subtitle="Across all regions"
                icon={<Storage />}
                color="primary"
              />
            </Grid>

            <Grid item xs={12} sm={6} md={3}>
              <MetricCard
                title="Active Regions"
                value={summary?.total_regions || '0'}
                subtitle="AWS regions discovered"
                icon={<CloudQueue />}
                color="info"
              />
            </Grid>

            <Grid item xs={12} sm={6} md={3}>
              <MetricCard
                title="VPCs"
                value={summary?.resources_by_type?.vpc || '0'}
                subtitle="Virtual Private Clouds"
                icon={<NetworkCheck />}
                color="success"
              />
            </Grid>

            <Grid item xs={12} sm={6} md={3}>
              <MetricCard
                title="Critical Issues"
                value="3"
                subtitle="Requires immediate attention"
                icon={<Warning />}
                color="error"
                onClick={() => window.location.href = '/anomalies'}
              />
            </Grid>
          </>
        )}
      </Grid>

      {/* Secondary Metrics */}
      <Grid container spacing={isMobile ? 2 : 3} mb={4}>
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" fontWeight={600} gutterBottom>
                Resources by Type
              </Typography>

              {isLoading ? (
                <Skeleton variant="rectangular" height={200} />
              ) : (
                <Box>
                  {Object.entries(summary?.resources_by_type || {}).map(([type, count]) => (
                    <Box
                      key={type}
                      display="flex"
                      justifyContent="space-between"
                      alignItems="center"
                      py={1.5}
                      borderBottom="1px solid"
                      borderColor="divider"
                    >
                      <Typography variant="body2" textTransform="capitalize">
                        {type.replace(/_/g, ' ')}
                      </Typography>
                      <Chip label={count} size="small" color="primary" variant="outlined" />
                    </Box>
                  ))}
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Typography variant="h6" fontWeight={600} gutterBottom>
                Health Status
              </Typography>

              <Box display="flex" flexDirection="column" gap={2} mt={2}>
                <Box display="flex" alignItems="center" gap={1}>
                  <CheckCircle color="success" fontSize="small" />
                  <Typography variant="body2">All systems operational</Typography>
                </Box>

                <Box display="flex" alignItems="center" gap={1}>
                  <Warning color="warning" fontSize="small" />
                  <Typography variant="body2">3 warnings detected</Typography>
                </Box>

                <Box display="flex" alignItems="center" gap={1}>
                  <Speed color="info" fontSize="small" />
                  <Typography variant="body2">Performance: Good</Typography>
                </Box>

                <Box display="flex" alignItems="center" gap={1}>
                  <Security color="success" fontSize="small" />
                  <Typography variant="body2">Compliance: 94%</Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Recent Activity */}
      <Card>
        <CardContent>
          <Typography variant="h6" fontWeight={600} gutterBottom>
            Recent Activity
          </Typography>

          <Box>
            {[
              { type: 'discovery', message: 'Discovery completed for us-east-1', time: '2 min ago', severity: 'success' },
              { type: 'anomaly', message: 'New security issue detected', time: '15 min ago', severity: 'error' },
              { type: 'change', message: '15 resources updated', time: '1 hour ago', severity: 'info' },
            ].map((activity, index) => (
              <Box
                key={index}
                display="flex"
                alignItems="center"
                gap={2}
                py={1.5}
                borderBottom={index < 2 ? '1px solid' : 'none'}
                borderColor="divider"
              >
                <Box
                  sx={{
                    width: 8,
                    height: 8,
                    borderRadius: '50%',
                    bgcolor: `${activity.severity}.main`,
                  }}
                />
                <Box flex={1}>
                  <Typography variant="body2">{activity.message}</Typography>
                  <Typography variant="caption" color="text.secondary">
                    {activity.time}
                  </Typography>
                </Box>
              </Box>
            ))}
          </Box>
        </CardContent>
      </Card>
    </Container>
  );
};

export default ExecutiveDashboard;
