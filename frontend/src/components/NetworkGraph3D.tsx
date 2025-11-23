import React, { useCallback, useRef, useState, useEffect } from 'react';
import ForceGraph3D from 'react-force-graph-3d';
import * as THREE from 'three';
import {
  Box,
  Paper,
  IconButton,
  Tooltip,
  Switch,
  FormControlLabel,
  Typography,
  Chip,
  Stack,
  Button,
  useTheme,
  alpha,
} from '@mui/material';
import {
  ZoomIn as ZoomInIcon,
  ZoomOut as ZoomOutIcon,
  CenterFocusStrong as CenterIcon,
  Rotate90DegreesCcw as RotateIcon,
  Fullscreen as FullscreenIcon,
  FullscreenExit as FullscreenExitIcon,
} from '@mui/icons-material';

interface Node {
  id: string;
  name: string;
  type: string;
  region?: string;
  vpc_id?: string;
  subnet_id?: string;
  metadata?: Record<string, any>;
  x?: number;
  y?: number;
  z?: number;
  vx?: number;
  vy?: number;
  vz?: number;
  fx?: number;
  fy?: number;
  fz?: number;
}

interface Link {
  source: string | Node;
  target: string | Node;
  type?: string;
  label?: string;
}

interface GraphData {
  nodes: Node[];
  links: Link[];
}

interface NetworkGraph3DProps {
  data: GraphData;
  onNodeClick?: (node: Node) => void;
  onNodeHover?: (node: Node | null) => void;
  width?: number;
  height?: number;
}

// Resource type to color mapping (AWS-themed)
const RESOURCE_COLORS: Record<string, string> = {
  vpc: '#FF9900', // AWS Orange
  subnet: '#0073BB', // AWS Blue
  ec2_instance: '#1D8102', // AWS Green
  rds_instance: '#D13212', // AWS Red
  nat_gateway: '#FF9900',
  internet_gateway: '#0073BB',
  transit_gateway: '#232F3E', // AWS Squid Ink
  load_balancer: '#EC7211',
  security_group: '#7D8998',
  route_table: '#545B64',
  network_acl: '#AAB7B8',
  vpc_peering: '#FF9900',
  vpn_connection: '#D13212',
  direct_connect: '#1D8102',
  lambda_eni: '#FF9900',
};

// Resource type to size mapping
const RESOURCE_SIZES: Record<string, number> = {
  vpc: 8,
  subnet: 6,
  ec2_instance: 5,
  rds_instance: 5,
  nat_gateway: 4,
  internet_gateway: 6,
  transit_gateway: 10,
  load_balancer: 6,
  security_group: 3,
  route_table: 3,
  network_acl: 3,
  vpc_peering: 4,
  vpn_connection: 4,
  direct_connect: 8,
  lambda_eni: 4,
};

