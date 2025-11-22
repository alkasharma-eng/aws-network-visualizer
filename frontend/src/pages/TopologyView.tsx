import React, { useState, useMemo } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  Box,
  Paper,
  Typography,
  ToggleButton,
  ToggleButtonGroup,
  CircularProgress,
  Alert,
  Breadcrumbs,
  Link,
  Chip,
  Stack,
  IconButton,
  Tooltip,
  Drawer,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  useTheme,
  useMediaQuery,
} from '@mui/material';
import {
  ViewInAr as View3DIcon,
  ViewModule as View2DIcon,
  FilterList as FilterIcon,
  Info as InfoIcon,
  NavigateNext as NavigateNextIcon,
  Home as HomeIcon,
  Public as PublicIcon,
  Storage as StorageIcon,
  Security as SecurityIcon,
  Router as RouterIcon,
  Cloud as CloudIcon,
} from '@mui/icons-material';
import { fetchTopology } from '../api/client';
import NetworkGraph3D from '../components/NetworkGraph3D';
import { motion, AnimatePresence } from 'framer-motion';

interface TopologyNode {
  id: string;
  name: string;
  type: string;
  region?: string;
  vpc_id?: string;
  subnet_id?: string;
  metadata?: Record<string, any>;
}

interface TopologyLink {
  source: string;
  target: string;
  type?: string;
  label?: string;
}

interface TopologyData {
  nodes: TopologyNode[];
  links: TopologyLink[];
}

type ViewMode = '2d' | '3d';

const RESOURCE_TYPE_ICONS: Record<string, React.ReactNode> = {
  vpc: <CloudIcon />,
  subnet: <PublicIcon />,
  ec2_instance: <StorageIcon />,
  security_group: <SecurityIcon />,
  route_table: <RouterIcon />,
  internet_gateway: <PublicIcon />,
  nat_gateway: <RouterIcon />,
};

