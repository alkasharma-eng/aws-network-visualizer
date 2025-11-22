import React, { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Box,
  Paper,
  Typography,
  Grid,
  Card,
  CardContent,
  Chip,
  Stack,
  Alert,
  CircularProgress,
  TextField,
  InputAdornment,
  ToggleButtonGroup,
  ToggleButton,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  List,
  ListItem,
  ListItemText,
  Button,
  Divider,
  useTheme,
  useMediaQuery,
  alpha,
} from '@mui/material';
import {
  Warning as WarningIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
  CheckCircle as CheckCircleIcon,
  Search as SearchIcon,
  ExpandMore as ExpandMoreIcon,
  Security as SecurityIcon,
  AttachMoney as CostIcon,
  Gavel as ComplianceIcon,
  Build as RemediateIcon,
} from '@mui/icons-material';
import { fetchAnomalies, type Anomaly, type AnomalyReport } from '../api/client';
import { motion } from 'framer-motion';

const SEVERITY_COLORS = {
  critical: 'error',
  high: 'warning',
  medium: 'info',
  low: 'success',
} as const;

const SEVERITY_ICONS = {
  critical: <ErrorIcon />,
  high: <WarningIcon />,
  medium: <InfoIcon />,
  low: <CheckCircleIcon />,
};

const TYPE_ICONS: Record<string, React.ReactNode> = {
  security: <SecurityIcon />,
  cost: <CostIcon />,
  compliance: <ComplianceIcon />,
};

type SeverityFilter = 'all' | 'critical' | 'high' | 'medium' | 'low';