const NetworkGraph3D: React.FC<NetworkGraph3DProps> = ({
  data,
  onNodeClick,
  onNodeHover,
  width = 1200,
  height = 800,
}) => {
  const theme = useTheme();
  const graphRef = useRef<any>();
  const [highlightNodes, setHighlightNodes] = useState<Set<string>>(new Set());
  const [highlightLinks, setHighlightLinks] = useState<Set<Link>>(new Set());
  const [hoverNode, setHoverNode] = useState<Node | null>(null);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [enableParticles, setEnableParticles] = useState(true);
  const [enableLabels, setEnableLabels] = useState(true);
  const [rotationSpeed, setRotationSpeed] = useState(0);
  const containerRef = useRef<HTMLDivElement>(null);

  // Auto-rotate camera
  useEffect(() => {
    if (rotationSpeed > 0 && graphRef.current) {
      const interval = setInterval(() => {
        const camera = graphRef.current.camera();
        if (camera) {
          camera.position.applyAxisAngle(
            new THREE.Vector3(0, 1, 0),
            rotationSpeed * 0.01
          );
          camera.lookAt(graphRef.current.scene().position);
        }
      }, 50);
      return () => clearInterval(interval);
    }
  }, [rotationSpeed]);

  // Handle node hover
  const handleNodeHover = useCallback(
    (node: Node | null) => {
      setHoverNode(node);
      if (onNodeHover) {
        onNodeHover(node);
      }

      if (!node) {
        setHighlightNodes(new Set());
        setHighlightLinks(new Set());
        return;
      }

      // Highlight connected nodes and links
      const connectedNodes = new Set<string>([node.id]);
      const connectedLinks = new Set<Link>();

      data.links.forEach((link) => {
        const sourceId = typeof link.source === 'string' ? link.source : link.source.id;
        const targetId = typeof link.target === 'string' ? link.target : link.target.id;

        if (sourceId === node.id || targetId === node.id) {
          connectedLinks.add(link);
          connectedNodes.add(sourceId);
          connectedNodes.add(targetId);
        }
      });

      setHighlightNodes(connectedNodes);
      setHighlightLinks(connectedLinks);
    },
    [data.links, onNodeHover]
  );

  // Handle node click
  const handleNodeClick = useCallback(
    (node: Node) => {
      setSelectedNode(node);
      if (onNodeClick) {
        onNodeClick(node);
      }

      // Zoom to node
      if (graphRef.current) {
        const distance = 40;
        const distRatio = 1 + distance / Math.hypot(node.x || 0, node.y || 0, node.z || 0);

        graphRef.current.cameraPosition(
          {
            x: (node.x || 0) * distRatio,
            y: (node.y || 0) * distRatio,
            z: (node.z || 0) * distRatio,
          },
          node,
          1000
        );
      }
    },
    [onNodeClick]
  );

  // Node styling
  const nodeColor = useCallback(
    (node: Node) => {
      const baseColor = RESOURCE_COLORS[node.type] || '#AAB7B8';

      if (selectedNode?.id === node.id) {
        return '#FFFF00'; // Yellow for selected
      }

      if (highlightNodes.size > 0 && !highlightNodes.has(node.id)) {
        return alpha(baseColor, 0.2);
      }

      return baseColor;
    },
    [selectedNode, highlightNodes]
  );

  const nodeSize = useCallback(
    (node: Node) => {
      const baseSize = RESOURCE_SIZES[node.type] || 4;
      if (selectedNode?.id === node.id) {
        return baseSize * 1.5;
      }
      if (hoverNode?.id === node.id) {
        return baseSize * 1.3;
      }
      return baseSize;
    },
    [selectedNode, hoverNode]
  );

  // Node label
  const nodeLabel = useCallback(
    (node: Node) => {
      if (!enableLabels) return '';

      return `
        <div style="
          background: ${alpha(theme.palette.background.paper, 0.95)};
          padding: 12px;
          border-radius: 8px;
          border: 2px solid ${RESOURCE_COLORS[node.type] || '#AAB7B8'};
          color: ${theme.palette.text.primary};
          font-family: ${theme.typography.fontFamily};
          box-shadow: 0 4px 12px rgba(0,0,0,0.3);
          min-width: 200px;
        ">
          <div style="font-weight: 700; font-size: 14px; margin-bottom: 8px; color: ${RESOURCE_COLORS[node.type] || '#AAB7B8'}">
            ${node.type.toUpperCase().replace(/_/g, ' ')}
          </div>
          <div style="font-size: 12px; margin-bottom: 4px;">
            <strong>ID:</strong> ${node.id}
          </div>
          ${node.name ? `<div style="font-size: 12px; margin-bottom: 4px;"><strong>Name:</strong> ${node.name}</div>` : ''}
          ${node.region ? `<div style="font-size: 12px; margin-bottom: 4px;"><strong>Region:</strong> ${node.region}</div>` : ''}
          ${node.vpc_id ? `<div style="font-size: 12px; margin-bottom: 4px;"><strong>VPC:</strong> ${node.vpc_id}</div>` : ''}
          ${node.subnet_id ? `<div style="font-size: 12px;"><strong>Subnet:</strong> ${node.subnet_id}</div>` : ''}
        </div>
      `;
    },
    [enableLabels, theme]
  );

  // Link styling
  const linkColor = useCallback(
    (link: Link) => {
      if (highlightLinks.size > 0 && !highlightLinks.has(link)) {
        return alpha('#AAB7B8', 0.1);
      }
      return alpha('#AAB7B8', 0.6);
    },
    [highlightLinks]
  );

  const linkWidth = useCallback(
    (link: Link) => {
      if (highlightLinks.has(link)) {
        return 2;
      }
      return 1;
    },
    [highlightLinks]
  );

  // Add particles to links for flow visualization
  const linkDirectionalParticles = useCallback(() => {
    return enableParticles ? 2 : 0;
  }, [enableParticles]);

  const linkDirectionalParticleSpeed = useCallback(() => 0.003, []);
  const linkDirectionalParticleWidth = useCallback(() => 2, []);

  // Camera controls
  const handleZoomIn = () => {
    if (graphRef.current) {
      const camera = graphRef.current.camera();
      const currentDistance = camera.position.length();
      const newDistance = currentDistance * 0.8;
      camera.position.normalize().multiplyScalar(newDistance);
    }
  };

  const handleZoomOut = () => {
    if (graphRef.current) {
      const camera = graphRef.current.camera();
      const currentDistance = camera.position.length();
      const newDistance = currentDistance * 1.2;
      camera.position.normalize().multiplyScalar(newDistance);
    }
  };

  const handleCenter = () => {
    if (graphRef.current) {
      graphRef.current.zoomToFit(400);
    }
  };

  const toggleRotation = () => {
    setRotationSpeed(rotationSpeed === 0 ? 1 : 0);
  };

  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      containerRef.current?.requestFullscreen();
      setIsFullscreen(true);
    } else {
      document.exitFullscreen();
      setIsFullscreen(false);
    }
  };

  return (
    <Paper
      ref={containerRef}
      elevation={3}
      sx={{
        position: 'relative',
        width: '100%',
        height: isFullscreen ? '100vh' : height,
        overflow: 'hidden',
        background: theme.palette.mode === 'dark' ? '#0A0A0A' : '#000000',
      }}
    >
      {/* Controls Panel */}
      <Box
        sx={{
          position: 'absolute',
          top: 16,
          right: 16,
          zIndex: 10,
          display: 'flex',
          flexDirection: 'column',
          gap: 1,
        }}
      >
        <Paper
          elevation={6}
          sx={{
            p: 1,
            background: alpha(theme.palette.background.paper, 0.9),
            backdropFilter: 'blur(10px)',
          }}
        >
          <Stack spacing={1}>
            <Tooltip title="Zoom In" placement="left">
              <IconButton size="small" onClick={handleZoomIn}>
                <ZoomInIcon />
              </IconButton>
            </Tooltip>
            <Tooltip title="Zoom Out" placement="left">
              <IconButton size="small" onClick={handleZoomOut}>
                <ZoomOutIcon />
              </IconButton>
            </Tooltip>
            <Tooltip title="Center View" placement="left">
              <IconButton size="small" onClick={handleCenter}>
                <CenterIcon />
              </IconButton>
            </Tooltip>
            <Tooltip title={rotationSpeed > 0 ? 'Stop Rotation' : 'Auto Rotate'} placement="left">
              <IconButton
                size="small"
                onClick={toggleRotation}
                color={rotationSpeed > 0 ? 'primary' : 'default'}
              >
                <RotateIcon />
              </IconButton>
            </Tooltip>
            <Tooltip title={isFullscreen ? 'Exit Fullscreen' : 'Fullscreen'} placement="left">
              <IconButton size="small" onClick={toggleFullscreen}>
                {isFullscreen ? <FullscreenExitIcon /> : <FullscreenIcon />}
              </IconButton>
            </Tooltip>
          </Stack>
        </Paper>

        {/* Settings Panel */}
        <Paper
          elevation={6}
          sx={{
            p: 2,
            background: alpha(theme.palette.background.paper, 0.9),
            backdropFilter: 'blur(10px)',
            minWidth: 200,
          }}
        >
          <Typography variant="caption" sx={{ fontWeight: 700, mb: 1, display: 'block' }}>
            Display Options
          </Typography>
          <Stack spacing={1}>
            <FormControlLabel
              control={
                <Switch
                  size="small"
                  checked={enableParticles}
                  onChange={(e) => setEnableParticles(e.target.checked)}
                />
              }
              label={
                <Typography variant="caption">
                  Link Particles
                </Typography>
              }
            />
            <FormControlLabel
              control={
                <Switch
                  size="small"
                  checked={enableLabels}
                  onChange={(e) => setEnableLabels(e.target.checked)}
                />
              }
              label={
                <Typography variant="caption">
                  Node Labels
                </Typography>
              }
            />
          </Stack>
        </Paper>
      </Box>

      {/* Stats Panel */}
      <Box
        sx={{
          position: 'absolute',
          top: 16,
          left: 16,
          zIndex: 10,
        }}
      >
        <Paper
          elevation={6}
          sx={{
            p: 2,
            background: alpha(theme.palette.background.paper, 0.9),
            backdropFilter: 'blur(10px)',
            minWidth: 250,
          }}
        >
          <Typography variant="h6" sx={{ fontWeight: 700, mb: 1 }}>
            Network Topology 3D
          </Typography>
          <Stack direction="row" spacing={1} sx={{ mb: 1 }}>
            <Chip
              label={`${data.nodes.length} Nodes`}
              size="small"
              color="primary"
              variant="outlined"
            />
            <Chip
              label={`${data.links.length} Links`}
              size="small"
              color="secondary"
              variant="outlined"
            />
          </Stack>
          {selectedNode && (
            <Box sx={{ mt: 2, pt: 2, borderTop: 1, borderColor: 'divider' }}>
              <Typography variant="caption" sx={{ fontWeight: 700, display: 'block', mb: 0.5 }}>
                Selected Node
              </Typography>
              <Typography variant="body2" sx={{ fontSize: '0.75rem' }}>
                {selectedNode.type.toUpperCase().replace(/_/g, ' ')}
              </Typography>
              <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                {selectedNode.id}
              </Typography>
              <Button
                size="small"
                variant="outlined"
                fullWidth
                sx={{ mt: 1 }}
                onClick={() => setSelectedNode(null)}
              >
                Deselect
              </Button>
            </Box>
          )}
        </Paper>
      </Box>

      {/* Legend */}
      <Box
        sx={{
          position: 'absolute',
          bottom: 16,
          left: 16,
          zIndex: 10,
        }}
      >
        <Paper
          elevation={6}
          sx={{
            p: 2,
            background: alpha(theme.palette.background.paper, 0.9),
            backdropFilter: 'blur(10px)',
            maxHeight: 300,
            overflow: 'auto',
          }}
        >
          <Typography variant="caption" sx={{ fontWeight: 700, mb: 1, display: 'block' }}>
            Resource Types
          </Typography>
          <Stack spacing={0.5}>
            {Object.keys(RESOURCE_COLORS).slice(0, 10).map((type) => (
              <Box key={type} sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Box
                  sx={{
                    width: 12,
                    height: 12,
                    borderRadius: '50%',
                    background: RESOURCE_COLORS[type],
                  }}
                />
                <Typography variant="caption" sx={{ fontSize: '0.7rem' }}>
                  {type.replace(/_/g, ' ').toUpperCase()}
                </Typography>
              </Box>
            ))}
          </Stack>
        </Paper>
      </Box>

      {/* 3D Graph */}
      <ForceGraph3D
        ref={graphRef}
        graphData={data}
        width={width}
        height={isFullscreen ? window.innerHeight : height}
        backgroundColor="#000000"
        nodeLabel={nodeLabel}
        nodeColor={nodeColor}
        nodeRelSize={nodeSize as any}
        nodeOpacity={0.9}
        linkColor={linkColor}
        linkWidth={linkWidth}
        linkOpacity={0.6}
        linkDirectionalParticles={linkDirectionalParticles}
        linkDirectionalParticleSpeed={linkDirectionalParticleSpeed}
        linkDirectionalParticleWidth={linkDirectionalParticleWidth}
        linkDirectionalParticleColor={() => '#FF9900'}
        onNodeClick={handleNodeClick}
        onNodeHover={handleNodeHover}
        enableNodeDrag={true}
        enableNavigationControls={true}
        showNavInfo={false}
        d3AlphaDecay={0.02}
        d3VelocityDecay={0.3}
        warmupTicks={100}
        cooldownTicks={200}
      />
    </Paper>
  );
};

export default NetworkGraph3D;