const TopologyView: React.FC = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const { region, vpcId } = useParams<{ region: string; vpcId: string }>();
  const [viewMode, setViewMode] = useState<ViewMode>('3d');
  const [selectedNode, setSelectedNode] = useState<TopologyNode | null>(null);
  const [filterDrawerOpen, setFilterDrawerOpen] = useState(false);
  const [detailsDrawerOpen, setDetailsDrawerOpen] = useState(false);
  const [enabledResourceTypes, setEnabledResourceTypes] = useState<Set<string>>(new Set());

  // Fetch topology data
  const {
    data: topologyData,
    isLoading,
    isError,
    error,
  } = useQuery<TopologyData>({
    queryKey: ['topology', region, vpcId],
    queryFn: () => fetchTopology(region!, vpcId!),
    enabled: !!region && !!vpcId,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  // Initialize enabled resource types
  React.useEffect(() => {
    if (topologyData && enabledResourceTypes.size === 0) {
      const types = new Set(topologyData.nodes.map((node) => node.type));
      setEnabledResourceTypes(types);
    }
  }, [topologyData, enabledResourceTypes.size]);

  // Filter data based on enabled resource types
  const filteredData = useMemo(() => {
    if (!topologyData) return null;

    const filteredNodes = topologyData.nodes.filter((node) =>
      enabledResourceTypes.has(node.type)
    );
    const filteredNodeIds = new Set(filteredNodes.map((node) => node.id));

    const filteredLinks = topologyData.links.filter(
      (link) =>
        filteredNodeIds.has(
          typeof link.source === 'string' ? link.source : link.source
        ) &&
        filteredNodeIds.has(
          typeof link.target === 'string' ? link.target : link.target
        )
    );

    return {
      nodes: filteredNodes,
      links: filteredLinks,
    };
  }, [topologyData, enabledResourceTypes]);

  // Get unique resource types for filtering
  const resourceTypes = useMemo(() => {
    if (!topologyData) return [];
    const types = new Set(topologyData.nodes.map((node) => node.type));
    return Array.from(types).sort();
  }, [topologyData]);

  const handleViewModeChange = (_: React.MouseEvent<HTMLElement>, newMode: ViewMode | null) => {
    if (newMode !== null) {
      setViewMode(newMode);
    }
  };

  const handleNodeClick = (node: TopologyNode) => {
    setSelectedNode(node);
    setDetailsDrawerOpen(true);
  };

  const toggleResourceType = (type: string) => {
    const newSet = new Set(enabledResourceTypes);
    if (newSet.has(type)) {
      newSet.delete(type);
    } else {
      newSet.add(type);
    }
    setEnabledResourceTypes(newSet);
  };

  const selectAllResourceTypes = () => {
    setEnabledResourceTypes(new Set(resourceTypes));
  };

  const deselectAllResourceTypes = () => {
    setEnabledResourceTypes(new Set());
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
          Loading network topology...
        </Typography>
      </Box>
    );
  }

  if (isError) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">
          <Typography variant="h6">Failed to load topology</Typography>
          <Typography variant="body2">{(error as Error).message}</Typography>
        </Alert>
      </Box>
    );
  }

  if (!filteredData) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="info">No topology data available</Alert>
      </Box>
    );
  }

  return (
    <Box sx={{ p: isMobile ? 1 : 3 }}>
      {/* Breadcrumbs */}
      <Breadcrumbs
        separator={<NavigateNextIcon fontSize="small" />}
        sx={{ mb: 2 }}
      >
        <Link
          href="/"
          underline="hover"
          sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}
        >
          <HomeIcon fontSize="small" />
          Dashboard
        </Link>
        <Typography color="text.primary" sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
          <CloudIcon fontSize="small" />
          {region}
        </Typography>
        <Typography color="text.primary">{vpcId}</Typography>
      </Breadcrumbs>

      {/* Header */}
      <Paper elevation={2} sx={{ p: 2, mb: 2 }}>
        <Box
          sx={{
            display: 'flex',
            flexDirection: isMobile ? 'column' : 'row',
            justifyContent: 'space-between',
            alignItems: isMobile ? 'flex-start' : 'center',
            gap: 2,
          }}
        >
          <Box>
            <Typography variant="h5" sx={{ fontWeight: 700, mb: 1 }}>
              Network Topology
            </Typography>
            <Stack direction="row" spacing={1}>
              <Chip
                label={`${filteredData.nodes.length} Resources`}
                size="small"
                color="primary"
              />
              <Chip
                label={`${filteredData.links.length} Connections`}
                size="small"
                color="secondary"
              />
              <Chip
                label={region}
                size="small"
                variant="outlined"
              />
            </Stack>
          </Box>

          <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
            {/* View Mode Toggle */}
            <ToggleButtonGroup
              value={viewMode}
              exclusive
              onChange={handleViewModeChange}
              size="small"
            >
              <ToggleButton value="2d" aria-label="2D view">
                <Tooltip title="2D View">
                  <View2DIcon />
                </Tooltip>
              </ToggleButton>
              <ToggleButton value="3d" aria-label="3D view">
                <Tooltip title="3D View">
                  <View3DIcon />
                </Tooltip>
              </ToggleButton>
            </ToggleButtonGroup>

            {/* Filter Button */}
            <Tooltip title="Filter Resources">
              <IconButton
                onClick={() => setFilterDrawerOpen(true)}
                color={enabledResourceTypes.size < resourceTypes.length ? 'primary' : 'default'}
              >
                <FilterIcon />
              </IconButton>
            </Tooltip>
          </Box>
        </Box>
      </Paper>

      {/* Graph Container */}
      <AnimatePresence mode="wait">
        <motion.div
          key={viewMode}
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.95 }}
          transition={{ duration: 0.3 }}
        >
          {viewMode === '3d' ? (
            <NetworkGraph3D
              data={filteredData}
              onNodeClick={handleNodeClick}
              width={window.innerWidth - (isMobile ? 32 : 96)}
              height={isMobile ? 500 : 700}
            />
          ) : (
            <Paper
              elevation={3}
              sx={{
                p: 3,
                minHeight: isMobile ? 400 : 600,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <Typography variant="h6" color="text.secondary">
                2D view coming soon...
              </Typography>
            </Paper>
          )}
        </motion.div>
      </AnimatePresence>

      {/* Filter Drawer */}
      <Drawer
        anchor="right"
        open={filterDrawerOpen}
        onClose={() => setFilterDrawerOpen(false)}
      >
        <Box sx={{ width: 300, p: 2 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6" sx={{ fontWeight: 700 }}>
              Filter Resources
            </Typography>
            <IconButton size="small" onClick={() => setFilterDrawerOpen(false)}>
              <NavigateNextIcon />
            </IconButton>
          </Box>

          <Stack direction="row" spacing={1} sx={{ mb: 2 }}>
            <Chip
              label="Select All"
              size="small"
              onClick={selectAllResourceTypes}
              variant="outlined"
            />
            <Chip
              label="Deselect All"
              size="small"
              onClick={deselectAllResourceTypes}
              variant="outlined"
            />
          </Stack>

          <Divider sx={{ mb: 2 }} />

          <List>
            {resourceTypes.map((type) => {
              const count = topologyData?.nodes.filter((n) => n.type === type).length || 0;
              const isEnabled = enabledResourceTypes.has(type);

              return (
                <ListItem
                  key={type}
                  button
                  onClick={() => toggleResourceType(type)}
                  sx={{
                    borderRadius: 1,
                    mb: 0.5,
                    opacity: isEnabled ? 1 : 0.4,
                    background: isEnabled ? theme.palette.action.selected : 'transparent',
                  }}
                >
                  <ListItemIcon>
                    {RESOURCE_TYPE_ICONS[type] || <InfoIcon />}
                  </ListItemIcon>
                  <ListItemText
                    primary={type.replace(/_/g, ' ').toUpperCase()}
                    secondary={`${count} resource${count !== 1 ? 's' : ''}`}
                  />
                </ListItem>
              );
            })}
          </List>
        </Box>
      </Drawer>

      {/* Details Drawer */}
      <Drawer
        anchor="right"
        open={detailsDrawerOpen}
        onClose={() => setDetailsDrawerOpen(false)}
      >
        <Box sx={{ width: 350, p: 3 }}>
          {selectedNode && (
            <>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6" sx={{ fontWeight: 700 }}>
                  Resource Details
                </Typography>
                <IconButton size="small" onClick={() => setDetailsDrawerOpen(false)}>
                  <NavigateNextIcon />
                </IconButton>
              </Box>

              <Chip
                label={selectedNode.type.replace(/_/g, ' ').toUpperCase()}
                color="primary"
                sx={{ mb: 2 }}
              />

              <Stack spacing={2}>
                <Box>
                  <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 700 }}>
                    Resource ID
                  </Typography>
                  <Typography variant="body2" sx={{ wordBreak: 'break-all' }}>
                    {selectedNode.id}
                  </Typography>
                </Box>

                {selectedNode.name && (
                  <Box>
                    <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 700 }}>
                      Name
                    </Typography>
                    <Typography variant="body2">{selectedNode.name}</Typography>
                  </Box>
                )}

                {selectedNode.region && (
                  <Box>
                    <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 700 }}>
                      Region
                    </Typography>
                    <Typography variant="body2">{selectedNode.region}</Typography>
                  </Box>
                )}

                {selectedNode.vpc_id && (
                  <Box>
                    <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 700 }}>
                      VPC ID
                    </Typography>
                    <Typography variant="body2">{selectedNode.vpc_id}</Typography>
                  </Box>
                )}

                {selectedNode.subnet_id && (
                  <Box>
                    <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 700 }}>
                      Subnet ID
                    </Typography>
                    <Typography variant="body2">{selectedNode.subnet_id}</Typography>
                  </Box>
                )}

                {selectedNode.metadata && Object.keys(selectedNode.metadata).length > 0 && (
                  <>
                    <Divider />
                    <Box>
                      <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 700, mb: 1, display: 'block' }}>
                        Additional Metadata
                      </Typography>
                      <Paper variant="outlined" sx={{ p: 1.5, background: theme.palette.action.hover }}>
                        {Object.entries(selectedNode.metadata).slice(0, 10).map(([key, value]) => (
                          <Box key={key} sx={{ mb: 0.5 }}>
                            <Typography variant="caption" sx={{ fontWeight: 600 }}>
                              {key}:
                            </Typography>{' '}
                            <Typography variant="caption">
                              {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                            </Typography>
                          </Box>
                        ))}
                      </Paper>
                    </Box>
                  </>
                )}
              </Stack>
            </>
          )}
        </Box>
      </Drawer>
    </Box>
  );
};

export default TopologyView;