const AnomaliesView: React.FC = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  const [severityFilter, setSeverityFilter] = useState<SeverityFilter>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedAnomaly, setExpandedAnomaly] = useState<string | false>(false);

  // Fetch anomalies
  const {
    data: anomalyReport,
    isLoading,
    isError,
    error,
  } = useQuery<AnomalyReport>({
    queryKey: ['anomalies'],
    queryFn: fetchAnomalies,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  // Filter anomalies
  const filteredAnomalies = useMemo(() => {
    if (!anomalyReport) return [];

    let filtered = anomalyReport.anomalies;

    // Filter by severity
    if (severityFilter !== 'all') {
      filtered = filtered.filter((a) => a.severity === severityFilter);
    }

    // Filter by search query
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(
        (a) =>
          a.title.toLowerCase().includes(query) ||
          a.description.toLowerCase().includes(query) ||
          a.type.toLowerCase().includes(query)
      );
    }

    return filtered;
  }, [anomalyReport, severityFilter, searchQuery]);

  const handleAccordionChange = (anomalyId: string) => (event: React.SyntheticEvent, isExpanded: boolean) => {
    setExpandedAnomaly(isExpanded ? anomalyId : false);
  };

  const handleRemediate = (anomaly: Anomaly) => {
    // Implement remediation logic
    console.log('Remediating anomaly:', anomaly);
  };

  if (isLoading) {
    return (
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          minHeight: '80vh',
          flexDirection: 'column',
          gap: 2,
        }}
      >
        <CircularProgress size={60} />
        <Typography variant="h6" color="text.secondary">
          Loading anomalies...
        </Typography>
      </Box>
    );
  }

  if (isError) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">
          <Typography variant="h6">Failed to load anomalies</Typography>
          <Typography variant="body2">{(error as Error).message}</Typography>
        </Alert>
      </Box>
    );
  }

  if (!anomalyReport) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="info">No anomaly data available</Alert>
      </Box>
    );
  }

  return (
    <Box sx={{ p: isMobile ? 2 : 3 }}>
      {/* Header */}
      <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
        <Typography variant="h4" sx={{ fontWeight: 700, mb: 2 }}>
          Security Anomalies & Issues
        </Typography>
        <Typography variant="body1" color="text.secondary">
          AI-powered detection of security risks, compliance issues, and cost optimization opportunities
        </Typography>
      </Paper>

      {/* Summary Cards */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={6} sm={3}>
          <Card elevation={2}>
            <CardContent>
              <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 1 }}>
                <ErrorIcon color="error" />
                <Typography variant="h4" sx={{ fontWeight: 700 }}>
                  {anomalyReport.by_severity.critical || 0}
                </Typography>
              </Stack>
              <Typography variant="body2" color="text.secondary">
                Critical
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={6} sm={3}>
          <Card elevation={2}>
            <CardContent>
              <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 1 }}>
                <WarningIcon color="warning" />
                <Typography variant="h4" sx={{ fontWeight: 700 }}>
                  {anomalyReport.by_severity.high || 0}
                </Typography>
              </Stack>
              <Typography variant="body2" color="text.secondary">
                High
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={6} sm={3}>
          <Card elevation={2}>
            <CardContent>
              <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 1 }}>
                <InfoIcon color="info" />
                <Typography variant="h4" sx={{ fontWeight: 700 }}>
                  {anomalyReport.by_severity.medium || 0}
                </Typography>
              </Stack>
              <Typography variant="body2" color="text.secondary">
                Medium
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={6} sm={3}>
          <Card elevation={2}>
            <CardContent>
              <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 1 }}>
                <CheckCircleIcon color="success" />
                <Typography variant="h4" sx={{ fontWeight: 700 }}>
                  {anomalyReport.by_severity.low || 0}
                </Typography>
              </Stack>
              <Typography variant="body2" color="text.secondary">
                Low
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Filters */}
      <Paper elevation={2} sx={{ p: 2, mb: 3 }}>
        <Stack
          direction={isMobile ? 'column' : 'row'}
          spacing={2}
          alignItems={isMobile ? 'stretch' : 'center'}
          justifyContent="space-between"
        >
          {/* Search */}
          <TextField
            placeholder="Search anomalies..."
            size="small"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            sx={{ flexGrow: isMobile ? 1 : 0, minWidth: isMobile ? '100%' : 300 }}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon />
                </InputAdornment>
              ),
            }}
          />

          {/* Severity Filter */}
          <ToggleButtonGroup
            value={severityFilter}
            exclusive
            onChange={(e, value) => value && setSeverityFilter(value)}
            size="small"
            fullWidth={isMobile}
          >
            <ToggleButton value="all">All</ToggleButton>
            <ToggleButton value="critical">Critical</ToggleButton>
            <ToggleButton value="high">High</ToggleButton>
            <ToggleButton value="medium">Medium</ToggleButton>
            <ToggleButton value="low">Low</ToggleButton>
          </ToggleButtonGroup>
        </Stack>
      </Paper>

      {/* Results Count */}
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        Showing {filteredAnomalies.length} of {anomalyReport.total_anomalies} anomalies
      </Typography>

      {/* Anomalies List */}
      {filteredAnomalies.length === 0 ? (
        <Alert severity="success" sx={{ mt: 2 }}>
          No anomalies found matching your filters. Your infrastructure looks healthy! 🎉
        </Alert>
      ) : (
        <Stack spacing={2}>
          {filteredAnomalies.map((anomaly, index) => (
            <motion.div
              key={`${anomaly.type}-${index}`}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, delay: index * 0.05 }}
            >
              <Accordion
                expanded={expandedAnomaly === `${anomaly.type}-${index}`}
                onChange={handleAccordionChange(`${anomaly.type}-${index}`)}
                elevation={3}
                sx={{
                  '&:before': {
                    display: 'none',
                  },
                  borderLeft: `4px solid`,
                  borderLeftColor:
                    theme.palette[SEVERITY_COLORS[anomaly.severity as keyof typeof SEVERITY_COLORS]]?.main ||
                    theme.palette.grey[500],
                }}
              >
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flexGrow: 1, pr: 2 }}>
                    {/* Type Icon */}
                    <Box sx={{ color: theme.palette.text.secondary }}>
                      {TYPE_ICONS[anomaly.type] || <InfoIcon />}
                    </Box>

                    {/* Title and Description */}
                    <Box sx={{ flexGrow: 1, minWidth: 0 }}>
                      <Typography variant="subtitle1" sx={{ fontWeight: 700 }}>
                        {anomaly.title}
                      </Typography>
                      <Typography
                        variant="body2"
                        color="text.secondary"
                        sx={{
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          whiteSpace: 'nowrap',
                        }}
                      >
                        {anomaly.description}
                      </Typography>
                    </Box>

                    {/* Severity and Confidence Chips */}
                    <Stack direction="row" spacing={1}>
                      <Chip
                        icon={SEVERITY_ICONS[anomaly.severity as keyof typeof SEVERITY_ICONS]}
                        label={anomaly.severity.toUpperCase()}
                        size="small"
                        color={SEVERITY_COLORS[anomaly.severity as keyof typeof SEVERITY_COLORS]}
                      />
                      <Chip
                        label={`${Math.round(anomaly.confidence_score * 100)}%`}
                        size="small"
                        variant="outlined"
                      />
                    </Stack>
                  </Box>
                </AccordionSummary>

                <AccordionDetails>
                  <Box sx={{ pt: 1 }}>
                    {/* Full Description */}
                    <Typography variant="body2" paragraph>
                      {anomaly.description}
                    </Typography>

                    <Divider sx={{ my: 2 }} />

                    {/* Affected Resources */}
                    <Typography variant="subtitle2" sx={{ fontWeight: 700, mb: 1 }}>
                      Affected Resources ({anomaly.affected_resources.length})
                    </Typography>
                    <Paper variant="outlined" sx={{ p: 1, mb: 2, maxHeight: 200, overflow: 'auto' }}>
                      <List dense>
                        {anomaly.affected_resources.map((resource, idx) => (
                          <ListItem key={idx}>
                            <ListItemText
                              primary={resource}
                              primaryTypographyProps={{
                                variant: 'caption',
                                fontFamily: 'monospace',
                              }}
                            />
                          </ListItem>
                        ))}
                      </List>
                    </Paper>

                    {/* Remediation Steps */}
                    {anomaly.remediation && (
                      <>
                        <Typography variant="subtitle2" sx={{ fontWeight: 700, mb: 1 }}>
                          Recommended Remediation
                        </Typography>
                        <Alert severity="info" icon={<RemediateIcon />} sx={{ mb: 2 }}>
                          {anomaly.remediation}
                        </Alert>
                      </>
                    )}

                    {/* Actions */}
                    <Stack direction="row" spacing={1} justifyContent="flex-end">
                      <Button variant="outlined" size="small">
                        Acknowledge
                      </Button>
                      <Button variant="outlined" size="small" color="warning">
                        Escalate
                      </Button>
                      {anomaly.remediation && (
                        <Button
                          variant="contained"
                          size="small"
                          startIcon={<RemediateIcon />}
                          onClick={() => handleRemediate(anomaly)}
                        >
                          Remediate
                        </Button>
                      )}
                    </Stack>
                  </Box>
                </AccordionDetails>
              </Accordion>
            </motion.div>
          ))}
        </Stack>
      )}
    </Box>
  );
};

export default AnomaliesView;
